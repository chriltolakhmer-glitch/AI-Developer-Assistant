"""User-facing command line entry point for the research prototype."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from typing import Sequence

from src.chunker import CodeChunker
from src.config import PrototypeConfig, load_config
from src.evaluation import PipelineValidationRunner
from src.evaluation.benchmark import Benchmark, BenchmarkCase
from src.evaluation.retrieval import EvaluationReport, RetrievalEvaluator
from src.models.corpus import RepositoryMetadata
from src.models.embedding import EmbeddingMetadata
from src.models.retrieval_result import SearchResult
from src.parser import PythonAstParser
from src.tracking import RunTracker, load_run


_DEMO_REPOSITORY = "synthetic/prototype-demo"
_DEMO_COMMIT = "0" * 40
def _build_demo() -> tuple[Benchmark, tuple[SearchResult, ...], tuple[object, ...]]:
    source = """\
def greet(name):
    return f\"Hello, {name}\"

def add(left, right):
    return left + right
"""
    module = PythonAstParser().parse(source, "demo.py")
    chunks = CodeChunker().chunk_module(
        module,
        source,
        RepositoryMetadata(_DEMO_REPOSITORY, _DEMO_COMMIT),
    )
    metadata = tuple(
        EmbeddingMetadata(
            chunk.repository_id,
            chunk.commit_sha,
            chunk.file_path,
            chunk.entity_type,
            chunk.qualified_name,
            chunk.start_line,
            chunk.end_line,
            "0" * 64,
            1,
        )
        for chunk in chunks
    )
    results = tuple(
        SearchResult(chunk.chunk_id, rank, 1.0 / rank, item, strategy="demo")
        for rank, (chunk, item) in enumerate(zip(chunks, metadata), start=1)
    )
    benchmark = Benchmark(
        "1.0",
        (
            BenchmarkCase(
                "prototype-demo-001",
                _DEMO_REPOSITORY,
                _DEMO_COMMIT,
                "Where is greeting implemented?",
                ((chunks[1].chunk_id, 2),),
            ),
            BenchmarkCase(
                "prototype-demo-002",
                _DEMO_REPOSITORY,
                _DEMO_COMMIT,
                "What does the module contain?",
                ((chunks[0].chunk_id, 1),),
            ),
        ),
    )
    return benchmark, results, chunks


def _evaluate_demo() -> EvaluationReport:
    benchmark, results, _ = _build_demo()

    def ranked(*rows: SearchResult) -> tuple[SearchResult, ...]:
        return tuple(replace(row, rank=rank) for rank, row in enumerate(rows, start=1))

    def retriever(case: BenchmarkCase) -> tuple[SearchResult, ...]:
        if case.query_id.endswith("001"):
            return ranked(results[1], results[2], results[0])
        return ranked(*results)

    return RetrievalEvaluator().evaluate(benchmark, "demo", retriever, ks=(1, 5))


def _path_argument(value: str) -> Path:
    return Path(value).expanduser()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prototype",
        description="Run the local, reproducible research software prototype.",
        epilog="Examples: prototype validate | prototype evaluate | prototype demo",
    )
    parser.add_argument(
        "--config",
        type=_path_argument,
        help="YAML configuration file (default: config/default.yaml).",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser(
        "validate",
        help="Validate pinned local checkouts with the scanner, parser, and chunker.",
        description="Run offline preprocessing validation. Missing checkouts are reported; nothing is fetched.",
    )
    validate.add_argument(
        "--corpus-root",
        type=_path_argument,
        help="Directory containing pinned local checkouts (default: config corpus_root).",
    )
    validate.add_argument(
        "--output-dir",
        type=_path_argument,
        help="External directory for aggregate reports (default: config validation_output).",
    )

    evaluate = commands.add_parser(
        "evaluate",
        help="Run the deterministic evaluation smoke check.",
        description="Evaluate generated, non-sensitive fixtures without model or network access.",
    )
    evaluate.add_argument(
        "--json",
        action="store_true",
        help="Print the complete machine-readable evaluation report.",
    )

    commands.add_parser(
        "demo",
        help="Demonstrate parsing, chunking, and evaluation with generated fixtures.",
        description="Run a short offline walkthrough using generated Python code only.",
    )
    reproduce = commands.add_parser(
        "reproduce",
        help="Rerun a saved run and compare its standardized result.",
        description="Load a saved run configuration, rerun its command, and compare payloads.",
    )
    reproduce.add_argument("run_id", help="Run directory name under the configured runs directory.")
    return parser


def _run_validate(options: argparse.Namespace, config: PrototypeConfig) -> dict[str, object]:
    corpus_root = options.corpus_root or config.corpus_root
    output_dir = options.output_dir or config.validation_output
    if corpus_root.exists() and not corpus_root.is_dir():
        raise ValueError(f"Corpus root is not a directory: {corpus_root}")
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(f"Validation output path is not a directory: {output_dir}")
    try:
        report = PipelineValidationRunner().run(corpus_root, output_dir)
    except OSError as error:
        raise ValueError(
            f"Validation could not read the corpus root '{corpus_root}' or write reports to "
            f"'{output_dir}': {error}"
        ) from error
    if not corpus_root.is_dir():
        import logging
        logging.getLogger("prototype").warning(
            "Corpus root is missing; no snapshots will validate and readiness will be no: %s",
            corpus_root,
        )
    logging.getLogger("prototype").info("Validation stage completed")
    print(
        f"Validation reports: {output_dir.resolve()}\n"
        f"Snapshots validated: {report.validated_repository_count}/{report.expected_repository_count}\n"
        f"Preprocessing ready: {'yes' if report.preprocessing_ready else 'no'}"
    )
    return {
        "status": "completed",
        "corpus_root": str(corpus_root),
        "output_dir": str(output_dir),
        "report": report.to_dict() if hasattr(report, "to_dict") else {
            "validated_repository_count": report.validated_repository_count,
            "expected_repository_count": report.expected_repository_count,
            "preprocessing_ready": report.preprocessing_ready,
        },
    }


def _run_evaluate(as_json: bool) -> dict[str, object]:
    report = _evaluate_demo()
    import logging
    logging.getLogger("prototype").info("Evaluation stage completed")
    payload = {"status": "completed", "report": report.to_dict()}
    if as_json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(
            f"Evaluation smoke check passed: system={report.system}, "
            f"queries={len(report.query_results)}, mrr={report.mrr:.3f}, "
            f"ndcg={report.ndcg:.3f}"
        )
    return payload


def _run_demo() -> dict[str, object]:
    benchmark, _, chunks = _build_demo()
    report = _evaluate_demo()
    import logging
    logging.getLogger("prototype").info("Demo parsing and chunking stage completed")
    print("Prototype demo (generated fixture; no repository or network access)")
    print(f"Parsed and chunked: {len(chunks)} chunks from demo.py")
    print(f"Evaluated: {len(benchmark.cases)} queries")
    print(f"Metrics: MRR={report.mrr:.3f}, nDCG={report.ndcg:.3f}")
    return {
        "status": "completed",
        "chunk_count": len(chunks),
        "query_count": len(benchmark.cases),
        "metrics": {"mrr": report.mrr, "ndcg": report.ndcg},
    }


def _run_command(options: argparse.Namespace, config: PrototypeConfig) -> dict[str, object]:
    if options.command == "validate":
        return _run_validate(options, config)
    if options.command == "evaluate":
        return _run_evaluate(options.json)
    return _run_demo()


def _run_reproduce(options: argparse.Namespace, config: PrototypeConfig) -> dict[str, object]:
    original_directory = config.data_root / "runs" / options.run_id
    original_config_path = original_directory / "config.yaml"
    metadata, original_results = load_run(config.data_root / "runs", options.run_id)
    original_config = load_config(original_config_path, environ={})
    original_arguments = metadata.get("arguments")
    if not isinstance(original_arguments, list) or not all(isinstance(item, str) for item in original_arguments):
        raise ValueError(f"Run has no valid command arguments: {options.run_id}")
    parser = _build_parser()
    replay_options = parser.parse_args(original_arguments)
    replay_payload = _run_command(replay_options, original_config)
    expected_payload = original_results.get("payload")
    if replay_payload != expected_payload:
        raise ValueError(
            f"Reproduction for run '{options.run_id}' did not match its saved result. "
            "Check that the same software revision, configuration, and local inputs are in use."
        )
    import logging
    logging.getLogger("prototype").info("Reproduction comparison passed for %s", options.run_id)
    print(f"Reproduction passed: {options.run_id}")
    return {"status": "matched", "original_run_id": options.run_id}


def main(arguments: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    options = parser.parse_args(arguments)
    tracker = None
    try:
        config = load_config(options.config)
        if options.command == "reproduce":
            command_name = "reproduce"
        else:
            command_name = options.command
        tracker = RunTracker(config, command_name, list(arguments or sys.argv[1:]))
        with tracker.execute():
            if options.command == "reproduce":
                payload = _run_reproduce(options, config)
            else:
                payload = _run_command(options, config)
        tracker.finish(payload)
        return 0
    except (OSError, ValueError) as error:
        if tracker is not None:
            try:
                tracker.finish({"status": "failed", "error": str(error)})
            except OSError:
                pass
        print(f"prototype: error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())