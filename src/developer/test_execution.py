"""Explicit, bounded unittest execution for one successful Phase 69 result."""
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from typing import Any

from src.developer_testing import catalog, plan as plan_tests
from .local_workflow import (DeveloperWorkspace, LocalWorkflowError, _digest, _git, _git_index_state,
                             _json_bytes, scan_local_repository)
from .patch_application import _load_authorization

_WORKER = Path(__file__).with_name("test_runner_worker.py").resolve(strict=True)
_TEST_ID = re.compile(r"^tests(?:\.[A-Za-z_]\w*){2,}$")


@dataclass(frozen=True, slots=True)
class TestExecutionPlan:
    plan_id: str
    schema_version: str
    source_execution_id: str
    repository_id: str
    repository_path: str
    repository_state: str
    target_paths: tuple[str, ...]
    test_runner: str
    test_identities: tuple[str, ...]
    selection_source: str
    changed_test_files: tuple[str, ...]
    selection_tier: str

    def to_dict(self) -> dict[str, Any]:
        return {f.name: list(getattr(self, f.name)) if f.name in {
            "target_paths", "test_identities", "changed_test_files"} else getattr(self, f.name)
                for f in fields(self)}


@dataclass(frozen=True, slots=True)
class TestExecutionObservation:
    observation_id: str
    schema_version: str
    source_execution_id: str
    source_authorization_id: str
    source_patch_id: str
    source_action_id: str
    repository_id: str
    repository_path: str
    repository_state_before: str
    repository_state_after: str
    test_runner: str
    test_identities: tuple[str, ...]
    started_at: str
    completed_at: str
    duration_seconds: float
    exit_code: int
    tests_run: int
    passed: int
    failures: int
    errors: int
    skipped: int
    status: str
    stdout_sha256: str
    stderr_sha256: str
    stdout_reference: str
    stderr_reference: str
    unexpected_repository_changes: bool
    unexpected_changed_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {f.name: list(getattr(self, f.name)) if f.name in {
            "test_identities", "unexpected_changed_paths"} else getattr(self, f.name)
                for f in fields(self)}


def _status(root: Path, *, ignored: bool = False) -> bytes:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    args = ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"]
    if ignored:
        args.append("--ignored")
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env)
    if result.returncode:
        raise LocalWorkflowError("Cannot inspect target repository status.")
    return result.stdout


def _changed_paths(status: bytes) -> set[str]:
    result = set()
    for raw in status.decode("utf-8", errors="surrogateescape").splitlines():
        if len(raw) >= 4:
            result.add(raw[3:].split(" -> ")[-1])
    return result


