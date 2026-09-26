"""Synthetic-only tests for benchmark freeze validation."""

from dataclasses import replace
import unittest

from src.evaluation.benchmark import Benchmark, BenchmarkCase
from src.evaluation.benchmark_validator import BenchmarkValidator
from src.models.corpus import RepositoryMetadata
from src.chunker import CodeChunker
from src.parser import PythonAstParser


REPOSITORY_ID = "example/fixture"
COMMIT_SHA = "a" * 40
SOURCE = "def authenticate(user):\n    return user\n\nvalue = 1\n"


class BenchmarkValidationTests(unittest.TestCase):
    def setUp(self):
        module = PythonAstParser().parse(SOURCE, "auth.py")
        self.chunks = CodeChunker().chunk_module(
            module, SOURCE, RepositoryMetadata(REPOSITORY_ID, COMMIT_SHA)
        )
        self.case = BenchmarkCase(
            "fixture-001",
            REPOSITORY_ID,
            COMMIT_SHA,
            "Where is user authentication implemented?",
            ((self.chunks[1].chunk_id, 2),),
        )
        self.benchmark = Benchmark("1.0", (self.case,))
        self.snapshots = {REPOSITORY_ID: COMMIT_SHA}
        self.validator = BenchmarkValidator()

    def test_valid_benchmark(self):
        report = self.validator.validate(self.benchmark, self.chunks, self.snapshots)

        self.assertTrue(report.is_valid)
        self.assertEqual(1, report.case_count)
        self.assertEqual(1, report.validated_case_count)
        self.assertEqual(len(self.chunks), report.inventory_chunk_count)
        self.assertEqual((), report.issues)

    def test_detects_missing_relevant_chunk(self):
        case = replace(self.case, relevance=(("missing-chunk", 2),))
        report = self.validator.validate(Benchmark("1.0", (case,)), self.chunks, self.snapshots)

        self.assertFalse(report.is_valid)
        self.assertIn("missing_chunk_id", report.issues)

    def test_detects_snapshot_mismatch(self):
        case = replace(self.case, commit_sha="b" * 40)
        report = self.validator.validate(Benchmark("1.0", (case,)), self.chunks, self.snapshots)

        self.assertFalse(report.is_valid)
        self.assertIn("snapshot_mismatch", report.issues)

    def test_detects_mixed_snapshot_in_chunk_inventory(self):
        chunks = (replace(self.chunks[0], commit_sha="b" * 40), *self.chunks[1:])
        report = self.validator.validate(self.benchmark, chunks, self.snapshots)

        self.assertFalse(report.is_valid)
        self.assertIn("inventory_snapshot_mismatch", report.issues)

    def test_rejects_invalid_relevance_grades(self):
        for grade in (0, 3, True, 1.5):
            with self.subTest(grade=grade):
                case = replace(self.case, relevance=((self.chunks[1].chunk_id, grade),))
                report = self.validator.validate(
                    Benchmark("1.0", (case,)), self.chunks, self.snapshots
                )
                self.assertFalse(report.is_valid)
                self.assertIn("relevance_grade_invalid", report.issues)

    def test_rejects_malformed_query_and_query_id(self):
        case = replace(self.case, query="  query\ntext  ", query_id="q-1")
        report = self.validator.validate(Benchmark("1.0", (case,)), self.chunks, self.snapshots)

        self.assertIn("query_format_invalid", report.issues)
        self.assertIn("query_id_format_invalid", report.issues)


if __name__ == "__main__":
    unittest.main()