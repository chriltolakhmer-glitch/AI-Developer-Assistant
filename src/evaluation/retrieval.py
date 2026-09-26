"""Deterministic evaluation of snapshot-scoped retrieval callables."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from src.models.retrieval_result import SearchResult
from .benchmark import Benchmark, BenchmarkCase
from .metrics import ndcg_at_k, recall_at_k, reciprocal_rank


@dataclass(frozen=True, slots=True)
class QueryEvaluation:
    query_id: str
    recall: tuple[tuple[int, float], ...]
    mrr: float
    ndcg: float


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    system: str
    query_results: tuple[QueryEvaluation, ...]
    recall: tuple[tuple[int, float], ...]
    mrr: float
    ndcg: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "query_results": [
                {"query_id": item.query_id, "recall": dict(item.recall),
                 "mrr": item.mrr, "ndcg": item.ndcg}
                for item in self.query_results
            ],
            "recall": dict(self.recall), "mrr": self.mrr, "ndcg": self.ndcg,
        }


Retriever = Callable[[BenchmarkCase], Sequence[SearchResult]]


class RetrievalEvaluator:
    def evaluate(self, benchmark: Benchmark, system: str, retriever: Retriever,
                 ks: tuple[int, ...] = (1, 5, 10)) -> EvaluationReport:
        if not isinstance(system, str) or not system.strip():
            raise ValueError("System name must be nonempty text")
        if not ks or any(type(k) is not int or k < 1 for k in ks):
            raise ValueError("ks must contain positive integers")
        ks = tuple(sorted(set(ks)))
        query_results = []
        for case in benchmark.cases:
            results = tuple(retriever(case))
            self._validate_snapshot(case, results)
            query_results.append(QueryEvaluation(
                case.query_id,
                tuple((k, recall_at_k(results, case.relevant_ids, k)) for k in ks),
                reciprocal_rank(results, case.relevant_ids),
                ndcg_at_k(results, case.relevance_by_id, max(ks)),
            ))
        count = len(query_results)
        return EvaluationReport(
            system,
            tuple(query_results),
            tuple((k, sum(dict(item.recall)[k] for item in query_results) / count)
                  for k in ks),
            sum(item.mrr for item in query_results) / count,
            sum(item.ndcg for item in query_results) / count,
        )

    def evaluate_systems(self, benchmark: Benchmark,
                         systems: Mapping[str, Retriever],
                         ks: tuple[int, ...] = (1, 5, 10)) -> tuple[EvaluationReport, ...]:
        return tuple(self.evaluate(benchmark, name, systems[name], ks)
                     for name in sorted(systems))

    @staticmethod
    def _validate_snapshot(case: BenchmarkCase, results: Sequence[SearchResult]) -> None:
        for result in results:
            if (result.repository_id, result.commit_sha) != (case.repository_id, case.commit_sha):
                raise ValueError("Retriever returned a result from a different snapshot")
