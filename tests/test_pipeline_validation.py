"""Integration tests for local scanner → parser → chunker validation."""

from pathlib import Path
import subprocess
import tempfile
import unittest

from src.evaluation import PipelineValidationRunner, RepositorySpec


class PipelineValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.corpus_root = self.root / "corpus"
        self.repository_path = self.corpus_root / "sample"
        self.repository_path.mkdir(parents=True)
        self._git("init", "--quiet")
        self._git("config", "user.name", "Pipeline Test")
        self._git("config", "user.email", "pipeline-test@example.invalid")
        self._write(
            "module.py",
            "class Counter:\n    def increment(self):\n        return 1\n",
        )
        self._write("broken.py", "def broken(:\n    pass\n")
        self._git("add", "--all")
        self._git("commit", "--quiet", "-m", "pipeline test corpus")
        self.commit_sha = self._git("rev-parse", "HEAD")
        self.output_directory = self.root / "validation-reports"
        self.spec = RepositorySpec(
            repository_id="example/sample",
            checkout_name="sample",
            commit_sha=self.commit_sha,
            expected_python_file_count=2,
            expected_python_loc=5,
        )
        self.runner = PipelineValidationRunner()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _git(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repository_path), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def _write(self, relative_path: str, content: str) -> None:
        path = self.repository_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    def test_validates_scanner_parser_and_chunker_together(self) -> None:
        result = self.runner.run(
            self.corpus_root,
            self.output_directory,
            repositories=(self.spec,),
        ).repositories[0]

        self.assertEqual("example/sample", result.repository_id)
        self.assertEqual(self.commit_sha, result.verified_commit_sha)
        self.assertEqual("validated_with_issues", result.status)
        self.assertEqual(2, result.python_file_count)
        self.assertEqual(5, result.eligible_python_loc)
        self.assertEqual(0, result.source_read_failure_count)
        self.assertEqual(1, result.parse_success_count)
        self.assertEqual(1, result.parse_failure_count)
        self.assertEqual(1, result.module_count)
        self.assertEqual(1, result.class_count)
        self.assertEqual(0, result.function_count)
        self.assertEqual(1, result.method_count)
        self.assertEqual(3, result.chunk_count)
        self.assertEqual(0, result.chunk_failure_count)
        self.assertTrue(result.deterministic)
        self.assertIn("parse_failures_present", result.issue_codes)
        self.assertEqual(3, result.chunk_size_statistics["characters"]["count"])
        self.assertTrue(self.output_directory.joinpath("pipeline-validation.json").is_file())
        self.assertTrue(self.output_directory.joinpath("pipeline-validation.md").is_file())

    def test_report_and_metrics_are_deterministic_and_source_is_read_only(self) -> None:
        source_before = (self.repository_path / "module.py").read_bytes()
        status_before = self._git("status", "--porcelain")

        first = self.runner.run(
            self.corpus_root,
            self.output_directory,
            repositories=(self.spec,),
        )
        first_json = (self.output_directory / "pipeline-validation.json").read_bytes()
        second = self.runner.run(
            self.corpus_root,
            self.output_directory,
            repositories=(self.spec,),
        )
        second_json = (self.output_directory / "pipeline-validation.json").read_bytes()

        self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual(first_json, second_json)
        self.assertEqual(source_before, (self.repository_path / "module.py").read_bytes())
        self.assertEqual(status_before, self._git("status", "--porcelain"))

    def test_missing_approved_checkout_is_reported_without_fetching(self) -> None:
        missing_spec = RepositorySpec(
            repository_id="example/missing",
            checkout_name="missing",
            commit_sha="b" * 40,
            expected_python_file_count=1,
            expected_python_loc=1,
        )

        result = self.runner.run(
            self.corpus_root,
            self.output_directory,
            repositories=(missing_spec,),
        ).repositories[0]

        self.assertEqual("missing_checkout", result.status)
        self.assertEqual(("missing_checkout",), result.issue_codes)
        self.assertIsNone(result.parse_success_count)

    def test_refuses_to_write_reports_inside_the_source_repository(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the source repository"):
            self.runner.run(
                self.corpus_root,
                self.runner.project_root / "validation-output",
                repositories=(self.spec,),
            )

        with self.assertRaisesRegex(ValueError, "outside every corpus checkout"):
            self.runner.run(
                self.corpus_root,
                self.repository_path / "reports",
                repositories=(self.spec,),
            )


if __name__ == "__main__":
    unittest.main()