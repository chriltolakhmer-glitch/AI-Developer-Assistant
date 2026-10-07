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
