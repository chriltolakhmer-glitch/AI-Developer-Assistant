"""Synthetic unit fixtures for annotation preparation; not benchmark cases."""

import json
from pathlib import Path
import tempfile
import unittest

from src.evaluation.benchmark import BenchmarkLoader
from src.evaluation.benchmark_annotation import (
    add_annotation_entry,
    export_benchmark_draft,
    load_annotation_template,
    save_annotation_template,
    validate_annotation_entry,
)


class BenchmarkAnnotationTests(unittest.TestCase):
    def setUp(self):
        self.entry = {
            "query_id": "synthetic-fixture-001",
            "repository_id": "example/synthetic-fixture",
            "commit_sha": "0123456789abcdef0123456789abcdef01234567",
            "category": "code_navigation",
            "query": "Where is the fixture behavior implemented?",
            "relevance": {"synthetic-chunk-a": 2},
            "expected_files": ["src/sample.py"],
            "expected_spans": [{
                "file": "src/sample.py",
                "symbol": "sample_behavior",
                "lines": [3, 8],
            }],
            "annotation_rationale": "The selected evidence directly supports the answer.",
            "ambiguity_notes": "No unresolved ambiguity in this synthetic fixture.",
        }
        self.template = {
            "template_schema_version": "1.0",
            "status": "annotation_in_progress_not_a_validated_benchmark",
            "cases": [{
                "query_id": self.entry["query_id"],
                "repository_id": self.entry["repository_id"],
                "commit_sha": self.entry["commit_sha"],
                "category": self.entry["category"],
                "query": "",
                "relevance": {},
                "expected_files": [],
                "expected_spans": [],
                "annotation_rationale": "",
                "ambiguity_notes": "",
            }],
        }

    def test_valid_annotation_entry_is_accepted_and_added_to_matching_slot(self):
        validate_annotation_entry(self.entry, chunk_ids={"synthetic-chunk-a"})

        annotated = add_annotation_entry(
            self.template,
            self.entry,
            chunk_ids={"synthetic-chunk-a"},
        )

        self.assertEqual(self.entry["query"], annotated["cases"][0]["query"])
        self.assertEqual("", self.template["cases"][0]["query"])

    def test_missing_chunk_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown chunk ID"):
            validate_annotation_entry(self.entry, chunk_ids={"different-chunk"})

    def test_missing_relevance_chunk_is_rejected(self):
        entry = dict(self.entry)
        entry["relevance"] = {}

        with self.assertRaisesRegex(ValueError, "at least one chunk ID"):
            validate_annotation_entry(entry)

    def test_invalid_relevance_grade_is_rejected(self):
        entry = dict(self.entry)
        entry["relevance"] = {"synthetic-chunk-a": True}

        with self.assertRaisesRegex(ValueError, "integer 1 or 2"):
            validate_annotation_entry(entry)

    def test_template_round_trip_and_draft_export_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template_path = root / "annotation-template.json"
            save_annotation_template(self.template, template_path)
            loaded = load_annotation_template(template_path)
            annotated = add_annotation_entry(loaded, self.entry)
            save_annotation_template(annotated, template_path)

            inventory = {
                (self.entry["repository_id"], self.entry["commit_sha"]): {
                    "synthetic-chunk-a",
                },
            }
            first_path = export_benchmark_draft(
                annotated,
                root / "draft-one.json",
                chunk_ids_by_snapshot=inventory,
            )
            second_path = export_benchmark_draft(
                annotated,
                root / "draft-two.json",
                chunk_ids_by_snapshot=inventory,
            )

            first_text = first_path.read_text(encoding="utf-8")
            self.assertEqual(first_text, second_path.read_text(encoding="utf-8"))
            payload = json.loads(first_text)
            self.assertEqual("draft_not_validated_or_frozen", payload["status"])
            self.assertNotIn("schema_version", payload)
            self.assertEqual([self.entry["query_id"]], [case["query_id"] for case in payload["cases"]])
            self.assertNotIn("expected_spans", payload["cases"][0])
            with self.assertRaisesRegex(ValueError, "Unsupported benchmark schema"):
                BenchmarkLoader().load(first_path)


if __name__ == "__main__":
    unittest.main()