"""Read-only, evidence-bound Phase 72 follow-up evaluation."""
from __future__ import annotations

from dataclasses import dataclass, fields
import difflib
import hashlib
from pathlib import Path
from typing import Any

from .execution_verification import _read_run
from .local_workflow import (DeveloperWorkspace, LocalWorkflowError, _git,
                             _git_index_state, _json_bytes, scan_local_repository)
from .patch_application import _apply_text, _status
from .test_execution import _changed_paths, _validate_phase69

_COMMAND = "evaluate-recovery"
_MODE = "developer-local-recovery-evaluation"
_EXPECTED_REFERENCE_KINDS = {"plan", "patch", "approval", "execution", "observation"}
_EXPECTED_FAILURE_DEVIATIONS = {"phase70_tests_did_not_pass", "phase70_test_failures_or_errors_present"}


@dataclass(frozen=True, slots=True)
class RecoveryEvaluation:
    evaluation_id: str
    schema_version: str
    repository_id: str
    repository_path: str
    verification_id: str
    verification_run_id: str
    execution_id: str
    execution_run_id: str
    observation_id: str
    observation_run_id: str
    verification_status: str
    classification: str
    candidate_actions: tuple[str, ...]
    blocking_conditions: tuple[str, ...]
    reasons: tuple[str, ...]
    rollback_feasible: bool
    rollback_candidate: dict[str, Any] | None
    retry_eligible: bool
    retry_boundary: dict[str, Any]
    new_proposal_required: bool
    remaining_uncertainty: tuple[str, ...]
    evidence_references: tuple[dict[str, str], ...]
    human_review_required: bool = True
    execution_authorized: bool = False
    source_mutation_performed: bool = False
    retry_performed: bool = False
    rollback_performed: bool = False
    lifecycle_transition_performed: bool = False

    def __post_init__(self) -> None:
        if (self.schema_version != "1.0" or not self.evaluation_id.startswith("recovery-")
                or not self.repository_id or not self.repository_path
                or not self.verification_id.startswith("verification-")
                or self.verification_status not in {"verified", "not_verified", "uncertain"}
                or self.classification not in {"no_recovery_required", "failed_tests", "stale_repository",
                                               "verification_mismatch", "unexpected_side_effect",
                                               "uncertain_verification"}
                or self.rollback_feasible is not (self.rollback_candidate is not None)
                or self.retry_eligible is not False or self.retry_boundary.get("eligible") is not False
                or self.human_review_required is not True or self.execution_authorized is not False
                or any((self.source_mutation_performed, self.retry_performed,
                        self.rollback_performed, self.lifecycle_transition_performed))):
            raise ValueError("Invalid or executable Phase 72 recovery contract.")
        if ("rollback_candidate" in self.candidate_actions) != self.rollback_feasible:
            raise ValueError("Rollback option and feasibility disagree.")
        if self.classification == "no_recovery_required" and self.candidate_actions != ("human_lifecycle_review",):
            raise ValueError("Verified execution cannot generate recovery work.")

    def to_dict(self) -> dict[str, Any]:
        sequence_fields = {"candidate_actions", "blocking_conditions", "reasons",
                           "remaining_uncertainty", "evidence_references"}
        return {field.name: list(getattr(self, field.name)) if field.name in sequence_fields
                else getattr(self, field.name) for field in fields(self)}


