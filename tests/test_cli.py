"""Usability tests for the public prototype command."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.cli import main


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
        output, errors = StringIO(), StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            status = main(arguments)
        return status, output.getvalue(), errors.getvalue()

    def test_help_lists_stable_commands(self):
        with self.assertRaises(SystemExit) as raised:
            main(("--help",))
        self.assertEqual(0, raised.exception.code)

    def test_demo_is_offline_and_reproducible(self):
        first = self.run_cli("demo")
        second = self.run_cli("demo")
        self.assertEqual((0, first[1], ""), first)
        self.assertEqual(first, second)
        self.assertIn("generated fixture", first[1])

    def test_evaluate_returns_machine_readable_report(self):
        status, output, errors = self.run_cli("evaluate", "--json")
        self.assertEqual(0, status)
        self.assertEqual("", errors)
        self.assertEqual("demo", __import__("json").loads(output)["system"])

    def test_validate_uses_runner_and_reports_external_paths(self):
        with patch("src.cli.PipelineValidationRunner") as runner_type:
            runner_type.return_value.run.return_value = type(
                "Report", (), {
                    "validated_repository_count": 0,
                    "expected_repository_count": 9,
                    "preprocessing_ready": False,
                }
            )()
            status, output, errors = self.run_cli(
                "validate", "--corpus-root", "C:/corpus", "--output-dir", "C:/reports"
            )
        self.assertEqual(0, status)
        self.assertEqual("", errors)
        self.assertIn("Snapshots validated: 0/9", output)
        runner_type.return_value.run.assert_called_once()

    def test_validate_reports_missing_corpus_without_fetching(self):
        with tempfile.TemporaryDirectory() as temporary_directory, patch.dict(
            "os.environ", {"PROTOTYPE_DATA_ROOT": temporary_directory}, clear=False
        ):
            status, output, _ = self.run_cli(
                "validate",
                "--corpus-root",
                str(Path(temporary_directory) / "not-acquired"),
                "--output-dir",
                str(Path(temporary_directory) / "reports"),
            )

        self.assertEqual(0, status)
        self.assertIn("Snapshots validated: 0/9", output)
        self.assertIn("Preprocessing ready: no", output)

    def test_validate_explains_when_corpus_root_is_a_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory, patch.dict(
            "os.environ", {"PROTOTYPE_DATA_ROOT": temporary_directory}, clear=False
        ):
            corpus_file = Path(temporary_directory) / "corpus.txt"
            corpus_file.write_text("not a directory", encoding="utf-8")
            status, _, errors = self.run_cli(
                "validate",
                "--corpus-root",
                str(corpus_file),
                "--output-dir",
                str(Path(temporary_directory) / "reports"),
            )

        self.assertEqual(2, status)
        self.assertIn("Corpus root is not a directory", errors)

    def test_validate_explains_when_output_path_is_a_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory, patch.dict(
            "os.environ", {"PROTOTYPE_DATA_ROOT": temporary_directory}, clear=False
        ):
            output_file = Path(temporary_directory) / "reports.txt"
            output_file.write_text("not a directory", encoding="utf-8")
            status, _, errors = self.run_cli(
                "validate",
                "--corpus-root",
                str(Path(temporary_directory) / "corpus"),
                "--output-dir",
                str(output_file),
            )

        self.assertEqual(2, status)
        self.assertIn("Validation output path is not a directory", errors)


if __name__ == "__main__":
    unittest.main()