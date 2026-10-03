"""Coverage for selection, isolation and honest unittest diagnostics."""
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from src import developer_testing as testing


class DeveloperTestingTests(unittest.TestCase):
    def test_default_fast_tier_excludes_developer_and_expensive_tests(self):
        result = testing.plan()
        self.assertEqual("T0", result["tier"])
        self.assertEqual(set(testing.FAST), set(result["selectors"]))
        self.assertFalse(any("test_embedding" in t for t in result["selected_tests"]))
        self.assertFalse(any("test_rrf.HybridSearchTests" in t for t in result["selected_tests"]))
        self.assertTrue(any("test_embedding" in row["test"] for row in result["not_selected"]))
        self.assertTrue(all(row["reason"] for row in result["not_selected"]))

    def test_developer_component_is_complete_and_excludes_research_subsystems(self):
        result = testing.plan(component="developer")
        self.assertEqual("T2", result["tier"])
        self.assertEqual([testing.DEVELOPER], result["selectors"])
        self.assertEqual(set(testing.catalog()[testing.DEVELOPER]), set(result["selected_tests"]))

    def test_expensive_component_is_explicit_and_tier_three(self):
        result = testing.plan(component="embedding")
        self.assertEqual("T3", result["tier"])
        self.assertIn("tests.test_embedding", result["selectors"])
        self.assertNotIn("tests.test_benchmark_freeze", result["selectors"])

    def test_configuration_and_governance_mappings_include_workflow(self):
        for component in ("configuration", "governance", "ranking", "context"):
            with self.subTest(component=component):
                self.assertIn(testing.DEVELOPER, testing.plan(component=component)["selectors"])
        self.assertIn("tests.test_tracking", testing.plan(component="testing")["selectors"])

    def test_explicit_module_class_and_method_selection(self):
        method = testing.catalog()["tests.test_config"][0]
        for selector in (method, method.rsplit(".", 1)[0], "tests.test_config"):
            result = testing.plan(tests=[selector])
            self.assertIn(method, result["selected_tests"])
            self.assertFalse(any("test_developer_mode" in name for name in result["selected_tests"]))
        self.assertEqual([method], testing.plan(tests=[method])["selected_tests"])

    def test_invalid_and_conflicting_selectors_are_errors(self):
        for options in ({"tests": ["os"]}, {"tests": ["tests.test_missing"]},
                        {"component": "missing"}, {"base": "HEAD"},
                        {"tier": "T3"}, {"changed": True, "component": "cli"},
                        {"final_gate": True}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                testing.plan(**options)

    def test_full_gate_never_runs_implicitly(self):
        result = testing.plan(tier="T4")
        with patch.object(testing.subprocess, "run") as run:
            report = testing.execute(result)
        run.assert_not_called()
        self.assertEqual(2, report["exit_code"])
        self.assertFalse(report["executed"])
        self.assertFalse(testing.plan(tier="T4", final_gate=True)["execution_blocked"])

    def test_changed_source_transitively_includes_dependent_tests(self):
        with patch.object(testing, "changed_files", return_value=["src/developer/context.py"]):
            result = testing.plan(changed=True)
        self.assertIn(testing.DEVELOPER, result["selectors"])
        self.assertNotIn("tests.test_embedding", result["selectors"])
        self.assertFalse(result["uncertain"])

    def test_changed_test_selects_itself_and_docs_use_fast_checks(self):
        with patch.object(testing, "changed_files", return_value=["tests/test_config.py"]):
            self.assertEqual(["tests.test_config"], testing.plan(changed=True)["selectors"])
        with patch.object(testing, "changed_files", return_value=["docs/research/example.md"]):
            result = testing.plan(changed=True)
            self.assertTrue(any("Documentation-only" in text for text in result["diagnostics"]))

    def test_package_initializers_reach_submodule_consumers(self):
        with patch.object(testing, "changed_files", return_value=["src/embedding/__init__.py"]):
            result = testing.plan(changed=True)
        self.assertIn("tests.test_embedding", result["selectors"])
        self.assertFalse(result["uncertain"])
        with patch.object(testing, "changed_files", return_value=["src/__init__.py"]):
            all_modules = testing.plan(changed=True)
        self.assertEqual("T4", all_modules["tier"])
        self.assertTrue(all_modules["execution_blocked"])

    def test_unknown_change_falls_back_to_explicit_full_gate(self):
        for path in ("requirements-lock.txt", "src/new_unknown.py", "tests/fixtures/new.json"):
            with self.subTest(path=path), patch.object(testing, "changed_files", return_value=[path]):
                result = testing.plan(changed=True)
                self.assertEqual("T4", result["tier"])
                self.assertTrue(result["execution_blocked"])
                self.assertTrue(result["diagnostics"])

    def test_mixed_known_and_unknown_python_change_does_not_hide_uncertainty(self):
        with patch.object(testing, "changed_files", return_value=["src/config.py", "src/unknown_new.py"]):
            result = testing.plan(changed=True)
        self.assertTrue(result["uncertain"])
        self.assertTrue(result["execution_blocked"])

    def test_overlapping_selectors_execute_only_once(self):
        method = testing.catalog()["tests.test_config"][0]
        result = testing.plan(tests=[method, "tests.test_config", "tests.test_config"])
        self.assertEqual(["tests.test_config"], result["selectors"])

    def test_git_detection_staged_unstaged_deleted_renamed_untracked_and_base(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", "-C", directory, *args], check=True,
                                      capture_output=True, text=True).stdout.strip()
            git("init", "--quiet")
            for name in ("staged.py", "unstaged.py", "deleted.py", "before space.py"):
                (root / name).write_text("old\n")
            git("add", "--all")
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "baseline")
            baseline = git("rev-parse", "HEAD")
            (root / "staged.py").write_text("new\n")
            git("add", "staged.py")
            (root / "unstaged.py").write_text("new\n")
            (root / "deleted.py").unlink()
            git("mv", "before space.py", "after space.py")
            (root / "untracked.py").write_text("new\n")
            expected = {"staged.py", "unstaged.py", "deleted.py", "before space.py", "after space.py", "untracked.py"}
            self.assertEqual(expected, set(testing.changed_files(root)))
            git("add", "--all")
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "changes")
            self.assertEqual([], testing.changed_files(root))
            self.assertEqual(expected, set(testing.changed_files(root, baseline)))

    def test_git_failure_does_not_pretend_no_changes(self):
        with patch.object(testing.subprocess, "run", side_effect=FileNotFoundError("git")):
            with self.assertRaisesRegex(ValueError, "Cannot inspect Git"):
                testing.changed_files()

    def test_target_execution_is_a_fresh_process_and_returns_real_timing(self):
        method = testing.catalog()["tests.test_config"][0]
        with redirect_stderr(StringIO()):
            result = testing.execute(testing.plan(tests=[method]))
        self.assertEqual(0, result["exit_code"])
        self.assertEqual(1, result["total_tests"])
        self.assertEqual(1, result["passed"])
        self.assertEqual([method], [row["test"] for row in result["tests"]])
        self.assertGreaterEqual(result["total_seconds"], result["tests"][0]["seconds"])
        self.assertIn("tests.test_config", result["modules"])

    def test_timing_preserves_failures_errors_skips_subtests_and_reproduction(self):
        class Sample(unittest.TestCase):
            def test_pass(self):
                pass
            def test_failure(self):
                self.fail("original failure")
            def test_error(self):
                raise RuntimeError("original error")
            @unittest.skip("environment requirement")
            def test_skip(self):
                pass
            def test_subtest(self):
                with self.subTest(case=1):
                    self.fail("subtest failure")
                with self.subTest(case=2):
                    self.fail("another subtest failure")
        result = unittest.TextTestRunner(stream=StringIO(), resultclass=testing.TimingResult).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Sample))
        report = testing.summarize(result, 1.0)
        self.assertEqual(5, report["total_tests"])
        self.assertEqual(1, report["passed"])
        self.assertEqual(3, len(report["failures"]))
        self.assertEqual(1, len(report["errors"]))
        self.assertEqual(1, len(report["skipped"]))
        self.assertEqual(3, len(report["reproduce"]))
        self.assertEqual(1, report["exit_code"])

    def test_class_fixture_error_remains_error_without_executed_tests(self):
        class Sample(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise RuntimeError("fixture failure")
            def test_never(self):
                pass
        result = unittest.TextTestRunner(stream=StringIO(), resultclass=testing.TimingResult).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Sample))
        report = testing.summarize(result, 1)
        self.assertEqual(0, report["total_tests"])
        self.assertEqual(1, len(report["errors"]))
        self.assertEqual(1, report["exit_code"])
        self.assertEqual("tests.test_developer_testing." + Sample.__qualname__, report["reproduce"][0][-2])

    def test_missing_module_is_reported_as_error_not_skip(self):
        with redirect_stderr(StringIO()):
            report = testing.worker({"tier": "T1", "selectors": ["tests.no_such_dependency"]})
        self.assertEqual(1, report["exit_code"])
        self.assertEqual(1, len(report["errors"]))
        self.assertEqual([], report["skipped"])

    def test_environment_limitations_are_explicit(self):
        with patch.dict(os.environ, {"EMBEDDING_MODEL_CACHE": ""}), patch.object(
                testing.importlib.util, "find_spec", return_value=None):
            report = testing.environment()
        self.assertIn("faiss", report["missing_dependencies"])
        self.assertTrue(report["limitations"])

    def test_crashed_worker_is_never_a_pass(self):
        completed = subprocess.CompletedProcess([], 7, "partial output")
        with patch.object(testing.subprocess, "run", return_value=completed):
            result = testing.execute(testing.plan())
        self.assertEqual(7, result["exit_code"])
        self.assertFalse(result["executed"])

    def test_resource_profile_is_opt_in_and_does_not_change_result(self):
        method = testing.catalog()["tests.test_config"][0]
        with redirect_stderr(StringIO()):
            normal = testing.worker({"tier": "T1", "selectors": [method]})
            profile = testing.worker({"tier": "T1", "selectors": [method], "profile": True})
        self.assertFalse(normal["profile_enabled"])
        self.assertTrue(profile["profile_enabled"])
        self.assertEqual(normal["passed"], profile["passed"])
        self.assertEqual(normal["exit_code"], profile["exit_code"])

    def test_json_encoding_is_not_classified_as_model_embedding(self):
        profiler = testing.cProfile.Profile()
        profiler.enable()
        json.dumps({"example": [1, 2, 3]})
        profiler.disable()
        self.assertFalse(any(row["category"] == "model initialization / embedding"
                             for row in testing._resource_profile(profiler)))

    def test_cli_dry_run_is_json_and_does_not_initialize_workspace(self):
        from src.cli import main
        for command in ("test", "test-timing"):
            output = StringIO()
            with patch.object(testing, "execute") as execute, redirect_stdout(output), redirect_stderr(StringIO()):
                status = main(["local", command, "--dry-run", "--json"])
            execute.assert_not_called()
            self.assertEqual(0, status)
            self.assertFalse(json.loads(output.getvalue())["executed"])

    def test_cli_propagates_failure_exit_and_rejects_internal_artifacts(self):
        from src.cli import main
        with patch.object(testing, "execute", return_value={"exit_code": 1}), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(1, main(["local", "test"]))
        with redirect_stderr(StringIO()):
            self.assertEqual(2, main(["local", "test", "--report", str(testing.ROOT / "report.json")]))

    def test_cli_external_report_is_new_and_not_overwritten(self):
        from src.cli import main
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(0, main(["local", "test-timing", "--dry-run", "--report", str(path)]))
                before = path.read_bytes()
                self.assertEqual(2, main(["local", "test-timing", "--dry-run", "--report", str(path)]))
            self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
