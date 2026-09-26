"""Pure retrieval-quality metrics."""

from collections.abc import Mapping, Sequence
import math

from src.models.retrieval_result import SearchResult


def _validate_k(k: int) -> None:
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer")


def _ranked_ids(results: Sequence[SearchResult]) -> tuple[str, ...]:
    ids = []
    seen = set()
    for position, result in enumerate(results, start=1):
        if type(result.rank) is not int or result.rank != position:
            raise ValueError("Result ranks must match one-based list positions")
        if not result.chunk_id or result.chunk_id in seen:
            raise ValueError("Results must contain unique, nonempty chunk IDs")
        seen.add(result.chunk_id)
        ids.append(result.chunk_id)
    return tuple(ids)


def recall_at_k(results: Sequence[SearchResult], relevant_ids: set[str] | frozenset[str], k: int) -> float:
    _validate_k(k)
    if not relevant_ids:
        raise ValueError("At least one relevant chunk is required")
    ranked = _ranked_ids(results)[:k]
    return len(set(ranked).intersection(relevant_ids)) / len(relevant_ids)


def reciprocal_rank(results: Sequence[SearchResult], relevant_ids: set[str] | frozenset[str]) -> float:
    if not relevant_ids:
        raise ValueError("At least one relevant chunk is required")
    for rank, chunk_id in enumerate(_ranked_ids(results), start=1):
        if chunk_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(results: Sequence[SearchResult], relevance: Mapping[str, int], k: int) -> float:
    _validate_k(k)
    if not relevance or any(type(grade) is not int or grade < 1 for grade in relevance.values()):
        raise ValueError("Relevance must contain positive integer grades")
    ranked = _ranked_ids(results)[:k]

    def gain(grade: int, rank: int) -> float:
        return (2 ** grade - 1) / math.log2(rank + 1)

    actual = sum(gain(relevance[chunk_id], rank)
                 for rank, chunk_id in enumerate(ranked, start=1)
                 if chunk_id in relevance)
    ideal_grades = sorted(relevance.values(), reverse=True)[:k]
    ideal = sum(gain(grade, rank) for rank, grade in enumerate(ideal_grades, start=1))
    return actual / ideal if ideal else 0.0
