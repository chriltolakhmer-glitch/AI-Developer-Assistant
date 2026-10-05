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
            "Developer commands: local scan, local inspect, local change-impact, local plan-change, local draft-patch, local index, local query, local trace, local diagnose, "
            "local analyze-context, local compare, local regression, local explain, local evaluate, local demo.\n"
            f"{_DEVELOPER_MODE_NOTICE}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Research: prototype validate | prototype evaluate --json | prototype reproduce RUN_ID\n"
            "Developer: prototype local scan REPOSITORY | prototype local change-impact REPOSITORY | prototype local plan-change REPOSITORY --goal TEXT | prototype local draft-patch REPOSITORY --proposal-run-id RUN --patch-file DIFF | prototype local index REPOSITORY | "
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
    from src.developer_testing import add_arguments
    for name in ("test", "test-timing"):
        test_command = local_commands.add_parser(name, help="Select developer tests with development, phase, or exhaustive validation gates.")
        add_arguments(test_command)
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

    change_impact = local_commands.add_parser(
        "change-impact", help="Plan change-aware context and affected tests without modifying source."
    )
    change_impact.add_argument("repository", type=_path_argument, help="Existing local Git working-tree root.")
    change_impact.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    change_impact.add_argument("--base", help="Include committed changes after this commit plus current worktree changes.")
    change_impact.add_argument("--question", help="Retrieve relevant indexed code only when the index is current.")
    change_impact.add_argument("--top-k", type=int, default=10, help="Maximum retrieval results (1-50; default: 10).")
    change_impact.add_argument("--json", action="store_true", help="Print the stable change-impact payload as JSON.")

    plan_change = local_commands.add_parser(
        "plan-change", help="Create an evidence-grounded implementation plan without modifying source."
    )
    plan_change.add_argument("repository", type=_path_argument, help="Existing local Git working-tree root.")
    plan_change.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    plan_change.add_argument("--base", help="Include committed changes after this commit plus current worktree changes.")
    plan_change.add_argument("--goal", required=True, help="Developer goal used as the retrieval question.")
    plan_change.add_argument("--top-k", type=int, default=10, help="Maximum retrieval results (1-50; default: 10).")
    plan_change.add_argument("--json", action="store_true", help="Print the stable implementation-plan payload as JSON.")

    draft_patch = local_commands.add_parser(
        "draft-patch", help="Validate and record a supplied unified-diff candidate without applying it."
    )
    draft_patch.add_argument("repository", type=_path_argument, help="Repository matching the Phase 66 proposal.")
    draft_patch.add_argument("--proposal-run-id", required=True, help="Run ID containing the Phase 66 proposal.")
    draft_patch.add_argument("--patch-file", required=True, type=_path_argument, help="Externally supplied unified diff candidate.")
    draft_patch.add_argument("--workspace", type=_path_argument, help="Developer workspace override.")
    draft_patch.add_argument("--json", action="store_true", help="Print the stable PatchDraft payload as JSON.")

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
    optimize.add_argument("--retrieval-settings", type=json.loads, help='Developer settings JSON, e.g. {"relationship_factor": 1.5}.')
    optimize.add_argument("--proposed-change")
    optimize.add_argument("--validation-method")
    optimize.add_argument("--supersedes", help="Prior rejected or failed candidate ID; preserves its pending review and history.")
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

    for command in ("readiness", "readiness-audit", "readiness-record-create", "readiness-history", "readiness-evidence",
                    "readiness-review", "readiness-transition", "readiness-close", "readiness-followup", "readiness-followup-complete"):
        readiness = local_commands.add_parser(command, help="Developer end-to-end readiness and explicit manual closure.")
        reports = {"readiness", "readiness-audit", "readiness-history"}
        if command in {"readiness", "readiness-audit"}:
            readiness.add_argument("id", nargs="?", help="Operational readiness ID.")
            readiness.add_argument("--deployment-id")
            readiness.add_argument("--decision-id")
        elif command == "readiness-evidence":
            readiness.add_argument("id", nargs="?", help="Operational readiness ID; defaults to the latest record.")
        else:
            readiness.add_argument("id", help="Deployment ID for create; operational readiness ID otherwise.")
        if command not in reports:
            if command == "readiness-evidence":
                readiness.add_argument("--reason", default="Capture end-to-end readiness evidence references")
            else:
                readiness.add_argument("--reason", required=True)
            readiness.add_argument("--actor", default="developer")
        if command in {"readiness-record-create", "readiness-review", "readiness-close", "readiness-followup", "readiness-followup-complete"}:
            readiness.add_argument("--owner", required=True)
        if command == "readiness-record-create":
            readiness.add_argument("--decision-id", required=True)
        if command == "readiness-transition":
            readiness.add_argument("state", choices=("not_ready", "review_required", "ready_for_manual_decision", "approved"))
        if command in {"readiness-transition", "readiness-close"}:
            readiness.add_argument("--confirm", action="store_true", help="Explicit human confirmation of approval/closure.")
        if command == "readiness-close":
            readiness.add_argument("--outstanding-reason")
        if command in {"readiness-review", "readiness-followup-complete"}:
            readiness.add_argument("--note", required=True)
        if command == "readiness-followup":
            readiness.add_argument("--component", required=True, choices=("promotion", "configuration", "deployment", "operations", "recovery", "assurance", "maturity", "evolution", "governance", "validation", "evidence"))
            readiness.add_argument("--manual-action", required=True)
            readiness.add_argument("--due-at", required=True, help="ISO timestamp with timezone.")
        if command == "readiness-followup-complete":
            readiness.add_argument("followup_id")
        readiness.add_argument("--workspace", type=_path_argument)
        readiness.add_argument("--json", action="store_true")

    for command in ("governance-decisions", "governance-actions", "governance-exceptions", "governance-decision", "governance-followup", "governance-close-check",
                    "governance-decision-create", "governance-decision-review", "governance-decision-transition", "governance-decision-assign",
                    "governance-action-add", "governance-action-transition", "governance-action-defer", "governance-action-assign",
                    "governance-exception-add", "governance-exception-transition", "governance-exception-assign"):
        operation = local_commands.add_parser(command, help="Developer-only governance decisions and operational follow-up.")
        reports = {"governance-decisions", "governance-actions", "governance-exceptions", "governance-decision", "governance-followup", "governance-close-check"}
        if command not in reports or command == "governance-decision":
            operation.add_argument("id", help="Governance ID for creation; otherwise decision ID.")
        if command not in reports:
            operation.add_argument("--reason", required=True)
            operation.add_argument("--actor", default="developer")
        if command in {"governance-decision-create", "governance-decision-assign", "governance-action-add", "governance-action-assign", "governance-exception-add", "governance-exception-assign"}:
            operation.add_argument("--owner", required=True)
        if command == "governance-decision-create":
            operation.add_argument("--decision", required=True)
        if command in {"governance-action-add", "governance-exception-add"}:
            operation.add_argument("--description", required=True)
        if command in {"governance-action-add", "governance-action-assign"}:
            operation.add_argument("--due-date", required=True)
        if command in {"governance-action-transition", "governance-action-defer", "governance-action-assign"}:
            operation.add_argument("action_id")
        if command == "governance-action-defer":
            operation.add_argument("--until", required=True)
        if command in {"governance-exception-transition", "governance-exception-assign"}:
            operation.add_argument("exception_id")
        if command == "governance-exception-add":
            operation.add_argument("--expires-at", required=True)
            operation.add_argument("--action-id")
        if command == "governance-decision-transition":
            operation.add_argument("state", choices=("open", "reviewing", "decided", "deferred", "closed"))
        if command == "governance-action-transition":
            operation.add_argument("state", choices=("open", "in_progress", "blocked", "completed", "cancelled"))
        if command == "governance-exception-transition":
            operation.add_argument("state", choices=("open", "accepted", "mitigated", "expired", "closed"))
        if command in {"governance-decision-review", "governance-decision-transition", "governance-action-transition", "governance-action-defer", "governance-exception-transition"}:
            operation.add_argument("--note", required=True)
        if command in {"governance-decision-review", "governance-action-transition", "governance-exception-transition"}:
            operation.add_argument("--evidence", action="append", default=[])
            operation.add_argument("--closure-reason")
        operation.add_argument("--workspace", type=_path_argument)
        operation.add_argument("--json", action="store_true")

    for command in ("governance-status", "governance-history", "governance-review", "governance-dependencies", "governance-plan-review",
                    "governance-create", "governance-update", "governance-transition", "governance-record-review",
                    "governance-roadmap-add", "governance-roadmap-update", "governance-roadmap-transition", "governance-dependency-review"):
        strategic = local_commands.add_parser(command, help="Developer-only recovery strategic governance.")
        reports = {"governance-status", "governance-history", "governance-review", "governance-dependencies", "governance-plan-review"}
        if command not in {"governance-status", "governance-dependencies", "governance-plan-review"}:
            strategic.add_argument("id", help="Objective description for create; otherwise governance ID.")
        if command not in reports:
            strategic.add_argument("--reason", required=True)
            strategic.add_argument("--actor", default="developer")
        if command in {"governance-create", "governance-update"}:
            if command == "governance-update":
                strategic.add_argument("--objective", required=True)
            strategic.add_argument("--owner", required=True)
            strategic.add_argument("--capability", action="append", required=True)
            strategic.add_argument("--evolution-id", action="append", default=[])
            strategic.add_argument("--dependency", action="append", default=[])
            strategic.add_argument("--note", action="append", default=[])
            strategic.add_argument("--risk", action="append", default=[])
        if command in {"governance-roadmap-add", "governance-roadmap-update"}:
            strategic.add_argument("--description", required=True)
            strategic.add_argument("--owner", required=True)
            strategic.add_argument("--target-period", required=True)
            strategic.add_argument("--dependency", action="append", default=[])
        if command in {"governance-roadmap-update", "governance-roadmap-transition"}:
            strategic.add_argument("--roadmap-id", required=True)
        if command == "governance-transition":
            strategic.add_argument("state", choices=("planned", "reviewing", "approved", "active", "completed", "retired"))
        if command == "governance-roadmap-transition":
            strategic.add_argument("state", choices=("proposed", "scheduled", "active", "completed", "deferred"))
        if command == "governance-dependency-review":
            strategic.add_argument("dependency")
            strategic.add_argument("resolution", choices=("resolved", "unresolved"))
            strategic.add_argument("--roadmap-id")
        if command in {"governance-transition", "governance-record-review", "governance-roadmap-transition", "governance-dependency-review"}:
            strategic.add_argument("--note", required=True)
        strategic.add_argument("--workspace", type=_path_argument)
        strategic.add_argument("--json", action="store_true")

    for command in ("evolution-status", "evolution-history", "evolution-impact", "evolution-review", "evolution-plan",
                    "evolution-create", "evolution-transition", "evolution-impact-add", "evolution-plan-add"):
        evolution = local_commands.add_parser(command, help="Developer-only manual recovery evolution management.")
        if command not in {"evolution-status", "evolution-plan"}:
            evolution.add_argument("id", help="Capability label for create; otherwise evolution ID.")
        if command in {"evolution-create", "evolution-transition", "evolution-impact-add", "evolution-plan-add"}:
            evolution.add_argument("--reason", required=True)
            evolution.add_argument("--actor", default="developer")
        if command in {"evolution-create", "evolution-plan-add"}:
            evolution.add_argument("--owner", required=True)
        if command == "evolution-create":
            evolution.add_argument("--change-type", default="improvement")
        if command == "evolution-transition":
            evolution.add_argument("state", choices=("planned", "reviewing", "approved", "implemented", "verified", "retired"))
            evolution.add_argument("--note", required=True)
        if command == "evolution-impact-add":
            evolution.add_argument("--capability", action="append", required=True)
            evolution.add_argument("--maturity-id", action="append", required=True)
            evolution.add_argument("--finding", action="append", default=[])
            evolution.add_argument("--note", action="append", default=[])
            evolution.add_argument("--risk", action="append", default=[])
        if command == "evolution-plan-add":
            evolution.add_argument("--improvement", action="append", required=True)
            evolution.add_argument("--dependency", action="append", default=[])
            evolution.add_argument("--milestone", action="append", required=True)
            evolution.add_argument("--supersedes")
        evolution.add_argument("--workspace", type=_path_argument)
        evolution.add_argument("--json", action="store_true")

    for command in ("maturity-status", "maturity-history", "maturity-review", "maturity-readiness", "maturity-plan",
                    "maturity-create", "maturity-assess", "maturity-assign", "maturity-transition", "maturity-plan-add", "maturity-plan-review"):
        maturity = local_commands.add_parser(command, help="Developer recovery capability maturity and manual planning.")
        if command not in {"maturity-status", "maturity-readiness", "maturity-plan"}:
            maturity.add_argument("id", help="Area for create/review; otherwise maturity ID.")
        if command in {"maturity-create", "maturity-assess", "maturity-assign", "maturity-transition", "maturity-plan-add", "maturity-plan-review"}:
            maturity.add_argument("--reason", required=True)
            maturity.add_argument("--actor", default="developer")
        if command in {"maturity-create", "maturity-assign"}:
            maturity.add_argument("--owner", required=True)
        if command == "maturity-create":
            maturity.add_argument("--assurance-id", action="append", required=True)
        if command == "maturity-assess":
            maturity.add_argument("capability")
            maturity.add_argument("--gap", action="append")
            maturity.add_argument("--note", action="append")
        if command == "maturity-transition":
            maturity.add_argument("level", choices=("initial", "defined", "managed", "measured", "improving"))
        if command == "maturity-plan-add":
            maturity.add_argument("--improvement", action="append", required=True)
            maturity.add_argument("--capability", action="append", required=True)
            maturity.add_argument("--finding", action="append", default=[])
            maturity.add_argument("--supersedes")
        if command == "maturity-plan-review":
            maturity.add_argument("plan_id")
            maturity.add_argument("state", choices=("reviewed", "deferred", "completed"))
            maturity.add_argument("--note", required=True)
        maturity.add_argument("--workspace", type=_path_argument)
        maturity.add_argument("--json", action="store_true")

    for command in ("assurance-operations", "assurance-findings", "assurance-review-cycle", "assurance-coverage",
                    "assurance-operation-create", "assurance-operation-review", "assurance-operation-transition",
                    "assurance-operation-assign", "assurance-operation-note"):
        operation = local_commands.add_parser(command, help="Developer-only assurance operations and manual review cycles.")
        if command not in {"assurance-operations", "assurance-findings", "assurance-coverage"}:
            operation.add_argument("id", help="Assurance ID for create/review-cycle; otherwise operation ID.")
        if command.startswith("assurance-operation-"):
            operation.add_argument("--reason", required=True)
            operation.add_argument("--actor", default="developer")
        if command in {"assurance-operation-create", "assurance-operation-assign"}:
            operation.add_argument("--owner", required=True)
        if command == "assurance-operation-transition":
            operation.add_argument("state", choices=("reviewing", "improved", "accepted", "closed"))
        if command == "assurance-operation-note":
            operation.add_argument("--note", required=True)
        operation.add_argument("--workspace", type=_path_argument)
        operation.add_argument("--json", action="store_true")

    for command in ("assurance-status", "assurance-history", "assurance-review", "assurance-check", "assurance-improvements",
                    "assurance-register", "assurance-transition", "assurance-assign", "assurance-schedule", "assurance-note", "assurance-record-check"):
        governance = local_commands.add_parser(command, help="Developer-only continuous recovery governance.")
        if command not in {"assurance-status", "assurance-check", "assurance-improvements"}:
            governance.add_argument("id")
        if command in {"assurance-register", "assurance-transition", "assurance-assign", "assurance-schedule", "assurance-note", "assurance-record-check"}:
            governance.add_argument("--reason", required=True)
            governance.add_argument("--actor", default="developer")
        if command in {"assurance-register", "assurance-assign"}:
            governance.add_argument("--owner", required=True)
            governance.add_argument("--responsibility", required=True)
        if command in {"assurance-register", "assurance-schedule"}:
            governance.add_argument("--every-hours", type=int, required=True)
        if command == "assurance-transition":
            governance.add_argument("state", choices=("active", "paused", "expired", "retired"))
        if command == "assurance-note":
            governance.add_argument("--kind", choices=("review", "improvement"), required=True)
            governance.add_argument("--note", required=True)
        if command == "assurance-record-check":
            governance.add_argument("--verification-id", required=True)
        governance.add_argument("--workspace", type=_path_argument)
        governance.add_argument("--json", action="store_true")

    for command in ("recovery-assurance", "recovery-evidence", "recovery-history-analysis", "recovery-verify-history",
                    "assurance-create", "assurance-verify", "assurance-expire"):
        assurance = local_commands.add_parser(command, help="Inspect developer recovery assurance and retain evidence.")
        if command != "recovery-history-analysis":
            assurance.add_argument("id", help="Scenario ID for reports/create; assurance ID for verify/expire.")
        if command in {"assurance-create", "assurance-expire"}:
            assurance.add_argument("--reason", required=True)
        elif command == "assurance-verify":
            assurance.add_argument("--reason", default="Verify recovery assurance evidence")
        if command.startswith("assurance-"):
            assurance.add_argument("--actor", default="developer")
        if command == "assurance-create":
            assurance.add_argument("--owner", default="developer")
            assurance.add_argument("--valid-for-hours", type=int, default=24, help="Evidence validity, 1 to 8760 hours (default 24).")
        assurance.add_argument("--workspace", type=_path_argument)
        assurance.add_argument("--json", action="store_true")

    for command in ("disaster-create", "disaster-status", "disaster-inspect", "disaster-check",
                    "disaster-test", "disaster-retire", "continuity-status"):
        disaster = local_commands.add_parser(command, help="Preserve developer continuity and validate recovery references.")
        if command not in {"disaster-status", "continuity-status"}:
            disaster.add_argument("id", help="Deployment ID for create; otherwise disaster scenario ID.")
        if command in {"disaster-create", "disaster-retire"}:
            disaster.add_argument("--reason", required=True)
        elif command == "disaster-test":
            disaster.add_argument("--reason", default="Validate recovery references without execution")
        if command in {"disaster-create", "disaster-retire", "disaster-test"}:
            disaster.add_argument("--actor", default="developer")
        if command == "disaster-create":
            disaster.add_argument("--owner", default="developer")
            disaster.add_argument("--type", dest="scenario_type", default="configuration_failure",
                                  choices=("configuration_failure", "deployment_failure", "rollback_unavailable", "history_loss"))
            disaster.add_argument("--plan-id", help="Recovery plan for this deployment; defaults to its latest plan.")
            disaster.add_argument("--step", action="append", help="Manual restoration instruction; repeat to replace default steps.")
        disaster.add_argument("--workspace", type=_path_argument)
        disaster.add_argument("--json", action="store_true")

    for command in ("reliability-check", "recovery-plan-create", "recovery-plan-status",
                    "recovery-plan-inspect", "recovery-verify", "readiness-create",
                    "readiness-check", "readiness-expire", "readiness-status"):
        reliability = local_commands.add_parser(command, help="Prepare developer readiness and recovery without execution.")
        if command not in {"recovery-plan-status", "readiness-status"}:
            reliability.add_argument("id", help="Deployment ID for create/reliability; otherwise plan or readiness ID.")
        if command in {"recovery-plan-create", "readiness-create", "readiness-expire"}:
            reliability.add_argument("--reason", required=True)
        elif command in {"recovery-verify", "readiness-check"}:
            reliability.add_argument("--reason", default="Verify recovery prerequisites" if command == "recovery-verify"
                                     else "Check deployment readiness")
        if command in {"recovery-plan-create", "readiness-create", "readiness-expire", "recovery-verify", "readiness-check"}:
            reliability.add_argument("--actor", default="developer")
        if command == "recovery-plan-create":
            reliability.add_argument("--owner", default="developer")
        reliability.add_argument("--workspace", type=_path_argument)
        reliability.add_argument("--json", action="store_true")

    for command in ("incident-create", "incident-status", "incident-inspect", "incident-investigate",
                    "incident-resolve", "incident-close", "incident-diff", "recovery-history", "deploy-health"):
        operation = local_commands.add_parser(command, help="Track developer deployment operations without recovery actions.")
        if command == "incident-diff":
            operation.add_argument("incident_a")
            operation.add_argument("incident_b")
        elif command not in {"incident-status", "recovery-history"}:
            operation.add_argument("id", help="Deployment ID for create/health; otherwise incident operation ID.")
        if command in {"incident-create", "incident-investigate", "incident-resolve", "incident-close"}:
            operation.add_argument("--reason", required=True)
            operation.add_argument("--actor", default="developer")
        if command == "incident-create":
            operation.add_argument("--owner", default="developer")
        if command == "incident-resolve":
            operation.add_argument("--recovery-action", required=True, help="Description of the manually completed recovery.")
            operation.add_argument("--rollback-reference", help="Existing rollback audit event ID for this deployment.")
        operation.add_argument("--workspace", type=_path_argument)
        operation.add_argument("--json", action="store_true")

    for command in ("deploy-status", "deploy-diff", "deploy-stage", "deploy-validate",
                    "deploy-audit", "deploy-governance-check", "deploy-history", "deploy-inspect",
                    "deploy-activate", "deploy-pause", "deploy-resume", "deploy-retire", "deploy-rollback"):
        deployment = local_commands.add_parser(command, help="Control developer deployment references.")
        if command == "deploy-diff":
            deployment.add_argument("deployment_a")
            deployment.add_argument("deployment_b")
        elif command in {"deploy-audit", "deploy-governance-check", "deploy-inspect"}:
            deployment.add_argument("id", help="Deployment ID to investigate without changes.")
        elif command not in {"deploy-status", "deploy-history"}:
            deployment.add_argument("id", help="Configuration ID for stage; otherwise deployment ID.")
            deployment.add_argument("--reason", required=True)
            deployment.add_argument("--actor", default="developer")
        deployment.add_argument("--workspace", type=_path_argument)
        deployment.add_argument("--json", action="store_true")

    for command in ("config-status", "config-history", "config-diff", "config-create",
                    "config-validate", "config-activate", "config-retire", "config-rollback"):
        configuration = local_commands.add_parser(command, help="Manage developer configuration snapshots.")
        if command == "config-diff":
            configuration.add_argument("version_a", type=int)
            configuration.add_argument("version_b", type=int)
        elif command not in {"config-status", "config-history"}:
            configuration.add_argument("id", help="Source promotion ID for create; otherwise configuration ID.")
            configuration.add_argument("--reason", required=True, help="Reason recorded in configuration history.")
            configuration.add_argument("--actor", default="developer")
        configuration.add_argument("--workspace", type=_path_argument)
        configuration.add_argument("--json", action="store_true")

    for command in ("optimize-promote", "optimize-promotion-status", "optimize-retire",
                    "optimize-promote-rollback", "optimize-promotion-check"):
        promotion = local_commands.add_parser(command, help="Manage developer retrieval promotions.")
        if command in {"optimize-promote", "optimize-retire", "optimize-promote-rollback"}:
            promotion.add_argument("id", help="Candidate or promotion ID.")
        promotion.add_argument("--workspace", type=_path_argument)
        promotion.add_argument("--json", action="store_true")

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
    if options.local_command == "change-impact":
        from src.developer.change_impact import analyze_change_impact
        payload = analyze_change_impact(
            developer, options.repository, base=options.base,
            question=options.question, top_k=options.top_k,
        )
        repository = payload["repository"]
        print(f"Repository: {repository['repository_path']}")
        print(f"Commit: {repository['current_commit']}; status: {repository['status']}; "
              f"index: {payload['index_freshness']['status']}")
        print("Changes:")
        if payload["changes"]["files"]:
            for row in payload["changes"]["files"]:
                rename = f" (from {row['old_path']})" if row.get("old_path") else ""
                print(f"  {row['change_type']}: {row['path']}{rename}")
        else:
            print("  none")
        print("Affected symbols:")
        for row in payload["symbols"]:
            print(f"  {row['change_type']}: {row['file_path']}:{row['start_line']}-{row['end_line']} "
                  f"{row['qualified_symbol']}")
        if not payload["symbols"]:
            print("  none")
        print("Potential static impact:")
        for row in payload["relationships"]:
            print(f"  {row['source_file']}:{row['source_symbol']} {row['relationship']} "
                  f"{row['target_file']}:{row['target_symbol']}")
        print(f"Unresolved relationships: {len(payload['unresolved_relationships'])}")
        if options.question:
            print(f"Relevant context: {payload['retrieval']['status']}; "
                  f"{len(payload['retrieval']['query_evidence'])} retrieved results")
        tests = payload["tests"]
        print(f"Affected tests: {len(tests['selected_tests'])}; tier: {tests['tier']}; executed: no")
        for selector in tests["selectors"]:
            print(f"  {selector}")
        print(f"Uncertainty: {'yes' if tests['uncertain'] else 'no'}")
        print("Recommended next actions:")
        for action in payload["recommended_actions"]:
            label = action.get("command", action.get("tier", action["action"]))
            print(f"  {label}: {action.get('reason', action['action'])}")
        print(f"Developer run: {payload['run_id']}")
        return payload
    if options.local_command == "plan-change":
        from src.developer.implementation_planning import plan_change
        payload = plan_change(
            developer, options.repository, goal=options.goal,
            base=options.base, top_k=options.top_k,
        )
        freshness = payload["change_impact"]["index_freshness"]["status"]
        print(f"Goal: {payload['goal']}")
        print(f"Repository: {payload['repository']['repository_path']}")
        print(f"Plan status: {payload['status']}; index: {freshness}")
        print("Current changes:")
        changes = payload["change_impact"]["changes"]["files"]
        if changes:
            for row in changes:
                print(f"  {row['change_type']}: {row['path']}")
        else:
            print("  none")
        print("Likely implementation targets:")
        for row in payload["implementation_targets"]:
            location = f":{row['start_line']}-{row['end_line']}" if row["start_line"] else ""
            symbol = f" {row['qualified_symbol']}" if row["qualified_symbol"] else ""
            print(f"  {row['role']}: {row['file_path']}{location}{symbol}")
            print(f"    Why: {'; '.join(row['reasons'])}")
        if not payload["implementation_targets"]:
            print("  none; manual review required")
        print("Behavior to preserve:")
        for row in payload["preserved_behavior"]:
            print(f"  {row['statement']}")
        if not payload["preserved_behavior"]:
            print("  none established by current evidence")
        proposal = payload["proposed_action"]
        print("Proposed action:")
        print(f"  status: {proposal['status']}")
        print(f"  execution allowed: {'yes' if proposal['execution_allowed'] else 'no'}")
        print(f"  human approval required: {'yes' if proposal['authority_required'] == 'human_approval_required' else 'no'}")
        print(f"  proposal ID: {proposal['action_id']}")
        print("Suggested implementation steps:")
        for row in payload["implementation_steps"]:
            print(f"  {row['order']}. {row['action']}")
        tests = payload["tests"]
        print(f"Tests: {len(tests['selected_tests'])} selected; tier: {tests['tier']}; executed: no")
        for row in payload["tests_to_update_or_review"]:
            print(f"  {row['classification']}: {row.get('test') or row.get('target', 'human decision')} — {row['reason']}")
        print("Validation sequence:")
        for row in payload["recommended_validation"]:
            print(f"  {row['order']}. {row['selector']}")
        print("Unresolved evidence:")
        for row in payload["unresolved_evidence"]:
            print(f"  {row['type']}: {row['action']}")
        print("Limitations:")
        for limitation in payload["limitations"]:
            print(f"  {limitation}")
        actions = payload["change_impact"]["recommended_actions"]
        print("Recommended next action:")
        print(f"  {actions[0].get('command', actions[0].get('action')) if actions else 'Review the plan before editing source.'}")
        print(f"Developer run: {payload['run_id']}")
        return payload
    if options.local_command == "draft-patch":
        from src.developer.patch_drafting import SuppliedPatchGenerator, draft_patch
        proposal_run = developer._contained(workspace / "runs" / options.proposal_run_id / "results.json")
        if not proposal_run.is_file():
            raise LocalWorkflowError(f"Phase 66 proposal run was not found in this developer workspace: {options.proposal_run_id}")
        proposal_payload = json.loads(proposal_run.read_text(encoding="utf-8"))
        patch_path = options.patch_file.resolve()
        if patch_path.is_relative_to(Path(options.repository).resolve()):
            raise LocalWorkflowError("Candidate patch file must be outside the target repository.")
        patch_text = patch_path.read_text(encoding="utf-8")
        payload = draft_patch(developer, options.repository, proposal_payload.get("proposed_action"),
                              SuppliedPatchGenerator(patch_text))
        print("PATCH DRAFT — NOT APPLIED — HUMAN REVIEW REQUIRED")
        print(f"Patch ID: {payload['patch_id']}")
        print(f"Proposal ID: {payload['source_action_id']}")
        print(f"Repository: {payload['repository_id']} at {payload['current_commit']}")
        print(f"Status: {payload['status']}; apply allowed: no; execution allowed: no")
        print("Target paths: " + (", ".join(payload['candidate_paths']) or "none"))
        print("Unified diff:")
        print(payload["patch_text"] or "(no valid patch retained)")
        print("Unresolved evidence:")
        for row in payload["unresolved_evidence"]:
            print(f"  {row}")
        print("Recommended validation:")
        for row in payload["validation_requirements"]:
            print(f"  {row}")
        print(f"Developer run: {payload['run_id']}")
        return payload
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
                                       options.proposed_change, options.validation_method, options.supersedes,
                                       options.retrieval_settings, owner=options.owner or "developer",
                                       purpose=options.purpose or options.problem)
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
    if options.local_command in {"readiness", "readiness-audit", "readiness-record-create", "readiness-history", "readiness-evidence",
                                 "readiness-review", "readiness-transition", "readiness-close", "readiness-followup", "readiness-followup-complete"}:
        from src.developer import readiness
        command = options.local_command
        if command == "readiness":
            if options.id and (options.deployment_id or options.decision_id):
                raise LocalWorkflowError("Use a readiness ID or explicit lifecycle selectors, not both")
            payload = readiness.status(developer, options.id, options.deployment_id, options.decision_id)
        elif command == "readiness-audit":
            if options.id:
                if options.deployment_id or options.decision_id:
                    raise LocalWorkflowError("Use a readiness ID or explicit lifecycle selectors, not both")
                record = readiness.history(developer, options.id)["record"]
                payload = readiness.audit(developer, record["deployment_id"], record["decision_id"])
            else:
                payload = readiness.audit(developer, options.deployment_id, options.decision_id)
        elif command == "readiness-record-create":
            payload = readiness.create(developer, options.id, options.decision_id, options.owner, options.reason, options.actor)
        elif command == "readiness-history":
            payload = readiness.history(developer, options.id)
        elif command == "readiness-evidence":
            payload = readiness.evidence(developer, options.id, options.reason, options.actor)
        elif command == "readiness-review":
            payload = readiness.review(developer, options.id, options.owner, options.note, options.reason, options.actor)
        elif command == "readiness-transition":
            payload = readiness.transition(developer, options.id, options.state, options.reason, options.confirm, options.actor)
        elif command == "readiness-close":
            payload = readiness.close(developer, options.id, options.owner, options.reason, options.confirm, options.outstanding_reason, options.actor)
        elif command == "readiness-followup":
            payload = readiness.followup(developer, options.id, options.owner, options.component, options.manual_action, options.due_at, options.reason, options.actor)
        else:
            payload = readiness.complete_followup(developer, options.id, options.followup_id, options.owner, options.note, options.reason, options.actor)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command.startswith(("governance-decision", "governance-action", "governance-exception")) or options.local_command in {"governance-followup", "governance-close-check"}:
        from src.developer import governance_operations as operations
        command = options.local_command.removeprefix("governance-")
        if command in {"decisions", "actions", "exceptions", "followup", "close-check"}:
            payload = getattr(operations, command.replace("-", "_"))(developer)
        elif command == "decision":
            payload = operations.decision(developer, options.id)
        elif command == "decision-create":
            payload = operations.create(developer, options.id, options.decision, options.owner, options.reason, options.actor)
        elif command == "decision-review":
            payload = operations.record_review(developer, options.id, options.note, options.evidence, options.closure_reason, options.reason, options.actor)
        elif command == "decision-transition":
            payload = operations.transition(developer, options.id, options.state, options.note, options.reason, options.actor)
        elif command == "decision-assign":
            payload = operations.assign(developer, options.id, options.owner, options.reason, options.actor)
        elif command == "action-add":
            payload = operations.add_action(developer, options.id, options.description, options.owner, options.due_date, options.reason, options.actor)
        elif command == "action-assign":
            payload = operations.assign_action(developer, options.id, options.action_id, options.owner, options.due_date, options.reason, options.actor)
        elif command == "action-transition":
            payload = operations.transition_action(developer, options.id, options.action_id, options.state, options.note, options.evidence, options.closure_reason, options.reason, options.actor)
        elif command == "action-defer":
            payload = operations.defer_action(developer, options.id, options.action_id, options.until, options.note, options.reason, options.actor)
        elif command == "exception-add":
            payload = operations.add_exception(developer, options.id, options.description, options.owner, options.expires_at, options.reason, options.action_id, options.actor)
        elif command == "exception-assign":
            payload = operations.assign_exception(developer, options.id, options.exception_id, options.owner, options.reason, options.actor)
        else:
            payload = operations.transition_exception(developer, options.id, options.exception_id, options.state, options.note, options.evidence, options.closure_reason, options.reason, options.actor)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command.startswith("governance-"):
        from src.developer import strategic_governance as strategic
        command = options.local_command.removeprefix("governance-")
        if command in {"status", "dependencies", "plan-review"}:
            payload = {"status": strategic.status, "dependencies": strategic.dependencies, "plan-review": strategic.plan_review}[command](developer)
        elif command in {"history", "review"}:
            payload = getattr(strategic, command)(developer, options.id)
        elif command in {"create", "update"}:
            fields = (options.owner, options.capability, options.evolution_id, options.dependency, options.note, options.risk, options.reason, options.actor)
            payload = strategic.create(developer, options.id, *fields) if command == "create" else strategic.update(developer, options.id, options.objective, *fields)
        elif command == "transition":
            payload = strategic.transition(developer, options.id, options.state, options.note, options.reason, options.actor)
        elif command == "record-review":
            payload = strategic.record_review(developer, options.id, options.note, options.reason, options.actor)
        elif command in {"roadmap-add", "roadmap-update"}:
            fields = (options.description, options.owner, options.target_period, options.dependency, options.reason, options.actor)
            payload = strategic.add_roadmap(developer, options.id, *fields) if command == "roadmap-add" else strategic.update_roadmap(developer, options.id, options.roadmap_id, *fields)
        elif command == "roadmap-transition":
            payload = strategic.transition_roadmap(developer, options.id, options.roadmap_id, options.state, options.note, options.reason, options.actor)
        else:
            payload = strategic.review_dependency(developer, options.id, options.dependency, options.resolution, options.note, options.reason, options.roadmap_id, options.actor)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command.startswith("evolution-"):
        from src.developer import evolution
        command = options.local_command.removeprefix("evolution-")
        if command in {"status", "plan"}:
            payload = {"status": evolution.status, "plan": evolution.plans}[command](developer)
        elif command in {"history", "impact", "review"}:
            payload = getattr(evolution, command)(developer, options.id)
        elif command == "create":
            payload = evolution.create(developer, options.id, options.change_type, options.owner, options.reason, options.actor)
        elif command == "transition":
            payload = evolution.transition(developer, options.id, options.state, options.note, options.reason, options.actor)
        elif command == "impact-add":
            payload = evolution.record_impact(developer, options.id, options.capability, options.maturity_id,
                options.finding, options.note, options.risk, options.reason, options.actor)
        else:
            payload = evolution.add_plan(developer, options.id, options.improvement, options.dependency,
                options.milestone, options.owner, options.reason, options.supersedes, options.actor)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command.startswith("maturity-"):
        from src.developer import maturity
        command = options.local_command.removeprefix("maturity-")
        if command in {"status", "readiness", "plan"}:
            payload = {"status": maturity.status, "readiness": maturity.readiness, "plan": maturity.plans}[command](developer)
        elif command in {"history", "review"}:
            payload = getattr(maturity, command)(developer, options.id)
        elif command == "create":
            payload = maturity.create(developer, options.id, options.assurance_id, options.owner, options.reason, options.actor)
        elif command == "assess":
            payload = maturity.assess(developer, options.id, options.capability, options.reason, options.gap, options.note, options.actor)
        elif command == "assign":
            payload = maturity.assign(developer, options.id, options.owner, options.reason, options.actor)
        elif command == "transition":
            payload = maturity.transition(developer, options.id, options.level, options.reason, options.actor)
        elif command == "plan-add":
            payload = maturity.add_plan(developer, options.id, options.improvement, options.capability, options.finding,
                                        options.reason, options.supersedes, options.actor)
        else:
            payload = maturity.review_plan(developer, options.id, options.plan_id, options.state, options.note, options.reason, options.actor)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command in {"assurance-operations", "assurance-findings", "assurance-review-cycle", "assurance-coverage", "assurance-improvements",
                                 "assurance-operation-create", "assurance-operation-review", "assurance-operation-transition",
                                 "assurance-operation-assign", "assurance-operation-note"}:
        from src.developer import assurance_operations as operations
        command = options.local_command.removeprefix("assurance-")
        if command in {"operations", "findings", "coverage", "improvements"}:
            payload = getattr(operations, command)(developer)
        elif command == "review-cycle":
            payload = operations.review_cycle(developer, options.id)
        elif command == "operation-create":
            payload = operations.create(developer, options.id, options.reason, options.owner, options.actor)
        elif command == "operation-review":
            payload = operations.record_review(developer, options.id, options.reason, options.actor)
        else:
            action = command.removeprefix("operation-")
            fields = {"transition": {"status": "state"}, "assign": {"owner": "owner"}, "note": {"note": "note"}}[action]
            payload = operations.change(developer, options.id, action, options.reason, options.actor,
                                        **{key: getattr(options, name) for key, name in fields.items()})
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command in {"assurance-status", "assurance-history", "assurance-review", "assurance-check", "assurance-improvements",
                                 "assurance-register", "assurance-transition", "assurance-assign", "assurance-schedule", "assurance-note", "assurance-record-check"}:
        from src.developer import recovery_governance as governance
        command = options.local_command.removeprefix("assurance-")
        if command in {"status", "check", "improvements"}:
            payload = getattr(governance, command)(developer)
        elif command in {"history", "review"}:
            payload = getattr(governance, command)(developer, options.id)
        elif command == "register":
            payload = governance.register(developer, options.id, options.reason, options.owner,
                                          options.responsibility, options.every_hours, options.actor)
        elif command == "record-check":
            payload = governance.record_check(developer, options.id, options.verification_id, options.reason, options.actor)
        else:
            fields = {"transition": ("status",), "assign": ("owner", "responsibility"),
                      "schedule": ("interval_hours",), "note": ("kind", "note")}[command]
            aliases = {"status": "state", "interval_hours": "every_hours"}
            payload = governance.change(developer, options.id, command, options.reason, options.actor,
                                        **{key: getattr(options, aliases.get(key, key)) for key in fields})
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if (options.local_command.startswith("assurance-") or options.local_command in
            {"recovery-assurance", "recovery-evidence", "recovery-history-analysis", "recovery-verify-history"}):
        from src.developer import assurance
        command = options.local_command
        if command == "assurance-create":
            payload = assurance.create_assurance(developer, options.id, options.reason, options.owner,
                                                  options.actor, options.valid_for_hours)
        elif command == "assurance-verify":
            payload = assurance.verify_assurance(developer, options.id, options.reason, options.actor)
        elif command == "assurance-expire":
            payload = assurance.transition_assurance(developer, options.id, "expired", options.reason, options.actor)
        elif command == "recovery-history-analysis":
            payload = assurance.recovery_history_analysis(developer)
        else:
            payload = {"recovery-assurance": assurance.recovery_assurance,
                       "recovery-evidence": assurance.recovery_evidence,
                       "recovery-verify-history": assurance.recovery_verify_history}[command](developer, options.id)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command.startswith("disaster-") or options.local_command == "continuity-status":
        from src.developer import continuity
        command = options.local_command
        if command == "disaster-create":
            payload = continuity.create_scenario(developer, options.id, options.reason, options.owner,
                                                 options.scenario_type, options.plan_id, options.actor, options.step)
        elif command in {"disaster-status", "continuity-status"}:
            payload = (continuity.disaster_status if command == "disaster-status" else continuity.continuity_status)(developer)
        elif command == "disaster-test":
            payload = continuity.test_scenario(developer, options.id, options.reason, options.actor)
        elif command == "disaster-retire":
            payload = continuity.transition_scenario(developer, options.id, "retired", options.reason, options.actor)
        else:
            payload = (continuity.disaster_check if command == "disaster-check"
                       else continuity.disaster_inspect)(developer, options.id)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if (options.local_command.startswith(("recovery-plan-", "readiness-"))
            or options.local_command in {"reliability-check", "recovery-verify"}):
        from src.developer import reliability
        command = options.local_command
        if command == "recovery-plan-create":
            payload = reliability.create_recovery_plan(developer, options.id, options.reason, options.owner, options.actor)
        elif command == "readiness-create":
            payload = reliability.create_readiness(developer, options.id, options.reason, options.actor)
        elif command in {"readiness-check", "recovery-verify"}:
            payload = (reliability.check_readiness if command == "readiness-check"
                       else reliability.verify_recovery)(developer, options.id, options.reason, options.actor)
        elif command == "readiness-expire":
            payload = reliability.transition_readiness(developer, options.id, "expired", options.reason, options.actor)
        elif command in {"recovery-plan-status", "readiness-status"}:
            payload = (reliability.recovery_plan_status if command == "recovery-plan-status"
                       else reliability.readiness_status)(developer)
        else:
            payload = (reliability.reliability_check if command == "reliability-check"
                       else reliability.recovery_plan_inspect)(developer, options.id)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if (options.local_command.startswith("incident-")
            or options.local_command in {"recovery-history", "deploy-health"}):
        from src.developer import operations
        command = options.local_command
        if command == "incident-create":
            payload = operations.create_incident(developer, options.id, options.reason, options.owner, options.actor)
        elif command in {"incident-status", "recovery-history"}:
            payload = (operations.incident_status if command == "incident-status"
                       else operations.recovery_history)(developer)
        elif command in {"incident-inspect", "deploy-health"}:
            payload = (operations.incident_inspect if command == "incident-inspect"
                       else operations.deployment_health)(developer, options.id)
        elif command == "incident-diff":
            payload = operations.incident_diff(developer, options.incident_a, options.incident_b)
        else:
            status = {"incident-investigate": "investigating", "incident-resolve": "resolved",
                      "incident-close": "closed"}[command]
            payload = operations.transition_incident(
                developer, options.id, status, options.reason, options.actor,
                getattr(options, "recovery_action", None), getattr(options, "rollback_reference", None))
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command.startswith("deploy-"):
        from src.developer.deployment import (
            deployment_status, deployment_diff, stage_deployment, transition_deployment,
            deployment_audit, deployment_governance_check, deployment_history, deployment_inspect,
        )
        action = options.local_command.removeprefix("deploy-")
        if action == "status":
            payload = deployment_status(developer)
        elif action == "history":
            payload = deployment_history(developer)
        elif action in {"audit", "governance-check", "inspect"}:
            payload = {"audit": deployment_audit, "governance-check": deployment_governance_check,
                       "inspect": deployment_inspect}[action](developer, options.id)
        elif action == "diff":
            payload = deployment_diff(developer, options.deployment_a, options.deployment_b)
        elif action == "stage":
            payload = stage_deployment(developer, options.id, options.reason, options.actor)
        else:
            payload = transition_deployment(developer, options.id, action, options.reason, options.actor)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command.startswith("config-"):
        from src.developer.configuration import (
            configuration_status, configuration_history, configuration_diff,
            create_configuration, transition_configuration,
        )
        action = options.local_command.removeprefix("config-")
        if action in {"status", "history"}:
            payload = (configuration_status if action == "status" else configuration_history)(developer)
        elif action == "diff":
            payload = configuration_diff(developer, options.version_a, options.version_b)
        elif action == "create":
            payload = create_configuration(developer, options.id, options.reason, options.actor)
        else:
            payload = transition_configuration(developer, options.id, action, options.reason, options.actor)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload
    if options.local_command in {"optimize-promote", "optimize-promotion-status", "optimize-retire",
                                 "optimize-promote-rollback", "optimize-promotion-check"}:
        from src.developer.promotion import promote, promotion_status, retire, rollback, promotion_check
        actions = {"optimize-promote": promote, "optimize-retire": retire,
                   "optimize-promote-rollback": rollback}
        if options.local_command in actions:
            payload = actions[options.local_command](developer, options.id)
        else:
            payload = (promotion_check if options.local_command == "optimize-promotion-check"
                       else promotion_status)(developer)
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
        if options.command == "local" and options.local_command in {"test", "test-timing"}:
            from src.developer_testing import run_command
            return run_command(options)
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
