"""Rank-fusion contracts and local end-to-end hybrid query integration."""

from dataclasses import asdict, replace
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np

from src.chunker import CodeChunker
from src.embedding.pipeline import EmbeddingPipeline, digest
from src.embedding.storage import save_artifacts, write_json
from src.evaluation.pipeline_validation import APPROVED_CORPUS
from src.models.corpus import RepositoryMetadata
from src.models.embedding import Embedding, EmbeddingMetadata
from src.models.retrieval_result import SearchResult
from src.parser import PythonAstParser
from src.retrieval import BM25Index, HybridSearch, VectorIndex
from src.retrieval.rrf import fuse_rankings, reciprocal_rank


def result(cid, rank, score=1.0):
    return SearchResult(cid, rank, score, EmbeddingMetadata(
        "synthetic/repository", "a" * 40, f"{cid}.py", "module", cid, 1, 2, "b" * 64, 10))


class RRFTests(unittest.TestCase):
    def test_reciprocal_rank_constant_and_invalid_ranks(self):
        self.assertEqual(1 / 61, reciprocal_rank(1))
        self.assertEqual(1 / 110, reciprocal_rank(50))
        for rank in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                reciprocal_rank(rank)

    def test_fusion_promotes_agreement_and_preserves_evidence(self):
        dense = (result("a", 1, .9), result("b", 2, .8))
        lexical = (result("b", 1, 100), result("c", 2, 30))
        fused = fuse_rankings({"dense": dense, "bm25": lexical})
        self.assertEqual(["b", "a", "c"], [r.chunk_id for r in fused])
        self.assertAlmostEqual(1 / 61 + 1 / 62, fused[0].score)
        self.assertEqual(dense[1].metadata, fused[0].metadata)
        self.assertEqual("hybrid", fused[0].strategy)
        self.assertIsInstance(fused[0], SearchResult)
        self.assertEqual([("bm25", 1, 100), ("dense", 2, .8)],
                         [(c.channel, c.rank, c.score) for c in fused[0].contributions])
        self.assertEqual([1, 2, 3], [r.rank for r in fused])

    def test_raw_score_scale_does_not_change_fused_scores(self):
        original = (result("a", 1, -0.1), result("b", 2, -0.9))
        changed = tuple(replace(r, score=r.score * 10000) for r in original)
        first = fuse_rankings({"dense": original})
        second = fuse_rankings({"dense": changed})
        self.assertEqual([(r.chunk_id, r.score) for r in first], [(r.chunk_id, r.score) for r in second])

    def test_ties_and_channel_order_are_deterministic(self):
        a = (result("b", 1), result("a", 2))
        b = (result("a", 1), result("b", 2))
        expected = fuse_rankings({"first": a, "second": b})
        self.assertEqual(["a", "b"], [r.chunk_id for r in expected])
        self.assertEqual(expected, fuse_rankings({"second": b, "first": a}))
        self.assertEqual(expected[:1], fuse_rankings({"second": b, "first": a}, k=1))

    def test_multiple_rankings_count_each_channel_once(self):
        fused = fuse_rankings({name: (result("a", 1),) for name in ("x", "y", "z")})
        self.assertAlmostEqual(3 / 61, fused[0].score)
        self.assertEqual(1, len(fused))

    def test_empty_and_missing_channel_contributions(self):
        self.assertEqual((), fuse_rankings({}))
        self.assertEqual((), fuse_rankings({"dense": (), "bm25": ()}))
        fused = fuse_rankings({"dense": (result("a", 1),), "bm25": ()})
        self.assertEqual(1 / 61, fused[0].score)
        self.assertEqual(1, len(fused[0].contributions))

    def test_input_and_output_windows_are_fixed(self):
        a = tuple(result(f"a{i:02}", i + 1) for i in range(51))
        b = tuple(result(f"b{i:02}", i + 1) for i in range(51))
        fused = fuse_rankings({"dense": a, "bm25": b})
        self.assertEqual(50, len(fused))
        only_a = fuse_rankings({"dense": a})
        self.assertNotIn("a50", [r.chunk_id for r in only_a])
        for k in (0, 51, True, 1.5):
            with self.assertRaises(ValueError):
                fuse_rankings({}, k)

    def test_malformed_component_rankings_fail(self):
        cases = [(result("a", 2),), (result("a", 1), result("a", 2)),
                 (result("a", True),), (result("", 1),), (result("a", 1, float("nan")),)]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                fuse_rankings({"dense": rows})
        with self.assertRaises(ValueError):
            fuse_rankings({"": ()})

    def test_conflicting_provenance_and_mixed_snapshots_fail(self):
        original = result("a", 1)
        for field, value in (("qualified_name", "different"), ("commit_sha", "c" * 40)):
            changed = replace(original, metadata=replace(original.metadata, **{field: value}))
            with self.subTest(field=field), self.assertRaises(ValueError):
                fuse_rankings({"dense": (original,), "bm25": (changed,)})


class HybridSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.spec = APPROVED_CORPUS[0]
        self.clearance = self.root / "clearance.json"
        write_json(self.clearance, {"schema_version": "1.0", "snapshot_id": "corpus-snapshot-v1",
            "repositories": [{"repository_id": self.spec.repository_id, "commit_sha": self.spec.commit_sha,
            "secret_review": "passed", "privacy_review": "passed", "unresolved_findings": 0,
            "reviewer": "test-only", "reviewed_at": "2026-09-27", "audit_record": "synthetic-test-only"}]})
        self.chunks = tuple(CodeChunker().chunk_module(PythonAstParser().parse(source, f"fixture_{i}.py"),
            source, RepositoryMetadata(self.spec.repository_id, self.spec.commit_sha))[0]
            for i, source in enumerate(("def load_user():\n    return 1\n", "def render_page():\n    return 2\n")))
        records = []
        for chunk in sorted(self.chunks, key=lambda c: c.chunk_id):
            meta = asdict(chunk)
            meta.pop("chunk_id")
            meta.pop("content")
            records.append(Embedding(chunk.chunk_id, (1.,) + (0.,) * 383,
                EmbeddingMetadata(**meta, content_sha256=digest(chunk.content.encode()), token_count=14)))
        self.artifacts = self.root / "embeddings"
        save_artifacts(self.artifacts, records, (), batch_size=32, input_count=2,
                       clearance_sha256=digest(self.clearance.read_bytes()))
        self.dense, self.lexical = self.indexes(self.artifacts)
        self.hybrid = HybridSearch(self.dense, self.lexical, self.root / "cache")
        self.model = Mock()
        self.model.tokenizer.return_value = {"input_ids": [1] * 10}
        self.model.encode.return_value = np.array([[1.] + [0.] * 383], dtype=np.float32)
        self.hybrid._model = self.model

    def indexes(self, directory):
        identity = {"repository_id": self.spec.repository_id, "commit_sha": self.spec.commit_sha}
        return (VectorIndex.build(directory, self.clearance, **identity),
                BM25Index.build(self.chunks, directory, self.clearance, **identity))

    def test_complete_flow_and_details(self):
        with patch.object(socket.socket, "connect", side_effect=AssertionError("Network prohibited")):
            report = self.hybrid.search_with_details(" load_user ", k=1)
        self.assertEqual(self.chunks[0].chunk_id, report.hybrid[0].chunk_id)
        self.assertEqual(2, len(report.dense))
        self.assertEqual(1, len(report.lexical))
        self.assertEqual(10, report.query_token_count)
        self.assertEqual(60, report.rrf_constant)
        self.assertEqual(report.hybrid, self.hybrid.search("load_user", k=1))
        self.model.encode.assert_called_with(["load_user"], batch_size=32, show_progress_bar=False,
                                            convert_to_numpy=True, normalize_embeddings=False)

    def test_smaller_output_cutoff_does_not_reduce_component_windows(self):
        with (patch.object(self.dense, "search", wraps=self.dense.search) as dense_search,
              patch("src.retrieval.hybrid_search.BM25Search") as lexical_search):
            lexical_search.return_value.search.return_value = ()
            self.hybrid.search("load_user", k=1)
            self.assertEqual(50, dense_search.call_args.kwargs["k"])
            lexical_search.return_value.search.assert_called_once_with("load_user", k=50)

    def test_unknown_lexical_query_still_returns_dense_contributions(self):
        report = self.hybrid.search_with_details("unknownword")
        self.assertEqual((), report.lexical)
        self.assertEqual(2, len(report.hybrid))
        self.assertTrue(all(r.contributions[0].channel == "dense" for r in report.hybrid))

    def test_blank_and_oversized_queries_rejected_before_inference(self):
        for query in ("", "   ", None):
            with self.assertRaises(ValueError):
                self.hybrid.search(query)
        self.model.tokenizer.return_value = {"input_ids": [1] * 257}
        with self.assertRaisesRegex(ValueError, "256"):
            self.hybrid.search("oversized")
        self.model.encode.assert_not_called()
        self.model.tokenizer.return_value = {"input_ids": [1] * 256}
        self.assertTrue(self.hybrid.search("accepted"))

    def test_invalid_encoder_output_and_channel_failure_abort(self):
        self.model.encode.return_value = np.zeros((1, 384))
        with self.assertRaises(ValueError):
            self.hybrid.search("query")
        self.model.encode.return_value = np.ones((1, 384))
        with patch.object(self.dense, "search", side_effect=RuntimeError("failure")):
            with self.assertRaises(RuntimeError):
                self.hybrid.search("query")

    def test_incompatible_index_inventory_provenance_and_run_fail(self):
        for field, value in (("_ids", ("different",)), ("_metadata", ()),
                             ("_embedding_run_sha256", "different"), ("_repository_id", "other")):
            with patch.object(self.dense, field, value):
                with self.subTest(field=field), self.assertRaises(ValueError):
                    HybridSearch(self.dense, self.lexical, self.root / "cache")

    def test_query_runtime_must_match_embedding_runtime(self):
        run = {**self.dense._embedding_run, "python": "different"}
        with patch.object(self.dense, "_embedding_run", run), patch.object(self.lexical, "_embedding_run", run):
            with self.assertRaisesRegex(ValueError, "runtime"):
                HybridSearch(self.dense, self.lexical, self.root / "cache")

    @unittest.skipUnless(os.environ.get("EMBEDDING_MODEL_CACHE"), "set EMBEDDING_MODEL_CACHE for offline integration")
    def test_real_embedding_to_persisted_indexes_to_text_query_offline(self):
        cache = Path(os.environ["EMBEDDING_MODEL_CACHE"])
        with patch.object(socket.socket, "connect", side_effect=AssertionError("Network prohibited")):
            artifacts = self.root / "real-embeddings"
            EmbeddingPipeline(cache).run(self.chunks, self.clearance, artifacts)
            dense, lexical = self.indexes(artifacts)
            dense.save(self.root / "dense")
            lexical.save(self.root / "lexical")
            hybrid = HybridSearch(VectorIndex.load(self.root / "dense", self.clearance),
                                  BM25Index.load(self.root / "lexical", self.clearance), cache)
            first = hybrid.search_with_details("load_user")
            self.assertEqual(first, hybrid.search_with_details("load_user"))
            self.assertEqual(self.chunks[0].chunk_id, first.hybrid[0].chunk_id)
            with self.assertRaisesRegex(ValueError, "256"):
                hybrid.search("x " * 255)


if __name__ == "__main__":
    unittest.main()
