"""Unit contracts plus opt-in offline integration with the pinned real model."""

from dataclasses import replace
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np

from src.embedding.benchmark import fixtures
from src.embedding.model import DIMENSIONS, PROJECT_ROOT, load_model
from src.embedding.pipeline import EmbeddingPipeline, check_clearance, validate_vector_matrix
from src.embedding.storage import load_artifacts, save_artifacts
from src.evaluation.pipeline_validation import APPROVED_CORPUS
from src.chunker import CodeChunker
from src.models.corpus import RepositoryMetadata
from src.parser import PythonAstParser


class EmbeddingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.chunks = fixtures(4)
        self.model = Mock()
        self.model.tokenizer.return_value = {"input_ids": list(range(20))}
        self.model.encode.side_effect = lambda texts, **kw: np.ones((len(texts), DIMENSIONS))
        self.pipeline = EmbeddingPipeline(self.root / "cache")
        self.pipeline._model = self.model

    def test_generation_order_metadata_and_normalization(self):
        first, rejected = self.pipeline._generate_validated(self.chunks)
        second, _ = self.pipeline._generate_validated(tuple(reversed(self.chunks)))
        self.assertEqual(first, second)
        self.assertEqual((), rejected)
        self.assertEqual(sorted(c.chunk_id for c in self.chunks), [e.chunk_id for e in first])
        self.assertEqual(64, len(first[0].metadata.content_sha256))
        np.testing.assert_allclose(np.linalg.norm([e.vector for e in first], axis=1), 1, atol=1e-6)

    def test_boundary_rejects_before_encoding(self):
        self.model.tokenizer.return_value = {"input_ids": [0] * 257}
        result, rejected = self.pipeline._generate_validated(self.chunks)
        self.assertFalse(result)
        self.assertEqual(4, len(rejected))
        self.model.encode.assert_not_called()
        self.model.tokenizer.return_value = {"input_ids": [0] * 256}
        result, rejected = self.pipeline._generate_validated(self.chunks)
        self.assertEqual(4, len(result))
        self.assertFalse(rejected)

    def test_duplicate_and_tampered_chunks_fail(self):
        for chunks in ((self.chunks[0], self.chunks[0]), (replace(self.chunks[0], content="bad\n"),)):
            with self.assertRaises(ValueError):
                self.pipeline._generate_validated(chunks)
        self.model.encode.assert_not_called()

    def test_invalid_outputs_fail(self):
        for vectors in (np.ones((3, 384)), np.ones((4, 383)), np.zeros((4, 384)),
                        np.full((4, 384), np.nan), np.full((4, 384), np.inf)):
            with self.subTest(shape=vectors.shape), self.assertRaises(ValueError):
                validate_vector_matrix(vectors, 4)

    def test_privacy_gate_precedes_model_loading(self):
        with patch("src.embedding.pipeline.load_model") as loader:
            with self.assertRaises(FileNotFoundError):
                self.pipeline.generate(self.chunks, self.root / "missing.json")
            path = self.root / "clearance.json"
            path.write_text('{}', encoding="utf-8")
            with self.assertRaises(ValueError):
                self.pipeline.generate(self.chunks, path)
            loader.assert_not_called()
        self.model.encode.assert_not_called()

    def test_clearance_requires_exact_snapshot_and_complete_review(self):
        spec = APPROVED_CORPUS[0]
        chunk = replace(self.chunks[0], repository_id=spec.repository_id, commit_sha=spec.commit_sha)
        record = {"repository_id": spec.repository_id, "commit_sha": spec.commit_sha,
                  "secret_review": "passed", "privacy_review": "passed", "unresolved_findings": 0,
                  "reviewer": "synthetic-reviewer", "reviewed_at": "2026-09-27", "audit_record": "local-record"}
        clearance = {"schema_version": "1.0", "snapshot_id": "corpus-snapshot-v1", "repositories": [record]}
        check_clearance((chunk,), clearance)
        for key, value in (("secret_review", "pending"), ("privacy_review", "pending"),
                           ("unresolved_findings", 1), ("reviewer", ""), ("commit_sha", "0" * 40)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_clearance((chunk,), {**clearance, "repositories": [{**record, key: value}]})
        with self.assertRaises(ValueError):
            check_clearance(self.chunks, clearance)

    def test_storage_roundtrip_integrity_and_no_source(self):
        result, rejected = self.pipeline._generate_validated(self.chunks)
        output = self.root / "run"
        save_artifacts(output, result, rejected, batch_size=32, input_count=4, clearance_sha256="fixture")
        vectors, metadata, manifest = load_artifacts(output)
        np.testing.assert_array_equal(vectors, np.asarray([e.vector for e in result], dtype=np.float32))
        self.assertEqual(4, manifest["counts"]["accepted"])
        self.assertNotIn("content", metadata[0]["metadata"])
        with self.assertRaises(FileExistsError):
            save_artifacts(output, result, rejected, batch_size=32, input_count=4, clearance_sha256="fixture")
        (output / "metadata.json").write_text('[]', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "integrity"):
            load_artifacts(output)

    def test_artifacts_must_be_external(self):
        with self.assertRaises(ValueError):
            EmbeddingPipeline(PROJECT_ROOT / "cache")

    def test_empty_source_and_empty_input_roundtrip(self):
        chunks = CodeChunker().chunk_module(PythonAstParser().parse("", "empty.py"), "",
                                            RepositoryMetadata("synthetic/fixture", "0" * 40))
        result, rejected = self.pipeline._generate_validated(chunks)
        self.assertEqual("empty", rejected[0]["reason"])
        self.model.encode.assert_not_called()
        save_artifacts(self.root / "empty", result, rejected, batch_size=32,
                       input_count=1, clearance_sha256="fixture")
        vectors, _, _ = load_artifacts(self.root / "empty")
        self.assertEqual((0, 384), vectors.shape)
        self.assertEqual(((), ()), self.pipeline._generate_validated(()))

    def test_public_run_with_synthetic_review_and_mock_encoder(self):
        # Test-only generated source using a frozen identity; no real audit attestation.
        spec = APPROVED_CORPUS[0]
        source = "value = 1\n"
        chunks = CodeChunker().chunk_module(PythonAstParser().parse(source, "fixture.py"), source,
                              RepositoryMetadata(spec.repository_id, spec.commit_sha))
        clearance = {"schema_version": "1.0", "snapshot_id": "corpus-snapshot-v1",
                     "repositories": [{"repository_id": spec.repository_id, "commit_sha": spec.commit_sha,
                     "secret_review": "passed", "privacy_review": "passed", "unresolved_findings": 0,
                     "reviewer": "test-only", "reviewed_at": "2026-09-27", "audit_record": "test-only"}]}
        path = self.root / "clearance.json"
        path.write_text(json.dumps(clearance), encoding="utf-8")
        self.pipeline.run(chunks, path, self.root / "public-run")
        vectors, metadata, manifest = load_artifacts(self.root / "public-run")
        self.assertEqual((1, 384), vectors.shape)
        self.assertEqual(chunks[0].chunk_id, metadata[0]["chunk_id"])
        self.assertEqual(64, len(manifest["clearance_sha256"]))

    def test_model_loading_is_pinned_cpu_and_offline(self):
        with patch("sentence_transformers.SentenceTransformer") as constructor:
            constructor.return_value.get_embedding_dimension.return_value = 384
            constructor.return_value.max_seq_length = 256
            load_model(self.root)
            kwargs = constructor.call_args.kwargs
            self.assertTrue(kwargs["local_files_only"])
            self.assertFalse(kwargs["trust_remote_code"])
            self.assertEqual("cpu", kwargs["device"])
            self.assertEqual(40, len(kwargs["revision"]))
            constructor.return_value.max_seq_length = 512
            with self.assertRaises(ValueError):
                load_model(self.root)

    @unittest.skipUnless(os.environ.get("EMBEDDING_MODEL_CACHE"), "set EMBEDDING_MODEL_CACHE for real offline inference")
    def test_real_model_offline_repeatability(self):
        pipeline = EmbeddingPipeline(Path(os.environ["EMBEDDING_MODEL_CACHE"]))
        with patch.object(socket.socket, "connect", side_effect=AssertionError("Network prohibited")):
            first, _ = pipeline._generate_validated(self.chunks)
            second, _ = pipeline._generate_validated(self.chunks)
            boundary_chunks = []
            for count in (253, 254):
                source = "# " + "x " * count + "\n"
                boundary_chunks.extend(CodeChunker().chunk_module(
                    PythonAstParser().parse(source, f"boundary_{count}.py"), source,
                    RepositoryMetadata("synthetic/fixture", "0" * 40)))
            accepted, rejected = pipeline._generate_validated(boundary_chunks)
        self.assertEqual(first, second)
        self.assertEqual(384, len(first[0].vector))
        self.assertEqual([256], [e.metadata.token_count for e in accepted])
        self.assertEqual([257], [r["token_count"] for r in rejected])


if __name__ == "__main__":
    unittest.main()
