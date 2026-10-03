"""Read-only change-aware developer assistance assembled from existing tools."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
from typing import Any

from src.chunker import CodeChunker
from src.developer_testing import plan as plan_tests
from src.models.corpus import RepositoryMetadata
from src.parser import ParserError, PythonAstParser

from .local_workflow import (
    DeveloperIndex,
    DeveloperWorkspace,
    LocalWorkflowError,
    ParsedLocalCode,
    _developer_context,
    _resolve_repository_argument,
    parse_local_repository,
)


def _git(root: Path, *arguments: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *arguments], capture_output=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "stderr", b"")
        detail = os.fsdecode(detail).strip() if detail else str(error)
        raise LocalWorkflowError(f"Cannot inspect Git changes: {detail}") from error


def _change_set(root: Path, base: str | None) -> dict[str, Any]:
    reference = "HEAD"
    if base:
        reference = os.fsdecode(
            _git(root, "rev-parse", "--verify", "--end-of-options", base + "^{commit}")
        ).strip()
    raw = _git(root, "diff", "--name-status", "-z", "--find-renames", reference, "--")
    fields = [os.fsdecode(item) for item in raw.split(b"\0") if item]
    rows: list[dict[str, Any]] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        code = status[:1]
        if code in {"R", "C"}:
            if index + 1 >= len(fields):
                raise LocalWorkflowError("Git returned an incomplete rename/copy change record.")
            old_path, path = fields[index:index + 2]
            index += 2
            rows.append({"path": path, "old_path": old_path,
                         "change_type": "renamed" if code == "R" else "copied",
                         "similarity": int(status[1:] or 0)})
        else:
            if index >= len(fields):
                raise LocalWorkflowError("Git returned an incomplete change record.")
            path = fields[index]
            index += 1
            rows.append({"path": path, "change_type": {
                "A": "added", "M": "modified", "D": "deleted", "T": "type_changed",
                "U": "unmerged",
            }.get(code, "modified")})
    untracked = [os.fsdecode(item) for item in
                 _git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if item]
    known_paths = {row["path"] for row in rows}
    rows.extend({"path": path, "change_type": "untracked"}
                for path in untracked if path not in known_paths)
    rows.sort(key=lambda row: (row["path"], row["change_type"]))
    changed_paths = {row["path"] for row in rows}
    changed_paths.update(row["old_path"] for row in rows if row.get("old_path"))
    tracked = {os.fsdecode(item) for item in _git(root, "ls-files", "-z").split(b"\0") if item}
    current = os.fsdecode(_git(root, "rev-parse", "--verify", "HEAD^{commit}")).strip().lower()
    working_tree_dirty = bool(_git(root, "status", "--porcelain=v1", "-z"))
    counts = Counter(row["change_type"] for row in rows)
    return {
        "base_reference": base or "HEAD",
        "base_commit": reference.lower(),
        "current_commit": current,
        "dirty": working_tree_dirty,
        "status": "dirty" if working_tree_dirty else "clean",
        "comparison_has_changes": bool(rows),
        "files": rows,
        "added_files": sorted(row["path"] for row in rows if row["change_type"] == "added"),
        "modified_files": sorted(row["path"] for row in rows if row["change_type"] == "modified"),
        "deleted_files": sorted(row["path"] for row in rows if row["change_type"] == "deleted"),
        "renamed_files": [row for row in rows if row["change_type"] == "renamed"],
        "untracked_files": sorted(row["path"] for row in rows if row["change_type"] == "untracked"),
        "unchanged_file_count": len(tracked - changed_paths),
        "counts": dict(sorted(counts.items())),
    }


def _parse_blob(source: str, path: str, repository_id: str, commit: str) -> ParsedLocalCode:
    parser, chunker = PythonAstParser(), CodeChunker()
    module = parser.parse(source, path)
    chunks = chunker.chunk_module(module, source, RepositoryMetadata(repository_id, commit))
    context = _developer_context(module, source, chunks)
    return ParsedLocalCode(None, chunks, (), context)  # type: ignore[arg-type]


def _base_symbols(root: Path, changes: dict[str, Any], repository_id: str) -> tuple[dict[tuple[str, str], Any], list[dict[str, Any]]]:
    symbols: dict[tuple[str, str], Any] = {}
    failures = []
    for row in changes["files"]:
        if row["change_type"] in {"added", "untracked", "copied"}:
            continue
        path = row.get("old_path", row["path"])
        if PurePosixPath(path).suffix.casefold() != ".py":
            continue
        try:
            source = os.fsdecode(_git(root, "show", f"{changes['base_commit']}:{path}"))
            parsed = _parse_blob(source, path, repository_id, changes["base_commit"])
            symbols.update({(path, chunk.qualified_name): chunk for chunk in parsed.chunks})
        except (LocalWorkflowError, ParserError, UnicodeError, ValueError) as error:
            failures.append({"file_path": path, "source": "base", "message": str(error)})
    return symbols, failures


def _symbol_row(chunk, change_type: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    return {
        "qualified_symbol": chunk.qualified_name,
        "file_path": chunk.file_path,
        "entity_type": chunk.entity_type,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "change_type": change_type,
        "imports": context.get("imports", []),
        "calls": context.get("called_symbol_names", []),
        "configuration_references": context.get("configuration_keys", []),
    }


def _symbols_and_relationships(parsed: ParsedLocalCode, changes: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    current_by_key = {(chunk.file_path, chunk.qualified_name): chunk for chunk in parsed.chunks}
    base_by_key, base_failures = _base_symbols(parsed.inventory.root, changes, parsed.inventory.repository_id)
    changed_rows = changes["files"]
    current_changed = {row["path"] for row in changed_rows
                       if row["change_type"] not in {"deleted"} and row["path"].endswith(".py")}
    old_changed = {row.get("old_path", row["path"]) for row in changed_rows
                   if row["change_type"] not in {"added", "untracked", "copied"}
                   and row.get("old_path", row["path"]).endswith(".py")}
    current_keys = {key for key in current_by_key if key[0] in current_changed}
    base_keys = {key for key in base_by_key if key[0] in old_changed}
    symbols = []
    impacted_ids = set()
    context_by_id = parsed.context
    current_id_by_key = {(chunk.file_path, chunk.qualified_name): chunk.chunk_id for chunk in parsed.chunks}
    for key in sorted(current_keys | base_keys):
        current_chunk, base_chunk = current_by_key.get(key), base_by_key.get(key)
        if current_chunk is None:
            symbols.append(_symbol_row(base_chunk, "removed"))
            continue
        context = context_by_id.get(current_chunk.chunk_id, {})
        impacted_ids.add(current_chunk.chunk_id)
        if base_chunk is None:
            kind = "added"
        elif hashlib.sha256(current_chunk.content.encode("utf-8")).digest() != hashlib.sha256(base_chunk.content.encode("utf-8")).digest():
            kind = "modified"
        else:
            kind = "context_changed"
        row = _symbol_row(current_chunk, kind, context)
        if kind == "context_changed":
            row["change_reason"] = "Containing file changed while this symbol body stayed unchanged; imports or module context may differ."
        symbols.append(row)

    chunks_by_id = {chunk.chunk_id: chunk for chunk in parsed.chunks}
    relationships = []
    unresolved = []
    seen = set()
    for chunk_id in sorted(impacted_ids):
        source = chunks_by_id[chunk_id]
        details = context_by_id.get(chunk_id, {})
        for edge in details.get("relationship_edges", []):
            identity = (source.file_path, source.qualified_name, edge["kind"], edge["file_path"], edge["symbol"])
            if identity not in seen:
                seen.add(identity)
                relationships.append({
                    "source_file": source.file_path, "source_symbol": source.qualified_name,
                    "relationship": edge["kind"], "target_file": edge["file_path"],
                    "target_symbol": edge["symbol"],
                    "evidence_type": "static_relationship",
                    "limitation": "Static parsed-source relationship; runtime execution is not confirmed.",
                })
        for diagnostic in details.get("relationship_diagnostics", []):
            unresolved.append({"source_file": source.file_path,
                               "source_symbol": source.qualified_name, **diagnostic})
    return symbols, relationships, unresolved, base_failures


def _index_freshness(workspace: DeveloperWorkspace, parsed: ParsedLocalCode) -> tuple[dict[str, Any], DeveloperIndex | None]:
    if not parsed.inventory.files:
        return ({"status": "unsupported", "reason": "No eligible Python source is available for indexing."}, None)
    active_path = workspace._indexes(parsed.inventory) / "active.json"
    if not active_path.exists():
        return ({"status": "missing", "reason": "No active developer index exists for this repository."}, None)
    active = workspace._read_active(active_path.parent)
    index = DeveloperIndex.load(workspace._contained(active_path.parent / active))
    indexed = index.manifest.get("working_tree_sha256")
    current = parsed.inventory.snapshot_id
    if indexed == current:
        return ({"status": "current", "working_tree_sha256": current}, index)
    state = json.loads((index.path / "state.json").read_text(encoding="utf-8"))
    previous = state.get("file_hashes", {})
    present = {item.relative_path: item.content_sha256 for item in parsed.inventory.files}
    stale_files = sorted(name for name in set(previous) | set(present) if previous.get(name) != present.get(name))
    return ({"status": "stale", "indexed_working_tree_sha256": indexed,
             "current_working_tree_sha256": current, "stale_source_files": stale_files,
             "reason": "Source changed after the active developer index was built."}, index)


def _retrieval_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    direct = []
    related = []
    for row in payload.get("results", []):
        direct.append({"file_path": row["file_path"], "symbol": row["qualified_name"],
                       "start_line": row["start_line"], "end_line": row["end_line"],
                       "evidence_type": "retrieved_query", "rank": row.get("rank"),
                       "reason": row.get("ranking_reason", {})})
        for item in row.get("related_context", []):
            related.append({"file_path": item.get("file_path"), "symbol": item.get("symbol_name"),
                            "evidence_type": "additional_related_context",
                            "reason": item.get("reason"), "source_result": row["chunk_id"]})
    return {"status": "completed", "question": payload.get("question"),
            "query_evidence": direct, "additional_related_context": related,
            "context_diagnostics": payload.get("context", {}), "run_id": payload.get("run_id")}


def analyze_change_impact(workspace: DeveloperWorkspace, repository: Path, *,
                          base: str | None = None, question: str | None = None,
                          top_k: int = 10) -> dict[str, Any]:
    """Compose change, symbol, relationship, retrieval, and test-plan evidence."""
    if type(top_k) is not int or not 1 <= top_k <= 50:
        raise LocalWorkflowError("top-k must be an integer from 1 to 50.")
    root = _resolve_repository_argument(repository)
    workspace._prepare(root)
    changes = _change_set(root, base)
    parsed = parse_local_repository(root)
    # Reuse the existing Phase 34 index/snapshot comparison. Git comparison
    # below adds base-reference, rename, staging, and untracked semantics.
    inspection = workspace.inspect(root, changes=True)
    symbols, relationships, unresolved, base_failures = _symbols_and_relationships(parsed, changes)
    freshness, _ = _index_freshness(workspace, parsed)
    changed_paths = {row["path"] for row in changes["files"]}
    changed_python_paths = {path for row in changes["files"]
                            for path in (row["path"], row.get("old_path"))
                            if path and path.endswith(".py")}
    decisions = {row["file_path"]: row for row in parsed.inventory.file_decisions}
    eligible = sorted(path for path in changed_paths if decisions.get(path, {}).get("included"))
    unsupported = [
        {"file_path": path, "reason": decisions.get(path, {}).get("reason", "deleted or unavailable source")}
        for path in sorted(changed_paths - set(eligible))
        if not path.endswith(".py") or decisions.get(path, {}).get("reason") == "unsupported file type (Python only)"
    ]
    parser_failures = list(inspection["parse_failures"]) + base_failures
    excluded = [item for item in inspection["chunks"] if item["reason"] in {"empty", "over_limit"}]
    try:
        test_plan = plan_tests(root=root, changed=True, base=base)
    except (SyntaxError, ValueError) as error:
        test_plan = {
            "tier": "T4", "tier_description": "Complete test inventory; final gate only.",
            "changed_files": sorted(changed_paths), "selected_tests": [], "selectors": [],
            "not_selected": [], "diagnostics": [f"Affected-test planning was incomplete: {error}"],
            "uncertain": True, "execution_blocked": True, "required_followup": ["manual test review", "T4 final gate"],
        }

    retrieval: dict[str, Any] = {"status": "not_requested", "question": None,
                                 "query_evidence": [], "additional_related_context": []}
    if question:
        if freshness["status"] == "current":
            retrieval = _retrieval_evidence(workspace.query(question, root, top_k))
        else:
            retrieval = {"status": "blocked", "question": question, "query_evidence": [],
                         "additional_related_context": [],
                         "reason": f"Developer index is {freshness['status']}; stale or absent retrieval is not current evidence."}

    recommendations = []
    if freshness["status"] in {"stale", "missing"}:
        recommendations.append({"action": "reindex", "command": f'prototype local index "{root}"',
                                "reason": f"Developer index is {freshness['status']}."})
    if unresolved:
        recommendations.append({"action": "inspect_unresolved_relationships",
                                "reason": "Static relationship evidence was ambiguous or unresolved."})
    if test_plan["selected_tests"]:
        recommendations.append({"action": "run_affected_tests",
                                "command": f'prototype local test --changed{f" --base {base}" if base else ""}',
                                "reason": f"Phase 62 selected {len(test_plan['selected_tests'])} tests at {test_plan['tier']}."})
    recommendations.extend({"action": "follow_up_validation", "tier": item} for item in test_plan["required_followup"])
    limitations = [
        "Relationships are conservative static parsed-source evidence and do not confirm runtime execution.",
        "Dynamic imports, generated code, and unsupported languages require manual review.",
        "Test selection is a plan only; this command never executes tests.",
    ]
    if unsupported:
        limitations.append("Unsupported changed files remain visible but have no fabricated symbols or dependencies.")

    payload = {
        "status": "completed", "mode": "developer-local-change-impact",
        "repository": {**parsed.inventory.summary(), "base_reference": changes["base_reference"],
                       "base_commit": changes["base_commit"], "current_commit": changes["current_commit"],
                       "status": changes["status"], "dirty": changes["dirty"]},
        "changes": {**changes, "changed_eligible_python_files": eligible,
                    "files_requiring_reindex": sorted(changed_python_paths | set(freshness.get("stale_source_files", []))),
                    "unsupported_changed_files": unsupported,
                    "parser_failures": parser_failures, "token_limit_exclusions": excluded,
                    "index_snapshot_comparison": inspection.get("changes", {})},
        "symbols": symbols, "relationships": relationships,
        "unresolved_relationships": unresolved, "index_freshness": freshness,
        "retrieval": retrieval, "tests": {**test_plan, "executed": False},
        "recommended_actions": recommendations, "limitations": limitations,
        "evidence_sections": {
            "changed_code": symbols,
            "static_relationships": relationships,
            "retrieved_query": retrieval.get("query_evidence", []),
            "additional_related_context": retrieval.get("additional_related_context", []),
        },
    }
    payload["run_id"] = workspace._record_run("change-impact", parsed.inventory, payload)
    return payload
