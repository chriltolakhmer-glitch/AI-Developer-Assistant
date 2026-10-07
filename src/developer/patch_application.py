"""Apply one exact, approved Phase 67 patch with bounded restoration."""
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

from .local_workflow import (DeveloperWorkspace, LocalWorkflowError, _digest, _git, _git_index_state,
                             _json_bytes, scan_local_repository)
from .patch_authorization import AuthorizationRecord, _read_patch_run, validate_exact_patch_authorization
from .patch_drafting import PatchDraft, validate_unified_diff
from .symbol_scope import derive_patch_symbols, patch_sections, postimages_for_patch, scope_is_allowed


def _status(root: Path) -> bytes:
    """Read Git status without its optional index refresh."""
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env)
    if result.returncode:
        raise LocalWorkflowError("Cannot verify repository status; PATCH NOT APPLIED.")
    return result.stdout


@dataclass(frozen=True, slots=True)
class PatchApplicationResult:
    execution_id: str
    schema_version: str
    authorization_id: str
    source_action_id: str
    source_patch_id: str
    repository_id: str
    repository_path: str
    repository_before: str
    repository_after: str
    working_tree_before: str
    working_tree_after: str
    target_paths: tuple[str, ...]
    patch_sha256: str
    status: str
    files_changed: tuple[str, ...]
    diff_after: str
    error: str | None
    applied_at: str
    actual_patch_symbol_scope: tuple[tuple[str, str], ...] = ()
    observed_applied_symbol_scope: tuple[tuple[str, str], ...] = ()
    file_postimages: tuple[tuple[str, str, str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {f.name: (list(getattr(self, f.name)) if f.name in {"target_paths", "files_changed"} else
                [{"file_path": p, "qualified_symbol": s} for p, s in getattr(self, f.name)]
                if f.name in {"actual_patch_symbol_scope", "observed_applied_symbol_scope"} else
                [{"file_path": p, "preimage_sha256": before, "expected_postimage_sha256": expected,
                  "observed_postimage_sha256": observed} for p, before, expected, observed in self.file_postimages]
                if f.name == "file_postimages" else getattr(self, f.name))
                for f in fields(self)}


def _load_authorization(workspace: DeveloperWorkspace, run_id: str) -> AuthorizationRecord:
    if not re.fullmatch(r"[0-9a-f]{20}", run_id):
        raise LocalWorkflowError("Invalid authorization run ID; PATCH NOT APPLIED.")
    directory = workspace._contained(workspace.root / "runs" / run_id)
    try:
        mb, rb = (directory / "metadata.json").read_bytes(), (directory / "results.json").read_bytes()
        meta, payload = json.loads(mb), json.loads(rb)
        if mb != _json_bytes(meta) or rb != _json_bytes(payload):
            raise ValueError("noncanonical run record")
        if (meta.get("run_id") != run_id or meta.get("command") != "review-patch"
                or meta.get("workspace_sha256") != hashlib.sha256(str(workspace.root).encode()).hexdigest()
                or payload.get("mode") != "developer-local-patch-authorization"):
            raise ValueError("wrong authorization record")
        record = AuthorizationRecord.from_dict({f.name: payload[f.name] for f in fields(AuthorizationRecord)})
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise LocalWorkflowError("Authorization is missing or malformed; PATCH NOT APPLIED.") from error
    identity = {"mode": "developer-local", "command": "review-patch",
                "repository_id": meta.get("repository_id"),
                "working_tree_sha256": meta.get("working_tree_sha256"), "payload": payload}
    if (_digest(_json_bytes(identity))[:20] != run_id
            or meta.get("repository_id") != record.repository_id
            or meta.get("repository_path") != record.repository_path
            or meta.get("commit_sha") != record.current_commit
            or meta.get("working_tree_sha256") != record.working_tree_sha256):
        raise LocalWorkflowError("Authorization run binding is invalid; PATCH NOT APPLIED.")
    return record


def validate_postimage_evidence(result: dict[str, Any]) -> tuple[tuple[str, str, str, str], ...]:
    """Validate run-bound exact-byte evidence; never accepts caller-provided hashes."""
    rows = result.get("file_postimages")
    keys = ("file_path", "preimage_sha256", "expected_postimage_sha256", "observed_postimage_sha256")
    paths = tuple(result.get("target_paths", ()))
    if (not isinstance(rows, list) or not rows or paths != tuple(sorted(set(paths)))
            or any(not isinstance(row, dict) or set(row) != set(keys) for row in rows)):
        raise LocalWorkflowError("Phase 69 post-image evidence is missing or noncanonical.")
    evidence = tuple(tuple(row[key] for key in keys) for row in rows)
    if (tuple(row[0] for row in evidence) != paths
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                   for row in evidence for value in row[1:])
            or any(row[2] != row[3] for row in evidence)):
        raise LocalWorkflowError("Phase 69 post-image hashes or candidate paths are invalid.")
    return evidence


def _apply_text(original: bytes, patch: str) -> bytes:
    try:
        lines = original.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError as error:
        raise LocalWorkflowError("Patch target is not UTF-8; PATCH NOT APPLIED.") from error
    patch_lines = patch.splitlines()
    output: list[str] = []
    cursor = 0
    i = 2
    while i < len(patch_lines):
        m = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*", patch_lines[i])
        if not m:
            raise LocalWorkflowError("Malformed patch hunk; PATCH NOT APPLIED.")
        old_count, new_count = int(m.group(2) or 1), int(m.group(4) or 1)
        old_start, new_start = int(m.group(1)), int(m.group(3))
        start = old_start if old_count == 0 else old_start - 1
        if start < cursor or start > len(lines):
            raise LocalWorkflowError("Patch context conflicts with target; PATCH NOT APPLIED.")
        output_before_hunk = len(output) + (start - cursor)
        expected_new_start = output_before_hunk if new_count == 0 else output_before_hunk + 1
        if new_start != expected_new_start:
            raise LocalWorkflowError("Patch new-line coordinates conflict with exact application; PATCH NOT APPLIED.")
        output.extend(lines[cursor:start]); cursor = start; i += 1
        old_count = new_count = 0
        while i < len(patch_lines) and not patch_lines[i].startswith(("@@ ", "--- ")):
            row = patch_lines[i]
            if row.startswith("\\ No newline"):
                i += 1; continue
            kind, body = row[0], row[1:]
            if kind in " -":
                if cursor >= len(lines) or lines[cursor].rstrip("\r\n") != body:
                    raise LocalWorkflowError("Patch context conflict (no fuzzy matching); PATCH NOT APPLIED.")
                if kind == " ": output.append(lines[cursor]); new_count += 1
                cursor += 1; old_count += 1
            elif kind == "+":
                newline = "\r\n" if any(line.endswith("\r\n") for line in lines) else "\n"
                output.append(body + (newline if original.endswith((b"\n", b"\r")) or cursor < len(lines) else "")); new_count += 1
            else:
                break
            i += 1
        if old_count != int(m.group(2) or 1) or new_count != int(m.group(4) or 1):
            raise LocalWorkflowError("Patch hunk counts disagree; PATCH NOT APPLIED.")
    output.extend(lines[cursor:])
    return "".join(output).encode("utf-8")


def apply_approved_patch(workspace: DeveloperWorkspace, repository: Path, authorization_run_id: str) -> dict[str, Any]:
    """Apply only the patch named by a valid, unused Phase 68 authorization run."""
    record = _load_authorization(workspace, authorization_run_id)
    if record.executed is not False or record.decision != "approve" or not record.execution_authorized:
        raise LocalWorkflowError("Authorization is rejected or already consumed; PATCH NOT APPLIED.")
    # Executions are append-only; same authorization ID is single-use.
    for entry in (workspace.root / "runs").iterdir():
        try:
            metadata_bytes = (entry / "metadata.json").read_bytes()
            result_bytes = (entry / "results.json").read_bytes()
            metadata, prior = json.loads(metadata_bytes), json.loads(result_bytes)
        except (OSError, ValueError):
            continue
        if isinstance(metadata, dict) and metadata.get("command") == "apply-patch":
            if (metadata_bytes != _json_bytes(metadata) or result_bytes != _json_bytes(prior)
                    or metadata.get("run_id") != entry.name or prior.get("mode") != "developer-local-patch-application"):
                raise LocalWorkflowError("Execution history is malformed; PATCH NOT APPLIED.")
            identity = {"mode": "developer-local", "command": "apply-patch",
                        "repository_id": metadata.get("repository_id"),
                        "working_tree_sha256": metadata.get("working_tree_sha256"), "payload": prior}
            if _digest(_json_bytes(identity))[:20] != entry.name:
                raise LocalWorkflowError("Execution history integrity failed; PATCH NOT APPLIED.")
            if prior.get("authorization_id") == record.authorization_id and prior.get("status") == "applied":
                raise LocalWorkflowError("Authorization was already consumed; PATCH NOT APPLIED.")
    draft = _read_patch_run(workspace, record.source_patch_run_id)
    workspace._prepare(Path(repository).resolve())
    validate_exact_patch_authorization(record, draft, repository)
    if _git(Path(repository).resolve(), ["status", "--porcelain=v1", "--untracked-files=all"]).strip():
        raise LocalWorkflowError("Repository has Git changes outside the approved state; PATCH NOT APPLIED.")
    if draft.status != "draft" or hashlib.sha256(draft.patch_text.encode()).hexdigest() != record.patch_sha256:
        raise LocalWorkflowError("Patch identity or status mismatch; PATCH NOT APPLIED.")
    paths = validate_unified_diff(draft.patch_text, draft.target_paths)
    if paths != record.candidate_paths:
        raise LocalWorkflowError("Candidate file scope differs from Phase 68 approval; PATCH NOT APPLIED.")
    root = Path(record.repository_path).resolve(strict=True)
    preimages, postimages = postimages_for_patch(root, draft.patch_text, paths, _apply_text)
    recomputed_symbols = derive_patch_symbols(draft.patch_text, preimages, postimages)
    if (recomputed_symbols != draft.candidate_symbol_scope
            or recomputed_symbols != record.candidate_symbol_scope
            or draft.allowed_symbol_scope != record.allowed_symbol_scope
            or not scope_is_allowed(recomputed_symbols, record.allowed_symbol_scope, preimages)):
        raise LocalWorkflowError("Patch symbol scope differs from exact Phase 68 approval; PATCH NOT APPLIED.")
    staged: dict[str, tuple[Path, bytes, bytes]] = {}
    # Capture repository-level Git state before computing any post-images.
    head_before = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode().strip()
    status_before = _status(root)
    index_before = _git_index_state(root)
    refs_before = _git(root, ["for-each-ref", "--format=%(refname) %(objectname)"]).decode()
    if status_before.strip():
        raise LocalWorkflowError("Repository has Git changes outside the approved state; PATCH NOT APPLIED.")
    section_by_path = patch_sections(draft.patch_text)
    for relative in paths:
        target = root.joinpath(*relative.split("/"))
        if target.is_symlink():
            raise LocalWorkflowError(f"Unsafe patch target {relative}; PATCH NOT APPLIED.")
        resolved = target.resolve(strict=True)
        if root not in resolved.parents or not resolved.is_file():
            raise LocalWorkflowError(f"Unsafe patch target {relative}; PATCH NOT APPLIED.")
        original = resolved.read_bytes()
        section = section_by_path.get(relative)
        if section is None:
            raise LocalWorkflowError(f"Patch section mismatch for {relative}; PATCH NOT APPLIED.")
        updated = _apply_text(original, section)
        staged[relative] = (resolved, original, updated)
    expected_changed = {p for p in paths if staged[p][1] != staged[p][2]}
    if expected_changed != set(paths):
        raise LocalWorkflowError("Approved patch includes a path with no resulting byte change; PATCH NOT APPLIED.")
    # Recheck exact approval-bound repository immediately before first replacement.
    validate_exact_patch_authorization(record, draft, root)
    head_check = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode().strip()
    refs_check = _git(root, ["for-each-ref", "--format=%(refname) %(objectname)"]).decode()
    if (_status(root).strip() or _git_index_state(root) != index_before
            or head_check != head_before or refs_check != refs_before):
        raise LocalWorkflowError("Repository drifted before mutation; PATCH NOT APPLIED.")
    written: list[str] = []
    def repo_state() -> tuple[str, bytes, str, str]:
        return (_git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode().strip(),
                _git_index_state(root), _status(root).decode(),
                _git(root, ["for-each-ref", "--format=%(refname) %(objectname)"]).decode())

    def restore_and_verify() -> bool:
        try:
            for relative in reversed(paths):
                target, old, _ = staged[relative]
                fd, temp_name = tempfile.mkstemp(prefix=".aida-phase69-restore-", dir=target.parent)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(old); stream.flush(); os.fsync(stream.fileno())
                os.replace(temp_name, target)
            return (all(staged[p][0].read_bytes() == staged[p][1] for p in paths)
                    and repo_state() == (head_before, index_before, status_before.decode(), refs_before))
        except Exception:
            return False

    try:
        for relative, (target, old, new) in staged.items():
            fd, temp_name = tempfile.mkstemp(prefix=".aida-phase69-", dir=target.parent)
            try:
                with os.fdopen(fd, "wb") as stream: stream.write(new); stream.flush(); os.fsync(stream.fileno())
                os.replace(temp_name, target)
            finally:
                if os.path.exists(temp_name): os.unlink(temp_name)
            written.append(relative)
        # Verify post-images and complete changed-path set before reporting success.
        actual_bytes = {p: staged[p][0].read_bytes() for p in paths}
        if any(actual_bytes[p] != staged[p][2] for p in paths):
            raise LocalWorkflowError("Post-application bytes differ from the computed approved post-state.")
        head_after, index_after, status_after, refs_after = repo_state()
        changed_paths = set()
        for line in status_after.splitlines():
            if line:
                changed_paths.add(line[3:].split(" -> ")[-1])
        if changed_paths != expected_changed:
            raise LocalWorkflowError("Actual changed paths differ from the approved target paths.")
        observed_postimages = {path: staged[path][0].read_text(encoding="utf-8") for path in paths}
        observed_diff = _git(root, ["diff", "--no-ext-diff", "--binary", "--", *paths]).decode("utf-8", errors="replace")
        observed_symbols = derive_patch_symbols(observed_diff, preimages, observed_postimages)
        if observed_symbols != recomputed_symbols:
            raise LocalWorkflowError("Observed applied symbols differ from the exact patch; PATCH NOT APPLIED.")
        if head_after != head_before or index_after != index_before or refs_after != refs_before:
            raise LocalWorkflowError(f"Git state changed: HEAD={head_after != head_before}, index={index_after != index_before}, refs={refs_after != refs_before}; before={refs_before!r}, after={refs_after!r}.")
    except Exception as error:
        restored = restore_and_verify()
        try:
            failed_inventory = scan_local_repository(root)
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            failure = PatchApplicationResult(
                "execution-" + hashlib.sha256((record.authorization_id + draft.patch_id + timestamp).encode()).hexdigest()[:20],
                "1.0", record.authorization_id, draft.source_action_id, draft.patch_id, record.repository_id,
                str(root), record.current_commit, failed_inventory.commit_sha, record.working_tree_sha256,
                failed_inventory.snapshot_id, paths, record.patch_sha256,
                "failed" if restored else "restoration_failed", tuple(written), "", str(error), timestamp)
            failed_payload = {"mode": "developer-local-patch-application", **failure.to_dict(),
                              "tests_executed": False, "git_commit_created": False,
                              "git_staging_performed": False, "restoration_verified": restored}
            failed_payload["run_id"] = workspace._record_run("apply-patch", failed_inventory, failed_payload)
        except Exception:
            pass
        if not restored:
            raise LocalWorkflowError(f"PATCH FAILED; restoration verification FAILED: {error}") from error
        raise LocalWorkflowError(f"PATCH NOT APPLIED; changes restored and verified: {error}") from error
    after = scan_local_repository(root)
    actual_diff = _git(root, ["diff", "--no-ext-diff", "--binary", "--", *paths]).decode("utf-8", errors="replace")
    semantic_index_sha256 = hashlib.sha256(_git_index_state(root)).hexdigest()
    refs_sha256 = hashlib.sha256(_git(root, ["for-each-ref", "--format=%(refname) %(objectname)"])).hexdigest()
    file_postimages = tuple((p, hashlib.sha256(staged[p][1]).hexdigest(),
                            hashlib.sha256(staged[p][2]).hexdigest(),
                            hashlib.sha256(actual_bytes[p]).hexdigest()) for p in sorted(paths))
    result = PatchApplicationResult("execution-" + hashlib.sha256(_json_bytes({
        "authorization_id": record.authorization_id, "source_patch_id": draft.patch_id,
        "file_postimages": [list(row) for row in file_postimages]})).hexdigest()[:20],
        "1.0", record.authorization_id, draft.source_action_id, draft.patch_id, record.repository_id,
        str(root), record.current_commit, after.commit_sha, record.working_tree_sha256, after.snapshot_id,
        paths, record.patch_sha256, "applied", tuple(sorted(expected_changed)),
        actual_diff, None, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        recomputed_symbols, observed_symbols, file_postimages)
    payload = {"mode": "developer-local-patch-application", **result.to_dict(), "expected_diff": draft.patch_text,
               "semantic_index_sha256": semantic_index_sha256, "semantic_index_unchanged": index_after == index_before,
               "refs_sha256": refs_sha256, "refs_unchanged": refs_after == refs_before,
               "tests_executed": False, "git_commit_created": False, "git_staging_performed": False}
    try:
        payload["run_id"] = workspace._record_run("apply-patch", after, payload)
    except Exception as error:
        restored = restore_and_verify()
        raise LocalWorkflowError("Execution record failed; " +
            ("source restoration verified." if restored else "source restoration verification FAILED.")) from error
    return payload
