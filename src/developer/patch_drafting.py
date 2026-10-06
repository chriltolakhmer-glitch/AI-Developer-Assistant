"""Evidence-bound, non-mutating unified-diff draft contracts for developer mode."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Protocol

from .local_workflow import DeveloperWorkspace, LocalWorkflowError, scan_local_repository
from .symbol_scope import derive_patch_symbols, postimages_for_patch, proposal_allowed_scope, scope_is_allowed


@dataclass(frozen=True, slots=True)
class PatchDraft:
    patch_id: str
    schema_version: str
    source_action_id: str
    repository_path: str
    repository_id: str
    base_reference: str | None
    base_commit: str | None
    current_commit: str | None
    working_tree_sha256: str | None
    goal: str
    target_paths: tuple[str, ...]
    candidate_paths: tuple[str, ...]
    target_symbols: tuple[str, ...]
    patch_format: str
    patch_text: str
    evidence_refs: tuple[dict[str, Any], ...]
    unresolved_evidence: tuple[dict[str, Any], ...]
    validation_requirements: tuple[str, ...]
    allowed_symbol_scope: tuple[tuple[str, str], ...] = ()
    candidate_symbol_scope: tuple[tuple[str, str], ...] = ()
    status: str = "draft"
    human_review_required: bool = True
    apply_allowed: bool = False
    execution_allowed: bool = False
    source_mutation_performed: bool = False

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.source_action_id.startswith("proposal-"):
            raise ValueError("PatchDraft must be bound to a Phase 66 proposal ID.")
        if not self.repository_id or not self.repository_path or not self.working_tree_sha256:
            raise ValueError("PatchDraft requires repository and working-tree identity.")
        if self.patch_format != "unified_diff":
            raise ValueError("Only unified_diff is supported.")
        if self.schema_version != "1.0" or not self.goal.strip():
            raise ValueError("PatchDraft schema version and goal are required.")
        if self.status not in {"draft", "blocked"}:
            raise ValueError("PatchDraft status must be 'draft' or 'blocked'.")
        if self.human_review_required is not True or self.apply_allowed is not False:
            raise ValueError("PatchDraft always requires review and forbids application.")
        if self.execution_allowed is not False or self.source_mutation_performed is not False:
            raise ValueError("PatchDraft cannot execute or mutate source.")
        if len(self.target_paths) != len(set(self.target_paths)):
            raise ValueError("PatchDraft target paths must be unique.")
        if tuple(sorted(set(self.candidate_paths))) != self.candidate_paths or not set(self.candidate_paths) <= set(self.target_paths):
            raise ValueError("PatchDraft candidate paths must be a canonical subset of allowed paths.")
        if self.status == "draft" and self.candidate_paths != validate_unified_diff(self.patch_text, self.target_paths):
            raise ValueError("PatchDraft candidate paths differ from the unified diff.")
        for path in self.target_paths:
            _diff_path(path)
        for scope in (self.allowed_symbol_scope, self.candidate_symbol_scope):
            if tuple(sorted(set(scope))) != scope or any(not isinstance(row, tuple) or len(row) != 2
                    or not all(isinstance(value, str) and value for value in row) for row in scope):
                raise ValueError("PatchDraft symbol scopes must be canonical path-qualified pairs.")
        if self.status == "draft":
            validate_unified_diff(self.patch_text, self.target_paths)
        elif self.patch_text:
            raise ValueError("Blocked PatchDrafts must not retain candidate patch text.")
        if self.patch_id != _patch_id(self):
            raise ValueError("PatchDraft ID does not match its deterministic content identity.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "patch_id": self.patch_id, "schema_version": self.schema_version,
            "source_action_id": self.source_action_id, "repository_path": self.repository_path,
            "repository_id": self.repository_id, "base_reference": self.base_reference,
            "base_commit": self.base_commit, "current_commit": self.current_commit,
            "working_tree_sha256": self.working_tree_sha256, "goal": self.goal,
            "target_paths": list(self.target_paths), "target_symbols": list(self.target_symbols),
            "candidate_paths": list(self.candidate_paths),
            "patch_format": self.patch_format, "patch_text": self.patch_text,
            "evidence_refs": [dict(row) for row in self.evidence_refs],
            "unresolved_evidence": [dict(row) for row in self.unresolved_evidence],
            "validation_requirements": list(self.validation_requirements),
            "allowed_symbol_scope": [{"file_path": path, "qualified_symbol": symbol}
                                     for path, symbol in self.allowed_symbol_scope],
            "candidate_symbol_scope": [{"file_path": path, "qualified_symbol": symbol}
                                       for path, symbol in self.candidate_symbol_scope],
            "status": self.status, "human_review_required": self.human_review_required,
            "apply_allowed": self.apply_allowed, "execution_allowed": self.execution_allowed,
            "source_mutation_performed": self.source_mutation_performed,
        }


class PatchDraftGenerator(Protocol):
    """Pure boundary: return candidate text without repository or process access."""

    def generate(self, proposal: dict[str, Any], source_context: dict[str, str]) -> str: ...


@dataclass(frozen=True, slots=True)
class SuppliedPatchGenerator:
    """Testable adapter for an explicitly supplied candidate; no model is implied."""
    patch_text: str

    def generate(self, proposal: dict[str, Any], source_context: dict[str, str]) -> str:
        del proposal, source_context
        return self.patch_text


def _patch_id_payload(payload: dict[str, Any]) -> str:
    payload = {key: value for key, value in payload.items() if key != "patch_id"}
    if "candidate_paths" in payload and isinstance(payload["candidate_paths"], tuple):
        payload["candidate_paths"] = list(payload["candidate_paths"])
    for name in ("allowed_symbol_scope", "candidate_symbol_scope"):
        value = payload.get(name)
        if value and isinstance(value[0], tuple):
            payload[name] = [{"file_path": path, "qualified_symbol": symbol} for path, symbol in value]
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return f"patch-{digest[:16]}"


def _patch_id(draft: PatchDraft) -> str:
    return _patch_id_payload(draft.to_dict())


def _diff_path(value: str) -> str:
    value = value.split("\t", 1)[0]
    if value.startswith(("a/", "b/")):
        value = value[2:]
    if (not value or value == "/dev/null" or "\\" in value
            or re.match(r"^[A-Za-z]:", value)):
        raise ValueError(f"Invalid or unsupported diff path: {value!r}")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"Diff path must not contain empty or traversal components: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise ValueError(f"Diff path must be safe and repository-relative: {value!r}")
    return path.as_posix()


def validate_unified_diff(patch_text: str, allowed_paths: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(patch_text, str) or not patch_text.strip():
        raise ValueError("Patch text must not be empty.")
    lines = patch_text.splitlines()
    paths: list[str] = []
    i = 0
    while i < len(lines):
        if not lines[i].startswith("--- ") or i + 1 >= len(lines) or not lines[i + 1].startswith("+++ "):
            raise ValueError("Malformed unified diff: expected paired ---/+++ file headers.")
        old, new = _diff_path(lines[i][4:]), _diff_path(lines[i + 1][4:])
        if old != new:
            raise ValueError("Adds, deletes, and renames are not authorized by this proposal contract.")
        if old not in allowed_paths:
            raise ValueError(f"Patch path is outside proposal scope: {old}")
        paths.append(old)
        i += 2
        hunks = 0
        while i < len(lines) and lines[i].startswith("@@ "):
            match = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)", lines[i])
            if not match:
                raise ValueError("Malformed unified diff: expected a valid hunk header.")
            old_count = int(match.group(2) or 1)
            new_count = int(match.group(4) or 1)
            seen_old = seen_new = 0
            i += 1
            while (seen_old < old_count or seen_new < new_count) and i < len(lines):
                line = lines[i]
                if line.startswith("\\ No newline"):
                    i += 1
                    continue
                if not line or line[0] not in " +-":
                    raise ValueError("Malformed unified diff hunk line.")
                if line[0] in " -": seen_old += 1
                if line[0] in " +": seen_new += 1
                if seen_old > old_count or seen_new > new_count:
                    raise ValueError("Unified diff hunk contains more lines than its header declares.")
                i += 1
            if (seen_old, seen_new) != (old_count, new_count):
                raise ValueError("Unified diff hunk line counts do not match its header.")
            while i < len(lines) and lines[i].startswith("\\ No newline"):
                i += 1
            hunks += 1
        if not hunks:
            raise ValueError("Each unified diff file must contain at least one hunk.")
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("Patch must contain unique, authorized file sections.")
    return tuple(paths)


def _proposal_dict(proposal: Any) -> dict[str, Any]:
    result = proposal.to_dict() if hasattr(proposal, "to_dict") else dict(proposal)
    if not result.get("action_id", "").startswith("proposal-"):
        raise ValueError("Missing Phase 66 proposal identity.")
    if result.get("status") != "proposed" or result.get("execution_allowed") is not False:
        raise ValueError("Proposal is inconsistent with the Phase 66 review-only contract.")
    if not result.get("repository_id") or not result.get("repository_path") or not result.get("current_commit"):
        raise ValueError("Proposal repository and current-commit identity are required.")
    if result.get("base_reference") and not result.get("base_commit"):
        raise ValueError("Proposal base reference has no bound base commit.")
    for path in result.get("target_paths", []):
        _diff_path(path)
    return result


def _apply_candidate_text(original: bytes, section: str) -> bytes:
    """Use Phase 69's exact no-fuzz interpreter for independent pre-approval attribution."""
    from .patch_application import _apply_text
    return _apply_text(original, section)


