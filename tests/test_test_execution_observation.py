"""Focused Phase 70 execution and Phase 71 verification invariants."""
from pathlib import Path
import json
import hashlib
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from src.developer.local_workflow import (DeveloperWorkspace, LocalWorkflowError,
                                          _git_index_state, scan_local_repository)
from src.developer.patch_application import apply_approved_patch
from src.developer.patch_authorization import record_patch_decision
from src.developer.patch_drafting import SuppliedPatchGenerator, _draft_patch_candidate as draft_patch
from src.developer.test_execution import execute_applied_patch_tests
from src.developer.implementation_planning import ProposedAction
from src.developer.execution_verification import verify_execution


class TestExecutionObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        home = Path(self.temp.name)
        self.repo = home / "repo"
        (self.repo / "tests").mkdir(parents=True)
        (self.repo / "app.py").write_text("def value():\n    return 1\n", encoding="utf-8")
        (self.repo / "tests" / "__init__.py").write_text("", encoding="utf-8")
        self._write_tests("pass")
        self.git("init", "--quiet")
        self.git("config", "user.name", "Phase 70 Test")
        self.git("config", "user.email", "phase70@example.invalid")
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "baseline")
        self.workspace = DeveloperWorkspace(home / "outside" / "workspace")
        self.repo.joinpath("app.py").write_text("def value():\n    return 0\n", encoding="utf-8")
        self.git("add", "app.py")
        self.git("commit", "--quiet", "-m", "target change")
        self.head = self.git("rev-parse", "HEAD")
        self.index = _git_index_state(self.repo)
        inventory = scan_local_repository(self.repo)
        self.plan_run_id = self._record_phase65_plan(inventory)
        self.patch_text = "--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,2 @@\n def value():\n-    return 0\n+    return 2\n"
        draft = draft_patch(self.workspace, self.repo, self.proposal,
                            SuppliedPatchGenerator(self.patch_text))
        approval = record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve")
        self.applied = apply_approved_patch(self.workspace, self.repo, approval["run_id"])

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True).stdout.decode().strip()

    def _write_tests(self, mode):
        rows = ["import unittest", "import app", "from pathlib import Path", "",
                "class AppTests(unittest.TestCase):"]
        if mode in {"pass", "fail", "skip", "git-refresh"}:
            rows += ["    def test_value(self):", "        self.assertEqual(2, app.value())"]
        if mode == "fail":
            rows = ["import unittest", "import app", "", "class AppTests(unittest.TestCase):",
                    "    def test_value(self):", "        self.assertEqual(3, app.value())"]
        if mode == "skip":
            rows += ["", "    @unittest.skip('planned fixture skip')", "    def test_skipped(self):",
                     "        self.fail('must not run')"]
        if mode == "side-effect":
            rows += ["    def test_side_effect(self):", "        Path('side-effect.txt').write_text('created')"]
        if mode == "error":
            rows += ["    def test_error(self):", "        raise RuntimeError('fixture error')"]
        if mode == "git-refresh":
            rows += ["    def test_git_metadata_refresh(self):",
                     "        import subprocess",
                     "        subprocess.run(['git', 'status', '--porcelain'], check=True, capture_output=True)"]
        (self.repo / "tests" / "test_app.py").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def _record_phase65_plan(self, inventory, *, uncertain=False, warnings=()):
        targets = [{"file_path": "app.py", "qualified_symbol": "value", "role": "primary_target",
                    "evidence_types": ["changed_code"], "reasons": ["fixture evidence"],
                    "current_index_evidence": False}]
        repository = {"repository_path": str(self.repo.resolve()), "repository_id": inventory.repository_id,
                      "base_reference": "HEAD", "base_commit": inventory.commit_sha,
                      "current_commit": inventory.commit_sha, "working_tree_sha256": inventory.snapshot_id}
        impact = {"repository": repository, "index_freshness": {"working_tree_sha256": inventory.snapshot_id},
                  "retrieval": {"query_evidence": []}}
        exact_test = "tests.test_app.AppTests.test_value"
        proposal = ProposedAction.from_plan(impact, targets, "Change value function", [])
        tests = {"selected_tests": [exact_test], "selectors": ["tests.test_app"], "uncertain": uncertain,
                 "exhaustive_required": False}
        payload = {"mode": "developer-local-implementation-plan", "status": "completed",
                   "goal": "Change value function", "repository": repository,
                   "change_impact": {**impact, "tests": tests}, "proposed_action": proposal.to_dict(),
                   "implementation_targets": targets, "tests": tests, "unresolved_evidence": [],
                   "warnings": list(warnings),
                   "tests_executed": False, "source_changes_made": False}
        payload["run_id"] = self.workspace._record_run("plan-change", inventory, payload)
        self.proposal = proposal.to_dict()
        return payload["run_id"]

    def _reapply_with_test_mode(self, mode, *, uncertain=False, warnings=()):
        # Rebuild the disposable repository state before creating a fresh Phase 69 chain.
        self.git("checkout", "--", "app.py")
        self._write_tests(mode)
        self.git("add", "tests/test_app.py")
        self.git("commit", "--quiet", "-m", f"fixture {mode}")
        self.head = self.git("rev-parse", "HEAD")
        self.index = _git_index_state(self.repo)
        self.workspace = DeveloperWorkspace(self.workspace.root.parent / f"workspace-{mode}")
        inventory = scan_local_repository(self.repo)
        self.plan_run_id = self._record_phase65_plan(inventory, uncertain=uncertain, warnings=warnings)
        draft = draft_patch(self.workspace, self.repo, self.proposal,
                            SuppliedPatchGenerator(self.patch_text))
        approval = record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve")
        self.applied = apply_approved_patch(self.workspace, self.repo, approval["run_id"])

    def run_tests(self, *identities):
        return execute_applied_patch_tests(self.workspace, self.repo, self.applied["run_id"],
                                           tests=tuple(identities))

    def test_passing_exact_test_records_external_observation_and_repeat_is_distinct(self):
        identity = "tests.test_app.AppTests.test_value"
        first, second = self.run_tests(identity), self.run_tests(identity)
        self.assertEqual("passed", first["status"])
        self.assertEqual((1, 1, 0, 0, 0), (first["tests_run"], first["passed"], first["failures"], first["errors"], first["skipped"]))
        self.assertNotEqual(first["observation_id"], second["observation_id"])
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.assertTrue(Path(first["stdout_reference"]).is_file())
        self.assertTrue(Path(first["stderr_reference"]).is_file())
        self.assertEqual(self.head, self.git("rev-parse", "HEAD"))
        self.assertEqual(self.index, _git_index_state(self.repo))
        self.assertEqual("M app.py", self.git("status", "--short"))
        self.assertIn(b"return 2", (self.repo / "app.py").read_bytes())

    def test_phase71_verifies_complete_chain_without_mutation_or_lifecycle_transition(self):
        observation = self.run_tests("tests.test_app.AppTests.test_value")
        head, index, target = self.git("rev-parse", "HEAD"), _git_index_state(self.repo), (self.repo / "app.py").read_bytes()
        result = verify_execution(self.workspace, self.repo, self.applied["run_id"], observation["run_id"])
        self.assertEqual("verified", result["status"], result["deviations"])
        self.assertEqual(self.plan_run_id, result["plan_run_id"])
        self.assertEqual(["tests.test_app.AppTests.test_value"], result["expected_test_identities"])
        self.assertEqual(result["expected_test_identities"], result["executed_test_identities"])
        self.assertFalse(result["lifecycle_transition_performed"])
        self.assertFalse(result["source_mutation_performed"])
        self.assertFalse(result["git_staging_performed"])
        self.assertFalse(result["git_commit_created"])
        self.assertFalse(result["phase72_started"])
        self.assertEqual(head, self.git("rev-parse", "HEAD"))
        self.assertEqual(index, _git_index_state(self.repo))
        self.assertEqual(target, (self.repo / "app.py").read_bytes())

    def _apply_equivalent_serialization_fixture(self):
        self.git("checkout", "--", "app.py")
        (self.repo / "app.py").write_bytes(b'def value():\n    """Old documentation."""\n    return 0\n')
        self.git("add", "app.py")
        self.git("commit", "--quiet", "-m", "signature and docstring baseline")
        self.workspace = DeveloperWorkspace(self.workspace.root.parent / "equivalent-workspace")
        self.plan_run_id = self._record_phase65_plan(scan_local_repository(self.repo))
        self.patch_text = ('--- a/app.py\n+++ b/app.py\n@@ -1,3 +1,3 @@\n'
                           '-def value():\n+def value(optional=0):\n'
                           '-    """Old documentation."""\n+    """New documentation."""\n'
                           '-    return 0\n+    return 2 + optional\n')
        draft = draft_patch(self.workspace, self.repo, self.proposal, SuppliedPatchGenerator(self.patch_text))
        approval = record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve")
        self.applied = apply_approved_patch(self.workspace, self.repo, approval["run_id"])

    def test_equivalent_diff_serialization_verifies_exact_postimage(self):
        self._apply_equivalent_serialization_fixture()
        # The old ordered hunk comparison rejected this valid exact application.
        supplied = tuple(row for row in self.patch_text.splitlines() if row.startswith(("-", "+")))
        regenerated = tuple(row for row in self.applied["diff_after"].splitlines() if row.startswith(("-", "+")))
        self.assertNotEqual(supplied, regenerated)
        row = self.applied["file_postimages"][0]
        self.assertEqual(row["expected_postimage_sha256"], row["observed_postimage_sha256"])
        self.assertEqual(row["observed_postimage_sha256"], hashlib.sha256((self.repo / "app.py").read_bytes()).hexdigest())
        observation = self.run_tests("tests.test_app.AppTests.test_value")
        result = verify_execution(self.workspace, self.repo, self.applied["run_id"], observation["run_id"])
        self.assertEqual("verified", result["status"], result["deviations"])

    def test_current_postimage_mismatch_is_not_verified(self):
        observation = self.run_tests("tests.test_app.AppTests.test_value")
        (self.repo / "app.py").write_bytes(b"def value():\n    return 3\n")
        result = verify_execution(self.workspace, self.repo, self.applied["run_id"], observation["run_id"])
        self.assertEqual("not_verified", result["status"])
        self.assertIn("current_content_differs_from_phase69_observed_postimage:app.py", result["deviations"])

    def test_tampered_postimage_hashes_fail_historical_integrity(self):
        from src.developer.local_workflow import _json_bytes
        from src.developer.test_execution import _validate_phase69
        record = self.workspace.root / "runs" / self.applied["run_id"] / "results.json"
        original = record.read_bytes()
        for key in ("preimage_sha256", "expected_postimage_sha256", "observed_postimage_sha256", "file_path"):
            with self.subTest(key=key):
                payload = json.loads(original)
                payload["file_postimages"][0][key] = "b.py" if key == "file_path" else "0" * 64
                record.write_bytes(_json_bytes(payload))
                with self.assertRaisesRegex(LocalWorkflowError, "tampered"):
                    _validate_phase69(self.workspace, self.repo, self.applied["run_id"])
                record.write_bytes(original)

    def test_phase71_preserves_nonblocking_retrieval_omission_warning(self):
        omission = {"type": "retrieval_omission", "classification": "non_blocking",
                    "evidence": {"file_path": "tests/test_app.py", "symbol_name": "AppTests.test_value",
                                 "reason": "relationship expansion limit"},
                    "basis": {"kind": "exact_expected_test_binding",
                              "test_identity": "tests.test_app.AppTests.test_value"}}
        self.git("checkout", "--", "app.py")
        self.workspace = DeveloperWorkspace(self.workspace.root.parent / "workspace-warning")
        inventory = scan_local_repository(self.repo)
        self.plan_run_id = self._record_phase65_plan(inventory, warnings=(omission,))
        draft = draft_patch(self.workspace, self.repo, self.proposal,
                            SuppliedPatchGenerator(self.patch_text))
        approval = record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve")
        self.applied = apply_approved_patch(self.workspace, self.repo, approval["run_id"])
        observation = self.run_tests("tests.test_app.AppTests.test_value")
        result = verify_execution(self.workspace, self.repo, self.applied["run_id"], observation["run_id"])
        self.assertEqual("verified", result["status"], result["deviations"])
        self.assertIn("phase65_retrieval_context_omitted_but_independently_grounded:tests/test_app.py:AppTests.test_value",
                      result["warnings"])

    def test_phase71_blocks_failed_tests_and_phase70_side_effects(self):
        self._reapply_with_test_mode("fail")
        failed = self.run_tests("tests.test_app.AppTests.test_value")
        verified = verify_execution(self.workspace, self.repo, self.applied["run_id"], failed["run_id"])
        self.assertNotEqual("verified", verified["status"])
        self.assertIn("phase70_tests_did_not_pass", verified["deviations"])
        self._reapply_with_test_mode("side-effect")
        side_effect = self.run_tests("tests.test_app.AppTests.test_side_effect")
        verified = verify_execution(self.workspace, self.repo, self.applied["run_id"], side_effect["run_id"])
        self.assertNotEqual("verified", verified["status"])
        self.assertIn("phase70_observation_reports_unexpected_repository_changes", verified["deviations"])

    def test_phase71_records_exact_test_mismatch_and_stale_repository(self):
        observation = self.run_tests("tests.test_app.AppTests.test_value")
        payload_path = self.workspace.root / "runs" / observation["run_id"] / "results.json"
        payload = json.loads(payload_path.read_bytes())
        payload["plan"]["test_identities"] = ["tests.test_app.AppTests.test_skipped"]
        payload["test_identities"] = ["tests.test_app.AppTests.test_skipped"]
        plan = payload["plan"]
        plan_identity = {"schema_version": "1.0", "source_execution_id": plan["source_execution_id"],
                         "repository_id": plan["repository_id"], "repository_state": plan["repository_state"],
                         "target_paths": plan["target_paths"], "test_runner": plan["test_runner"],
                         "test_identities": plan["test_identities"], "selection_source": plan["selection_source"]}
        from src.developer.local_workflow import _json_bytes
        plan["plan_id"] = "test-plan-" + hashlib.sha256(_json_bytes(plan_identity)).hexdigest()[:20]
        payload["run_id"] = self.workspace._record_run("test-applied-patch", scan_local_repository(self.repo), payload)
        mismatched = verify_execution(self.workspace, self.repo, self.applied["run_id"], payload["run_id"])
        self.assertNotEqual("verified", mismatched["status"])
        self.assertEqual(["tests.test_app.AppTests.test_value"], mismatched["missing_test_identities"])
        self.assertEqual(["tests.test_app.AppTests.test_skipped"], mismatched["unexpected_test_identities"])

        current = execute_applied_patch_tests(self.workspace, self.repo, self.applied["run_id"],
                                              tests=("tests.test_app.AppTests.test_value",))
        (self.repo / "unplanned.txt").write_text("drift\n", encoding="utf-8")
        stale = verify_execution(self.workspace, self.repo, self.applied["run_id"], current["run_id"])
        self.assertNotEqual("verified", stale["status"])
        self.assertIn("current_repository_is_stale_or_drifted_from_phase69_poststate", stale["deviations"])

    def test_phase71_rejects_cross_repository_and_tampered_execution_records(self):
        observation = self.run_tests("tests.test_app.AppTests.test_value")
        other = self.repo.parent / "other-repository"
        other.mkdir()
        subprocess.run(["git", "-C", str(other), "init", "--quiet"], check=True)
        (other / "other.py").write_text("VALUE = 1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(other), "add", "other.py"], check=True)
        subprocess.run(["git", "-C", str(other), "-c", "user.name=Test", "-c",
                        "user.email=test@example.invalid", "commit", "--quiet", "-m", "initial"], check=True)
        cross_repository = verify_execution(self.workspace, other, self.applied["run_id"], observation["run_id"])
        self.assertNotEqual("verified", cross_repository["status"])
        self.assertTrue(cross_repository["deviations"])
        path = self.workspace.root / "runs" / self.applied["run_id"] / "results.json"
        original = path.read_bytes()
        path.write_bytes(original.replace(b'"status": "applied"', b'"status": "failed "'))
        with self.assertRaisesRegex(LocalWorkflowError, "tampered"):
            verify_execution(self.workspace, self.repo, self.applied["run_id"], observation["run_id"])
        path.write_bytes(original)

    def test_phase71_blocks_required_uncertainty_and_tampered_patch_evidence(self):
        self._reapply_with_test_mode("git-refresh", uncertain=True)
        observation = self.run_tests("tests.test_app.AppTests.test_value")
        uncertain = verify_execution(self.workspace, self.repo, self.applied["run_id"], observation["run_id"])
        self.assertNotEqual("verified", uncertain["status"])
        self.assertIn("phase65_affected_test_selection_is_uncertain", uncertain["unresolved_uncertainty"])

        auth_entry = next(path for path in (self.workspace.root / "runs").iterdir()
                          if json.loads((path / "results.json").read_text()).get("mode")
                          == "developer-local-patch-authorization"
                          and json.loads((path / "results.json").read_text()).get("authorization_id")
                          == self.applied["authorization_id"])
        auth = json.loads((auth_entry / "results.json").read_text())
        patch_record = self.workspace.root / "runs" / auth["source_patch_run_id"] / "results.json"
        original = patch_record.read_bytes()
        patch_record.write_bytes(original.replace(b"return 2", b"return 9"))
        tampered = verify_execution(self.workspace, self.repo, self.applied["run_id"], observation["run_id"])
        self.assertNotEqual("verified", tampered["status"])
        self.assertIn("phase67_patch_evidence_missing_or_invalid", tampered["deviations"])
        patch_record.write_bytes(original)

    def test_failure_is_recorded_without_reverting_patch_or_committing(self):
        self._reapply_with_test_mode("fail")
        result = self.run_tests("tests.test_app.AppTests.test_value")
        self.assertEqual("failed", result["status"])
        self.assertEqual((1, 0, 1), (result["tests_run"], result["passed"], result["failures"]))
        self.assertIn(b"return 2", (self.repo / "app.py").read_bytes())
        self.assertEqual(self.head, self.git("rev-parse", "HEAD"))
        self.assertEqual(self.index, _git_index_state(self.repo))

    def test_error_and_skip_counts_are_structured(self):
        self._reapply_with_test_mode("error")
        errored = self.run_tests("tests.test_app.AppTests.test_error")
        self.assertEqual("error", errored["status"])
        self.assertEqual((1, 1), (errored["tests_run"], errored["errors"]))
        self._reapply_with_test_mode("skip")
        skipped = self.run_tests("tests.test_app.AppTests.test_skipped")
        self.assertEqual(("passed", 1, 0, 1), (skipped["status"], skipped["tests_run"], skipped["passed"], skipped["skipped"]))

    def test_unknown_identity_and_shell_fragment_are_rejected_without_execution(self):
        with self.assertRaisesRegex(LocalWorkflowError, "exact known"):
            self.run_tests("tests.test_app.AppTests.test_value;evil")
        with self.assertRaisesRegex(LocalWorkflowError, "exact known"):
            self.run_tests("C:\\Windows\\System32\\cmd.exe")

    def test_cli_does_not_accept_an_arbitrary_command_argument(self):
        from src.cli import _build_parser
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            _build_parser().parse_args(["local", "test-applied-patch", str(self.repo),
                                        "--execution-run-id", self.applied["run_id"],
                                        "--", "python", "-c", "print(1)"])

    def test_execution_from_another_repository_and_tampered_record_are_rejected(self):
        other = self.repo.parent / "other"
        other.mkdir()
        with self.assertRaisesRegex(LocalWorkflowError, "another repository"):
            execute_applied_patch_tests(self.workspace, other, self.applied["run_id"],
                                        tests=("tests.test_app.AppTests.test_value",))
        record = self.workspace.root / "runs" / self.applied["run_id"] / "results.json"
        original = record.read_bytes()
        record.write_bytes(original.replace(b'"status": "applied"', b'"status": "failed "'))
        with self.assertRaisesRegex(LocalWorkflowError, "tampered"):
            self.run_tests("tests.test_app.AppTests.test_value")
        record.write_bytes(original)

    def test_stale_state_blocks_execution(self):
        target = self.repo / "app.py"
        target.write_text(target.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "TEST NOT EXECUTED"):
            self.run_tests("tests.test_app.AppTests.test_value")

    def test_test_side_effect_is_reported_and_left_in_place(self):
        self._reapply_with_test_mode("side-effect")
        result = self.run_tests("tests.test_app.AppTests.test_side_effect")
        self.assertTrue(result["unexpected_repository_changes"])
        self.assertIn("side-effect.txt", result["unexpected_changed_paths"])
        self.assertTrue((self.repo / "side-effect.txt").is_file())

    def test_git_stat_refresh_is_not_reported_as_staging_side_effect(self):
        self._reapply_with_test_mode("git-refresh")
        result = self.run_tests("tests.test_app.AppTests.test_git_metadata_refresh")
        self.assertEqual("passed", result["status"])
        self.assertFalse(result["unexpected_repository_changes"])
        self.assertFalse(any("index" in value for value in result["unexpected_changed_paths"]))
        self.assertEqual(self.index, _git_index_state(self.repo))


if __name__ == "__main__":
    unittest.main()
