"""Focused Phase 69 mutation, verification, and recovery invariants."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch as mock_patch

from src.developer.local_workflow import DeveloperWorkspace, LocalWorkflowError, _git_index_state, scan_local_repository
from src.developer.patch_application import _apply_text, apply_approved_patch
from src.developer.patch_authorization import record_patch_decision
from src.developer.patch_drafting import SuppliedPatchGenerator, _draft_patch_candidate as draft_patch


class PatchApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        home = Path(self.temp.name)
        self.repo = home / "repo"
        self.repo.mkdir()
        self.a = self.repo / "a.py"
        self.b = self.repo / "b.py"
        self.a.write_bytes(b"def run():\n    return 1\n")
        self.b.write_bytes(b"VALUE = 1\n")
        self.git("init", "--quiet")
        self.git("config", "user.name", "Phase 69 Test")
        self.git("config", "user.email", "phase69@example.invalid")
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "baseline")
        self.workspace = DeveloperWorkspace(home / "external-workspace")
        inv = scan_local_repository(self.repo)
        self.proposal = {
            "action_id": "proposal-phase69-test", "status": "proposed", "execution_allowed": False,
            "repository_path": str(self.repo.resolve()), "repository_id": inv.repository_id,
            "base_reference": "HEAD", "base_commit": inv.commit_sha, "current_commit": inv.commit_sha,
            "working_tree_sha256": inv.snapshot_id, "goal": "Change exact values",
            "target_paths": ["a.py", "b.py"], "target_symbols": ["run"],
            "evidence_refs": [{"file_path": "a.py", "symbol": "run", "evidence_types": ["changed_code"]}],
            "unresolved_evidence": [],
        }
        self.patch_text = (
            "--- a/a.py\n+++ b/a.py\n@@ -1,2 +1,2 @@\n def run():\n-    return 1\n+    return 2\n"
            "--- a/b.py\n+++ b/b.py\n@@ -1 +1 @@\n-VALUE = 1\n+VALUE = 2\n"
        )

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True).stdout.decode().strip()

    def make_authorization(self, patch_text=None):
        draft = draft_patch(self.workspace, self.repo, self.proposal,
                            SuppliedPatchGenerator(patch_text or self.patch_text))
        decision = record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve")
        return draft, decision

    def snapshot(self):
        return (self.a.read_bytes(), self.b.read_bytes(), self.git("rev-parse", "HEAD"),
                _git_index_state(self.repo), self.git("status", "--porcelain=v1"))

    def execute(self, decision):
        return apply_approved_patch(self.workspace, self.repo, decision["run_id"])

    def test_exact_authorized_patch_applies_and_records_external_observation(self):
        _, decision = self.make_authorization()
        head, index = self.git("rev-parse", "HEAD"), _git_index_state(self.repo)
        result = self.execute(decision)
        self.assertEqual(b"def run():\n    return 2\n", self.a.read_bytes())
        self.assertEqual(b"VALUE = 2\n", self.b.read_bytes())
        self.assertEqual(["a.py", "b.py"], result["files_changed"])
        self.assertEqual(head, self.git("rev-parse", "HEAD"))
        self.assertEqual(index, _git_index_state(self.repo))
        self.assertFalse(result["tests_executed"])
        self.assertFalse(result["git_commit_created"])
        self.assertFalse(result["git_staging_performed"])
        self.assertTrue(result["semantic_index_unchanged"])
        self.assertTrue(result["refs_unchanged"])
        self.assertEqual(__import__("hashlib").sha256(_git_index_state(self.repo)).hexdigest(),
                         result["semantic_index_sha256"])
        self.assertTrue((self.workspace.root / "runs" / result["run_id"] / "results.json").is_file())
        self.assertFalse((self.repo / "runs").exists())

    def test_approved_allowed_scope_accepts_a_smaller_exact_patch(self):
        only_a = "--- a/a.py\n+++ b/a.py\n@@ -1,2 +1,2 @@\n def run():\n-    return 1\n+    return 2\n"
        draft, decision = self.make_authorization(only_a)
        self.assertEqual(["a.py", "b.py"], decision["target_paths"])
        self.assertEqual(["a.py"], draft["candidate_paths"])
        result = self.execute(decision)
        self.assertEqual(["a.py"], result["files_changed"])
        self.assertEqual(b"VALUE = 1\n", self.b.read_bytes())

    def test_index_refresh_metadata_does_not_change_semantic_entries(self):
        before = _git_index_state(self.repo)
        self.a.touch()
        self.git("update-index", "--refresh")
        self.assertEqual(before, _git_index_state(self.repo))

    def test_staged_content_changes_semantic_index_and_blocks_application(self):
        _, decision = self.make_authorization()
        before = _git_index_state(self.repo)
        self.a.write_bytes(b"def run():\n    return 9\n")
        self.git("add", "a.py")
        after = _git_index_state(self.repo)
        self.assertNotEqual(before, after)
        with self.assertRaises(LocalWorkflowError):
            self.execute(decision)
        self.assertEqual(after, _git_index_state(self.repo))

    def test_replay_is_rejected_without_source_change(self):
        _, decision = self.make_authorization()
        self.execute(decision)
        before = self.snapshot()
        with self.assertRaisesRegex(LocalWorkflowError, "already consumed"):
            self.execute(decision)
        self.assertEqual(before, self.snapshot())

    def test_rejected_authorization_cannot_apply(self):
        draft = draft_patch(self.workspace, self.repo, self.proposal, SuppliedPatchGenerator(self.patch_text))
        rejected = record_patch_decision(self.workspace, self.repo, draft["run_id"], "reject")
        before = self.snapshot()
        with self.assertRaises(LocalWorkflowError):
            self.execute(rejected)
        self.assertEqual(before, self.snapshot())

    def test_stale_repository_and_conflicting_context_fail_before_mutation(self):
        _, decision = self.make_authorization()
        self.a.write_bytes(b"def run():\n    return 9\n")
        before = self.snapshot()
        with self.assertRaises(LocalWorkflowError):
            self.execute(decision)
        self.assertEqual(before, self.snapshot())

    def test_wrong_patch_hash_or_tampered_authorization_fails_closed(self):
        _, decision = self.make_authorization()
        record_file = self.workspace.root / "runs" / decision["run_id"] / "results.json"
        original = record_file.read_bytes()
        record_file.write_bytes(original.replace(b"\"decision\": \"approve\"", b"\"decision\": \"reject\""))
        before = self.snapshot()
        with self.assertRaises(LocalWorkflowError):
            self.execute(decision)
        self.assertEqual(before, self.snapshot())

    def test_unauthorized_target_is_rejected_during_draft_validation(self):
        unauthorized = self.patch_text.replace("a/a.py", "a/other.py").replace("b/a.py", "b/other.py")
        with self.assertRaisesRegex(ValueError, "outside proposal scope"):
            draft_patch(self.workspace, self.repo, {**self.proposal, "target_paths": ["a.py"]},
                        SuppliedPatchGenerator(unauthorized))

    def test_post_write_byte_mismatch_restores_and_records_verified_failure(self):
        _, decision = self.make_authorization()
        before = self.snapshot()
        import src.developer.patch_application as app
        real_replace = app.os.replace
        corrupted = False

        def corrupt_after_first_replace(source, target):
            nonlocal corrupted
            result = real_replace(source, target)
            if ".aida-phase69-" in str(source) and not corrupted:
                corrupted = True
                Path(target).write_bytes(b"UNAPPROVED CONTENT\n")
            return result

        with mock_patch.object(app.os, "replace", side_effect=corrupt_after_first_replace):
            with self.assertRaisesRegex(LocalWorkflowError, "restored and verified"):
                self.execute(decision)
        self.assertEqual(before, self.snapshot())
        failures = []
        for entry in (self.workspace.root / "runs").iterdir():
            try:
                payload = __import__("json").loads((entry / "results.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if payload.get("authorization_id") == decision["authorization_id"]:
                failures.append(payload)
        self.assertTrue(any(row.get("status") == "failed" and row.get("restoration_verified") is True
                            for row in failures))

    def test_midway_write_failure_restores_all_target_bytes_and_git_state(self):
        _, decision = self.make_authorization()
        before = self.snapshot()
        import src.developer.patch_application as app
        real_replace = app.os.replace
        calls = 0

        def fail_second(source, target):
            nonlocal calls
            if ".aida-phase69-" in str(source) and "restore" not in str(source):
                calls += 1
                if calls == 2:
                    raise OSError("simulated second target failure")
            return real_replace(source, target)

        with mock_patch.object(app.os, "replace", side_effect=fail_second):
            with self.assertRaisesRegex(LocalWorkflowError, "restored and verified"):
                self.execute(decision)
        self.assertEqual(before, self.snapshot())

    def test_patch_interpreter_rejects_stale_context_without_fuzz(self):
        patch_text = "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-old\n+new\n"
        with self.assertRaisesRegex(LocalWorkflowError, "no fuzzy matching"):
            _apply_text(b"prefix\nold\n", patch_text)


if __name__ == "__main__":
    unittest.main()
