"""Regression coverage for isolated personal developer workflows."""

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict
from io import StringIO
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

from src.cli import main
from src.developer import DEVELOPER_MODE_NOTICE, DeveloperWorkspace, LocalWorkflowError, local_demo
from src.developer import local_workflow
from src.models.embedding import Embedding


class FakeTokenizer:
    def __call__(self, text, add_special_tokens=True, **kwargs):
        return {"input_ids": [1] * max(1, len(text.split()) + (2 if add_special_tokens else 0))}


class DeveloperModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.cleanup_temporary_repository)
        self.root = Path(self.temp.name)
        self.repository = self.root / "sample-repository"
        self.repository.mkdir()
        self.git("init", "--quiet")
        self.git("config", "user.name", "Developer Mode Test")
        self.git("config", "user.email", "developer-test@example.invalid")
        self.source_path = self.repository / "src" / "session.py"
        self.source_path.parent.mkdir()
        self.source_path.write_text(
            "def load_session_token(headers):\n"
            "    return headers.get('session-token')\n\n"
            "def build_auth_header(token):\n"
            "    return {'Authorization': token}\n",
            encoding="utf-8",
        )
        (self.repository / "README.md").write_text("Local Python developer fixture.\n", encoding="utf-8")
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "create local fixture")
        self.workspace_path = self.root / "developer-workspace"
        self.research_root = self.root / "research-data"
        self.developer = DeveloperWorkspace(self.workspace_path, (self.research_root,))

    def cleanup_temporary_repository(self):
        # Windows can briefly retain Git-directory handles or pending entries.
        # Retry sharing/not-empty races; persistent and unrelated errors still fail.
        for attempt in range(11):
            try:
                self.temp.cleanup()
                return
            except OSError as error:
                if getattr(error, "winerror", None) not in {32, 145} or attempt == 10:
                    raise
                time.sleep(0.1)

    def git(self, *args):
        result = subprocess.run(
            ["git", "-C", str(self.repository), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    @staticmethod
    def _embedding_stub(chunks, _model_cache):
        rows = []
        for chunk in sorted(chunks, key=lambda item: item.chunk_id):
            metadata = asdict(chunk)
            metadata.pop("chunk_id")
            metadata.pop("content")
            from src.models.embedding import EmbeddingMetadata
            rows.append(Embedding(
                chunk.chunk_id,
                (1.0,) + (0.0,) * 383,
                EmbeddingMetadata(
                    **metadata,
                    content_sha256=local_workflow._digest(chunk.content.encode("utf-8")),
                    token_count=max(1, len(chunk.content.split())),
                ),
            ))
        return tuple(rows), ()

    def _copy_evaluation_repository(self):
        fixture_root = Path(__file__).parent / "fixtures" / "developer_eval"
        repository = self.root / "trust-repository"
        shutil.copytree(fixture_root / "sample_repository", repository)
        deleted = repository / "src" / "auth" / "deleted.py"
        deleted.write_text("def removed_auth_helper():\n    return 'removed'\n", encoding="utf-8")
        unsupported = repository / "unsupported"
        unsupported.mkdir()
        (unsupported / "app.ts").write_text("export function loginHandler() {}\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repository), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.name", "Trust Fixture"], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.email", "trust@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repository), "add", "--all"], check=True)
        subprocess.run(["git", "-C", str(repository), "commit", "--quiet", "-m", "trust fixture"], check=True)
        return repository

    def _copy_quality_repository(self):
        source = Path(__file__).parent / "fixtures" / "developer_eval" / "quality_repository"
        repository = self.root / "quality-repository"
        shutil.copytree(source, repository)
        subprocess.run(["git", "-C", str(repository), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.name", "Quality Fixture"], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.email", "quality@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repository), "add", "--all"], check=True)
        subprocess.run(["git", "-C", str(repository), "commit", "--quiet", "-m", "quality fixture"], check=True)
        return repository

    @staticmethod
    def _query_model():
        return type("FakeModel", (), {
            "tokenizer": FakeTokenizer(),
            "encode": lambda _self, texts, **kwargs: np.asarray(
                [[1.] + [0.] * 383 for _ in texts], dtype=np.float32
            ),
        })()

    def test_scan_accepts_local_repo_read_only_and_reports_unsupported_types(self):
        before = self.git("status", "--porcelain")
        result = self.developer.scan(self.repository)
        after = self.git("status", "--porcelain")

        self.assertEqual(before, after)
        self.assertEqual("developer-local", result["mode"])
        self.assertEqual(1, result["scan"]["eligible_python_file_count"])
        self.assertEqual({".md": 1}, result["scan"]["unsupported_extensions"])
        self.assertEqual(64, len(result["scan"]["working_tree_sha256"]))
        self.assertTrue((self.workspace_path / "runs" / result["run_id"] / "results.json").is_file())
        self.assertTrue(all((self.workspace_path / name).is_dir()
                    for name in ("indexes", "runs", "model-cache", "tmp")))
        self.assertFalse(self.research_root.exists())

    def test_invalid_path_and_unsupported_repository_have_actionable_errors(self):
        with self.assertRaisesRegex(LocalWorkflowError, "does not exist or cannot be resolved"):
            self.developer.scan(self.root / "missing")

        empty_repo = self.root / "docs-only"
        empty_repo.mkdir()
        subprocess.run(["git", "-C", str(empty_repo), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(empty_repo), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(empty_repo), "config", "user.email", "test@example.invalid"], check=True)
        (empty_repo / "index.html").write_text("<main>Unsupported</main>", encoding="utf-8")
        subprocess.run(["git", "-C", str(empty_repo), "add", "--all"], check=True)
        subprocess.run(["git", "-C", str(empty_repo), "commit", "--quiet", "-m", "docs"], check=True)
        scan = self.developer.scan(empty_repo)
        self.assertEqual(0, scan["scan"]["eligible_python_file_count"])
        self.assertEqual({".html": 1}, scan["scan"]["unsupported_extensions"])
        with self.assertRaisesRegex(LocalWorkflowError, "No Python chunks could be indexed"):
            self.developer.index(empty_repo)

    def test_workspace_rejects_research_and_repository_overlap(self):
        with self.assertRaisesRegex(LocalWorkflowError, "overlaps protected storage"):
            DeveloperWorkspace(self.research_root / "developer", (self.research_root,)).scan(self.repository)
        with self.assertRaisesRegex(LocalWorkflowError, "overlaps protected storage"):
            DeveloperWorkspace(self.repository / ".developer").scan(self.repository)
        with self.assertRaisesRegex(LocalWorkflowError, "outside the prototype checkout"):
            DeveloperWorkspace(Path(__file__).resolve().parents[1] / ".developer-workspace").scan(self.repository)

    def test_index_and_query_reuse_dense_bm25_and_are_repeatable(self):
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            indexed = self.developer.index(self.repository)
            repeated = self.developer.index(self.repository)

        self.assertEqual("indexed", indexed["index_status"])
        self.assertEqual("already indexed", repeated["index_status"])
        self.assertEqual(indexed["index_path"], repeated["index_path"])
        self.assertGreater(indexed["indexed_chunk_count"], 0)
        self.assertTrue((Path(indexed["index_path"]) / "manifest.json").is_file())
        self.assertFalse((self.research_root / "runs").exists())
        self.assertFalse((self.research_root / "indexes").exists())

        fake_model = type("FakeModel", (), {
            "tokenizer": FakeTokenizer(),
            "encode": lambda _self, _texts, **_kwargs: np.asarray([[1.0] + [0.0] * 383], dtype=np.float32),
        })()
        with patch("src.developer.local_workflow.load_model", return_value=fake_model):
            first = self.developer.query("Where is the session token loaded?", self.repository, top_k=3)
            second = self.developer.query("Where is the session token loaded?", self.repository, top_k=3)

        self.assertEqual(first["results"], second["results"])
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertTrue(first["results"])
        self.assertEqual("hybrid", first["results"][0]["strategy"])
        self.assertTrue(all(row["file_path"] == "src/session.py" for row in first["results"]))
        for command in ("index", "query"):
            run_dirs = list((self.workspace_path / "runs").glob("*"))
            self.assertTrue(any(json.loads((path / "metadata.json").read_text(encoding="utf-8"))["command"] == command
                                for path in run_dirs))

    def test_local_demo_is_generated_retrieval_not_benchmark(self):
        demo = local_demo()
        self.assertEqual(DEVELOPER_MODE_NOTICE, demo["notice"])
        self.assertEqual("developer-local-demo", demo["mode"])
        self.assertEqual("generated in-memory fixture", demo["source"])
        self.assertTrue(demo["results"])
        self.assertFalse(self.workspace_path.exists())

    def test_unchanged_index_does_not_parse_or_load_model(self):
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            first = self.developer.index(self.repository)
        with patch("src.developer.local_workflow._parse_inventory", side_effect=AssertionError("reparsed")), \
                patch("src.developer.local_workflow.load_model", side_effect=AssertionError("model loaded")):
            second = self.developer.index(self.repository)
        self.assertEqual(first["index_path"], second["index_path"])
        self.assertTrue(second["cache_reuse"])
        self.assertEqual(0, second["rebuilt_file_count"])
        self.assertEqual(first["indexed_chunk_count"], second["reused_chunk_count"])

    def test_incremental_index_only_embeds_changed_files_and_removes_deleted_files(self):
        other = self.repository / "src" / "database.py"
        other.write_text("def connect_database():\n    return 'connection'\n", encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            first = self.developer.index(self.repository)
        original = self._embedding_stub
        seen = []
        def embed(chunks, cache):
            seen.extend(c.file_path for c in chunks)
            return original(chunks, cache)
        other.write_text("def connect_database():\n    return 'new connection'\n", encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", side_effect=embed):
            second = self.developer.index(self.repository)
        self.assertEqual({"src/database.py"}, set(seen))
        self.assertEqual((1, 1), (second["reused_file_count"], second["rebuilt_file_count"]))
        self.assertGreater(second["reused_chunk_count"], 0)
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            cold = DeveloperWorkspace(self.root / "cold-workspace").index(self.repository)
        for filename in ("manifest.json", "documents.json", "vectors.npy", "state.json"):
            self.assertEqual((Path(second["index_path"]) / filename).read_bytes(),
                             (Path(cold["index_path"]) / filename).read_bytes())
        other.unlink()
        with patch("src.developer.local_workflow.load_model", side_effect=AssertionError("unneeded model")):
            deleted = self.developer.index(self.repository)
        rows = json.loads((Path(deleted["index_path"]) / "documents.json").read_text())
        self.assertTrue(all(r["metadata"]["file_path"] != "src/database.py" for r in rows))
        self.assertEqual(1, deleted["removed_file_count"])
        self.assertTrue(Path(first["index_path"]).exists())

    def test_inspect_changes_reports_added_modified_deleted_and_stale_symbols(self):
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        added = self.repository / "src" / "token_service.py"
        added.write_text("def issue_token():\n    return 'new'\n", encoding="utf-8")
        self.source_path.write_text("def authenticate_session(headers):\n    return headers.get('session-token')\n", encoding="utf-8")
        changes = self.developer.inspect(self.repository, changes=True)["changes"]
        self.assertEqual(["src/token_service.py"], changes["added_files"])
        self.assertEqual(["src/session.py"], changes["modified_files"])
        self.assertEqual(2, changes["reindexed_files"])
        self.assertIn("load_session_token", {chunk["qualified_name"] for chunk in json.loads(
            (next((self.workspace_path / "indexes").rglob("state.json"))).read_text(encoding="utf-8")
        )["chunks"]})
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            indexed = self.developer.index(self.repository)
        self.assertEqual(2, indexed["reindexed_file_count"])
        added.unlink()
        deleted = self.developer.index(self.repository)
        self.assertIn("src/token_service.py", deleted["changed_files"])
        self.assertGreaterEqual(deleted["removed_file_count"], 1)

    def test_commit_change_rebuilds_provenance_and_corruption_refuses_reuse(self):
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
            self.git("commit", "--allow-empty", "--quiet", "-m", "new commit")
            current = self.developer.index(self.repository)
        self.assertEqual(0, current["reused_file_count"])
        rows = json.loads((Path(current["index_path"]) / "documents.json").read_text())
        self.assertTrue(all(r["metadata"]["commit_sha"] == self.git("rev-parse", "HEAD") for r in rows))
        (Path(current["index_path"]) / "state.json").write_text("{}")
        with self.assertRaisesRegex(LocalWorkflowError, "integrity"):
            self.developer.index(self.repository)

    def test_inspect_reports_exclusions_rejections_and_parser_errors(self):
        (self.repository / "bad.py").write_text("def broken(:\n")
        (self.repository / "empty.py").write_text("")
        (self.repository / "large.py").write_text("def large():\n    return '" + "token " * 400 + "'\n")
        (self.repository / "vendor").mkdir()
        (self.repository / "vendor" / "ignored.py").write_text("x = 1\n")
        (self.repository / "routes.ts").write_text("export const route = 1;\n")
        model = type("Model", (), {"tokenizer": FakeTokenizer()})()
        with patch("src.developer.local_workflow.load_model", return_value=model):
            report = self.developer.inspect(self.repository)
        self.assertEqual("bad.py", report["parse_failures"][0]["file_path"])
        self.assertGreater(report["chunk_counts"]["over_limit"], 0)
        self.assertGreater(report["chunk_counts"]["empty"], 0)
        files = {f["file_path"]: f for f in report["files"]}
        self.assertFalse(files["vendor/ignored.py"]["included"])
        self.assertIn("unsupported", files["routes.ts"]["reason"])
        self.assertFalse(self.research_root.exists())

    def test_inspect_without_model_does_not_claim_token_eligibility(self):
        with patch("src.developer.local_workflow.load_model", side_effect=RuntimeError("missing cache")):
            report = self.developer.inspect(self.repository)
        self.assertIn("unknown", report["chunk_counts"])
        self.assertIn("unavailable", report["warning"])

    def test_developer_navigation_fixtures_return_expected_files_and_explanations(self):
        fixtures = {
            "config.py": "def load_configuration():\n    return 'configuration settings'\n",
            "routes.py": "def define_api_routes():\n    return 'api routes'\n",
            "auth.py": "def authenticate_user():\n    return 'authentication auth'\n",
            "database.py": "def create_database_connection():\n    return 'database connections'\n",
            "test_routes.py": "def test_api_routes():\n    return 'api routes'\n",
        }
        for name, source in fixtures.items():
            (self.repository / "src" / name).write_text(source)
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        model = type("Model", (), {
            "tokenizer": FakeTokenizer(),
            "encode": lambda _self, texts, **kwargs: np.asarray([[1.] + [0.] * 383 for _ in texts], dtype=np.float32),
        })()
        questions = [("Where is configuration loaded?", "config.py"),
                     ("Where are API routes defined?", "routes.py"),
                     ("Where is authentication implemented?", "auth.py"),
                     ("Where are database connections created?", "database.py")]
        with patch("src.developer.local_workflow.load_model", return_value=model):
            for question, expected in questions:
                with self.subTest(question=question):
                    payload = self.developer.query(question, self.repository, top_k=3)
                    self.assertIn("src/" + expected, [r["file_path"] for r in payload["results"]])
                    for row in payload["results"]:
                        self.assertIn(row["retrieval_source"], {"lexical", "vector", "hybrid"})
                        self.assertIn("formula", row["ranking_reason"])
                        self.assertIn("lexical_contribution", row["ranking_reason"])
                        self.assertIn("vector_contribution", row["ranking_reason"])
                        self.assertIn("developer_context", row)
                        self.assertTrue(row["contributions"])
            payload = self.developer.query("Where are API routes defined?", self.repository)
            paths = [r["file_path"] for r in payload["results"]]
            self.assertLess(paths.index("src/routes.py"), paths.index("src/test_routes.py"))
            self.assertTrue(payload["context"]["files"])
            self.assertTrue(payload["context"]["expansion_decisions"])

    def test_context_sidecar_tracks_symbols_imports_relationships_and_configuration(self):
        source = (
            "import os\n"
            "from handlers import handle_login\n\n"
            "API_PREFIX = '/api'\n\n"
            "class AuthService:\n"
            "    def login(self):\n"
            "        return handle_login(os.getenv('TOKEN'))\n"
        )
        path = self.repository / "src" / "auth.py"
        path.write_text(source, encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            result = self.developer.index(self.repository)
        state = json.loads((Path(result["index_path"]) / "state.json").read_text(encoding="utf-8"))
        contexts = state["context"]
        auth_chunks = [item for item in state["chunks"] if item["file_path"] == "src/auth.py"]
        self.assertTrue(auth_chunks)
        class_context = contexts[next(item["chunk_id"] for item in auth_chunks if item["entity_type"] == "class")]
        method_context = contexts[next(item["chunk_id"] for item in auth_chunks if item["entity_type"] == "method")]
        self.assertEqual("src.auth", class_context["module_name"])
        self.assertEqual("AuthService", class_context["symbol_name"])
        self.assertEqual("AuthService", method_context["parent_symbol"])
        self.assertIn("handlers.handle_login", method_context["imports"])
        self.assertIn("API_PREFIX", method_context["configuration_keys"])
        self.assertTrue(method_context["nearby_chunk_ids"])

    def test_cli_explain_is_developer_only_and_reports_context(self):
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        model = type("Model", (), {
            "tokenizer": FakeTokenizer(),
            "encode": lambda _self, texts, **kwargs: np.asarray([[1.] + [0.] * 383 for _ in texts], dtype=np.float32),
        })()
        output = StringIO()
        with patch("src.developer.local_workflow.load_model", return_value=model), redirect_stdout(output):
            status = main(("local", "explain", "find the session token", "--repository", str(self.repository),
                           "--workspace", str(self.workspace_path)))
        self.assertEqual(0, status)
        self.assertIn("Context files:", output.getvalue())
        self.assertIn("Excluded context:", output.getvalue())
        self.assertFalse(self.research_root.exists())

    def test_developer_evaluation_reports_metrics_and_case_diagnostics(self):
        fixture_root = Path(__file__).parent / "fixtures" / "developer_eval"
        evaluation_repo = self.root / "developer-evaluation-repository"
        shutil.copytree(fixture_root / "sample_repository", evaluation_repo)
        subprocess.run(["git", "-C", str(evaluation_repo), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(evaluation_repo), "config", "user.name", "Evaluation Test"], check=True)
        subprocess.run(["git", "-C", str(evaluation_repo), "config", "user.email", "evaluation@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(evaluation_repo), "add", "--all"], check=True)
        subprocess.run(["git", "-C", str(evaluation_repo), "commit", "--quiet", "-m", "evaluation fixture"], check=True)
        model = type("Model", (), {
            "tokenizer": FakeTokenizer(),
            "encode": lambda _self, texts, **kwargs: np.asarray([[1.] + [0.] * 383 for _ in texts], dtype=np.float32),
        })()
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub), \
                patch("src.developer.local_workflow.load_model", return_value=model):
            self.developer.index(evaluation_repo)
            report = self.developer.evaluate(
                evaluation_repo, fixture_root / "cases.json", top_k=10, explain=True
            )
            compared = self.developer.evaluate(
                evaluation_repo, fixture_root / "cases.json", top_k=10, explain=True, compare=True
            )
        self.assertEqual("developer-local-evaluation", report["mode"])
        self.assertEqual(3, report["queries"])
        self.assertEqual(3, report["file_hits"])
        self.assertGreaterEqual(report["symbol_hits"], 2)
        self.assertGreater(report["explanation_coverage"], 0)
        self.assertEqual(3, len(report["details"]))
        self.assertTrue(all(detail["results"] for detail in report["details"]))
        self.assertIsNotNone(compared["comparison"]["baseline"])
        self.assertEqual(3, len(compared["comparison"]["changed_cases"]))
        self.assertFalse(self.research_root.exists())

    def test_quality_fixtures_cover_workflows_and_context_assembly_reduces_noise(self):
        fixture_root = Path(__file__).parent / "fixtures" / "developer_eval"
        cases_path = fixture_root / "quality_cases.json"
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        self.assertEqual(7, len(cases))
        for case in cases:
            self.assertTrue(case["query"])
            self.assertIn("files", case["expected"])
            self.assertIn("symbols", case["expected"])
            self.assertIn("relationships", case["expected"])
            self.assertIn("allowed_extra_context", case)
            self.assertIn("required_relationships", case)
            self.assertIn("failure_tolerance", case)

        repository = self._copy_quality_repository()
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(repository)
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            report = self.developer.evaluate(repository, cases_path, top_k=50, explain=True)
            exact = self.developer.query("AuthService.login", repository, top_k=50)
            repeated = self.developer.query("AuthService.login", repository, top_k=50)
            dependency = self.developer.query(
                "Where does TokenManager.issue format a login token?", repository, top_k=50
            )
            analysis = self.developer.analyze_context(
                "Where are login tokens generated?", repository, 50, cases_path,
                "quality-authentication-flow",
            )
            traced = self.developer.trace("Where does the login API route call authentication?", repository, 50)
            diagnosed = self.developer.diagnose("quality-authentication-flow", cases_path, repository, 50)

        self.assertEqual(7, report["queries"])
        self.assertFalse([
            {"id": item["id"], "files": item["missing_files"], "symbols": item["missing_symbols"],
             "relationships": item["missing_relationships"]}
            for item in report["details"]
            if item["missing_files"] or item["missing_symbols"] or item["missing_relationships"]
        ])
        exact_first = exact["results"][0]
        self.assertEqual("AuthService.login", exact_first["qualified_name"])
        self.assertTrue(exact_first["ranking_reason"]["exact_symbol_match"])
        self.assertGreater(exact_first["ranking_reason"]["symbol_factor"], 1.0)
        self.assertEqual(exact["results"], repeated["results"])
        token_issue = next(row for row in dependency["results"] if row["qualified_name"] == "TokenManager.issue")
        self.assertIn("format_token", {item["symbol_name"] for item in token_issue["related_context"]})
        # A tied candidate may already be excluded by an overlapping module range;
        # suppression event counts are therefore not an invariant of this query.
        self.assertEqual(len(analysis["duplicate_context"]), analysis["duplicate_context_count"])
        signatures = [(row["qualified_name"], row["developer_context"]["content_sha256"])
                      for row in exact["results"]]
        self.assertEqual(len(signatures), len(set(signatures)))
        self.assertEqual([], analysis["missing_expected_evidence"]["files"])
        self.assertEqual([], analysis["missing_expected_evidence"]["symbols"])
        self.assertTrue(all(
            related["reason"] != "nearby source region"
            for row in exact["results"] for related in row["related_context"]
        ))
        self.assertEqual("developer-local-retrieval-trace", traced["mode"])
        self.assertEqual("developer-local-context-diagnosis", diagnosed["mode"])
        self.assertIn("missing_evidence", diagnosed)
        output = StringIO()
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()), redirect_stdout(output):
            status = main(("local", "analyze-context", "Where are login tokens generated?", "--repository",
                           str(repository), "--workspace", str(self.workspace_path), "--cases", str(cases_path),
                           "--case-id", "quality-authentication-flow", "--json"))
        self.assertEqual(0, status)
        self.assertEqual("developer-local-context-analysis", json.loads(output.getvalue())["mode"])
        self.assertFalse(self.research_root.exists())

    def test_compare_reports_prior_ranking_and_explanation_changes(self):
        repository = self._copy_quality_repository()
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(repository)
        question = "Where are login tokens generated?"
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            previous = self.developer.query(question, repository, top_k=8)
            from src.developer.ranking import rank_developer_results

            def changed_ranking(*args, **kwargs):
                rows = list(rank_developer_results(*args, **kwargs))
                rows.reverse()
                for rank, row in enumerate(rows, start=1):
                    row["rank"] = rank
                    row["ranking_reason"]["comparison_fixture"] = "changed explanation"
                return rows

            with patch("src.developer.ranking.rank_developer_results", side_effect=changed_ranking):
                compared = self.developer.compare(question, repository, top_k=8)
        comparison = compared["comparison"]
        self.assertEqual("compared", comparison["status"])
        self.assertEqual(previous["run_id"], comparison["previous_run_id"])
        self.assertTrue(comparison["ranking_changes"])
        self.assertTrue(comparison["explanation_changes"])
        self.assertIn("added_files", comparison)
        self.assertIn("removed_files", comparison)
        self.assertIn("quality score", comparison["note"])
        output = StringIO()
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()), redirect_stdout(output):
            status = main(("local", "compare", question, "--repository", str(repository),
                           "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        self.assertEqual("developer-local-retrieval-comparison", json.loads(output.getvalue())["mode"])
        self.assertFalse(self.research_root.exists())

    def test_trace_explains_every_result_and_preserves_ranking_reasons(self):
        repository = self._copy_evaluation_repository()
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(repository)
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            payload = self.developer.trace("Where is AuthService.login authentication handled?", repository)

        self.assertEqual("developer-local-retrieval-trace", payload["mode"])
        self.assertEqual(payload["question"], payload["trace"]["query"])
        self.assertTrue(payload["trace"]["selected_results"])
        for row in payload["results"]:
            self.assertTrue(row["explanation"]["match_reasons"])
            self.assertIn("ranking_factors", row["explanation"])
            self.assertIn("formula", row["ranking_reason"])
            self.assertTrue(row["ranking_reason"]["context_expansion_reason"])
        login = next(row for row in payload["trace"]["selected_results"] if row["symbol"] == "AuthService.login")
        self.assertIn("exact_symbol_match", login["evidence"])
        self.assertIn("symbol_exact_match", login["ranking_factors"])
        self.assertTrue(any(edge["kind"] == "import_relationship" and edge["to"].endswith("TokenManager")
                            for edge in login["relationship_path"]))
        self.assertIn(payload["confidence"]["level"], {"high", "medium", "low"})
        output = StringIO()
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()), redirect_stdout(output):
            status = main(("local", "trace", "Where is AuthService.login handled?", "--repository",
                           str(repository), "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        self.assertEqual("developer-local-retrieval-trace", json.loads(output.getvalue())["mode"])
        self.assertFalse(self.research_root.exists())

    def test_missing_context_diagnosis_covers_unsupported_stale_and_deleted_files(self):
        fixture_root = Path(__file__).parent / "fixtures" / "developer_eval"
        cases = fixture_root / "trust_cases.json"
        repository = self._copy_evaluation_repository()
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(repository)
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            ambiguous = self.developer.trace("Where are settings loaded?", repository)
            unsupported = self.developer.diagnose("trust-unsupported-language", cases, repository)
            missing = self.developer.diagnose("trust-missing-symbol", cases, repository)
            self.assertIn(ambiguous["confidence"]["level"], {"low", "medium"})
            self.assertNotIn("exact_symbol_match", ambiguous["confidence"]["signals"])
            self.assertEqual("current", unsupported["index_freshness"]["status"])
            self.assertTrue(any("unsupported language" in cause for cause in unsupported["likely_causes"]))
            self.assertTrue(missing["missing_evidence"])
            self.assertTrue(any("not found in supported indexed Python source" in cause
                                for cause in missing["likely_causes"]))
            output = StringIO()
            with redirect_stdout(output):
                status = main(("local", "diagnose", "trust-unsupported-language", "--cases", str(cases),
                               "--repository", str(repository), "--workspace", str(self.workspace_path), "--json"))
            self.assertEqual(0, status)
            self.assertEqual("developer-local-context-diagnosis", json.loads(output.getvalue())["mode"])

            service = repository / "src" / "auth" / "service.py"
            service.write_text(service.read_text(encoding="utf-8") + "\n# changed after index\n", encoding="utf-8")
            stale = self.developer.diagnose("trust-stale-index", cases, repository)
            self.assertEqual("stale", stale["index_freshness"]["status"])
            self.assertTrue(any("stale index" in cause for cause in stale["likely_causes"]))

            (repository / "src" / "auth" / "deleted.py").unlink()
            deleted = self.developer.diagnose("trust-deleted-file", cases, repository)
            self.assertEqual("stale", deleted["index_freshness"]["status"])
            self.assertTrue(any("deleted from current source" in cause for cause in deleted["likely_causes"]))
        self.assertFalse(self.research_root.exists())

    def test_stability_and_run_case_explanation_are_developer_only(self):
        cases = self.root / "cases.json"
        cases.write_text(json.dumps([{
            "id": "session", "query": "Where is the session token loaded?",
            "expected": {"files": ["src/session.py"], "symbols": ["load_session_token"]},
        }]), encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        model = type("Model", (), {
            "tokenizer": FakeTokenizer(),
            "encode": lambda _self, texts, **kwargs: np.asarray([[1.] + [0.] * 383 for _ in texts], dtype=np.float32),
        })()
        with patch("src.developer.local_workflow.load_model", return_value=model):
            report = self.developer.evaluate(self.repository, cases, explain=True, stability=True)
        self.assertEqual({"query_count": 1, "stable_results": 1, "changed_results": 0},
                         {key: report["stability"][key] for key in ("query_count", "stable_results", "changed_results")})
        self.assertEqual({"query_count": 1, "stable_results": 1, "changed_results": 0, "changed_cases": []},
                 report["stability"])
        explained = self.developer.explain_run(report["run_id"], "session")
        self.assertEqual(report["run_id"], explained["run_id"])
        self.assertEqual("session", explained["case"]["id"])
        self.assertIn("index_state", explained)
        self.assertFalse(self.research_root.exists())

    def test_cli_evaluate_json_is_developer_only(self):
        cases = self.root / "cases.json"
        cases.write_text(json.dumps([{
            "id": "session", "query": "Where is the session token loaded?",
            "expected": {"files": ["src/session.py"], "symbols": ["load_session_token"]},
        }]), encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        model = type("Model", (), {
            "tokenizer": FakeTokenizer(),
            "encode": lambda _self, texts, **kwargs: np.asarray([[1.] + [0.] * 383 for _ in texts], dtype=np.float32),
        })()
        output = StringIO()
        with patch("src.developer.local_workflow.load_model", return_value=model), redirect_stdout(output):
            status = main(("local", "evaluate", str(self.repository), "--cases", str(cases),
                           "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        report = json.loads(output.getvalue())
        self.assertEqual("developer-local-evaluation", report["mode"])
        self.assertFalse(self.research_root.exists())

    def test_cli_explain_case_reports_expected_and_failure_evidence(self):
        cases = self.root / "cases.json"
        cases.write_text(json.dumps([{
            "id": "session", "query": "Where is the session token loaded?",
            "expected": {"files": ["src/missing.py"], "symbols": ["missing_symbol"]},
        }]), encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        model = type("Model", (), {
            "tokenizer": FakeTokenizer(),
            "encode": lambda _self, texts, **kwargs: np.asarray([[1.] + [0.] * 383 for _ in texts], dtype=np.float32),
        })()
        output = StringIO()
        with patch("src.developer.local_workflow.load_model", return_value=model), redirect_stdout(output):
            status = main(("local", "explain", "session", "--cases", str(cases),
                           "--repository", str(self.repository), "--workspace", str(self.workspace_path)))
        self.assertEqual(0, status)
        self.assertIn("Expected:", output.getvalue())
        self.assertIn("Failures:", output.getvalue())
        self.assertIn("wrong_file", output.getvalue())

    def test_invalid_workspace_and_write_denial_are_actionable(self):
        blocked = self.root / "not-directory"
        blocked.write_text("file")
        with self.assertRaisesRegex(LocalWorkflowError, "not a directory"):
            DeveloperWorkspace(blocked).scan(self.repository)
        with patch("src.developer.local_workflow.tempfile.TemporaryFile", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(LocalWorkflowError, "permissions"):
                self.developer.scan(self.repository)

    def test_cli_inspect_json_is_parseable_without_research_runs(self):
        output = StringIO()
        with redirect_stdout(output), patch("src.developer.local_workflow.load_model", side_effect=RuntimeError("no cache")):
            status = main(("local", "inspect", str(self.repository), "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        payload = json.loads(output.getvalue())
        self.assertEqual("developer-local", payload["mode"])
        self.assertTrue(payload["files"])
        self.assertFalse(self.research_root.exists())

    def test_workspace_rejects_redirected_artifact_directory(self):
        original_resolve = Path.resolve
        redirected = self.developer.root / "indexes"
        def resolve(path, *args, **kwargs):
            if path == redirected:
                return self.research_root
            return original_resolve(path, *args, **kwargs)
        with patch.object(Path, "resolve", resolve):
            with self.assertRaisesRegex(LocalWorkflowError, "outside"):
                self.developer.scan(self.repository)
        self.assertFalse(self.research_root.exists())

    def test_source_edit_during_indexing_does_not_publish(self):
        def embed(chunks, cache):
            self.source_path.write_text("def changed():\n    return 5\n")
            return self._embedding_stub(chunks, cache)
        with patch("src.developer.local_workflow._embed_developer_chunks", side_effect=embed):
            with self.assertRaisesRegex(LocalWorkflowError, "changed during indexing"):
                self.developer.index(self.repository)
        self.assertFalse(list((self.workspace_path / "indexes").rglob("active.json")))

    def test_query_rejects_stale_source_and_unsupported_repository(self):
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        self.source_path.write_text("def changed():\n    return 5\n")
        with self.assertRaisesRegex(LocalWorkflowError, "changed after indexing"):
            self.developer.query("session", self.repository)
        self.source_path.unlink()
        with self.assertRaisesRegex(LocalWorkflowError, "cannot be queried"):
            self.developer.query("session", self.repository)

    def test_ranking_removes_overlaps_and_preserves_explicit_test_intent(self):
        from src.developer.ranking import rank_developer_results
        from src.models.embedding import EmbeddingMetadata
        from src.models.retrieval_result import SearchResult
        rows = []
        for rank, (path, kind, start, end) in enumerate([
            ("routes.py", "module", 1, 30), ("routes.py", "function", 2, 10),
            ("routes.py", "function", 12, 20), ("routes.py", "function", 22, 30),
            ("tests/test_routes.py", "function", 1, 10),
        ], 1):
            metadata = EmbeddingMetadata("local/fixture", "a" * 40, path, kind,
                                         "api_routes", start, end, "b" * 64, 10)
            rows.append(SearchResult(str(rank), rank, 1.0, metadata, "bm25"))
        result = rank_developer_results("tests for API routes", (), rows, 10)
        self.assertTrue(all(r["ranking_reason"]["test_factor"] == 1.0 for r in result))
        self.assertTrue(all(r["retrieval_source"] == "lexical" for r in result))
        routes = [r for r in result if r["file_path"] == "routes.py"]
        self.assertEqual(3, len(routes))  # Distinct methods are not hard-capped.
        for first in routes:
            for second in routes:
                if first is not second:
                    self.assertTrue(first["end_line"] < second["start_line"] or second["end_line"] < first["start_line"])

    def test_oversized_definition_is_reported_not_silently_truncated(self):
        oversized = self.repository / "src" / "oversized.py"
        oversized.write_text(
            "def oversized_function():\n    return '" + ("token " * 400) + "'\n",
            encoding="utf-8",
        )
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "add oversized local definition")
        with patch("src.developer.local_workflow.load_model") as model_loader:
            model_loader.return_value.tokenizer.side_effect = lambda text, **_kwargs: {
                "input_ids": [1] * (257 if "oversized_function" in text else 8)
            }
            model_loader.return_value.encode.side_effect = lambda texts, **_kwargs: np.asarray(
                [[1.0] + [0.0] * 383 for _ in texts], dtype=np.float32
            )
            result = self.developer.index(self.repository)
        self.assertGreaterEqual(result["rejected_chunk_count"], 1)
        self.assertIn("over_limit", result["rejections"])
        self.assertTrue(all("content" not in row for row in json.loads(
            (Path(result["index_path"]) / "documents.json").read_text(encoding="utf-8")
        )))

    def test_observability_capture_history_filter_timeline_and_compatibility(self):
        from src.developer.observability import inspect_history, timeline
        cases = self.root / "observation-cases.json"
        cases.write_text(json.dumps([{"id": "session", "query": "load_session_token",
            "expected": {"files": ["src/session.py"], "symbols": ["absent_symbol"]},
            "required_relationships": ["absent_relationship"]}]), encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            traced = self.developer.trace("load_session_token", self.repository)
            self.developer.regression(self.repository, cases, create_baseline=True)
            self.developer.regression(self.repository, cases)
            self.developer.diagnose("session", cases, self.repository)
        history = inspect_history(self.developer, "session", limit=1)
        self.assertEqual(3, history["matching_events"])
        self.assertEqual(1, len(history["events"]))
        kinds = {row["pattern"] for row in history["failure_patterns"]}
        self.assertIn("missing_symbol", kinds)
        self.assertIn("missing_relationship", kinds)
        self.assertFalse(inspect_history(self.developer, "unknown")["events"])
        event = next(row for row in inspect_history(self.developer)["events"] if row.get("command") == "query")
        self.assertEqual([row["qualified_name"] for row in traced["results"]],
                         [row["symbol"] for row in event["record"]["ranking"]["order"]])
        for key in ("timestamp", "index_version", "index_generation", "ranking_reasons",
                    "context_changes", "exclusions", "diagnostics"):
            self.assertIn(key, event)
        self.assertNotIn('"content":', json.dumps(event))
        repo = event["repository_id"]
        self.assertFalse(inspect_history(self.developer, repository_id="other")["events"])
        result = timeline(self.developer, repo, "Adjusted local case expectations after investigation.")
        self.assertTrue({"retrieval_state", "baseline_created", "regression", "fix_applied"}
                        <= {row["kind"] for row in result["entries"]})
        for command in (("inspect-history", "--query", "session"), ("timeline",)):
            with redirect_stdout(StringIO()) as output, patch("src.cli.RunTracker") as research:
                self.assertEqual(0, main(("local", *command, "--workspace", str(self.workspace_path), "--json")))
                self.assertEqual("developer-local-observability", json.loads(output.getvalue())["mode"])
                research.assert_not_called()

    def test_observability_patterns_require_repeated_evidence_and_repository_scope(self):
        from copy import deepcopy
        from src.developer.observability import failure_patterns
        # Use explicit descriptive regression records, independent of retrieval implementation.
        event = {"kind": "regression", "repository_id": "a", "query_id": "case-a", "event_id": "one",
                 "comparison": {"missing_evidence": {"symbols": ["missing"], "relationships": ["edge"],
                                                       "files": ["app.ts"]},
                                "changes": [{"kind": "unstable_ranking_changes"}]},
                 "record": {"retrieved": {"files": ["noise.py"], "symbols": []}, "context": {},
                            "expected": {"files": []}, "allowed_extra_context": []}}
        self.assertEqual([], failure_patterns([event]))
        second = deepcopy(event)
        second.update(event_id="two", query_id="case-b", repository_id="b")
        self.assertEqual([], failure_patterns([event, second]))
        second["repository_id"] = "a"
        patterns = failure_patterns([event, second])
        self.assertEqual({"missing_symbol", "missing_relationship", "unrelated_context",
                          "unstable_ranking", "unsupported_file_type"}, {row["pattern"] for row in patterns})
        self.assertTrue(all(row["cases"] == ["case-a", "case-b"] for row in patterns))

    def test_observability_changed_ranking_and_timeline_configuration(self):
        from src.developer.observability import inspect_history, timeline, _write
        from copy import deepcopy
        record = {"id": "x", "query": "x", "repository_fixture": "fixture", "expected": {},
                  "allowed_extra_context": [], "required_relationships": [], "failure_tolerance": {},
                  "retrieved": {"files": ["a.py"], "symbols": ["a", "b"]},
                  "ranking": {"order": ["a", "b"], "reasons": []}, "context": {}}
        event = {"kind": "retrieval", "query_id": "x", "repository_id": "fixture", "record": record,
                 "index_version": "v2", "index_generation": "one", "retrieval_version": "v2",
                 "configuration": {"top_k": 2}}
        first = _write(self.developer, event)
        event = deepcopy(event)
        event["record"]["ranking"]["order"].reverse()
        event["configuration"]["top_k"] = 3
        second = _write(self.developer, event)
        self.assertNotEqual(first["event_id"], second["event_id"])
        changes = inspect_history(self.developer)["behavior_changes"]
        self.assertEqual(1, len(changes))
        self.assertIsNotNone(changes[0]["ranking_differences"])
        self.assertEqual(2, len(timeline(self.developer)["entries"]))
        self.assertEqual([], inspect_history(self.developer)["failure_patterns"])

    def test_observability_rejects_unsafe_storage_invalid_limit_and_malformed_history(self):
        from src.developer.observability import inspect_history, timeline, _write
        with self.assertRaises(LocalWorkflowError):
            inspect_history(DeveloperWorkspace(Path(__file__).resolve().parents[1] / "observability"))
        with self.assertRaises(LocalWorkflowError):
            inspect_history(self.developer, limit=0)
        with self.assertRaises(LocalWorkflowError):
            timeline(self.developer, note="fix")
        directory = self.workspace_path / "observability" / "events"
        directory.mkdir(parents=True)
        (directory / "bad.json").write_text("not json", encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "Cannot read developer history"):
            inspect_history(self.developer)
        (directory / "bad.json").unlink()
        directory.rmdir()
        outside = self.root / "outside-events"
        outside.mkdir()
        if __import__("os").name == "nt":
            subprocess.run(["cmd", "/c", "mklink", "/J", str(directory), str(outside)],
                           check=True, capture_output=True)
        else:
            directory.symlink_to(outside, target_is_directory=True)
        try:
            with self.assertRaises(LocalWorkflowError):
                _write(self.developer, {"kind": "fix_applied"})
            (outside / "outside.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(LocalWorkflowError):
                inspect_history(self.developer)
        finally:
            if __import__("os").name == "nt":
                directory.rmdir()
            else:
                directory.unlink()

    def _optimization_setup(self, identifier="session-fix", retrieval_settings=None):
        from src.developer.optimization import create_candidate
        cases = self.root / "optimization-cases.json"
        cases.write_text(json.dumps([{"id": "session", "query": "load_session_token",
            "expected": {"files": ["src/session.py"], "symbols": ["load_session_token"]}}]), encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            baseline = self.developer.regression(self.repository, cases, create_baseline=True)
        candidate = create_candidate(self.developer, identifier, "Review repeated context", ["session"],
            [baseline["history_id"] + ":session"], "Inspect expansion limits", "Run all baseline cases and compatibility gates",
            retrieval_settings=retrieval_settings)
        return cases, baseline, candidate

    def _register_passed_lifecycle_validation(self, candidate):
        from src.developer.governance import register_candidate, transition_candidate
        from src.developer.optimization import _write, _storage

        register_candidate(self.developer, candidate["id"], "developer", "review validated candidate",
                           candidate["cases"])
        transition_candidate(self.developer, candidate["id"], "experimenting", "begin reviewed experiment")
        validation = _write(self.developer, _storage(self.developer, candidate["id"]) / "validations" / "review-test.json", {
            "id": "review-test", "candidate_id": candidate["id"], "before": "default", "after": "review-history",
            "gates": {name: True for name in ("regression_cases", "stability", "ranking_review",
                                               "duplicate_context", "trace_compatibility", "diagnose_compatibility")},
            "passed": True, "ranking_notes": {}, "compatibility": [], "comparison": {"comparisons": []},
            "status": "validated"})
        transition_candidate(self.developer, candidate["id"], "validated", "validation evidence passed",
                             last_validation_at=validation["recorded_at"])
        return validation

    def test_optimization_candidate_evidence_and_creation_validation(self):
        from src.developer.optimization import create_candidate, show_candidates
        _, _, candidate = self._optimization_setup()
        shown = show_candidates(self.developer)["candidates"][0]
        self.assertEqual("candidate", shown["status"])
        self.assertEqual(candidate["source"], [event["event_id"] for event in shown["evidence"]])
        self.assertIsNone(shown["result"])
        for identifier, cases, source in (("../escape", ["session"], candidate["source"]),
                                          ("missing", ["unknown"], candidate["source"]),
                                          ("bad-source", ["session"], ["research-event"])):
            with self.assertRaises(LocalWorkflowError):
                create_candidate(self.developer, identifier, "gap", cases, source, "change", "check")
        with self.assertRaisesRegex(LocalWorkflowError, "already exists"):
            create_candidate(self.developer, candidate["id"], "gap", candidate["cases"], candidate["source"], "change", "check")
        self.assertFalse(self.research_root.exists())

    def test_optimization_workflow_validation_acceptance_and_cli(self):
        from src.developer.optimization import validate_candidate, decide_candidate, show_candidates
        cases, baseline, candidate = self._optimization_setup()
        baseline_bytes = Path(baseline["baseline_path"]).read_bytes()
        with self.assertRaisesRegex(LocalWorkflowError, "every gate"):
            decide_candidate(self.developer, candidate["id"], "accepted", "too soon")
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()), \
                patch("src.cli.RunTracker") as research:
            with redirect_stdout(StringIO()) as output:
                status = main(("local", "optimize", "validate", "--id", candidate["id"],
                    "--repository", str(self.repository), "--cases", str(cases), "--before", "default",
                    "--workspace", str(self.workspace_path), "--json"))
            self.assertEqual(0, status)
            result = json.loads(output.getvalue())
            self.assertTrue(result["passed"], result)
            self.assertEqual(6, len(result["gates"]))
            research.assert_not_called()
        decision = decide_candidate(self.developer, candidate["id"], "accepted", "No-op compatibility control passed")
        self.assertEqual(result["id"], decision["validation_id"])
        self.assertEqual("accepted", show_candidates(self.developer, candidate["id"])["candidates"][0]["status"])
        with self.assertRaisesRegex(LocalWorkflowError, "already decided"):
            validate_candidate(self.developer, candidate["id"], self.repository, cases, "default")
        with self.assertRaisesRegex(LocalWorkflowError, "already exists"):
            decide_candidate(self.developer, candidate["id"], "rejected", "cannot rewrite")
        self.assertEqual(baseline_bytes, Path(baseline["baseline_path"]).read_bytes())
        for command in (("optimize",), ("optimize", "show", "--id", candidate["id"]),
                        ("compare", "--before", "default", "--after", result["after"])):
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(0, main(("local", *command, "--workspace", str(self.workspace_path), "--json")))
            self.assertEqual("developer-local-optimization", json.loads(output.getvalue())["mode"])

    def test_optimization_rejection_and_failed_compatibility(self):
        from src.developer.optimization import validate_candidate, decide_candidate, show_candidates
        cases, _, candidate = self._optimization_setup()
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()), \
                patch.object(self.developer, "trace", return_value={}), \
                patch.object(self.developer, "diagnose", return_value={}):
            result = validate_candidate(self.developer, candidate["id"], self.repository, cases, "default")
        self.assertFalse(result["passed"])
        self.assertFalse(result["gates"]["trace_compatibility"])
        with self.assertRaises(LocalWorkflowError):
            decide_candidate(self.developer, candidate["id"], "accepted", "invalid")
        decide_candidate(self.developer, candidate["id"], "rejected", "Trace contract failed")
        self.assertEqual("rejected", show_candidates(self.developer)["candidates"][0]["status"])

    def test_optimization_version_comparison_regression_and_improvement(self):
        from copy import deepcopy
        from src.developer.optimization import compare_versions
        _, baseline, candidate = self._optimization_setup()
        document = json.loads(Path(baseline["baseline_path"]).read_text(encoding="utf-8"))
        changed = deepcopy(document)
        record = changed["records"][0]
        record["retrieved"]["symbols"] = []
        record["ranking"]["reasons"][0]["explanation"] = {}
        record["context"]["expanded_symbols"] = [
            {"file_path": "extra.py", "symbol_name": "extra"},
            {"file_path": "extra.py", "symbol_name": "extra"}]
        changed_path = Path(baseline["baseline_path"]).with_name("changed.json")
        changed_path.write_text(json.dumps(changed), encoding="utf-8")
        difference = compare_versions(self.developer, "default", "changed")["comparisons"][0]
        self.assertEqual("regression", difference["classification"])
        self.assertTrue({"expected_evidence_lost", "explanations_removed", "duplicate_context_increased"}
                        <= set(difference["regressions"]))
        self.assertEqual(["load_session_token"], difference["expected_lost"]["symbols"])
        improved = compare_versions(self.developer, "changed", "default")["comparisons"][0]
        self.assertEqual("improved", improved["classification"])
        self.assertIn("expected_evidence_gained", improved["improvements"])
        self.assertIn("duplicate_context_reduced", improved["improvements"])
        changed["records"][0]["query"] = "changed case"
        changed_path.write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "Case definition changed"):
            compare_versions(self.developer, "default", "changed")
        with self.assertRaises(LocalWorkflowError):
            compare_versions(self.developer, "../escape", "default", candidate["repository_id"])

    def test_optimization_stability_gate_blocks_acceptance(self):
        from copy import deepcopy
        from src.developer.optimization import validate_candidate, decide_candidate
        cases, _, candidate = self._optimization_setup()
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            payload = self.developer.query("load_session_token", self.repository)
            changed = deepcopy(payload)
            changed["results"] = []
            with patch.object(self.developer, "query", side_effect=[payload, changed, payload]):
                result = validate_candidate(self.developer, candidate["id"], self.repository, cases, "default")
        self.assertFalse(result["gates"]["stability"])
        self.assertIn("unstable_ranking", result["comparison"]["comparisons"][0]["regressions"])
        with self.assertRaises(LocalWorkflowError):
            decide_candidate(self.developer, candidate["id"], "accepted", "unstable")

    def test_optimization_ranking_review_and_latest_validation(self):
        from src.developer.optimization import validate_candidate, decide_candidate
        cases, baseline, candidate = self._optimization_setup()
        # Alter only the saved test baseline's explanation to model a previous version.
        document = json.loads(Path(baseline["baseline_path"]).read_text(encoding="utf-8"))
        document["records"][0]["ranking"]["reasons"][0]["reason"]["symbol_relevance"] = "previous reason"
        alternate = Path(baseline["baseline_path"]).with_name("previous.json")
        alternate.write_text(json.dumps(document), encoding="utf-8")
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            failed = validate_candidate(self.developer, candidate["id"], self.repository, cases, "previous")
            self.assertFalse(failed["gates"]["ranking_review"])
            passed = validate_candidate(self.developer, candidate["id"], self.repository, cases, "previous",
                {"session": "Restored structured symbol relevance explanation"})
            self.assertTrue(passed["passed"], passed)
            latest = validate_candidate(self.developer, candidate["id"], self.repository, cases, "previous")
        self.assertFalse(latest["passed"])
        with self.assertRaises(LocalWorkflowError):
            decide_candidate(self.developer, candidate["id"], "accepted", "Older validation passed")

    def test_optimization_storage_isolation_and_cli_errors(self):
        from src.developer.optimization import show_candidates
        with self.assertRaises(LocalWorkflowError):
            show_candidates(DeveloperWorkspace(Path(__file__).resolve().parents[1] / "optimization"))
        with self.assertRaises(LocalWorkflowError):
            show_candidates(DeveloperWorkspace(self.research_root, (self.research_root,)))
        for command in (("optimize", "create"), ("optimize", "validate", "--id", "x"),
                        ("compare", "--before", "default"), ("compare",)):
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertNotEqual(0, main(("local", *command, "--workspace", str(self.workspace_path))))

    def test_optimization_redirected_storage_and_malformed_candidate(self):
        from src.developer.optimization import show_candidates
        outside = self.root / "outside-optimization"
        outside.mkdir()
        self.developer._prepare()
        redirect = self.workspace_path / "optimization"
        if __import__("os").name == "nt":
            subprocess.run(["cmd", "/c", "mklink", "/J", str(redirect), str(outside)],
                           check=True, capture_output=True)
        else:
            redirect.symlink_to(outside, target_is_directory=True)
        try:
            with self.assertRaisesRegex(LocalWorkflowError, "outside"):
                show_candidates(self.developer)
            self.assertEqual([], list(outside.iterdir()))
        finally:
            if __import__("os").name == "nt":
                redirect.rmdir()
            else:
                redirect.unlink()
        path = self.workspace_path / "optimization/candidates/bad/candidate.json"
        path.parent.mkdir(parents=True)
        path.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "JSON object"):
            show_candidates(self.developer)

    def test_safety_decision_records_capture_accountability_and_rollback(self):
        from src.developer.optimization import validate_candidate, decide_candidate
        from src.developer.safety import record_rollback, show_rollback
        cases, baseline, candidate = self._optimization_setup()
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            result = validate_candidate(self.developer, candidate["id"], self.repository, cases, "default")
        self.assertTrue(result["passed"], result)
        decision = decide_candidate(self.developer, candidate["id"], "accepted", "Reviewed evidence and gates")
        self.assertEqual(candidate["source"], decision["evidence"])
        self.assertEqual(result["id"], decision["validation_id"])
        self.assertEqual("default", decision["rollback"]["restore_to"])
        self.assertIn("regressions", decision["validation"])
        self.assertTrue(decision["validation"]["stability_passed"])
        before = show_rollback(self.developer, candidate["id"])["candidates"][0]
        self.assertTrue(before["rollback_available"])
        self.assertEqual([], before["rollback_records"])
        self.assertTrue(any(item["version"] == "default" for item in before["previous_states"]))
        recorded = record_rollback(self.developer, candidate["id"], "Restore original ranking behavior")
        self.assertEqual("default", recorded["target_version"])
        self.assertEqual("developer-local-rollback", recorded["mode"])
        after = show_rollback(self.developer, candidate["id"])["candidates"][0]
        self.assertEqual(1, len(after["rollback_records"]))
        with self.assertRaisesRegex(LocalWorkflowError, "nonempty"):
            record_rollback(self.developer, candidate["id"], "  ")
        self.assertFalse(self.research_root.exists())

    def test_governance_lifecycle_transitions_and_invalid_rejection(self):
        from src.developer.governance import register_candidate, transition_candidate, show_lifecycle
        _, _, candidate = self._optimization_setup()
        with self.assertRaisesRegex(LocalWorkflowError, "nonempty owner"):
            register_candidate(self.developer, candidate["id"], "", "purpose", ["session"])
        with self.assertRaisesRegex(LocalWorkflowError, "subset"):
            register_candidate(self.developer, candidate["id"], "dev", "purpose", ["unknown-case"])
        registered = register_candidate(self.developer, candidate["id"], "developer",
                                        "reduce missing dependency context", ["session"])
        self.assertEqual("proposed", registered["state"])
        with self.assertRaisesRegex(LocalWorkflowError, "already has a recorded lifecycle"):
            register_candidate(self.developer, candidate["id"], "developer", "reduce missing dependency context", ["session"])
        with self.assertRaisesRegex(LocalWorkflowError, "Invalid lifecycle transition"):
            transition_candidate(self.developer, candidate["id"], "accepted", "skip ahead")
        transition_candidate(self.developer, candidate["id"], "experimenting", "started experimenting")
        transition_candidate(self.developer, candidate["id"], "validated", "gates passed",
                             last_validation_at="2026-09-29T00:00:00+00:00")
        transition_candidate(self.developer, candidate["id"], "accepted", "decision recorded")
        with self.assertRaisesRegex(LocalWorkflowError, "Invalid lifecycle transition"):
            transition_candidate(self.developer, candidate["id"], "experimenting", "cannot go back")
        summary = show_lifecycle(self.developer, candidate["id"])["candidates"][0]
        self.assertEqual("accepted", summary["state"])
        self.assertEqual(4, len(summary["history"]))
        self.assertEqual("2026-09-29T00:00:00+00:00", summary["last_validation_at"])
        lifecycle_dir = self.workspace_path / "optimization" / "candidates" / candidate["id"] / "lifecycle"
        self.assertEqual(4, len(list(lifecycle_dir.glob("*.json"))))
        self.assertFalse(self.research_root.exists())

    def test_governance_every_declared_transition_succeeds(self):
        from datetime import datetime, timezone
        from src.developer.governance import TRANSITIONS, register_candidate, transition_candidate
        from src.developer.optimization import create_candidate
        _, _, seed = self._optimization_setup("transition-seed")
        paths_to_state = {
            "proposed": [],
            "experimenting": ["experimenting"],
            "validated": ["experimenting", "validated"],
            "accepted": ["experimenting", "validated", "accepted"],
            "rejected": ["experimenting", "rejected"],
            "rolled_back": ["experimenting", "validated", "accepted", "rolled_back"],
        }
        edge_number = 0
        for start, targets in TRANSITIONS.items():
            for target in sorted(targets):
                identifier = f"edge-{edge_number}"
                edge_number += 1
                create_candidate(self.developer, identifier, "Transition coverage", seed["cases"],
                                 seed["source"], "Transition coverage proposal", "State-only validation")
                register_candidate(self.developer, identifier, "developer", "transition coverage", seed["cases"])
                for state in paths_to_state[start]:
                    timestamp = (datetime.now(timezone.utc).isoformat() if state == "validated" else None)
                    transition_candidate(self.developer, identifier, state, f"move to {state}", timestamp)
                timestamp = datetime.now(timezone.utc).isoformat() if target == "validated" else None
                event = transition_candidate(self.developer, identifier, target, f"move to {target}", timestamp)
                self.assertEqual(target, event["state"], f"{start} -> {target}")
                self.assertEqual(start, event["previous_state"], f"{start} -> {target}")
        self.assertEqual(edge_number, sum(map(len, TRANSITIONS.values())))
        self.assertFalse(self.research_root.exists())

    def test_governance_cli_register_transition_status_and_archive(self):
        _, _, candidate = self._optimization_setup()
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize", "register", "--id", candidate["id"], "--owner", "developer",
                          "--purpose", "reduce missing dependency context", "--case", "session",
                          "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        self.assertEqual("proposed", json.loads(output.getvalue())["state"])
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize", "transition", "--id", candidate["id"], "--state", "experimenting",
                          "--note", "started experimenting", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        self.assertEqual("experimenting", json.loads(output.getvalue())["state"])
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-status", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        report = json.loads(output.getvalue())
        self.assertEqual(1, len(report["active"]))
        self.assertEqual([], report["archived"])
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-archive", candidate["id"], "--note", "obsolete experiment",
                          "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        archived = json.loads(output.getvalue())
        self.assertEqual("archived", archived["state"])
        self.assertEqual("experimenting", archived["previous_state"])
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-status", "--workspace", str(self.workspace_path), "--json"))
        report = json.loads(output.getvalue())
        self.assertEqual(1, len(report["archived"]))
        self.assertEqual([], report["active"])
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertNotEqual(0, main(("local", "optimize", "transition", "--id", candidate["id"], "--state", "accepted",
                                        "--note", "too late", "--workspace", str(self.workspace_path))))
        self.assertFalse(self.research_root.exists())

    def test_governance_maintenance_detects_stale_and_duplicate_candidates(self):
        from src.developer.optimization import create_candidate
        from src.developer.governance import register_candidate, maintenance_report
        _, _, candidate = self._optimization_setup("dependency-gap-one")
        create_candidate(self.developer, "dependency-gap-two", "Same repeated gap", candidate["cases"],
                         candidate["source"], candidate["proposed_change"], "Run baseline cases")
        registered = register_candidate(self.developer, "dependency-gap-one", "developer", "purpose", candidate["cases"])
        lifecycle_path = (self.workspace_path / "optimization" / "candidates" / "dependency-gap-one"
                          / "lifecycle" / f"{registered['id']}.json")
        document = json.loads(lifecycle_path.read_text(encoding="utf-8"))
        document["recorded_at"] = "2020-01-01T00:00:00+00:00"
        lifecycle_path.write_text(json.dumps(document), encoding="utf-8")
        report = maintenance_report(self.developer)
        self.assertEqual(["dependency-gap-one"], [item["candidate_id"] for item in report["stale_candidates"]])
        self.assertTrue(any(item["type"] == "duplicate_attempt" for item in report["duplicates"]))
        self.assertEqual([], report["maintenance_notes"])
        self.assertFalse(self.research_root.exists())

    def test_governance_history_preservation_and_safety_compatibility(self):
        from src.developer.governance import register_candidate, transition_candidate, show_lifecycle
        from src.developer.optimization import validate_candidate, decide_candidate
        from src.developer.safety import detect_conflicts, show_rollback
        cases, baseline, candidate = self._optimization_setup()
        register_candidate(self.developer, candidate["id"], "developer", "reduce missing dependency context", ["session"])
        transition_candidate(self.developer, candidate["id"], "experimenting", "begin validation")
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            result = validate_candidate(self.developer, candidate["id"], self.repository, cases, "default")
        transition_candidate(self.developer, candidate["id"], "validated", "validation gates passed",
                             last_validation_at=result["recorded_at"])
        decide_candidate(self.developer, candidate["id"], "accepted", "Reviewed evidence and gates")
        transition_candidate(self.developer, candidate["id"], "accepted", "decision recorded")
        conflicts = detect_conflicts(self.developer)
        self.assertEqual([], conflicts["conflicts"])
        rollback = show_rollback(self.developer, candidate["id"])["candidates"][0]
        self.assertTrue(rollback["rollback_available"])
        history = show_lifecycle(self.developer, candidate["id"])["candidates"][0]["history"]
        self.assertEqual(["proposed", "experimenting", "validated", "accepted"], [item["state"] for item in history])
        self.assertEqual("Candidate registered for lifecycle tracking.", history[0]["note"])
        self.assertFalse(self.research_root.exists())

    def test_governance_audit_is_read_only_and_detects_corruption(self):
        from src.developer.governance import optimize_audit, register_candidate, transition_candidate
        _, _, candidate = self._optimization_setup()
        register_candidate(self.developer, candidate["id"], "developer", "audit lifecycle", ["session"])
        transition_candidate(self.developer, candidate["id"], "experimenting", "begin experiment")
        lifecycle_dir = self.workspace_path / "optimization" / "candidates" / candidate["id"] / "lifecycle"
        before = {path.name: path.read_bytes() for path in lifecycle_dir.glob("*.json")}
        clean = optimize_audit(self.developer)
        self.assertEqual("clean", clean["audit_status"])
        self.assertEqual([], clean["issues"])
        self.assertEqual(before, {path.name: path.read_bytes() for path in lifecycle_dir.glob("*.json")})

        source = json.loads(next(lifecycle_dir.glob("*.json")).read_text(encoding="utf-8"))
        source["owner"] = ""
        source["state"] = []
        broken_path = lifecycle_dir / "manually-corrupted.json"
        broken_path.write_text(json.dumps(source), encoding="utf-8")
        unchanged = broken_path.read_bytes()
        report = optimize_audit(self.developer)
        self.assertEqual("issues_found", report["audit_status"])
        self.assertTrue(report["missing_metadata"])
        self.assertTrue(report["duplicate_history_entries"])
        self.assertTrue(report["inconsistent_states"])
        self.assertEqual(unchanged, broken_path.read_bytes())
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-audit", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        cli_report = json.loads(output.getvalue())
        self.assertEqual(report["audit_status"], cli_report["audit_status"])
        self.assertTrue(cli_report["issues"])
        self.assertEqual(report["missing_metadata"], cli_report["missing_metadata"])
        self.assertFalse(self.research_root.exists())

    def test_governance_history_includes_ownership_validation_rollback_and_archive(self):
        from src.developer.governance import (
            optimize_history, register_candidate, transition_candidate,
        )
        from src.developer.optimization import decide_candidate, validate_candidate
        from src.developer.safety import record_rollback
        cases, _, candidate = self._optimization_setup()
        register_candidate(self.developer, candidate["id"], "first-owner", "trace experiment", ["session"])
        transition_candidate(self.developer, candidate["id"], "experimenting", "started", owner="second-owner")
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            validation = validate_candidate(self.developer, candidate["id"], self.repository, cases, "default")
        transition_candidate(self.developer, candidate["id"], "validated", "all gates passed",
                            last_validation_at=validation["recorded_at"])
        decide_candidate(self.developer, candidate["id"], "accepted", "reviewed")
        transition_candidate(self.developer, candidate["id"], "accepted", "accepted after review")
        record_rollback(self.developer, candidate["id"], "restore prior behavior")
        transition_candidate(self.developer, candidate["id"], "rolled_back", "manual restoration recorded")
        transition_candidate(self.developer, candidate["id"], "archived", "experiment complete")

        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-history", candidate["id"], "--workspace",
                           str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        history = json.loads(output.getvalue())
        self.assertEqual("archived", history["history"][-1]["record"]["state"])
        kinds = [event["event_type"] for event in history["history"]]
        self.assertIn("ownership_changed", kinds)
        self.assertIn("validation", kinds)
        self.assertIn("rollback", kinds)
        self.assertIn("archived", kinds)
        self.assertTrue(all(event["immutable"] for event in history["history"]))
        times = [event["recorded_at"] for event in history["history"]]
        self.assertEqual(sorted(times), times)
        self.assertFalse(self.research_root.exists())

    def test_governance_rejected_archival_and_archived_inspection(self):
        from src.developer.governance import optimize_history, register_candidate, transition_candidate
        from src.developer.optimization import decide_candidate
        _, _, candidate = self._optimization_setup()
        register_candidate(self.developer, candidate["id"], "developer", "retire failed attempt", ["session"])
        transition_candidate(self.developer, candidate["id"], "experimenting", "attempt started")
        decide_candidate(self.developer, candidate["id"], "rejected", "evidence did not support change")
        transition_candidate(self.developer, candidate["id"], "rejected", "rejected after review")
        transition_candidate(self.developer, candidate["id"], "archived", "retain for reference")
        report = optimize_history(self.developer, candidate["id"])
        self.assertEqual("archived", report["history"][-1]["record"]["state"])
        self.assertEqual("rejected", report["history"][-2]["record"]["state"])
        with self.assertRaisesRegex(LocalWorkflowError, "Invalid lifecycle transition"):
            transition_candidate(self.developer, candidate["id"], "experimenting", "reopen archived record")

    def test_governance_maintenance_reports_metadata_validation_and_archived_references(self):
        from src.developer.optimization import create_candidate, decide_candidate
        from src.developer.governance import maintenance_report, register_candidate, transition_candidate
        _, _, candidate = self._optimization_setup("retired-parent")
        decide_candidate(self.developer, candidate["id"], "rejected", "not supported")
        child = create_candidate(self.developer, "active-child", "Retry", candidate["cases"],
                                 candidate["source"], "A revised proposal", "Repeat local cases",
                                 supersedes=candidate["id"])
        register_candidate(self.developer, candidate["id"], "developer", "archive prior attempt", ["session"])
        transition_candidate(self.developer, candidate["id"], "archived", "replaced by retry")
        register_candidate(self.developer, child["id"], "developer", "active retry", ["session"])
        transition_candidate(self.developer, child["id"], "experimenting", "begin retry")
        transition_candidate(self.developer, child["id"], "validated", "record incomplete validation",
                            last_validation_at="2020-01-01T00:00:00+00:00")
        transition_candidate(self.developer, child["id"], "accepted", "stale acceptance for diagnostic")

        lifecycle_dir = self.workspace_path / "optimization" / "candidates" / child["id"] / "lifecycle"
        latest = max(lifecycle_dir.glob("*.json"), key=lambda path: json.loads(path.read_text())["sequence"])
        record = json.loads(latest.read_text(encoding="utf-8"))
        record["owner"] = ""
        latest.write_text(json.dumps(record), encoding="utf-8")
        report = maintenance_report(self.developer)
        self.assertTrue(report["incomplete_validation_records"])
        self.assertTrue(report["missing_ownership_fields"])
        self.assertTrue(report["stale_accepted_candidates"])
        self.assertEqual([candidate["id"]], [item["candidate_id"] for item in report["archived_active_references"]])
        self.assertTrue(report["recommendations"])
        self.assertFalse(report["automatic_changes"])
        self.assertFalse(self.research_root.exists())

    def test_governance_health_and_summary_cli_are_read_only(self):
        from src.developer.governance import register_candidate
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-health", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        self.assertEqual("clean", json.loads(output.getvalue())["health_status"])

        _, _, candidate = self._optimization_setup()
        register_candidate(self.developer, candidate["id"], "developer", "health check", ["session"])
        lifecycle_dir = self.workspace_path / "optimization" / "candidates" / candidate["id"] / "lifecycle"
        before = {path.name: path.read_bytes() for path in lifecycle_dir.glob("*.json")}

        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-health", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        health = json.loads(output.getvalue())
        self.assertEqual("warnings", health["health_status"])
        self.assertEqual("passed", health["checks"]["lifecycle"]["status"])
        self.assertEqual("passed", health["checks"]["metadata"]["status"])
        self.assertTrue(any(item["issue"] == "unresolved_candidate" for item in health["issues"]))
        self.assertFalse(health["automatic_changes"])

        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-summary", "--workspace", str(self.workspace_path),
                           "--recent-limit", "5", "--json"))
        self.assertEqual(0, status)
        summary = json.loads(output.getvalue())["summary"]
        self.assertEqual(1, summary["candidate_state_counts"]["proposed"])
        self.assertEqual(0, summary["candidate_records_total"] - sum(summary["candidate_state_counts"].values())
                         - summary["untracked_candidate_count"])
        self.assertEqual(0, summary["untracked_candidate_count"])
        self.assertEqual(candidate["id"], summary["recent_lifecycle_activity"][0]["candidate_id"])
        self.assertNotIn("score", summary)
        self.assertNotIn("ranking", summary)
        self.assertEqual(before, {path.name: path.read_bytes() for path in lifecycle_dir.glob("*.json")})
        self.assertFalse(self.research_root.exists())

    def test_governance_checkpoint_cli_appends_immutable_workspace_snapshots(self):
        _, _, candidate = self._optimization_setup()
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-checkpoint", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        first = json.loads(output.getvalue())
        self.assertEqual("developer-local-governance-checkpoint", first["mode"])
        self.assertEqual("warnings", first["health_status"])
        self.assertEqual({"proposed": 0, "experimenting": 0, "validated": 0, "accepted": 0,
                          "rejected": 0, "rolled_back": 0, "archived": 0}, first["candidate_state_counts"])
        self.assertEqual(1, first["untracked_candidate_count"])
        checkpoint_dir = self.workspace_path / "optimization" / "governance-checkpoints"
        checkpoint_path = Path(first["path"])
        first_bytes = checkpoint_path.read_bytes()
        self.assertEqual(self.workspace_path.resolve(), checkpoint_path.resolve().parents[2])

        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-checkpoint", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        second = json.loads(output.getvalue())
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(first_bytes, checkpoint_path.read_bytes())
        self.assertEqual(2, len(list(checkpoint_dir.glob("*.json"))))
        self.assertEqual(candidate["id"], first["detected_issues"][0]["candidate_id"])
        self.assertFalse(self.research_root.exists())

    def test_governance_maintenance_findings_include_priority_actions_and_events(self):
        from src.developer.optimization import create_candidate
        from src.developer.governance import maintenance_report, register_candidate
        _, _, candidate = self._optimization_setup("maintenance-primary")
        create_candidate(self.developer, "maintenance-duplicate", "Same issue", candidate["cases"],
                         candidate["source"], candidate["proposed_change"], "Run local cases")
        register_candidate(self.developer, candidate["id"], "developer", "review duplicate", candidate["cases"])
        report = maintenance_report(self.developer)
        duplicate = next(item for item in report["findings"] if item["issue"] == "duplicate_attempt")
        self.assertEqual("warning", duplicate["severity"])
        self.assertEqual(["maintenance-duplicate", "maintenance-primary"], duplicate["affected_candidate_ids"])
        self.assertIn("Review", duplicate["recommendation"])
        self.assertTrue(duplicate["related_lifecycle_events"])
        self.assertTrue(all("event_id" in event for event in duplicate["related_lifecycle_events"]))
        self.assertFalse(report["automatic_changes"])
        self.assertFalse(self.research_root.exists())

    def test_safety_rejected_candidate_has_reason_and_blocks_rollback(self):
        from src.developer.optimization import decide_candidate
        from src.developer.safety import record_rollback
        _, _, candidate = self._optimization_setup()
        decision = decide_candidate(self.developer, candidate["id"], "rejected", "Introduced unrelated context")
        self.assertEqual("Introduced unrelated context", decision["reason"])
        self.assertIsNone(decision["validation"])
        self.assertIsNone(decision["rollback"]["restore_to"])
        with self.assertRaisesRegex(LocalWorkflowError, "previously accepted"):
            record_rollback(self.developer, candidate["id"], "attempt restore")

    def test_safety_experiment_history_tracks_superseded_attempts(self):
        from src.developer.optimization import create_candidate, decide_candidate, show_candidates
        _, _, candidate = self._optimization_setup("attempt-one")
        decide_candidate(self.developer, "attempt-one", "rejected", "Too much unrelated context")
        retry = create_candidate(self.developer, "attempt-two", "Review repeated context", candidate["cases"],
                                 candidate["source"], "Narrower dependency expansion", "Run baseline cases",
                                 supersedes="attempt-one")
        self.assertEqual("attempt-one", retry["supersedes"])
        shown = show_candidates(self.developer, "attempt-two")["candidates"][0]
        self.assertEqual(2, len(shown["history"]))
        self.assertEqual(["attempt-one", "attempt-two"], [item["candidate_id"] for item in shown["history"]])
        self.assertEqual("rejected", shown["history"][0]["status"])
        self.assertEqual("Too much unrelated context", shown["history"][0]["reason"])
        self.assertEqual("candidate", shown["history"][1]["status"])
        self.assertIsNone(shown["history"][1]["reason"])
        self.assertEqual(["attempt-two"], show_candidates(self.developer)["unresolved_candidates"])
        with self.assertRaisesRegex(LocalWorkflowError, "previously rejected"):
            create_candidate(self.developer, "attempt-three", "gap", candidate["cases"], candidate["source"],
                             "change", "check", supersedes="attempt-two")

    def test_safety_optimize_check_reports_conflicts_without_resolving(self):
        from src.developer.optimization import create_candidate
        from src.developer.safety import detect_conflicts
        _, _, candidate = self._optimization_setup("dependency-gap-one")
        create_candidate(self.developer, "dependency-gap-two", "Same repeated gap", candidate["cases"],
                         candidate["source"], candidate["proposed_change"], "Run baseline cases")
        report = detect_conflicts(self.developer)
        types = {item["type"] for item in report["conflicts"]}
        self.assertIn("repeated_case_target", types)
        self.assertIn("duplicate_attempt", types)
        self.assertIn("session", report["affected_cases"])
        self.assertTrue(any(item["type"] == "unresolved_candidate" for item in report["warnings"]))
        repeated = next(item for item in report["conflicts"] if item["type"] == "repeated_case_target")
        self.assertEqual(["dependency-gap-one", "dependency-gap-two"], repeated["candidates"])
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-check", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        cli_report = json.loads(output.getvalue())
        self.assertEqual(report["conflicts"], cli_report["conflicts"])

    def test_safety_cli_rollback_show_and_record(self):
        from src.developer.optimization import validate_candidate, decide_candidate
        cases, baseline, candidate = self._optimization_setup()
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            validate_candidate(self.developer, candidate["id"], self.repository, cases, "default")
        decide_candidate(self.developer, candidate["id"], "accepted", "Reviewed evidence and gates")
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "rollback", "--id", candidate["id"], "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        payload = json.loads(output.getvalue())
        self.assertTrue(payload["candidates"][0]["rollback_available"])
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "rollback", "record", "--id", candidate["id"], "--note", "Restore baseline",
                          "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        recorded = json.loads(output.getvalue())
        self.assertEqual(candidate["id"], recorded["candidate_id"])
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertNotEqual(0, main(("local", "rollback", "record", "--workspace", str(self.workspace_path))))
        self.assertFalse(self.research_root.exists())

    def _promotion_setup(self, identifier="promotable"):
        from src.developer.optimization import validate_candidate
        from src.developer.governance import register_candidate, transition_candidate
        from src.developer.review import create_review, approve_review
        cases, baseline, candidate = self._optimization_setup(
            identifier, retrieval_settings={"relationship_factor": 1.5})
        register_candidate(self.developer, candidate["id"], "developer", "validate settings", candidate["cases"])
        transition_candidate(self.developer, candidate["id"], "experimenting", "try explicit settings")
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            validation = validate_candidate(self.developer, candidate["id"], self.repository, cases, "default",
                                            {"session": "Review relationship factor change"})
        self.assertTrue(validation["passed"], validation)
        transition_candidate(self.developer, candidate["id"], "validated", "gates passed",
                             last_validation_at=validation["recorded_at"])
        review = create_review(self.developer, candidate["id"], "Review configuration",
                               conflict_note="Case IDs can overlap across isolated repositories.")
        approve_review(self.developer, review["review_id"], "developer", "Approved settings and evidence")
        return candidate, cases

    def _configuration_setup(self):
        from src.developer.promotion import promote
        from src.developer.configuration import create_configuration
        candidate, _ = self._promotion_setup()
        source = promote(self.developer, candidate["id"])
        record = create_configuration(self.developer, source["promotion_id"], "Snapshot approved settings")
        return source, record

    def test_configuration_creation_validation_and_invalid_transitions(self):
        from src.developer.configuration import configuration_history, transition_configuration
        source, record = self._configuration_setup()
        self.assertEqual(1, record["version"])
        self.assertEqual("draft", record["status"])
        self.assertEqual(source["retrieval_settings"], record["settings"])
        self.assertEqual(source["promotion_id"], record["source_promotion"])
        with self.assertRaisesRegex(LocalWorkflowError, "Invalid configuration transition"):
            transition_configuration(self.developer, record["config_id"], "activate", "Premature")
        transition_configuration(self.developer, record["config_id"], "validate", "Evidence checked")
        with self.assertRaises(LocalWorkflowError):
            transition_configuration(self.developer, record["config_id"], "validate", "Repeat")
        with self.assertRaises(LocalWorkflowError):
            transition_configuration(self.developer, record["config_id"], "activate", " ")
        self.assertEqual(2, len(configuration_history(self.developer)["events"]))

    def test_configuration_activation_rollback_and_history_preservation(self):
        from src.developer.configuration import (
            create_configuration, transition_configuration, configuration_history, configuration_status,
        )
        source, first = self._configuration_setup()
        directory = self.workspace_path / "optimization" / "configurations"
        original = {p: p.read_bytes() for p in directory.glob("*.json")}
        for action in ("validate", "activate"):
            transition_configuration(self.developer, first["config_id"], action, "First snapshot")
        second = create_configuration(self.developer, source["promotion_id"], "Second snapshot")
        self.assertEqual(2, second["version"])
        self.assertEqual(first["config_id"], second["previous_active"])
        for action in ("validate", "activate"):
            transition_configuration(self.developer, second["config_id"], action, "Second snapshot")
        state = configuration_history(self.developer)
        self.assertEqual("retired", state["configurations"][0]["status"])
        self.assertEqual(first["config_id"], state["events"][-1]["retired_configuration"])
        with self.assertRaises(LocalWorkflowError):
            transition_configuration(self.developer, first["config_id"], "rollback", "Out of order")
        transition_configuration(self.developer, second["config_id"], "rollback", "Restore prior reference")
        self.assertEqual(first["config_id"], configuration_status(self.developer)["active"])
        transition_configuration(self.developer, first["config_id"], "rollback", "Restore empty reference")
        self.assertIsNone(configuration_status(self.developer)["active"])
        self.assertEqual(["rolled_back", "rolled_back"],
                         [r["status"] for r in configuration_history(self.developer)["configurations"]])
        for path, content in original.items():
            self.assertEqual(content, path.read_bytes())

    def test_configuration_diff_nested_added_removed_changed_and_versions(self):
        from src.developer.configuration import settings_diff, configuration_diff, create_configuration
        diff = settings_diff({"ranking": {"symbol_weight": 1}, "old": True},
                             {"ranking": {"symbol_weight": 2}, "context": {"max_files": 10}})
        self.assertEqual([{"path": ["ranking", "symbol_weight"], "previous": 1, "value": 2}], diff["changed"])
        self.assertEqual([{"path": ["old"], "previous": True}], diff["removed"])
        self.assertEqual([{"path": ["context"], "value": {"max_files": 10}}], diff["added"])
        source, _ = self._configuration_setup()
        create_configuration(self.developer, source["promotion_id"], "Another immutable snapshot")
        self.assertEqual([], configuration_diff(self.developer, 1, 2)["changed"])
        with self.assertRaises(LocalWorkflowError):
            configuration_diff(self.developer, 1, 99)

    def test_configuration_policy_approval_and_promotion_compatibility(self):
        from src.developer.configuration import transition_configuration, configuration_status
        from src.developer.promotion import retire, active_configuration
        source, record = self._configuration_setup()
        before = active_configuration(self.developer)
        with patch("src.developer.promotion.policy_check", return_value={"blocked": [{"check": "policy"}]}):
            with self.assertRaisesRegex(LocalWorkflowError, "policy"):
                transition_configuration(self.developer, record["config_id"], "validate", "Blocked")
        transition_configuration(self.developer, record["config_id"], "validate", "Valid")
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            with self.assertRaisesRegex(LocalWorkflowError, "approved"):
                transition_configuration(self.developer, record["config_id"], "activate", "No approval")
        transition_configuration(self.developer, record["config_id"], "activate", "Approved")
        self.assertEqual(before, active_configuration(self.developer))
        retire(self.developer, source["promotion_id"])
        self.assertTrue(configuration_status(self.developer)["blocked"])

    def test_configuration_stale_reference_and_retirement(self):
        from src.developer.configuration import create_configuration, transition_configuration, configuration_status
        source, first = self._configuration_setup()
        stale = create_configuration(self.developer, source["promotion_id"], "Parallel draft")
        for record in (first, stale):
            transition_configuration(self.developer, record["config_id"], "validate", "Check")
        transition_configuration(self.developer, first["config_id"], "activate", "Activate first")
        with self.assertRaisesRegex(LocalWorkflowError, "reference changed"):
            transition_configuration(self.developer, stale["config_id"], "activate", "Stale")
        transition_configuration(self.developer, stale["config_id"], "retire", "Discard stale draft")
        transition_configuration(self.developer, first["config_id"], "retire", "Retire active reference")
        self.assertIsNone(configuration_status(self.developer)["active"])
        with self.assertRaises(LocalWorkflowError):
            transition_configuration(self.developer, first["config_id"], "activate", "Cannot reactivate")

    def test_configuration_atomic_failure_corruption_and_read_only_status(self):
        from src.developer.configuration import configuration_status, configuration_history, transition_configuration
        self.assertIsNone(configuration_status(self.developer)["active"])
        self.assertFalse((self.workspace_path / "optimization" / "configurations").exists())
        _, record = self._configuration_setup()
        before = configuration_history(self.developer)
        with patch("src.developer.configuration.os.link", side_effect=FileExistsError("Competing writer")):
            with self.assertRaisesRegex(LocalWorkflowError, "Cannot append"):
                transition_configuration(self.developer, record["config_id"], "validate", "Try append")
        self.assertEqual(before, configuration_history(self.developer))
        directory = self.workspace_path / "optimization" / "configurations"
        self.assertFalse(list(directory.glob("*.tmp")))
        path = next(directory.glob("*.json"))
        event = json.loads(path.read_text())
        event["configuration"]["version"] = 99
        path.write_text(json.dumps(event))
        with self.assertRaisesRegex(LocalWorkflowError, "Invalid configuration journal"):
            configuration_history(self.developer)

    def test_configuration_cli_and_audit_compatibility(self):
        from src.developer.promotion import promote, promotion_check
        from src.developer.governance import optimize_audit
        candidate, _ = self._promotion_setup()
        source = promote(self.developer, candidate["id"])
        def cli(*arguments):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main(("local", *arguments, "--workspace", str(self.workspace_path), "--json")))
            return json.loads(output.getvalue())
        record = cli("config-create", source["promotion_id"], "--reason", "CLI snapshot")
        identifier = record["config_id"]
        for command in ("config-validate", "config-activate"):
            cli(command, identifier, "--reason", "CLI transition")
        files = {p: p.read_bytes() for p in self.workspace_path.rglob("*.json")}
        self.assertEqual(identifier, cli("config-status")["active"])
        self.assertEqual(3, len(cli("config-history")["events"]))
        self.assertFalse(cli("config-diff", "1", "1")["changed"])
        self.assertFalse(promotion_check(self.developer)["blocked"])
        self.assertEqual("clean", optimize_audit(self.developer)["audit_status"])
        for path, content in files.items():
            self.assertEqual(content, path.read_bytes())
        cli("config-rollback", identifier, "--reason", "CLI restore")
        cli("config-retire", identifier, "--reason", "CLI retire")
        self.assertEqual("retired", cli("config-history")["configurations"][0]["status"])

    def test_configuration_isolation_and_rollback_policy_failure(self):
        from src.developer.configuration import (
            create_configuration, transition_configuration, configuration_history, configuration_status,
        )
        from src.developer.local_workflow import _PROJECT_ROOT
        for root in (_PROJECT_ROOT / "config-records", self.research_root / "config-records"):
            isolated = DeveloperWorkspace(root, (self.research_root,))
            with self.assertRaises(LocalWorkflowError):
                configuration_status(isolated)
            self.assertFalse(root.exists())
        source, first = self._configuration_setup()
        for action in ("validate", "activate"):
            transition_configuration(self.developer, first["config_id"], action, "First")
        second = create_configuration(self.developer, source["promotion_id"], "Second")
        for action in ("validate", "activate"):
            transition_configuration(self.developer, second["config_id"], action, "Second")
        before = configuration_history(self.developer)
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            with self.assertRaises(LocalWorkflowError):
                transition_configuration(self.developer, second["config_id"], "rollback", "Blocked restore")
        self.assertEqual(before, configuration_history(self.developer))

    def test_deployment_audit_lifecycle_is_append_only(self):
        from src.developer import deployment as d
        _, _, record = self._deployment_setup()
        identifier = record["deployment_id"]
        directory = self.workspace_path / "optimization" / "deployments"
        before = {p: p.read_bytes() for p in directory.glob("*.json")}
        for action in ("validate", "activate", "pause", "resume", "rollback", "retire"):
            d.transition_deployment(self.developer, identifier, action, "Decision: " + action, "operator")
        events = d.deployment_audit(self.developer, identifier)["events"]
        self.assertEqual(["created", "staged", "validated", "activated", "paused", "resumed",
                          "rolled_back", "retired"], [e["event_type"] for e in events])
        self.assertEqual(len(events), len({e["event_id"] for e in events}))
        for event in events:
            self.assertEqual({"event_id", "deployment_id", "event_type", "created_at", "actor", "reason", "metadata"},
                             set(event))
            self.assertTrue(event["created_at"])
        self.assertEqual("operator", events[2]["actor"])
        self.assertEqual("Decision: validate", events[2]["reason"])
        self.assertTrue(events[2]["metadata"]["validation"]["configuration_valid"])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        events[0]["reason"] = "Attempted mutation"
        self.assertNotEqual(events, d.deployment_audit(self.developer, identifier)["events"])

    def test_deployment_audit_covers_atomic_replacement_and_restoration(self):
        from src.developer import deployment as d
        source, _, first = self._deployment_setup()
        for action in ("validate", "activate"):
            d.transition_deployment(self.developer, first["deployment_id"], action, "First")
        second = self._next_deployment(source)
        for action in ("validate", "activate"):
            d.transition_deployment(self.developer, second["deployment_id"], action, "Second")
        identifier = second["deployment_id"]
        inspect = d.deployment_inspect(self.developer, identifier)
        self.assertTrue(inspect["rollback"]["action_available"])
        self.assertFalse(inspect["governance"]["blocked"])
        retired = d.deployment_audit(self.developer, first["deployment_id"])["events"][-1]
        self.assertEqual("retired", retired["event_type"])
        self.assertEqual("superseded", retired["metadata"]["action"])
        self.assertEqual(identifier, retired["metadata"]["trigger_deployment_id"])
        d.transition_deployment(self.developer, identifier, "rollback", "Restore", "on-call")
        restored = d.deployment_audit(self.developer, first["deployment_id"])["events"][-1]
        rollback = d.deployment_audit(self.developer, identifier)["events"][-1]
        self.assertEqual("activated", restored["event_type"])
        self.assertEqual("restored", restored["metadata"]["action"])
        self.assertEqual("rolled_back", rollback["event_type"])
        self.assertEqual(restored["metadata"]["sequence"], rollback["metadata"]["sequence"])
        self.assertEqual(first["deployment_id"], restored["deployment_id"])
        self.assertEqual("on-call", restored["actor"])

    def test_deployment_audit_rejects_invalid_records_and_missing_history(self):
        from src.developer import deployment as d
        _, _, record = self._deployment_setup()
        identifier = record["deployment_id"]
        directory = self.workspace_path / "optimization" / "deployments"
        before = {p: p.read_bytes() for p in directory.glob("*.json")}
        for action, reason, actor in (("invalid", "Why", "developer"), ("validate", "", "developer"),
                                      ("validate", "Why", "")):
            with self.assertRaises(LocalWorkflowError):
                d.transition_deployment(self.developer, identifier, action, reason, actor)
        self.assertEqual(before, {p: p.read_bytes() for p in directory.glob("*.json")})
        tail = directory / "00000002.json"
        original = json.loads(tail.read_text())
        from copy import deepcopy
        for key, value in (("event_type", "unknown"), ("deployment_id", "wrong"),
                           ("reason", "rewritten"), ("metadata", {}), ("actor", "")):
            event = deepcopy(original)
            event["audit_records"][0][key] = value
            tail.write_text(json.dumps(event), encoding="utf-8")
            with self.assertRaisesRegex(LocalWorkflowError, "audit records"):
                d.deployment_audit(self.developer, identifier)
            self.assertEqual("audit_history", d.deployment_governance_check(self.developer, identifier)["blocked"][0]["check"])
        tail.write_bytes(before[tail])
        (directory / "00000001.json").unlink()
        with self.assertRaisesRegex(LocalWorkflowError, "journal"):
            d.deployment_inspect(self.developer, identifier)

    def test_deployment_audit_legacy_journal_compatibility(self):
        from src.developer import deployment as d
        import hashlib
        from src.developer.local_workflow import _json_bytes
        _, _, record = self._deployment_setup()
        identifier = record["deployment_id"]
        expected = d.deployment_audit(self.developer, identifier)
        directory = self.workspace_path / "optimization" / "deployments"
        digest = None
        for path in sorted(directory.glob("*.json")):
            event = json.loads(path.read_text())
            event["schema_version"] = 1
            event.pop("audit_records")
            event["previous_digest"] = digest
            path.write_bytes(_json_bytes(event))
            digest = hashlib.sha256(_json_bytes(event)).hexdigest()
        before = {p: p.read_bytes() for p in directory.glob("*.json")}
        self.assertEqual(expected, d.deployment_audit(self.developer, identifier))
        d.transition_deployment(self.developer, identifier, "validate", "Upgrade append")
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual(3, len(d.deployment_audit(self.developer, identifier)["events"]))

    def test_deployment_governance_live_prerequisites_and_compatibility(self):
        from src.developer import deployment as d
        from src.developer.configuration import transition_configuration
        _, config, record = self._deployment_setup()
        identifier = record["deployment_id"]
        staged = d.deployment_governance_check(self.developer, identifier)
        self.assertEqual(["validation_evidence"], [x["check"] for x in staged["blocked"]])
        d.transition_deployment(self.developer, identifier, "validate", "Validate")
        good = d.deployment_governance_check(self.developer, identifier)
        self.assertFalse(good["blocked"])
        self.assertEqual({"ownership", "source_configuration", "promotion_approval", "validation_evidence",
                          "lifecycle_state", "audit_history"}, {x["check"] for x in good["passed"]})
        self.assertEqual("rollback_target", good["warnings"][0]["check"])
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            bad = d.deployment_governance_check(self.developer, identifier)
            self.assertIn("promotion_approval", [x["check"] for x in bad["blocked"]])
        transition_configuration(self.developer, config["config_id"], "retire", "Withdraw config")
        bad = d.deployment_governance_check(self.developer, identifier)
        self.assertIn("source_configuration", [x["check"] for x in bad["blocked"]])
        self.assertTrue(d.deployment_inspect(self.developer, identifier)["audit_timeline"])

    def test_deployment_investigation_cli_is_read_only(self):
        from src.developer import deployment as d
        source, config, record = self._deployment_setup()
        identifier = record["deployment_id"]
        d.transition_deployment(self.developer, identifier, "validate", "Validate")
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        results = {}
        for command in ("deploy-audit", "deploy-governance-check", "deploy-history", "deploy-inspect"):
            output = StringIO()
            args = [] if command == "deploy-history" else [identifier]
            with redirect_stdout(output):
                self.assertEqual(0, main(["local", command, *args, "--workspace", str(self.workspace_path), "--json"]))
            results[command] = json.loads(output.getvalue())
        inspect = results["deploy-inspect"]
        self.assertEqual(config["config_id"], inspect["deployment"]["configuration"]["config_id"])
        self.assertEqual(source["promotion_id"], inspect["source_promotion"]["record"]["promotion_id"])
        self.assertEqual(results["deploy-audit"]["events"], inspect["audit_timeline"])
        self.assertEqual("validated", results["deploy-history"]["deployments"][0]["stage"])
        self.assertEqual("validated", results["deploy-history"]["events"][0]["event_type"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        self.assertFalse(self.research_root.exists())

    def test_deployment_investigation_empty_unknown_and_isolation(self):
        from src.developer import deployment as d
        self.assertEqual([], d.deployment_history(self.developer)["events"])
        for reader in (d.deployment_audit, d.deployment_inspect, d.deployment_governance_check):
            with self.assertRaisesRegex(LocalWorkflowError, "Unknown deployment"):
                reader(self.developer, "missing")
        self.assertFalse(self.workspace_path.exists())
        for root in (local_workflow._PROJECT_ROOT / "audit-records", self.research_root / "audit-records"):
            isolated = DeveloperWorkspace(root, (self.research_root,))
            for reader in (d.deployment_audit, d.deployment_inspect):
                with self.assertRaises(LocalWorkflowError):
                    reader(isolated, "missing")
            self.assertTrue(d.deployment_governance_check(isolated, "missing")["blocked"])
            self.assertFalse(root.exists())

    def test_operations_creation_types_ownership_and_history_links(self):
        from src.developer import operations as o
        _, _, deployed = self._deployment_setup()
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        for kind in sorted(o.TYPES):
            record = o.create_operation(self.developer, deployed["deployment_id"], kind, "Investigate", "on-call")
            self.assertEqual(kind, record["type"])
            self.assertEqual("open", record["status"])
            self.assertEqual("on-call", record["owner"])
            self.assertEqual(deployed["history"], record["deployment_snapshot"]["history"])
            self.assertEqual("open", record["history"][0]["status"])
        self.assertEqual(5, len(o._load(self.developer)["operations"]))
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        record["history"].clear()
        self.assertTrue(o._load(self.developer)["operations"][-1]["history"])

    def test_operations_incident_lifecycle_and_atomic_recovery(self):
        from src.developer import operations as o
        _, _, deployed = self._deployment_setup()
        incident = o.create_incident(self.developer, deployed["deployment_id"], "Unexpected behavior", "operator")
        identifier = incident["operation_id"]
        directory = self.workspace_path / "optimization" / "operations"
        before = {p: p.read_bytes() for p in directory.glob("*.json")}
        o.transition_incident(self.developer, identifier, "investigating", "Review evidence", "operator")
        prior = o._load(self.developer)
        with patch("src.developer.operations.os.link", side_effect=FileExistsError("Competing writer")):
            with self.assertRaises(LocalWorkflowError):
                o.transition_incident(self.developer, identifier, "resolved", "Recovered", "operator", "Manual verification")
        self.assertEqual(prior, o._load(self.developer))
        self.assertFalse(list(directory.glob("*.tmp")))
        resolved = o.transition_incident(self.developer, identifier, "resolved", "Recovered", "operator", "Manual verification")
        history = o.recovery_history(self.developer)
        recovery = history["recovery_actions"][0]
        self.assertEqual(identifier, recovery["incident_id"])
        self.assertEqual(recovery["operation_id"], resolved["resolution"]["recovery_id"])
        self.assertEqual("resolved", recovery["status"])
        self.assertEqual(1, len(o.incident_status(self.developer)["resolved"]))
        closed = o.transition_incident(self.developer, identifier, "closed", "Investigation complete")
        self.assertEqual(["open", "investigating", "resolved", "closed"], [e["status"] for e in closed["history"]])
        self.assertEqual(1, len(o.incident_status(self.developer)["closed"]))
        self.assertEqual(1, len(history["resolution_history"]))
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_operations_invalid_transitions_and_attribution_do_not_write(self):
        from src.developer import operations as o
        _, _, deployed = self._deployment_setup()
        identifier = o.create_incident(self.developer, deployed["deployment_id"], "Issue")["operation_id"]
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        for status, reason, actor, recovery, rollback in (
                ("closed", "Why", "developer", None, None), ("unknown", "Why", "developer", None, None),
                ("open", "Why", "developer", None, None), ("investigating", "", "developer", None, None),
                ("investigating", "Why", " ", None, None), ("resolved", "Why", "developer", None, None),
                ("resolved", "Why", "developer", " ", None),
                ("resolved", "Why", "developer", "Manual action", "missing"),
                ("investigating", "Why", "developer", "Not allowed", None)):
            with self.assertRaises(LocalWorkflowError):
                o.transition_incident(self.developer, identifier, status, reason, actor, recovery, rollback)
        for kind, owner in (("unknown", "developer"), ("incident", " ")):
            with self.assertRaises(LocalWorkflowError):
                o.create_operation(self.developer, deployed["deployment_id"], kind, "Why", owner)
        with self.assertRaises(LocalWorkflowError):
            o.create_incident(self.developer, "missing", "Why")
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        o.transition_incident(self.developer, identifier, "resolved", "No change needed", recovery_action="Verified prerequisites")
        o.transition_incident(self.developer, identifier, "closed", "Done")
        for status in o.STATES:
            with self.assertRaises(LocalWorkflowError):
                o.transition_incident(self.developer, identifier, status, "Cannot reopen", recovery_action="Repeat")

    def test_operations_health_inspection_and_governance_are_read_only(self):
        from src.developer import deployment as d, operations as o
        from src.developer.configuration import transition_configuration
        _, config, deployed = self._deployment_setup()
        identifier = deployed["deployment_id"]
        incident = o.create_incident(self.developer, identifier, "Check readiness")
        self.assertEqual("blocked", o.deployment_health(self.developer, identifier)["status"])
        for action in ("validate", "activate"):
            d.transition_deployment(self.developer, identifier, action, "Ready")
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        health = o.deployment_health(self.developer, identifier)
        self.assertEqual("active", health["deployment_state"])
        self.assertEqual("warning", health["status"])  # Empty-reference first rollback.
        self.assertTrue(health["rollback_available"])
        self.assertEqual("validated", health["configuration_state"]["status"])
        inspect = o.incident_inspect(self.developer, incident["operation_id"])
        self.assertEqual(d.deployment_audit(self.developer, identifier)["events"], inspect["audit_events"])
        self.assertEqual(incident["history"], inspect["investigation_history"])
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            self.assertEqual("blocked", o.deployment_health(self.developer, identifier)["status"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        transition_configuration(self.developer, config["config_id"], "retire", "Withdraw")
        self.assertEqual("blocked", o.deployment_health(self.developer, identifier)["status"])
        self.assertFalse(self.research_root.exists())

    def test_operations_manual_rollback_references_and_comparison(self):
        from src.developer import deployment as d, operations as o
        source, _, first = self._deployment_setup()
        for action in ("validate", "activate"):
            d.transition_deployment(self.developer, first["deployment_id"], action, "First")
        first_incident = o.create_incident(self.developer, first["deployment_id"], "First issue")["operation_id"]
        second = self._next_deployment(source)
        for action in ("validate", "activate"):
            d.transition_deployment(self.developer, second["deployment_id"], action, "Second")
        self.assertEqual("healthy", o.deployment_health(self.developer, second["deployment_id"])["status"])
        incident = o.create_incident(self.developer, second["deployment_id"], "Second issue")["operation_id"]
        d.transition_deployment(self.developer, second["deployment_id"], "rollback", "Manual rollback")
        audit = d.deployment_audit(self.developer, second["deployment_id"])["events"][-1]
        before = d.deployment_history(self.developer)
        with self.assertRaises(LocalWorkflowError):
            o.transition_incident(self.developer, first_incident, "resolved", "Wrong target", recovery_action="Rollback",
                                  rollback_reference=audit["event_id"])
        o.transition_incident(self.developer, incident, "resolved", "Verified", recovery_action="Manually rolled back",
                              rollback_reference=audit["event_id"])
        self.assertEqual(before, d.deployment_history(self.developer))
        self.assertEqual(audit["event_id"], o.recovery_history(self.developer)["resolution_history"][0]["rollback_reference"])
        diff = o.incident_diff(self.developer, first_incident, incident)
        self.assertTrue(diff["configuration"]["changed"])
        self.assertTrue(diff["timeline"]["changed"])
        self.assertTrue(diff["resolution"]["changed"])
        self.assertEqual(first["deployment_id"], diff["affected_deployments"]["a"])
        with self.assertRaises(LocalWorkflowError):
            o.incident_diff(self.developer, incident, "missing")

    def test_operations_journal_corruption_and_deployment_links_fail_closed(self):
        from src.developer import operations as o
        from copy import deepcopy
        _, _, deployed = self._deployment_setup()
        incident = o.create_incident(self.developer, deployed["deployment_id"], "Issue")["operation_id"]
        directory = self.workspace_path / "optimization" / "operations"
        path = directory / "00000001.json"
        original = json.loads(path.read_text())
        for field, value in (("previous_digest", "bad"), ("sequence", 9), ("type", "unknown"),
                             ("created_at", "2026-09-29T00:00:00"), ("owner", ""), ("operation_id", "wrong")):
            event = deepcopy(original)
            event[field] = value
            path.write_text(json.dumps(event), encoding="utf-8")
            with self.assertRaisesRegex(LocalWorkflowError, "Invalid operations journal"):
                o.incident_status(self.developer)
        event = deepcopy(original)
        event["deployment_snapshot"]["configuration"]["config_id"] = "wrong"
        path.write_text(json.dumps(event), encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "history reference"):
            o.incident_inspect(self.developer, incident)
        path.write_text(json.dumps(original), encoding="utf-8")
        o.transition_incident(self.developer, incident, "investigating", "Check")
        path.unlink()
        with self.assertRaisesRegex(LocalWorkflowError, "journal chain"):
            o.recovery_history(self.developer)

    def test_operations_empty_unknown_and_workspace_isolation(self):
        from src.developer import operations as o
        self.assertFalse(o.incident_status(self.developer)["active"])
        self.assertFalse(o.recovery_history(self.developer)["incidents"])
        for reader in (o.incident_inspect, o.deployment_health):
            with self.assertRaises(LocalWorkflowError):
                reader(self.developer, "missing")
        self.assertFalse(self.workspace_path.exists())
        for root in (local_workflow._PROJECT_ROOT / "operation-records", self.research_root / "operation-records"):
            isolated = DeveloperWorkspace(root, (self.research_root,))
            for reader in (o.incident_status, o.recovery_history):
                with self.assertRaises(LocalWorkflowError):
                    reader(isolated)
            with self.assertRaises(LocalWorkflowError):
                o.create_incident(isolated, "missing", "Do not write")
            self.assertFalse(root.exists())

    def test_operations_cli_workflow_and_read_only_reports(self):
        from src.developer import operations as o
        _, _, deployed = self._deployment_setup()
        def run(command, *args):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main(["local", command, *args, "--workspace", str(self.workspace_path), "--json"]))
            return json.loads(output.getvalue())
        incident = run("incident-create", deployed["deployment_id"], "--owner", "on-call", "--reason", "Issue")
        identifier = incident["operation_id"]
        self.assertEqual("on-call", incident["owner"])
        run("incident-investigate", identifier, "--reason", "Investigating")
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        self.assertEqual("investigating", run("incident-status")["active"][0]["status"])
        self.assertEqual(identifier, run("incident-inspect", identifier)["incident"]["operation_id"])
        self.assertEqual("blocked", run("deploy-health", deployed["deployment_id"])["status"])
        self.assertFalse(run("incident-diff", identifier, identifier)["configuration"]["changed"])
        self.assertEqual(1, len(run("recovery-history")["incidents"]))
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        resolved = run("incident-resolve", identifier, "--reason", "Done", "--recovery-action", "Verified manually")
        with self.assertRaisesRegex(LocalWorkflowError, "not an incident"):
            o.incident_inspect(self.developer, resolved["resolution"]["recovery_id"])
        self.assertEqual("closed", run("incident-close", identifier, "--reason", "Reviewed")["status"])

    def test_reliability_readiness_creation_failure_and_expiry(self):
        from src.developer import reliability as r
        _, _, deployed = self._deployment_setup()
        record = r.create_readiness(self.developer, deployed["deployment_id"], "Prepare handoff", "on-call")
        identifier = record["readiness_id"]
        self.assertEqual("pending", record["status"])
        self.assertEqual([], record["checks"])
        self.assertEqual(deployed["history"], record["deployment_snapshot"]["history"])
        directory = self.workspace_path / "optimization" / "reliability"
        before = {p: p.read_bytes() for p in directory.glob("*.json")}
        checked = r.check_readiness(self.developer, identifier)
        self.assertEqual("failed", checked["status"])
        self.assertEqual(["pending", "checking", "failed"], [h["status"] for h in checked["history"]])
        self.assertIn("recovery_plan", [c["check"] for c in checked["checks"] if c["status"] == "blocked"])
        self.assertTrue(r.readiness_status(self.developer)["readiness"][0]["evidence_current"])
        expired = r.transition_readiness(self.developer, identifier, "expired", "Replace assessment")
        self.assertEqual("expired", expired["status"])
        self.assertEqual(checked["checks"], expired["checks"])
        self.assertTrue(r.readiness_status(self.developer)["readiness"][0]["requires_new_check"])
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_reliability_readiness_pass_and_stale_evidence(self):
        from src.developer import reliability as r, deployment as d, operations as o
        _, _, deployed = self._deployment_setup()
        identifier = deployed["deployment_id"]
        d.transition_deployment(self.developer, identifier, "validate", "Validate readiness prerequisite")
        plan = r.create_recovery_plan(self.developer, identifier, "Prepare recovery", "on-call")
        verified = r.verify_recovery(self.developer, plan["plan_id"])
        self.assertEqual("passed", verified["validation_status"])
        self.assertIsNone(verified["rollback_target"])
        self.assertIsNone(verified["previous_configuration"])
        self.assertTrue(verified["verification"]["warnings"])
        readiness = r.create_readiness(self.developer, identifier, "Check deployment")
        checked = r.check_readiness(self.developer, readiness["readiness_id"])
        self.assertEqual("passed", checked["status"])
        self.assertFalse(d.deployment_status(self.developer)["active_deployment"])
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        status = r.readiness_status(self.developer)["readiness"][0]
        self.assertTrue(status["evidence_current"])
        self.assertFalse(status["requires_new_check"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        incident = o.create_incident(self.developer, identifier, "Handoff issue", "on-call")
        stale = r.readiness_status(self.developer)["readiness"][0]
        self.assertEqual("passed", stale["status"])
        self.assertFalse(stale["evidence_current"])
        self.assertTrue(stale["requires_new_check"])
        report = r.reliability_check(self.developer, identifier)
        self.assertIn("incident_consistency", [w["check"] for w in report["warnings"]])
        self.assertEqual(incident["operation_id"], report["evidence"]["incidents"][0]["operation_id"])

    def test_reliability_invalid_transitions_and_outcome_cannot_bypass_checks(self):
        from src.developer import reliability as r
        _, _, deployed = self._deployment_setup()
        identifier = r.create_readiness(self.developer, deployed["deployment_id"], "Prepare")["readiness_id"]
        for status in ("pending", "passed", "failed", "unknown"):
            with self.assertRaises(LocalWorkflowError):
                r.transition_readiness(self.developer, identifier, status, "Invalid")
        r.transition_readiness(self.developer, identifier, "checking", "Start")
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        with self.assertRaisesRegex(LocalWorkflowError, "outcome"):
            r.transition_readiness(self.developer, identifier, "passed", "Cannot force pass")
        for reason, actor in (("", "developer"), ("Reason", " ")):
            with self.assertRaises(LocalWorkflowError):
                r.create_readiness(self.developer, deployed["deployment_id"], reason, actor)
        with self.assertRaises(LocalWorkflowError):
            r.create_recovery_plan(self.developer, deployed["deployment_id"], "No owner", " ")
        with self.assertRaises(LocalWorkflowError):
            r.create_recovery_plan(self.developer, "missing", "Bad deployment")
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        r.transition_readiness(self.developer, identifier, "failed", "Record failure")
        with self.assertRaises(LocalWorkflowError):
            r.check_readiness(self.developer, identifier)
        r.transition_readiness(self.developer, identifier, "expired", "End assessment")
        for status in r.STATES:
            with self.assertRaises(LocalWorkflowError):
                r.transition_readiness(self.developer, identifier, status, "Expired is terminal")

    def test_reliability_recovery_plan_predecessor_and_manual_rollback_compatibility(self):
        from src.developer import reliability as r, deployment as d, operations as o
        source, config, first = self._deployment_setup()
        for action in ("validate", "activate"):
            d.transition_deployment(self.developer, first["deployment_id"], action, "First rollout")
        second = self._next_deployment(source)
        identifier = second["deployment_id"]
        for action in ("validate", "activate"):
            d.transition_deployment(self.developer, identifier, action, "Second rollout")
        plan = r.create_recovery_plan(self.developer, identifier, "Recovery handoff", "recovery-owner")
        self.assertEqual(first["deployment_id"], plan["rollback_target"])
        self.assertEqual(first["deployment_id"], plan["previous_deployment"])
        self.assertEqual(config["config_id"], plan["previous_configuration"]["config_id"])
        self.assertEqual("pending", plan["validation_status"])
        self.assertIn("recovery_validation", [b["check"] for b in r.reliability_check(self.developer, identifier)["blocked"]])
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        verified = r.verify_recovery(self.developer, plan["plan_id"], actor="verifier")
        self.assertEqual("passed", verified["validation_status"])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertFalse(r.reliability_check(self.developer, identifier)["blocked"])
        self.assertEqual(identifier, d.deployment_status(self.developer)["active_deployment"])
        incident = o.create_incident(self.developer, identifier, "Investigate rollout")["operation_id"]
        inspection = r.recovery_plan_inspect(self.developer, plan["plan_id"])
        self.assertEqual(incident, inspection["incident_history"][0]["operation_id"])
        self.assertEqual(d.deployment_audit(self.developer, identifier)["events"], inspection["audit_history"])
        d.transition_deployment(self.developer, identifier, "rollback", "Explicit manual recovery")
        audit = d.deployment_audit(self.developer, identifier)["events"][-1]
        o.transition_incident(self.developer, incident, "resolved", "Verified rollback", recovery_action="Manual rollback",
                              rollback_reference=audit["event_id"])
        self.assertEqual("failed", r.verify_recovery(self.developer, plan["plan_id"])["validation_status"])
        self.assertEqual(first["deployment_id"], d.deployment_status(self.developer)["active_deployment"])
        self.assertEqual(audit["event_id"], o.recovery_history(self.developer)["resolution_history"][0]["rollback_reference"])

    def test_reliability_live_governance_and_previous_configuration_validation(self):
        from src.developer import reliability as r, deployment as d, configuration as c
        source, config, first = self._deployment_setup()
        for action in ("validate", "activate"):
            d.transition_deployment(self.developer, first["deployment_id"], action, "First rollout")
        second = self._next_deployment(source)
        d.transition_deployment(self.developer, second["deployment_id"], "validate", "Validate second")
        plan = r.create_recovery_plan(self.developer, second["deployment_id"], "Recovery")
        r.verify_recovery(self.developer, plan["plan_id"])
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            report = r.reliability_check(self.developer, second["deployment_id"])
            self.assertIn("governance", [b["check"] for b in report["blocked"]])
            failed = r.verify_recovery(self.developer, plan["plan_id"])
            self.assertEqual("failed", failed["validation_status"])
        c.transition_configuration(self.developer, config["config_id"], "retire", "Withdraw rollback config")
        failed = r.verify_recovery(self.developer, plan["plan_id"])
        self.assertIn("previous_configuration", [b["check"] for b in failed["verification"]["blocked"]])
        self.assertEqual(["pending", "passed", "failed", "failed"], [h["status"] for h in failed["history"]])
        self.assertTrue(failed["history"][1]["verification"]["passed"])

    def test_reliability_atomic_failures_and_interrupted_check_resume(self):
        from src.developer import reliability as r
        _, _, deployed = self._deployment_setup()
        identifier = r.create_readiness(self.developer, deployed["deployment_id"], "Check")["readiness_id"]
        before = r._load(self.developer)
        with patch("src.developer.reliability.os.link", side_effect=FileExistsError("Competing writer")):
            with self.assertRaises(LocalWorkflowError):
                r.check_readiness(self.developer, identifier)
        self.assertEqual(before, r._load(self.developer))
        real_link = r.os.link
        calls = []
        def fail_outcome(source, target):
            calls.append(target)
            if len(calls) == 2:
                raise FileExistsError("Interrupted outcome")
            return real_link(source, target)
        with patch("src.developer.reliability.os.link", side_effect=fail_outcome):
            with self.assertRaises(LocalWorkflowError):
                r.check_readiness(self.developer, identifier)
        self.assertEqual("checking", r._load(self.developer)["readiness"][0]["status"])
        result = r.check_readiness(self.developer, identifier)
        self.assertEqual(["pending", "checking", "failed"], [h["status"] for h in result["history"]])
        directory = self.workspace_path / "optimization" / "reliability"
        self.assertFalse(list(directory.glob("*.tmp")))
        result["history"].clear()
        self.assertTrue(r._load(self.developer)["readiness"][0]["history"])

    def test_reliability_corrupt_journals_are_blocked_and_reads_do_not_repair(self):
        from src.developer import reliability as r, operations as o
        _, _, deployed = self._deployment_setup()
        identifier = deployed["deployment_id"]
        plan = r.create_recovery_plan(self.developer, identifier, "Prepare recovery")
        r.verify_recovery(self.developer, plan["plan_id"])
        o.create_incident(self.developer, identifier, "Issue")
        for subdirectory, name, check in (("operations", "00000001.json", "incident_consistency"),
                                          ("deployments", "00000002.json", "audit_completeness"),
                                          ("reliability", "00000002.json", "recovery_plan")):
            path = self.workspace_path / "optimization" / subdirectory / name
            original = path.read_bytes()
            path.write_text("{}", encoding="utf-8")
            before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
            report = r.reliability_check(self.developer, identifier)
            self.assertIn(check, [b["check"] for b in report["blocked"]])
            self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
            path.write_bytes(original)
        path = self.workspace_path / "optimization" / "reliability" / "00000002.json"
        original = json.loads(path.read_text())
        from copy import deepcopy
        for key, value in (("previous_digest", "wrong"), ("identifier", "missing"),
                           ("created_at", "2026-09-29T00:00:00"), ("verification", {"passed": [], "warnings": [], "blocked": []})):
            event = deepcopy(original)
            event[key] = value
            path.write_text(json.dumps(event), encoding="utf-8")
            with self.assertRaisesRegex(LocalWorkflowError, "Invalid reliability journal"):
                r.recovery_plan_status(self.developer)
        path.write_text(json.dumps(original), encoding="utf-8")
        (path.parent / "00000001.json").unlink()
        with self.assertRaisesRegex(LocalWorkflowError, "journal chain"):
            r.readiness_status(self.developer)

    def test_reliability_empty_unknown_and_external_workspace_isolation(self):
        from src.developer import reliability as r
        self.assertEqual([], r.readiness_status(self.developer)["readiness"])
        self.assertEqual([], r.recovery_plan_status(self.developer)["plans"])
        for reader in (r.reliability_check, r.recovery_plan_inspect, r.verify_recovery):
            with self.assertRaises(LocalWorkflowError):
                reader(self.developer, "missing")
        self.assertFalse(self.workspace_path.exists())
        for root in (local_workflow._PROJECT_ROOT / "reliability-records", self.research_root / "reliability-records"):
            isolated = DeveloperWorkspace(root, (self.research_root,))
            for reader in (r.readiness_status, r.recovery_plan_status):
                with self.assertRaises(LocalWorkflowError):
                    reader(isolated)
            for action in (r.create_readiness, r.create_recovery_plan):
                with self.assertRaises(LocalWorkflowError):
                    action(isolated, "missing", "Must not write")
            with self.assertRaises(LocalWorkflowError):
                r.reliability_check(isolated, "missing")
            self.assertFalse(root.exists())

    def test_reliability_cli_plan_handoff_and_read_only_reports(self):
        from src.developer import deployment as d
        _, _, deployed = self._deployment_setup()
        identifier = deployed["deployment_id"]
        d.transition_deployment(self.developer, identifier, "validate", "Validated prerequisite")
        def run(command, *args):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main(["local", command, *args, "--workspace", str(self.workspace_path), "--json"]))
            return json.loads(output.getvalue())
        plan = run("recovery-plan-create", identifier, "--reason", "Prepare", "--owner", "first-owner")
        replacement = run("recovery-plan-create", identifier, "--reason", "Handoff", "--owner", "second-owner")
        plans = run("recovery-plan-status")["plans"]
        self.assertFalse(plans[0]["active"])
        self.assertTrue(plans[1]["active"])
        self.assertEqual("first-owner", plans[0]["owner"])
        verified = run("recovery-verify", replacement["plan_id"])
        self.assertEqual("passed", verified["validation_status"])
        ready = run("readiness-create", identifier, "--reason", "Assess")
        self.assertEqual("passed", run("readiness-check", ready["readiness_id"])["status"])
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        report = run("reliability-check", identifier)
        self.assertFalse(report["blocked"])
        self.assertEqual(replacement["plan_id"], report["evidence"]["plan"]["plan_id"])
        self.assertEqual("second-owner", run("recovery-plan-inspect", replacement["plan_id"])["plan"]["owner"])
        self.assertEqual(plan["plan_id"], run("recovery-plan-inspect", plan["plan_id"])["plan"]["plan_id"])
        self.assertTrue(run("readiness-status")["readiness"][0]["evidence_current"])
        self.assertTrue(run("recovery-plan-status")["plans"][1]["verification_current"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        self.assertEqual("expired", run("readiness-expire", ready["readiness_id"], "--reason", "End handoff window")["status"])
        self.assertFalse(self.research_root.exists())

    def _assurance_setup(self, simulate=True):
        from src.developer import continuity as c
        _, config, deployed, plan = self._continuity_setup()
        scenario = c.create_scenario(self.developer, deployed["deployment_id"], "Prepare assurance", "scenario-owner")
        if simulate:
            c.test_scenario(self.developer, scenario["scenario_id"])
        return config, deployed, plan, scenario

    def test_assurance_creation_lifecycle_and_immutable_evidence(self):
        from src.developer import assurance as a, deployment as d
        _, deployed, plan, scenario = self._assurance_setup()
        record = a.create_assurance(self.developer, scenario["scenario_id"], "Capture assurance", "assurance-owner")
        self.assertEqual("pending", record["status"])
        self.assertEqual([], record["checks"])
        self.assertEqual(scenario["scenario_id"], record["scenario_id"])
        self.assertEqual("assurance-owner", record["owner"])
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        verified = a.verify_assurance(self.developer, record["assurance_id"])
        self.assertEqual("passed", verified["status"])
        self.assertEqual(["pending", "verifying", "passed"], [h["status"] for h in verified["history"]])
        self.assertEqual(list(a.EVIDENCE_TYPES), [e["evidence_type"] for e in verified["evidence"]])
        evidence = {e["evidence_type"]: e for e in verified["evidence"]}
        self.assertEqual(plan["plan_id"], evidence["rollback_reference"]["source"])
        self.assertEqual(d.deployment_audit(self.developer, deployed["deployment_id"])["events"],
                         evidence["deployment_audit"]["content"]["record"])
        self.assertTrue(all(e["status"] == "available" and e["checked_at"] and e["expires_at"] for e in verified["evidence"]))
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        before_evidence = verified["evidence"]
        expired = a.transition_assurance(self.developer, record["assurance_id"], "expired", "End assurance window")
        self.assertEqual(before_evidence, expired["evidence"])
        self.assertEqual(len(a.EVIDENCE_TYPES), len(a.recovery_evidence(self.developer, scenario["scenario_id"])["expired"]))
        expired["evidence"][0]["status"] = "mutated"
        self.assertEqual("available", a._load(self.developer)["assurances"][0]["evidence"][0]["status"])

    def test_assurance_invalid_transitions_and_missing_simulation_warnings(self):
        from src.developer import assurance as a
        _, _, _, scenario = self._assurance_setup(simulate=False)
        identifier = a.create_assurance(self.developer, scenario["scenario_id"], "Prepare")["assurance_id"]
        for status in ("pending", "passed", "failed", "unknown"):
            with self.assertRaises(LocalWorkflowError):
                a.transition_assurance(self.developer, identifier, status, "Invalid")
        a.transition_assurance(self.developer, identifier, "verifying", "Start")
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        with self.assertRaisesRegex(LocalWorkflowError, "outcome"):
            a.transition_assurance(self.developer, identifier, "passed", "Cannot force pass")
        for kwargs in ({"owner": " "}, {"actor": ""}, {"valid_for_hours": 0}, {"valid_for_hours": True},
                       {"valid_for_hours": 8761}, {"valid_for_hours": 1.5}):
            with self.assertRaises(LocalWorkflowError):
                a.create_assurance(self.developer, scenario["scenario_id"], "Invalid", **kwargs)
        with self.assertRaises(LocalWorkflowError):
            a.create_assurance(self.developer, scenario["scenario_id"], "")
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        report = a.recovery_evidence(self.developer, scenario["scenario_id"])
        self.assertEqual(["previous_simulations"], [e["evidence_type"] for e in report["missing"]])
        self.assertTrue(report["warnings"])
        result = a.verify_assurance(self.developer, identifier)
        self.assertEqual("failed", result["status"])
        self.assertIn("previous_checks", [c["check"] for c in result["checks"] if c["status"] == "blocked"])
        with self.assertRaises(LocalWorkflowError):
            a.verify_assurance(self.developer, identifier)
        a.transition_assurance(self.developer, identifier, "expired", "Replace")
        for status in a.STATES:
            with self.assertRaises(LocalWorkflowError):
                a.transition_assurance(self.developer, identifier, status, "Expired is terminal")

    def test_assurance_time_expiration_is_read_only_and_new_evidence_can_replace_it(self):
        from datetime import datetime, timedelta, timezone
        from src.developer import assurance as a
        _, _, _, scenario = self._assurance_setup()
        start = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
        with patch("src.developer.assurance._now", return_value=start):
            record = a.create_assurance(self.developer, scenario["scenario_id"], "One hour", valid_for_hours=1)
            a.verify_assurance(self.developer, record["assurance_id"])
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        with patch("src.developer.assurance._now", return_value=start + timedelta(minutes=59)):
            self.assertFalse(a.recovery_evidence(self.developer, scenario["scenario_id"])["expired"])
        with patch("src.developer.assurance._now", return_value=start + timedelta(hours=1)):
            report = a.recovery_assurance(self.developer, scenario["scenario_id"])
            self.assertEqual("expired", report["recovery_readiness"])
            self.assertEqual("passed", report["assurances"][0]["status"])
            self.assertEqual(len(a.EVIDENCE_TYPES), len(report["evidence"]["expired"]))
            self.assertIn("evidence_current", [b["check"] for b in a.recovery_verify_history(self.developer, scenario["scenario_id"])["blocked"]])
            self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
            new = a.create_assurance(self.developer, scenario["scenario_id"], "Renew")
            self.assertEqual("passed", a.verify_assurance(self.developer, new["assurance_id"])["status"])
            self.assertEqual("passed", a.recovery_assurance(self.developer, scenario["scenario_id"])["recovery_readiness"])

    def test_assurance_source_changes_expire_evidence_without_rewriting_history(self):
        from src.developer import assurance as a, continuity as c, operations as o
        _, deployed, _, scenario = self._assurance_setup()
        identifier = a.create_assurance(self.developer, scenario["scenario_id"], "Capture")["assurance_id"]
        a.verify_assurance(self.developer, identifier)
        first = a.recovery_evidence(self.developer, scenario["scenario_id"])
        second = a.recovery_evidence(self.developer, scenario["scenario_id"])
        self.assertEqual([e["content_digest"] for e in first["available"]], [e["content_digest"] for e in second["available"]])
        saved = a._load(self.developer)
        incident = o.create_incident(self.developer, deployed["deployment_id"], "New investigation")
        changed = a.recovery_assurance(self.developer, scenario["scenario_id"])
        self.assertEqual("expired", changed["recovery_readiness"])
        self.assertEqual(saved, a._load(self.developer))
        self.assertTrue(changed["verification"]["blocked"])
        o.transition_incident(self.developer, incident["operation_id"], "resolved", "Reviewed", recovery_action="Verified manually")
        c.test_scenario(self.developer, scenario["scenario_id"])
        replacement = a.create_assurance(self.developer, scenario["scenario_id"], "New observation")
        a.verify_assurance(self.developer, replacement["assurance_id"])
        self.assertFalse(a.recovery_verify_history(self.developer, scenario["scenario_id"])["blocked"])
        self.assertEqual(1, len(a.recovery_history_analysis(self.developer)["recovery_history"]["resolution_history"]))

    def test_assurance_missing_evidence_and_lost_continuity_fail_closed(self):
        from src.developer import assurance as a
        _, _, _, scenario = self._assurance_setup()
        identifier = a.create_assurance(self.developer, scenario["scenario_id"], "Preserve evidence")["assurance_id"]
        a.verify_assurance(self.developer, identifier)
        retained = a._load(self.developer)
        for folder, kind in (("reliability", "recovery_plan"), ("configurations", "configuration_history"),
                             ("deployments", "deployment_audit"), ("continuity", "continuity_record")):
            directory = self.workspace_path / "optimization" / folder
            path = sorted(directory.glob("*.json"))[-1]
            original = path.read_bytes()
            path.write_text("{}", encoding="utf-8")
            before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
            evidence = a.recovery_evidence(self.developer, scenario["scenario_id"])
            self.assertIn(kind, [e["evidence_type"] for e in evidence["missing"]])
            self.assertTrue(evidence["warnings"])
            self.assertTrue(a.recovery_verify_history(self.developer, scenario["scenario_id"])["blocked"])
            self.assertEqual(retained, a._load(self.developer))
            self.assertTrue(a.recovery_history_analysis(self.developer)["unresolved_findings"])
            self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
            path.write_bytes(original)

    def test_assurance_history_analysis_preserves_failures_and_current_findings(self):
        from src.developer import assurance as a, continuity as c
        _, _, _, scenario = self._assurance_setup(simulate=False)
        first = a.create_assurance(self.developer, scenario["scenario_id"], "Before simulation")
        self.assertEqual("failed", a.verify_assurance(self.developer, first["assurance_id"])["status"])
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            self.assertEqual("failed", c.test_scenario(self.developer, scenario["scenario_id"])["status"])
        c.test_scenario(self.developer, scenario["scenario_id"])
        second = a.create_assurance(self.developer, scenario["scenario_id"], "Current evidence")
        self.assertEqual("passed", a.verify_assurance(self.developer, second["assurance_id"])["status"])
        result = a.recovery_history_analysis(self.developer)
        self.assertEqual({"simulation", "assurance"}, {f["kind"] for f in result["failures"]})
        self.assertEqual(["failed", "validated"], [t["status"] for t in result["simulation_history"]])
        self.assertTrue(all(not f["blocked"] for f in result["unresolved_findings"]))
        self.assertEqual("passed", a.recovery_assurance(self.developer, scenario["scenario_id"])["recovery_readiness"])
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            self.assertTrue(a.recovery_verify_history(self.developer, scenario["scenario_id"])["blocked"])
        c.transition_scenario(self.developer, scenario["scenario_id"], "retired", "End scenario")
        self.assertIn("scenario_state", [b["check"] for b in a.recovery_verify_history(self.developer, scenario["scenario_id"])["blocked"]])

    def test_assurance_atomic_interruption_and_evidence_corruption(self):
        from src.developer import assurance as a
        from copy import deepcopy
        _, _, _, scenario = self._assurance_setup()
        with patch("src.developer.assurance.os.link", side_effect=FileExistsError("Competing writer")):
            with self.assertRaises(LocalWorkflowError):
                a.create_assurance(self.developer, scenario["scenario_id"], "Attempt")
        self.assertEqual([], a._load(self.developer)["assurances"])
        identifier = a.create_assurance(self.developer, scenario["scenario_id"], "Capture")["assurance_id"]
        real_link, calls = a.os.link, []
        def fail_outcome(source, target):
            calls.append(target)
            if len(calls) == 2:
                raise FileExistsError("Interrupted outcome")
            return real_link(source, target)
        with patch("src.developer.assurance.os.link", side_effect=fail_outcome):
            with self.assertRaises(LocalWorkflowError):
                a.verify_assurance(self.developer, identifier)
        self.assertEqual("verifying", a._load(self.developer)["assurances"][0]["status"])
        self.assertEqual([], a._load(self.developer)["assurances"][0]["evidence"])
        self.assertEqual("passed", a.verify_assurance(self.developer, identifier)["status"])
        directory = self.workspace_path / "optimization" / "assurance"
        self.assertFalse(list(directory.glob("*.tmp")))
        tail = directory / "00000003.json"
        original = json.loads(tail.read_text())
        mutations = [("content_digest", "wrong"), ("expires_at", "2099-01-01T00:00:00+00:00"),
                     ("status", "expired"), ("evidence_id", "wrong")]
        for field, value in mutations:
            event = deepcopy(original)
            event["report"]["evidence"][0][field] = value
            tail.write_text(json.dumps(event), encoding="utf-8")
            with self.assertRaisesRegex(LocalWorkflowError, "immutable evidence"):
                a.recovery_evidence(self.developer, scenario["scenario_id"])
        tail.write_text(json.dumps(original), encoding="utf-8")
        (directory / "00000001.json").unlink()
        with self.assertRaisesRegex(LocalWorkflowError, "journal chain"):
            a.recovery_history_analysis(self.developer)

    def test_assurance_empty_unknown_and_workspace_isolation(self):
        from src.developer import assurance as a
        self.assertEqual([], a.recovery_history_analysis(self.developer)["assurance_history"])
        for reader in (a.recovery_assurance, a.recovery_evidence, a.recovery_verify_history):
            with self.assertRaises(LocalWorkflowError):
                reader(self.developer, "missing")
        with self.assertRaises(LocalWorkflowError):
            a.create_assurance(self.developer, "missing", "Unknown scenario")
        self.assertFalse(self.workspace_path.exists())
        for root in (local_workflow._PROJECT_ROOT / "assurance-records", self.research_root / "assurance-records"):
            isolated = DeveloperWorkspace(root, (self.research_root,))
            with self.assertRaises(LocalWorkflowError):
                a.recovery_history_analysis(isolated)
            with self.assertRaises(LocalWorkflowError):
                a.create_assurance(isolated, "missing", "Must not write")
            self.assertFalse(root.exists())

    def test_assurance_cli_reports_are_read_only_and_recording_is_explicit(self):
        _, _, _, scenario = self._assurance_setup()
        def run(command, *args):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main(["local", command, *args, "--workspace", str(self.workspace_path), "--json"]))
            return json.loads(output.getvalue())
        identifier = scenario["scenario_id"]
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        self.assertEqual("pending", run("recovery-assurance", identifier)["recovery_readiness"])
        self.assertFalse(run("recovery-evidence", identifier)["missing"])
        self.assertFalse(run("recovery-verify-history", identifier)["blocked"])
        self.assertEqual(1, len(run("recovery-history-analysis")["simulation_history"]))
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        self.assertFalse((self.workspace_path / "optimization" / "assurance").exists())
        record = run("assurance-create", identifier, "--reason", "Capture", "--owner", "on-call", "--valid-for-hours", "1")
        self.assertEqual("on-call", record["owner"])
        self.assertEqual("passed", run("assurance-verify", record["assurance_id"])["status"])
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        self.assertEqual("passed", run("recovery-assurance", identifier)["recovery_readiness"])
        self.assertEqual(1, len(run("recovery-evidence", identifier)["recorded"]))
        self.assertEqual(record["assurance_id"], run("recovery-verify-history", identifier)["previous_assurance"])
        self.assertFalse(run("recovery-history-analysis")["failures"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        self.assertEqual("expired", run("assurance-expire", record["assurance_id"], "--reason", "End window")["status"])
        self.assertFalse(self.research_root.exists())

    def _continuity_setup(self):
        from src.developer import deployment as d, reliability as r
        source, config, deployed = self._deployment_setup()
        d.transition_deployment(self.developer, deployed["deployment_id"], "validate", "Continuity prerequisite")
        plan = r.create_recovery_plan(self.developer, deployed["deployment_id"], "Prepare recovery", "plan-owner")
        r.verify_recovery(self.developer, plan["plan_id"])
        return source, config, deployed, plan

    def test_continuity_scenario_types_and_atomic_knowledge_capture(self):
        from src.developer import continuity as c
        _, config, deployed, plan = self._continuity_setup()
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        for kind in sorted(c.TYPES):
            scenario = c.create_scenario(self.developer, deployed["deployment_id"], "Prepare disaster", "incident-owner", kind)
            self.assertEqual(kind, scenario["type"])
            self.assertEqual("planned", scenario["status"])
            self.assertEqual("incident-owner", scenario["owner"])
            inspection = c.disaster_inspect(self.developer, scenario["scenario_id"])
            record = inspection["continuity"]
            self.assertEqual(scenario["continuity_id"], record["continuity_id"])
            self.assertEqual(plan["plan_id"], record["recovery_plan"])
            self.assertEqual([deployed["deployment_id"]], record["deployment_dependencies"])
            self.assertEqual([config["config_id"]], record["configuration_dependencies"])
            self.assertTrue(record["knowledge"]["audit_history"])
            self.assertTrue(record["knowledge"]["restoration_steps"])
            self.assertEqual("pending", record["validation_status"])
        self.assertEqual(4, len(c.continuity_status(self.developer)["continuity"]))
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        scenario["history"].clear()
        self.assertTrue(c.disaster_inspect(self.developer, scenario["scenario_id"])["scenario"]["history"])

    def test_continuity_lifecycle_attempts_and_no_recovery_execution(self):
        from src.developer import continuity as c, deployment as d, reliability as r
        _, _, deployed, plan = self._continuity_setup()
        identifier = c.create_scenario(self.developer, deployed["deployment_id"], "Plan", "incident-owner")["scenario_id"]
        directory = self.workspace_path / "optimization" / "continuity"
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        result = c.test_scenario(self.developer, identifier, "Validate preparation", "test-operator")
        self.assertEqual("validated", result["status"])
        attempt = result["tests"][0]
        self.assertEqual("incident-owner", attempt["owner"])
        self.assertEqual("test-operator", attempt["actor"])
        self.assertEqual("reference_validation_only", attempt["method"])
        self.assertTrue(attempt["test_date"])
        self.assertTrue(attempt["findings"])
        self.assertTrue(attempt["validation_results"]["warnings"])  # Explicit empty initial rollback.
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertIsNone(d.deployment_status(self.developer)["active_deployment"])
        self.assertEqual("passed", r.recovery_plan_status(self.developer)["plans"][0]["validation_status"])
        self.assertTrue(c.disaster_status(self.developer)["scenarios"][0]["evidence_current"])
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            failed = c.test_scenario(self.developer, identifier, "Approval withdrawn")
        self.assertEqual("failed", failed["status"])
        retry = c.test_scenario(self.developer, identifier, "Evidence restored")
        self.assertEqual(["validated", "failed", "validated"], [a["status"] for a in retry["tests"]])
        knowledge = c.continuity_status(self.developer)["continuity"][0]
        self.assertEqual(3, len([h for h in knowledge["history"] if "validation_attempt" in h]))
        retired = c.transition_scenario(self.developer, identifier, "retired", "End exercise")
        self.assertEqual("retired", retired["status"])
        self.assertFalse(c.disaster_status(self.developer)["scenarios"][0]["active"])
        self.assertFalse(list(directory.glob("*.tmp")))

    def test_continuity_invalid_transitions_ownership_and_plan_links(self):
        from src.developer import continuity as c, reliability as r
        _, _, deployed = self._deployment_setup()
        with self.assertRaisesRegex(LocalWorkflowError, "recovery plan"):
            c.create_scenario(self.developer, deployed["deployment_id"], "No plan")
        self.assertFalse((self.workspace_path / "optimization" / "continuity").exists())
        r.create_recovery_plan(self.developer, deployed["deployment_id"], "Unverified plan")
        identifier = c.create_scenario(self.developer, deployed["deployment_id"], "Prepare")["scenario_id"]
        for status in ("planned", "validated", "failed", "unknown"):
            with self.assertRaises(LocalWorkflowError):
                c.transition_scenario(self.developer, identifier, status, "Invalid")
        c.transition_scenario(self.developer, identifier, "testing", "Start validation")
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        with self.assertRaisesRegex(LocalWorkflowError, "outcome"):
            c.transition_scenario(self.developer, identifier, "validated", "Cannot force validation")
        for kwargs in ({"owner": " "}, {"scenario_type": "unknown"}, {"actor": ""},
                       {"plan_id": "missing"}, {"restoration_steps": []}, {"restoration_steps": [""]}):
            with self.assertRaises(LocalWorkflowError):
                c.create_scenario(self.developer, deployed["deployment_id"], "Invalid", **kwargs)
        with self.assertRaises(LocalWorkflowError):
            c.create_scenario(self.developer, deployed["deployment_id"], "")
        with self.assertRaises(LocalWorkflowError):
            c.create_scenario(self.developer, "missing", "Unknown deployment")
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        self.assertEqual("failed", c.test_scenario(self.developer, identifier)["status"])
        c.transition_scenario(self.developer, identifier, "retired", "End")
        for status in c.STATES:
            with self.assertRaises(LocalWorkflowError):
                c.transition_scenario(self.developer, identifier, status, "Retired is terminal")
        with self.assertRaises(LocalWorkflowError):
            c.test_scenario(self.developer, identifier)

    def test_continuity_nonempty_dependencies_and_existing_rollback_compatibility(self):
        from src.developer import continuity as c, deployment as d, reliability as r, operations as o
        source, config, first, first_plan = self._continuity_setup()
        d.transition_deployment(self.developer, first["deployment_id"], "activate", "First rollout")
        second = self._next_deployment(source)
        for action in ("validate", "activate"):
            d.transition_deployment(self.developer, second["deployment_id"], action, "Second rollout")
        with self.assertRaisesRegex(LocalWorkflowError, "recovery plan"):
            c.create_scenario(self.developer, second["deployment_id"], "Wrong plan", plan_id=first_plan["plan_id"])
        plan = r.create_recovery_plan(self.developer, second["deployment_id"], "Second recovery")
        r.verify_recovery(self.developer, plan["plan_id"])
        identifier = c.create_scenario(self.developer, second["deployment_id"], "Prepare")["scenario_id"]
        report = c.disaster_check(self.developer, identifier)
        self.assertFalse(report["blocked"])
        self.assertFalse(report["warnings"])
        self.assertEqual(first["deployment_id"], report["evidence"]["rollback_deployment"]["deployment_id"])
        record = c.continuity_status(self.developer)["continuity"][0]
        self.assertEqual([second["config_id"], config["config_id"]], record["configuration_dependencies"])
        prior = d.deployment_history(self.developer)
        c.test_scenario(self.developer, identifier)
        self.assertEqual(prior, d.deployment_history(self.developer))
        incident = o.create_incident(self.developer, second["deployment_id"], "Actual incident")["operation_id"]
        self.assertFalse(c.disaster_status(self.developer)["scenarios"][0]["evidence_current"])
        d.transition_deployment(self.developer, second["deployment_id"], "rollback", "Explicit recovery")
        audit = d.deployment_audit(self.developer, second["deployment_id"])["events"][-1]
        o.transition_incident(self.developer, incident, "resolved", "Recovered", recovery_action="Manual rollback",
                              rollback_reference=audit["event_id"])
        self.assertEqual("failed", c.test_scenario(self.developer, identifier)["status"])
        self.assertEqual(first["deployment_id"], d.deployment_status(self.developer)["active_deployment"])
        self.assertEqual("validated", c.continuity_status(self.developer)["continuity"][0]["history"][2]["status"])

    def test_continuity_missing_dependencies_preserve_knowledge_and_report_blockers(self):
        from src.developer import continuity as c
        _, _, deployed, _ = self._continuity_setup()
        identifier = c.create_scenario(self.developer, deployed["deployment_id"], "Capture history")["scenario_id"]
        saved = c.continuity_status(self.developer)
        for folder, check in (("reliability", "recovery_plan"), ("deployments", "deployment_history"),
                              ("configurations", "configuration_history")):
            directory = self.workspace_path / "optimization" / folder
            path = sorted(directory.glob("*.json"))[-1]
            original = path.read_bytes()
            path.write_text("{}", encoding="utf-8")
            before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
            report = c.disaster_check(self.developer, identifier)
            self.assertIn(check, [b["check"] for b in report["blocked"]])
            self.assertEqual(saved, c.continuity_status(self.developer))
            self.assertEqual(saved["continuity"][0], c.disaster_inspect(self.developer, identifier)["continuity"])
            self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
            path.write_bytes(original)
        directory = self.workspace_path / "optimization" / "reliability"
        originals = {p: p.read_bytes() for p in directory.glob("*.json")}
        for path in originals:
            path.unlink()
        self.assertIn("recovery_plan", [b["check"] for b in c.disaster_check(self.developer, identifier)["blocked"]])
        self.assertEqual("failed", c.test_scenario(self.developer, identifier)["status"])
        for path, content in originals.items():
            path.write_bytes(content)

    def test_continuity_ownership_handoff_and_live_governance(self):
        from src.developer import continuity as c, reliability as r, configuration as config
        _, conf, deployed, plan = self._continuity_setup()
        identifier = c.create_scenario(self.developer, deployed["deployment_id"], "Original handoff", "first-owner")["scenario_id"]
        c.test_scenario(self.developer, identifier)
        replacement = r.create_recovery_plan(self.developer, deployed["deployment_id"], "New owner", "second-owner")
        r.verify_recovery(self.developer, replacement["plan_id"])
        report = c.disaster_check(self.developer, identifier)
        self.assertIn("recovery_plan", [b["check"] for b in report["blocked"]])
        original = c.disaster_inspect(self.developer, identifier)
        self.assertEqual("first-owner", original["continuity"]["owner"])
        self.assertEqual(plan["plan_id"], original["continuity"]["recovery_plan"])
        new = c.create_scenario(self.developer, deployed["deployment_id"], "New handoff", "second-owner")
        self.assertFalse(c.disaster_check(self.developer, new["scenario_id"])["blocked"])
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            self.assertIn("reliability", [b["check"] for b in c.disaster_check(self.developer, new["scenario_id"])["blocked"]])
        config.transition_configuration(self.developer, conf["config_id"], "retire", "Withdraw configuration")
        self.assertIn("reliability", [b["check"] for b in c.disaster_check(self.developer, new["scenario_id"])["blocked"]])

    def test_continuity_atomic_publication_interruption_and_corruption(self):
        from src.developer import continuity as c
        from copy import deepcopy
        _, _, deployed, _ = self._continuity_setup()
        with patch("src.developer.continuity.os.link", side_effect=FileExistsError("Competing writer")):
            with self.assertRaises(LocalWorkflowError):
                c.create_scenario(self.developer, deployed["deployment_id"], "Attempt create")
        self.assertEqual([], c._load(self.developer)["scenarios"])
        self.assertEqual([], c.continuity_status(self.developer)["continuity"])
        identifier = c.create_scenario(self.developer, deployed["deployment_id"], "Create")["scenario_id"]
        real_link, calls = c.os.link, []
        def fail_outcome(source, target):
            calls.append(target)
            if len(calls) == 2:
                raise FileExistsError("Interrupted outcome")
            return real_link(source, target)
        with patch("src.developer.continuity.os.link", side_effect=fail_outcome):
            with self.assertRaises(LocalWorkflowError):
                c.test_scenario(self.developer, identifier)
        self.assertEqual("testing", c._load(self.developer)["scenarios"][0]["status"])
        self.assertEqual([], c._load(self.developer)["scenarios"][0]["tests"])
        result = c.test_scenario(self.developer, identifier)
        self.assertEqual(["planned", "testing", "validated"], [h["status"] for h in result["history"]])
        directory = self.workspace_path / "optimization" / "continuity"
        self.assertFalse(list(directory.glob("*.tmp")))
        tail = directory / "00000003.json"
        original = json.loads(tail.read_text())
        for key, value in (("previous_digest", "wrong"), ("status", "failed"), ("actor", ""),
                           ("created_at", "2026-09-30T00:00:00"), ("report", {"passed": [], "warnings": [], "blocked": []})):
            event = deepcopy(original)
            event[key] = value
            tail.write_text(json.dumps(event), encoding="utf-8")
            with self.assertRaisesRegex(LocalWorkflowError, "Invalid continuity journal"):
                c.disaster_check(self.developer, identifier)
        tail.write_text(json.dumps(original), encoding="utf-8")
        (directory / "00000001.json").unlink()
        with self.assertRaisesRegex(LocalWorkflowError, "journal chain"):
            c.continuity_status(self.developer)

    def test_continuity_empty_unknown_and_external_workspace_isolation(self):
        from src.developer import continuity as c
        self.assertEqual([], c.disaster_status(self.developer)["scenarios"])
        self.assertEqual([], c.continuity_status(self.developer)["continuity"])
        for action in (c.disaster_check, c.disaster_inspect, c.test_scenario):
            with self.assertRaises(LocalWorkflowError):
                action(self.developer, "missing")
        self.assertFalse(self.workspace_path.exists())
        for root in (local_workflow._PROJECT_ROOT / "disaster-records", self.research_root / "disaster-records"):
            isolated = DeveloperWorkspace(root, (self.research_root,))
            for reader in (c.disaster_status, c.continuity_status):
                with self.assertRaises(LocalWorkflowError):
                    reader(isolated)
            with self.assertRaises(LocalWorkflowError):
                c.create_scenario(isolated, "missing", "Must not write")
            self.assertFalse(root.exists())

    def test_continuity_cli_read_only_checks_and_simulation_tracking(self):
        _, _, deployed, plan = self._continuity_setup()
        def run(command, *args):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main(["local", command, *args, "--workspace", str(self.workspace_path), "--json"]))
            return json.loads(output.getvalue())
        scenario = run("disaster-create", deployed["deployment_id"], "--reason", "Prepare", "--owner", "on-call",
                       "--type", "history_loss", "--plan-id", plan["plan_id"], "--step", "Inspect retained audit copies")
        identifier = scenario["scenario_id"]
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        self.assertFalse(run("disaster-check", identifier)["blocked"])
        self.assertEqual("planned", run("disaster-status")["scenarios"][0]["status"])
        inspection = run("disaster-inspect", identifier)
        self.assertEqual(["Inspect retained audit copies"], inspection["continuity"]["knowledge"]["restoration_steps"])
        self.assertEqual(plan["plan_id"], inspection["recovery_plan"]["plan_id"])
        self.assertTrue(inspection["audit_history"])
        self.assertEqual("on-call", run("continuity-status")["continuity"][0]["owner"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        self.assertEqual("validated", run("disaster-test", identifier)["status"])
        self.assertEqual("retired", run("disaster-retire", identifier, "--reason", "Exercise complete")["status"])
        self.assertFalse(self.research_root.exists())

    def _deployment_setup(self):
        from src.developer.configuration import transition_configuration
        from src.developer.deployment import stage_deployment
        source, config = self._configuration_setup()
        transition_configuration(self.developer, config["config_id"], "validate", "Deployment prerequisite")
        record = stage_deployment(self.developer, config["config_id"], "Stage approved configuration")
        return source, config, record

    def _next_deployment(self, source):
        from src.developer.configuration import create_configuration, transition_configuration
        from src.developer.deployment import stage_deployment
        config = create_configuration(self.developer, source["promotion_id"], "Next rollout snapshot")
        transition_configuration(self.developer, config["config_id"], "validate", "Validate next snapshot")
        return stage_deployment(self.developer, config["config_id"], "Stage next snapshot")

    def test_deployment_creation_staging_validation_and_activation(self):
        from src.developer.deployment import deployment_status, transition_deployment
        _, config, record = self._deployment_setup()
        self.assertEqual("staged", record["stage"])
        self.assertEqual({}, record["validation"])
        self.assertEqual(config["config_id"], record["config_id"])
        self.assertEqual(["planned", "staged"], [h["stage"] for h in record["history"]])
        self.assertIsNone(deployment_status(self.developer)["active_deployment"])
        record = transition_deployment(self.developer, record["deployment_id"], "validate", "Check rollout")
        for field in ("configuration_valid", "policy_check_passed", "rollback_available"):
            self.assertIs(True, record["validation"][field])
        self.assertIsNone(record["validation"]["previous_active_configuration"])
        self.assertEqual(config["source_promotion"], record["validation"]["source_promotion"])
        transition_deployment(self.developer, record["deployment_id"], "activate", "Explicit activation")
        self.assertEqual(record["deployment_id"], deployment_status(self.developer)["active_deployment"])

    def test_deployment_invalid_transitions_duplicates_and_attribution(self):
        from src.developer.deployment import deployment_status, transition_deployment, stage_deployment
        _, config, record = self._deployment_setup()
        identifier = record["deployment_id"]
        before = deployment_status(self.developer)
        for action in ("activate", "resume", "pause", "rollback", "unknown"):
            with self.assertRaises(LocalWorkflowError):
                transition_deployment(self.developer, identifier, action, "Invalid transition")
        with self.assertRaises(LocalWorkflowError):
            transition_deployment(self.developer, identifier, "validate", " ")
        with self.assertRaises(LocalWorkflowError):
            stage_deployment(self.developer, config["config_id"], "Duplicate")
        self.assertEqual(before, deployment_status(self.developer))
        transition_deployment(self.developer, identifier, "retire", "Close unused rollout")
        with self.assertRaises(LocalWorkflowError):
            transition_deployment(self.developer, identifier, "validate", "Retired rollout")

    def test_deployment_requires_configuration_validation_and_approval(self):
        from src.developer.configuration import transition_configuration
        from src.developer.deployment import stage_deployment, transition_deployment, deployment_status
        _, config = self._configuration_setup()
        with self.assertRaisesRegex(LocalWorkflowError, "validated configuration"):
            stage_deployment(self.developer, config["config_id"], "Draft is not ready")
        transition_configuration(self.developer, config["config_id"], "validate", "Ready")
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            with self.assertRaisesRegex(LocalWorkflowError, "approved"):
                stage_deployment(self.developer, config["config_id"], "Missing approval")
        self.assertFalse((self.workspace_path / "optimization" / "deployments").exists())
        record = stage_deployment(self.developer, config["config_id"], "Stage")
        with patch("src.developer.promotion.policy_check", return_value={"blocked": [{"check": "policy"}]}):
            with self.assertRaises(LocalWorkflowError):
                transition_deployment(self.developer, record["deployment_id"], "validate", "Blocked policy")
        transition_deployment(self.developer, record["deployment_id"], "validate", "Valid")
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            with self.assertRaises(LocalWorkflowError):
                transition_deployment(self.developer, record["deployment_id"], "activate", "Approval lost")
            self.assertTrue(deployment_status(self.developer)["blocked"])
        self.assertIsNone(deployment_status(self.developer)["active_deployment"])

    def test_deployment_rollback_preserves_history_and_configuration_journals(self):
        from src.developer.deployment import deployment_status, transition_deployment
        source, first_config, first = self._deployment_setup()
        for action in ("validate", "activate"):
            transition_deployment(self.developer, first["deployment_id"], action, "First rollout")
        second = self._next_deployment(source)
        self.assertEqual(first["deployment_id"], second["previous_deployment"])
        directory = self.workspace_path / "optimization"
        preserved = {p: p.read_bytes() for p in directory.rglob("*.json")}
        for action in ("validate", "activate"):
            second = transition_deployment(self.developer, second["deployment_id"], action, "Second rollout")
        self.assertEqual(first_config["config_id"], second["validation"]["previous_active_configuration"])
        with self.assertRaises(LocalWorkflowError):
            transition_deployment(self.developer, first["deployment_id"], "rollback", "Out of order")
        transition_deployment(self.developer, second["deployment_id"], "rollback", "Restore first rollout")
        state = deployment_status(self.developer)
        self.assertEqual(first["deployment_id"], state["active_deployment"])
        self.assertEqual(["planned", "staged", "validated", "active", "retired", "active"],
                         [h["stage"] for h in state["deployments"][0]["history"]])
        transition_deployment(self.developer, first["deployment_id"], "rollback", "Restore empty reference")
        self.assertIsNone(deployment_status(self.developer)["active_deployment"])
        transition_deployment(self.developer, second["deployment_id"], "retire", "Close rolled-back rollout")
        for path, content in preserved.items():
            self.assertEqual(content, path.read_bytes())

    def test_deployment_pause_resume_and_retirement(self):
        from src.developer.deployment import deployment_status, transition_deployment
        _, _, record = self._deployment_setup()
        identifier = record["deployment_id"]
        for action in ("validate", "activate", "pause"):
            transition_deployment(self.developer, identifier, action, "Pause lifecycle")
        state = deployment_status(self.developer)
        self.assertIsNone(state["active_deployment"])
        self.assertEqual(identifier, state["selected_deployment"])
        with self.assertRaises(LocalWorkflowError):
            transition_deployment(self.developer, identifier, "activate", "Use explicit resume")
        transition_deployment(self.developer, identifier, "resume", "Recheck and resume")
        self.assertEqual(identifier, deployment_status(self.developer)["active_deployment"])
        transition_deployment(self.developer, identifier, "retire", "Close rollout")
        self.assertIsNone(deployment_status(self.developer)["selected_deployment"])

    def test_deployment_stale_references_and_configuration_changes(self):
        from src.developer.configuration import transition_configuration
        from src.developer.deployment import transition_deployment, deployment_status
        source, config, first = self._deployment_setup()
        stale = self._next_deployment(source)
        for record in (first, stale):
            transition_deployment(self.developer, record["deployment_id"], "validate", "Validate in parallel")
        transition_deployment(self.developer, first["deployment_id"], "activate", "Select first")
        with self.assertRaisesRegex(LocalWorkflowError, "reference changed"):
            transition_deployment(self.developer, stale["deployment_id"], "activate", "Stale reference")
        fresh = self._next_deployment(source)
        transition_deployment(self.developer, fresh["deployment_id"], "validate", "Bind configuration reference")
        transition_configuration(self.developer, config["config_id"], "activate", "Independent configuration change")
        with self.assertRaisesRegex(LocalWorkflowError, "evidence changed"):
            transition_deployment(self.developer, fresh["deployment_id"], "activate", "Stale evidence")
        self.assertEqual(first["deployment_id"], deployment_status(self.developer)["active_deployment"])

    def test_deployment_rollback_rechecks_source_eligibility(self):
        from src.developer.configuration import transition_configuration
        from src.developer.deployment import transition_deployment, deployment_status
        source, config, first = self._deployment_setup()
        for action in ("validate", "activate"):
            transition_deployment(self.developer, first["deployment_id"], action, "First rollout")
        second = self._next_deployment(source)
        for action in ("validate", "activate"):
            transition_deployment(self.developer, second["deployment_id"], action, "Second rollout")
        transition_configuration(self.developer, config["config_id"], "retire", "Withdraw prior configuration")
        events = deployment_status(self.developer)["events"]
        with self.assertRaisesRegex(LocalWorkflowError, "validated configuration"):
            transition_deployment(self.developer, second["deployment_id"], "rollback", "Cannot restore withdrawn config")
        state = deployment_status(self.developer)
        self.assertEqual(events, state["events"])
        self.assertEqual(second["deployment_id"], state["active_deployment"])

    def test_deployment_diff_cli_and_audit_compatibility(self):
        from src.developer.governance import optimize_audit
        from src.developer.promotion import promotion_check
        from src.developer.configuration import transition_configuration
        _, config = self._configuration_setup()
        transition_configuration(self.developer, config["config_id"], "validate", "Prerequisite")
        def cli(*arguments):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main(("local", *arguments, "--workspace", str(self.workspace_path), "--json")))
            return json.loads(output.getvalue())
        record = cli("deploy-stage", config["config_id"], "--reason", "Stage through CLI")
        preserved = {p: p.read_bytes() for p in self.workspace_path.rglob("*.json")
                     if "deployments" not in p.parts}
        identifier = record["deployment_id"]
        for command in ("deploy-validate", "deploy-activate", "deploy-pause", "deploy-resume"):
            cli(command, identifier, "--reason", "Explicit rollout action")
        status = cli("deploy-status")
        self.assertEqual(identifier, status["active_deployment"])
        diff = cli("deploy-diff", identifier, identifier)
        for section in ("configuration", "deployment", "validation", "lifecycle"):
            self.assertEqual({"added": [], "removed": [], "changed": []}, diff[section])
        self.assertEqual("clean", optimize_audit(self.developer)["audit_status"])
        self.assertFalse(promotion_check(self.developer)["blocked"])
        cli("deploy-rollback", identifier, "--reason", "Rollback through CLI")
        cli("deploy-retire", identifier, "--reason", "Retire through CLI")
        for path, content in preserved.items():
            self.assertEqual(content, path.read_bytes())

    def test_deployment_comparison_reports_lifecycle_and_validation_changes(self):
        from src.developer.deployment import transition_deployment, deployment_diff
        source, _, first = self._deployment_setup()
        transition_deployment(self.developer, first["deployment_id"], "validate", "Validate first")
        second = self._next_deployment(source)
        diff = deployment_diff(self.developer, first["deployment_id"], second["deployment_id"])
        self.assertTrue(diff["configuration"]["changed"])
        self.assertTrue(diff["deployment"]["changed"])
        self.assertTrue(diff["validation"]["removed"])
        self.assertTrue(diff["lifecycle"]["changed"])
        with self.assertRaises(LocalWorkflowError):
            deployment_diff(self.developer, first["deployment_id"], "missing")

    def test_deployment_atomic_publication_corruption_and_isolation(self):
        from src.developer.deployment import deployment_status, transition_deployment
        from src.developer.local_workflow import _PROJECT_ROOT
        self.assertFalse(deployment_status(self.developer)["deployments"])
        self.assertFalse(self.workspace_path.exists())
        for root in (_PROJECT_ROOT / "deployment-records", self.research_root / "deployment-records"):
            with self.assertRaises(LocalWorkflowError):
                deployment_status(DeveloperWorkspace(root, (self.research_root,)))
            self.assertFalse(root.exists())
        _, _, record = self._deployment_setup()
        before = deployment_status(self.developer)
        with patch("src.developer.deployment.os.link", side_effect=FileExistsError("Competing writer")):
            with self.assertRaisesRegex(LocalWorkflowError, "Cannot append"):
                transition_deployment(self.developer, record["deployment_id"], "validate", "Try write")
        self.assertEqual(before, deployment_status(self.developer))
        directory = self.workspace_path / "optimization" / "deployments"
        self.assertFalse(list(directory.glob("*.tmp")))
        path = sorted(directory.glob("*.json"))[-1]
        event = json.loads(path.read_text())
        event["previous_digest"] = "broken"
        path.write_text(json.dumps(event))
        original = path.read_bytes()
        with self.assertRaisesRegex(LocalWorkflowError, "Invalid deployment journal"):
            deployment_status(self.developer)
        self.assertEqual(original, path.read_bytes())

    def test_deployment_partial_staging_can_resume_without_rewriting_plan(self):
        from src.developer import deployment
        from src.developer.configuration import transition_configuration
        _, config = self._configuration_setup()
        transition_configuration(self.developer, config["config_id"], "validate", "Prerequisite")
        real_link = deployment.os.link
        calls = []
        def fail_staging(source, target):
            calls.append(target)
            if len(calls) == 2:
                raise OSError("Stage publication failed")
            return real_link(source, target)
        with patch("src.developer.deployment.os.link", side_effect=fail_staging):
            with self.assertRaisesRegex(LocalWorkflowError, "Cannot append"):
                deployment.stage_deployment(self.developer, config["config_id"], "Initial staging attempt")
        state = deployment.deployment_status(self.developer)
        self.assertEqual(["planned"], [d["stage"] for d in state["deployments"]])
        directory = self.workspace_path / "optimization" / "deployments"
        planned_path = next(directory.glob("*.json"))
        original = planned_path.read_bytes()
        record = deployment.stage_deployment(self.developer, config["config_id"], "Retry staging")
        self.assertEqual("staged", record["stage"])
        self.assertEqual("deployment-001", record["deployment_id"])
        self.assertEqual(original, planned_path.read_bytes())
        self.assertEqual({}, record["validation"])

    def test_promotion_creation_transitions_and_append_only_history(self):
        from src.developer.promotion import create_promotion, transition_promotion, active_configuration
        candidate, _ = self._promotion_setup()
        record = create_promotion(self.developer, candidate["id"])
        self.assertEqual("pending", record["status"])
        self.assertEqual("developer", record["approved_by"])
        directory = self.workspace_path / "optimization" / "promotions"
        first = next(directory.glob("*.json"))
        saved = first.read_bytes()
        self.assertFalse(active_configuration(self.developer)["entries"])
        with self.assertRaisesRegex(LocalWorkflowError, "Invalid promotion transition"):
            transition_promotion(self.developer, record["promotion_id"], "promoted")
        transition_promotion(self.developer, record["promotion_id"], "validated")
        record = transition_promotion(self.developer, record["promotion_id"], "promoted")
        self.assertEqual(["pending", "validated", "promoted"], [h["status"] for h in record["history"]])
        self.assertEqual(saved, first.read_bytes())
        self.assertEqual([candidate["id"]], active_configuration(self.developer)["active_candidates"])

    def test_promotion_cli_runtime_retirement_and_review_governance_compatibility(self):
        from src.developer.promotion import active_configuration, retrieval_settings
        from src.developer.governance import optimize_audit
        from src.developer.review import policy_check
        from src.developer.ranking import rank_developer_results
        with self.source_path.open("a", encoding="utf-8") as stream:
            stream.write("\ndef wrapper(headers):\n    return load_session_token(headers)\n")
        candidate, cases = self._promotion_setup()
        original = self.source_path.read_bytes()
        with redirect_stdout(StringIO()) as output:
            self.assertEqual(0, main(("local", "optimize-promote", candidate["id"],
                                     "--workspace", str(self.workspace_path), "--json")))
        record = json.loads(output.getvalue())
        self.assertEqual("promoted", record["status"])
        self.assertEqual({}, retrieval_settings(self.developer, "another-repository"))
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()), \
                patch("src.developer.ranking.rank_developer_results", wraps=rank_developer_results) as ranking:
            queried = self.developer.query("load_session_token", self.repository)
            self.assertTrue(any(row["ranking_reason"]["relationship_factor"] == 1.5
                                for row in queried["results"]))
            self.developer.trace("load_session_token", self.repository)
            self.developer.diagnose("session", cases, self.repository)
        self.assertEqual(3, ranking.call_count)
        self.assertTrue(all(c.args[-1] == {"relationship_factor": 1.5} for c in ranking.call_args_list))
        self.assertEqual("clean", optimize_audit(self.developer)["audit_status"])
        self.assertFalse(policy_check(self.developer)["blocked"])
        for command in ("optimize-promotion-status", "optimize-promotion-check"):
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(0, main(("local", command, "--workspace", str(self.workspace_path), "--json")))
            payload = json.loads(output.getvalue())
            if command.endswith("check"):
                self.assertFalse(payload["blocked"], payload)
            else:
                self.assertEqual(1, len(payload["active_promotions"]))
        with redirect_stdout(StringIO()) as output:
            self.assertEqual(0, main(("local", "optimize-retire", candidate["id"],
                                     "--workspace", str(self.workspace_path), "--json")))
        self.assertEqual("retired", json.loads(output.getvalue())["history"][-1]["status"])
        self.assertFalse(active_configuration(self.developer)["entries"])
        self.assertEqual(original, self.source_path.read_bytes())
        self.assertFalse(self.research_root.exists())

    def test_promotion_rollback_restores_exact_configuration(self):
        from src.developer.promotion import promote, active_configuration, promotion_status, retire
        candidate, _ = self._promotion_setup()
        previous = active_configuration(self.developer)
        record = promote(self.developer, candidate["id"])
        with redirect_stdout(StringIO()) as output:
            self.assertEqual(0, main(("local", "optimize-promote-rollback", record["promotion_id"],
                                     "--workspace", str(self.workspace_path), "--json")))
        self.assertEqual("rolled_back", json.loads(output.getvalue())["status"])
        self.assertEqual(previous, active_configuration(self.developer))
        self.assertEqual(1, len(promotion_status(self.developer)["rollback_history"]))
        retire(self.developer, record["promotion_id"])
        self.assertEqual(1, len(promotion_status(self.developer)["retired_promotions"]))

    def test_promotion_rollback_order_preserves_other_repositories(self):
        from src.developer.promotion import promote, rollback, active_configuration, transition_promotion
        first, _ = self._promotion_setup()
        initial = active_configuration(self.developer)
        first_promotion = promote(self.developer, first["id"])
        first_config = active_configuration(self.developer)
        second_repository = self.root / "second-repository"
        shutil.copytree(self.repository, second_repository)
        self.repository = second_repository
        second, _ = self._promotion_setup("second-promotion")
        second_promotion = promote(self.developer, second["id"])
        self.assertEqual(2, len(active_configuration(self.developer)["entries"]))
        with self.assertRaisesRegex(LocalWorkflowError, "undo later changes"):
            rollback(self.developer, first_promotion["promotion_id"])
        with self.assertRaisesRegex(LocalWorkflowError, "undo later changes"):
            transition_promotion(self.developer, first_promotion["promotion_id"], "paused")
        rollback(self.developer, second_promotion["promotion_id"])
        self.assertEqual(first_config, active_configuration(self.developer))
        rollback(self.developer, first_promotion["promotion_id"])
        self.assertEqual(initial, active_configuration(self.developer))

    def test_promotion_atomic_publication_failure_preserves_active_state(self):
        from src.developer.promotion import promote, active_configuration, promotion_status, transition_promotion
        candidate, _ = self._promotion_setup()
        with patch("src.developer.promotion.os.link", side_effect=OSError("publication failed")):
            with self.assertRaisesRegex(LocalWorkflowError, "Cannot append"):
                promote(self.developer, candidate["id"])
        self.assertFalse(active_configuration(self.developer)["entries"])
        self.assertFalse(promotion_status(self.developer)["promotions"])
        self.assertFalse(list((self.workspace_path / "optimization" / "promotions").glob("*.tmp")))
        record = promote(self.developer, candidate["id"])
        prior = active_configuration(self.developer)
        with patch("src.developer.promotion.os.link", side_effect=FileExistsError("competing writer")):
            with self.assertRaises(LocalWorkflowError):
                transition_promotion(self.developer, record["promotion_id"], "retired")
        self.assertEqual(prior, active_configuration(self.developer))

    def test_promotion_requires_approval_settings_and_valid_policy(self):
        from src.developer.promotion import promote
        from src.developer.review import create_review, approve_review
        from src.developer.governance import transition_candidate
        _, _, candidate = self._optimization_setup()
        with self.assertRaises(LocalWorkflowError):
            promote(self.developer, "missing")
        with self.assertRaisesRegex(LocalWorkflowError, "approved"):
            promote(self.developer, candidate["id"])
        self._register_passed_lifecycle_validation(candidate)
        review = create_review(self.developer, candidate["id"], "Review legacy proposal")
        approve_review(self.developer, review["review_id"], "developer", "Approved")
        with self.assertRaisesRegex(LocalWorkflowError, "explicit settings"):
            promote(self.developer, candidate["id"])
        transition_candidate(self.developer, candidate["id"], "rejected", "Reject experiment")
        with self.assertRaisesRegex(LocalWorkflowError, "policy"):
            promote(self.developer, candidate["id"])
        self.assertFalse((self.workspace_path / "optimization" / "promotions").exists())

    def test_promotion_rejects_stale_approval_and_missing_rollback(self):
        from src.developer.promotion import promote
        from src.developer.optimization import _storage
        candidate, _ = self._promotion_setup()
        validation_file = next((_storage(self.developer, candidate["id"]) / "validations").glob("*.json"))
        original = validation_file.read_bytes()
        document = json.loads(original)
        document["retrieval_settings"] = {"relationship_factor": 1.7}
        validation_file.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "stale"):
            promote(self.developer, candidate["id"])
        validation_file.write_bytes(original)
        baseline = next((self.workspace_path / "regression").glob("*/baselines/default.json"))
        baseline.unlink()
        with self.assertRaises(LocalWorkflowError):
            promote(self.developer, candidate["id"])

    def test_promotion_read_only_check_and_corruption_detection(self):
        from src.developer.promotion import promote, promotion_check
        report = promotion_check(self.developer)
        self.assertFalse(report["blocked"])
        self.assertFalse(self.workspace_path.exists())
        candidate, _ = self._promotion_setup()
        promote(self.developer, candidate["id"])
        before = {str(p): p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        self.assertFalse(promotion_check(self.developer)["blocked"])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        latest = sorted((self.workspace_path / "optimization" / "promotions").glob("*.json"))[-1]
        document = json.loads(latest.read_text(encoding="utf-8"))
        document["configuration"]["active_candidates"] = []
        latest.write_text(json.dumps(document), encoding="utf-8")
        self.assertTrue(promotion_check(self.developer)["blocked"])

    def test_promotion_pause_resume_duplicate_and_invalid_settings(self):
        from src.developer.promotion import promote, transition_promotion, active_configuration, validate_settings, rollback
        for settings in ([], {"unknown": 1}, {"relationship_factor": True}, {"relationship_factor": float("nan")},
                         {"relationship_factor": 3}):
            with self.assertRaises(LocalWorkflowError):
                validate_settings(settings)
        candidate, _ = self._promotion_setup()
        record = promote(self.developer, candidate["id"])
        with self.assertRaises(LocalWorkflowError):
            promote(self.developer, candidate["id"])
        transition_promotion(self.developer, record["promotion_id"], "paused")
        self.assertFalse(active_configuration(self.developer)["entries"])
        transition_promotion(self.developer, record["promotion_id"], "promoted")
        transition_promotion(self.developer, record["promotion_id"], "paused")
        rollback(self.developer, record["promotion_id"])
        self.assertFalse(active_configuration(self.developer)["entries"])

    def test_review_queue_history_transitions_and_cli_visibility(self):
        from src.developer.review import create_review, show_reviews, defer_review, reopen_review, withdraw_review

        _, _, candidate = self._optimization_setup()
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-review-create", candidate["id"], "--reason",
                           "Request review of local experiment", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        opened = json.loads(output.getvalue())
        self.assertEqual("pending", opened["status"])
        self.assertEqual("developer", opened["owner"])
        self.assertEqual(candidate["cases"], opened["affected_cases"])
        self.assertEqual(["pending"], [item["status"] for item in opened["review_history"]])
        event_dir = self.workspace_path / "optimization" / "reviews" / opened["review_id"] / "events"
        first_event = next(event_dir.glob("*.json"))
        first_bytes = first_event.read_bytes()
        with self.assertRaisesRegex(LocalWorkflowError, "already has a pending review"):
            create_review(self.developer, candidate["id"], "duplicate request")

        deferred = defer_review(self.developer, opened["review_id"], "reviewer-a", "Need additional evidence")
        self.assertEqual("deferred", deferred["status"])
        reopened = reopen_review(self.developer, opened["review_id"], "reviewer-a", "Evidence is ready")
        self.assertEqual("pending", reopened["status"])
        withdrawn = withdraw_review(self.developer, opened["review_id"], "reviewer-a", "Request withdrawn")
        self.assertEqual("withdrawn", withdrawn["status"])
        self.assertEqual(["pending", "deferred", "pending", "withdrawn"],
                         [item["status"] for item in withdrawn["review_history"]])
        self.assertEqual(first_bytes, first_event.read_bytes())
        self.assertEqual(4, len(list(event_dir.glob("*.json"))))
        with self.assertRaisesRegex(LocalWorkflowError, "Invalid review transition"):
            reopen_review(self.developer, opened["review_id"], "reviewer-a", "Cannot reopen withdrawn")

        with redirect_stdout(StringIO()) as output:
            self.assertEqual(0, main(("local", "optimize-review", "--workspace", str(self.workspace_path), "--json")))
        self.assertEqual(["withdrawn"], [item["status"] for item in json.loads(output.getvalue())["reviews"]])
        self.assertEqual("withdrawn", show_reviews(self.developer, candidate["id"])["review"]["status"])
        self.assertFalse(self.research_root.exists())

    def test_review_approval_requires_validation_and_records_reviewer(self):
        from src.developer.review import create_review, approve_review, policy_check, show_reviews

        _, _, candidate = self._optimization_setup("review-approval")
        review = create_review(self.developer, candidate["id"], "Request approval after validation")
        blocked = policy_check(self.developer, candidate["id"])
        self.assertTrue(any(item["check"] == "ownership" for item in blocked["blocked"]))
        self.assertTrue(any(item["check"] == "validation_evidence" for item in blocked["blocked"]))
        with redirect_stdout(StringIO()) as output:
            self.assertEqual(0, main(("local", "optimize-policy-check", "--id", candidate["id"],
                                     "--workspace", str(self.workspace_path), "--json")))
        self.assertEqual(blocked["blocked"], json.loads(output.getvalue())["blocked"])
        with self.assertRaisesRegex(LocalWorkflowError, "blocked by policy checks"):
            approve_review(self.developer, review["review_id"], "reviewer-b", "Approve change")
        self.assertEqual("pending", show_reviews(self.developer, review["review_id"])["review"]["status"])

        validation = self._register_passed_lifecycle_validation(candidate)
        before_policy = policy_check(self.developer, candidate["id"])
        self.assertFalse(before_policy["blocked"], before_policy)
        self.assertTrue(any(item["check"] == "validation_evidence" for item in before_policy["passed"]))
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-approve", review["review_id"], "--reviewer", "reviewer-b",
                           "--reason", "Validation gates and lifecycle reviewed", "--workspace",
                           str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        approved = json.loads(output.getvalue())
        self.assertEqual("approved", approved["status"])
        self.assertEqual("reviewer-b", approved["reviewer"])
        self.assertEqual("approved", approved["review_history"][-1]["status"])
        details = show_reviews(self.developer, candidate["id"])
        self.assertEqual(validation["id"], details["review"]["validation_summary"]["id"])
        self.assertEqual(1, len(details["validation_results"]))
        self.assertEqual([], details["previous_decisions"])
        self.assertTrue(details["candidate_lifecycle_history"] if "candidate_lifecycle_history" in details else
                        details["lifecycle_history"])
        self.assertFalse(self.research_root.exists())

    def test_review_rejection_policy_conflict_documentation_and_read_only_checks(self):
        from src.developer.optimization import create_candidate
        from src.developer.review import create_review, policy_check

        _, _, candidate = self._optimization_setup("review-conflict")
        self._register_passed_lifecycle_validation(candidate)
        create_candidate(self.developer, "review-conflict-peer", "Peer proposal", candidate["cases"],
                         candidate["source"], candidate["proposed_change"], "Repeat local checks")
        review = create_review(self.developer, candidate["id"], "Review candidate with known overlap")
        before = {path: path.read_bytes() for path in (self.workspace_path / "optimization").rglob("*.json")}
        blocked = policy_check(self.developer, candidate["id"])
        self.assertTrue(any(item["check"] == "conflicts" for item in blocked["blocked"]))
        self.assertFalse(blocked["automatic_changes"])
        self.assertEqual(before, {path: path.read_bytes() for path in before})

        documented = policy_check(self.developer, candidate["id"], "Peer overlap reviewed; retain both proposals for evidence comparison.")
        self.assertFalse(documented["blocked"], documented)
        self.assertTrue(any(item["check"] == "conflicts" for item in documented["warnings"]))
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-reject", review["review_id"], "--reviewer", "reviewer-c",
                           "--reason", "Overlap is not justified", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        rejected = json.loads(output.getvalue())
        self.assertEqual("rejected", rejected["status"])
        self.assertEqual("Overlap is not justified", rejected["review_history"][-1]["reason"])
        self.assertEqual("review-conflict", rejected["candidate_id"])
        self.assertFalse(self.research_root.exists())

    def test_review_compatibility_with_rollback_audit_and_checkpoint(self):
        from src.developer.governance import optimize_audit, transition_candidate
        from src.developer.optimization import decide_candidate
        from src.developer.review import create_review, policy_check, reject_review
        from src.developer.safety import record_rollback

        _, _, candidate = self._optimization_setup("review-rollback")
        validation = self._register_passed_lifecycle_validation(candidate)
        decide_candidate(self.developer, candidate["id"], "accepted", "Existing optimization decision")
        transition_candidate(self.developer, candidate["id"], "accepted", "Existing lifecycle acceptance")
        rollback = record_rollback(self.developer, candidate["id"], "Restore previous local baseline")
        transition_candidate(self.developer, candidate["id"], "rolled_back", "Manual restoration recorded")
        candidate_directory = self.workspace_path / "optimization" / "candidates" / candidate["id"]
        decision_bytes = (candidate_directory / "decision.json").read_bytes()
        rollback_path = next((candidate_directory / "rollback").glob("*.json"))
        rollback_bytes = rollback_path.read_bytes()
        review = create_review(self.developer, candidate["id"], "Record retrospective review")
        report = policy_check(self.developer, candidate["id"])
        self.assertTrue(any(item["check"] == "rollback_information" for item in report["passed"]))
        self.assertTrue(any(item["check"] == "lifecycle_state" for item in report["blocked"]))
        self.assertEqual("clean", optimize_audit(self.developer)["audit_status"])
        before = {path.name: path.read_bytes() for path in
                  (self.workspace_path / "optimization" / "candidates" / candidate["id"] / "lifecycle").glob("*.json")}
        reject_review(self.developer, review["review_id"], "reviewer-d", "Retrospective only; lifecycle is rolled back")
        self.assertEqual(before, {path.name: path.read_bytes() for path in
                                  (self.workspace_path / "optimization" / "candidates" / candidate["id"] / "lifecycle").glob("*.json")})
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "optimize-checkpoint", "--workspace", str(self.workspace_path), "--json"))
        self.assertEqual(0, status)
        checkpoint = json.loads(output.getvalue())
        self.assertEqual("developer-local-governance-checkpoint", checkpoint["mode"])
        self.assertTrue((self.workspace_path / "optimization" / "governance-checkpoints" / f"{checkpoint['id']}.json").is_file())
        self.assertEqual(validation["id"], json.loads((candidate_directory / "validations" / "review-test.json").read_text(encoding="utf-8"))["id"])
        self.assertEqual(decision_bytes, (candidate_directory / "decision.json").read_bytes())
        self.assertEqual(rollback_bytes, rollback_path.read_bytes())
        self.assertEqual(rollback["candidate_id"], candidate["id"])
        self.assertEqual("clean", optimize_audit(self.developer)["audit_status"])
        self.assertFalse(self.research_root.exists())

    def test_regression_baseline_history_stability_and_trace_diagnose_compatibility(self):
        cases = self.root / "regression-cases.json"
        cases.write_text(json.dumps([{"id": "session", "query": "load_session_token",
            "expected": {"files": ["src/session.py"], "symbols": ["load_session_token"]}}]), encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()), \
                patch("src.cli.RunTracker") as research:
            created = self.developer.regression(self.repository, cases, create_baseline=True)
            baseline_bytes = Path(created["baseline_path"]).read_bytes()
            before = self.developer.trace("load_session_token", self.repository)
            report = self.developer.regression(self.repository, cases)
            after = self.developer.trace("load_session_token", self.repository)
            diagnosis = self.developer.diagnose("session", cases, self.repository)
            with redirect_stdout(StringIO()) as output:
                status = main(("local", "regression", str(self.repository), "--cases", str(cases),
                               "--workspace", str(self.workspace_path), "--json"))
            self.assertEqual(0, status)
            self.assertEqual("developer-local-regression", json.loads(output.getvalue())["mode"])
            research.assert_not_called()
        self.assertEqual(before["results"], after["results"])
        self.assertIn("missing_evidence", diagnosis)
        self.assertEqual(baseline_bytes, Path(created["baseline_path"]).read_bytes())
        self.assertTrue(all(item["stable"] for item in report["stability"]))
        self.assertFalse(any(item["behavior_changed"] for item in report["comparisons"]))
        self.assertNotEqual(created["history_id"], report["history_id"])
        history = json.loads(Path(report["history_path"]).read_text(encoding="utf-8"))
        self.assertEqual("developer-navigation-v2", history["snapshot"]["retrieval_version"])
        self.assertEqual(["session"], history["report"]["query_cases"])
        self.assertEqual(3, len(list(Path(report["history_path"]).parent.glob("*.json"))))
        for forbidden in ("quality_score", "noise_rate", "context_completeness", '"score":'):
            self.assertNotIn(forbidden, json.dumps(history))
        self.assertFalse(self.research_root.exists())
        with self.assertRaisesRegex(LocalWorkflowError, "already exists"):
            self.developer.regression(self.repository, cases, create_baseline=True)
        with self.assertRaisesRegex(LocalWorkflowError, "Cannot compare"):
            self.developer.regression(self.repository, cases, top_k=3)
        with self.assertRaisesRegex(LocalWorkflowError, "Baseline name"):
            self.developer.regression(self.repository, cases, baseline="../escape")
        with self.assertRaisesRegex(LocalWorkflowError, "outside the prototype checkout"):
            DeveloperWorkspace(Path(__file__).resolve().parents[1] / "baseline-data").regression(
                self.repository, cases, create_baseline=True)
        cases.write_text(json.dumps([{"id": "session", "query": "different query", "expected": {}}]), encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "case definition changed"):
            self.developer.regression(self.repository, cases)

    def test_regression_comparison_detects_ranking_context_missing_and_noise(self):
        from copy import deepcopy
        from src.developer.regression import compare_records
        fixture = Path(__file__).parent / "fixtures/developer_eval/baseline_records/auth-flow.json"
        old = json.loads(fixture.read_text(encoding="utf-8"))
        current = deepcopy(old)
        current["retrieved"]["symbols"] = []
        current["retrieved"]["files"].append("src/unrelated.py")
        current["ranking"]["order"].reverse()
        current["ranking"]["reasons"][0]["reason"] = {}
        current["context"]["expanded_symbols"] = []
        report = compare_records(old, current)
        self.assertTrue(report["ranking_differences"])
        self.assertTrue(report["context_differences"])
        self.assertIn("TokenManager.issue", report["missing_evidence"]["symbols"])
        self.assertEqual(["src/unrelated.py"], report["newly_introduced_noise"])
        kinds = {item["kind"] for item in report["changes"]}
        self.assertTrue({"missing_previously_found_symbols", "context_expansion_loss", "explanation_removed",
                         "unrelated_files_added", "ranking_changed"} <= kinds)
        for change in report["changes"]:
            self.assertEqual(old["id"], change["case_id"])
            self.assertIn("previous_behavior", change)
            self.assertIn("current_behavior", change)
            self.assertTrue(change["suspected_cause"])
        self.assertFalse(compare_records(old, old)["behavior_changed"])
        reordered = deepcopy(old)
        reordered["ranking"]["order"].append({"file": "src/config.py", "symbol": "load_auth_config"})
        baseline = deepcopy(reordered)
        reordered["ranking"]["order"].reverse()
        order_report = compare_records(baseline, reordered)
        self.assertTrue(order_report["ranking_differences"])
        self.assertIsNone(order_report["context_differences"])

    def test_regression_classifies_expected_changes_and_normalizes_chunk_ids(self):
        from copy import deepcopy
        from src.developer.regression import compare_records, snapshot
        case = {"id": "test", "query": "issue token", "expected": {"symbols": ["issue"]},
                "required_relationships": ["format_token"]}
        row = {"file_path": "token.py", "qualified_name": "issue", "chunk_id": "old", "score": 9,
               "ranking_reason": {"context_expansion_reason": "static call"},
               "related_context": [{"chunk_id": "a", "file_path": "format.py",
                                    "symbol_name": "format_token", "reason": "call"}]}
        payload = {"results": [row], "context": {}}
        current = snapshot(case, payload, "synthetic")
        row["chunk_id"] = "new"
        row["related_context"][0]["chunk_id"] = "b"
        row["score"] = 2
        self.assertEqual(current, snapshot(case, payload, "synthetic"))
        previous = deepcopy(current)
        previous["retrieved"]["symbols"] = []
        previous["context"]["expanded_symbols"] = []
        changes = compare_records(previous, current)["changes"]
        self.assertTrue({"improved_symbol_coverage", "better_relationship_expansion"}
                        <= {item["kind"] for item in changes if item["classification"] == "expected_change"})
        previous = deepcopy(current)
        previous["context"]["expanded_symbols"] *= 2
        self.assertIn("reduced_duplicate_context", {item["kind"] for item in compare_records(previous, current)["changes"]})

    def test_regression_rejects_unstable_baseline_and_reports_unstable_comparison(self):
        from copy import deepcopy
        cases = self.root / "cases.json"
        cases.write_text(json.dumps([{"id": "s", "query": "session", "expected": {}}]), encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            first = self.developer.query("session", self.repository)
        second = deepcopy(first)
        second["results"] = []
        with patch.object(self.developer, "query", side_effect=[first, second]):
            with self.assertRaisesRegex(LocalWorkflowError, "unstable"):
                self.developer.regression(self.repository, cases, create_baseline=True)
        self.assertFalse((self.workspace_path / "regression").exists())
        with patch.object(self.developer, "query", return_value=first):
            self.developer.regression(self.repository, cases, create_baseline=True)
        with patch.object(self.developer, "query", side_effect=[first, second]):
            report = self.developer.regression(self.repository, cases)
        self.assertFalse(report["stability"][0]["stable"])
        self.assertIn("unstable_ranking_changes", {item["kind"] for item in report["comparisons"][0]["changes"]})

    def test_regression_rejects_malformed_baselines_and_redirected_storage(self):
        cases = self.root / "cases.json"
        cases.write_text(json.dumps([{"id": "s", "query": "session", "expected": {}}]), encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "Cannot compare"):
            self.developer.regression(self.repository, cases)
        inventory = local_workflow.scan_local_repository(self.repository)
        storage = self.workspace_path / "regression" / local_workflow._safe_component(inventory.repository_id)
        baseline = storage / "baselines/default.json"
        baseline.parent.mkdir(parents=True)
        baseline.write_text('{"records": null}', encoding="utf-8")
        with self.assertRaisesRegex(LocalWorkflowError, "Cannot compare"):
            self.developer.regression(self.repository, cases)
        self.assertFalse((storage / "history").exists())
        other = self.root / "redirected-workspace"
        other.mkdir()
        outside = self.root / "protected-output"
        outside.mkdir()
        # Windows junctions exercise resolved-path containment without symlink privileges.
        import os
        if os.name == "nt":
            subprocess.run(["cmd", "/c", "mklink", "/J", str(other / "regression"), str(outside)],
                           check=True, capture_output=True)
        else:
            (other / "regression").symlink_to(outside, target_is_directory=True)
        try:
            with self.assertRaisesRegex(LocalWorkflowError, "resolves outside"):
                DeveloperWorkspace(other).regression(self.repository, cases, create_baseline=True)
            self.assertEqual([], list(outside.iterdir()))
        finally:
            if os.name == "nt":
                (other / "regression").rmdir()
            else:
                (other / "regression").unlink()

    def test_duplicate_suppression_with_controlled_nonoverlapping_candidates(self):
        from src.developer.ranking import rank_developer_results
        from src.models.embedding import EmbeddingMetadata
        from src.models.retrieval_result import SearchResult
        rows = [SearchResult(str(i), i, 1.0,
                EmbeddingMetadata("local/fixture", "a" * 40, path, "function", "format_token", 1, 2,
                                  "b" * 64, 10), "bm25")
                for i, path in enumerate(("utils.py", "legacy.py"), 1)]
        context = {row.chunk_id: {"content_sha256": "b" * 64} for row in rows}
        selected = rank_developer_results("format_token", (), rows, 10, context)
        self.assertEqual(1, len(selected))
        self.assertEqual(1, len(selected[0]["ranking_reason"]["duplicate_suppressed"]))

    def test_cli_help_separates_modes_and_local_demo_runs(self):
        with self.assertRaises(SystemExit) as raised, redirect_stdout(StringIO()) as output:
            main(("--help",))
        self.assertEqual(0, raised.exception.code)
        self.assertIn("Research commands:", output.getvalue())
        self.assertIn("Developer commands:", output.getvalue())
        self.assertIn(DEVELOPER_MODE_NOTICE, output.getvalue())
        with patch("src.cli.RunTracker") as research_tracker:
            with redirect_stdout(StringIO()):
                status = main(("local", "demo", "--workspace", str(self.workspace_path)))
        self.assertEqual(0, status)
        research_tracker.assert_not_called()

        with redirect_stdout(StringIO()) as demo_output:
            status = main(("local", "demo", "--workspace", str(self.workspace_path)))
        self.assertEqual(0, status)
        self.assertIn(DEVELOPER_MODE_NOTICE, demo_output.getvalue())
        self.assertIn("Parsed and chunked", demo_output.getvalue())

    def test_cli_scan_and_error_messages(self):
        with redirect_stdout(StringIO()) as output:
            status = main(("local", "scan", str(self.repository), "--workspace", str(self.workspace_path)))
        self.assertEqual(0, status)
        self.assertIn("Python files: 1", output.getvalue())
        self.assertIn("Ignored unsupported file types", output.getvalue())
        self.assertIn("not benchmark results", output.getvalue())

        errors = StringIO()
        with redirect_stderr(errors):
            status = main(("local", "scan", str(self.root / "missing"), "--workspace", str(self.workspace_path)))
        self.assertEqual(2, status)
        self.assertIn("prototype local: error:", errors.getvalue())
        self.assertIn("does not exist or cannot be resolved", errors.getvalue())

    def test_cli_index_and_query_route_only_to_developer_workspace(self):
        index_payload = {
            "index_status": "indexed",
            "index_path": str(self.workspace_path / "indexes" / "snapshot"),
            "parsed_python_file_count": 1,
            "chunk_count": 3,
            "indexed_chunk_count": 2,
            "rejected_chunk_count": 1,
            "repository": {"unsupported_extensions": {".md": 1}},
            "parse_failure_count": 0,
            "run_id": "local-index-run",
        }
        query_payload = {
            "repository": {
                "repository_path": str(self.repository),
                "working_tree_sha256": "a" * 64,
            },
            "results": [{
                "rank": 1, "file_path": "src/session.py", "start_line": 1, "end_line": 2,
                "entity_type": "function", "qualified_name": "load_session_token", "score": 0.5,
            }],
            "run_id": "local-query-run",
        }
        with patch("src.developer.DeveloperWorkspace") as workspace_type:
            workspace_type.return_value.index.return_value = index_payload
            workspace_type.return_value.query.return_value = query_payload
            index_status = main((
                "local", "index", str(self.repository), "--workspace", str(self.workspace_path)
            ))
            query_status = main((
                "local", "query", "find the session token", "--repository", str(self.repository),
                "--workspace", str(self.workspace_path), "--top-k", "4",
            ))

        self.assertEqual((0, 0), (index_status, query_status))
        self.assertEqual(self.workspace_path.resolve(), workspace_type.call_args.args[0].resolve())
        self.assertEqual(self.repository, workspace_type.return_value.index.call_args.args[0])
        workspace_type.return_value.query.assert_called_once_with("find the session token", Path(self.repository), 4)
        self.assertFalse(self.research_root.exists())


    def _governance_setup(self):
        from src.developer import assurance, recovery_governance as governance
        _, _, _, scenario = self._assurance_setup()
        source = assurance.create_assurance(self.developer, scenario["scenario_id"], "Governance baseline")
        source = assurance.verify_assurance(self.developer, source["assurance_id"])
        record = governance.register(self.developer, source["assurance_id"], "Register responsibility")
        return source, record

    def test_recovery_governance_lifecycle_and_append_only_history(self):
        from src.developer import recovery_governance as g
        source, record = self._governance_setup()
        identifier = record["assurance_id"]
        original = {p: p.read_bytes() for p in g._root(self.developer).glob("*.json")}
        with self.assertRaises(LocalWorkflowError):
            g.change(self.developer, identifier, "transition", "Invalid", status="paused")
        for state in ("active", "paused", "expired", "active", "retired"):
            record = g.change(self.developer, identifier, "transition", "Explicit transition", status=state)
        self.assertEqual("retired", record["status"])
        self.assertEqual(6, len(record["history"]))
        with self.assertRaises(LocalWorkflowError):
            g.change(self.developer, identifier, "transition", "Terminal", status="active")
        for path, content in original.items():
            self.assertEqual(content, path.read_bytes())
        self.assertEqual(source, record["source"])

    def test_recovery_governance_scheduling_expiry_and_no_replay(self):
        from datetime import timedelta
        from src.developer import recovery_governance as g
        source, record = self._governance_setup()
        identifier = record["assurance_id"]
        g.change(self.developer, identifier, "transition", "Start", status="active")
        self.assertIn("scheduled_check_overdue", g.review(self.developer, identifier)["findings"])
        record = g.record_check(self.developer, identifier, identifier, "Capture completed evidence")
        self.assertEqual(source["evidence"][0]["checked_at"], record["last_check"])
        self.assertEqual([], g.review(self.developer, identifier)["findings"])
        with self.assertRaises(LocalWorkflowError):
            g.record_check(self.developer, identifier, identifier, "Cannot refresh old evidence")
        due = g.assurance._timestamp(record["next_check"])
        with patch.object(g, "_now", return_value=due - timedelta(microseconds=1)):
            self.assertNotIn("scheduled_check_overdue", g.review(self.developer, identifier)["findings"])
        with patch.object(g, "_now", return_value=due):
            self.assertIn(identifier, g.check(self.developer)["expired"])
            self.assertIn("scheduled_check_overdue", g.review(self.developer, identifier)["findings"])
        self.assertEqual("active", g.history(self.developer, identifier)["record"]["status"])
        with self.assertRaises(LocalWorkflowError):
            g.change(self.developer, identifier, "schedule", "Invalid", interval_hours=0)
        updated = g.change(self.developer, identifier, "schedule", "Shorter interval", interval_hours=1)
        self.assertEqual((g.assurance._timestamp(record["last_check"]) + timedelta(hours=1)).isoformat(), updated["next_check"])

    def test_recovery_governance_ownership_notes_and_improvements(self):
        from src.developer import recovery_governance as g
        _, record = self._governance_setup()
        identifier = record["assurance_id"]
        g.change(self.developer, identifier, "transition", "Start", status="active")
        g.record_check(self.developer, identifier, identifier, "Capture")
        g.change(self.developer, identifier, "assign", "Handoff", owner="maintainer", responsibility="Review rollback references")
        for kind in ("review", "improvement"):
            record = g.change(self.developer, identifier, "note", "Manual review", kind=kind, note="Schedule a fresh verification")
        self.assertEqual("maintainer", record["owner"])
        self.assertEqual("developer", record["verification_history"][0]["owner"])
        self.assertIn("ownership_review_due", g.review(self.developer, identifier)["findings"])
        self.assertEqual(1, len(record["review_notes"]))
        report = g.improvements(self.developer)["improvements"][0]
        self.assertEqual(1, len(report["manual_improvement_notes"]))
        self.assertIn("ownership_review_due", report["current_findings"])
        with self.assertRaises(LocalWorkflowError):
            g.change(self.developer, identifier, "assign", "Bad owner", owner=" ", responsibility="Review")

    def test_recovery_governance_fresh_evidence_resolves_recorded_findings(self):
        from datetime import timedelta
        from src.developer import assurance, recovery_governance as g
        source, record = self._governance_setup()
        identifier = record["assurance_id"]
        g.change(self.developer, identifier, "transition", "Start", status="active")
        future = assurance._timestamp(source["evidence"][0]["expires_at"]) + timedelta(seconds=1)
        with patch.object(g, "_now", return_value=future), patch.object(assurance, "_now", return_value=future):
            record = g.record_check(self.developer, identifier, identifier, "Retain stale check")
            self.assertTrue(record["verification_history"][-1]["findings"])
            fresh = assurance.create_assurance(self.developer, record["scenario_id"], "Renew")
            assurance.verify_assurance(self.developer, fresh["assurance_id"])
            record = g.record_check(self.developer, identifier, fresh["assurance_id"], "Capture renewal")
            self.assertEqual([], record["verification_history"][-1]["findings"])
            report = g.improvements(self.developer)["improvements"][0]
            self.assertTrue(report["resolved_findings"][-1]["findings"])
            self.assertEqual([], report["unresolved_findings"])
        self.assertEqual(2, len(record["verification_history"]))
        self.assertIn("evidence_changes", record["verification_history"][-1])

    def test_recovery_governance_drift_and_lost_evidence_are_visible(self):
        from src.developer import assurance, recovery_governance as g
        _, record = self._governance_setup()
        identifier = record["assurance_id"]
        g.change(self.developer, identifier, "transition", "Start", status="active")
        g.record_check(self.developer, identifier, identifier, "Capture")
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            report = g.review(self.developer, identifier)
            self.assertTrue(report["findings"])
            self.assertTrue(report["manual_actions"])
        with patch.object(assurance, "_collect", side_effect=LocalWorkflowError("Missing history")):
            report = g.review(self.developer, identifier)
            self.assertEqual(list(assurance.EVIDENCE_TYPES), report["missing_evidence"])
        assurance.transition_assurance(self.developer, identifier, "expired", "Expire source")
        self.assertTrue(g.review(self.developer, identifier)["expired"])
        self.assertEqual(1, len(g.history(self.developer, identifier)["record"]["verification_history"]))

    def test_recovery_governance_rejects_incomplete_wrong_scenario_and_inactive_checks(self):
        from src.developer import assurance, continuity, recovery_governance as g
        source, record = self._governance_setup()
        identifier = record["assurance_id"]
        with self.assertRaises(LocalWorkflowError):
            g.record_check(self.developer, identifier, identifier, "Draft cannot verify")
        g.change(self.developer, identifier, "transition", "Start", status="active")
        pending = assurance.create_assurance(self.developer, record["scenario_id"], "Pending")
        with self.assertRaises(LocalWorkflowError):
            g.record_check(self.developer, identifier, pending["assurance_id"], "Incomplete")
        scenario = continuity.create_scenario(self.developer, source["deployment_id"], "Different scenario")
        other = assurance.create_assurance(self.developer, scenario["scenario_id"], "Other")
        assurance.verify_assurance(self.developer, other["assurance_id"])
        with self.assertRaises(LocalWorkflowError):
            g.record_check(self.developer, identifier, other["assurance_id"], "Wrong scenario")
        with self.assertRaises(LocalWorkflowError):
            g.register(self.developer, identifier, "Duplicate")

    def test_recovery_governance_cli_reports_are_read_only(self):
        from src.developer import recovery_governance as g
        _, record = self._governance_setup()
        identifier = record["assurance_id"]
        commands = [("assurance-transition", identifier, "active", "--reason", "Start"),
                    ("assurance-record-check", identifier, "--verification-id", identifier, "--reason", "Capture"),
                    ("assurance-assign", identifier, "--owner", "reviewer", "--responsibility", "Maintain evidence", "--reason", "Handoff"),
                    ("assurance-schedule", identifier, "--every-hours", "2", "--reason", "Schedule"),
                    ("assurance-note", identifier, "--kind", "improvement", "--note", "Verify again", "--reason", "Review")]
        for command in commands:
            with redirect_stdout(StringIO()):
                self.assertEqual(0, main(["local", *command, "--workspace", str(self.workspace_path)]))
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        for command in ("assurance-status", "assurance-history", "assurance-review", "assurance-check", "assurance-improvements"):
            args = ["local", command]
            if command in {"assurance-history", "assurance-review"}:
                args.append(identifier)
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main([*args, "--workspace", str(self.workspace_path), "--json"]))
            self.assertEqual(g.MODE, json.loads(output.getvalue())["mode"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})

    def test_recovery_governance_cli_registration_and_evidence_changes(self):
        from src.developer import assurance, continuity, recovery_governance as g
        _, _, _, scenario = self._assurance_setup()
        source = assurance.create_assurance(self.developer, scenario["scenario_id"], "Initial verification")
        assurance.verify_assurance(self.developer, source["assurance_id"])
        identifier = source["assurance_id"]
        with redirect_stdout(StringIO()):
            self.assertEqual(0, main(["local", "assurance-register", identifier,
                "--owner", "operator", "--responsibility", "Review evidence", "--every-hours", "24",
                "--reason", "Register", "--workspace", str(self.workspace_path)]))
        g.change(self.developer, identifier, "transition", "Start", status="active")
        g.change(self.developer, identifier, "assign", "Handoff before recording", owner="new-owner", responsibility="Review evidence")
        g.record_check(self.developer, identifier, identifier, "Old source does not acknowledge handoff")
        self.assertIn("ownership_review_due", g.review(self.developer, identifier)["findings"])
        continuity.test_scenario(self.developer, scenario["scenario_id"])
        fresh = assurance.create_assurance(self.developer, scenario["scenario_id"], "Changed simulation history")
        assurance.verify_assurance(self.developer, fresh["assurance_id"])
        record = g.record_check(self.developer, identifier, fresh["assurance_id"], "Capture changed evidence")
        self.assertNotIn("ownership_review_due", g.review(self.developer, identifier)["findings"])
        self.assertTrue(record["verification_history"][-1]["evidence_changes"]["changed"])
        self.assertEqual(identifier, record["verification_history"][0]["source"]["assurance_id"])

    def test_recovery_governance_corruption_atomic_failure_and_isolation(self):
        from src.developer import recovery_governance as g
        self.assertEqual([], g.check(self.developer)["passed"])
        self.assertFalse(g._root(self.developer).exists())
        with self.assertRaises(LocalWorkflowError):
            g.history(self.developer, "unknown")
        _, record = self._governance_setup()
        path = next(g._root(self.developer).glob("*.json"))
        original = path.read_bytes()
        with patch.object(g.os, "link", side_effect=FileExistsError("Concurrent append")):
            with self.assertRaises(LocalWorkflowError):
                g.change(self.developer, record["assurance_id"], "transition", "Start", status="active")
        self.assertEqual(original, path.read_bytes())
        self.assertFalse(list(g._root(self.developer).glob("*.tmp")))
        event = json.loads(original)
        event["sequence"] = 2
        path.write_text(json.dumps(event), encoding="utf-8")
        with self.assertRaises(LocalWorkflowError):
            g.status(self.developer)
        path.write_bytes(original)
        self.assertEqual("draft", g.history(self.developer, record["assurance_id"])["record"]["status"])
        with self.assertRaises(LocalWorkflowError):
            g.check(DeveloperWorkspace(self.research_root / "governance", research_roots=[self.research_root]))


    def _assurance_operations_setup(self, verified=False):
        from src.developer import assurance_operations as ops, recovery_governance as g
        source, record = self._governance_setup()
        if verified:
            g.change(self.developer, record["assurance_id"], "transition", "Start", status="active")
            g.record_check(self.developer, record["assurance_id"], source["assurance_id"], "Capture evidence")
        operation = ops.create(self.developer, record["assurance_id"], "Start operations", owner="operator")
        return source, operation

    def test_assurance_operations_lifecycle_and_preserved_history(self):
        from src.developer import assurance_operations as ops
        _, operation = self._assurance_operations_setup()
        identifier = operation["operation_id"]
        original = {p: p.read_bytes() for p in ops._root(self.developer).glob("*.json")}
        with self.assertRaises(LocalWorkflowError):
            ops.change(self.developer, identifier, "transition", "Cannot skip review", status="closed")
        ops.change(self.developer, identifier, "transition", "Begin", status="reviewing")
        with self.assertRaises(LocalWorkflowError):
            ops.change(self.developer, identifier, "transition", "Must record review", status="accepted")
        reviewed = ops.record_review(self.developer, identifier, "Inspect current findings")
        self.assertEqual("reviewing", reviewed["status"])
        self.assertIsNotNone(reviewed["last_reviewed"])
        with self.assertRaises(LocalWorkflowError):
            ops.change(self.developer, identifier, "transition", "Unresolved findings", status="improved")
        ops.change(self.developer, identifier, "transition", "Explicitly accept current findings", status="accepted")
        closed = ops.change(self.developer, identifier, "transition", "Close accepted operation", status="closed")
        self.assertTrue(ops.findings(self.developer)["active"])
        with self.assertRaises(LocalWorkflowError):
            ops.record_review(self.developer, identifier, "Closed cannot change")
        self.assertEqual(5, len(closed["history"]))
        for path, content in original.items():
            self.assertEqual(content, path.read_bytes())

    def test_assurance_operations_repeated_findings_resolution_and_reopening(self):
        from src.developer import assurance_operations as ops, recovery_governance as g
        source, operation = self._assurance_operations_setup()
        identifier, anchor = operation["operation_id"], source["assurance_id"]
        ops.record_review(self.developer, identifier, "First observation")
        ops.record_review(self.developer, identifier, "Repeated observation")
        report = ops.findings(self.developer)
        self.assertTrue(report["recurring"])
        self.assertEqual({"warning", "info"}, {f["severity"] for f in report["active"]})
        for finding in report["active"]:
            self.assertEqual(anchor, finding["assurance_id"])
            self.assertEqual([identifier], finding["related_operations"])
            self.assertLessEqual(finding["first_seen"], finding["last_seen"])
        g.change(self.developer, anchor, "transition", "Start", status="active")
        g.record_check(self.developer, anchor, anchor, "Record verified evidence")
        # Read-only reporting cannot resolve the recorded findings.
        self.assertEqual([], ops.review_cycle(self.developer, anchor)["current_findings"])
        self.assertTrue(ops.findings(self.developer)["active"])
        ops.record_review(self.developer, identifier, "Confirm resolution")
        self.assertEqual([], ops.findings(self.developer)["active"])
        self.assertTrue(ops.findings(self.developer)["resolved"])
        ops.change(self.developer, identifier, "transition", "Confirmed improvement", status="improved")
        g.change(self.developer, anchor, "assign", "Missing refreshed ownership verification", owner="next", responsibility="Review evidence")
        ops.record_review(self.developer, identifier, "New handoff finding")
        self.assertIn("ownership_review_due", [f["key"] for f in ops.findings(self.developer)["active"]])
        # The original draft lifecycle finding recurs in a separate scenario observation.
        g.change(self.developer, anchor, "transition", "Pause", status="paused")
        ops.record_review(self.developer, identifier, "Paused observation")
        g.change(self.developer, anchor, "transition", "Resume", status="active")
        ops.record_review(self.developer, identifier, "Resolve paused lifecycle")
        g.change(self.developer, anchor, "transition", "Pause again", status="paused")
        reviewed = ops.record_review(self.developer, identifier, "Reopened lifecycle finding")
        self.assertIn(anchor + ":lifecycle:paused", reviewed["reviews"][-1]["reopened_findings"])

    def test_assurance_operations_shared_findings_and_manual_notes(self):
        from src.developer import assurance_operations as ops, recovery_governance as g
        source, first = self._assurance_operations_setup()
        ops.record_review(self.developer, first["operation_id"], "First cycle")
        second = ops.create(self.developer, source["assurance_id"], "Follow-up cycle", owner="next-operator")
        ops.record_review(self.developer, second["operation_id"], "Repeated unresolved findings")
        for finding in ops.findings(self.developer)["active"]:
            self.assertEqual([first["operation_id"], second["operation_id"]], finding["related_operations"])
        ops.change(self.developer, second["operation_id"], "assign", "Operations handoff", owner="reviewer")
        ops.change(self.developer, second["operation_id"], "note", "Manual action", note="Plan evidence renewal")
        self.assertEqual("developer", g.history(self.developer, source["assurance_id"])["record"]["owner"])
        legacy = g.improvements(self.developer)
        report = ops.improvements(self.developer)
        self.assertEqual(legacy, {k: report[k] for k in legacy})
        self.assertTrue(report["operations"]["repeated_findings"][-1]["findings"])
        self.assertEqual("Plan evidence renewal", report["operations"]["improvement_notes"][0]["note"])
        cycle = ops.review_cycle(self.developer, source["assurance_id"])
        self.assertEqual(2, len(cycle["previous_reviews"]))
        self.assertTrue(cycle["pending_actions"])
        self.assertEqual(second["operation_id"], cycle["improvement_history"][0]["operation_id"])

    def test_assurance_operations_coverage_includes_ungoverned_and_unverified_scenarios(self):
        from src.developer import assurance, assurance_operations as ops, continuity, recovery_governance as g
        _, deployed, _, scenario = self._assurance_setup()
        empty = ops.coverage(self.developer)
        self.assertEqual([{"assurance_id": None, "scenario_id": scenario["scenario_id"]}], empty["missing_owner"])
        self.assertTrue(empty["missing_schedule"])
        self.assertEqual([], empty["covered"])
        source = assurance.create_assurance(self.developer, scenario["scenario_id"], "Ungoverned assurance")
        assurance.verify_assurance(self.developer, source["assurance_id"])
        ungoverned = ops.coverage(self.developer)
        self.assertEqual(source["assurance_id"], ungoverned["missing_owner"][0]["assurance_id"])
        self.assertIn(scenario["scenario_id"], ungoverned["verified_scenarios"])
        g.register(self.developer, source["assurance_id"], "Register")
        g.change(self.developer, source["assurance_id"], "transition", "Start", status="active")
        g.record_check(self.developer, source["assurance_id"], source["assurance_id"], "Record verification")
        covered = ops.coverage(self.developer)
        self.assertEqual(1, len(covered["covered"]))
        self.assertEqual([], covered["missing_owner"])
        other = continuity.create_scenario(self.developer, deployed["deployment_id"], "Scenario without assurance")
        mixed = ops.coverage(self.developer)
        self.assertEqual(1, len(mixed["covered"]))
        self.assertEqual(other["scenario_id"], mixed["uncovered"][0]["scenario_id"])
        fresh = assurance.create_assurance(self.developer, scenario["scenario_id"], "Renewal")
        assurance.verify_assurance(self.developer, fresh["assurance_id"])
        g.record_check(self.developer, source["assurance_id"], fresh["assurance_id"], "Renewal linked to governance")
        self.assertFalse(any(row["assurance_id"] == fresh["assurance_id"] for row in ops.coverage(self.developer)["uncovered"]))

    def test_assurance_operations_expiry_missing_references_and_stale_improvement(self):
        from datetime import timedelta
        from src.developer import assurance_operations as ops, recovery_governance as g
        source, operation = self._assurance_operations_setup(verified=True)
        identifier = operation["operation_id"]
        ops.record_review(self.developer, identifier, "Clean review")
        due = g.assurance._timestamp(source["evidence"][0]["expires_at"]) + timedelta(seconds=1)
        with patch.object(g, "_now", return_value=due):
            report = ops.coverage(self.developer)
            self.assertTrue(report["expired"])
            self.assertEqual([], report["covered"])
            with self.assertRaises(LocalWorkflowError):
                ops.change(self.developer, identifier, "transition", "Old clean review is stale", status="improved")
        with patch("src.developer.promotion._all_reviews", return_value=[]):
            report = ops.coverage(self.developer)
            self.assertTrue(report["missing_recovery_references"])
            self.assertEqual([], report["verified_scenarios"])

    def test_assurance_operations_missing_history_preserves_findings(self):
        from src.developer import assurance_operations as ops, recovery_governance as g
        source, operation = self._assurance_operations_setup()
        ops.record_review(self.developer, operation["operation_id"], "Capture findings")
        original = ops.findings(self.developer)["active"]
        with patch.object(g, "review", side_effect=LocalWorkflowError("Missing governance history")):
            cycle = ops.review_cycle(self.developer, source["assurance_id"])
            self.assertIn("assurance_history_unavailable", cycle["current_findings"])
            self.assertTrue(cycle["previous_reviews"])
            with self.assertRaises(LocalWorkflowError):
                ops.record_review(self.developer, operation["operation_id"], "Unavailable history")
        self.assertEqual(original, ops.findings(self.developer)["active"])
        incomplete = g.review(self.developer, source["assurance_id"])
        incomplete["findings"] = ["recovery_history_unavailable"]
        with patch.object(g, "review", return_value=incomplete):
            ops.record_review(self.developer, operation["operation_id"], "Incomplete review cannot resolve old findings")
        self.assertTrue(set(f["finding_id"] for f in original).issubset({f["finding_id"] for f in ops.findings(self.developer)["active"]}))
        with patch.object(g, "_load", side_effect=LocalWorkflowError("Unreadable governance")):
            report = ops.coverage(self.developer)
            self.assertTrue(report["diagnostics"])
            self.assertEqual([], report["covered"])

    def test_assurance_operations_cli_reports_and_prior_journals_unchanged(self):
        from src.developer import assurance_operations as ops, recovery_governance as g
        source, _ = self._governance_setup()
        anchor = source["assurance_id"]
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        commands = [("assurance-operation-create", anchor, "--owner", "operator"),
                    ("assurance-operation-review", "operation-001"),
                    ("assurance-operation-assign", "operation-001", "--owner", "reviewer"),
                    ("assurance-operation-note", "operation-001", "--note", "Manual improvement"),
                    ("assurance-operation-transition", "operation-001", "accepted")]
        for command in commands:
            with redirect_stdout(StringIO()):
                self.assertEqual(0, main(["local", *command, "--reason", "Explicit operation", "--workspace", str(self.workspace_path)]))
        for path, content in before.items():
            self.assertEqual(content, path.read_bytes())
        all_files = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        for command in ("assurance-operations", "assurance-findings", "assurance-review-cycle", "assurance-coverage", "assurance-improvements"):
            args = ["local", command] + ([anchor] if command == "assurance-review-cycle" else [])
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main([*args, "--workspace", str(self.workspace_path), "--json"]))
            self.assertEqual(g.MODE if command == "assurance-improvements" else ops.MODE, json.loads(output.getvalue())["mode"])
        self.assertEqual(all_files, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})

    def test_assurance_operations_corruption_atomic_failure_and_isolation(self):
        from src.developer import assurance_operations as ops
        self.assertEqual([], ops.operations(self.developer)["operations"])
        self.assertEqual([], ops.coverage(self.developer)["covered"])
        self.assertFalse(ops._root(self.developer).exists())
        with self.assertRaises(LocalWorkflowError):
            ops.create(self.developer, "unknown", "Unknown assurance")
        with self.assertRaises(LocalWorkflowError):
            ops.review_cycle(self.developer, "unknown")
        _, operation = self._assurance_operations_setup()
        path = next(ops._root(self.developer).glob("*.json"))
        original = path.read_bytes()
        with patch.object(ops.os, "link", side_effect=FileExistsError("Concurrent append")):
            with self.assertRaises(LocalWorkflowError):
                ops.record_review(self.developer, operation["operation_id"], "Atomic failure")
        self.assertEqual(original, path.read_bytes())
        self.assertEqual([], ops.findings(self.developer)["active"])
        self.assertFalse(list(ops._root(self.developer).glob("*.tmp")))
        event = json.loads(original)
        event["owner"] = " "
        path.write_text(json.dumps(event), encoding="utf-8")
        with self.assertRaises(LocalWorkflowError):
            ops.operations(self.developer)
        path.write_bytes(original)
        with self.assertRaises(LocalWorkflowError):
            ops.change(self.developer, operation["operation_id"], "assign", "Invalid owner", owner=" ")
        with self.assertRaises(LocalWorkflowError):
            ops.coverage(DeveloperWorkspace(self.research_root / "operations", research_roots=[self.research_root]))

    def test_assurance_operations_improvement_keeps_verification_links_and_closes(self):
        from src.developer import assurance_operations as ops
        source, operation = self._assurance_operations_setup(verified=True)
        identifier = operation["operation_id"]
        ops.record_review(self.developer, identifier, "Clean evidence")
        improved = ops.change(self.developer, identifier, "transition", "Verified improvement", status="improved")
        self.assertEqual("improved", improved["status"])
        ops.change(self.developer, identifier, "transition", "Close reviewed improvement", status="closed")
        report = ops.improvements(self.developer)
        linked = report["operations"]["linked_verification_history"][0]["verification_history"]
        self.assertEqual(source["assurance_id"], linked[0]["verification_id"])
        self.assertEqual([], ops.operations(self.developer)["active"])
        self.assertEqual(1, len(ops.operations(self.developer)["operations"]))


    def _maturity_setup(self):
        from src.developer import assurance_operations as ops, maturity
        source, operation = self._assurance_operations_setup(verified=True)
        ops.record_review(self.developer, operation["operation_id"], "Current reviewed evidence")
        record = maturity.create(self.developer, "recovery-verification", [source["assurance_id"]], "maintainer", "Define assurance area")
        return source, operation, record

    def test_maturity_lifecycle_requires_assessments_and_preserves_history(self):
        from src.developer import maturity as m
        _, _, record = self._maturity_setup()
        identifier = record["maturity_id"]
        original = {p: p.read_bytes() for p in m._root(self.developer).glob("*.json")}
        with self.assertRaises(LocalWorkflowError):
            m.transition(self.developer, identifier, "defined", "Missing assessment")
        for index, capability in enumerate(m.CAPABILITIES):
            if capability == m.CAPABILITIES[3]:
                planned = m.add_plan(self.developer, identifier, ["Retain recurring verification reviews"], [capability], [], "Plan improvement")
                m.review_plan(self.developer, identifier, planned["plans"][-1]["plan_id"], "reviewed", "Manual plan review", "Review")
            m.assess(self.developer, identifier, capability, "Assess capability")
            before = m.history(self.developer, identifier)["record"]["level"]
            m.readiness(self.developer)
            self.assertEqual(before, m.history(self.developer, identifier)["record"]["level"])
            record = m.transition(self.developer, identifier, m.LEVELS[index + 1], "Explicit evidence-backed promotion")
        self.assertEqual("improving", record["level"])
        self.assertEqual(1, len(m.readiness(self.developer)["ready"]))
        self.assertEqual(["initial", "defined", "managed", "measured"], [a["level"] for a in record["assessments"]])
        self.assertEqual("measured", m.transition(self.developer, identifier, "measured", "Manual reassessment downgrade")["level"])
        for path, content in original.items():
            self.assertEqual(content, path.read_bytes())

    def test_maturity_invalid_transitions_scopes_and_manual_gaps(self):
        from src.developer import maturity as m
        source, _, record = self._maturity_setup()
        identifier = record["maturity_id"]
        for level in ("initial", "managed", "unknown"):
            with self.assertRaises(LocalWorkflowError):
                m.transition(self.developer, identifier, level, "Invalid transition")
        with self.assertRaises(LocalWorkflowError):
            m.create(self.developer, "recovery-verification", [source["assurance_id"]], "owner", "Duplicate area")
        with self.assertRaises(LocalWorkflowError):
            m.create(self.developer, "empty", [], "owner", "Empty scope")
        with self.assertRaises(LocalWorkflowError):
            m.create(self.developer, "unknown", ["assurance-unknown"], "owner", "Unknown scope")
        with self.assertRaises(LocalWorkflowError):
            m.assess(self.developer, identifier, "unknown-capability", "Invalid")
        m.assess(self.developer, identifier, m.CAPABILITIES[0], "Document manual gap", gaps=["Handoff instructions need review"], improvement_notes=["Arrange a review"])
        with self.assertRaises(LocalWorkflowError):
            m.transition(self.developer, identifier, "defined", "Cannot ignore manual gap")
        m.assess(self.developer, identifier, m.CAPABILITIES[0], "Manual gap reviewed and cleared")
        self.assertEqual("defined", m.transition(self.developer, identifier, "defined", "Ready")["level"])
        self.assertEqual(["Handoff instructions need review"], m.history(self.developer, identifier)["record"]["assessments"][0]["gaps"])

    def test_maturity_owner_handoff_requires_reassessment(self):
        from src.developer import maturity as m, recovery_governance as g
        source, _, record = self._maturity_setup()
        identifier = record["maturity_id"]
        m.assess(self.developer, identifier, m.CAPABILITIES[0], "Assess owner")
        m.assign(self.developer, identifier, "new-maintainer", "Maturity ownership handoff")
        review = m.review(self.developer, record["assurance_area"])
        self.assertIn("ownership_reassessment_required", review["capabilities"][0]["gaps"])
        with self.assertRaises(LocalWorkflowError):
            m.transition(self.developer, identifier, "defined", "Old owner assessment")
        m.assess(self.developer, identifier, m.CAPABILITIES[0], "New owner confirms scope")
        m.transition(self.developer, identifier, "defined", "Confirmed")
        self.assertEqual("developer", g.history(self.developer, source["assurance_id"])["record"]["owner"])
        with self.assertRaises(LocalWorkflowError):
            m.assign(self.developer, identifier, " ", "Invalid attribution")

    def test_maturity_stale_evidence_blocks_promotion_and_records_differences(self):
        from datetime import timedelta
        from src.developer import maturity as m, recovery_governance as g
        source, _, record = self._maturity_setup()
        identifier = record["maturity_id"]
        m.assess(self.developer, identifier, m.CAPABILITIES[0], "Owner")
        m.transition(self.developer, identifier, "defined", "Defined")
        original = m.assess(self.developer, identifier, m.CAPABILITIES[1], "Current verification")["assessments"][-1]
        future = g.assurance._timestamp(source["evidence"][0]["expires_at"]) + timedelta(seconds=1)
        with patch.object(g, "_now", return_value=future):
            report = m.review(self.developer, record["assurance_area"])
            self.assertIn("assessment_stale", report["capabilities"][1]["gaps"])
            with self.assertRaises(LocalWorkflowError):
                m.transition(self.developer, identifier, "managed", "Stale evidence")
            changed = m.assess(self.developer, identifier, m.CAPABILITIES[1], "Retain expiry finding")
            self.assertTrue(changed["assessments"][-1]["evidence_changes"]["changed"])
            self.assertTrue(m.readiness(self.developer)["needs_attention"])
        self.assertEqual(original, changed["assessments"][-2])
        self.assertEqual("defined", changed["level"])

    def test_maturity_plans_preserve_revisions_and_manual_reviews(self):
        from src.developer import maturity as m
        _, _, record = self._maturity_setup()
        identifier = record["maturity_id"]
        record = m.add_plan(self.developer, identifier, ["Review retained evidence"], [m.CAPABILITIES[1]], [], "Initial plan")
        first = record["plans"][0]
        with self.assertRaises(LocalWorkflowError):
            m.review_plan(self.developer, identifier, first["plan_id"], "completed", "Skip review", "Invalid")
        m.review_plan(self.developer, identifier, first["plan_id"], "reviewed", "Evidence inspected", "Manual review")
        record = m.review_plan(self.developer, identifier, first["plan_id"], "completed", "Review activity complete", "Manual completion")
        completed = record["plans"][0]
        with self.assertRaises(LocalWorkflowError):
            m.review_plan(self.developer, identifier, first["plan_id"], "reviewed", "Cannot rewrite", "Invalid")
        record = m.add_plan(self.developer, identifier, ["Expand review instructions"], [m.CAPABILITIES[2]], [], "Next plan version", supersedes=first["plan_id"])
        self.assertEqual(completed, record["plans"][0])
        self.assertEqual(first["plan_id"], record["plans"][1]["supersedes"])
        self.assertEqual(2, len(completed["review_history"]))
        self.assertEqual(2, len(m.plans(self.developer)["plans"]))
        self.assertIn("manually_reviewed_plan_missing", m.review(self.developer, record["assurance_area"])["capabilities"][3]["gaps"])

    def test_maturity_finding_links_require_scope_and_confirmed_resolution(self):
        from src.developer import assurance_operations as ops, maturity as m, recovery_governance as g
        source, operation = self._assurance_operations_setup()
        ops.record_review(self.developer, operation["operation_id"], "Capture unresolved findings")
        finding = ops.findings(self.developer)["active"][0]
        record = m.create(self.developer, "finding-management", [source["assurance_id"]], "maintainer", "Area")
        identifier = record["maturity_id"]
        with self.assertRaises(LocalWorkflowError):
            m.add_plan(self.developer, identifier, ["Repair"], [m.CAPABILITIES[1]], ["unrelated-finding"], "Invalid reference")
        planned = m.add_plan(self.developer, identifier, ["Activate and verify assurance"], [m.CAPABILITIES[1], m.CAPABILITIES[2]], [finding["finding_id"]], "Linked improvement")
        plan_id = planned["plans"][0]["plan_id"]
        m.review_plan(self.developer, identifier, plan_id, "reviewed", "Review pending work", "Manual")
        with self.assertRaises(LocalWorkflowError):
            m.review_plan(self.developer, identifier, plan_id, "completed", "Still unresolved", "Invalid")
        g.change(self.developer, source["assurance_id"], "transition", "Activate", status="active")
        g.record_check(self.developer, source["assurance_id"], source["assurance_id"], "Record evidence")
        with self.assertRaises(LocalWorkflowError):
            m.review_plan(self.developer, identifier, plan_id, "completed", "Operations review is still old", "Invalid")
        ops.record_review(self.developer, operation["operation_id"], "Confirm findings resolved")
        before = ops.findings(self.developer)
        completed = m.review_plan(self.developer, identifier, plan_id, "completed", "Resolution reviewed", "Complete")
        self.assertEqual("completed", completed["plans"][0]["status"])
        self.assertEqual("open", completed["plans"][0]["finding_snapshots"][0]["status"])
        self.assertEqual(before, ops.findings(self.developer))

    def test_maturity_missing_source_history_retains_assessments(self):
        from src.developer import maturity as m, recovery_governance as g
        _, _, record = self._maturity_setup()
        identifier = record["maturity_id"]
        m.assess(self.developer, identifier, m.CAPABILITIES[0], "Retain source evidence")
        original = m.history(self.developer, identifier)
        with patch.object(g, "review", side_effect=LocalWorkflowError("Governance history unavailable")):
            review = m.review(self.developer, record["assurance_area"])
            self.assertTrue(review["missing_evidence"])
            self.assertEqual([], m.readiness(self.developer)["ready"])
            with self.assertRaises(LocalWorkflowError):
                m.transition(self.developer, identifier, "defined", "Unavailable source")
        self.assertEqual(original, m.history(self.developer, identifier))

    def test_maturity_cli_reports_read_only_and_prior_journals_unchanged(self):
        from src.developer import assurance_operations as ops, maturity as m
        source, operation = self._assurance_operations_setup(verified=True)
        ops.record_review(self.developer, operation["operation_id"], "Current review")
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        commands = [("maturity-create", "recovery-verification", "--assurance-id", source["assurance_id"], "--owner", "maintainer"),
                    ("maturity-assess", "maturity-001", m.CAPABILITIES[0], "--note", "Owner confirmed"),
                    ("maturity-transition", "maturity-001", "defined"),
                    ("maturity-assign", "maturity-001", "--owner", "next-maintainer"),
                    ("maturity-plan-add", "maturity-001", "--improvement", "Review evidence", "--capability", m.CAPABILITIES[1]),
                    ("maturity-plan-review", "maturity-001", "maturity-001-plan-001", "reviewed", "--note", "Manual review")]
        for command in commands:
            with redirect_stdout(StringIO()):
                self.assertEqual(0, main(["local", *command, "--reason", "Explicit maturity action", "--workspace", str(self.workspace_path)]))
        for path, content in before.items():
            self.assertEqual(content, path.read_bytes())
        all_files = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        for command in ("maturity-status", "maturity-history", "maturity-review", "maturity-readiness", "maturity-plan"):
            args = ["local", command]
            if command == "maturity-history":
                args.append("maturity-001")
            elif command == "maturity-review":
                args.append("recovery-verification")
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main([*args, "--workspace", str(self.workspace_path), "--json"]))
            self.assertEqual(m.MODE, json.loads(output.getvalue())["mode"])
        self.assertEqual(all_files, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})

    def test_maturity_atomic_publication_corruption_and_isolation(self):
        from src.developer import maturity as m
        self.assertEqual([], m.readiness(self.developer)["ready"])
        self.assertFalse(m._root(self.developer).exists())
        with self.assertRaises(LocalWorkflowError):
            m.history(self.developer, "unknown")
        with self.assertRaises(LocalWorkflowError):
            m.review(self.developer, "unknown")
        _, _, record = self._maturity_setup()
        original = m.history(self.developer, record["maturity_id"])
        with patch.object(m.os, "link", side_effect=FileExistsError("Concurrent append")):
            with self.assertRaises(LocalWorkflowError):
                m.assess(self.developer, record["maturity_id"], m.CAPABILITIES[0], "Interrupted publication")
        self.assertEqual(original, m.history(self.developer, record["maturity_id"]))
        self.assertFalse(list(m._root(self.developer).glob("*.tmp")))
        path = next(m._root(self.developer).glob("*.json"))
        content = path.read_bytes()
        event = json.loads(content)
        event["sequence"] = 2
        path.write_text(json.dumps(event), encoding="utf-8")
        with self.assertRaises(LocalWorkflowError):
            m.status(self.developer)
        path.write_bytes(content)
        with self.assertRaises(LocalWorkflowError):
            m.readiness(DeveloperWorkspace(self.research_root / "maturity", research_roots=[self.research_root]))


    def _evolution_setup(self, capability=None):
        from src.developer import evolution as e, maturity as m
        source, operation, mature = self._maturity_setup()
        capability = capability or m.CAPABILITIES[0]
        m.assess(self.developer, mature["maturity_id"], capability, "Assess source capability")
        record = e.create(self.developer, "recovery-verification", "improvement", "maintainer", "Plan evolution")
        e.record_impact(self.developer, record["evolution_id"], [capability], [mature["maturity_id"]], [],
                        ["Scope reviewed"], [], "Capture source evidence")
        return source, operation, mature, record

    def test_evolution_lifecycle_and_append_only_decisions(self):
        from src.developer import evolution as e, maturity as m
        _, _, mature, record = self._evolution_setup()
        identifier = record["evolution_id"]
        original = {p: p.read_bytes() for p in self.workspace_path.rglob("*.json")}
        before = m.readiness(self.developer)
        for state in ("reviewing", "approved", "implemented", "verified", "retired"):
            record = e.transition(self.developer, identifier, state, "Manual decision", "Reviewed change")
            self.assertEqual(state, record["status"])
        self.assertEqual(["planned", "planned", "reviewing", "approved", "implemented", "verified", "retired"],
                         [h["status"] for h in record["history"]])
        self.assertEqual(1, len(e.status(self.developer)["retired"]))
        self.assertEqual(before, m.readiness(self.developer))
        for path, content in original.items():
            self.assertEqual(content, path.read_bytes())
        self.assertEqual("initial", m.history(self.developer, mature["maturity_id"])["record"]["level"])

    def test_evolution_invalid_transitions_and_terminal_records_do_not_write(self):
        from src.developer import evolution as e
        record = e.create(self.developer, "recovery-verification", "improvement", "owner", "Plan")
        identifier = record["evolution_id"]
        for state in ("planned", "approved", "implemented", "verified", "unknown"):
            with self.assertRaises(LocalWorkflowError):
                e.transition(self.developer, identifier, state, "Decision", "Invalid")
        self.assertEqual(record, e.history(self.developer, identifier)["record"])
        e.transition(self.developer, identifier, "reviewing", "Manual review", "Review")
        with self.assertRaises(LocalWorkflowError):
            e.transition(self.developer, identifier, "approved", "Decision", "Missing evidence")
        self.assertIn("impact_missing", e.review(self.developer, identifier)["missing_evidence"])
        e.transition(self.developer, identifier, "retired", "Withdraw", "Retire")
        retired = e.history(self.developer, identifier)
        with self.assertRaises(LocalWorkflowError):
            e.add_plan(self.developer, identifier, ["Improve"], [], ["Review"], "owner", "Invalid")
        with self.assertRaises(LocalWorkflowError):
            e.transition(self.developer, identifier, "planned", "Reopen", "Invalid")
        self.assertEqual(retired, e.history(self.developer, identifier))

    def test_evolution_impact_scope_risks_and_revision_history(self):
        from src.developer import evolution as e, maturity as m
        _, _, mature, record = self._evolution_setup()
        identifier, mid = record["evolution_id"], mature["maturity_id"]
        original = e.impact(self.developer, identifier)["current"]
        for capabilities, mids, findings in ((["unknown"], [mid], []), ([], [mid], []),
                                             ([m.CAPABILITIES[0]], ["missing"], []),
                                             ([m.CAPABILITIES[0]], [mid], ["missing"])):
            with self.assertRaises(LocalWorkflowError):
                e.record_impact(self.developer, identifier, capabilities, mids, findings, [], [], "Invalid scope")
        e.record_impact(self.developer, identifier, [m.CAPABILITIES[0]], [mid], [], ["Needs review"], ["Owner risk"], "Risk update")
        e.transition(self.developer, identifier, "reviewing", "Review", "Review")
        self.assertEqual(["Owner risk"], e.review(self.developer, identifier)["warnings"])
        with self.assertRaises(LocalWorkflowError):
            e.transition(self.developer, identifier, "approved", "Approve", "Unresolved risk")
        e.record_impact(self.developer, identifier, [m.CAPABILITIES[0]], [mid], [], ["Risk resolved manually"], [], "Refresh")
        self.assertEqual(["manual_approval"], e.review(self.developer, identifier)["ready"])
        self.assertEqual(original, e.impact(self.developer, identifier)["impact_history"][0])
        e.transition(self.developer, identifier, "approved", "Approve", "Decision")
        with self.assertRaises(LocalWorkflowError):
            e.record_impact(self.developer, identifier, [m.CAPABILITIES[0]], [mid], [], [], [], "Cannot silently alter approval")

    def test_evolution_stale_maturity_blocks_verification_until_refresh(self):
        from src.developer import evolution as e, maturity as m
        _, _, mature, record = self._evolution_setup()
        identifier, mid = record["evolution_id"], mature["maturity_id"]
        for state in ("reviewing", "approved", "implemented"):
            e.transition(self.developer, identifier, state, "Decision", "Manual action")
        with self.assertRaises(LocalWorkflowError):
            e.record_impact(self.developer, identifier, [m.CAPABILITIES[1]], [mid], [], [], [], "Changed implemented scope")
        m.assign(self.developer, mid, "new-owner", "Handoff")
        report = e.review(self.developer, identifier)
        self.assertIn("impact_evidence_stale", report["missing_evidence"])
        self.assertEqual([], report["ready"])
        with self.assertRaises(LocalWorkflowError):
            e.transition(self.developer, identifier, "verified", "Verify", "Stale source")
        m.assess(self.developer, mid, m.CAPABILITIES[0], "New owner assessment")
        e.record_impact(self.developer, identifier, [m.CAPABILITIES[0]], [mid], [], ["Review handoff"], [], "Refresh")
        self.assertEqual(["manual_verification"], e.review(self.developer, identifier)["ready"])
        e.transition(self.developer, identifier, "verified", "Verified externally", "Manual verification")
        self.assertEqual(1, len(e.status(self.developer)["verified"]))

    def test_evolution_assurance_evidence_expiry_and_missing_source(self):
        from datetime import timedelta
        from src.developer import evolution as e, maturity as m, recovery_governance as g
        _, _, mature, record = self._evolution_setup(m.CAPABILITIES[1])
        identifier = record["evolution_id"]
        e.transition(self.developer, identifier, "reviewing", "Review", "Review")
        self.assertEqual(["manual_approval"], e.review(self.developer, identifier)["ready"])
        with patch.object(g, "_now", return_value=g._now() + timedelta(days=400)):
            self.assertTrue(e.review(self.developer, identifier)["missing_evidence"])
            with self.assertRaises(LocalWorkflowError):
                e.transition(self.developer, identifier, "approved", "Approve", "Expired")
        original = e.history(self.developer, identifier)
        with patch.object(m, "history", side_effect=LocalWorkflowError("Source unavailable")):
            self.assertTrue(e.review(self.developer, identifier)["missing_evidence"])
            self.assertEqual(original, e.history(self.developer, identifier))

    def test_evolution_planning_revisions_preserve_ownership_and_dependencies(self):
        from src.developer import evolution as e
        identifier = e.create(self.developer, "recovery-verification", "improvement", "owner", "Plan")["evolution_id"]
        record = e.add_plan(self.developer, identifier, ["Document renewal"], ["recovery-ownership"],
                            ["Review next quarter"], "planner", "Direction")
        first = record["plans"][0]
        e.add_plan(self.developer, identifier, ["Review renewal procedure"], ["recovery-evidence-validation"],
                   ["Review after evidence renewal"], "new-planner", "Revise direction", first["plan_id"])
        plans = e.plans(self.developer)["plans"]
        self.assertFalse(plans[0]["current"])
        self.assertTrue(plans[1]["current"])
        self.assertEqual(first, e.history(self.developer, identifier)["record"]["plans"][0])
        self.assertEqual("planner", plans[0]["owner"])
        for supersedes in ("missing", first["plan_id"]):
            with self.assertRaises(LocalWorkflowError):
                e.add_plan(self.developer, identifier, ["Improve"], [], ["Review"], "owner", "Bad revision", supersedes)
        self.assertEqual(2, len(e.plans(self.developer)["plans"]))

    def test_evolution_cli_reports_read_only_and_source_compatibility(self):
        from src.cli import main
        from src.developer import maturity as m
        _, _, mature = self._maturity_setup()
        m.assess(self.developer, mature["maturity_id"], m.CAPABILITIES[0], "Assess")
        commands = [("evolution-create", "recovery-verification", "--owner", "maintainer"),
                    ("evolution-impact-add", "evolution-001", "--capability", m.CAPABILITIES[0], "--maturity-id", mature["maturity_id"], "--note", "Reviewed"),
                    ("evolution-transition", "evolution-001", "reviewing", "--note", "Manual decision"),
                    ("evolution-plan-add", "evolution-001", "--improvement", "Review renewal", "--dependency", "recovery-ownership", "--milestone", "Quarterly review", "--owner", "planner")]
        for command in commands:
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(0, main(["local", *command, "--reason", "Explicit action", "--workspace", str(self.workspace_path), "--json"]))
            self.assertEqual("evolution-001", json.loads(output.getvalue())["evolution_id"])
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        for command in ("evolution-status", "evolution-history", "evolution-impact", "evolution-review", "evolution-plan"):
            args = ["local", command]
            if command not in {"evolution-status", "evolution-plan"}:
                args.append("evolution-001")
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(0, main([*args, "--workspace", str(self.workspace_path), "--json"]))
            self.assertEqual("developer-recovery-evolution", json.loads(output.getvalue())["mode"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})

    def test_evolution_linked_findings_require_manual_source_resolution(self):
        from src.developer import evolution as e, maturity as m, assurance_operations as ops, recovery_governance as g
        source, operation = self._assurance_operations_setup()
        ops.record_review(self.developer, operation["operation_id"], "Capture findings")
        finding = ops.findings(self.developer)["active"][0]["finding_id"]
        mid = m.create(self.developer, "finding-management", [source["assurance_id"]], "owner", "Scope")["maturity_id"]
        m.assess(self.developer, mid, m.CAPABILITIES[0], "Assess ownership")
        identifier = e.create(self.developer, "recovery-verification", "improvement", "owner", "Plan")["evolution_id"]
        e.record_impact(self.developer, identifier, [m.CAPABILITIES[0]], [mid], [finding], [], [], "Link finding")
        e.transition(self.developer, identifier, "reviewing", "Review", "Review")
        self.assertIn(finding + ":finding_unresolved", e.review(self.developer, identifier)["missing_evidence"])
        g.change(self.developer, source["assurance_id"], "transition", "Activate", status="active")
        g.record_check(self.developer, source["assurance_id"], source["assurance_id"], "Record evidence")
        self.assertIn(finding + ":finding_unresolved", e.review(self.developer, identifier)["missing_evidence"])
        ops.record_review(self.developer, operation["operation_id"], "Confirm resolved")
        e.record_impact(self.developer, identifier, [m.CAPABILITIES[0]], [mid], [finding], [], [], "Refresh evidence")
        before = ops.findings(self.developer)
        self.assertEqual(["manual_approval"], e.review(self.developer, identifier)["ready"])
        e.transition(self.developer, identifier, "approved", "Approve", "Manual approval")
        self.assertEqual(before, ops.findings(self.developer))
        old = e.impact(self.developer, identifier)["impact_history"][0]["evidence"]["references"]
        self.assertEqual("open", next(r["snapshot"]["status"] for r in old if r["reference"] == finding))

    def test_evolution_journal_atomicity_corruption_and_workspace_isolation(self):
        from src.developer import evolution as e
        self.assertEqual([], e.status(self.developer)["evolutions"])
        self.assertEqual([], e.plans(self.developer)["plans"])
        self.assertFalse(e._root(self.developer).exists())
        record = e.create(self.developer, "recovery-verification", "improvement", "owner", "Plan")
        with patch.object(e.os, "link", side_effect=FileExistsError("Concurrent append")):
            with self.assertRaises(LocalWorkflowError):
                e.transition(self.developer, record["evolution_id"], "reviewing", "Review", "Review")
        self.assertEqual(record, e.history(self.developer, record["evolution_id"])["record"])
        self.assertFalse(list(e._root(self.developer).glob("*.tmp")))
        path = next(e._root(self.developer).glob("*.json"))
        original = path.read_bytes()
        event = json.loads(original)
        event["previous_digest"] = "broken"
        path.write_text(json.dumps(event), encoding="utf-8")
        with self.assertRaises(LocalWorkflowError):
            e.status(self.developer)
        path.write_bytes(original)
        with self.assertRaises(LocalWorkflowError):
            e.status(DeveloperWorkspace(self.research_root / "evolution", research_roots=[self.research_root]))


    def _strategic_setup(self):
        from src.developer import strategic_governance as g
        source, operation, mature, evolved = self._evolution_setup()
        record = g.create(self.developer, "Improve recovery verification reliability", "strategy-owner",
                          ["recovery-ownership"], [evolved["evolution_id"]], [], ["Initial direction"], [], "Define strategy")
        record = g.add_roadmap(self.developer, record["governance_id"], "Review ownership procedure", "roadmap-owner", "Next quarter", [], "Plan roadmap")
        return source, mature, evolved, record

    def _strategic_activate(self, record):
        from src.developer import strategic_governance as g
        identifier = record["governance_id"]
        g.transition(self.developer, identifier, "reviewing", "Start review", "Review")
        for state in ("approved", "active"):
            g.record_review(self.developer, identifier, "Evidence reviewed manually", "Review")
            record = g.transition(self.developer, identifier, state, "Human decision", "Decision")
        return record

    def test_strategic_lifecycle_reviews_completion_and_prior_history(self):
        from src.developer import strategic_governance as g, evolution as e, maturity as m
        _, mature, evolved, record = self._strategic_setup()
        identifier, rid = record["governance_id"], record["roadmap"][0]["roadmap_id"]
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*.json")}
        readiness = m.readiness(self.developer)
        self._strategic_activate(record)
        for state in ("scheduled", "active", "completed"):
            g.transition_roadmap(self.developer, identifier, rid, state, "Manual roadmap decision", "Decision")
        g.record_review(self.developer, identifier, "Inspect completion", "Review")
        with self.assertRaises(LocalWorkflowError):
            g.transition(self.developer, identifier, "completed", "Not yet verified", "Invalid")
        for state in ("reviewing", "approved", "implemented", "verified"):
            e.transition(self.developer, evolved["evolution_id"], state, "Explicit source decision", "Source workflow")
        g.record_review(self.developer, identifier, "Verified source reviewed", "Review")
        self.assertEqual(["manual_completed"], g.review(self.developer, identifier)["ready"])
        g.transition(self.developer, identifier, "completed", "Objective achieved", "Decision")
        dependent = g.create(self.developer, "Follow-up strategy", "owner", ["capability"], [], [identifier], [], [], "Dependency")
        self.assertTrue(g.dependencies(self.developer)["dependencies"][0]["resolved"])
        record = g.transition(self.developer, identifier, "retired", "Archive direction", "Decision")
        self.assertFalse(g.dependencies(self.developer)["dependencies"][0]["resolved"])
        self.assertEqual("retired", record["status"])
        self.assertEqual(4, len(record["reviews"]))
        self.assertEqual(readiness, m.readiness(self.developer))
        for path, content in before.items():
            self.assertEqual(content, path.read_bytes())
        self.assertEqual("initial", m.history(self.developer, mature["maturity_id"])["record"]["level"])

    def test_strategic_invalid_transitions_missing_evidence_and_terminal_states(self):
        from src.developer import strategic_governance as g
        record = g.create(self.developer, "Future direction", "owner", ["evidence-validation"], [], [], [], [], "Plan")
        identifier = record["governance_id"]
        for state in ("planned", "approved", "active", "completed", "unknown"):
            with self.assertRaises(LocalWorkflowError):
                g.transition(self.developer, identifier, state, "Manual", "Invalid")
        self.assertEqual(record, g.history(self.developer, identifier)["record"])
        g.transition(self.developer, identifier, "reviewing", "Review", "Review")
        g.record_review(self.developer, identifier, "Incomplete proposal reviewed", "Review")
        self.assertIn("linked_evolution_missing", g.review(self.developer, identifier)["missing_evidence"])
        with self.assertRaises(LocalWorkflowError):
            g.transition(self.developer, identifier, "approved", "Approve", "Invalid")
        record = g.transition(self.developer, identifier, "retired", "Withdraw", "Decision")
        with self.assertRaises(LocalWorkflowError):
            g.add_roadmap(self.developer, identifier, "New work", "owner", "Next year", [], "Invalid")
        self.assertEqual(record, g.history(self.developer, identifier)["record"])

    def test_strategic_objective_revisions_keep_prior_links_and_ownership(self):
        from src.developer import strategic_governance as g
        _, _, evolved, record = self._strategic_setup()
        identifier = record["governance_id"]
        original = g.history(self.developer, identifier)["record"]["history"][:]
        record = g.update(self.developer, identifier, "Renew assurance direction", "new-owner", ["evidence-validation"],
                          [evolved["evolution_id"]], ["verification-scheduling"], ["Revised after review"], ["Pending resources"], "Revision")
        self.assertEqual(original, record["history"][:len(original)])
        self.assertEqual("new-owner", record["owner"])
        self.assertEqual("strategy-owner", record["history"][0]["owner"])
        self.assertEqual([evolved["evolution_id"]], record["history"][0]["evolution_ids"])
        report = g.review(self.developer, identifier)
        self.assertIn("Pending resources", report["risks"])
        self.assertTrue(g.plan_review(self.developer)["risks"])
        with self.assertRaises(LocalWorkflowError):
            g.update(self.developer, identifier, "Invalid link", "owner", ["capability"], ["evolution-missing"], [], [], [], "Invalid")

    def test_strategic_dependency_visibility_manual_resolution_and_cycles(self):
        from src.developer import strategic_governance as g
        first = g.create(self.developer, "First", "owner", ["evidence-validation"], [], ["verification-scheduling"], [], [], "Plan")
        second = g.create(self.developer, "Second", "owner", ["evidence-validation"], [], [first["governance_id"]], [], [], "Plan")
        before = g.status(self.developer)
        with self.assertRaises(LocalWorkflowError):
            g.update(self.developer, first["governance_id"], "First", "owner", ["evidence-validation"], [], [second["governance_id"]], [], [], "Cycle")
        with self.assertRaises(LocalWorkflowError):
            g.create(self.developer, "Unknown dependency", "owner", ["capability"], [], ["governance-999"], [], [], "Invalid")
        self.assertEqual(before, g.status(self.developer))
        self.assertEqual(2, len(g.dependencies(self.developer)["blocked"]))
        g.review_dependency(self.developer, first["governance_id"], "verification-scheduling", "resolved", "Schedule reviewed externally", "Manual resolution")
        self.assertEqual(1, len(g.dependencies(self.developer)["blocked"]))
        with self.assertRaises(LocalWorkflowError):
            g.review_dependency(self.developer, second["governance_id"], first["governance_id"], "resolved", "Cannot override", "Invalid")
        g.review_dependency(self.developer, first["governance_id"], "verification-scheduling", "unresolved", "Prerequisite changed", "Reopen")
        self.assertEqual(2, len(g.dependencies(self.developer)["blocked"]))
        self.assertEqual(2, len(g.history(self.developer, first["governance_id"])["record"]["dependency_reviews"]))

    def test_strategic_roadmap_updates_deferrals_and_dependencies(self):
        from src.developer import strategic_governance as g
        _, _, _, record = self._strategic_setup()
        identifier, first = record["governance_id"], record["roadmap"][0]["roadmap_id"]
        record = g.add_roadmap(self.developer, identifier, "Follow-up review", "second-owner", "Following quarter", [first], "Dependency")
        second = record["roadmap"][-1]["roadmap_id"]
        g.update_roadmap(self.developer, identifier, first, "Revised procedure review", "new-owner", "2027 Q1", [], "Revise period")
        with self.assertRaises(LocalWorkflowError):
            g.update_roadmap(self.developer, identifier, first, "Cycle", "owner", "Later", [second], "Invalid")
        with self.assertRaises(LocalWorkflowError):
            g.transition_roadmap(self.developer, identifier, first, "active", "Skip scheduling", "Invalid")
        self._strategic_activate(record)
        g.transition_roadmap(self.developer, identifier, second, "scheduled", "Schedule manually", "Decision")
        with self.assertRaises(LocalWorkflowError):
            g.transition_roadmap(self.developer, identifier, second, "active", "Dependency unresolved", "Invalid")
        for state in ("scheduled", "deferred", "scheduled", "active", "completed"):
            g.transition_roadmap(self.developer, identifier, first, state, "Manual roadmap decision", "Decision")
        g.transition_roadmap(self.developer, identifier, second, "active", "Prerequisite complete", "Decision")
        report = g.dependencies(self.developer)
        self.assertFalse(report["blocked"])
        items = g.status(self.developer)["roadmap"]
        self.assertEqual([first, second], [r["roadmap_id"] for r in items])
        self.assertEqual("roadmap-owner", items[0]["history"][0]["owner"])
        self.assertEqual("2027 Q1", items[0]["target_period"])
        with self.assertRaises(LocalWorkflowError):
            g.update_roadmap(self.developer, identifier, first, "Completed edit", "owner", "Later", [], "Invalid")

    def test_strategic_review_staleness_and_evolution_maturity_compatibility(self):
        from src.developer import strategic_governance as g, evolution as e, maturity as m
        _, mature, evolved, record = self._strategic_setup()
        identifier = record["governance_id"]
        g.transition(self.developer, identifier, "reviewing", "Review", "Review")
        g.record_review(self.developer, identifier, "Review evidence", "Review")
        self.assertEqual(["manual_approved"], g.review(self.developer, identifier)["ready"])
        e.add_plan(self.developer, evolved["evolution_id"], ["Renew instructions"], [], ["Quarterly review"], "owner", "Source plan")
        with self.assertRaises(LocalWorkflowError):
            g.transition(self.developer, identifier, "approved", "Stale review", "Invalid")
        g.record_review(self.developer, identifier, "Review changed plan", "Review")
        m.assign(self.developer, mature["maturity_id"], "new-owner", "Handoff")
        report = g.review(self.developer, identifier)
        self.assertTrue(report["missing_evidence"])
        self.assertFalse(report["ready"])
        g.record_review(self.developer, identifier, "Inspect missing evidence", "Review")
        with self.assertRaises(LocalWorkflowError):
            g.transition(self.developer, identifier, "approved", "Cannot force approval", "Invalid")
        prior = g.history(self.developer, identifier)
        with patch.object(e, "history", side_effect=LocalWorkflowError("Source unavailable")):
            self.assertIn(evolved["evolution_id"] + ":evolution_unavailable", g.review(self.developer, identifier)["missing_evidence"])
            self.assertEqual(prior, g.history(self.developer, identifier))

    def test_strategic_cli_reports_are_read_only_and_preserve_assurance_history(self):
        from src.developer import strategic_governance as g
        _, _, evolved, record = self._strategic_setup()
        identifier = record["governance_id"]
        prior_sources = {p: p.read_bytes() for p in self.workspace_path.rglob("*.json") if g._root(self.developer) not in p.parents}
        def run(*args):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main(["local", *args, "--workspace", str(self.workspace_path), "--json"]))
            return json.loads(output.getvalue())
        created = run("governance-create", "CLI objective", "--owner", "owner", "--capability", "evidence-validation", "--evolution-id", evolved["evolution_id"], "--reason", "Create")
        cid = created["governance_id"]
        run("governance-update", cid, "--objective", "Updated CLI objective", "--owner", "owner", "--capability", "evidence-validation", "--evolution-id", evolved["evolution_id"], "--dependency", "scheduling", "--reason", "Update")
        road = run("governance-roadmap-add", cid, "--description", "Review", "--owner", "owner", "--target-period", "Next quarter", "--reason", "Plan")["roadmap"][0]["roadmap_id"]
        run("governance-roadmap-update", cid, "--roadmap-id", road, "--description", "Review procedure", "--owner", "new-owner", "--target-period", "Later quarter", "--reason", "Update")
        run("governance-roadmap-transition", cid, "scheduled", "--roadmap-id", road, "--note", "Manual scheduling", "--reason", "Decision")
        run("governance-dependency-review", cid, "scheduling", "resolved", "--note", "Prerequisite confirmed", "--reason", "Review")
        run("governance-transition", cid, "reviewing", "--note", "Start review", "--reason", "Review")
        run("governance-record-review", cid, "--note", "Current evidence reviewed", "--reason", "Review")
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        for command in ("governance-status", "governance-history", "governance-review", "governance-dependencies", "governance-plan-review"):
            args = (command, identifier) if command in {"governance-history", "governance-review"} else (command,)
            self.assertEqual(g.MODE, run(*args)["mode"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        for path, content in prior_sources.items():
            self.assertEqual(content, path.read_bytes())

    def test_strategic_external_roadmap_prerequisites_require_explicit_review(self):
        from src.developer import strategic_governance as g
        _, _, _, record = self._strategic_setup()
        identifier, rid = record["governance_id"], record["roadmap"][0]["roadmap_id"]
        g.update_roadmap(self.developer, identifier, rid, "Review procedure", "owner", "Next quarter", ["verification-scheduling"], "Prerequisite")
        self._strategic_activate(record)
        g.transition_roadmap(self.developer, identifier, rid, "scheduled", "Manual schedule", "Decision")
        with self.assertRaises(LocalWorkflowError):
            g.transition_roadmap(self.developer, identifier, rid, "active", "Unresolved prerequisite", "Invalid")
        g.review_dependency(self.developer, identifier, "verification-scheduling", "resolved", "Schedule checked externally", "Manual resolution", roadmap_id=rid)
        g.transition_roadmap(self.developer, identifier, rid, "active", "Prerequisite reviewed", "Decision")
        g.review_dependency(self.developer, identifier, "verification-scheduling", "unresolved", "Schedule changed", "Reopen", roadmap_id=rid)
        with self.assertRaises(LocalWorkflowError):
            g.transition_roadmap(self.developer, identifier, rid, "completed", "Dependency reopened", "Invalid")
        self.assertTrue(g.plan_review(self.developer)["warnings"])
        self.assertEqual("active", g.status(self.developer)["roadmap"][0]["status"])

    def test_strategic_journal_atomicity_corruption_empty_reports_and_isolation(self):
        from src.developer import strategic_governance as g
        self.assertEqual([], g.status(self.developer)["objectives"])
        self.assertEqual([], g.dependencies(self.developer)["dependencies"])
        self.assertEqual([], g.plan_review(self.developer)["ready"])
        self.assertFalse(g._root(self.developer).exists())
        for reason, owner in (("", "owner"), ("Plan", "")):
            with self.assertRaises(LocalWorkflowError):
                g.create(self.developer, "Objective", owner, ["capability"], [], [], [], [], reason)
        record = g.create(self.developer, "Objective", "owner", ["capability"], [], [], [], [], "Plan")
        identifier = record["governance_id"]
        with patch.object(g.os, "link", side_effect=FileExistsError("Concurrent append")):
            with self.assertRaises(LocalWorkflowError):
                g.transition(self.developer, identifier, "reviewing", "Review", "Review")
        self.assertEqual(record, g.history(self.developer, identifier)["record"])
        self.assertFalse(list(g._root(self.developer).glob("*.tmp")))
        path = next(g._root(self.developer).glob("*.json"))
        original = path.read_bytes()
        event = json.loads(original)
        event["previous_digest"] = "broken"
        path.write_text(json.dumps(event), encoding="utf-8")
        with self.assertRaises(LocalWorkflowError):
            g.status(self.developer)
        path.write_bytes(original)
        with self.assertRaises(LocalWorkflowError):
            g.status(DeveloperWorkspace(self.research_root / "strategic", research_roots=[self.research_root]))


    def _governance_ops_setup(self):
        from src.developer import governance_operations as o
        source, mature, evolved, strategic = self._strategic_setup()
        record = o.create(self.developer, strategic["governance_id"], "Continue assurance improvement", "decision-owner", "Record decision proposal")
        return source, mature, evolved, strategic, record

    def _governance_ops_decide(self, identifier):
        from src.developer import governance_operations as o
        o.transition(self.developer, identifier, "reviewing", "Begin review", "Review")
        o.record_review(self.developer, identifier, "Human review of current governance", [], "Decision rationale confirmed manually", "Review")
        return o.transition(self.developer, identifier, "decided", "Proceed with follow-up", "Human decision")

    def test_governance_ops_decision_lifecycle_actions_and_closure_history(self):
        from datetime import timedelta
        from src.developer import governance_operations as o
        _, _, _, _, record = self._governance_ops_setup()
        identifier = record["decision_id"]
        original = {p: p.read_bytes() for p in self.workspace_path.rglob("*.json")}
        o.transition(self.developer, identifier, "deferred", "Await review", "Defer")
        o.transition(self.developer, identifier, "open", "Resume consideration", "Resume")
        self._governance_ops_decide(identifier)
        item = o.add_action(self.developer, identifier, "Review renewal procedure", "action-owner", (o._now().date() + timedelta(days=7)).isoformat(), "Follow-up")["actions"][0]
        with self.assertRaises(LocalWorkflowError):
            o.transition(self.developer, identifier, "closed", "Open action remains", "Invalid")
        o.transition_action(self.developer, identifier, item["action_id"], "in_progress", "Started manually", [], None, "Work")
        o.transition_action(self.developer, identifier, item["action_id"], "completed", "Reviewed procedure", [], "Procedure checked manually", "Complete")
        before = o.decisions(self.developer)
        self.assertEqual(1, len(o.close_check(self.developer)["passed"]))
        self.assertEqual(before, o.decisions(self.developer))
        closed = o.transition(self.developer, identifier, "closed", "Closure evidence reviewed", "Close explicitly")
        self.assertEqual("closed", closed["status"])
        self.assertFalse(closed["history"][-1]["closure"]["blocked"])
        self.assertEqual("Procedure checked manually", closed["actions"][0]["completion_evidence"]["manual_reason"])
        for path, content in original.items():
            self.assertEqual(content, path.read_bytes())

    def test_governance_ops_invalid_transitions_attribution_and_missing_proof(self):
        from src.developer import governance_operations as o
        _, _, _, strategic, record = self._governance_ops_setup()
        identifier = record["decision_id"]
        for state in ("open", "decided", "closed", "unknown"):
            with self.assertRaises(LocalWorkflowError):
                o.transition(self.developer, identifier, state, "Invalid", "Invalid")
        self.assertEqual(record, o.decisions(self.developer)["decisions"][0])
        for owner, reason in (("", "Reason"), ("owner", "")):
            with self.assertRaises(LocalWorkflowError):
                o.create(self.developer, strategic["governance_id"], "Decision", owner, reason)
        with self.assertRaises(LocalWorkflowError):
            o.create(self.developer, "governance-999", "Unknown objective", "owner", "Invalid")
        item = o.add_action(self.developer, identifier, "Follow up", "owner", "2027-01-01", "Action")["actions"][0]
        with self.assertRaises(LocalWorkflowError):
            o.transition_action(self.developer, identifier, item["action_id"], "completed", "Skip progress", [], None, "Invalid")
        o.transition_action(self.developer, identifier, item["action_id"], "in_progress", "Start", [], None, "Work")
        with self.assertRaises(LocalWorkflowError):
            o.transition_action(self.developer, identifier, item["action_id"], "completed", "Missing proof", [], None, "Invalid")
        self.assertEqual("in_progress", o.actions(self.developer)["actions"][0]["status"])
        self.assertTrue(o.followup(self.developer)["missing_evidence"])

    def test_governance_ops_overdue_deferrals_and_post_closure_followup(self):
        from datetime import timedelta
        from src.developer import governance_operations as o
        _, _, _, _, record = self._governance_ops_setup()
        identifier = record["decision_id"]
        self._governance_ops_decide(identifier)
        now = o._now()
        item = o.add_action(self.developer, identifier, "Follow-up review", "owner", (now.date() - timedelta(days=1)).isoformat(), "Action")["actions"][0]
        aid = item["action_id"]
        self.assertEqual(1, len(o.actions(self.developer)["overdue"]))
        o.defer_action(self.developer, identifier, aid, (now.date() + timedelta(days=2)).isoformat(), "Explicit follow-up window", "Defer")
        self.assertEqual([], o.actions(self.developer)["overdue"])
        self.assertEqual(1, len(o.close_check(self.developer)["passed"]))
        o.transition(self.developer, identifier, "closed", "Documented deferral accepted", "Close")
        closed_event = o.decisions(self.developer)["decisions"][0]["history"][-1]
        with patch.object(o, "_now", return_value=now + timedelta(days=3)):
            self.assertEqual(1, len(o.followup(self.developer)["overdue_actions"]))
            self.assertTrue(o.close_check(self.developer)["blocked"])
        o.transition_action(self.developer, identifier, aid, "in_progress", "Resume deferred work", [], None, "Resume")
        o.transition_action(self.developer, identifier, aid, "completed", "Follow-up confirmed", [], "Manual completion after closure", "Complete")
        current = o.decisions(self.developer)["decisions"][0]
        self.assertIn(closed_event, current["history"])
        self.assertEqual("closed", current["status"])
        with self.assertRaises(LocalWorkflowError):
            o.add_action(self.developer, identifier, "New scope", "owner", "2027-01-01", "Invalid")

    def test_governance_ops_exception_acceptance_expiry_and_mitigation(self):
        from datetime import timedelta
        from src.developer import governance_operations as o
        _, _, _, _, record = self._governance_ops_setup()
        identifier = record["decision_id"]
        self._governance_ops_decide(identifier)
        now = o._now()
        record = o.add_exception(self.developer, identifier, "Temporary procedure exception", "exception-owner", (now + timedelta(days=2)).isoformat(), "Pending replacement review")
        eid = record["exceptions"][0]["exception_id"]
        self.assertTrue(o.close_check(self.developer)["blocked"])
        o.transition_exception(self.developer, identifier, eid, "accepted", "Human acceptance until expiry", [], None, "Accept")
        self.assertEqual(1, len(o.close_check(self.developer)["passed"]))
        with patch.object(o, "_now", return_value=now + timedelta(days=3)):
            before = o.decisions(self.developer)
            self.assertEqual(1, len(o.exceptions(self.developer)["expired"]))
            self.assertTrue(o.close_check(self.developer)["blocked"])
            self.assertEqual(before, o.decisions(self.developer))
            o.transition_exception(self.developer, identifier, eid, "expired", "Record observed expiry", [], None, "Expire explicitly")
        o.transition_exception(self.developer, identifier, eid, "mitigated", "Replacement reviewed", [], "Manual mitigation evidence", "Mitigate")
        o.transition_exception(self.developer, identifier, eid, "closed", "Exception resolved", [], "Resolution confirmed manually", "Close")
        exception = o.exceptions(self.developer)["exceptions"][0]
        self.assertEqual(4, len(exception["review_history"]))
        self.assertEqual("Pending replacement review", exception["reason"])
        self.assertEqual([], o.exceptions(self.developer)["unresolved"])
        with self.assertRaises(LocalWorkflowError):
            o.transition_exception(self.developer, identifier, eid, "accepted", "Cannot reopen", [], None, "Invalid")

    def test_governance_ops_evidence_files_drift_missing_and_containment(self):
        from src.developer import governance_operations as o
        _, _, _, _, record = self._governance_ops_setup()
        identifier = record["decision_id"]
        path = self.workspace_path / "closure-proof.txt"
        path.write_text("Manually reviewed decision evidence", encoding="utf-8")
        o.transition(self.developer, identifier, "reviewing", "Review", "Review")
        o.record_review(self.developer, identifier, "Review evidence file", [path.name], None, "Review")
        o.transition(self.developer, identifier, "decided", "Evidence reviewed", "Decide")
        self.assertEqual(1, len(o.close_check(self.developer)["passed"]))
        original = o.decisions(self.developer)
        path.write_text("Changed evidence", encoding="utf-8")
        self.assertTrue(o.close_check(self.developer)["blocked"])
        with self.assertRaises(LocalWorkflowError):
            o.transition(self.developer, identifier, "closed", "Changed proof", "Invalid")
        path.unlink()
        self.assertTrue(o.followup(self.developer)["missing_evidence"])
        self.assertEqual(original, o.decisions(self.developer))
        for reference in ("../outside.txt", str(self.repository / "source.py"), "missing.txt"):
            with self.assertRaises(LocalWorkflowError):
                o.record_review(self.developer, identifier, "Invalid evidence reference", [reference], None, "Invalid")
        o.record_review(self.developer, identifier, "Explicit alternative closure rationale", [], "Reviewer documented the outcome manually", "Refresh")
        self.assertEqual(1, len(o.close_check(self.developer)["passed"]))

    def test_governance_ops_source_drift_ownership_and_earlier_phase_compatibility(self):
        from src.developer import governance_operations as o, strategic_governance as g, maturity as m, evolution as e
        _, mature, evolved, strategic, record = self._governance_ops_setup()
        identifier = record["decision_id"]
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*.json") if o._root(self.developer) not in p.parents}
        ready = m.readiness(self.developer)
        self._governance_ops_decide(identifier)
        o.followup(self.developer)
        o.close_check(self.developer)
        self.assertEqual(ready, m.readiness(self.developer))
        for path, content in before.items():
            self.assertEqual(content, path.read_bytes())
        o.assign(self.developer, identifier, "new-owner", "Ownership handoff")
        self.assertIn("decision_owner_review_stale", o.close_check(self.developer)["blocked"][0]["blocked"])
        o.record_review(self.developer, identifier, "New owner review", [], "Manual rationale", "Review")
        g.add_roadmap(self.developer, strategic["governance_id"], "New direction", "owner", "Next year", [], "Change plan")
        self.assertIn("governance_review_stale", o.close_check(self.developer)["blocked"][0]["blocked"])
        original = o.decisions(self.developer)
        with patch.object(g, "history", side_effect=LocalWorkflowError("Source unavailable")):
            self.assertIn("related_governance_unavailable", o.close_check(self.developer)["blocked"][0]["blocked"])
            self.assertEqual(original["decisions"][0], o.decision(self.developer, identifier)["record"])
        self.assertEqual("initial", m.history(self.developer, mature["maturity_id"])["record"]["level"])
        self.assertEqual("planned", e.history(self.developer, evolved["evolution_id"])["record"]["status"])

    def test_governance_ops_cli_mutations_reports_and_exception_ownership(self):
        from datetime import timedelta
        from src.developer import governance_operations as o
        _, _, _, strategic, _ = self._governance_ops_setup()
        def run(*args):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(0, main(["local", *args, "--workspace", str(self.workspace_path), "--json"]))
            return json.loads(output.getvalue())
        identifier = run("governance-decision-create", strategic["governance_id"], "--decision", "CLI follow-up", "--owner", "owner", "--reason", "Create")["decision_id"]
        run("governance-decision-assign", identifier, "--owner", "reviewer", "--reason", "Handoff")
        run("governance-decision-transition", identifier, "reviewing", "--note", "Review", "--reason", "Review")
        run("governance-decision-review", identifier, "--note", "Review evidence", "--closure-reason", "Manual decision rationale", "--reason", "Review")
        run("governance-decision-transition", identifier, "decided", "--note", "Human decision", "--reason", "Decide")
        aid = run("governance-action-add", identifier, "--description", "Follow-up", "--owner", "owner", "--due-date", "2027-01-01", "--reason", "Action")["actions"][0]["action_id"]
        run("governance-action-assign", identifier, aid, "--owner", "new-owner", "--due-date", "2027-02-01", "--reason", "Handoff")
        run("governance-action-defer", identifier, aid, "--until", (o._now().date() + timedelta(days=7)).isoformat(), "--note", "Deferred by owner", "--reason", "Defer")
        run("governance-action-transition", identifier, aid, "cancelled", "--note", "Replaced by another plan", "--closure-reason", "Explicit cancellation rationale", "--reason", "Cancel")
        eid = run("governance-exception-add", identifier, "--description", "Temporary exception", "--owner", "owner", "--expires-at", (o._now() + timedelta(days=7)).isoformat(), "--action-id", aid, "--reason", "Exception")["exceptions"][0]["exception_id"]
        run("governance-exception-transition", identifier, eid, "accepted", "--note", "Human acceptance", "--reason", "Accept")
        run("governance-exception-assign", identifier, eid, "--owner", "new-owner", "--reason", "Handoff")
        self.assertEqual("open", o.decision(self.developer, identifier)["exceptions"][0]["status"])
        run("governance-exception-transition", identifier, eid, "closed", "--note", "Resolved", "--closure-reason", "Manual resolution", "--reason", "Close")
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        for command in ("governance-decisions", "governance-actions", "governance-exceptions", "governance-decision", "governance-followup", "governance-close-check"):
            args = (command, identifier) if command == "governance-decision" else (command,)
            self.assertEqual(o.MODE, run(*args)["mode"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        run("governance-decision-transition", identifier, "closed", "--note", "Closure checked", "--reason", "Close")

    def test_governance_ops_time_validation_missing_review_and_expired_acceptance(self):
        from datetime import timedelta
        from src.developer import governance_operations as o
        _, _, _, _, record = self._governance_ops_setup()
        identifier = record["decision_id"]
        now = o._now()
        for due in ("", "2027-99-01", "20270101"):
            with self.assertRaises(LocalWorkflowError):
                o.add_action(self.developer, identifier, "Action", "owner", due, "Invalid")
        for expiry in ("2027-01-01", (now - timedelta(days=1)).isoformat()):
            with self.assertRaises(LocalWorkflowError):
                o.add_exception(self.developer, identifier, "Exception", "owner", expiry, "Invalid")
        with self.assertRaises(LocalWorkflowError):
            o.add_exception(self.developer, identifier, "Exception", "owner", (now + timedelta(days=1)).isoformat(), "Invalid link", action_id="action-999")
        o.transition(self.developer, identifier, "reviewing", "Review", "Review")
        with self.assertRaises(LocalWorkflowError):
            o.transition(self.developer, identifier, "decided", "No recorded review", "Invalid")
        o.record_review(self.developer, identifier, "Decision reviewed without closure evidence yet", [], None, "Review")
        o.transition(self.developer, identifier, "decided", "Human decision", "Decide")
        self.assertIn("closure_evidence_missing", o.close_check(self.developer)["blocked"][0]["blocked"])
        from copy import deepcopy
        state = o._load(self.developer)
        forged = {**deepcopy(state["events"][-1]), "status": "closed", "closure": {"blocked": [], "decision_id": identifier}}
        with self.assertRaises(ValueError):
            o._apply(deepcopy(state), forged)
        eid = o.add_exception(self.developer, identifier, "Temporary exception", "owner", (now + timedelta(days=1)).isoformat(), "Exception")["exceptions"][0]["exception_id"]
        with patch.object(o, "_now", return_value=now + timedelta(days=2)):
            with self.assertRaises(LocalWorkflowError):
                o.transition_exception(self.developer, identifier, eid, "accepted", "Too late", [], None, "Invalid")
        self.assertEqual("open", o.exceptions(self.developer)["exceptions"][0]["status"])

    def test_governance_ops_journal_atomicity_corruption_and_empty_isolation(self):
        from src.developer import governance_operations as o
        for reader, field in ((o.decisions, "decisions"), (o.actions, "actions"), (o.exceptions, "exceptions"), (o.followup, "decisions"), (o.close_check, "passed")):
            self.assertEqual([], reader(self.developer)[field])
        self.assertFalse(o._root(self.developer).exists())
        _, _, _, _, record = self._governance_ops_setup()
        identifier = record["decision_id"]
        with patch.object(o.os, "link", side_effect=FileExistsError("Concurrent append")):
            with self.assertRaises(LocalWorkflowError):
                o.transition(self.developer, identifier, "reviewing", "Review", "Review")
        self.assertEqual(record, o.decisions(self.developer)["decisions"][0])
        self.assertFalse(list(o._root(self.developer).glob("*.tmp")))
        path = next(o._root(self.developer).glob("*.json"))
        original = path.read_bytes()
        event = json.loads(original)
        event["sequence"] = 2
        path.write_text(json.dumps(event), encoding="utf-8")
        with self.assertRaises(LocalWorkflowError):
            o.followup(self.developer)
        path.write_bytes(original)
        with self.assertRaises(LocalWorkflowError):
            o.actions(DeveloperWorkspace(self.research_root / "governance-operations", research_roots=[self.research_root]))


    def _operational_readiness_setup(self):
        from src.developer import (readiness as r, maturity as m, evolution as e,
                                   strategic_governance as g, governance_operations as o,
                                   assurance, assurance_operations, continuity, operations,
                                   configuration, deployment, reliability, recovery_governance)
        _, config, deployed = self._deployment_setup()
        configuration.transition_configuration(self.developer, config["config_id"], "activate", "Manual activation fixture")
        deployment.transition_deployment(self.developer, deployed["deployment_id"], "validate", "Validate fixture")
        deployment.transition_deployment(self.developer, deployed["deployment_id"], "activate", "Manual activation fixture")
        operation = operations.create_operation(self.developer, deployed["deployment_id"], "health_check", "Manual health review")
        operations.transition_operation(self.developer, operation["operation_id"], "resolved", "Reviewed manually")
        plan = reliability.create_recovery_plan(self.developer, deployed["deployment_id"], "Recovery fixture")
        reliability.verify_recovery(self.developer, plan["plan_id"])
        scenario = continuity.create_scenario(self.developer, deployed["deployment_id"], "Continuity fixture")
        continuity.test_scenario(self.developer, scenario["scenario_id"])
        source = assurance.create_assurance(self.developer, scenario["scenario_id"], "Assurance fixture")
        source = assurance.verify_assurance(self.developer, source["assurance_id"])
        recovery_governance.register(self.developer, source["assurance_id"], "Register owner")
        recovery_governance.change(self.developer, source["assurance_id"], "transition", "Manual governance activation", status="active")
        recovery_governance.record_check(self.developer, source["assurance_id"], source["assurance_id"], "Record verification")
        operated = assurance_operations.create(self.developer, source["assurance_id"], "Review cycle")
        assurance_operations.record_review(self.developer, operated["operation_id"], "Review current evidence")
        mature = m.create(self.developer, "readiness-fixture", [source["assurance_id"]], "maintainer", "Create maturity")
        evolved = e.create(self.developer, "recovery-verification", "improvement", "maintainer", "Create evolution")
        strategic = g.create(self.developer, "Maintain recovery readiness", "strategy-owner", [m.CAPABILITIES[0]],
                             [evolved["evolution_id"]], [], [], [], "Define strategy")
        strategic = g.add_roadmap(self.developer, strategic["governance_id"], "Schedule evidence review manually",
                                  "roadmap-owner", "Next review period", [], "Document roadmap")
        decision = o.create(self.developer, strategic["governance_id"], "Confirm end-to-end readiness", "decision-owner", "Propose decision")
        mid, eid, gid, did = mature["maturity_id"], evolved["evolution_id"], strategic["governance_id"], decision["decision_id"]
        plan = m.add_plan(self.developer, mid, ["Maintain evidence review"], [m.CAPABILITIES[0]], [], "Manual plan")
        pid = plan["plans"][-1]["plan_id"]
        m.review_plan(self.developer, mid, pid, "reviewed", "Plan reviewed", "Review")
        for capability in m.CAPABILITIES:
            m.assess(self.developer, mid, capability, "Assess current evidence")
        e.record_impact(self.developer, eid, [m.CAPABILITIES[0]], [mid], [], [], [], "Refresh current impact")
        g.record_review(self.developer, gid, "Review complete lifecycle evidence", "Review")
        self._governance_ops_decide(did)
        scenario = continuity._resolve(continuity._load(self.developer), source["scenario_id"])
        depid = scenario["deployment_id"]
        record = r.create(self.developer, depid, did, "readiness-owner", "Consolidate lifecycle")
        return record, source, strategic

    def test_operational_readiness_complete_chain_closure_and_history(self):
        from src.developer import readiness as r
        record, _, _ = self._operational_readiness_setup()
        identifier = record["readiness_id"]
        report = r.audit(self.developer, record["deployment_id"], record["decision_id"])
        self.assertEqual([], report["blocked"], report["blocked"])
        components = {i["component"] for i in report["evidence"]}
        self.assertTrue({"candidate", "review", "promotion", "configuration", "deployment", "operations",
                         "recovery", "continuity", "assurance", "maturity", "evolution", "governance", "decisions", "validation"} <= components)
        original = {p: p.read_bytes() for p in self.workspace_path.rglob("*.json")}
        r.transition(self.developer, identifier, "review_required", "Request review")
        r.review(self.developer, identifier, "readiness-owner", "Review current chain", "Review")
        r.transition(self.developer, identifier, "ready_for_manual_decision", "Ready")
        with self.assertRaises(LocalWorkflowError):
            r.transition(self.developer, identifier, "approved", "Approve")
        r.transition(self.developer, identifier, "approved", "Approve", confirmed=True)
        with self.assertRaises(LocalWorkflowError):
            r.close(self.developer, identifier, "readiness-owner", "Close", confirmed=True)
        bundled = r.evidence(self.developer, identifier, "Capture references")
        self.assertTrue(bundled["evidence_bundles"][-1]["references"])
        with self.assertRaises(LocalWorkflowError):
            r.close(self.developer, identifier, "other-owner", "Close", confirmed=True)
        closed = r.close(self.developer, identifier, "readiness-owner", "Lifecycle reviewed", confirmed=True)
        self.assertEqual("closed", closed["status"])
        self.assertEqual("readiness-owner", closed["closure"]["owner"])
        for target in r.STATES:
            with self.assertRaises(LocalWorkflowError):
                r.transition(self.developer, identifier, target, "Reopen")
        with self.assertRaises(LocalWorkflowError):
            r.followup(self.developer, identifier, "owner", "recovery", "Review", "2027-01-01T00:00:00+00:00", "Plan")
        for path, data in original.items():
            self.assertEqual(data, path.read_bytes())
        self.assertEqual(closed, r.history(self.developer, identifier)["record"])
        self.assertFalse(r.status(self.developer, identifier)["recorded_evidence_stale"])

    def test_operational_readiness_incomplete_chain_invalid_transitions_and_followup(self):
        from src.developer import readiness as r, continuity
        source, _, _, _, decision = self._governance_ops_setup()
        scenario = continuity._resolve(continuity._load(self.developer), source["scenario_id"])
        record = r.create(self.developer, scenario["deployment_id"], decision["decision_id"], "owner", "Record gaps")
        identifier = record["readiness_id"]
        self.assertEqual("not_ready", record["status"])
        self.assertTrue(record["latest_evidence"]["blocked"])
        for target in ("approved", "closed", "ready_for_manual_decision", "unknown"):
            with self.assertRaises(LocalWorkflowError):
                r.transition(self.developer, identifier, target, "Invalid")
        r.transition(self.developer, identifier, "review_required", "Inspect gaps")
        with self.assertRaises(LocalWorkflowError):
            r.review(self.developer, identifier, "other", "Review", "Wrong owner")
        r.review(self.developer, identifier, "owner", "Gaps reviewed", "Review")
        with self.assertRaises(LocalWorkflowError):
            r.transition(self.developer, identifier, "ready_for_manual_decision", "Blocked")
        for component, due_at in (("invalid", "2027-01-01T00:00:00+00:00"), ("validation", "2020-01-01T00:00:00+00:00"), ("validation", "2027-01-01")):
            with self.assertRaises(LocalWorkflowError):
                r.followup(self.developer, identifier, "owner", component, "Refresh evidence", due_at, "Gap")
        updated = r.followup(self.developer, identifier, "owner", "validation", "Run validation manually", "2027-01-01T00:00:00+00:00", "Missing evidence")
        item = updated["followups"][-1]
        self.assertEqual("open", item["status"])
        with self.assertRaises(LocalWorkflowError):
            r.complete_followup(self.developer, identifier, item["followup_id"], "other", "Done", "Complete")
        complete = r.complete_followup(self.developer, identifier, item["followup_id"], "owner", "Validation inspected manually", "Complete")
        self.assertEqual("completed", complete["followups"][-1]["status"])
        self.assertTrue(r.status(self.developer, identifier)["blocking"])

    def test_operational_readiness_drift_expiry_and_compatibility(self):
        from datetime import timedelta
        from src.developer import (readiness as r, governance_operations as o, strategic_governance as g,
                                   assurance, configuration, deployment, continuity, reliability)
        record, source, strategic = self._operational_readiness_setup()
        identifier, did = record["readiness_id"], record["decision_id"]
        r.transition(self.developer, identifier, "review_required", "Review")
        r.review(self.developer, identifier, "readiness-owner", "Review evidence", "Review")
        r.transition(self.developer, identifier, "ready_for_manual_decision", "Ready")
        action = o.add_action(self.developer, did, "Renew ownership review", "owner", "2027-01-01", "Manual action")
        report = r.audit(self.developer, record["deployment_id"], did)
        self.assertTrue(report["blocked"])
        self.assertEqual(1, len(report["open_actions"]))
        with self.assertRaises(LocalWorkflowError):
            r.transition(self.developer, identifier, "approved", "Stale", confirmed=True)
        o.transition_action(self.developer, did, action["actions"][-1]["action_id"], "cancelled", "Replaced", [], "Manual cancellation", "Cancel")
        o.add_exception(self.developer, did, "Temporary issue", "owner", (o._now() + timedelta(hours=1)).isoformat(), "Document exception")
        with patch.object(o, "_now", return_value=o._now() + timedelta(hours=2)):
            report = r.audit(self.developer, record["deployment_id"], did)
            self.assertTrue(any(i["expired"] for i in report["open_exceptions"]))
            self.assertTrue(report["blocked"])
        with patch.object(assurance, "_now", return_value=assurance._now() + timedelta(days=2)):
            report = r.audit(self.developer, record["deployment_id"], did)
            self.assertTrue(report["stale_evidence"])
        for module, function in ((configuration, "_check"), (deployment, "deployment_governance_check"),
                                 (reliability, "_verify"), (assurance, "recovery_assurance"), (g, "review")):
            with patch.object(module, function, side_effect=LocalWorkflowError("Current evidence unavailable")):
                self.assertTrue(r.audit(self.developer, record["deployment_id"], did)["blocked"])
        self.assertTrue(r.status(self.developer, identifier)["recorded_evidence_stale"])

    def test_operational_readiness_missing_orphaned_links_and_read_only_isolation(self):
        from src.developer import readiness as r, configuration, governance_operations as o
        absent = DeveloperWorkspace(self.root / "absent", (self.research_root,))
        self.assertTrue(r.audit(absent)["missing"])
        self.assertFalse(absent.root.exists())
        self.assertEqual("not_ready", r.status(absent)["status"])
        self.assertFalse(absent.root.exists())
        for workspace in (DeveloperWorkspace(self.research_root / "ready", (self.research_root,)),
                          DeveloperWorkspace(Path(local_workflow.__file__).resolve().parents[2] / "readiness")):
            with self.assertRaises(LocalWorkflowError):
                r.audit(workspace)
        record, _, _ = self._operational_readiness_setup()
        before = {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()}
        r.status(self.developer, record["readiness_id"])
        r.audit(self.developer, record["deployment_id"], record["decision_id"])
        r.history(self.developer, record["readiness_id"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.workspace_path.rglob("*") if p.is_file()})
        state = configuration._load(self.developer)
        state["configurations"][0]["source_promotion"] = "missing-promotion"
        with patch.object(configuration, "_load", return_value=state):
            report = r.audit(self.developer, record["deployment_id"], record["decision_id"])
            self.assertTrue(any(i["check"] == "orphaned_record" for i in report["missing"]))
        with patch.object(o, "_load", side_effect=LocalWorkflowError("Broken decision history")):
            self.assertTrue(r.audit(self.developer)["blocked"])

    def test_operational_readiness_cli_and_manual_outstanding_items(self):
        from src.developer import readiness as r
        record, _, _ = self._operational_readiness_setup()
        identifier = record["readiness_id"]
        def run(*args, expected=0):
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                self.assertEqual(expected, main(["local", *args, "--workspace", str(self.workspace_path), "--json"]))
            return json.loads(output.getvalue()) if expected == 0 else None
        created = run("readiness-record-create", record["deployment_id"], "--decision-id", record["decision_id"],
                      "--owner", "readiness-owner", "--reason", "Second manual closure cycle")
        self.assertEqual("not_ready", created["status"])
        run("readiness")
        report = run("readiness-audit", identifier)
        self.assertEqual([], report["blocked"])
        self.assertEqual("passed", report["lifecycle"]["recovery"][0]["status"])
        # The real audit above verifies the CLI integration. Reuse that immutable
        # source view while testing argument dispatch and manual decision gates;
        # separate integration tests exercise live source drift and closure checks.
        self.enterContext(patch.object(r, "audit", return_value={k: v for k, v in report.items() if k != "notice"}))
        run("readiness-transition", identifier, "review_required", "--reason", "Review")
        run("readiness-review", identifier, "--owner", "readiness-owner", "--note", "Reviewed", "--reason", "Review")
        run("readiness-transition", identifier, "ready_for_manual_decision", "--reason", "Ready")
        run("readiness-transition", identifier, "approved", "--confirm", "--reason", "Approve")
        follow = run("readiness-followup", identifier, "--owner", "owner", "--component", "assurance", "--manual-action", "Schedule next review manually", "--due-at", "2027-01-01T00:00:00+00:00", "--reason", "Future maintenance")
        self.assertEqual("open", follow["followups"][-1]["status"])
        run("readiness-evidence", identifier, "--reason", "Bundle")
        run("readiness-close", identifier, "--owner", "readiness-owner", "--reason", "Close", expected=2)
        run("readiness-close", identifier, "--owner", "readiness-owner", "--reason", "Close", "--confirm", expected=2)
        closed = run("readiness-close", identifier, "--owner", "readiness-owner", "--reason", "Close", "--confirm", "--outstanding-reason", "Owner will schedule the next review manually")
        self.assertEqual("closed", closed["status"])
        self.assertTrue(closed["closure"]["outstanding_items"])
        run("readiness-history", identifier)

    def test_operational_readiness_atomic_append_corruption_and_history_preservation(self):
        from src.developer import readiness as r
        # A real empty audit exercises journal replay without synthesizing source evidence.
        report = r.audit(self.developer, "deployment-001", "decision-001")
        state = r._load(self.developer)
        record = r._append(self.developer, state, "create", "retrieval-readiness-001", "Record missing chain", "developer", report,
                           deployment_id="deployment-001", decision_id="decision-001", owner="owner")
        identifier = record["readiness_id"]
        with patch("src.developer.readiness.os.link", side_effect=OSError("Append failed")):
            with self.assertRaises(LocalWorkflowError):
                r.transition(self.developer, identifier, "review_required", "Review")
        self.assertEqual(record, r.history(self.developer, identifier)["record"])
        self.assertFalse(list(r._root(self.developer).glob("*.tmp")))
        path = next(r._root(self.developer).glob("*.json"))
        original = path.read_bytes()
        for field, value in (("previous_digest", "broken"), ("owner", ""), ("sequence", 9)):
            event = json.loads(original)
            event[field] = value
            path.write_text(json.dumps(event), encoding="utf-8")
            with self.assertRaises(LocalWorkflowError):
                r.history(self.developer, identifier)
        path.write_bytes(original)
        self.assertEqual(record, r.history(self.developer, identifier)["record"])


if __name__ == "__main__":
    unittest.main()
