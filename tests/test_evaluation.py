"""Unit tests for deterministic retrieval evaluation."""

import json
from pathlib import Path
import tempfile
import unittest

from src.evaluation import BenchmarkLoader, RetrievalEvaluator
from src.evaluation.metrics import ndcg_at_k, recall_at_k, reciprocal_rank
from src.models.embedding import EmbeddingMetadata
from src.models.retrieval_result import SearchResult


SNAPSHOT = ("fixture/repository", "a" * 40)


def result(chunk_id, rank, score=1.0, snapshot=SNAPSHOT):
    return SearchResult(chunk_id, rank, score, EmbeddingMetadata(
        snapshot[0], snapshot[1], f"{chunk_id}.py", "function", chunk_id,
        1, 2, "b" * 64, 8))


def benchmark_payload():
    return {
        "schema_version": "1.0",
        "cases": [
            {"query_id": "q-002", "repository_id": SNAPSHOT[0], "commit_sha": SNAPSHOT[1],
             "query": "second query", "relevance": {"b": 3, "c": 1}},
            {"query_id": "q-001", "repository_id": SNAPSHOT[0], "commit_sha": SNAPSHOT[1],
             "query": "first query", "relevance": {"a": 2}},
        ],
    }


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "benchmark.json"
        self.path.write_text(json.dumps(benchmark_payload()), encoding="utf-8")
        self.benchmark = BenchmarkLoader().load(self.path)

    def test_metric_calculation(self):
        results = (result("b", 1), result("x", 2), result("c", 3))
        self.assertAlmostEqual(1.0, recall_at_k(results, {"b", "c"}, 3))
        self.assertAlmostEqual(0.5, recall_at_k(results, {"b", "c"}, 1))
        self.assertEqual(1.0, reciprocal_rank(results, {"b", "c"}))
        self.assertAlmostEqual(1 / 3, reciprocal_rank(results, {"c"}))
        self.assertAlmostEqual(0.9828422279, ndcg_at_k(results, {"b": 3, "c": 1}, 3))

    def test_metric_validation_and_ranked_evaluation(self):
        with self.assertRaises(ValueError):
            recall_at_k((), set(), 1)
        with self.assertRaises(ValueError):
            recall_at_k((result("a", 2),), {"a"}, 1)
        with self.assertRaises(ValueError):
            ndcg_at_k((result("a", 1),), {"a": 0}, 1)

        def dense(case):
            return (result("a", 1),) if case.query_id == "q-001" else (result("x", 1),)

        report = RetrievalEvaluator().evaluate(self.benchmark, "dense", dense, ks=(1, 5))
        self.assertEqual("dense", report.system)
        self.assertEqual(("q-002", "q-001"), tuple(item.query_id for item in report.query_results))
        self.assertEqual(((1, 0.5), (5, 0.5)), report.recall)
        self.assertEqual(0.5, report.mrr)
        self.assertEqual(0.5, report.ndcg)

    def test_loader_and_evaluation_are_deterministic(self):
        first = BenchmarkLoader().load(self.path)
        second = BenchmarkLoader().load(self.path)
        self.assertEqual(first, second)

        systems = {"hybrid": lambda case: (result("b", 1), result("c", 2)),
                   "dense": lambda case: (result("a", 1),)}
        evaluator = RetrievalEvaluator()
        first_reports = evaluator.evaluate_systems(first, systems, ks=(1, 5))
        second_reports = evaluator.evaluate_systems(second, systems, ks=(1, 5))
        self.assertEqual(first_reports, second_reports)
        self.assertEqual(("dense", "hybrid"), tuple(report.system for report in first_reports))

    def test_snapshot_mismatch_is_rejected(self):
        def wrong_snapshot(case):
            return (result("a", 1, snapshot=(case.repository_id, "c" * 40)),)

        with self.assertRaisesRegex(ValueError, "different snapshot"):
            RetrievalEvaluator().evaluate(self.benchmark, "wrong", wrong_snapshot)


if __name__ == "__main__":
    unittest.main()
