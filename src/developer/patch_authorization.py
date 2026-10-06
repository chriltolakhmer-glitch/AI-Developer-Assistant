"""Explicit local approval or rejection of one Phase 67 patch draft."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .local_workflow import (DeveloperWorkspace, LocalInventory, LocalWorkflowError,
                             _digest, _json_bytes, scan_local_repository)
from .patch_drafting import PatchDraft, _diff_path, validate_unified_diff


def _authorization_id(value: dict[str, Any]) -> str:
    content = {key: item for key, item in value.items() if key != "authorization_id"}
    digest = hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return f"authorization-{digest[:20]}"


@dataclass(frozen=True, slots=True)
class AuthorizationRecord:
    authorization_id: str
    schema_version: str
    source_action_id: str
    source_patch_id: str
    source_patch_run_id: str
    repository_id: str
    repository_path: str
    current_commit: str
    working_tree_sha256: str
    patch_sha256: str
    target_paths: tuple[str, ...]
    candidate_paths: tuple[str, ...]
    allowed_symbol_scope: tuple[tuple[str, str], ...]
    candidate_symbol_scope: tuple[tuple[str, str], ...]
    decision: str
    decided_at: str
    approved_by: str
    execution_authorized: bool
    allowed_operation: str
    executed: bool = False
    note: str | None = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.schema_version != "1.0" or self.decision not in {"approve", "reject"}:
            raise ValueError("Authorization schema or explicit decision is invalid.")
        if not self.source_action_id.startswith("proposal-") or not self.source_patch_id.startswith("patch-"):
            raise ValueError("Authorization requires Phase 66 and Phase 67 identities.")
        if not re.fullmatch(r"[0-9a-f]{20}", self.source_patch_run_id):
            raise ValueError("Authorization requires a valid source patch run ID.")
        if not self.repository_id or not self.repository_path or not self.current_commit:
            raise ValueError("Authorization requires repository identity and commit.")
        if not all(re.fullmatch(r"[0-9a-f]{64}", value) for value in
                   (self.working_tree_sha256, self.patch_sha256)):
            raise ValueError("Authorization requires complete SHA-256 bindings.")
        if len(self.target_paths) != len(set(self.target_paths)):
            raise ValueError("Authorization target paths must be unique.")
        for path in self.target_paths:
            if _diff_path(path) != path:
                raise ValueError("Authorization target paths must be repository-relative.")
        for scope in (self.allowed_symbol_scope, self.candidate_symbol_scope):
            if tuple(sorted(set(scope))) != scope:
                raise ValueError("Authorization symbol scope must be canonical.")
        if not self.decided_at or not self.approved_by.strip() or len(self.approved_by) > 100:
            raise ValueError("Authorization requires a decision time and short audit label.")
        if self.note is not None and (not isinstance(self.note, str) or len(self.note) > 500):
            raise ValueError("Authorization note must be at most 500 characters.")
        if self.executed is not False:
            raise ValueError("Phase 68 never records execution.")
        if self.decision == "approve":
            if self.execution_authorized is not True or self.allowed_operation != "apply_exact_patch":
                raise ValueError("Approval permits only future exact patch application.")
            if not self.target_paths:
                raise ValueError("Approval requires patch target paths.")
        elif self.execution_authorized is not False or self.allowed_operation != "none":
            raise ValueError("Rejection cannot grant execution authority.")
        if self.authorization_id != _authorization_id(self.to_dict()):
            raise ValueError("Authorization ID does not match the decision record.")

    def to_dict(self) -> dict[str, Any]:
        return {field.name: (list(getattr(self, field.name)) if field.name in {"target_paths", "candidate_paths"} else
                [{"file_path": p, "qualified_symbol": s} for p, s in getattr(self, field.name)]
                if field.name in {"allowed_symbol_scope", "candidate_symbol_scope"} else getattr(self, field.name))
                for field in fields(self)}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> AuthorizationRecord:
        expected = {field.name for field in fields(cls)}
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("Authorization record fields are missing or unexpected.")
        converted = dict(value, target_paths=tuple(value["target_paths"]),
                         candidate_paths=tuple(value["candidate_paths"]))
        for name in ("allowed_symbol_scope", "candidate_symbol_scope"):
            converted[name] = tuple((row["file_path"], row["qualified_symbol"]) for row in value[name])
        return cls(**converted)


def _read_patch_run(workspace: DeveloperWorkspace, patch_run_id: str) -> PatchDraft:
    if not re.fullmatch(r"[0-9a-f]{20}", patch_run_id):
        raise LocalWorkflowError("Invalid Phase 67 patch run ID.")
    directory = workspace._contained(workspace.root / "runs" / patch_run_id)
    try:
        metadata_bytes = (directory / "metadata.json").read_bytes()
        result_bytes = (directory / "results.json").read_bytes()
        metadata, payload = json.loads(metadata_bytes), json.loads(result_bytes)
    except (OSError, ValueError, TypeError) as error:
        raise LocalWorkflowError("Phase 67 patch run is missing or malformed; redraft the patch.") from error
    if (not isinstance(metadata, dict) or not isinstance(payload, dict)
            or metadata_bytes != _json_bytes(metadata) or result_bytes != _json_bytes(payload)
            or metadata.get("schema_version") != "developer-local-run-v1"
            or metadata.get("mode") != "developer-local" or metadata.get("command") != "draft-patch"
            or metadata.get("run_id") != patch_run_id
            or metadata.get("workspace_sha256") != _digest(str(workspace.root).encode("utf-8"))
            or payload.get("mode") != "developer-local-patch-draft"
            or payload.get("tests_executed") is not False):
        raise LocalWorkflowError("Phase 67 patch run identity or content is invalid; redraft the patch.")
    identity = {"mode": "developer-local", "command": "draft-patch",
                "repository_id": metadata.get("repository_id"),
                "working_tree_sha256": metadata.get("working_tree_sha256"), "payload": payload}
    if _digest(_json_bytes(identity))[:20] != patch_run_id:
        raise LocalWorkflowError("Phase 67 patch run content was modified; redraft the patch.")
    try:
        content = {field.name: payload[field.name] for field in fields(PatchDraft)}
        for name in ("target_paths", "candidate_paths", "target_symbols", "evidence_refs", "unresolved_evidence",
                     "validation_requirements"):
            content[name] = tuple(content[name])
        for name in ("allowed_symbol_scope", "candidate_symbol_scope"):
            content[name] = tuple((row["file_path"], row["qualified_symbol"]) for row in payload[name])
        draft = PatchDraft(**content)
        if (any(payload[field.name] != draft.to_dict()[field.name] for field in fields(PatchDraft))
                or metadata.get("repository_id") != draft.repository_id
                or metadata.get("repository_path") != draft.repository_path
                or metadata.get("commit_sha") != draft.current_commit
                or metadata.get("working_tree_sha256") != draft.working_tree_sha256
                or (draft.status == "draft" and payload.get("candidate_paths") != list(
                    validate_unified_diff(draft.patch_text, draft.target_paths)))):
            raise ValueError("Patch record fields disagree with the typed draft or run metadata.")
    except (KeyError, TypeError, ValueError) as error:
        raise LocalWorkflowError("Phase 67 patch draft failed integrity validation; redraft the patch.") from error
    return draft


def _check_repository(draft: PatchDraft, inventory: LocalInventory, *, require_state: bool) -> None:
    if str(inventory.root.resolve()) != str(Path(draft.repository_path).resolve()):
        raise LocalWorkflowError("Repository path differs from the PatchDraft; replan and redraft.")
    if inventory.repository_id != draft.repository_id:
        raise LocalWorkflowError("Repository identity differs from the PatchDraft; replan and redraft.")
    if require_state and (inventory.commit_sha != draft.current_commit
                          or inventory.snapshot_id != draft.working_tree_sha256):
        raise LocalWorkflowError("Repository state differs from the PatchDraft; replan and redraft.")


def validate_exact_patch_authorization(record: AuthorizationRecord, draft: PatchDraft,
                                       repository: Path) -> None:
    """Read-only binding check for a later phase; it never applies the patch."""
    record.validate()
    draft.validate()
    if record.decision != "approve" or record.execution_authorized is not True:
        raise LocalWorkflowError("Patch was rejected or has no execution authority.")
    if draft.status != "draft":
        raise LocalWorkflowError("Blocked PatchDraft cannot be approved; replan and redraft.")
    expected = (draft.source_action_id, draft.patch_id, draft.repository_id,
                str(Path(draft.repository_path).resolve()), draft.current_commit,
                draft.working_tree_sha256, hashlib.sha256(draft.patch_text.encode("utf-8")).hexdigest(),
                draft.target_paths, draft.candidate_paths, draft.allowed_symbol_scope, draft.candidate_symbol_scope)
    actual = (record.source_action_id, record.source_patch_id, record.repository_id,
              str(Path(record.repository_path).resolve()), record.current_commit,
              record.working_tree_sha256, record.patch_sha256, record.target_paths,
              record.candidate_paths, record.allowed_symbol_scope, record.candidate_symbol_scope)
    if actual != expected:
        raise LocalWorkflowError("Authorization does not match the exact PatchDraft; approve the new draft.")
    _check_repository(draft, scan_local_repository(repository), require_state=True)


def record_patch_decision(workspace: DeveloperWorkspace, repository: Path, patch_run_id: str,
                          decision: str, *, approved_by: str = "local-developer",
                          note: str | None = None) -> dict[str, Any]:
    """Record one explicit human decision under the external developer workspace."""
    if decision not in {"approve", "reject"}:
        raise ValueError("Choose an explicit approve or reject decision.")
    if not isinstance(approved_by, str) or not approved_by.strip() or len(approved_by) > 100:
        raise ValueError("The audit label must be a nonempty name of at most 100 characters.")
    if note is not None and (not isinstance(note, str) or len(note) > 500):
        raise ValueError("The optional review note must be at most 500 characters.")
    inventory = scan_local_repository(repository)
    workspace._prepare(inventory.root)
    draft = _read_patch_run(workspace, patch_run_id)
    _check_repository(draft, inventory, require_state=decision == "approve")
    if decision == "approve" and draft.status != "draft":
        raise LocalWorkflowError("Blocked PatchDraft cannot be approved; replan and redraft.")
    data = dict(
        schema_version="1.0", source_action_id=draft.source_action_id,
        source_patch_id=draft.patch_id, source_patch_run_id=patch_run_id,
        repository_id=draft.repository_id, repository_path=draft.repository_path,
        current_commit=draft.current_commit, working_tree_sha256=draft.working_tree_sha256,
        patch_sha256=hashlib.sha256(draft.patch_text.encode("utf-8")).hexdigest(),
        target_paths=draft.target_paths, candidate_paths=draft.candidate_paths,
        allowed_symbol_scope=draft.allowed_symbol_scope,
        candidate_symbol_scope=draft.candidate_symbol_scope, decision=decision,
        decided_at=datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        approved_by=approved_by.strip(), execution_authorized=decision == "approve",
        allowed_operation="apply_exact_patch" if decision == "approve" else "none",
        executed=False, note=note,
    )
    identity_data = {**data, "target_paths": list(draft.target_paths),
                     "candidate_paths": list(draft.candidate_paths),
                     "allowed_symbol_scope": [{"file_path": p, "qualified_symbol": s}
                                              for p, s in draft.allowed_symbol_scope],
                     "candidate_symbol_scope": [{"file_path": p, "qualified_symbol": s}
                                                for p, s in draft.candidate_symbol_scope]}
    data["authorization_id"] = _authorization_id(identity_data)
    record = AuthorizationRecord(**data)
    if decision == "approve":
        validate_exact_patch_authorization(record, draft, inventory.root)
    payload = {"mode": "developer-local-patch-authorization", **record.to_dict(),
               "tests_executed": False, "source_mutation_performed": False}
    payload["run_id"] = workspace._record_run("review-patch", inventory, payload)
    return payload
