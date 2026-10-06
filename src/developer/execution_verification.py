"""Deterministic Phase 71 verification of one Phase 65-70 evidence chain."""
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .implementation_planning import ProposedAction
from .local_workflow import (DeveloperWorkspace, LocalWorkflowError, _digest, _git,
                             _git_index_state, _json_bytes, scan_local_repository)
from .patch_application import _load_authorization
from .patch_authorization import _read_patch_run
from .test_execution import _read_execution, _validate_phase69

_RECORD_COMMAND = "verify-execution"
_EXPECTED_RUNS = {
    "impact": ("change-impact", "developer-local-change-impact"),
    "plan": ("plan-change", "developer-local-implementation-plan"),
    "proposal": ("plan-change", "developer-local-implementation-plan"),
    "patch": ("draft-patch", "developer-local-patch-draft"),
    "approval": ("review-patch", "developer-local-patch-authorization"),
    "execution": ("apply-patch", "developer-local-patch-application"),
    "observation": ("test-applied-patch", "developer-local-test-observation"),
    "verification": ("verify-execution", "developer-local-execution-verification"),
}


@dataclass(frozen=True, slots=True)
class ExecutionVerificationSummary:
    verification_id: str
    schema_version: str
    status: str
    repository_id: str
    repository_path: str
    plan_run_id: str
    proposal_id: str
    patch_id: str
    authorization_id: str
    execution_id: str
    execution_run_id: str
    test_plan_id: str
    observation_id: str
    observation_run_id: str
    expected_target_paths: tuple[str, ...]
    approved_target_paths: tuple[str, ...]
    actual_changed_paths: tuple[str, ...]
    expected_test_identities: tuple[str, ...]
    executed_test_identities: tuple[str, ...]
    missing_test_identities: tuple[str, ...]
    unexpected_test_identities: tuple[str, ...]
    test_outcome: dict[str, Any]
    repository_state_comparison: dict[str, Any]
    deviations: tuple[str, ...]
    unexpected_changes: tuple[str, ...]
    unresolved_uncertainty: tuple[str, ...]
    warnings: tuple[str, ...]
    evidence_references: tuple[dict[str, str], ...]
    lifecycle_transition_performed: bool = False
    source_mutation_performed: bool = False
    git_staging_performed: bool = False
    git_commit_created: bool = False
    phase72_started: bool = False

    def to_dict(self) -> dict[str, Any]:
        list_fields = {"expected_target_paths", "approved_target_paths", "actual_changed_paths", "expected_test_identities",
                       "executed_test_identities", "missing_test_identities", "unexpected_test_identities",
                       "deviations", "unexpected_changes",
                       "unresolved_uncertainty", "warnings", "evidence_references"}
        return {field.name: (list(getattr(self, field.name)) if field.name in list_fields
                             else getattr(self, field.name)) for field in fields(self)}


