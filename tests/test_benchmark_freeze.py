"""Synthetic-only deterministic benchmark freeze metadata tests."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from src.chunker import CodeChunker
from src.evaluation.benchmark import Benchmark, BenchmarkCase
from src.evaluation.benchmark_freeze import BenchmarkFreezeUtility
from src.models.corpus import RepositoryMetadata
from src.parser import PythonAstParser


REPOSITORY_ID = "example/fixture"
COMMIT_SHA = "a" * 40


class BenchmarkFreezeTests(unittest.TestCase):
    def setUp(self):
        source = "def authenticate(user):\n    return user\n"
        self.chunks = CodeChunker().chunk_module(
            PythonAstParser().parse(source, "auth.py"),
            source,
            RepositoryMetadata(REPOSITORY_ID, COMMIT_SHA),
        )
        self.cases = (
            BenchmarkCase("fixture-001", REPOSITORY_ID, COMMIT_SHA,
                          "Where is authentication handled?",
                          ((self.chunks[1].chunk_id, 2),)),
            BenchmarkCase("fixture-002", REPOSITORY_ID, COMMIT_SHA,
                          "What does the module define?",
                          ((self.chunks[0].chunk_id, 1),)),
        )
        self.benchmark = Benchmark("1.0", self.cases)
        self.snapshots = {REPOSITORY_ID: COMMIT_SHA}
        self.categories = {
            "fixture-001": "code_navigation",
            "fixture-002": "architecture_understanding",
        }
        self.utility = BenchmarkFreezeUtility()
        self.ledger_hash = "1" * 64
        self.review_hash = "2" * 64

    def freeze(self, benchmark=None, categories=None, **kwargs):
        return self.utility.freeze(
            benchmark or self.benchmark,
            self.chunks,
            self.snapshots,
            categories or self.categories,
            annotation_ledger_sha256=self.ledger_hash,
            **kwargs,
        )

    def test_hash_is_deterministic_across_case_and_label_order(self):
        first = self.freeze(review_record_sha256=self.review_hash)
        reordered = Benchmark("1.0", tuple(reversed(self.cases)))
        second = self.freeze(benchmark=reordered, review_record_sha256=self.review_hash)

        self.assertEqual(first.benchmark_sha256, second.benchmark_sha256)
        self.assertEqual(first.snapshot_map_sha256, second.snapshot_map_sha256)
        self.assertEqual(first.freeze_bundle_sha256, second.freeze_bundle_sha256)

    def test_metadata_reports_counts_and_does_not_claim_incomplete_fixture_is_frozen(self):
        metadata = self.freeze(review_record_sha256=self.review_hash)

        self.assertEqual("validated_pending_target_coverage", metadata.freeze_status)
        self.assertEqual("passed", metadata.validation_status)
        self.assertFalse(metadata.target_coverage_ready)
        self.assertEqual(2, metadata.query_count)
        self.assertEqual(1, metadata.repository_count)
        self.assertEqual(2, metadata.chunk_reference_count)
        self.assertEqual(2, metadata.unique_chunk_reference_count)
        self.assertEqual(len(self.chunks), metadata.chunk_inventory_count)
        self.assertEqual(self.review_hash, metadata.review_record_sha256)
        self.assertIn(metadata.benchmark_sha256, metadata.to_json())

    def test_complete_reviewed_target_is_reported_frozen(self):
        complete_chunks = []
        complete_cases = []
        complete_categories = {}
        category_names = (
            "architecture_understanding",
            "code_navigation",
            "dependency_understanding",
            "bug_investigation",
        )
        complete_snapshots = {}
        for repository_number in range(9):
            repository_id = f"owner/repo{repository_number}"
            commit_sha = f"{repository_number + 10:040x}"
            complete_snapshots[repository_id] = commit_sha
            source = "value = 1\n"
            chunk = CodeChunker().chunk_module(
                PythonAstParser().parse(source, "module.py"),
                source,
                RepositoryMetadata(repository_id, commit_sha),
            )[0]
            complete_chunks.append(chunk)
            for sequence in range(12):
                query_id = f"repo{repository_number}-{sequence + 1:03}"
                complete_cases.append(BenchmarkCase(
                    query_id, repository_id, commit_sha,
                    f"Question {sequence + 1} for repository {repository_number}?",
                    ((chunk.chunk_id, 2),),
                ))
                complete_categories[query_id] = category_names[sequence % 4]

        metadata = self.utility.freeze(
            Benchmark("1.0", tuple(complete_cases)),
            complete_chunks,
            complete_snapshots,
            complete_categories,
            annotation_ledger_sha256=self.ledger_hash,
            review_record_sha256=self.review_hash,
        )

        self.assertTrue(metadata.target_coverage_ready)
        self.assertEqual("frozen", metadata.freeze_status)
        self.assertEqual(108, metadata.query_count)
        self.assertEqual(9, metadata.repository_count)
        self.assertEqual(108, metadata.chunk_reference_count)
        self.assertEqual(27, dict(metadata.category_counts)["bug_investigation"])

    def test_rejects_invalid_benchmark_before_creating_freeze_metadata(self):
        case = replace(self.cases[0], relevance=(("absent-chunk", 2),))
        invalid = Benchmark("1.0", (case,))

        with self.assertRaisesRegex(ValueError, "missing_chunk_id"):
            self.freeze(benchmark=invalid)

    def test_rejects_unknown_categories_and_invalid_annotation_hash(self):
        with self.assertRaisesRegex(ValueError, "unknown query category"):
            self.freeze(categories={**self.categories, "fixture-001": "other"})
        with self.assertRaisesRegex(ValueError, "annotation_ledger_sha256"):
            self.utility.freeze(
                self.benchmark, self.chunks, self.snapshots, self.categories,
                annotation_ledger_sha256="not-a-digest",
            )

    def test_metadata_file_is_external_and_never_overwritten(self):
        metadata = self.freeze()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "freeze.json"
            self.utility.write_metadata(metadata, path)
            self.assertEqual(metadata.to_json(), path.read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                self.utility.write_metadata(metadata, path)


if __name__ == "__main__":
    unittest.main()