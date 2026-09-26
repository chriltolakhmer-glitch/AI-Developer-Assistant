"""Focused hybrid query orchestration and compatibility tests."""

from dataclasses import dataclass
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import numpy as np

from src.models.embedding import EmbeddingMetadata
from src.models.retrieval_result import SearchResult
from src.retrieval.hybrid_search import HybridSearch


@dataclass
class FakeIndex:
    repository_id: str = "fixture/repository"
    commit_sha: str = "a" * 40
    _ids: tuple[str, ...] = ("chunk-a", "chunk-b")
    _metadata: tuple[EmbeddingMetadata, ...] = ()
    _embedding_run_sha256: str = "run-sha"
    _embedding_run: dict = None

    @property
    def chunk_ids(self):
        return self._ids

    def search(self, query_vector, k=50):
        return ()


def metadata(chunk_id):
    return EmbeddingMetadata("fixture/repository", "a" * 40, f"{chunk_id}.py",
                             "function", chunk_id, 1, 2, "b" * 64, 8)


def result(chunk_id, rank, score, strategy):
    return SearchResult(chunk_id, rank, score, metadata(chunk_id), strategy)


class HybridSearchTests(unittest.TestCase):
    def make_channels(self):
        dense = FakeIndex(_metadata=(metadata("chunk-a"), metadata("chunk-b")))
        lexical = FakeIndex(_metadata=dense._metadata)
        dense.search = Mock(return_value=(result("chunk-a", 1, 0.9, "dense"),
                                          result("chunk-b", 2, 0.8, "dense")))
        lexical.search = Mock()
        return dense, lexical

    def make_hybrid(self):
        dense, lexical = self.make_channels()
        dense._embedding_run = lexical._embedding_run = {"batch_size": 32}
        hybrid = HybridSearch.__new__(HybridSearch)
        hybrid._dense, hybrid._lexical = dense, lexical
        hybrid._cache = Path("C:/outside-model-cache")
        hybrid._model = Mock()
        hybrid._validate_indexes = Mock()
        hybrid._model.tokenizer.return_value = {"input_ids": [1] * 8}
        hybrid._model.encode.return_value = np.array([[1.0] + [0.0] * 383], dtype=np.float32)
        return hybrid, dense, lexical

    def test_text_query_fans_out_to_dense_and_bm25_then_fuses(self):
        hybrid, dense, lexical = self.make_hybrid()
        lexical_results = (result("chunk-b", 1, 4.0, "bm25"),)
        with patch("src.retrieval.hybrid_search.BM25Search") as bm25:
            bm25.return_value.search.return_value = lexical_results
            response = hybrid.search_with_details("  load_user  ", k=2)
        self.assertEqual(("chunk-b", "chunk-a"), tuple(row.chunk_id for row in response.hybrid))
        self.assertEqual("chunk-b", response.hybrid[0].chunk_id)
        self.assertEqual(8, response.query_token_count)
        dense.search.assert_called_once()
        query_vector, = dense.search.call_args.args
        np.testing.assert_array_equal(query_vector, np.array([1.0] + [0.0] * 383, dtype=np.float32))
        self.assertEqual(50, dense.search.call_args.kwargs["k"])
        bm25.return_value.search.assert_called_once_with("load_user", k=50)
        self.assertEqual(response.hybrid[0].metadata, lexical_results[0].metadata)
        self.assertEqual("bm25", response.hybrid[0].contributions[0].channel)

    def test_component_windows_are_50_and_output_is_50(self):
        hybrid, dense, lexical = self.make_hybrid()
        dense.search.return_value = tuple(result(f"d{i}", i + 1, 1.0, "dense") for i in range(50))
        dense._ids = tuple(f"d{i}" for i in range(50))
        dense._metadata = tuple(metadata(f"d{i}") for i in range(50))
        lexical._ids = dense._ids
        lexical._metadata = dense._metadata
        lexical_results = tuple(result(f"l{i}", i + 1, 1.0, "bm25") for i in range(50))
        with patch("src.retrieval.hybrid_search.BM25Search") as bm25:
            bm25.return_value.search.return_value = lexical_results
            response = hybrid.search_with_details("query")
        self.assertEqual(50, len(response.hybrid))
        self.assertEqual(50, dense.search.call_args.kwargs["k"])
        self.assertEqual(50, bm25.return_value.search.call_args.kwargs["k"])
        self.assertEqual(60, response.rrf_constant)
        self.assertEqual(50, response.candidate_window)

    def test_snapshot_and_inventory_mismatches_fail_closed(self):
        dense, lexical = self.make_channels()
        for field, value in (("commit_sha", "c" * 40), ("_ids", ("different",))):
            changed = FakeIndex(_metadata=dense._metadata)
            setattr(changed, field, value)
            if field == "commit_sha":
                lexical = changed
            else:
                dense = changed
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "share snapshot"):
                with patch.object(HybridSearch, "_validate_indexes", HybridSearch._validate_indexes):
                    HybridSearch(dense, lexical, Path("C:/outside-model-cache"))
            dense, lexical = self.make_channels()

    def test_result_provenance_survives_hybrid_fusion(self):
        hybrid, _, _ = self.make_hybrid()
        with patch("src.retrieval.hybrid_search.BM25Search") as bm25:
            bm25.return_value.search.return_value = (result("chunk-a", 1, 2.0, "bm25"),)
            fused = hybrid.search("query")
        self.assertEqual("fixture/repository", fused[0].repository_id)
        self.assertEqual("a" * 40, fused[0].commit_sha)
        self.assertEqual("chunk-a.py", fused[0].file_path)
        self.assertEqual((1, 2), fused[0].line_range)


if __name__ == "__main__":
    unittest.main()