def _read_run(workspace: DeveloperWorkspace, run_id: str, kind: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if not re.fullmatch(r"[0-9a-f]{20}", run_id):
        raise LocalWorkflowError(f"Invalid Phase 71 {kind} run ID.")
    directory = workspace._contained(workspace.root / "runs" / run_id)
    try:
        meta_bytes, payload_bytes = (directory / "metadata.json").read_bytes(), (directory / "results.json").read_bytes()
        meta, payload = json.loads(meta_bytes), json.loads(payload_bytes)
        command, mode = _EXPECTED_RUNS[kind]
        if (not isinstance(meta, dict) or not isinstance(payload, dict)
                or meta_bytes != _json_bytes(meta) or payload_bytes != _json_bytes(payload)
                or meta.get("schema_version") != "developer-local-run-v1"
                or meta.get("mode") != "developer-local" or meta.get("run_id") != run_id
                or meta.get("command") != command or meta.get("workspace_sha256") != _digest(str(workspace.root).encode())
                or payload.get("mode") != mode or payload.get("run_id") not in (None, run_id)):
            raise ValueError("record envelope mismatch")
        identity = {"mode": "developer-local", "command": command,
                    "repository_id": meta.get("repository_id"),
                    "working_tree_sha256": meta.get("working_tree_sha256"), "payload": payload}
        if (_digest(_json_bytes(identity))[:20] != run_id
                or meta.get("repository_id") != payload.get("repository_id", meta.get("repository_id"))):
            raise ValueError("content identity mismatch")
        return meta, payload
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise LocalWorkflowError(f"Phase 71 {kind} evidence is missing, malformed, or tampered.") from error


def _proposal(value: dict[str, Any]) -> ProposedAction:
    try:
        content = dict(value)
        for name in ("target_paths", "target_symbols", "evidence_refs", "unresolved_evidence",
                     "required_mutations"):
            content[name] = tuple(content[name])
        proposal = ProposedAction(**content)
        if proposal.to_dict() != value:
            raise ValueError("proposal differs from canonical contract")
        return proposal
    except (KeyError, TypeError, ValueError) as error:
        raise LocalWorkflowError("Phase 66 ProposedAction integrity validation failed.") from error


def _patch_hunk_lines(value: str) -> tuple[str, ...]:
    rows = []
    for line in value.splitlines():
        if not line.startswith(("@@", " ", "+", "-", "\\")):
            continue
        if line.startswith("@@"):
            match = re.match(r"^(@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@)", line)
            line = match.group(1) if match else line
        rows.append(line)
    return tuple(rows)


def verify_execution(workspace: DeveloperWorkspace, repository: Path, execution_run_id: str,
                     observation_run_id: str) -> dict[str, Any]:
    """Verify and record one exact execution/observation chain; never mutates the target."""
    root = Path(repository).expanduser().resolve(strict=True)
    workspace._prepare(root)
    deviations: list[str] = []
    uncertainty: list[str] = []
    warnings: list[str] = []
    unexpected: set[str] = set()
    refs: list[dict[str, str]] = []

    def load(kind: str, identifier: str):
        meta, payload = _read_run(workspace, identifier, kind)
        refs.append({"phase": kind, "run_id": identifier,
                     "record_sha256": hashlib.sha256(_json_bytes(payload)).hexdigest()})
        return meta, payload

    # Resolve the exact user-selected Phase 69 execution and linked Phase 68/67 evidence.
    execution_meta, execution = load("execution", execution_run_id)
    if str(Path(execution_meta.get("repository_path", "")).resolve()) != str(root):
        deviations.append("phase69_execution_run_metadata_repository_mismatch")
    if (execution.get("status") != "applied" or execution.get("tests_executed") is not False
            or execution.get("git_commit_created") is not False or execution.get("git_staging_performed") is not False):
        deviations.append("phase69_execution_not_successfully_applied")
    execution_id = "execution-" + hashlib.sha256(
        (execution.get("authorization_id", "") + execution.get("source_patch_id", "")).encode()).hexdigest()[:20]
    if execution.get("execution_id") != execution_id:
        deviations.append("phase69_execution_identity_mismatch")

    auth_matches = []
    for entry in (workspace.root / "runs").iterdir():
        try:
            candidate = json.loads((entry / "results.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if candidate.get("mode") == "developer-local-patch-authorization" and candidate.get("authorization_id") == execution.get("authorization_id"):
            auth_matches.append(entry.name)
    if len(auth_matches) != 1:
        deviations.append("phase68_approval_missing_or_ambiguous")
        authorization = None
        approval_meta = {}
    else:
        approval_meta, approval_payload = load("approval", auth_matches[0])
        try:
            authorization = _load_authorization(workspace, auth_matches[0])
            if str(Path(approval_meta.get("repository_path", "")).resolve()) != str(root):
                deviations.append("phase68_approval_run_metadata_repository_mismatch")
            if (authorization.decision != "approve" or authorization.execution_authorized is not True
                    or authorization.source_action_id != execution.get("source_action_id")
                    or authorization.source_patch_id != execution.get("source_patch_id")
                    or authorization.authorization_id != execution.get("authorization_id")):
                deviations.append("phase68_approval_does_not_match_phase69_execution")
        except LocalWorkflowError:
            authorization = None
            deviations.append("phase68_approval_integrity_validation_failed")

    patch_run_id = authorization.source_patch_run_id if authorization else ""
    try:
        patch_meta, patch_payload = load("patch", patch_run_id)
        draft = _read_patch_run(workspace, patch_run_id)
        if authorization is None:
            deviations.append("phase67_patch_cannot_be_linked_without_phase68_approval")
    except (LocalWorkflowError, AttributeError):
        patch_meta, patch_payload, draft = {}, {}, None
        deviations.append("phase67_patch_evidence_missing_or_invalid")
    if draft is not None:
        if str(Path(patch_meta.get("repository_path", "")).resolve()) != str(root):
            deviations.append("phase67_patch_run_metadata_repository_mismatch")
        patch_hash = hashlib.sha256(draft.patch_text.encode()).hexdigest()
        if (draft.status != "draft" or patch_hash != execution.get("patch_sha256")
                or patch_hash != (authorization.patch_sha256 if authorization else None)
                or draft.patch_id != execution.get("source_patch_id")
                 or not set(execution.get("target_paths", ())) <= set(draft.target_paths)):
            deviations.append("phase67_patch_identity_hash_or_scope_mismatch")

    # Follow the Phase 67 source action to its exact Phase 65 plan run.
    bound_plan_run_id = patch_payload.get("source_plan_run_id") if draft is not None else None
    plan_matches = [bound_plan_run_id] if bound_plan_run_id else []
    if not bound_plan_run_id:
        for entry in (workspace.root / "runs").iterdir():
            try:
                candidate = json.loads((entry / "results.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            action = candidate.get("proposed_action", {})
            if candidate.get("mode") == "developer-local-implementation-plan" and action.get("action_id") == execution.get("source_action_id"):
                plan_matches.append(entry.name)
    if len(plan_matches) != 1:
        deviations.append("phase65_plan_missing_or_ambiguous")
        plan_meta, plan = {}, {}
        proposal = None
    else:
        plan_meta, plan = load("plan", plan_matches[0])
        if draft is not None and patch_payload.get("source_plan_run_id") is not None \
                and patch_payload.get("source_plan_run_id") != plan_matches[0]:
            deviations.append("phase67_draft_source_plan_run_id_mismatch")
        if (str(Path(plan_meta.get("repository_path", "")).resolve()) != str(root)
                or plan.get("repository", {}).get("repository_id") != execution.get("repository_id")):
            deviations.append("phase65_plan_run_metadata_repository_mismatch")
        try:
            proposal = _proposal(plan["proposed_action"])
        except (KeyError, LocalWorkflowError):
            proposal = None
            deviations.append("phase66_proposed_action_missing_or_invalid")
    expected_tests: tuple[str, ...] = ()
    if proposal is not None and draft is not None:
        targets = set(proposal.target_paths)
        plan_expected = {row.get("file_path") for row in plan.get("implementation_targets", []) if row.get("file_path")}
        plan_symbols = {row.get("qualified_symbol") for row in plan.get("implementation_targets", []) if row.get("qualified_symbol")}
        if (proposal.action_id != draft.source_action_id or proposal.repository_id != draft.repository_id
                or str(Path(proposal.repository_path).resolve()) != str(root)
                or not set(draft.target_paths) <= targets
                or not draft.target_paths
                or proposal.target_symbols != draft.target_symbols
                or proposal.target_symbols != tuple(sorted(plan_symbols))
                or proposal.evidence_refs != draft.evidence_refs
                or proposal.unresolved_evidence != draft.unresolved_evidence
                or targets != plan_expected):
            deviations.append("phase65_plan_and_phase66_proposal_scope_or_evidence_mismatch")
        if plan.get("status") != "completed":
            uncertainty.append("phase65_plan_status_is_not_completed")
        unresolved_rows = plan.get("unresolved_evidence", [])
        informational_types = {"runtime_behavior_unverified", "token_limit_exclusion_summary"}
        blocking_rows = [row for row in unresolved_rows if row.get("type") not in informational_types]
        if blocking_rows or any(row.get("type") not in informational_types
                                for row in proposal.unresolved_evidence):
            uncertainty.append("phase65_plan_contains_blocking_unresolved_evidence")
        if unresolved_rows and not blocking_rows:
            warnings.append("phase65_static_plan_retains_runtime_behavior_uncertainty_outside_executed_test_scope")
        expected_proposal = ProposedAction.from_plan(
            plan.get("change_impact", {}), plan.get("implementation_targets", []),
            plan.get("goal", ""), plan.get("unresolved_evidence", []))
        if expected_proposal.to_dict() != proposal.to_dict():
            deviations.append("phase66_proposal_does_not_match_phase65_plan_content")
        tests = plan.get("tests", {})
        if tests.get("expected_test_selection") is not None \
                and tests != plan.get("change_impact", {}).get("tests"):
            deviations.append("phase65_expected_tests_differ_from_plan_impact")
        expected_tests = tuple(sorted(set(tests.get("selected_tests", ()))))
        bound_selection = tests.get("expected_test_selection")
        if bound_selection is not None:
            evidence = bound_selection.get("evidence", ())
            if (bound_selection.get("status") != "known"
                    or bound_selection.get("selected_tests") != list(expected_tests)
                    or sorted(row.get("test") for row in evidence if isinstance(row, dict)) != list(expected_tests)
                    or any(not isinstance(row, dict) or not row.get("source") or not row.get("target_paths")
                           for row in evidence)):
                uncertainty.append("phase65_expected_test_selection_unknown_or_unevidenced")
        if not expected_tests and tests.get("selectors"):
            deviations.append("phase65_plan_did_not_record_exact_expected_test_identities")
        elif expected_tests:
            expected_modules = set(tests.get("selectors", ()))
            if not all(any(identity.startswith(module + ".") for identity in expected_tests)
                       for module in expected_modules):
                deviations.append("phase65_exact_test_set_does_not_cover_selected_test_modules")

    # Phase 70 carries the plan in its observation record; validate observation/run linkage.
    observation_meta, observation = load("observation", observation_run_id)
    if str(Path(observation_meta.get("repository_path", "")).resolve()) != str(root):
        deviations.append("phase70_observation_run_metadata_repository_mismatch")
    test_plan = observation.get("plan", {})
    test_plan_id = test_plan.get("plan_id", "")
    selected_tests = tuple(sorted(set(test_plan.get("test_identities", ()))))
    original_selected_tests = tuple(test_plan.get("test_identities", ()))
    missing_tests = tuple(sorted(set(expected_tests) - set(selected_tests)))
    extra_tests = tuple(sorted(set(selected_tests) - set(expected_tests)))
    plan_identity = {"schema_version": "1.0", "source_execution_id": test_plan.get("source_execution_id"),
                     "repository_id": observation.get("repository_id"), "repository_state": test_plan.get("repository_state"),
                     "target_paths": list(test_plan.get("target_paths", ())), "test_runner": test_plan.get("test_runner"),
                     "test_identities": list(test_plan.get("test_identities", ())),
                     "selection_source": test_plan.get("selection_source")}
    if (not test_plan_id or test_plan_id != "test-plan-" + hashlib.sha256(_json_bytes(plan_identity)).hexdigest()[:20]):
        deviations.append("phase70_test_plan_identity_mismatch")
    if not re.fullmatch(r"observation-[0-9a-f]{20}", observation.get("observation_id", "")):
        deviations.append("phase70_observation_identity_malformed")
    if (observation.get("source_execution_id") != execution.get("execution_id")
            or observation.get("source_authorization_id") != execution.get("authorization_id")
            or observation.get("source_patch_id") != execution.get("source_patch_id")
            or observation.get("source_action_id") != execution.get("source_action_id")
            or observation.get("repository_id") != execution.get("repository_id")
            or str(Path(observation.get("repository_path", "")).resolve()) != str(root)
            or test_plan.get("source_execution_id") != execution.get("execution_id")
            or test_plan.get("repository_id") != execution.get("repository_id")
            or set(test_plan.get("target_paths", ())) != set(execution.get("target_paths", ()))):
        deviations.append("phase70_observation_is_bound_to_another_execution_or_repository")
    if expected_tests != selected_tests:
        deviations.append("phase65_expected_tests_differ_from_phase70_executed_tests")
    if observation.get("test_identities") != test_plan.get("test_identities"):
        deviations.append("phase70_observation_test_identities_differ_from_its_plan")
    if original_selected_tests != selected_tests:
        deviations.append("phase70_test_plan_test_identities_are_not_canonical_or_unique")
    from src.developer_testing import catalog
    known_tests = {name for rows in catalog(root).values() for name in rows}
    if not selected_tests or any(identity not in known_tests for identity in selected_tests):
        deviations.append("phase70_test_plan_contains_unknown_test_identities")
    if plan.get("tests", {}).get("uncertain"):
        if (plan.get("tests", {}).get("exhaustive_required") is True
                and expected_tests == selected_tests == tuple(sorted(known_tests))):
            warnings.append("phase65_test_selection_escalated_to_exhaustive_and_phase70_ran_the_complete_exact_inventory")
        else:
            uncertainty.append("phase65_affected_test_selection_is_uncertain")
    stdout_path = Path(observation.get("stdout_reference", ""))
    stderr_path = Path(observation.get("stderr_reference", ""))
    try:
        evidence_root = workspace._contained(workspace.root / "evidence" / observation.get("observation_id", ""))
        if (stdout_path.resolve() != (evidence_root / "stdout.log").resolve()
                or stderr_path.resolve() != (evidence_root / "stderr.log").resolve()
                or hashlib.sha256(stdout_path.read_bytes()).hexdigest() != observation.get("stdout_sha256")
                or hashlib.sha256(stderr_path.read_bytes()).hexdigest() != observation.get("stderr_sha256")):
            deviations.append("phase70_external_log_hash_or_reference_mismatch")
    except (OSError, LocalWorkflowError, RuntimeError):
        deviations.append("phase70_external_logs_missing_or_outside_workspace")
    if observation.get("unexpected_repository_changes"):
        unexpected.update(observation.get("unexpected_changed_paths", ()))
        deviations.append("phase70_observation_reports_unexpected_repository_changes")
    if observation.get("status") != "passed" or observation.get("exit_code") != 0:
        deviations.append("phase70_tests_did_not_pass")
    if observation.get("errors") or observation.get("failures"):
        deviations.append("phase70_test_failures_or_errors_present")
    if int(observation.get("tests_run", 0)) != sum(int(observation.get(key, 0)) for key in ("passed", "failures", "errors", "skipped")):
        deviations.append("phase70_test_result_counts_are_inconsistent")
    if observation.get("status") == "passed" and (observation.get("exit_code") != 0
            or observation.get("failures") or observation.get("errors")):
        deviations.append("phase70_passed_status_conflicts_with_test_counts_or_exit_code")
    if observation.get("status") in {"failed", "error"} and observation.get("exit_code") == 0 and not observation.get("failures") and not observation.get("errors"):
        deviations.append("phase70_failure_status_conflicts_with_test_counts_or_exit_code")

    # Validate the full historical chain with Phase 70's authoritative validator.
    try:
        validated_execution, validated_auth, _ = _validate_phase69(workspace, root, execution_run_id)
        if validated_execution != execution or validated_auth.authorization_id != execution.get("authorization_id"):
            deviations.append("phase69_revalidated_chain_mismatch")
    except (LocalWorkflowError, OSError, ValueError) as error:
        deviations.append("phase69_historical_execution_invalid:" + str(error))

    # Distinguish historical application state from today's repository facts.
    inventory = scan_local_repository(root)
    head = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode().strip()
    semantic_index = hashlib.sha256(_git_index_state(root)).hexdigest()
    refs_hash = hashlib.sha256(_git(root, ["for-each-ref", "--format=%(refname) %(objectname)"])).hexdigest()
    from .patch_application import _status as git_status
    current_status = git_status(root).decode("utf-8", errors="replace")
    actual_diff = _git(root, ["diff", "--no-ext-diff", "--binary", "--", *execution.get("target_paths", ())]).decode("utf-8", errors="replace")
    changed_paths = tuple(sorted(line[3:].split(" -> ")[-1] for line in current_status.splitlines() if len(line) >= 4))
    approved_paths = tuple(sorted(authorization.target_paths if authorization else ()))
    actual_paths = tuple(sorted(execution.get("files_changed", ())))
    if not set(actual_paths) <= set(approved_paths):
        deviations.append("phase69_actual_changed_paths_exceed_approved_paths")
    if not set(actual_paths) <= set(proposal.target_paths if proposal is not None else ()):
        deviations.append("phase69_actual_changed_paths_exceed_phase66_proposed_scope")
    if actual_diff != execution.get("diff_after"):
        deviations.append("phase69_recorded_diff_or_current_postimage_mismatch")
    if draft is not None:
        actual_hunks, approved_hunks = _patch_hunk_lines(actual_diff), _patch_hunk_lines(draft.patch_text)
        if actual_hunks != approved_hunks:
            deviations.append("phase69_actual_diff_hunks_differ_from_approved_patch")
        section_paths = {new for _, new in re.findall(r"(?m)^diff --git a/(.*?) b/(.*?)$", actual_diff)}
        if section_paths != set(actual_paths):
            deviations.append("phase69_recorded_diff_paths_differ_from_actual_scope")
    expected_state = execution.get("working_tree_after")
    current_state_matches = inventory.snapshot_id == expected_state
    repository_comparison = {
        "historical_head_before": execution.get("repository_before"),
        "historical_head_after": execution.get("repository_after"), "current_head": head,
        "head_unchanged_since_execution": head == execution.get("repository_after"),
        "historical_semantic_index_sha256": execution.get("semantic_index_sha256"),
        "current_semantic_index_sha256": semantic_index,
        "current_refs_sha256": refs_hash,
        "historical_working_tree_after": expected_state,
        "current_working_tree": inventory.snapshot_id,
        "current_working_tree_matches_execution": current_state_matches,
        "current_changed_paths": list(changed_paths),
        "current_status_clean": not current_status,
    }
    if not current_state_matches or head != execution.get("repository_after") or changed_paths != actual_paths:
        deviations.append("current_repository_is_stale_or_drifted_from_phase69_poststate")
        unexpected.update(changed_paths)
    if execution.get("repository_before") != execution.get("repository_after"):
        deviations.append("phase69_head_changed_during_application")
    try:
        index_digest = execution.get("semantic_index_sha256")
        refs_digest = execution.get("refs_sha256")
        if not index_digest or not refs_digest:
            deviations.append("phase69_semantic_git_state_evidence_missing")
        if index_digest and index_digest != semantic_index:
            deviations.append("current_semantic_git_index_differs_from_phase69")
        if refs_digest and refs_digest != refs_hash:
            deviations.append("current_git_refs_differ_from_phase69")
        if execution.get("semantic_index_unchanged") is not True:
            deviations.append("phase69_semantic_git_index_changed_during_application")
        if execution.get("refs_unchanged") is not True:
            deviations.append("phase69_git_refs_changed_during_application")
    except TypeError:
        deviations.append("phase69_git_state_evidence_malformed")

    verification_status = "verified" if not deviations and not uncertainty and not unexpected else (
        "not_verified" if deviations or unexpected else "uncertain")
    test_outcome = {key: observation.get(key) for key in (
        "tests_run", "passed", "failures", "errors", "skipped", "exit_code", "status",
        "stdout_sha256", "stderr_sha256", "stdout_reference", "stderr_reference",
        "unexpected_repository_changes", "unexpected_changed_paths", "repository_state_before",
        "repository_state_after")}
    identity_payload = {"execution_run_id": execution_run_id, "observation_run_id": observation_run_id,
                        "repository_id": execution.get("repository_id"), "status": verification_status,
                        "deviations": sorted(set(deviations)), "uncertainty": sorted(set(uncertainty)),
                        "warnings": sorted(set(warnings)), "actual_paths": list(actual_paths),
                        "selected_tests": list(selected_tests), "repository_state": repository_comparison,
                        "test_outcome": test_outcome}
    verification_id = "verification-" + hashlib.sha256(_json_bytes(identity_payload)).hexdigest()[:20]
    summary = ExecutionVerificationSummary(
        verification_id, "1.0", verification_status, execution.get("repository_id", ""), str(root),
        plan_matches[0] if plan_matches else "", execution.get("source_action_id", ""),
        execution.get("source_patch_id", ""), execution.get("authorization_id", ""),
        execution.get("execution_id", ""), execution_run_id, test_plan_id,
        observation.get("observation_id", ""), observation_run_id,
        tuple(proposal.target_paths if proposal is not None else execution.get("target_paths", ())),
        approved_paths, actual_paths, expected_tests, selected_tests,
        missing_tests, extra_tests,
        test_outcome, repository_comparison, tuple(sorted(set(deviations))), tuple(sorted(unexpected)),
        tuple(sorted(set(uncertainty))), tuple(sorted(set(warnings))), tuple(refs))
    payload = {"mode": "developer-local-execution-verification", **summary.to_dict(),
               "human_review_required": True, "lifecycle_decision": "none",
               "automatic_followup": False, "repair_performed": False, "retry_performed": False,
               "rollback_performed": False}
    verify_inventory = scan_local_repository(root)
    payload["run_id"] = workspace._record_run(_RECORD_COMMAND, verify_inventory, payload)
    return payload
