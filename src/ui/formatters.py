"""Pure presentation helpers for Phase 65/66 planning evidence."""

from collections import defaultdict
from typing import Any


TARGET_ROLES = (
    "primary_target", "configuration_target", "supporting_target",
    "test_target", "related_context", "manual_review",
)

ROLE_LABELS = {
    "primary_target": "Primary target",
    "configuration_target": "Configuration target",
    "supporting_target": "Supporting target",
    "test_target": "Test target",
    "related_context": "Related context",
    "manual_review": "Manual review",
}

RETAINED_PROOF_KINDS = {
    "exact_retained_primary_leaf",
    "exact_retained_test_leaf",
    "exact_retained_leaf_evidence",
}


def _rows(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _find_retained_proofs(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def visit(item: Any, container: Any = None, warning_type: Any = None) -> None:
        if isinstance(item, dict):
            warning_type = item.get("type", warning_type)
            if item.get("kind") in RETAINED_PROOF_KINDS or item.get("proof_kind") in RETAINED_PROOF_KINDS:
                found.append({"warning_type": warning_type, "container": container, "proof": item})
                return
            for key, child in item.items():
                visit(child, child if key == "container" else container, warning_type)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child, container, warning_type)

    visit(value)
    return found


def format_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Prepare display groupings while retaining all backend values verbatim."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for target in _rows(plan.get("implementation_targets")):
        if isinstance(target, dict):
            role = target.get("role")
            grouped[role if isinstance(role, str) else "unavailable"].append(target)

    tests = plan.get("tests") if isinstance(plan.get("tests"), dict) else {}
    proposal = plan.get("proposed_action") if isinstance(plan.get("proposed_action"), dict) else {}
    impact = plan.get("change_impact") if isinstance(plan.get("change_impact"), dict) else {}
    freshness = impact.get("index_freshness") if isinstance(impact.get("index_freshness"), dict) else {}
    unresolved = _rows(plan.get("unresolved_evidence"))
    warnings = _rows(plan.get("warnings"))
    selection = tests.get("expected_test_selection")
    return {
        "status": plan.get("status"),
        "goal": plan.get("goal"),
        "run_id": plan.get("run_id"),
        "repository": plan.get("repository"),
        "change_impact": impact,
        "index_freshness": freshness,
        "proposed_action": proposal,
        "targets_by_role": dict(grouped),
        "selected_tests": _rows(tests.get("selected_tests")),
        "test_selection": selection,
        "test_evidence": _rows(selection.get("evidence")) if isinstance(selection, dict) else [],
        "test_uncertainty": _rows(selection.get("uncertainty")) if isinstance(selection, dict) else [],
        "unresolved_evidence": unresolved,
        "warnings": warnings,
        "retained_leaf_proofs": _find_retained_proofs(warnings),
        "preserved_behavior": _rows(plan.get("preserved_behavior")),
        "implementation_steps": _rows(plan.get("implementation_steps")),
        "recommended_validation": _rows(plan.get("recommended_validation")),
        "limitations": _rows(plan.get("limitations")),
        "tests_to_update_or_review": plan.get("tests_to_update_or_review"),
    }


def role_label(role: str) -> str:
    """Return a friendly role label while keeping the exact role explicit."""
    return f"{ROLE_LABELS.get(role, role)} ({role})"
