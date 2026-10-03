"""Focused Phase 64 change-aware developer assistance coverage."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from src.cli import main
from src.developer.change_impact import analyze_change_impact
from src.developer.local_workflow import DeveloperWorkspace, LocalWorkflowError


class _Tokenizer:
    def __call__(self, text, add_special_tokens=True, **kwargs):
        return {"input_ids": [1] * max(1, len(text.split()) + (2 if add_special_tokens else 0))}


class _Model:
    tokenizer = _Tokenizer()

    def encode(self, texts, **kwargs):
        vectors = np.ones((len(texts), 384), dtype=np.float32)
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


class ChangeImpactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.workspace_path = self.root / "workspace"
        self.repository.mkdir()
        (self.repository / "src").mkdir()
        (self.repository / "tests").mkdir()
        (self.repository / "src" / "helpers.py").write_text(
            "def support(value):\n    return value\n", encoding="utf-8"
        )
        (self.repository / "src" / "app.py").write_text(
            "from src.helpers import support\n\ndef run(value):\n    return support(value)\n",
            encoding="utf-8",
        )
        (self.repository / "tests" / "test_app.py").write_text(
            "from src.app import run\n\nimport unittest\n\nclass AppTests(unittest.TestCase):\n"
            "    def test_run(self):\n        self.assertEqual('x', run('x'))\n",
            encoding="utf-8",
        )
        (self.repository / "README.md").write_text("fixture\n", encoding="utf-8")
        self.git("init", "--quiet")
        self.git("config", "user.name", "Phase 64 Test")
        self.git("config", "user.email", "phase64@example.invalid")
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "baseline")
        self.baseline = self.git("rev-parse", "HEAD")
        self.developer = DeveloperWorkspace(self.workspace_path, (self.root / "research",))

    def git(self, *arguments):
        return subprocess.run(
            ["git", "-C", str(self.repository), *arguments], check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def analyze(self, **kwargs):
        with patch("src.developer.local_workflow.load_model", side_effect=RuntimeError("offline test")):
            return analyze_change_impact(self.developer, self.repository, **kwargs)

    def test_clean_staged_unstaged_untracked_deleted_and_base_changes(self):
        clean = self.analyze()
        self.assertEqual("clean", clean["repository"]["status"])
        self.assertEqual([], clean["changes"]["files"])

        app = self.repository / "src" / "app.py"
        app.write_text(app.read_text(encoding="utf-8").replace("support(value)", "support(value + '!')"), encoding="utf-8")
        self.git("add", "src/app.py")
        staged = self.analyze()
        self.assertIn("src/app.py", staged["changes"]["modified_files"])
        self.assertIn("run", {row["qualified_symbol"] for row in staged["symbols"]})
        self.assertTrue(any(row["relationship"] == "call_relationship" for row in staged["relationships"]))
        self.assertIn("tests.test_app", staged["tests"]["selectors"])
        self.assertFalse(staged["tests"]["executed"])

        (self.repository / "src" / "helpers.py").write_text("def support(value):\n    return str(value)\n", encoding="utf-8")
        (self.repository / "src" / "new_file.py").write_text("def added():\n    return True\n", encoding="utf-8")
        (self.repository / "tests" / "test_app.py").unlink()
        mixed = self.analyze()
        kinds = {row["path"]: row["change_type"] for row in mixed["changes"]["files"]}
        self.assertEqual("modified", kinds["src/helpers.py"])
        self.assertEqual("untracked", kinds["src/new_file.py"])
        self.assertEqual("deleted", kinds["tests/test_app.py"])
        self.assertIn("tests/test_app.py", mixed["changes"]["files_requiring_reindex"])

        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "change fixture")
        based = self.analyze(base=self.baseline)
        self.assertEqual("clean", based["repository"]["status"])
        self.assertEqual(self.baseline, based["repository"]["base_commit"])
        self.assertIn("src/app.py", {row["path"] for row in based["changes"]["files"]})

    def test_added_deleted_unsupported_configuration_and_ambiguity_are_explicit(self):
        (self.repository / "src" / "a.py").write_text("def ping():\n    return 'a'\n", encoding="utf-8")
        (self.repository / "src" / "b.py").write_text("def ping():\n    return 'b'\n", encoding="utf-8")
        (self.repository / "src" / "caller.py").write_text(
            "from src.a import ping\nfrom src.b import ping\n\ndef call():\n    return ping()\n", encoding="utf-8"
        )
        (self.repository / "settings.yaml").write_text("feature: true\n", encoding="utf-8")
        (self.repository / "web.ts").write_text("export const enabled = true;\n", encoding="utf-8")
        report = self.analyze()
        unsupported = {row["file_path"] for row in report["changes"]["unsupported_changed_files"]}
        self.assertEqual({"settings.yaml", "web.ts"}, unsupported)
        self.assertTrue(any(row["status"] == "ambiguous" for row in report["unresolved_relationships"]))
        self.assertFalse(any(row["file_path"].endswith(".ts") for row in report["symbols"]))
        self.assertTrue(report["tests"]["uncertain"])

    def test_index_freshness_blocks_stale_retrieval_and_current_retrieval_is_separate(self):
        with patch("src.developer.local_workflow.load_model", return_value=_Model()):
            self.developer.index(self.repository)
        current = self.analyze()
        self.assertEqual("current", current["index_freshness"]["status"])
        with patch("src.developer.local_workflow.load_model", side_effect=RuntimeError("offline test")), \
                patch.object(self.developer, "query", return_value={
            "question": "where is run", "results": [{
                "file_path": "src/app.py", "qualified_name": "run", "start_line": 3,
                "end_line": 4, "rank": 1, "ranking_reason": {"reason": "test"},
                "chunk_id": "run-id", "related_context": [{"file_path": "src/helpers.py",
                "symbol_name": "support", "reason": "call relationship"}],
            }], "context": {"relationship_diagnostics": []}, "run_id": "query-run",
        }):
            queried = analyze_change_impact(self.developer, self.repository, question="where is run")
        self.assertEqual("completed", queried["retrieval"]["status"])
        self.assertEqual("retrieved_query", queried["retrieval"]["query_evidence"][0]["evidence_type"])
        self.assertEqual("additional_related_context", queried["retrieval"]["additional_related_context"][0]["evidence_type"])

        app = self.repository / "src" / "app.py"
        app.write_text(app.read_text(encoding="utf-8") + "\ndef later():\n    return 1\n", encoding="utf-8")
        with patch.object(self.developer, "query") as query:
            stale = self.analyze(question="where is run")
        query.assert_not_called()
        self.assertEqual("stale", stale["index_freshness"]["status"])
        self.assertEqual("blocked", stale["retrieval"]["status"])
        self.assertIn("src/app.py", stale["index_freshness"]["stale_source_files"])

    def test_json_and_human_cli_outputs_are_actionable_and_planning_only(self):
        app = self.repository / "src" / "app.py"
        app.write_text(app.read_text(encoding="utf-8").replace("return support", "return support"), encoding="utf-8")
        for as_json in (False, True):
            output, error = StringIO(), StringIO()
            arguments = ["local", "change-impact", str(self.repository), "--workspace", str(self.workspace_path)]
            if as_json:
                arguments.append("--json")
            with patch("src.developer.local_workflow.load_model", side_effect=RuntimeError("offline test")), \
                    redirect_stdout(output), redirect_stderr(error):
                status = main(arguments)
            self.assertEqual(0, status, error.getvalue())
            if as_json:
                payload = json.loads(output.getvalue())
                self.assertEqual("developer-local-change-impact", payload["mode"])
                self.assertFalse(payload["tests"]["executed"])
            else:
                self.assertIn("Affected tests:", output.getvalue())
                self.assertIn("Recommended next actions:", output.getvalue())

    def test_external_workspace_and_protected_boundaries(self):
        before = {path.relative_to(self.repository).as_posix(): path.read_bytes()
                  for path in self.repository.rglob("*") if path.is_file() and ".git" not in path.parts}
        self.analyze()
        after = {path.relative_to(self.repository).as_posix(): path.read_bytes()
                 for path in self.repository.rglob("*") if path.is_file() and ".git" not in path.parts}
        self.assertEqual(before, after)
        self.assertTrue(self.workspace_path.is_dir())
        with self.assertRaises(LocalWorkflowError):
            analyze_change_impact(DeveloperWorkspace(self.repository / "workspace"), self.repository)
        source = Path("src/developer/change_impact.py").read_text(encoding="utf-8").casefold()
        self.assertNotIn("src.research", source)
        self.assertNotIn("humanize", source)


if __name__ == "__main__":
    unittest.main()
