"""Phase 67 contract, validator, binding, and non-mutation coverage."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from src.cli import main
from src.developer.local_workflow import DeveloperWorkspace, LocalWorkflowError, scan_local_repository
from src.developer.patch_drafting import (PatchDraft, SuppliedPatchGenerator,
    _draft_patch_candidate as draft_patch, draft_patch as validated_draft_patch,
    validate_unified_diff)


class PatchDraftingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.repo = root / "repo"
        self.repo.mkdir()
        self.file = self.repo / "app.py"
        self.file.write_text("def run():\n    return 1\n\ndef reset_state():\n    return 0\n", encoding="utf-8")
        self.git("init", "--quiet")
        self.git("config", "user.name", "Phase 67")
        self.git("config", "user.email", "phase67@example.invalid")
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "baseline")
        self.workspace = DeveloperWorkspace(root / "workspace")
        self.inventory = scan_local_repository(self.repo)
        self.proposal = {
            "action_id": "proposal-test", "status": "proposed", "execution_allowed": False,
            "repository_path": str(self.repo.resolve()), "repository_id": self.inventory.repository_id,
            "base_reference": "HEAD", "base_commit": self.inventory.commit_sha,
            "current_commit": self.inventory.commit_sha, "working_tree_sha256": self.inventory.snapshot_id,
            "goal": "Change return value", "target_paths": ["app.py"], "target_symbols": ["run"],
            "evidence_refs": [{"file_path": "app.py", "symbol": "run", "evidence_types": ["changed_code"]}],
            "unresolved_evidence": [],
        }
        self.patch = "--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,2 @@\n def run():\n-    return 1\n+    return 2\n"

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def test_draft_identity_serialization_and_no_repository_mutation(self):
        before = {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file() and ".git" not in p.parts}
        head = self.git("rev-parse", "HEAD")
        status = self.git("status", "--porcelain=v1", "--untracked-files=all")
        index = (self.repo / ".git" / "index").read_bytes()
        branch = self.git("symbolic-ref", "--short", "HEAD")
        tags = self.git("tag", "--list")
        config = (self.repo / ".git" / "config").read_bytes()
        first = draft_patch(self.workspace, self.repo, self.proposal, SuppliedPatchGenerator(self.patch))
        second = draft_patch(self.workspace, self.repo, self.proposal, SuppliedPatchGenerator(self.patch))
        self.assertEqual(first["patch_id"], second["patch_id"])
        self.assertEqual(json.loads(json.dumps(first))["patch_text"], self.patch)
        self.assertEqual(first["status"], "draft")
        self.assertFalse(first["apply_allowed"])
        self.assertFalse(first["execution_allowed"])
        self.assertTrue(first["human_review_required"])
        self.assertEqual(first["source_action_id"], self.proposal["action_id"])
        self.assertEqual(first["evidence_refs"], self.proposal["evidence_refs"])
        after = {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(before, after)
        self.assertEqual(head, self.git("rev-parse", "HEAD"))
        self.assertEqual(status, self.git("status", "--porcelain=v1", "--untracked-files=all"))
        self.assertEqual(index, (self.repo / ".git" / "index").read_bytes())
        self.assertEqual(branch, self.git("symbolic-ref", "--short", "HEAD"))
        self.assertEqual(tags, self.git("tag", "--list"))
        self.assertEqual(config, (self.repo / ".git" / "config").read_bytes())
        self.assertEqual("developer-local-patch-draft", first["mode"])
        self.assertFalse(first["tests_executed"])
        self.assertEqual([{"file_path": "app.py", "qualified_symbol": "run"}], first["candidate_symbol_scope"])
        self.assertEqual(first["candidate_symbol_scope"], first["allowed_symbol_scope"])

    def test_sibling_symbol_expansion_is_blocked_before_draft_record(self):
        expanded = self.patch + "@@ -4,2 +4,2 @@\n def reset_state():\n-    return 0\n+    return 1\n"
        before_runs = set(path.name for path in (self.workspace.root / "runs").iterdir()) if (self.workspace.root / "runs").exists() else set()
        before_file = self.file.read_bytes()
        with self.assertRaisesRegex(LocalWorkflowError, "symbol scope"):
            draft_patch(self.workspace, self.repo, self.proposal, SuppliedPatchGenerator(expanded))
        after_runs = set(path.name for path in (self.workspace.root / "runs").iterdir()) if (self.workspace.root / "runs").exists() else set()
        self.assertEqual(before_runs, after_runs)
        self.assertEqual(before_file, self.file.read_bytes())

    def test_module_scope_requires_explicit_path_qualified_authorization(self):
        module_patch = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-import os\n+import sys\n"
        self.file.write_text("import os\n\ndef run():\n    return 1\n\ndef reset_state():\n    return 0\n", encoding="utf-8")
        self.git("add", "--all"); self.git("commit", "--quiet", "-m", "module fixture")
        self.inventory = scan_local_repository(self.repo)
        proposal = dict(self.proposal, current_commit=self.inventory.commit_sha,
                        base_commit=self.inventory.commit_sha,
                        working_tree_sha256=self.inventory.snapshot_id)
        with self.assertRaisesRegex(LocalWorkflowError, "symbol scope"):
            draft_patch(self.workspace, self.repo, proposal, SuppliedPatchGenerator(module_patch))

    def test_public_drafting_requires_a_validated_source_plan(self):
        before = self.file.read_bytes()
        with self.assertRaises(TypeError):
            validated_draft_patch(self.workspace, self.repo, self.proposal,
                                  SuppliedPatchGenerator(self.patch))
        with self.assertRaises(LocalWorkflowError):
            validated_draft_patch(self.workspace, self.repo, self.proposal,
                                  SuppliedPatchGenerator(self.patch), plan_run_id="0" * 20)
        self.assertEqual(before, self.file.read_bytes())

    def test_changed_patch_has_changed_identity(self):
        one = draft_patch(self.workspace, self.repo, self.proposal, SuppliedPatchGenerator(self.patch))
        changed = self.patch.replace("return 2", "return 3")
        two = draft_patch(self.workspace, self.repo, self.proposal, SuppliedPatchGenerator(changed))
        self.assertNotEqual(one["patch_id"], two["patch_id"])

    def test_scope_absolute_traversal_and_malformed_diff_fail_closed(self):
        candidates = [
            self.patch.replace("app.py", "other.py"),
            self.patch.replace("app.py", "../escape.py"),
            self.patch.replace("app.py", "app//other.py"),
            self.patch.replace("a/app.py", "a/C:/escape.py").replace("b/app.py", "b/C:/escape.py"),
            self.patch.replace("a/app.py", "a//etc/passwd").replace("b/app.py", "b//etc/passwd"),
            "not a diff",
            self.patch.replace("@@ -1,2 +1,2 @@", "@@ -1,8 +1,2 @@"),
        ]
        for candidate in candidates:
            with self.subTest(candidate=candidate[:40]), self.assertRaises(ValueError):
                validate_unified_diff(candidate, ("app.py",))
        valid_dash_content = self.patch.replace("-    return 1", "---- source line begins with dashes")
        self.assertEqual(("app.py",), validate_unified_diff(valid_dash_content, ("app.py",)))

    def test_stale_repository_state_and_mismatched_identity_rejected(self):
        self.file.write_text("def run():\n    return 9\n", encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "fingerprint"):
            draft_patch(self.workspace, self.repo, self.proposal, SuppliedPatchGenerator(self.patch))
        stale = dict(self.proposal, repository_id="other-repo")
        # Restore proposal snapshot is unnecessary: repository identity check precedes fingerprint.
        with self.assertRaisesRegex(LocalWorkflowError, "identity"):
            draft_patch(self.workspace, self.repo, stale, SuppliedPatchGenerator(self.patch))

    def test_proposal_identity_evidence_and_unresolved_uncertainty_are_preserved(self):
        proposal = dict(self.proposal, action_id="proposal-second",
                        unresolved_evidence=[{"type": "ambiguous", "action": "manual_review_required"}])
        result = draft_patch(self.workspace, self.repo, proposal, SuppliedPatchGenerator(self.patch))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["patch_text"], "")
        self.assertEqual(result["source_action_id"], "proposal-second")
        self.assertEqual(result["unresolved_evidence"], proposal["unresolved_evidence"])

    def test_genuinely_required_omitted_context_still_blocks_phase67(self):
        proposal = dict(self.proposal, action_id="proposal-omitted-context",
                        unresolved_evidence=[{
                            "type": "omitted_context", "classification": "blocking",
                            "evidence": {"file_path": "tests/test_app.py",
                                         "symbol_name": "AppTests.test_contract"},
                            "action": "Inspect omitted context because no independent evidence establishes it.",
                        }])
        result = draft_patch(self.workspace, self.repo, proposal, SuppliedPatchGenerator(self.patch))
        self.assertEqual("blocked", result["status"])
        self.assertEqual("", result["patch_text"])
        self.assertEqual("omitted_context", result["unresolved_evidence"][0]["type"])

    def test_informational_runtime_uncertainty_is_preserved_without_blocking(self):
        proposal = dict(self.proposal, unresolved_evidence=[{
            "type": "runtime_behavior_unverified", "action": "Confirm runtime dispatch during review"
        }])
        result = draft_patch(self.workspace, self.repo, proposal, SuppliedPatchGenerator(self.patch))
        self.assertEqual(result["status"], "draft")
        self.assertEqual(result["patch_text"], self.patch)
        self.assertEqual(result["unresolved_evidence"], proposal["unresolved_evidence"])

    def test_no_evidence_blocks_candidate_and_unsupported_language_is_rejected(self):
        proposal = dict(self.proposal, evidence_refs=[])
        result = draft_patch(self.workspace, self.repo, proposal, SuppliedPatchGenerator(self.patch))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["patch_text"], "")
        self.assertEqual(result["unresolved_evidence"][0]["type"], "insufficient_proposal_evidence")
        unsupported = dict(self.proposal, target_paths=["app.ts"])
        with self.assertRaisesRegex(LocalWorkflowError, "Unsupported or unsafe"):
            draft_patch(self.workspace, self.repo, unsupported, SuppliedPatchGenerator(self.patch))

    def test_cli_rejects_uncanonical_upstream_record_without_mutation(self):
        with self.assertRaises(LocalWorkflowError):
            self.workspace._contained(self.workspace.root / "runs" / ".." / ".." / "outside.json")
        runs = self.workspace.root / "runs" / "proposal-run"
        runs.mkdir(parents=True)
        (runs / "results.json").write_text(json.dumps({"proposed_action": self.proposal}), encoding="utf-8")
        external_patch = self.workspace.root / "candidate.diff"
        external_patch.write_text(self.patch, encoding="utf-8")
        before = self.file.read_bytes()
        args = ["local", "draft-patch", str(self.repo), "--proposal-run-id", "proposal-run",
                "--patch-file", str(external_patch), "--workspace", str(self.workspace.root)]
        error = StringIO()
        with redirect_stdout(StringIO()), redirect_stderr(error):
            self.assertNotEqual(0, main([*args, "--json"]))
        self.assertIn("Invalid Phase 71 plan run ID", error.getvalue())
        self.assertEqual(before, self.file.read_bytes())
        self.assertNotIn("candidate.diff", {p.name for p in self.repo.rglob("*")})

    def test_typed_contract_rejects_authority_or_identity_changes(self):
        result = draft_patch(self.workspace, self.repo, self.proposal, SuppliedPatchGenerator(self.patch))
        fields = {key: result[key] for key in PatchDraft.__dataclass_fields__}
        fields["candidate_paths"] = tuple(fields["candidate_paths"])
        for scope_name in ("allowed_symbol_scope", "candidate_symbol_scope"):
            fields[scope_name] = tuple((row["file_path"], row["qualified_symbol"]) for row in fields[scope_name])
        fields["execution_allowed"] = True
        with self.assertRaisesRegex(ValueError, "cannot execute"):
            PatchDraft(**fields)


if __name__ == "__main__":
    unittest.main()
