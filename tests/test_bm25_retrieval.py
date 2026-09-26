"""Lexical scoring, accepted-inventory alignment, and shared result contracts."""

from dataclasses import asdict, replace
import json
import math
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from src.chunker import CodeChunker
from src.embedding.model import PROJECT_ROOT
from src.embedding.pipeline import digest
from src.embedding.storage import save_artifacts, write_json
from src.evaluation.pipeline_validation import APPROVED_CORPUS
from src.models.corpus import RepositoryMetadata
from src.models.embedding import Embedding, EmbeddingMetadata
from src.models.retrieval_result import RetrievalResult
from src.parser import PythonAstParser
from src.retrieval import BM25Index, BM25Search, SearchResult, VectorIndex
from src.retrieval.bm25_index import tokenize


class BM25RetrievalTests(unittest.TestCase):
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
        self.chunks = self.make_chunks((
            "def load_user_profile(user_id):\n    return user_id\n",
            "def renderPage(template):\n    return template\n",
            "def parseHTTPResponse(response):\n    return response\n",
        ))
        self.artifacts = self.root / "embeddings"
        self.save_embeddings(self.chunks, self.artifacts)

    def make_chunks(self, sources):
        return tuple(CodeChunker().chunk_module(PythonAstParser().parse(source, f"fixture_{i}.py"),
            source, RepositoryMetadata(self.spec.repository_id, self.spec.commit_sha))[0]
            for i, source in enumerate(sources))

    def save_embeddings(self, chunks, directory):
        embeddings = []
        for chunk in sorted(chunks, key=lambda c: c.chunk_id):
            meta = asdict(chunk)
            meta.pop("chunk_id")
            meta.pop("content")
            embeddings.append(Embedding(chunk.chunk_id, (1.0,) + (0.0,) * 383,
                EmbeddingMetadata(**meta, content_sha256=digest(chunk.content.encode()), token_count=20)))
        save_artifacts(directory, embeddings, (), batch_size=32, input_count=len(chunks),
                       clearance_sha256=digest(self.clearance.read_bytes()))

    def build(self, chunks=None, artifacts=None):
        return BM25Index.build(self.chunks if chunks is None else chunks,
            artifacts or self.artifacts, self.clearance,
            repository_id=self.spec.repository_id, commit_sha=self.spec.commit_sha)

    def test_build_stores_tokens_and_same_dense_inventory(self):
        index = self.build()
        dense = VectorIndex.build(self.artifacts, self.clearance,
            repository_id=self.spec.repository_id, commit_sha=self.spec.commit_sha)
        self.assertEqual(3, index.count)
        self.assertEqual(tuple(sorted(c.chunk_id for c in self.chunks)), index.chunk_ids)
        self.assertEqual(set(index.chunk_ids), {r.chunk_id for r in dense.search([1.0] + [0.0] * 383)})
        self.assertIn("load_user_profile", sum(index.tokenized_chunks, ()))

    def test_keyword_and_identifier_matches(self):
        search = BM25Search(self.build())
        for query, position in (("template", 1), ("load_user_profile", 0),
                                ("parseHTTPResponse", 2), ("HTTP response", 2),
                                ("USER profile", 0), ("renderPage", 1)):
            with self.subTest(query=query):
                results = search.search(query)
                self.assertEqual(self.chunks[position].chunk_id, results[0].chunk_id)
                self.assertGreater(results[0].score, 0)

    def test_tokenizer_preserves_identifiers_and_components(self):
        self.assertEqual(("get_http2_response", "get", "http", "2", "response"),
                         tokenize("get_HTTP2_response"))
        self.assertEqual(("parsehttpresponse", "parse", "http", "response"), tokenize("parseHTTPResponse"))
        self.assertEqual(("__init__", "init", "café", "42"), tokenize("__init__ Café 42 + _"))
        self.assertEqual(("foo_foo", "foo", "foo_foo", "foo"), tokenize("foo_foo foo_foo"))

    def test_shared_result_preserves_provenance(self):
        result = BM25Search(self.build()).search("load_user_profile")[0]
        self.assertIs(SearchResult, RetrievalResult)
        self.assertIsInstance(result, RetrievalResult)
        chunk = self.chunks[0]
        for field in ("chunk_id", "repository_id", "commit_sha", "file_path", "entity_type", "qualified_name",
                      "start_line", "end_line"):
            self.assertEqual(getattr(chunk, field), getattr(result, field))
        self.assertEqual((1, 2), result.line_range)
        self.assertEqual("bm25", result.strategy)
        self.assertEqual(digest(chunk.content.encode()), result.metadata.content_sha256)

    def test_repeatability_and_query_term_policy(self):
        first = BM25Search(self.build())
        second = BM25Search(self.build(tuple(reversed(self.chunks))))
        self.assertEqual(first.search("return def"), second.search("def return return"))
        self.assertEqual(first.search("return"), first.search("return"))

    def test_equal_scores_break_ties_before_cutoff(self):
        chunks = self.make_chunks(("# same words\n",) * 3)
        directory = self.root / "ties"
        self.save_embeddings(chunks, directory)
        search = BM25Search(self.build(chunks, directory))
        self.assertEqual(min(c.chunk_id for c in chunks), search.search("same", 1)[0].chunk_id)
        self.assertEqual([1, 2, 3], [r.rank for r in search.search("same", 100)])

    def test_scoring_against_hand_computed_example(self):
        chunks = self.make_chunks(("# apple apple\n", "# banana\n"))
        directory = self.root / "formula"
        self.save_embeddings(chunks, directory)
        result = BM25Search(self.build(chunks, directory)).search("apple")[0]
        # N=2, df=1, tf=2, length=2, avg_length=1.5, k1=1.2, b=.75.
        self.assertAlmostEqual(math.log(2) * 4.4 / 3.5, result.score, places=12)

    def test_length_normalization_and_term_frequency(self):
        chunks = self.make_chunks(("# apple\n", "# apple banana banana\n", "# apple apple apple\n"))
        directory = self.root / "lengths"
        self.save_embeddings(chunks, directory)
        scores = {r.chunk_id: r.score for r in BM25Search(self.build(chunks, directory)).search("apple")}
        self.assertGreater(scores[chunks[0].chunk_id], scores[chunks[1].chunk_id])
        self.assertGreater(scores[chunks[2].chunk_id], scores[chunks[1].chunk_id])

    def test_empty_unknown_and_invalid_queries(self):
        search = BM25Search(self.build())
        for query in ("", "  ", "+ - ()", "nonexistentidentifier"):
            self.assertEqual((), search.search(query))
        with self.assertRaises(ValueError):
            search.search(None)
        for k in (0, -1, True, 2.5):
            with self.assertRaises(ValueError):
                search.search("return", k)

    def test_zero_lexical_token_inventory(self):
        chunks = self.make_chunks(("# + -\n",))
        directory = self.root / "no-terms"
        self.save_embeddings(chunks, directory)
        index = self.build(chunks, directory)
        self.assertEqual(((),), index.tokenized_chunks)
        self.assertEqual((), BM25Search(index).search("anything"))

    def test_only_dense_accepted_chunks_are_indexed(self):
        extra = self.make_chunks(("# excludeduniqueterm\n",))[0]
        index = self.build((*self.chunks, extra))
        self.assertEqual(3, index.count)
        self.assertEqual((), BM25Search(index).search("excludeduniqueterm"))
        with self.assertRaisesRegex(ValueError, "Missing accepted"):
            self.build(self.chunks[:-1])

    def test_duplicate_tampered_and_cross_snapshot_chunks_fail(self):
        for chunks in ((*self.chunks, self.chunks[0]),
                       (replace(self.chunks[0], content="changed\n"), *self.chunks[1:]),
                       (replace(self.chunks[0], repository_id="other"), *self.chunks[1:])):
            with self.assertRaises(ValueError):
                self.build(chunks)

    def test_clearance_fails_before_tokenization(self):
        clearance = json.loads(self.clearance.read_text())
        clearance["repositories"][0]["privacy_review"] = "pending"
        write_json(self.clearance, clearance)
        with patch("src.retrieval.bm25_index.tokenize") as tokenizer:
            with self.assertRaises(ValueError):
                self.build()
            tokenizer.assert_not_called()

    def test_roundtrip_is_deterministic_and_offline(self):
        with patch.object(socket.socket, "connect", side_effect=AssertionError("Network prohibited")):
            index = self.build()
            output = self.root / "lexical"
            index.save(output)
            loaded = BM25Index.load(output, self.clearance)
            self.assertEqual(index.tokenized_chunks, loaded.tokenized_chunks)
            self.assertEqual(BM25Search(index).search("return"), BM25Search(loaded).search("return"))
            loaded.save(self.root / "second")
            for name in ("documents.json", "manifest.json"):
                self.assertEqual((output / name).read_bytes(), (self.root / "second" / name).read_bytes())
            with self.assertRaises(FileExistsError):
                index.save(output)
        with self.assertRaises(ValueError):
            index.save(PROJECT_ROOT / "lexical")

    def test_unicode_casefold_roundtrip(self):
        chunks = self.make_chunks(("# İstanbul café\n",))
        directory = self.root / "unicode-embeddings"
        self.save_embeddings(chunks, directory)
        index = self.build(chunks, directory)
        index.save(self.root / "unicode-index")
        loaded = BM25Index.load(self.root / "unicode-index", self.clearance)
        self.assertEqual(BM25Search(index).search("İstanbul"), BM25Search(loaded).search("İstanbul"))

    def test_corruption_and_runtime_mismatch_fail(self):
        output = self.root / "lexical"
        self.build().save(output)
        manifest = json.loads((output / "manifest.json").read_text())
        write_json(output / "manifest.json", {**manifest, "tokenizer": "changed"})
        with self.assertRaisesRegex(ValueError, "contract"):
            BM25Index.load(output, self.clearance)
        write_json(output / "manifest.json", manifest)
        (output / "documents.json").write_bytes(b"[]")
        with self.assertRaisesRegex(ValueError, "integrity"):
            BM25Index.load(output, self.clearance)

    def test_reload_requires_original_clearance(self):
        output = self.root / "lexical"
        self.build().save(output)
        self.clearance.write_bytes(self.clearance.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "Clearance differs"):
            BM25Index.load(output, self.clearance)

    def test_missing_clearance_and_empty_inventory_fail(self):
        with self.assertRaises(FileNotFoundError):
            BM25Index.build(self.chunks, self.artifacts, self.root / "absent.json",
                            repository_id=self.spec.repository_id, commit_sha=self.spec.commit_sha)
        directory = self.root / "empty"
        self.save_embeddings((), directory)
        with self.assertRaisesRegex(ValueError, "no accepted"):
            self.build((), directory)

    def test_invalid_tokens_and_provenance_fail_even_with_updated_hash(self):
        output = self.root / "lexical"
        self.build().save(output)
        original = json.loads((output / "documents.json").read_text())
        for mode in ("tokens", "metadata"):
            rows = json.loads(json.dumps(original))
            if mode == "tokens":
                rows[0]["tokens"] = ["not a token"]
            else:
                rows[0]["metadata"]["qualified_name"] = "incorrect"
            write_json(output / "documents.json", rows)
            manifest = json.loads((output / "manifest.json").read_text())
            manifest["documents_sha256"] = digest((output / "documents.json").read_bytes())
            write_json(output / "manifest.json", manifest)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                BM25Index.load(output, self.clearance)


if __name__ == "__main__":
    unittest.main()
