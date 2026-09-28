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

    def _optimization_setup(self, identifier="session-fix"):
        from src.developer.optimization import create_candidate
        cases = self.root / "optimization-cases.json"
        cases.write_text(json.dumps([{"id": "session", "query": "load_session_token",
            "expected": {"files": ["src/session.py"], "symbols": ["load_session_token"]}}]), encoding="utf-8")
        with patch("src.developer.local_workflow._embed_developer_chunks", self._embedding_stub):
            self.developer.index(self.repository)
        with patch("src.developer.local_workflow.load_model", return_value=self._query_model()):
            baseline = self.developer.regression(self.repository, cases, create_baseline=True)
        candidate = create_candidate(self.developer, identifier, "Review repeated context", ["session"],
            [baseline["history_id"] + ":session"], "Inspect expansion limits", "Run all baseline cases and compatibility gates")
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


if __name__ == "__main__":
    unittest.main()
