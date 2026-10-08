"""Non-writing repository facts for the first desktop UI slice."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
import os
from pathlib import Path
import subprocess
from typing import Any

from .change_impact import _index_freshness
from .local_workflow import DeveloperWorkspace, LocalWorkflowError, parse_local_repository


def _git_read(root: Path, *arguments: str) -> bytes:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments], env=env,
            capture_output=True, check=False,
        )
    except OSError as error:
        raise LocalWorkflowError(f"Cannot read Git repository: {error}") from error
    if result.returncode:
        detail = os.fsdecode(result.stderr).strip() or "Git returned no diagnostic"
        raise LocalWorkflowError(f"Cannot read Git repository: {detail}")
    return result.stdout


def _software_identity() -> tuple[str, str]:
    source_root = Path(__file__).resolve().parents[2]
    try:
        software_version = (source_root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        try:
            software_version = version("research-prototype")
        except PackageNotFoundError:
            software_version = "unknown"
    # Do not report an enclosing/target repository's HEAD as AIDA authority.
    authority = "unknown"
    if (source_root / ".git").exists():
        try:
            top = Path(os.fsdecode(_git_read(source_root, "rev-parse", "--show-toplevel")).strip()).resolve()
            if top == source_root:
                authority = _git_read(source_root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
        except (LocalWorkflowError, OSError, UnicodeError):
            pass
    return software_version or "unknown", authority


def read_repository(workspace: DeveloperWorkspace, repository: Path) -> dict[str, Any]:
    """Read facts only; never prepare storage, record evidence or load a model."""
    root = Path(repository).expanduser().resolve(strict=True)
    workspace._validate_isolation(root)
    if workspace.root.exists() and not workspace.root.is_dir():
        raise LocalWorkflowError(f"Developer workspace is not a directory: '{workspace.root}'.")
    parsed = parse_local_repository(root)
    inventory = parsed.inventory
    branch = _git_read(root, "rev-parse", "--symbolic-full-name", "HEAD").decode("utf-8", errors="replace").strip()
    detached = branch == "HEAD"
    branch_name = None if detached else branch.removeprefix("refs/heads/")
    raw_status = _git_read(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = raw_status.split(b"\0")
    changes = []
    index = 0
    while index < len(entries) and entries[index]:
        entry = entries[index]
        if len(entry) < 4 or entry[2:3] != b" ":
            raise LocalWorkflowError("Git returned malformed porcelain status.")
        code = entry[:2].decode("ascii")
        row = {"status": code, "path": os.fsdecode(entry[3:])}
        if "R" in code or "C" in code:
            index += 1
            if index >= len(entries) or not entries[index]:
                raise LocalWorkflowError("Git returned incomplete renamed-path status.")
            row["original_path"] = os.fsdecode(entries[index])
        changes.append(row)
        index += 1
    # A refresh is a snapshot, never execution permission. Refuse a moving HEAD.
    current_head = _git_read(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    if current_head != inventory.commit_sha:
        raise LocalWorkflowError("Repository HEAD changed while status was read; refresh explicitly.")
    try:
        freshness, _ = _index_freshness(workspace, parsed)
    except (LocalWorkflowError, OSError, ValueError, TypeError, KeyError) as error:
        freshness = {"status": "unavailable", "reason": str(error)}
    software_version, authority = _software_identity()
    return {
        "repository_path": str(inventory.root), "repository_id": inventory.repository_id,
        "branch": branch_name, "detached_head": detached, "head": inventory.commit_sha,
        "working_tree_sha256": inventory.snapshot_id, "working_tree_status": changes,
        "clean": not changes,
        "staged_changes": any(row["status"][0] not in " ?" for row in changes),
        "unstaged_changes": any(row["status"][1] not in " ?" for row in changes),
        "untracked_files": any(row["status"] == "??" for row in changes),
        "supported_languages": inventory.summary()["supported_languages"],
        "workspace_path": str(workspace.root), "index_freshness": freshness,
        "aida_version": software_version, "source_authority": authority,
        "parser_failures": list(parsed.parse_failures),
        "notice": "Read-only snapshot; no AIDA evidence created. Branch is display context only.",
    }


def review_patch(workspace: DeveloperWorkspace, repository: Path,
                 patch_run_id: str) -> dict[str, Any]:
    """Load canonical review evidence without preparing storage or recording runs."""
    from .patch_authorization import _read_patch_run, _check_repository
    from .local_workflow import _digest, scan_local_repository
    from .execution_verification import _read_run, _proposal

    root = Path(repository).expanduser().resolve(strict=True)
    workspace._validate_isolation(root)
    draft = _read_patch_run(workspace, patch_run_id)
    _, payload = _read_run(workspace, patch_run_id, "patch")
    if any(payload.get(key) != value for key, value in draft.to_dict().items()):
        raise LocalWorkflowError("Phase 67 patch changed while review was read; review explicitly again.")
    _check_repository(draft, scan_local_repository(root), require_state=False)
    facts = read_repository(workspace, root)
    bound_tests, plan_error, warnings = None, None, []
    plan_run_id = payload.get("source_plan_run_id")
    if plan_run_id:
        try:
            metadata, plan = _read_run(workspace, plan_run_id, "plan")
            proposal = _proposal(plan["proposed_action"])
            selection = plan["tests"]["expected_test_selection"]
            if (proposal.action_id != draft.source_action_id
                    or metadata["repository_id"] != draft.repository_id
                    or metadata["repository_path"] != draft.repository_path
                    or proposal.current_commit != draft.current_commit
                    or proposal.working_tree_sha256 != draft.working_tree_sha256
                    or selection["status"] != "known"
                    or selection["selected_tests"] != plan["tests"]["selected_tests"]):
                raise ValueError("Linked plan/action/test association is unavailable.")
            bound_tests = list(selection["selected_tests"])
            warnings = plan.get("warnings", [])
        except (LocalWorkflowError, KeyError, TypeError, ValueError) as error:
            plan_error = str(error)
    return {
        "draft": {**payload, "run_id": patch_run_id}, "facts": facts,
        # Existing shared backend SHA-256 primitive; same UTF-8 bytes as Phase 68.
        "patch_sha256": _digest(draft.patch_text.encode("utf-8")),
        "state_matches": (facts["head"] == draft.current_commit
                          and facts["working_tree_sha256"] == draft.working_tree_sha256),
        "bound_tests": bound_tests, "linked_plan_error": plan_error,
        "plan_warnings": warnings,
    }
