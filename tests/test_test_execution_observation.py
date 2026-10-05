"""Focused Phase 70 target unittest execution and observation invariants."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from src.developer.local_workflow import (DeveloperWorkspace, LocalWorkflowError,
                                          _git_index_state, scan_local_repository)
from src.developer.patch_application import apply_approved_patch
from src.developer.patch_authorization import record_patch_decision
from src.developer.patch_drafting import SuppliedPatchGenerator, draft_patch
from src.developer.test_execution import execute_applied_patch_tests


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
        self.proposal = {
            "action_id": "proposal-phase70-test", "status": "proposed", "execution_allowed": False,
            "repository_path": str(self.repo.resolve()), "repository_id": inventory.repository_id,
            "base_reference": "HEAD", "base_commit": inventory.commit_sha, "current_commit": inventory.commit_sha,
            "working_tree_sha256": inventory.snapshot_id, "goal": "Change value function",
            "target_paths": ["app.py"], "target_symbols": ["value"],
            "evidence_refs": [{"file_path": "app.py", "symbol": "value", "evidence_types": ["changed_code"]}],
            "unresolved_evidence": [],
        }
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
        if mode in {"pass", "fail", "skip"}:
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

    def _reapply_with_test_mode(self, mode):
        # Rebuild the disposable repository state before creating a fresh Phase 69 chain.
        self.git("checkout", "--", "app.py")
        self._write_tests(mode)
        self.git("add", "tests/test_app.py")
        self.git("commit", "--quiet", "-m", f"fixture {mode}")
        self.head = self.git("rev-parse", "HEAD")
        self.index = _git_index_state(self.repo)
        self.workspace = DeveloperWorkspace(self.workspace.root.parent / f"workspace-{mode}")
        inventory = scan_local_repository(self.repo)
        self.proposal = {**self.proposal, "repository_id": inventory.repository_id,
                         "repository_path": str(self.repo.resolve()), "base_commit": inventory.commit_sha,
                         "current_commit": inventory.commit_sha, "working_tree_sha256": inventory.snapshot_id}
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
