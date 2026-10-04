"""Deterministic, evidence-grounded implementation planning for developer mode."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .change_impact import analyze_change_impact
from .local_workflow import DeveloperWorkspace, LocalWorkflowError, scan_local_repository


_ROLE_PRIORITY = {
    "manual_review": 0,
    "related_context": 1,
    "supporting_target": 2,
    "configuration_target": 6,
    "test_target": 4,
    "primary_target": 5,
}


def _test_path(selector: str) -> str:
    return selector.replace(".", "/") + ".py"


def _target_key(path: str | None, symbol: str | None) -> tuple[str, str]:
    return path or "", symbol or ""


def _configuration_references(symbol: dict[str, Any]) -> list[str]:
    """Return only configuration-like names present in parsed Phase 64 evidence."""
    references = set(symbol.get("configuration_references", []))
    references.update(item for item in symbol.get("imports", [])
                      if item.rsplit(".", 1)[-1].isupper())
    return sorted(references)


def _terms(value: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]+", value.casefold()) if len(term) >= 3}


def _shares_goal_term(goal_terms: set[str], values: list[str]) -> bool:
    evidence_terms = set().union(*(_terms(value) for value in values if value))
    return any(left == right or (len(left) >= 5 and len(right) >= 5 and left[:5] == right[:5])
               for left in goal_terms for right in evidence_terms)


def _add_target(targets: dict[tuple[str, str], dict[str, Any]], *, file_path: str,
                symbol: str | None, role: str, evidence_type: str, reason: str,
                entity_type: str | None = None, start_line: int | None = None,
                end_line: int | None = None, change_status: str = "unchanged_but_related",
                current_index_evidence: bool = False, related_symbol: str | None = None,
                unresolved_note: str | None = None) -> None:
    """Merge only explicitly evidenced targets; never infer file neighbours."""
    key = _target_key(file_path, symbol)
    row = targets.get(key)
    if row is None:
        row = {
            "file_path": file_path,
            "qualified_symbol": symbol,
            "entity_type": entity_type,
            "start_line": start_line,
            "end_line": end_line,
            "role": role,
            "evidence_types": [],
            "reasons": [],
            "related_symbols": [],
            "change_status": change_status,
            "current_index_evidence": current_index_evidence,
            "unresolved_notes": [],
        }
        targets[key] = row
    elif _ROLE_PRIORITY[role] > _ROLE_PRIORITY[row["role"]]:
        row["role"] = role
    if evidence_type not in row["evidence_types"]:
        row["evidence_types"].append(evidence_type)
    if reason not in row["reasons"]:
        row["reasons"].append(reason)
    if related_symbol and related_symbol not in row["related_symbols"]:
        row["related_symbols"].append(related_symbol)
    if unresolved_note and unresolved_note not in row["unresolved_notes"]:
        row["unresolved_notes"].append(unresolved_note)
    row["current_index_evidence"] = row["current_index_evidence"] or current_index_evidence
    if row["change_status"] != "already_changed" and change_status == "already_changed":
        row["change_status"] = change_status
    for name, value in (("entity_type", entity_type), ("start_line", start_line), ("end_line", end_line)):
        if row[name] is None and value is not None:
            row[name] = value


def _implementation_targets(impact: dict[str, Any], goal: str) -> list[dict[str, Any]]:
    targets: dict[tuple[str, str], dict[str, Any]] = {}
    changed_paths = {row["path"] for row in impact["changes"]["files"]}
    symbols = {(row["file_path"], row["qualified_symbol"]): row for row in impact["symbols"]}
    goal_terms = _terms(goal)

    for row in impact["symbols"]:
        if row.get("entity_type") == "module":
            continue
        configuration_references = _configuration_references(row)
        # Module-wide import lists are useful relationship evidence but are too broad
        # to prove that every symbol in a changed file intersects the goal.
        evidence_values = [row["file_path"], row["qualified_symbol"],
                           *row.get("calls", []), *configuration_references]
        config_goal = bool(configuration_references and goal_terms & {"config", "configuration", "setting", "settings"})
        if row["change_type"] == "context_changed" or not (
                config_goal or _shares_goal_term(goal_terms, evidence_values)):
            continue
        role = "test_target" if row["file_path"].startswith("tests/") else "primary_target"
        if config_goal and role == "primary_target":
            role = "configuration_target"
        _add_target(
            targets, file_path=row["file_path"], symbol=row["qualified_symbol"], role=role,
            evidence_type="changed_code", entity_type=row.get("entity_type"),
            start_line=row.get("start_line"), end_line=row.get("end_line"),
            change_status="test_coverage" if role == "test_target" else "already_changed",
            reason=f"Changed-code evidence identifies this symbol as {row['change_type']}.",
        )
        for key in configuration_references:
            targets[_target_key(row["file_path"], row["qualified_symbol"])]["reasons"].append(
                f"Parsed source references configuration key {key}."
            )

    for row in impact["retrieval"].get("query_evidence", []):
        key = (row["file_path"], row["symbol"])
        known = symbols.get(key, {})
        role = "test_target" if row["file_path"].startswith("tests/") else "primary_target"
        _add_target(
            targets, file_path=row["file_path"], symbol=row["symbol"], role=role,
            evidence_type="retrieval_evidence", entity_type=known.get("entity_type"),
            start_line=row.get("start_line"), end_line=row.get("end_line"),
            change_status="already_changed" if row["file_path"] in changed_paths else
            ("test_coverage" if role == "test_target" else "unchanged_but_related"),
            current_index_evidence=True,
            reason=f"Current developer-index retrieval selected this symbol for the goal at rank {row.get('rank')}.",
        )
        if known:
            _add_target(
                targets, file_path=row["file_path"], symbol=row["symbol"], role=role,
                evidence_type="changed_code", entity_type=known.get("entity_type"),
                start_line=known.get("start_line"), end_line=known.get("end_line"),
                change_status="already_changed",
                reason=f"Phase 64 also identifies this retrieved symbol as {known['change_type']} in a changed file.",
            )

    for row in impact["retrieval"].get("additional_related_context", []):
        if not row.get("file_path") or not row.get("symbol"):
            continue
        role = "test_target" if row["file_path"].startswith("tests/") else "related_context"
        _add_target(
            targets, file_path=row["file_path"], symbol=row["symbol"], role=role,
            evidence_type="additional_related_context", current_index_evidence=True,
            change_status="already_changed" if row["file_path"] in changed_paths else
            ("test_coverage" if role == "test_target" else "unchanged_but_related"),
            reason=f"Current retrieval included this relationship-expanded context: {row.get('reason') or 'related context'}.",
        )

    # Only resolved edges touching an already grounded goal/change target expand the plan,
    # and only by one hop. Do not recursively turn the repository graph into a plan.
    # Ambiguous diagnostics remain unresolved and never become dependencies.
    anchor_keys = set(targets)
    for edge in impact["relationships"]:
        source_key = _target_key(edge["source_file"], edge["source_symbol"])
        target_key = _target_key(edge["target_file"], edge["target_symbol"])
        if source_key not in anchor_keys and target_key not in anchor_keys:
            continue
        if edge["relationship"] in {"parent_relationship", "member_relationship"} and not (
                source_key in anchor_keys and target_key in anchor_keys):
            continue
        unanchored = target_key if source_key in anchor_keys else source_key
        if unanchored not in anchor_keys:
            _, symbol = unanchored
            if not _shares_goal_term(goal_terms, [symbol]):
                continue
        for side, other in (("source", "target"), ("target", "source")):
            path, symbol = edge[f"{side}_file"], edge[f"{side}_symbol"]
            other_symbol = edge[f"{other}_symbol"]
            known = symbols.get((path, symbol), {})
            existing = targets.get(_target_key(path, symbol))
            role = existing["role"] if existing else (
                "test_target" if path.startswith("tests/") else "supporting_target"
            )
            _add_target(
                targets, file_path=path, symbol=symbol, role=role,
                evidence_type="static_relationship", entity_type=known.get("entity_type"),
                start_line=known.get("start_line"), end_line=known.get("end_line"),
                change_status="already_changed" if path in changed_paths else
                ("test_coverage" if role == "test_target" else "unchanged_but_related"),
                reason=(f"Parsed static {edge['relationship']} connects this symbol with "
                        f"{edge[f'{other}_file']}:{other_symbol}; runtime execution is not confirmed."),
                related_symbol=other_symbol,
            )

    return sorted(targets.values(), key=lambda row: (
        -_ROLE_PRIORITY[row["role"]], row["file_path"], row["qualified_symbol"] or ""
    ))


def _preserved_behavior(impact: dict[str, Any], targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, statement: str, evidence_type: str, references: list[dict[str, Any]]) -> None:
        key = kind, statement
        if key not in seen:
            seen.add(key)
            rows.append({"kind": kind, "statement": statement,
                         "evidence_type": evidence_type, "references": references})

    target_keys = {_target_key(row["file_path"], row["qualified_symbol"]) for row in targets}
    for edge in impact["relationships"]:
        if (_target_key(edge["source_file"], edge["source_symbol"]) not in target_keys
                or _target_key(edge["target_file"], edge["target_symbol"]) not in target_keys):
            continue
        add(
            "static_dependency",
            f"Parsed source shows {edge['source_symbol']} has a {edge['relationship']} to {edge['target_symbol']}; preserve or deliberately update that source-level contract.",
            "static_relationship",
            [{"file_path": edge["source_file"], "symbol": edge["source_symbol"]},
             {"file_path": edge["target_file"], "symbol": edge["target_symbol"]}],
        )
    for symbol in impact["symbols"]:
        if _target_key(symbol["file_path"], symbol["qualified_symbol"]) not in target_keys:
            continue
        for key in _configuration_references(symbol):
            add(
                "configuration_reference",
                f"Parsed source shows {symbol['qualified_symbol']} references configuration key {key}; retain its contract unless the goal explicitly changes it.",
                "changed_code",
                [{"file_path": symbol["file_path"], "symbol": symbol["qualified_symbol"]}],
            )
    relevant_test_paths = {row["file_path"] for row in targets if row["role"] == "test_target"}
    if impact["changes"]["files"]:
        relevant_test_paths.update(_test_path(selector) for selector in impact["tests"]["selectors"])
    for path in sorted(relevant_test_paths):
        add(
            "existing_test_coverage",
            f"Existing test-selection or retrieval evidence identifies {path}; inspect its assertions before changing covered behavior.",
            "test_selection",
            [{"file_path": path}],
        )
    return rows


def _test_guidance(goal: str, impact: dict[str, Any], targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    guidance = []
    for selector in impact["tests"]["selectors"]:
        guidance.append({
            "classification": "existing_test_to_run", "test": selector,
            "reason": f"The reused Phase 62 affected-test planner selected this module at {impact['tests']['tier']}.",
            "evidence_type": "test_selection",
        })
        if impact["changes"]["files"]:
            guidance.append({
                "classification": "existing_test_to_review", "test": selector,
                "reason": "Review existing assertions for changed-code coverage; selection alone does not mean the test must be edited.",
                "evidence_type": "test_selection",
            })
    goal_terms = {term.strip(".,:;()[]{}").casefold() for term in goal.split()}
    if goal_terms & {"validation", "validate", "error", "errors", "exception", "handling", "invalid"}:
        primary = next((row for row in targets if row["role"] in {"primary_target", "configuration_target"}), None)
        if primary:
            guidance.append({
                "classification": "possible_new_regression_test", "test": None,
                "target": {"file_path": primary["file_path"], "symbol": primary["qualified_symbol"]},
                "reason": "The goal explicitly concerns validation or error handling; human review should decide whether existing selected tests cover the intended case.",
                "evidence_type": "developer_goal",
            })
    if impact["tests"]["uncertain"]:
        guidance.append({
            "classification": "manual_test_review", "test": None,
            "reason": "The affected-test planner reported uncertainty; inspect its diagnostics and unmapped changes.",
            "evidence_type": "test_selection",
        })
    return guidance


def _validation(impact: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    selected = impact["tests"]["selected_tests"]
    changed_test_modules = {
        ".".join(PurePosixPath(row["path"]).with_suffix("").parts)
        for row in impact["changes"]["files"] if row["path"].startswith("tests/") and row["path"].endswith(".py")
    }
    exact = [test for test in selected if any(test.startswith(module + ".") for module in changed_test_modules)]
    for test in exact:
        rows.append({"order": len(rows) + 1, "scope": "exact_test", "selector": test,
                     "reason": "Run the exact changed or added regression test first.", "execute": False})
    for selector in impact["tests"]["selectors"]:
        rows.append({"order": len(rows) + 1, "scope": "affected_module", "selector": selector,
                     "reason": "Run the directly affected module selected by the Phase 62 planner.", "execute": False})
    if "T2 developer suite" in impact["tests"]["required_followup"]:
        rows.append({"order": len(rows) + 1, "scope": "T2", "selector": "prototype local test --tier T2",
                     "reason": "Run the developer component gate because the planner requires it.", "execute": False})
    if impact["tests"]["tier"] == "T3":
        rows.append({"order": len(rows) + 1, "scope": "T3", "selector": "planner-selected expensive component",
                     "reason": "Run only the affected expensive subsystem before the final gate.", "execute": False})
    rows.append({"order": len(rows) + 1, "scope": "T4_final_gate",
                 "selector": "prototype local test --tier T4 --final-gate",
                 "reason": "Preserve full discovery for the final validation gate.", "execute": False})
    return rows


def _proposed_action(impact: dict[str, Any], targets: list[dict[str, Any]], goal: str) -> dict[str, Any]:
    target_paths = sorted({row["file_path"] for row in targets if row.get("file_path")})
    target_symbols = [row["qualified_symbol"] for row in targets if row.get("qualified_symbol")]
    evidence_refs = []
    for row in targets:
        evidence_refs.append({
            "file_path": row.get("file_path"),
            "symbol": row.get("qualified_symbol"),
            "role": row.get("role"),
            "evidence_types": row.get("evidence_types", []),
            "current_index_evidence": row.get("current_index_evidence", False),
            "reason": row["reasons"][0] if row.get("reasons") else None,
        })
    if not evidence_refs:
        for row in impact["retrieval"].get("query_evidence", []):
            evidence_refs.append({
                "file_path": row.get("file_path"),
                "symbol": row.get("symbol"),
                "role": "retrieval_evidence",
                "evidence_types": ["retrieval_evidence"],
                "current_index_evidence": True,
                "reason": row.get("reason"),
            })
    hashed = hashlib.sha256(f"{impact['repository']['repository_path']}\0{goal}".encode("utf-8")).hexdigest()[:12]
    return {
        "action_id": f"proposal-{hashed}",
        "action_type": "implementation_plan",
        "source_mode": "developer-local-implementation-plan",
        "schema_version": "1.0",
        "goal": goal,
        "repository_path": impact["repository"]["repository_path"],
        "target_paths": target_paths,
        "target_symbols": target_symbols,
        "evidence_refs": evidence_refs,
        "authority_required": "human_approval_required",
        "required_mutations": [],
        "status": "proposed",
        "execution_allowed": False,
    }


def _unresolved(impact: dict[str, Any], targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in impact["unresolved_relationships"]:
        rows.append({"type": "ambiguous_or_unresolved_relationship", "evidence": item,
                     "action": "Inspect the named source and candidates manually; do not treat this as a definite dependency."})
    for item in impact["changes"]["unsupported_changed_files"]:
        rows.append({"type": "unsupported_file", "evidence": item,
                     "action": "Inspect this file manually; Python evidence cannot establish its implementation behavior."})
    for item in impact["changes"]["parser_failures"]:
        rows.append({"type": "parser_failure", "evidence": item,
                     "action": "Resolve or manually inspect the parser failure before relying on symbol evidence."})
    relevant_paths = {row["file_path"] for row in targets}
    relevant_paths.update(row["path"] for row in impact["changes"]["files"])
    exclusions = impact["changes"]["token_limit_exclusions"]
    relevant_exclusions = [item for item in exclusions if item.get("file_path") in relevant_paths]
    for item in relevant_exclusions:
        rows.append({"type": "token_limit_exclusion", "evidence": item,
                     "action": "Inspect the excluded source directly; it was not valid retrieval evidence."})
    unrelated_exclusions = exclusions[len(relevant_exclusions):] if not relevant_exclusions else [
        item for item in exclusions if item not in relevant_exclusions
    ]
    if unrelated_exclusions:
        rows.append({"type": "token_limit_exclusion_summary",
                     "evidence": {"count": len(unrelated_exclusions),
                                  "files": sorted({item.get("file_path") for item in unrelated_exclusions})},
                     "action": "These exclusions did not intersect a current target; inspect them if the goal scope expands."})
    freshness = impact["index_freshness"]
    if freshness["status"] != "current":
        rows.append({"type": "index_not_current", "evidence": freshness,
                     "action": f"Run prototype local index \"{impact['repository']['repository_path']}\" after review; this plan does not reindex automatically."})
    context = impact["retrieval"].get("context_diagnostics", {})
    for item in context.get("relationship_diagnostics", []):
        rows.append({"type": "retrieval_relationship_diagnostic", "evidence": item,
                     "action": "Review this unresolved retrieval relationship manually."})
    for item in context.get("omitted_context", []):
        rows.append({"type": "omitted_context", "evidence": item,
                     "action": "Inspect omitted context if the implementation depends on it."})
    if not targets:
        rows.append({"type": "missing_implementation_evidence",
                     "evidence": {"goal": impact["retrieval"].get("question")},
                     "action": "Refine the goal, build a current index if needed, or identify a target through human inspection."})
    rows.append({"type": "runtime_behavior_unverified",
                 "evidence": {"basis": "static parsed-source analysis"},
                 "action": "Confirm dynamic imports, generated code, dispatch, and runtime behavior during implementation review."})
    return rows


def _steps(targets: list[dict[str, Any]], preserved: list[dict[str, Any]],
           guidance: list[dict[str, Any]], impact: dict[str, Any]) -> list[dict[str, Any]]:
    primary = [{"file_path": row["file_path"], "symbol": row["qualified_symbol"]}
               for row in targets if row["role"] in {"primary_target", "configuration_target"}]
    supporting = [{"file_path": row["file_path"], "symbol": row["qualified_symbol"]}
                  for row in targets if row["role"] in {"supporting_target", "related_context"}]
    rows = []
    if primary:
        rows.append({"order": 1, "action": "Inspect the primary targets and their existing source-level contracts.",
                     "target_references": primary, "evidence_basis": ["changed_code", "retrieval_evidence", "static_relationship"],
                     "expected_validation": "Confirm that the intended goal maps to these exact symbols before editing."})
        rows.append({"order": 2, "action": "Change the narrowest supported implementation boundary.",
                     "target_references": primary, "evidence_basis": sorted({e for row in targets for e in row["evidence_types"]}),
                     "expected_validation": "Review the change against each cited target reason; do not expand to unevidenced files."})
    if supporting:
        rows.append({"order": len(rows) + 1, "action": "Inspect related callers, imports, helpers, and configuration context before changing contracts.",
                     "target_references": supporting, "evidence_basis": ["static_relationship", "additional_related_context"],
                     "expected_validation": "Verify static relationships manually where runtime dispatch could differ."})
    if preserved:
        rows.append({"order": len(rows) + 1, "action": "Preserve or deliberately revise the identified existing behavior.",
                     "target_references": [ref for row in preserved for ref in row["references"]],
                     "evidence_basis": sorted({row["evidence_type"] for row in preserved}),
                     "expected_validation": "Existing assertions and source-level contracts remain satisfied or receive reviewed updates."})
    if guidance:
        rows.append({"order": len(rows) + 1, "action": "Review existing coverage and add a focused regression case only where the goal is not already covered.",
                     "target_references": [{"test": row.get("test"), **row.get("target", {})} for row in guidance],
                     "evidence_basis": ["developer_goal", "test_selection"],
                     "expected_validation": "Run exact tests first, followed by affected modules."})
    rows.append({"order": len(rows) + 1, "action": "Follow the recommended validation sequence without automatic execution.",
                 "target_references": [], "evidence_basis": ["test_selection"],
                 "expected_validation": f"Use the planner-selected {impact['tests']['tier']} scope and preserve T4 for the final gate."})
    return rows


def plan_change(workspace: DeveloperWorkspace, repository: Path, *, goal: str,
                base: str | None = None, top_k: int = 10) -> dict[str, Any]:
    """Build and externally record a read-only plan from Phase 64 evidence."""
    if not isinstance(goal, str) or not goal.strip():
        raise LocalWorkflowError("goal must be nonempty text.")
    goal = " ".join(goal.split())
    impact = analyze_change_impact(workspace, repository, base=base, question=goal, top_k=top_k)
    targets = _implementation_targets(impact, goal)
    preserved = _preserved_behavior(impact, targets)
    guidance = _test_guidance(goal, impact, targets)
    unresolved = _unresolved(impact, targets)

    non_test_targets = [row for row in targets if row["role"] != "test_target"]
    freshness = impact["index_freshness"]["status"]
    unsupported = impact["changes"]["unsupported_changed_files"]
    if not non_test_targets or (freshness == "unsupported" and unsupported):
        status = "manual_review_required"
    elif freshness != "current" or impact["unresolved_relationships"]:
        status = "limited"
    else:
        status = "completed"

    limitations = list(impact["limitations"])
    if freshness != "current":
        limitations.append("Goal retrieval is unavailable or invalid because the developer index is not current; the plan is incomplete.")
    if status == "manual_review_required":
        limitations.append("Repository evidence is insufficient to identify a supported implementation target; human inspection is required.")
    payload = {
        "mode": "developer-local-implementation-plan",
        "status": status,
        "goal": goal,
        "repository": impact["repository"],
        "change_impact": {
            "run_id": impact["run_id"], "changes": impact["changes"], "symbols": impact["symbols"],
            "relationships": impact["relationships"], "unresolved_relationships": impact["unresolved_relationships"],
            "index_freshness": impact["index_freshness"], "retrieval": impact["retrieval"],
            "recommended_actions": impact["recommended_actions"],
        },
        "proposed_action": _proposed_action(impact, targets, goal),
        "implementation_targets": targets,
        "preserved_behavior": preserved,
        "implementation_steps": _steps(targets, preserved, guidance, impact),
        "tests": impact["tests"],
        "tests_to_update_or_review": guidance,
        "recommended_validation": _validation(impact),
        "unresolved_evidence": unresolved,
        "limitations": list(dict.fromkeys(limitations)),
        "tests_executed": False,
        "source_changes_made": False,
    }
    inventory = scan_local_repository(Path(repository))
    payload["run_id"] = workspace._record_run("plan-change", inventory, payload)
    return payload
