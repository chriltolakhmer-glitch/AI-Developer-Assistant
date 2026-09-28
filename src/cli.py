"""User-facing command line entry point for the research prototype."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import logging
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
_DEVELOPER_MODE_NOTICE = "This is a local developer workspace. Results are not benchmark results."


def _research_storage_roots(config: PrototypeConfig) -> tuple[Path, ...]:
    return (config.data_root, config.corpus_root, config.validation_output, config.embedding_model_cache)


def _print_local_results(results: object) -> None:
    if not results:
        print("No positive matches. Try a symbol name or a term present in the repository.")
        return
    for result in results:
        print(
            f"{result['rank']}. {result['file_path']}:{result['start_line']}-{result['end_line']} "
            f"({result['entity_type']} {result['qualified_name']}, score={result['score']:.4f})"
        )
        if "ranking_reason" in result:
            reason = result["ranking_reason"]
            print(f"   {result['retrieval_source']}; metadata matches: {', '.join(reason['matched_metadata_terms']) or 'none'}; "
                  f"factors: metadata={reason['metadata_factor']}, tests={reason['test_factor']}, container={reason['container_factor']}, diversity={reason['diversity_factor']:.3f}")


def _print_unsupported_files(extensions: dict[str, int]) -> None:
    if extensions:
        details = ", ".join(f"{suffix}: {count}" for suffix, count in sorted(extensions.items()))
        print(f"Ignored unsupported file types (Python-only parser): {details}")


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
        description=(
            "Run separate research workflows or personal local developer experiments.\n\n"
            "Research commands: validate, evaluate, reproduce.\n"
            "Developer commands: local scan, local inspect, local index, local query, local trace, local diagnose, "
            "local analyze-context, local compare, local regression, local explain, local evaluate, local demo.\n"
            f"{_DEVELOPER_MODE_NOTICE}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Research: prototype validate | prototype evaluate --json | prototype reproduce RUN_ID\n"
            "Developer: prototype local scan REPOSITORY | prototype local index REPOSITORY | "
            "prototype local query QUESTION | prototype local trace QUERY | prototype local diagnose CASE | "
            "prototype local analyze-context QUERY | prototype local compare QUERY | prototype local regression REPOSITORY --cases PATH | "
            "prototype local explain QUESTION | prototype local evaluate REPOSITORY | prototype local demo"
        ),
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

    local = commands.add_parser(
        "local",
        help="Use a separate local developer workspace (not research or benchmark mode).",
        description=_DEVELOPER_MODE_NOTICE,
    )
    local_commands = local.add_subparsers(dest="local_command", required=True)
    for name, help_text in (
        ("scan", "Read-only scan of a local Git repository."),
        ("inspect", "Explain file exclusions, parser failures and chunk coverage."),
        ("index", "Parse and build a temporary local dense + BM25 index."),
    ):
        command = local_commands.add_parser(name, help=help_text)
        command.add_argument("repository", type=_path_argument, help="Existing local Git working-tree root.")
        command.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
        command.add_argument("--json", action="store_true", help="Print developer diagnostics as JSON.")
        command.add_argument("--changes", action="store_true", help="Show changed files and stale-symbol diagnostics.")

    query = local_commands.add_parser("query", help="Query an existing local developer index.")
    query.add_argument("question", help="Question text; stored only in the local developer run record.")
    query.add_argument("--repository", type=_path_argument, help="Select an indexed repository when multiple exist.")
    query.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    query.add_argument("--top-k", type=int, default=10, help="Maximum results (1-50; default: 10).")
    query.add_argument("--json", action="store_true", help="Print results with component scores and ranking reasons.")
    trace = local_commands.add_parser("trace", help="Explain retrieval evidence, relationships and ranking factors.")
    trace.add_argument("question", help="Query text; stored only in the local developer run record.")
    trace.add_argument("--repository", type=_path_argument, help="Select an indexed repository when multiple exist.")
    trace.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    trace.add_argument("--top-k", type=int, default=10, help="Maximum results (1-50; default: 10).")
    trace.add_argument("--json", action="store_true", help="Print the complete retrieval trace as JSON.")
    analyze_context = local_commands.add_parser(
        "analyze-context", help="Explain selected, missing, extra, and duplicate developer context."
    )
    analyze_context.add_argument("question", help="Query text to analyze against the local index.")
    analyze_context.add_argument("--repository", type=_path_argument, help="Select an indexed repository.")
    analyze_context.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    analyze_context.add_argument("--top-k", type=int, default=10, help="Maximum results to analyze (1-50; default: 10).")
    analyze_context.add_argument("--cases", type=_path_argument, help="Optional developer-only expected-evidence cases.")
    analyze_context.add_argument("--case-id", help="Select an expected-evidence case from --cases.")
    analyze_context.add_argument("--json", action="store_true", help="Print the complete context analysis as JSON.")
    compare = local_commands.add_parser(
        "compare", help="Compare current retrieval with the previous local retrieval record."
    )
    compare.add_argument("question", nargs="?", help="Query text to compare against its prior local result.")
    compare.add_argument("--before", help="Saved developer baseline name or regression history ID.")
    compare.add_argument("--after", help="Saved developer baseline name or regression history ID.")
    compare.add_argument("--repository-id", help="Repository identifier for saved version comparison.")
    compare.add_argument("--repository", type=_path_argument, help="Select an indexed repository.")
    compare.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    compare.add_argument("--top-k", type=int, default=10, help="Maximum results per retrieval (1-50; default: 10).")
    compare.add_argument("--json", action="store_true", help="Print the complete retrieval comparison as JSON.")
    for command in ("inspect-history", "timeline"):
        history = local_commands.add_parser(command, help="Inspect developer-only retrieval observations.")
        history.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
        history.add_argument("--repository-id", help="Exact repository identifier from local records.")
        history.add_argument("--json", action="store_true", help="Print the complete descriptive report.")
        if command == "inspect-history":
            history.add_argument("--query", help="Exact case ID or query identifier.")
            history.add_argument("--limit", type=int, default=20, help="Recent events to display (1-1000).")
        else:
            history.add_argument("--note", help="Record a developer-supplied fix note; requires --repository-id.")

    optimize = local_commands.add_parser("optimize", help="Track and validate developer-only optimization experiments.")
    optimize.add_argument("action", nargs="?", default="list",
                          choices=("list", "show", "create", "validate", "accept", "reject", "register", "transition"))
    optimize.add_argument("--id", help="Candidate identifier.")
    optimize.add_argument("--problem")
    optimize.add_argument("--case", action="append", default=[], help="Affected case ID; repeat as needed.")
    optimize.add_argument("--source", action="append", default=[], help="Evidence event ID from inspect-history; repeat as needed.")
    optimize.add_argument("--proposed-change")
    optimize.add_argument("--validation-method")
    optimize.add_argument("--supersedes", help="Prior rejected candidate ID this experiment retries.")
    optimize.add_argument("--repository", type=_path_argument)
    optimize.add_argument("--cases", type=_path_argument)
    optimize.add_argument("--before", help="Immutable named baseline for live validation.")
    optimize.add_argument("--ranking-note", action="append", default=[], metavar="CASE=EXPLANATION")
    optimize.add_argument("--note", help="Acceptance or rejection rationale, or lifecycle transition note.")
    optimize.add_argument("--owner", help="Developer accountable for the experiment (lifecycle registration).")
    optimize.add_argument("--purpose", help="Why the experiment exists (lifecycle registration).")
    optimize.add_argument("--last-validation-at", help="ISO-8601 timestamp for a validated lifecycle transition.")
    optimize.add_argument("--state", choices=("proposed", "experimenting", "validated", "accepted", "rejected",
                                              "rolled_back", "archived"), help="Target lifecycle state (transition).")
    optimize.add_argument("--workspace", type=_path_argument)
    optimize.add_argument("--json", action="store_true")

    optimize_status = local_commands.add_parser(
        "optimize-status", help="Show developer-only optimization lifecycle status across candidates."
    )
    optimize_status.add_argument("--workspace", type=_path_argument)
    optimize_status.add_argument("--json", action="store_true")

    optimize_archive = local_commands.add_parser(
        "optimize-archive", help="Archive an obsolete developer-only optimization experiment; history is preserved."
    )
    optimize_archive.add_argument("id", help="Candidate identifier.")
    optimize_archive.add_argument("--note", required=True, help="Reason for archiving the experiment.")
    optimize_archive.add_argument("--workspace", type=_path_argument)
    optimize_archive.add_argument("--json", action="store_true")

    optimize_maintenance = local_commands.add_parser(
        "optimize-maintenance", help="Detect stale, duplicate or unmaintained developer-only optimization candidates."
    )
    optimize_maintenance.add_argument("--workspace", type=_path_argument)
    optimize_maintenance.add_argument("--json", action="store_true")

    optimize_audit = local_commands.add_parser(
        "optimize-audit", help="Audit developer-only optimization lifecycle integrity without modifying records."
    )
    optimize_audit.add_argument("--workspace", type=_path_argument)
    optimize_audit.add_argument("--json", action="store_true")

    optimize_history = local_commands.add_parser(
        "optimize-history", help="Inspect immutable developer-only lifecycle and experiment history for one candidate."
    )
    optimize_history.add_argument("id", help="Candidate identifier.")
    optimize_history.add_argument("--workspace", type=_path_argument)
    optimize_history.add_argument("--json", action="store_true")

    optimize_health = local_commands.add_parser(
        "optimize-health", help="Run a read-only developer optimization governance health check."
    )
    optimize_health.add_argument("--workspace", type=_path_argument)
    optimize_health.add_argument("--json", action="store_true")

    optimize_summary = local_commands.add_parser(
        "optimize-summary", help="Summarize developer-only candidate lifecycle and governance activity."
    )
    optimize_summary.add_argument("--workspace", type=_path_argument)
    optimize_summary.add_argument("--recent-limit", type=int, default=20,
                                  help="Recent lifecycle events to include (1-1000; default: 20).")
    optimize_summary.add_argument("--json", action="store_true")

    optimize_checkpoint = local_commands.add_parser(
        "optimize-checkpoint", help="Append a read-only governance health snapshot in the developer workspace."
    )
    optimize_checkpoint.add_argument("--workspace", type=_path_argument)
    optimize_checkpoint.add_argument("--json", action="store_true")

    optimize_review_create = local_commands.add_parser(
        "optimize-review-create", help="Open a pending developer-only optimization review."
    )
    optimize_review_create.add_argument("candidate_id", help="Optimization candidate identifier.")
    optimize_review_create.add_argument("--owner", default="developer", help="Developer responsible for the review request.")
    optimize_review_create.add_argument("--reason", required=True, help="Why this candidate is being submitted for review.")
    optimize_review_create.add_argument("--case", action="append", dest="affected_cases", help="Affected case ID; repeat as needed.")
    optimize_review_create.add_argument("--conflict-note", help="Document known conflicts for human review; does not resolve them.")
    optimize_review_create.add_argument("--workspace", type=_path_argument)
    optimize_review_create.add_argument("--json", action="store_true")

    optimize_review = local_commands.add_parser(
        "optimize-review", help="Show a complete developer-only review or list the review queue."
    )
    optimize_review.add_argument("id", nargs="?", help="Review ID or candidate ID; omit to list the queue.")
    optimize_review.add_argument("--workspace", type=_path_argument)
    optimize_review.add_argument("--json", action="store_true")

    for command, help_text in (
        ("optimize-approve", "Approve a pending developer-only review after policy and validation checks."),
        ("optimize-reject", "Reject a pending developer-only review and preserve the reason."),
        ("optimize-review-defer", "Defer a pending developer-only review."),
        ("optimize-review-withdraw", "Withdraw a pending developer-only review."),
        ("optimize-review-reopen", "Return a deferred developer-only review to pending."),
    ):
        review_action = local_commands.add_parser(command, help=help_text)
        review_action.add_argument("id", help="Review ID or unambiguous candidate ID.")
        review_action.add_argument("--reviewer", default="developer", help="Developer recording the review decision.")
        review_action.add_argument("--reason", required=True, help="Decision or transition reason.")
        if command == "optimize-approve":
            review_action.add_argument("--conflict-note", help="Document known conflicts for human review; does not resolve them.")
        review_action.add_argument("--workspace", type=_path_argument)
        review_action.add_argument("--json", action="store_true")

    optimize_policy = local_commands.add_parser(
        "optimize-policy-check", help="Run read-only developer optimization governance policy checks."
    )
    optimize_policy.add_argument("--id", help="Optionally check one candidate instead of the whole workspace.")
    optimize_policy.add_argument("--workspace", type=_path_argument)
    optimize_policy.add_argument("--json", action="store_true")

    optimize_check = local_commands.add_parser(
        "optimize-check", help="Diagnose developer-only optimization conflicts without resolving them."
    )
    optimize_check.add_argument("--repository-id", help="Restrict diagnostics to one developer repository.")
    optimize_check.add_argument("--workspace", type=_path_argument)
    optimize_check.add_argument("--json", action="store_true")

    rollback = local_commands.add_parser(
        "rollback", help="Inspect or record developer-only restoration of a decided optimization candidate."
    )
    rollback.add_argument("action", nargs="?", default="show", choices=("show", "record"))
    rollback.add_argument("--id", help="Candidate identifier.")
    rollback.add_argument("--note", help="Rollback rationale; required to record a rollback.")
    rollback.add_argument("--workspace", type=_path_argument)
    rollback.add_argument("--json", action="store_true")

    regression = local_commands.add_parser("regression", help="Compare developer retrieval with an immutable local baseline (no scores).")
    regression.add_argument("repository", type=_path_argument, help="Existing indexed local Git repository.")
    regression.add_argument("--cases", type=_path_argument, required=True, help="Developer-only query cases JSON.")
    regression.add_argument("--baseline", default="default", help="Named baseline in the developer workspace.")
    regression.add_argument("--create-baseline", action="store_true", help="Create a new baseline; existing baselines are never overwritten.")
    regression.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    regression.add_argument("--top-k", type=int, default=10, help="Results per case (1-50; must match baseline).")
    regression.add_argument("--json", action="store_true", help="Print the complete descriptive regression report.")
    diagnose = local_commands.add_parser("diagnose", help="Explain missing evidence for a developer case.")
    diagnose.add_argument("case_id", help="Case ID from the developer-only cases JSON file.")
    diagnose.add_argument("--cases", type=_path_argument, required=True, help="Developer-only case specification.")
    diagnose.add_argument("--repository", type=_path_argument, help="Repository containing the active local index.")
    diagnose.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    diagnose.add_argument("--top-k", type=int, default=10, help="Maximum results used for diagnosis (1-50; default: 10).")
    diagnose.add_argument("--json", action="store_true", help="Print the complete diagnosis as JSON.")
    explain = local_commands.add_parser("explain", help="Query an index and show developer context assembly reasons.")
    explain.add_argument("question", help="Question text; stored only in the local developer run record.")
    explain.add_argument("case_id", nargs="?", help="Optional case ID when explaining an evaluation run.")
    explain.add_argument("--repository", type=_path_argument, help="Select an indexed repository when multiple exist.")
    explain.add_argument("--cases", type=_path_argument, help="Developer-only case specification when explaining a case ID.")
    explain.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    explain.add_argument("--top-k", type=int, default=10, help="Maximum results (1-50; default: 10).")
    explain.add_argument("--json", action="store_true", help="Print retrieval and context diagnostics as JSON.")
    evaluate = local_commands.add_parser("evaluate", help="Measure retrieval and context quality against developer-only cases.")
    evaluate.add_argument("repository", type=_path_argument, help="Existing local Git working-tree root.")
    evaluate.add_argument("--cases", type=_path_argument, required=True, help="Developer-only JSON query case specification.")
    evaluate.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    evaluate.add_argument("--top-k", type=int, default=10, help="Maximum results per case (1-50; default: 10).")
    evaluate.add_argument("--explain", action="store_true", help="Include full result and ranking diagnostics for failed cases.")
    evaluate.add_argument("--compare", action="store_true", help="Compare with the previous developer evaluation for this repository.")
    evaluate.add_argument("--stability", action="store_true", help="Repeat each query and report ranked-result stability.")
    evaluate.add_argument("--json", action="store_true", help="Print the complete machine-readable report.")

    local_demo_parser = local_commands.add_parser(
        "demo", help="Run a generated-fixture local parser/chunker/BM25 demonstration."
    )
    local_demo_parser.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
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


def _run_local_command(options: argparse.Namespace, config: PrototypeConfig) -> dict[str, object]:
    if getattr(options, "json", False):
        from contextlib import redirect_stdout
        from io import StringIO
        with redirect_stdout(StringIO()):
            payload = _run_local_text_command(options, config)
        print(json.dumps({"notice": _DEVELOPER_MODE_NOTICE, **payload}, indent=2, sort_keys=True))
        return payload
    return _run_local_text_command(options, config)


def _run_local_text_command(options: argparse.Namespace, config: PrototypeConfig) -> dict[str, object]:
    try:
        from src.developer import DeveloperWorkspace, LocalWorkflowError, local_demo
    except ImportError as error:
        raise ValueError(
            "Developer mode requires the full pinned retrieval environment. "
            "Install requirements-lock.txt and the project, then retry."
        ) from error
    workspace = options.workspace or config.developer_workspace
    developer = DeveloperWorkspace(workspace, research_roots=_research_storage_roots(config))
    print(_DEVELOPER_MODE_NOTICE)
    if options.local_command == "demo":
        payload = local_demo()
        print("Developer demo (generated in-memory fixture; no repository or network access)")
        print(f"Parsed and chunked: {payload['chunk_count']} fixture chunks")
        print(f"Question: {payload['question']}")
        _print_local_results(payload["results"])
        return payload
    workspace_status = "existing" if workspace.exists() else "new; created only after separation checks"
    print(f"Developer workspace: {workspace.resolve()} ({workspace_status}; check local filesystem permissions)")
    if options.local_command == "inspect":
        payload = developer.inspect(options.repository, options.changes)
        inventory = payload["repository"]
        print(f"Files scanned: {inventory['files_scanned']}; included: {inventory['files_included']}; excluded: {inventory['files_excluded']}")
        for file in payload["files"]:
            print(f"  {file['file_path']}: {file['reason']}")
        print(f"Generated chunks: {payload['generated_chunk_count']}; eligibility: {payload['chunk_counts']}")
        print(f"Active index current: {payload['active_index_current']}; searchable chunks: {payload['searchable_chunk_count']}")
        for chunk in payload["chunks"]:
            print(f"  {chunk['file_path']}:{chunk['start_line']}-{chunk['end_line']} {chunk['qualified_name']}: {chunk['reason']} ({chunk['token_count']} tokens); in current index: {chunk['in_current_index']}")
        for failure in payload["parse_failures"]:
            print(f"  Parser failure: {failure['file_path']}:{failure['line'] or 0}: {failure['message']}")
        if payload["warning"]:
            print(payload["warning"])
        print(payload["coverage_note"])
        if options.changes:
            print(f"Changes: {payload['changes']}")
        print(f"Developer run: {payload['run_id']}")
        return payload
    if options.local_command == "scan":
        payload = developer.scan(options.repository)
        scan = payload["scan"]
        print(f"Repository: {scan['repository_path']}")
        print(f"Python files: {scan['eligible_python_file_count']}; code LOC: {scan['eligible_python_code_loc']}")
        print(f"Working-tree SHA-256: {scan['working_tree_sha256']}")
        _print_unsupported_files(scan["unsupported_extensions"])
        if scan["eligible_python_file_count"] == 0:
            print("Indexing unavailable: this prototype parses Python (.py) files only.")
        print(f"Developer run: {payload['run_id']} ({workspace / 'runs' / payload['run_id']})")
        return payload
    if options.local_command == "index":
        import time
        started = time.perf_counter()
        payload = developer.index(options.repository)
        print(f"Index {payload['index_status']}: {payload['index_path']}")
        print(
            f"Parsed files: {payload['parsed_python_file_count']}; chunks: {payload['chunk_count']}; "
            f"indexed: {payload['indexed_chunk_count']}; rejected: {payload['rejected_chunk_count']}"
        )
        _print_unsupported_files(payload["repository"]["unsupported_extensions"])
        print(f"Cache reuse: {payload.get('cache_reuse', False)}; "
              f"files reused/rebuilt: {payload.get('reused_file_count', 0)}/{payload.get('rebuilt_file_count', 0)}; "
              f"chunks reused/rebuilt: {payload.get('reused_chunk_count', 0)}/{payload.get('rebuilt_chunk_count', 0)}; "
              f"elapsed: {time.perf_counter() - started:.3f}s")
        if payload["parse_failure_count"]:
            print(f"Files with parse/read errors: {payload['parse_failure_count']}")
            for failure in payload["parse_failures"]:
                print(f"  {failure['file_path']}:{failure['line'] or 0}: {failure['message']}")
        print(f"Developer run: {payload['run_id']}")
        return payload
    if options.local_command == "explain" and options.case_id:
        payload = developer.explain_run(options.question, options.case_id)
        detail = payload["case"]
        print(f"Run: {options.question}\nCase: {detail['id']}\nQuery: {detail['query']}\nExpected: {detail['expected']}")
        print(f"Indexed version: {payload.get('index_state')}\nRetrieved: {detail['retrieved']}\nFailures: {detail['failure_type'] or 'none'}")
        print(f"Explanation: {detail['explanation']}")
        for row in detail.get("results", ()):
            print(f"  {row['rank']}. {row['file_path']}:{row['start_line']}-{row['end_line']} {row['qualified_name']}")
            print(f"     {row['ranking_reason']}")
        return payload
    if options.local_command == "explain" and options.cases:
        report = developer.evaluate(options.repository, options.cases, options.top_k, True)
        detail = next((item for item in report["details"] if item["id"] == options.question), None)
        if detail is None:
            raise LocalWorkflowError(f"Case '{options.question}' was not found in '{options.cases}'.")
        payload = {"status": "completed", "mode": "developer-local-case-explanation", "case": detail,
                   "repository": report["repository"], "run_id": report["run_id"]}
        print(f"Case: {detail['id']}\nQuery: {detail['query']}\nExpected: {detail['expected']}")
        print(f"Retrieved: {detail['retrieved']}\nFailures: {detail['failure_type'] or 'none'}")
        print(f"Explanation: {detail['explanation']}")
        for row in detail["results"]:
            print(f"  {row['rank']}. {row['file_path']}:{row['start_line']}-{row['end_line']} {row['qualified_name']}")
            print(f"     {row['ranking_reason']}")
        print(f"Developer run: {report['run_id']}")
        return payload
    if options.local_command in {"inspect-history", "timeline"}:
        from src.developer.observability import inspect_history, timeline
        payload = (inspect_history(developer, options.query, options.repository_id, options.limit)
                   if options.local_command == "inspect-history"
                   else timeline(developer, options.repository_id, options.note))
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize":
        from src.developer.optimization import create_candidate, show_candidates, validate_candidate, decide_candidate
        if options.action != "list" and not options.id:
            raise ValueError("Optimization action requires --id.")
        if options.action in {"list", "show"}:
            payload = show_candidates(developer, options.id)
        elif options.action == "create":
            payload = create_candidate(developer, options.id, options.problem, options.case, options.source,
                                       options.proposed_change, options.validation_method, options.supersedes)
        elif options.action == "validate":
            if not all((options.repository, options.cases, options.before)):
                raise ValueError("Validation requires --repository, --cases and --before.")
            notes = {}
            for value in options.ranking_note:
                case, separator, note = value.partition("=")
                if not separator or not case.strip() or not note.strip() or case in notes:
                    raise ValueError("Each --ranking-note must be a unique CASE=EXPLANATION.")
                notes[case] = note
            payload = validate_candidate(developer, options.id, options.repository, options.cases, options.before, notes)
        elif options.action == "register":
            from src.developer.governance import register_candidate
            if not options.owner or not options.purpose:
                raise ValueError("Lifecycle registration requires --owner and --purpose.")
            payload = register_candidate(developer, options.id, options.owner, options.purpose, options.case)
        elif options.action == "transition":
            from src.developer.governance import transition_candidate
            if not options.state or not options.note:
                raise ValueError("Lifecycle transition requires --state and --note.")
            payload = transition_candidate(developer, options.id, options.state, options.note,
                                           options.last_validation_at, options.owner)
        else:
            payload = decide_candidate(developer, options.id, "accepted" if options.action == "accept" else "rejected", options.note)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-status":
        from src.developer.governance import optimize_status
        payload = optimize_status(developer)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-archive":
        from src.developer.governance import archive_candidate
        payload = archive_candidate(developer, options.id, options.note)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-maintenance":
        from src.developer.governance import maintenance_report
        payload = maintenance_report(developer)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-audit":
        from src.developer.governance import optimize_audit
        payload = optimize_audit(developer)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-history":
        from src.developer.governance import optimize_history
        payload = optimize_history(developer, options.id)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-health":
        from src.developer.governance import optimize_health
        payload = optimize_health(developer)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-summary":
        from src.developer.governance import optimize_summary
        payload = optimize_summary(developer, options.recent_limit)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-checkpoint":
        from src.developer.governance import create_governance_checkpoint
        payload = create_governance_checkpoint(developer)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-review-create":
        from src.developer.review import create_review
        payload = create_review(developer, options.candidate_id, options.reason, options.owner,
                                options.affected_cases, options.conflict_note)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-review":
        from src.developer.review import show_reviews
        payload = show_reviews(developer, options.id)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command in {"optimize-approve", "optimize-reject", "optimize-review-defer",
                                 "optimize-review-withdraw", "optimize-review-reopen"}:
        from src.developer.review import (approve_review, defer_review, reject_review,
                                          reopen_review, withdraw_review)
        actions = {"optimize-approve": approve_review, "optimize-reject": reject_review,
                   "optimize-review-defer": defer_review, "optimize-review-withdraw": withdraw_review,
                   "optimize-review-reopen": reopen_review}
        if options.local_command == "optimize-approve":
            payload = approve_review(developer, options.id, options.reviewer, options.reason,
                                     options.conflict_note)
        else:
            payload = actions[options.local_command](developer, options.id, options.reviewer, options.reason)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-policy-check":
        from src.developer.review import policy_check
        payload = policy_check(developer, options.id)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "optimize-check":
        from src.developer.safety import detect_conflicts
        payload = detect_conflicts(developer, options.repository_id)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "rollback":
        from src.developer.safety import record_rollback, show_rollback
        if options.action == "record":
            if not options.id:
                raise ValueError("Rollback record requires --id.")
            payload = record_rollback(developer, options.id, options.note)
        else:
            payload = show_rollback(developer, options.id)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "regression":
        payload = developer.regression(options.repository, options.cases, options.baseline,
                                       options.create_baseline, options.top_k)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command == "diagnose":
        payload = developer.diagnose(options.case_id, options.cases, options.repository, options.top_k)
        print(f"Case: {payload['case_id']}\nQuery: {payload['query']}")
        print(f"Index freshness: {payload['index_freshness']['status']}")
        print(f"Expected evidence: {payload['expected_evidence']}")
        print(f"Available evidence: {payload['available_evidence']}")
        print(f"Missing evidence: {payload['missing_evidence'] or 'none'}")
        for cause in payload["likely_causes"]:
            print(f"Likely cause: {cause}")
        if "run_id" in payload:
            print(f"Developer run: {payload['run_id']}")
        return payload
    if options.local_command == "analyze-context":
        payload = developer.analyze_context(
            options.question, options.repository, options.top_k, options.cases, options.case_id
        )
        print(f"Selected files: {payload['selected_files']}")
        print(f"Missing expected evidence: {payload['missing_expected_evidence']}")
        print(f"Extra context: {payload['extra_context']}")
        print(f"Duplicate context: {payload['duplicate_context']}")
        print(f"Developer run: {payload['run_id']}")
        return payload
    if options.local_command == "compare":
        if options.before or options.after:
            if not options.before or not options.after or options.question or options.repository:
                raise ValueError("Saved comparison requires --before and --after; use --repository-id to select a repository.")
            from src.developer.optimization import compare_versions
            payload = compare_versions(developer, options.before, options.after, options.repository_id)
            print(json.dumps(payload, indent=2, sort_keys=True))
            return payload
        if not options.question or options.repository_id:
            raise ValueError("Provide a query or both --before and --after versions.")
        payload = developer.compare(options.question, options.repository, options.top_k)
        comparison = payload["comparison"]
        print(f"Comparison status: {comparison['status']}")
        print(f"Added files: {comparison['added_files']}")
        print(f"Removed files: {comparison['removed_files']}")
        print(f"Ranking changes: {comparison['ranking_changes']}")
        print(f"Explanation changes: {comparison['explanation_changes']}")
        print(comparison["note"])
        print(f"Developer run: {payload['run_id']}")
        return payload
    if options.local_command in {"query", "explain", "trace"}:
        payload = (developer.trace(options.question, options.repository, options.top_k)
                   if options.local_command == "trace"
                   else developer.query(options.question, options.repository, options.top_k))
        print(f"Repository: {payload['repository']['repository_path']}")
        print(f"Working-tree SHA-256: {payload['repository']['working_tree_sha256']}")
        print(f"Retrieved {len(payload['results'])} chunks; strategy: dense + BM25 + RRF + developer navigation preferences")
        if options.local_command == "trace":
            for row in payload["trace"]["selected_results"]:
                print(f"{row['rank']}. {row['file']} â€” {row['symbol']}")
                print(f"   Evidence: {', '.join(row['evidence']) or 'no direct match signal'}")
                print(f"   Ranking factors: {', '.join(row['ranking_factors'])}")
                print(f"   Relationships: {row['relationship_path'] or 'none observed'}")
                print(f"   Context expansion: {row['context_expansion_reason']}")
            print(f"Confidence: {payload['confidence']['level']} â€” {', '.join(payload['confidence']['signals']) or 'no positive evidence signals'}")
            print(f"Confidence limitations: {', '.join(payload['confidence']['limitations']) or 'none reported'}")
        else:
            _print_local_results(payload["results"])
            if payload.get("confidence"):
                print(f"Retrieval confidence: {payload['confidence']['level']} ({', '.join(payload['confidence']['signals']) or 'no positive signals'})")
        if options.local_command == "explain":
            print(f"Context files: {len(payload['context']['files'])}; expansion decisions: {len(payload['context']['expansion_decisions'])}")
            print(f"Excluded context: {payload['context']['excluded_context']}")
        print(f"Developer run: {payload['run_id']}")
        return payload
    if options.local_command == "evaluate":
        payload = developer.evaluate(options.repository, options.cases, options.top_k, options.explain, options.compare, options.stability)
        print(f"Developer evaluation: {payload['queries']} queries")
        print(f"File hits: {payload['file_hits']}; symbol hits: {payload['symbol_hits']}")
        print(f"Context completeness: {payload['context_completeness']:.3f}; noise rate: {payload['noise_rate']:.3f}; explanation coverage: {payload['explanation_coverage']:.3f}")
        for detail in payload["details"]:
            missing = detail["missing_files"] + detail["missing_symbols"] + detail["missing_relationships"]
            if missing:
                print(f"  {detail['id']}: missing {', '.join(missing)}; extra files: {', '.join(detail['extra_files']) or 'none'}")
                if options.explain and detail.get("results"):
                    for row in detail["results"]:
                        print(f"    {row['file_path']}:{row['start_line']}-{row['end_line']} {row['qualified_name']}: {row['ranking_reason']}")
        if options.compare:
            print(f"Comparison: {json.dumps(payload.get('comparison', {}), sort_keys=True)}")
        if options.stability:
            print(f"Stability: {json.dumps(payload.get('stability', {}), sort_keys=True)}")
        print(f"Developer run: {payload['run_id']}")
        return payload
    raise LocalWorkflowError(f"Unsupported local command: {options.local_command}")


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
        if options.command == "local":
            _run_local_command(options, config)
            return 0
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
        prefix = "prototype local" if options.command == "local" else "prototype"
        print(f"{prefix}: error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
