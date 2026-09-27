"""Tests for experiment run persistence and reproduction."""

from datetime import datetime, timezone
from contextlib import redirect_stderr
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.cli import main
from src.config import load_config
from src.tracking import RunTracker, configuration_hash, deterministic_run_id, load_run


class TrackingTests(unittest.TestCase):
    def test_run_id_is_deterministic_for_same_inputs(self):
        timestamp = datetime(2026, 9, 28, 12, 34, 56, tzinfo=timezone.utc)
        digest = configuration_hash({"device": "cpu", "retrieval_k": 50})

        self.assertEqual(
            deterministic_run_id(timestamp, "demo", digest),
            deterministic_run_id(timestamp, "demo", digest),
        )
        self.assertRegex(deterministic_run_id(timestamp, "demo", digest), r"^20260928-123456-[0-9a-f]{12}$")

    def test_tracker_writes_run_files_and_metadata(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = load_config(environ={"PROTOTYPE_DATA_ROOT": temporary_directory})
            tracker = RunTracker(config, "demo", ["demo"])
            with tracker.execute():
                payload = tracker.finish({"status": "completed", "value": 1})

            run_directory = config.data_root / "runs" / tracker.run_id
            self.assertEqual(tracker.run_id, payload["run_id"])
            self.assertEqual(
                {"config.yaml", "metadata.json", "results.json", "logs.txt"},
                {path.name for path in run_directory.iterdir()},
            )
            metadata = json.loads((run_directory / "metadata.json").read_text(encoding="utf-8"))
            results = json.loads((run_directory / "results.json").read_text(encoding="utf-8"))
            self.assertEqual(tracker.config_sha256, metadata["configuration_hash"])
            self.assertEqual(tracker.config_sha256, results["configuration_hash"])
            self.assertEqual("0.1.0", metadata["software_version"])
            self.assertEqual("completed", results["payload"]["status"])
            self.assertIn("Starting command", (run_directory / "logs.txt").read_text(encoding="utf-8"))

    def test_reproduce_command_matches_saved_demo_payload(self):
        with tempfile.TemporaryDirectory() as temporary_directory, patch.dict(
            "os.environ", {"PROTOTYPE_DATA_ROOT": temporary_directory}, clear=False
        ):
            self.assertEqual(0, main(("demo",)))
            runs = sorted((Path(temporary_directory) / "runs").iterdir())
            self.assertEqual(1, len(runs))
            run_id = runs[0].name

            self.assertEqual(0, main(("reproduce", run_id)))
            self.assertEqual(2, len(list((Path(temporary_directory) / "runs").iterdir())))

    def test_corrupt_run_record_names_the_invalid_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory) / "sample-run"
            directory.mkdir()
            (directory / "metadata.json").write_text("{}", encoding="utf-8")
            (directory / "results.json").write_text("{broken", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "invalid 'results.json'"):
                load_run(Path(temporary_directory), "sample-run")

    def test_failed_reproduction_explains_payload_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary_directory, patch.dict(
            "os.environ", {"PROTOTYPE_DATA_ROOT": temporary_directory}, clear=False
        ):
            self.assertEqual(0, main(("demo",)))
            run_id = next((Path(temporary_directory) / "runs").iterdir()).name
            results_path = Path(temporary_directory) / "runs" / run_id / "results.json"
            results = json.loads(results_path.read_text(encoding="utf-8"))
            results["payload"] = {"status": "tampered"}
            results_path.write_text(json.dumps(results), encoding="utf-8")
            errors = StringIO()

            with redirect_stderr(errors):
                status = main(("reproduce", run_id))

            self.assertEqual(2, status)
            self.assertIn("did not match its saved result", errors.getvalue())


if __name__ == "__main__":
    unittest.main()