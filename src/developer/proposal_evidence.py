"""Validate the stored Phase 65/66 evidence before accepting a patch candidate."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .implementation_planning import ProposedAction, _bind_expected_tests
from .local_workflow import DeveloperWorkspace, LocalWorkflowError, scan_local_repository


def validated_plan(workspace: DeveloperWorkspace, repository: Path,
                   run_id: str, *, require_current: bool = True) -> tuple[dict[str, Any], ProposedAction]:
    # Reuse the canonical Phase 71 run reader and typed proposal validation.
    from .execution_verification import _proposal, _read_run

    root = Path(repository).expanduser().resolve(strict=True)
    workspace._prepare(root)
    metadata, plan = _read_run(workspace, run_id, "plan")
    try:
        impact_ref = plan["change_impact"]["run_id"]
        impact_meta, impact = _read_run(workspace, impact_ref, "impact")
        proposal = _proposal(plan["proposed_action"])
        recomputed = ProposedAction.from_plan(plan["change_impact"],
                                               plan["implementation_targets"],
                                               plan["goal"], plan["unresolved_evidence"])
        selection = plan["tests"]["expected_test_selection"]
        selected = plan["tests"]["selected_tests"]
        evidence = selection["evidence"]
        if (plan["mode"] != "developer-local-implementation-plan"
                or plan["status"] != "completed"
                or metadata["repository_path"] != str(root)
                or impact_meta["repository_path"] != str(root)
                or metadata["repository_id"] != impact_meta["repository_id"]
                or plan["repository"] != plan["change_impact"]["repository"]
                or plan["repository"] != impact["repository"]
                or proposal.to_dict() != recomputed.to_dict()
                or plan["tests"] != plan["change_impact"]["tests"]
                or selection["selected_tests"] != selected
                or not selected or selection["status"] != "known"
                or sorted(set(selected)) != selected
                or sorted(row["test"] for row in evidence) != selected
                or any(not row.get("source") or not row.get("target_paths") for row in evidence)
                or metadata["commit_sha"] != proposal.current_commit
                or metadata["working_tree_sha256"] != proposal.working_tree_sha256
                or impact_meta["commit_sha"] != impact["repository"]["current_commit"]
                or impact_meta["working_tree_sha256"] != impact["repository"]["working_tree_sha256"]):
            raise ValueError("plan, proposal, expected tests, or repository bindings differ")
        copied = {"repository": "repository", "changes": "changes", "symbols": "symbols",
                  "relationships": "relationships", "unresolved_relationships": "unresolved_relationships",
                  "index_freshness": "index_freshness", "retrieval": "retrieval",
                  "recommended_actions": "recommended_actions"}
        if any(plan["change_impact"][target] != impact[source]
               for target, source in copied.items()):
            raise ValueError("Phase 64 evidence differs from the stored plan")
        if require_current:
            inventory = scan_local_repository(root)
            if (inventory.repository_id != proposal.repository_id
                    or inventory.commit_sha != proposal.current_commit
                    or inventory.snapshot_id != proposal.working_tree_sha256):
                raise ValueError("upstream plan is stale; replan before drafting")
            explicit = tuple(selected) if selection.get("confidence") == "developer_selected" else ()
            expected = _bind_expected_tests(root, impact, plan["implementation_targets"], explicit)
            if expected != selection:
                raise ValueError("expected-test evidence differs from current planned targets")
        return plan, proposal
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise LocalWorkflowError(f"Phase 65/66 evidence validation failed: {error}") from error
