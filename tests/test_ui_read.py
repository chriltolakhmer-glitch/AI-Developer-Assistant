from pathlib import Path
from unittest.mock import patch

from src.developer.local_workflow import DeveloperWorkspace, LocalWorkflowError
from src.developer.ui_read import read_repository
from tests.ui_fixture import GitFixture


class UIReadTests(GitFixture):
    def read(self, repository=None, workspace=None):
        return read_repository(DeveloperWorkspace(workspace or self.workspace_path), repository or self.repo)

    def test_clean_open_and_refresh_leave_every_file_index_head_refs_and_workspace_unchanged(self):
        before = self.snapshot()
        with patch.object(DeveloperWorkspace, "_prepare", side_effect=AssertionError("write path")), \
                patch.object(DeveloperWorkspace, "_record_run", side_effect=AssertionError("record")), \
                patch("src.developer.local_workflow.load_model", side_effect=AssertionError("model")):
            for _ in range(2):
                facts = self.read()
                self.assertEqual(self.git("rev-parse", "HEAD").decode().strip(), facts["head"])
                self.assertEqual("main", facts["branch"])
                self.assertFalse(facts["detached_head"])
                self.assertTrue(facts["clean"])
                self.assertFalse(facts["staged_changes"])
                self.assertFalse(facts["unstaged_changes"])
                self.assertFalse(facts["untracked_files"])
                self.assertEqual(["python"], facts["supported_languages"])
                self.assertEqual("missing", facts["index_freshness"]["status"])
                self.assertEqual(str(self.repo.resolve()), facts["repository_path"])
                self.assertEqual(str(self.workspace_path.resolve()), facts["workspace_path"])
                self.assertTrue(facts["repository_id"].startswith("local/"))
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.workspace_path.exists())

    def test_dirty_staged_unstaged_and_untracked_facts_preserve_bytes(self):
        (self.repo / "app.py").write_text("def run():\n    return 2\n", encoding="utf-8")
        self.git("add", "app.py")
        (self.repo / "app.py").write_text("def run():\n    return 3\n", encoding="utf-8")
        (self.repo / "new file.txt").write_text("untracked", encoding="utf-8")
        before = self.snapshot()
        facts = self.read()
        self.assertFalse(facts["clean"])
        self.assertTrue(facts["staged_changes"])
        self.assertTrue(facts["unstaged_changes"])
        self.assertTrue(facts["untracked_files"])
        self.assertEqual(before, self.snapshot())

    def test_detached_head_is_explicit(self):
        self.git("checkout", "--detach", "-q")
        before = self.snapshot()
        facts = self.read()
        self.assertIsNone(facts["branch"])
        self.assertTrue(facts["detached_head"])
        self.assertEqual(before, self.snapshot())

    def test_invalid_and_nested_repository_do_not_initialize_workspace(self):
        invalid = self.root / "invalid"
        invalid.mkdir()
        with self.assertRaises(LocalWorkflowError):
            self.read(invalid)
        nested = self.repo / "nested"
        nested.mkdir()
        with self.assertRaisesRegex(LocalWorkflowError, "root"):
            self.read(nested)
        self.assertFalse(self.workspace_path.exists())

    def test_missing_head_is_actionable(self):
        self.git("update-ref", "-d", "refs/heads/main")
        with self.assertRaises(LocalWorkflowError):
            self.read()
        self.assertFalse(self.workspace_path.exists())

    def test_existing_isolation_rules_remain_non_writing(self):
        with self.assertRaisesRegex(LocalWorkflowError, "overlaps"):
            self.read(workspace=self.repo / "workspace")
        with self.assertRaisesRegex(LocalWorkflowError, "outside"):
            self.read(workspace=Path(__file__).resolve().parents[1] / "workspace")
        workspace = DeveloperWorkspace(self.workspace_path, research_roots=(self.repo,))
        with self.assertRaisesRegex(LocalWorkflowError, "overlaps"):
            read_repository(workspace, self.repo)
        self.assertFalse(self.workspace_path.exists())

    def test_workspace_file_and_malformed_index_are_not_repaired(self):
        self.workspace_path.write_text("file", encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "not a directory"):
            self.read()
        self.workspace_path.unlink()
        facts = self.read()
        from src.developer.local_workflow import scan_local_repository
        workspace = DeveloperWorkspace(self.workspace_path)
        index_root = workspace._indexes(scan_local_repository(self.repo))
        index_root.mkdir(parents=True)
        (index_root / "active.json").write_text("broken", encoding="utf-8")
        before = self.snapshot()
        facts = self.read()
        self.assertEqual("unavailable", facts["index_freshness"]["status"])
        self.assertTrue(facts["index_freshness"]["reason"])
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.workspace_path / "runs").exists())

    def test_freshness_reuses_backend_result_without_claiming_a_new_index(self):
        with patch("src.developer.ui_read._index_freshness", return_value=({"status": "stale", "reason": "changed"}, None)):
            self.assertEqual({"status": "stale", "reason": "changed"}, self.read()["index_freshness"])

    def test_software_authority_is_explicitly_unknown_when_unavailable(self):
        with patch("src.developer.ui_read._software_identity", return_value=("0.1.1", "unknown")):
            facts = self.read()
        self.assertEqual("0.1.1", facts["aida_version"])
        self.assertEqual("unknown", facts["source_authority"])
