"""Progress and scaffold tests using public snapshot metadata only."""

import json
from pathlib import Path
import tempfile
import unittest

from src.evaluation.benchmark_statistics import (
    calculate_benchmark_statistics,
    create_annotation_template,
)
from src.evaluation.pipeline_validation import APPROVED_CORPUS


class BenchmarkStatisticsTests(unittest.TestCase):
    def test_template_has_108_slots_with_balanced_categories(self):
        with tempfile.TemporaryDirectory() as temp:
            path = create_annotation_template(Path(temp) / "annotation-template.json")
            payload = json.loads(path.read_text(encoding="utf-8"))

        report = calculate_benchmark_statistics(payload)
        self.assertEqual(108, report.case_slots)
        self.assertEqual(108, report.target_query_count)
        self.assertEqual(0, report.authored_query_count)
        self.assertEqual(0, report.annotated_case_count)
        self.assertEqual(0.0, report.annotation_completeness)
        self.assertEqual(9, report.repository_count)
        self.assertEqual(0, report.repositories_with_authored_queries)
        self.assertEqual(27, dict(report.category_distribution)["architecture_understanding"])
        self.assertEqual("not_run", report.chunk_validation_status)
        self.assertEqual((), report.issue_codes)

    def test_template_carries_frozen_snapshots_and_external_path_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            path = create_annotation_template(Path(temp) / "template.json")
            payload = json.loads(path.read_text(encoding="utf-8"))
            cases = payload["cases"]
            self.assertEqual(108, len({case["query_id"] for case in cases}))
            self.assertEqual(
                {(repo.repository_id, repo.commit_sha) for repo in APPROVED_CORPUS},
                {(case["repository_id"], case["commit_sha"]) for case in cases},
            )
            self.assertTrue(all(case["query"] == "" and not case["relevance"] for case in cases))
            with self.assertRaises(FileExistsError):
                create_annotation_template(path)

        from src.embedding.model import PROJECT_ROOT

        with self.assertRaisesRegex(ValueError, "outside the project"):
            create_annotation_template(PROJECT_ROOT / "annotation-template.json")

    def test_statistics_detect_missing_chunk_ids_when_inventory_is_supplied(self):
        payload = {
            "template_schema_version": "1.0",
            "cases": [{
                "query_id": "fixture-001",
                "repository_id": APPROVED_CORPUS[0].repository_id,
                "commit_sha": APPROVED_CORPUS[0].commit_sha,
                "category": "code_navigation",
                "query": "Where is this behavior implemented?",
                "relevance": {"absent-chunk": 2},
                "expected_files": ["module.py"],
                "expected_spans": [{"file": "module.py", "symbol": "run", "lines": [1, 2]}],
                "annotation_rationale": "Direct evidence.",
                "ambiguity_notes": "None.",
            }],
        }
        snapshot = (APPROVED_CORPUS[0].repository_id, APPROVED_CORPUS[0].commit_sha)
        report = calculate_benchmark_statistics(payload, {snapshot: {"other-chunk"}})

        self.assertEqual(1, report.authored_query_count)
        self.assertEqual(0, report.annotated_case_count)
        self.assertEqual("failed", report.chunk_validation_status)
        self.assertEqual(1, report.missing_chunk_reference_count)
        self.assertIn("chunk_reference_missing", report.issue_codes)

    def test_statistics_count_completed_annotation_and_matching_chunk(self):
        repository = APPROVED_CORPUS[0]
        payload = {
            "template_schema_version": "1.0",
            "cases": [{
                "query_id": "python-dotenv-001",
                "repository_id": repository.repository_id,
                "commit_sha": repository.commit_sha,
                "category": "code_navigation",
                "query": "Where is loading configured?",
                "relevance": {"known-chunk": 2},
                "expected_files": ["config.py"],
                "expected_spans": [{"file": "config.py", "symbol": "load", "lines": [2, 8]}],
                "annotation_rationale": "This is the direct implementation.",
                "ambiguity_notes": "None.",
            }],
        }
        snapshot = (repository.repository_id, repository.commit_sha)
        report = calculate_benchmark_statistics(payload, {snapshot: {"known-chunk"}})

        self.assertEqual(1, report.annotated_case_count)
        self.assertEqual(1 / 108, report.annotation_completeness)
        self.assertEqual("passed", report.chunk_validation_status)
        self.assertEqual(0, report.missing_chunk_reference_count)


if __name__ == "__main__":
    unittest.main()