def draft_patch(workspace: DeveloperWorkspace, repository: Path, proposal: Any,
                generator: PatchDraftGenerator, *, plan_run_id: str) -> dict[str, Any]:
    """Accept a candidate only after validating its exact Phase 65/66 source run."""
    from .proposal_evidence import validated_plan
    proposed = _proposal_dict(proposal)
    _, validated = validated_plan(workspace, repository, plan_run_id)
    if validated.to_dict() != proposed:
        raise LocalWorkflowError("Phase 66 proposal differs from validated Phase 65 evidence.")
    return _draft_patch_candidate(workspace, repository, proposed, generator,
                                  plan_run_id=plan_run_id)


def _draft_patch_candidate(workspace: DeveloperWorkspace, repository: Path, proposal: Any,
                           generator: PatchDraftGenerator, *, plan_run_id: str | None = None) -> dict[str, Any]:
    """Low-level structural adapter for isolated Phase 67 contract fixtures."""
    proposed = _proposal_dict(proposal)
    inventory = scan_local_repository(repository)
    root = str(inventory.root.resolve())
    if root != str(Path(proposed["repository_path"]).resolve()):
        raise LocalWorkflowError("Repository path differs from the Phase 66 proposal; replan first.")
    if inventory.repository_id != proposed["repository_id"]:
        raise LocalWorkflowError("Repository identity differs from the Phase 66 proposal; replan first.")
    if inventory.commit_sha != proposed.get("current_commit"):
        raise LocalWorkflowError("Current commit differs from the Phase 66 proposal; replan first.")
    base_reference, base_commit = proposed.get("base_reference"), proposed.get("base_commit")
    if base_reference and base_commit:
        resolved = subprocess.run(
            ["git", "-C", str(inventory.root), "rev-parse", "--verify", "--end-of-options",
             f"{base_reference}^{{commit}}"], capture_output=True, check=False,
        )
        if resolved.returncode or resolved.stdout.decode("ascii", errors="replace").strip() != base_commit:
            raise LocalWorkflowError("Base reference no longer resolves to the Phase 66 base commit; replan first.")
    if inventory.snapshot_id != proposed.get("working_tree_sha256"):
        raise LocalWorkflowError("Working-tree fingerprint differs from the Phase 66 proposal; replan first.")
    source_context: dict[str, str] = {}
    for relative in proposed.get("target_paths", []):
        path = (inventory.root / relative).resolve()
        if inventory.root.resolve() not in path.parents or path.suffix.lower() != ".py":
            raise LocalWorkflowError(f"Unsupported or unsafe proposal target: {relative}")
        if not path.is_file():
            raise LocalWorkflowError(f"Proposal target is missing: {relative}")
        source = path.read_text(encoding="utf-8")
        if len(source.encode("utf-8")) > 262_144:
            raise LocalWorkflowError(f"Authorized source context exceeds the 256 KiB drafting boundary: {relative}")
        source_context[relative] = source
    candidate = generator.generate(proposed, source_context)
    paths = validate_unified_diff(candidate, tuple(proposed.get("target_paths", ())))
    allowed_symbols = proposal_allowed_scope(proposed)
    preimages, postimages = postimages_for_patch(inventory.root, candidate, paths, _apply_candidate_text)
    candidate_symbols = derive_patch_symbols(candidate, preimages, postimages)
    if ((allowed_symbols and not scope_is_allowed(candidate_symbols, allowed_symbols, preimages))
            or (proposed.get("evidence_refs") and not allowed_symbols)
            or not set(paths) <= set(proposed.get("target_paths", ()))):
        raise LocalWorkflowError("Candidate patch exceeds path-qualified Phase 65 symbol scope; replan before approval.")
    unresolved_rows = [dict(row) for row in proposed.get("unresolved_evidence", [])]
    if not proposed.get("evidence_refs"):
        unresolved_rows.append({"type": "insufficient_proposal_evidence", "action": "manual_review_required",
                                "evidence": "Phase 66 proposal contains no evidence references; no patch body was retained."})
    unresolved = tuple(unresolved_rows)
    informational_types = {"runtime_behavior_unverified", "token_limit_exclusion_summary"}
    blocking_uncertainty = any(row.get("type") not in informational_types for row in unresolved)
    status = "blocked" if blocking_uncertainty or not paths else "draft"
    if status == "blocked":
        # Keep the attempted candidate out of the purported valid patch body.
        candidate = ""
    fields = dict(
        schema_version="1.0", source_action_id=proposed["action_id"],
        repository_path=proposed["repository_path"], repository_id=proposed["repository_id"],
        base_reference=proposed.get("base_reference"), base_commit=proposed.get("base_commit"),
        current_commit=proposed.get("current_commit"), working_tree_sha256=proposed["working_tree_sha256"],
        goal=proposed["goal"], target_paths=tuple(proposed.get("target_paths", ())),
        candidate_paths=tuple(sorted(paths)),
        target_symbols=tuple(proposed.get("target_symbols", ())), patch_format="unified_diff",
        patch_text=candidate, evidence_refs=tuple(dict(row) for row in proposed.get("evidence_refs", [])),
        unresolved_evidence=unresolved, validation_requirements=("Review evidence and diff.", "Run proposal-recommended validation after separate human authorization."),
        allowed_symbol_scope=allowed_symbols, candidate_symbol_scope=candidate_symbols,
        status=status, human_review_required=True, apply_allowed=False,
        execution_allowed=False, source_mutation_performed=False,
    )
    fields["patch_id"] = _patch_id_payload({**fields, "patch_id": ""})
    draft = PatchDraft(**fields)
    payload = {"mode": "developer-local-patch-draft", **draft.to_dict(),
                "generator": "supplied_candidate_no_production_model",
                "candidate_paths": list(paths), "source_plan_run_id": plan_run_id,
                "tests_executed": False}
    payload["run_id"] = workspace._record_run("draft-patch", inventory, payload)
    return payload