def _require_verification(workspace: DeveloperWorkspace, root: Path, run_id: str,
                          repository_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    meta, value = _read_run(workspace, run_id, "verification")
    if (meta.get("repository_path") != str(root) or meta.get("repository_id") != repository_id
            or value.get("repository_path") != str(root) or value.get("repository_id") != repository_id
            or value.get("schema_version") != "1.0"
            or value.get("status") not in {"verified", "not_verified", "uncertain"}
            or value.get("human_review_required") is not True
            or value.get("lifecycle_decision") != "none"
            or any(value.get(key) is not False for key in (
                "automatic_followup", "repair_performed", "retry_performed", "rollback_performed",
                "lifecycle_transition_performed", "source_mutation_performed", "git_staging_performed",
                "git_commit_created", "phase72_started"))):
        raise LocalWorkflowError("Phase 71 verification contract or repository binding is invalid.")
    try:
        for key in ("deviations", "unresolved_uncertainty", "warnings", "actual_changed_paths",
                    "executed_test_identities", "unexpected_changes"):
            if not isinstance(value[key], list) or len(value[key]) != len(set(value[key])):
                raise ValueError(key)
        symbol_scopes = {}
        for key in ("expected_symbol_scope", "approved_symbol_scope", "actual_symbol_scope"):
            rows = value[key]
            if (not isinstance(rows, list) or any(not isinstance(row, dict)
                    or set(row) != {"file_path", "qualified_symbol"} for row in rows)):
                raise ValueError(key)
            pairs = [(row["file_path"], row["qualified_symbol"]) for row in rows]
            if pairs != sorted(set(pairs)):
                raise ValueError(key)
            symbol_scopes[key] = [list(pair) for pair in pairs]
        comparison, outcome = value["repository_state_comparison"], value["test_outcome"]
        if (not isinstance(comparison, dict) or not isinstance(outcome, dict)
                or comparison.get("current_working_tree") != meta.get("working_tree_sha256")
                or comparison.get("historical_working_tree_after") is None):
            raise ValueError("repository state comparison")
        identity = {"execution_run_id": value["execution_run_id"],
                    "observation_run_id": value["observation_run_id"],
                    "repository_id": repository_id, "status": value["status"],
                    "deviations": sorted(value["deviations"]),
                    "uncertainty": sorted(value["unresolved_uncertainty"]),
                    "warnings": sorted(value["warnings"]),
                    "actual_paths": value["actual_changed_paths"],
                    "expected_symbols": symbol_scopes["expected_symbol_scope"],
                    "approved_symbols": symbol_scopes["approved_symbol_scope"],
                    "actual_symbols": symbol_scopes["actual_symbol_scope"],
                    "selected_tests": value["executed_test_identities"],
                    "repository_state": comparison, "test_outcome": outcome}
        expected = "verification-" + hashlib.sha256(_json_bytes(identity)).hexdigest()[:20]
        if value["verification_id"] != expected:
            raise ValueError("verification ID")
        if value["status"] == "verified" and (value["deviations"] or value["unexpected_changes"]
                                              or value["unresolved_uncertainty"]):
            raise ValueError("verified status conflicts with findings")
        if value["status"] == "uncertain" and (not value["unresolved_uncertainty"]
                                               or value["deviations"] or value["unexpected_changes"]):
            raise ValueError("uncertain status conflicts with findings")
        if value["status"] == "not_verified" and not (value["deviations"] or value["unexpected_changes"]):
            raise ValueError("not_verified has no finding")
    except (KeyError, TypeError, ValueError) as error:
        raise LocalWorkflowError("Phase 71 verification identity or findings are malformed.") from error
    return meta, value


def _linked_evidence(workspace: DeveloperWorkspace, root: Path, verification: dict[str, Any],
                     repository_id: str) -> tuple[dict[str, Any], dict[str, Any], tuple[dict[str, str], ...]]:
    references = verification.get("evidence_references")
    if not isinstance(references, list):
        raise LocalWorkflowError("Phase 71 evidence references are malformed.")
    seen: set[str] = set()
    records: dict[str, dict[str, Any]] = {}
    for reference in references:
        if not isinstance(reference, dict) or set(reference) != {"phase", "run_id", "record_sha256"}:
            raise LocalWorkflowError("Phase 71 evidence reference is malformed.")
        kind, run_id, digest = reference["phase"], reference["run_id"], reference["record_sha256"]
        if kind not in _EXPECTED_REFERENCE_KINDS or kind in seen:
            raise LocalWorkflowError("Phase 71 evidence references are ambiguous or unsupported.")
        seen.add(kind)
        meta, payload = _read_run(workspace, run_id, kind)
        if (meta.get("repository_path") != str(root) or meta.get("repository_id") != repository_id
                or hashlib.sha256(_json_bytes(payload)).hexdigest() != digest):
            raise LocalWorkflowError("Phase 71 linked evidence differs from its recorded reference.")
        records[kind] = payload
    if seen != _EXPECTED_REFERENCE_KINDS:
        raise LocalWorkflowError("Phase 71 linked evidence chain is incomplete.")
    execution, observation = records["execution"], records["observation"]
    plan, patch, approval = records["plan"], records["patch"], records["approval"]
    recorded_outcome = verification["test_outcome"]
    outcome_keys = ("tests_run", "passed", "failures", "errors", "skipped", "exit_code", "status",
                    "stdout_sha256", "stderr_sha256", "stdout_reference", "stderr_reference",
                    "unexpected_repository_changes", "unexpected_changed_paths", "repository_state_before",
                    "repository_state_after")
    if (next(row["run_id"] for row in references if row["phase"] == "execution")
            != verification.get("execution_run_id")
            or next(row["run_id"] for row in references if row["phase"] == "observation")
            != verification.get("observation_run_id")
            or execution.get("execution_id") != verification.get("execution_id")
            or observation.get("observation_id") != verification.get("observation_id")
            or observation.get("source_execution_id") != execution.get("execution_id")
            or observation.get("repository_id") != repository_id
            or execution.get("repository_id") != repository_id
            or any(recorded_outcome.get(key) != observation.get(key) for key in outcome_keys)
            or verification.get("test_plan_id") != observation.get("plan", {}).get("plan_id")
            or verification.get("plan_run_id") != next(row["run_id"] for row in references if row["phase"] == "plan")
            or verification.get("proposal_id") != plan.get("proposed_action", {}).get("action_id")
            or verification.get("patch_id") != patch.get("patch_id")
            or verification.get("authorization_id") != approval.get("authorization_id")
            or execution.get("source_action_id") != verification.get("proposal_id")
            or execution.get("source_patch_id") != verification.get("patch_id")
            or execution.get("authorization_id") != verification.get("authorization_id")):
        raise LocalWorkflowError("Phase 71 verification is bound to a different execution or observation.")
    return execution, observation, tuple(references)


def _current_state(root: Path, inventory, execution: dict[str, Any]) -> tuple[bool, tuple[str, ...]]:
    paths = tuple(execution.get("files_changed", ()))
    head = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode().strip()
    index = hashlib.sha256(_git_index_state(root)).hexdigest()
    refs = hashlib.sha256(_git(root, ["for-each-ref", "--format=%(refname) %(objectname)"])).hexdigest()
    changed = _changed_paths(_status(root))
    diff = _git(root, ["diff", "--no-ext-diff", "--binary", "--", *paths]).decode("utf-8", errors="replace") if paths else ""
    blockers = []
    if head != execution.get("repository_after"):
        blockers.append("head_moved_since_phase69")
    if inventory.snapshot_id != execution.get("working_tree_after"):
        blockers.append("working_tree_moved_since_phase69")
    if index != execution.get("semantic_index_sha256"):
        blockers.append("semantic_index_moved_since_phase69")
    if refs != execution.get("refs_sha256"):
        blockers.append("refs_moved_since_phase69")
    if changed != set(paths):
        blockers.append("changed_paths_differ_from_phase69")
    if diff != execution.get("diff_after"):
        blockers.append("target_diff_differs_from_phase69")
    return not blockers, tuple(blockers)


def _rollback_candidate(workspace: DeveloperWorkspace, root: Path, execution_run_id: str,
                        execution: dict[str, Any], inventory) -> dict[str, Any]:
    validated, authorization, _ = _validate_phase69(workspace, root, execution_run_id)
    if validated != execution or authorization.target_paths != tuple(execution.get("target_paths", ())):
        raise LocalWorkflowError("Phase 69 chain differs from the rollback source.")
    if (execution.get("semantic_index_unchanged") is not True
            or execution.get("refs_unchanged") is not True
            or execution.get("repository_before") != execution.get("repository_after")):
        raise LocalWorkflowError("Phase 69 Git state is incompatible with rollback evaluation.")
    sections: dict[str, str] = {}
    import re
    from .patch_drafting import _diff_path
    for section in re.split(r"(?m)(?=^--- )", execution["expected_diff"]):
        if section.strip():
            sections[_diff_path(section.splitlines()[0][4:])] = section
    rows = []
    reverse_parts = []
    for path in execution["target_paths"]:
        target = root.joinpath(*path.split("/"))
        if target.is_symlink() or not target.resolve(strict=True).is_file() or root not in target.resolve().parents:
            raise LocalWorkflowError("Rollback target path is no longer a safe regular file.")
        blob = _git(root, ["show", f"HEAD:{path}"])
        after = target.read_bytes()
        candidates = {blob, blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")}
        matching = [candidate for candidate in candidates
                    if path in sections and _apply_text(candidate, sections[path]) == after]
        if len(matching) != 1:
            raise LocalWorkflowError("Approved Phase 69 patch does not reproduce current target bytes.")
        before = matching[0]
        before_text, after_text = before.decode("utf-8"), after.decode("utf-8")
        reverse_parts.extend(difflib.unified_diff(after_text.splitlines(keepends=True),
                             before_text.splitlines(keepends=True), fromfile=f"a/{path}", tofile=f"b/{path}"))
        rows.append({"path": path, "postimage_sha256": hashlib.sha256(after).hexdigest(),
                     "reverse_content_sha256": hashlib.sha256(before).hexdigest()})
    if not rows or tuple(row["path"] for row in rows) != tuple(execution["target_paths"]):
        raise LocalWorkflowError("Rollback target scope is empty or inconsistent.")
    reverse_digest = hashlib.sha256("".join(reverse_parts).encode("utf-8")).hexdigest()
    identity = {"execution_run_id": execution_run_id, "execution_id": execution["execution_id"],
                "repository_id": inventory.repository_id, "repository_path": str(root),
                "head": execution["repository_after"], "poststate": inventory.snapshot_id,
                "semantic_index_sha256": execution["semantic_index_sha256"],
                "refs_sha256": execution["refs_sha256"], "target_paths": list(execution["target_paths"]),
                "target_bytes": rows, "reverse_diff_sha256": reverse_digest}
    return {**identity, "candidate_id": "rollback-" + hashlib.sha256(_json_bytes(identity)).hexdigest()[:20],
            "human_approval_required": True, "execution_authorized": False}


def evaluate_recovery(workspace: DeveloperWorkspace, repository: Path,
                      verification_run_id: str) -> dict[str, Any]:
    """Record bounded follow-up options; never run tests or mutate the repository."""
    root = Path(repository).expanduser().resolve(strict=True)
    workspace._prepare(root)
    inventory = scan_local_repository(root)
    _, verification = _require_verification(workspace, root, verification_run_id, inventory.repository_id)
    execution, observation, references = _linked_evidence(workspace, root, verification, inventory.repository_id)
    state_matches, state_blockers = _current_state(root, inventory, execution)
    deviations = set(verification["deviations"])
    unexpected = set(verification["unexpected_changes"])
    unexpected.update(observation.get("unexpected_changed_paths", ()))
    side_effects = bool(unexpected or observation.get("unexpected_repository_changes"))
    uncertainty = tuple(verification["unresolved_uncertainty"])
    failed_tests = observation.get("status") in {"failed", "error"} or bool(observation.get("failures") or observation.get("errors"))
    evidence_mismatch = bool(deviations - _EXPECTED_FAILURE_DEVIATIONS)
    blockers = list(state_blockers)
    if side_effects:
        blockers.append("unexpected_repository_side_effects:" + ",".join(sorted(unexpected)))
    if evidence_mismatch:
        blockers.extend(sorted(deviations - _EXPECTED_FAILURE_DEVIATIONS))
    if uncertainty:
        blockers.append("phase71_required_uncertainty_unresolved")
    if verification["status"] == "verified" and (failed_tests or evidence_mismatch or side_effects or uncertainty):
        raise LocalWorkflowError("Phase 71 verified status conflicts with linked evidence.")
    if verification["status"] == "uncertain" and failed_tests:
        raise LocalWorkflowError("Phase 71 uncertain status conflicts with failed observation.")
    if verification["status"] == "not_verified" and failed_tests and not _EXPECTED_FAILURE_DEVIATIONS & deviations:
        raise LocalWorkflowError("Phase 71 findings omit the linked test failure.")

    rollback = None
    if (failed_tests and state_matches and not side_effects and not uncertainty and not evidence_mismatch
            and execution.get("status") == "applied"):
        try:
            rollback = _rollback_candidate(workspace, root, verification["execution_run_id"], execution, inventory)
        except (LocalWorkflowError, OSError, ValueError, UnicodeDecodeError) as error:
            blockers.append("rollback_exact_reverse_unavailable:" + str(error))

    if side_effects:
        classification = "unexpected_side_effect"
        actions = ("manual_investigation_required",)
    elif not state_matches:
        classification = "stale_repository"
        actions = ("new_proposal_required", "manual_investigation_required")
    elif evidence_mismatch:
        classification = "verification_mismatch"
        actions = ("manual_investigation_required",)
    elif verification["status"] == "uncertain":
        classification = "uncertain_verification"
        actions = ("additional_evidence_required",)
    elif verification["status"] == "verified":
        classification = "no_recovery_required"
        actions = ("human_lifecycle_review",)
    elif failed_tests:
        classification = "failed_tests"
        actions = ("new_proposal_required", "manual_investigation_required")
        if rollback:
            actions += ("rollback_candidate",)
    else:
        classification = "verification_mismatch"
        actions = ("manual_investigation_required",)
    # Phase 70 has no typed transient-cause proof. Failure prose cannot justify a retry.
    retry = {"eligible": False, "reason": "no_typed_transient_cause_or_new_human_authorization",
             "prior_observation_run_id": verification["observation_run_id"],
             "prior_test_plan_id": verification["test_plan_id"],
             "source_execution_run_id": verification["execution_run_id"],
             "repository_id": inventory.repository_id,
             "repository_state": inventory.snapshot_id,
             "current_head": _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode().strip(),
             "current_semantic_index_sha256": hashlib.sha256(_git_index_state(root)).hexdigest(),
             "current_refs_sha256": hashlib.sha256(_git(root, ["for-each-ref", "--format=%(refname) %(objectname)"])).hexdigest(),
             "exact_test_identities": list(observation.get("test_identities", ())),
             "same_operation_only": True, "maximum_future_attempts": 1,
             "changed_test_plan_is_retry": False, "changed_patch_is_retry": False,
             "explicit_future_human_authorization_required": True}
    reasons = tuple(sorted(set(verification["deviations"] + verification["warnings"]
                               + (["phase70_tests_failed_or_errored"] if failed_tests else []))))
    evidence_refs = ({"phase": "verification", "run_id": verification_run_id,
                      "record_sha256": hashlib.sha256(_json_bytes({k: v for k, v in verification.items()
                                                                    if k != "run_id"})).hexdigest()}, *references)
    facts = {"verification_run_id": verification_run_id, "verification_id": verification["verification_id"],
             "repository_id": inventory.repository_id, "repository_state": inventory.snapshot_id,
             "classification": classification, "candidate_actions": actions, "blocking_conditions": sorted(set(blockers)),
             "rollback_candidate": rollback, "retry_boundary": retry, "reasons": reasons,
             "remaining_uncertainty": uncertainty}
    evaluation_id = "recovery-" + hashlib.sha256(_json_bytes(facts)).hexdigest()[:20]
    summary = RecoveryEvaluation(evaluation_id, "1.0", inventory.repository_id, str(root),
                                 verification["verification_id"], verification_run_id,
                                 execution["execution_id"], verification["execution_run_id"],
                                 observation["observation_id"], verification["observation_run_id"],
                                 verification["status"], classification, actions,
                                 tuple(sorted(set(blockers))), reasons, rollback is not None, rollback,
                                 False, retry, "new_proposal_required" in actions, uncertainty,
                                 tuple(evidence_refs))
    payload = {"mode": _MODE, **summary.to_dict()}
    payload["run_id"] = workspace._record_run(_COMMAND, scan_local_repository(root), payload)
    return payload
