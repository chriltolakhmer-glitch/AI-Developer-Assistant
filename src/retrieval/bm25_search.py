"""Deterministic positive-match BM25 ranking over the local lexical index."""

from collections import defaultdict

from src.models.retrieval_result import SearchResult
from .bm25_index import B, K1, BM25Index, tokenize


class BM25Search:
    def __init__(self, index: BM25Index):
        self.index = index

    def search(self, query: str, k: int = 50) -> tuple[SearchResult, ...]:
        if type(k) is not int or k < 1:
            raise ValueError("k must be a positive integer")
        terms = sorted(set(tokenize(query)))
        scores = defaultdict(float)
        for term in terms:
            for row, frequency in self.index._postings.get(term, ()):
                length_factor = 1 - B + B * self.index._lengths[row] / self.index._average_length
                scores[row] += self.index._idf[term] * frequency * (K1 + 1) / (frequency + K1 * length_factor)
        ranked = sorted(scores, key=lambda row: (-scores[row], self.index._ids[row]))[:k]
        return tuple(SearchResult(self.index._ids[row], rank, scores[row],
                                  self.index._metadata[row], strategy="bm25")
                     for rank, row in enumerate(ranked, start=1))