def _read_execution(workspace: DeveloperWorkspace, run_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{20}", run_id):
        raise LocalWorkflowError("Invalid Phase 69 execution run ID; TEST NOT EXECUTED.")
    directory = workspace._contained(workspace.root / "runs" / run_id)
    try:
        mb, rb = (directory / "metadata.json").read_bytes(), (directory / "results.json").read_bytes()
        meta, payload = json.loads(mb), json.loads(rb)
        if (mb != _json_bytes(meta) or rb != _json_bytes(payload)
                or meta.get("run_id") != run_id or meta.get("command") != "apply-patch"
                or meta.get("workspace_sha256") != _digest(str(workspace.root).encode("utf-8"))
                or payload.get("mode") != "developer-local-patch-application"):
            raise ValueError("invalid Phase 69 run record")
        identity = {"mode": "developer-local", "command": "apply-patch",
                    "repository_id": meta.get("repository_id"),
                    "working_tree_sha256": meta.get("working_tree_sha256"), "payload": payload}
        if _digest(_json_bytes(identity))[:20] != run_id:
            raise ValueError("Phase 69 run identity does not match contents")
    except (OSError, ValueError, TypeError) as error:
        raise LocalWorkflowError("Phase 69 execution record is missing, malformed, or tampered; TEST NOT EXECUTED.") from error
    return {"metadata": meta, "payload": payload}


def _validate_phase69(workspace: DeveloperWorkspace, repository: Path, run_id: str) -> tuple[dict[str, Any], Any, Any]:
    loaded = _read_execution(workspace, run_id)
    meta, result = loaded["metadata"], loaded["payload"]
    if (result.get("status") != "applied" or result.get("tests_executed") is not False
            or result.get("git_commit_created") is not False or result.get("git_staging_performed") is not False):
        raise LocalWorkflowError("A successful Phase 69 application is required; TEST NOT EXECUTED.")
    expected_execution_id = "execution-" + hashlib.sha256(
        (result.get("authorization_id", "") + result.get("source_patch_id", "")).encode()).hexdigest()[:20]
    if (result.get("execution_id") != expected_execution_id
            or result.get("patch_sha256") != hashlib.sha256(result.get("expected_diff", "").encode()).hexdigest()
            or tuple(result.get("target_paths", ())) != tuple(result.get("files_changed", ()))
            or not result.get("authorization_id") or not result.get("source_action_id")
            or not result.get("source_patch_id")):
        raise LocalWorkflowError("Phase 69 execution bindings are invalid; TEST NOT EXECUTED.")
    auth_matches = []
    for entry in (workspace.root / "runs").iterdir():
        try:
            candidate = json.loads((entry / "results.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if (candidate.get("mode") == "developer-local-patch-authorization"
                and candidate.get("authorization_id") == result["authorization_id"]):
            auth_matches.append(entry.name)
    if len(auth_matches) != 1:
        raise LocalWorkflowError("Phase 69 authorization record is missing or ambiguous; TEST NOT EXECUTED.")
    authorization = _load_authorization(workspace, auth_matches[0])
    if (authorization.decision != "approve" or authorization.execution_authorized is not True
            or authorization.source_action_id != result["source_action_id"]
            or authorization.source_patch_id != result["source_patch_id"]
            or authorization.repository_id != result["repository_id"]
            or authorization.patch_sha256 != result["patch_sha256"]):
        raise LocalWorkflowError("Phase 69 approval binding is invalid; TEST NOT EXECUTED.")
    root = Path(repository).expanduser().resolve(strict=True)
    if (str(root) != str(Path(result.get("repository_path", "")).resolve())
            or meta.get("repository_id") != result.get("repository_id")
            or str(root) != str(Path(meta.get("repository_path", "")).resolve())):
        raise LocalWorkflowError("Execution belongs to another repository; TEST NOT EXECUTED.")
    inventory = scan_local_repository(root)
    head = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode().strip()
    paths = tuple(result["files_changed"])
    current_diff = _git(root, ["diff", "--no-ext-diff", "--binary", "--", *paths]).decode("utf-8", errors="replace")
    phase69_diff = result.get("diff_after", "")
    expected_patch = result.get("expected_diff", "")
    patch_hash = result.get("patch_sha256", "")
    expected_paths = set(paths)
    diff_sections = re.findall(r"(?m)^diff --git a/(.*?) b/(.*?)$", phase69_diff)
    auth_payload = authorization.to_dict()
    if (inventory.repository_id != result["repository_id"] or head != result["repository_after"]
            or inventory.snapshot_id != result["working_tree_after"]
            or _changed_paths(_status(root)) != expected_paths or current_diff != phase69_diff
            or hashlib.sha256(expected_patch.encode()).hexdigest() != patch_hash
            or {new for _, new in diff_sections} != expected_paths
            or any(old != new for old, new in diff_sections)
            or auth_payload.get("repository_path") != str(root)
            or auth_payload.get("repository_id") != inventory.repository_id
            or auth_payload.get("current_commit") != head
            or auth_payload.get("working_tree_sha256") != result.get("working_tree_before")
            or auth_payload.get("patch_sha256") != patch_hash
            or set(auth_payload.get("target_paths", ())) != expected_paths):
        raise LocalWorkflowError("Repository no longer matches the Phase 69 post-state; TEST NOT EXECUTED.")
    _check_phase69_draft_and_auth(workspace, authorization, expected_paths, root, result, inventory)
    return result, authorization, inventory


def _check_phase69_draft_and_auth(workspace: DeveloperWorkspace, authorization, paths: set[str],
                                  root: Path, result: dict[str, Any], inventory) -> None:
    from .patch_authorization import _read_patch_run
    draft = _read_patch_run(workspace, authorization.source_patch_run_id)
    draft.validate()
    authorization.validate()
    if (draft.patch_id != result["source_patch_id"] or draft.source_action_id != result["source_action_id"]
            or draft.repository_id != result["repository_id"] or set(draft.target_paths) != paths
            or draft.patch_text != result.get("expected_diff") or draft.repository_path != str(root)
            or draft.current_commit != result.get("repository_before")
            or draft.working_tree_sha256 != result.get("working_tree_before")
            or authorization.source_patch_id != draft.patch_id
            or authorization.source_action_id != draft.source_action_id
            or authorization.repository_id != inventory.repository_id
            or authorization.repository_path != str(root)
            or authorization.current_commit != result.get("repository_before")
            or authorization.working_tree_sha256 != result.get("working_tree_before")
            or authorization.patch_sha256 != result.get("patch_sha256")
            or set(authorization.target_paths) != paths):
        raise LocalWorkflowError("Phase 69 PatchDraft binding is invalid; TEST NOT EXECUTED.")


def _make_plan(result: dict[str, Any], inventory, repository: Path,
               explicit_tests: tuple[str, ...]) -> TestExecutionPlan:
    identities = {name for module_tests in catalog(repository).values() for name in module_tests}
    if explicit_tests:
        unique = tuple(sorted(set(explicit_tests)))
        if any(not _TEST_ID.fullmatch(name) or name not in identities for name in unique):
            raise LocalWorkflowError("Explicit selector must be an exact known unittest method identity.")
        selection = plan_tests(root=repository, tests=unique)
        source = "explicit_exact_test_identities"
    else:
        selection = plan_tests(root=repository, changed=True)
        source = "static_changed_file_dependency_selection"
    selected = tuple(sorted(set(selection["selected_tests"])))
    if not selected or any(name not in identities for name in selected):
        raise LocalWorkflowError("No supported exact unittest identities were selected; TEST NOT EXECUTED.")
    if tuple(selection["changed_files"]) and set(selection["changed_files"]) != set(result["files_changed"]):
        raise LocalWorkflowError("Test selection observed files outside the Phase 69 patch scope.")
    identity = {"schema_version": "1.0", "source_execution_id": result["execution_id"],
                "repository_id": inventory.repository_id, "repository_state": inventory.snapshot_id,
                "target_paths": list(result["files_changed"]), "test_runner": "python -m unittest",
                "test_identities": list(selected), "selection_source": source}
    plan_id = "test-plan-" + hashlib.sha256(_json_bytes(identity)).hexdigest()[:20]
    return TestExecutionPlan(plan_id, "1.0", result["execution_id"], inventory.repository_id,
                             str(repository), inventory.snapshot_id, tuple(result["files_changed"]),
                             "python -m unittest", selected, source,
                             tuple(selection["changed_files"]), selection["tier"])


def _state_snapshot(root: Path, inventory) -> dict[str, Any]:
    head = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode().strip()
    refs = _git(root, ["for-each-ref", "--format=%(refname) %(objectname)"])
    return {"head": head, "index_entries_sha256": hashlib.sha256(_git_index_state(root)).hexdigest(),
            "refs_sha256": hashlib.sha256(refs).hexdigest(), "working_tree_sha256": inventory.snapshot_id,
            "status": _status(root).decode("utf-8", errors="surrogateescape"),
            "ignored_status": _status(root, ignored=True).decode("utf-8", errors="surrogateescape")}


def execute_applied_patch_tests(workspace: DeveloperWorkspace, repository: Path,
                                execution_run_id: str, *, tests: tuple[str, ...] = ()) -> dict[str, Any]:
    """Run a validated unittest plan for an unchanged successful Phase 69 result."""
    root = Path(repository).expanduser().resolve(strict=True)
    workspace._prepare(root)
    result, authorization, before_inventory = _validate_phase69(workspace, root, execution_run_id)
    plan = _make_plan(result, before_inventory, root, tests)
    before = _state_snapshot(root, before_inventory)
    # Final source binding immediately before starting the fixed unittest worker.
    latest = scan_local_repository(root)
    if (latest.snapshot_id != result["working_tree_after"]
            or _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode().strip() != result["repository_after"]
            or _changed_paths(_status(root)) != set(result["files_changed"])):
        raise LocalWorkflowError("Repository drifted before test execution; TEST NOT EXECUTED.")
    started_clock = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    request = {"repository_path": str(root), "test_identities": list(plan.test_identities)}
    completed = subprocess.run([sys.executable, "-B", str(_WORKER)], input=json.dumps(request), text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=root, env=env, check=False)
    completed_at = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    duration = time.perf_counter() - started_clock
    after_inventory = scan_local_repository(root)
    after = _state_snapshot(root, after_inventory)
    unexpected: set[str] = set()
    if after["status"] != before["status"]:
        unexpected |= _changed_paths(after["status"].encode()) ^ _changed_paths(before["status"].encode())
        # Same paths with changed index/staging state are still unexpected.
        if after["status"] != before["status"]:
            unexpected |= _changed_paths(after["status"].encode()) & _changed_paths(before["status"].encode())
    if after["ignored_status"] != before["ignored_status"]:
        unexpected.add("<ignored-files>")
    if after_inventory.snapshot_id != before_inventory.snapshot_id:
        unexpected.add("<python-source-state>")
    for key in ("head", "index_entries_sha256", "refs_sha256"):
        if after[key] != before[key]:
            unexpected.add(f"<git-{key}>")
    report: dict[str, Any]
    protocol_error = None
    try:
        if completed.returncode != 0:
            raise ValueError(f"worker process exited {completed.returncode}")
        report = json.loads(completed.stdout)
        required = {"exit_code", "tests_run", "passed", "failures", "errors", "skipped",
                    "stdout", "stderr", "duration_seconds"}
        if not isinstance(report, dict) or not required <= set(report):
            raise ValueError("worker response fields are incomplete")
    except (ValueError, TypeError) as error:
        protocol_error = f"Test worker did not return a structured unittest result: {error}"
        report = {"exit_code": completed.returncode or 2, "tests_run": 0, "passed": 0,
                  "failures": 0, "errors": 1, "skipped": 0, "stdout": completed.stdout,
                  "stderr": completed.stderr + protocol_error, "failure_tests": [],
                  "error_tests": ["worker protocol"], "skip_tests": []}
    stdout_bytes = str(report.get("stdout", "")).encode("utf-8")
    stderr_text = str(report.get("stderr", "")) + str(report.get("runner_output", "")) + completed.stderr
    if protocol_error:
        stderr_text += protocol_error
    stderr_bytes = stderr_text.encode("utf-8")
    observation_id = "observation-" + uuid.uuid4().hex[:20]
    evidence_root = workspace._contained(workspace.root / "evidence" / observation_id)
    evidence_root.mkdir(parents=True, exist_ok=False)
    stdout_path, stderr_path = evidence_root / "stdout.log", evidence_root / "stderr.log"
    stdout_path.write_bytes(stdout_bytes); stderr_path.write_bytes(stderr_bytes)
    exit_code = int(report.get("exit_code", completed.returncode or 2))
    errors = int(report.get("errors", 0))
    failures = int(report.get("failures", 0))
    status = ("error" if errors or protocol_error else "failed" if exit_code != 0 or failures
              else "passed")
    observation = TestExecutionObservation(
        observation_id, "1.0", result["execution_id"], authorization.authorization_id,
        result["source_patch_id"], result["source_action_id"], result["repository_id"], str(root),
        before_inventory.snapshot_id, after_inventory.snapshot_id, plan.test_runner, plan.test_identities,
        started_at, completed_at, duration, exit_code, int(report.get("tests_run", 0)),
        int(report.get("passed", 0)), failures, errors, int(report.get("skipped", 0)), status,
        hashlib.sha256(stdout_bytes).hexdigest(), hashlib.sha256(stderr_bytes).hexdigest(),
        str(stdout_path), str(stderr_path), bool(unexpected), tuple(sorted(unexpected)))
    payload = {"mode": "developer-local-test-observation", **observation.to_dict(),
               "plan": plan.to_dict(), "expected_failures": int(report.get("expected_failures", 0)),
               "unexpected_successes": int(report.get("unexpected_successes", 0)),
               "failure_tests": report.get("failure_tests", []), "error_tests": report.get("error_tests", []),
               "skip_tests": report.get("skip_tests", []), "requested_explicitly": True,
               "automatic_retry": False, "source_mutation_performed": False,
               "git_commit_created_by_phase70": False, "git_staging_performed_by_phase70": False,
               "lifecycle_transition_performed": False, "phase71_verification_performed": False,
               "worker_process_exit_code": completed.returncode}
    payload["run_id"] = workspace._record_run("test-applied-patch", after_inventory, payload)
    payload["plan"] = plan.to_dict()
    return payload
