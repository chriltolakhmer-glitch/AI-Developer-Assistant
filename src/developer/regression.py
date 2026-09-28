"""Descriptive developer retrieval snapshots; independent of research evaluation."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

SCHEMA = "developer-retrieval-baseline-v1"


def _portable(value):
    """Exclude run-specific chunk identities and retrieval scores from comparisons."""
    if isinstance(value, dict):
        return {key: _portable(item) for key, item in value.items()
                if key not in {"chunk_id", "selected_chunk_id", "related_chunk_ids", "results",
                               "score", "navigation_score", "base_rrf_score"}}
    if isinstance(value, list):
        return [_portable(item) for item in value]
    return value


def snapshot(case: dict[str, Any], payload: dict[str, Any], repository_fixture: str) -> dict[str, Any]:
    rows = payload["results"]
    selected = [{"file": row["file_path"], "symbol": row["qualified_name"]} for row in rows]
    expanded = [_portable(item) for row in rows for item in row.get("related_context", [])]
    context = _portable(payload.get("context", {}))
    context["expanded_symbols"] = expanded
    context["expansion_decisions"] = [
        {**identity, "reason": row.get("ranking_reason", {}).get("context_expansion_reason"),
         "related": _portable(row.get("related_context", []))}
        for identity, row in zip(selected, rows)
    ]
    context["configuration_keys"] = sorted({key for row in rows
        for key in row.get("developer_context", {}).get("configuration_keys", [])})
    return {
        "id": case["id"], "query": case["query"], "repository_fixture": repository_fixture,
        "expected": deepcopy(case["expected"]),
        "allowed_extra_context": case.get("allowed_extra_context", []),
        "required_relationships": case.get("required_relationships", []),
        "failure_tolerance": case.get("failure_tolerance", {}),
        "retrieved": {"files": sorted({row["file_path"] for row in rows}),
                      "symbols": sorted({row["qualified_name"] for row in rows})},
        "ranking": {"order": selected, "reasons": [
            {**identity, "reason": _portable(row.get("ranking_reason", {})),
             "explanation": _portable(row.get("explanation", {}))}
            for identity, row in zip(selected, rows)]},
        "context": context,
    }


def _evidence(record):
    context = record["context"]
    files = set(record["retrieved"]["files"])
    files.update(item["file_path"] for item in context.get("files", []))
    symbols = set(record["retrieved"]["symbols"]) | set(context.get("configuration_keys", []))
    expanded = {item["symbol_name"] for item in context.get("expanded_symbols", [])}
    return files, symbols | expanded, expanded


def compare_records(previous, current):
    """Report evidence changes without a scalar quality judgment."""
    if any(previous.get(key) != current.get(key) for key in (
            "id", "query", "repository_fixture", "expected", "allowed_extra_context",
            "required_relationships", "failure_tolerance")):
        raise ValueError("Case definition changed; create a separately named baseline.")
    changes = []

    def change(kind, before, after, cause, classification="potential_regression"):
        changes.append({"case_id": current["id"], "classification": classification,
                        "kind": kind, "previous_behavior": before, "current_behavior": after,
                        "suspected_cause": cause})

    def delta(old, new):
        return {"added": sorted(set(new) - set(old)), "removed": sorted(set(old) - set(new))}

    files = delta(previous["retrieved"]["files"], current["retrieved"]["files"])
    symbols = delta(previous["retrieved"]["symbols"], current["retrieved"]["symbols"])
    old_files, old_symbols, old_expanded = _evidence(previous)
    new_files, new_symbols, new_expanded = _evidence(current)
    expected = current["expected"]
    missing = {
        "files": sorted(set(expected.get("files", [])) - new_files),
        "symbols": sorted(set(expected.get("symbols", [])) - new_symbols),
        "relationships": sorted(set(current["required_relationships"]) - new_symbols),
    }
    if old_symbols - new_symbols:
        change("missing_previously_found_symbols", sorted(old_symbols), sorted(new_symbols),
               "Candidate selection, parser coverage, or context expansion changed.")
    if any(missing.values()):
        change("missing_evidence", {"files": sorted(old_files), "symbols": sorted(old_symbols)},
               missing, "Declared evidence is absent; inspect local diagnose and index freshness.")
    allowed = set(expected.get("files", [])) | set(current["allowed_extra_context"])
    noise = sorted((new_files - old_files) - allowed)
    if noise:
        change("unrelated_files_added", sorted(old_files - allowed), sorted(new_files - allowed),
               "New candidates or relationship expansion introduced undeclared files.")
    if (new_symbols - old_symbols) & set(expected.get("symbols", [])):
        change("improved_symbol_coverage", sorted(old_symbols), sorted(new_symbols),
               "Additional declared symbols are now present.", "expected_change")
    if old_expanded - new_expanded:
        change("context_expansion_loss", sorted(old_expanded), sorted(new_expanded),
               "Relationship selection or expansion limits changed.")
    if (new_expanded - old_expanded) & set(current["required_relationships"]):
        change("better_relationship_expansion", sorted(old_expanded), sorted(new_expanded),
               "Additional required relationships are now expanded.", "expected_change")
    def duplicates(record):
        identities = [(item.get("file_path"), item.get("symbol_name"))
                      for item in record["context"].get("expanded_symbols", [])]
        return sum(count - 1 for count in Counter(identities).values())
    if duplicates(current) < duplicates(previous):
        change("reduced_duplicate_context", duplicates(previous), duplicates(current),
               "Repeated context evidence was reduced.", "expected_change")
    old_reasons = {(item["file"], item["symbol"]): item for item in previous["ranking"]["reasons"]}
    def explanation_removed(before, after):
        if isinstance(before, dict) and isinstance(after, dict):
            return bool(set(before) - set(after)) or any(
                explanation_removed(value, after[key]) for key, value in before.items() if key in after)
        return isinstance(before, (str, dict)) and bool(before) and not after

    for item in current["ranking"]["reasons"]:
        old = old_reasons.get((item["file"], item["symbol"]))
        if old and (explanation_removed(old.get("reason", {}), item.get("reason", {}))
                    or explanation_removed(old.get("explanation", {}), item.get("explanation", {}))):
            change("explanation_removed", old, item, "Ranking explanation fields were dropped or emptied.")
    ranking = None if previous["ranking"] == current["ranking"] else {
        "previous": previous["ranking"], "current": current["ranking"]}
    context = None if previous["context"] == current["context"] else {
        "previous": previous["context"], "current": current["context"]}
    if ranking:
        change("ranking_changed", previous["ranking"], current["ranking"],
               "Retrieval version, candidates, or ranking explanations changed.", "observed_change")
    if context:
        change("context_changed", previous["context"], current["context"],
               "Context assembly decisions changed.", "observed_change")
    return {"case_id": current["id"], "changed_files": files, "changed_symbols": symbols,
            "ranking_differences": ranking, "context_differences": context,
            "missing_evidence": missing, "newly_introduced_noise": noise,
            "changes": changes, "behavior_changed": previous != current}


def run_regression(workspace, repository, cases_path, baseline="default", create_baseline=False, top_k=10):
    """Keep immutable named baselines and per-invocation history inside the workspace."""
    import json
    import re
    from datetime import datetime, timezone
    from uuid import uuid4

    from .evaluation import load_cases
    from .local_workflow import (DeveloperIndex, LocalWorkflowError, _INDEX_SCHEMA,
                                 _json_bytes, _resolve_repository_argument, _safe_component,
                                 scan_local_repository)
    from .ranking import RANKING_VERSION

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", baseline):
        raise LocalWorkflowError("Baseline name must be 1-64 letters, digits, underscores or hyphens.")
    if type(top_k) is not int or not 1 <= top_k <= 50:
        raise LocalWorkflowError("top-k must be an integer from 1 to 50.")
    root = _resolve_repository_argument(repository)
    workspace._prepare(root)
    cases = load_cases(cases_path)
    if len({case["id"] for case in cases}) != len(cases):
        raise LocalWorkflowError("Duplicate developer case IDs are not supported.")
    for case in cases:
        if any(not isinstance(case["expected"].get(key, []), list)
               for key in ("files", "symbols", "relationships")):
            raise LocalWorkflowError("Expected evidence must use lists of text values.")
    inventory = scan_local_repository(root)
    storage = workspace._contained(workspace.root / "regression" / _safe_component(inventory.repository_id))
    baseline_path = workspace._contained(storage / "baselines" / f"{baseline}.json")
    old = None
    if create_baseline:
        if baseline_path.exists():
            raise LocalWorkflowError("Baseline already exists; choose a new name to preserve history.")
    else:
        try:
            old = json.loads(baseline_path.read_text(encoding="utf-8"))
            if (old["schema_version"] != SCHEMA or old["mode"] != "developer-local-regression"
                    or old["repository_id"] != inventory.repository_id or old["top_k"] != top_k
                    or not all(isinstance(old[key], str) for key in ("retrieval_version", "index_version"))
                    or not isinstance(old["records"], list)
                    or {item["id"] for item in old["records"]} != {case["id"] for case in cases}
                    or len(old["records"]) != len(cases)):
                raise ValueError("schema, repository, top-k or case IDs differ")
            for case in cases:
                record = next(item for item in old["records"] if item["id"] == case["id"])
                if any(record.get(key) != case[key] for key in (
                        "query", "expected", "allowed_extra_context", "required_relationships", "failure_tolerance")):
                    raise ValueError("case definition changed")
                compare_records(record, record)  # Validate comparison fields before retrieval/writes.
        except (OSError, ValueError, KeyError, TypeError, AttributeError, StopIteration) as error:
            raise LocalWorkflowError(
                f"Cannot compare developer baseline '{baseline_path}': {error}. "
                "Create a separately named baseline with --create-baseline."
            ) from error
    index_root = workspace._indexes(inventory)
    index = DeveloperIndex.load(workspace._contained(index_root / workspace._read_active(index_root)))
    records, comparisons, stability = [], [], []
    old_records = {item["id"]: item for item in old["records"]} if old else {}
    for case in cases:
        payloads = [workspace.query(case["query"], root, top_k) for _ in range(2)]
        if any(payload["repository"]["working_tree_sha256"] != inventory.snapshot_id for payload in payloads):
            raise LocalWorkflowError("Repository changed during regression; rerun with a stable index.")
        first, second = [snapshot(case, payload, root.name) for payload in payloads]
        records.append(first)
        stable = first == second
        stability.append({"case_id": case["id"], "stable": stable})
        comparison = compare_records(old_records.get(case["id"], first), first)
        if not stable:
            comparison["changes"].append({
                "case_id": case["id"], "classification": "potential_regression",
                "kind": "unstable_ranking_changes", "previous_behavior": first,
                "current_behavior": second,
                "suspected_cause": "Repeated retrieval changed against the same index; inspect tie ordering or model determinism.",
            })
        comparisons.append(comparison)
    if create_baseline and not all(item["stable"] for item in stability):
        raise LocalWorkflowError("Repeated retrieval is unstable; baseline was not created.")
    document = {
        "schema_version": SCHEMA, "mode": "developer-local-regression",
        "repository_id": inventory.repository_id, "repository_fixture": root.name,
        "working_tree_sha256": inventory.snapshot_id, "commit_sha": inventory.commit_sha,
        "retrieval_version": RANKING_VERSION, "index_version": _INDEX_SCHEMA,
        "index_runtime": index.manifest["runtime"], "index_generation": index.path.name,
        "top_k": top_k, "records": records,
    }
    report = {"status": "completed", "mode": "developer-local-regression",
              "baseline": baseline, "baseline_created": create_baseline,
              "previous_versions": {key: old[key] for key in ("retrieval_version", "index_version")} if old else None,
              "retrieval_version": RANKING_VERSION, "index_version": _INDEX_SCHEMA,
              "query_cases": [case["id"] for case in cases], "comparisons": comparisons,
              "stability": stability,
              "limitations": ["Developer evidence changes only; no research or benchmark scores.",
                              "Undeclared files are possible noise, not proven irrelevant.",
                              "Suspected causes are hypotheses; static Python relationships are incomplete."]}
    timestamp = datetime.now(timezone.utc).isoformat()
    history_id = uuid4().hex
    history_path = workspace._contained(storage / "history" / f"{history_id}.json")
    # Resolve every destination before any output is created, including redirected subdirectories.
    workspace._contained(baseline_path)
    workspace._contained(history_path)
    if create_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with baseline_path.open("xb") as stream:
            stream.write(_json_bytes(document))
    report["history_id"] = history_id
    report["baseline_path"] = str(baseline_path)
    report["history_path"] = str(history_path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("xb") as stream:
        stream.write(_json_bytes({"recorded_at": timestamp, "snapshot": document, "report": report}))
    return report
