"""Phase 68 exact-patch decision and non-execution coverage."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from src.cli import main
from src.developer.local_workflow import DeveloperWorkspace, LocalWorkflowError, scan_local_repository
from src.developer.patch_authorization import (AuthorizationRecord, _read_patch_run,
                                               record_patch_decision, validate_exact_patch_authorization)
from src.developer.patch_drafting import SuppliedPatchGenerator, _draft_patch_candidate as draft_patch


class PatchAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.repo = root / "repo"
        self.repo.mkdir()
        self.file = self.repo / "app.py"
        self.file.write_text("def run():\n    return 1\n", encoding="utf-8")
        self.git("init", "--quiet")
        self.git("config", "user.name", "Phase 68 Test")
        self.git("config", "user.email", "phase68@example.invalid")
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "baseline")
        self.workspace = DeveloperWorkspace(root / "workspace")
        inventory = scan_local_repository(self.repo)
        self.proposal = {
            "action_id": "proposal-test", "status": "proposed", "execution_allowed": False,
            "repository_path": str(self.repo.resolve()), "repository_id": inventory.repository_id,
            "base_reference": "HEAD", "base_commit": inventory.commit_sha,
            "current_commit": inventory.commit_sha, "working_tree_sha256": inventory.snapshot_id,
            "goal": "Change return value", "target_paths": ["app.py"], "target_symbols": ["run"],
            "evidence_refs": [{"file_path": "app.py", "symbol": "run", "evidence_types": ["changed_code"]}],
            "unresolved_evidence": [],
        }
        self.patch = "--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,2 @@\n def run():\n-    return 1\n+    return 2\n"

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def draft(self, patch=None, proposal=None):
        return draft_patch(self.workspace, self.repo, proposal or self.proposal,
                           SuppliedPatchGenerator(patch or self.patch))

    def snapshot(self):
        return (self.file.read_bytes(), self.git("rev-parse", "HEAD"),
                self.git("status", "--porcelain=v1", "--untracked-files=all"),
                (self.repo / ".git" / "index").read_bytes())

    def test_approval_is_typed_bound_external_and_does_not_mutate_target(self):
        draft = self.draft()
        before = self.snapshot()
        result = record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve",
                                       approved_by="local-developer", note="Reviewed exact diff.")
        record = AuthorizationRecord.from_dict({key: result[key] for key in AuthorizationRecord.__dataclass_fields__})
        self.assertEqual("developer-local-patch-authorization", result["mode"])
        self.assertEqual("approve", record.decision)
        self.assertEqual("apply_exact_patch", record.allowed_operation)
        self.assertTrue(record.execution_authorized)
        self.assertFalse(record.executed)
        self.assertFalse(result["source_mutation_performed"])
        self.assertFalse(result["tests_executed"])
        self.assertEqual(draft["source_action_id"], record.source_action_id)
        self.assertEqual(draft["patch_id"], record.source_patch_id)
        self.assertEqual(draft["run_id"], record.source_patch_run_id)
        self.assertEqual(draft["repository_id"], record.repository_id)
        self.assertEqual(draft["current_commit"], record.current_commit)
        self.assertEqual(draft["working_tree_sha256"], record.working_tree_sha256)
        self.assertEqual(tuple(draft["target_paths"]), record.target_paths)
        self.assertEqual(hashlib.sha256(self.patch.encode()).hexdigest(), record.patch_sha256)
        self.assertEqual(before, self.snapshot())
        self.assertTrue((self.workspace.root / "runs" / result["run_id"] / "results.json").is_file())
        self.assertFalse(self.workspace.root.is_relative_to(self.repo))
        validate_exact_patch_authorization(record, _read_patch_run(self.workspace, draft["run_id"]), self.repo)

    def test_rejection_records_no_authority_and_can_reject_blocked_draft(self):
        blocked = self.draft(proposal={**self.proposal, "unresolved_evidence": [
            {"type": "ambiguous", "action": "manual_review_required"}]})
        self.assertEqual("blocked", blocked["status"])
        before = self.snapshot()
        result = record_patch_decision(self.workspace, self.repo, blocked["run_id"], "reject", note="Incorrect behavior")
        self.assertEqual("reject", result["decision"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual("none", result["allowed_operation"])
        self.assertFalse(result["executed"])
        self.assertEqual(before, self.snapshot())
        record = AuthorizationRecord.from_dict({key: result[key] for key in AuthorizationRecord.__dataclass_fields__})
        with self.assertRaisesRegex(LocalWorkflowError, "no execution authority"):
            validate_exact_patch_authorization(record, _read_patch_run(self.workspace, blocked["run_id"]), self.repo)

    def test_missing_unknown_decision_and_blocked_approval_fail(self):
        draft = self.draft()
        for value in (None, "", "maybe"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "explicit"):
                record_patch_decision(self.workspace, self.repo, draft["run_id"], value)
        blocked = self.draft(proposal={**self.proposal, "evidence_refs": []})
        with self.assertRaisesRegex(LocalWorkflowError, "Blocked PatchDraft"):
            record_patch_decision(self.workspace, self.repo, blocked["run_id"], "approve")

    def test_stale_worktree_and_commit_cannot_be_approved(self):
        draft = self.draft()
        self.file.write_text("def run():\n    return 9\n", encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "Repository state"):
            record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve")
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "drift")
        with self.assertRaisesRegex(LocalWorkflowError, "Repository state"):
            record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve")

    def test_modified_patch_run_and_metadata_are_rejected(self):
        draft = self.draft()
        path = self.workspace.root / "runs" / draft["run_id"] / "results.json"
        content = json.loads(path.read_text(encoding="utf-8"))
        content["patch_text"] = content["patch_text"].replace("return 2", "return 3")
        path.write_bytes((json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        with self.assertRaisesRegex(LocalWorkflowError, "modified"):
            record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve")

    def test_changed_patch_and_repository_invalidate_existing_authority(self):
        draft = self.draft()
        result = record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve")
        record = AuthorizationRecord.from_dict({key: result[key] for key in AuthorizationRecord.__dataclass_fields__})
        changed = self.draft(patch=self.patch.replace("return 2", "return 3"))
        with self.assertRaisesRegex(LocalWorkflowError, "exact PatchDraft"):
            validate_exact_patch_authorization(record, _read_patch_run(self.workspace, changed["run_id"]), self.repo)
        self.file.write_text("def run():\n    return 9\n", encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "Repository state"):
            validate_exact_patch_authorization(record, _read_patch_run(self.workspace, draft["run_id"]), self.repo)

    def test_modified_authorization_fields_fail_closed(self):
        draft = self.draft()
        result = record_patch_decision(self.workspace, self.repo, draft["run_id"], "approve")
        original = {key: result[key] for key in AuthorizationRecord.__dataclass_fields__}
        for key, changed in (("source_action_id", "proposal-other"), ("source_patch_id", "patch-other"),
                             ("source_patch_run_id", "0" * 20), ("patch_sha256", "0" * 64),
                             ("repository_id", "other"), ("working_tree_sha256", "0" * 64),
                             ("target_paths", ["other.py"]), ("decision", "reject")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                AuthorizationRecord.from_dict({**original, key: changed})
        with self.assertRaises(ValueError):
            AuthorizationRecord.from_dict({key: value for key, value in original.items() if key != "decision"})

    def test_cli_approval_rejection_json_and_human_output(self):
        draft = self.draft()
        args = ["local", "approve-patch", str(self.repo), "--patch-run-id", draft["run_id"],
                "--workspace", str(self.workspace.root)]
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(StringIO()):
            self.assertEqual(0, main([*args, "--json"]))
        payload = json.loads(output.getvalue())
        self.assertTrue(payload["execution_authorized"])
        self.assertFalse(payload["executed"])
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(StringIO()):
            self.assertEqual(0, main(args))
        self.assertIn("APPROVED FOR FUTURE PATCH APPLICATION", output.getvalue())
        self.assertIn("NOT APPLIED", output.getvalue())
        reject = ["local", "reject-patch", str(self.repo), "--patch-run-id", draft["run_id"],
                  "--workspace", str(self.workspace.root), "--note", "Needs work"]
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(StringIO()):
            self.assertEqual(0, main(reject))
        self.assertIn("PATCH REJECTED", output.getvalue())
        self.assertIn("NO EXECUTION AUTHORITY", output.getvalue())
        self.assertIn("Needs work", output.getvalue())


if __name__ == "__main__":
    unittest.main()
