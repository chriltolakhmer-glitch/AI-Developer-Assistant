"""Real FAISS tests using generated provenance and synthetic unit vectors only."""

from dataclasses import replace
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

import faiss
import numpy as np

from src.chunker import CodeChunker
from src.embedding.model import PROJECT_ROOT
from src.embedding.pipeline import digest
from src.embedding.storage import save_artifacts, write_json
from src.evaluation.pipeline_validation import APPROVED_CORPUS
from src.models.corpus import RepositoryMetadata
from src.models.embedding import Embedding, EmbeddingMetadata
from src.parser import PythonAstParser
from src.retrieval import VectorIndex


class VectorRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.spec = APPROVED_CORPUS[0]
        self.query = np.eye(1, 384, dtype=np.float32)[0]
        clearance = {"schema_version": "1.0", "snapshot_id": "corpus-snapshot-v1", "repositories": [
            {"repository_id": s.repository_id, "commit_sha": s.commit_sha, "secret_review": "passed",
             "privacy_review": "passed", "unresolved_findings": 0, "reviewer": "test-only",
             "reviewed_at": "2026-09-27", "audit_record": "synthetic-test-only"}
            for s in APPROVED_CORPUS[:2]]}
        self.clearance = self.root / "clearance.json"
        write_json(self.clearance, clearance)
        records = []
        for i in range(5):
            source = f"value_{i} = {i}\n"
            chunk = CodeChunker().chunk_module(PythonAstParser().parse(source, f"fixture_{i}.py"),
                source, RepositoryMetadata(self.spec.repository_id, self.spec.commit_sha))[0]
            metadata = EmbeddingMetadata(chunk.repository_id, chunk.commit_sha, chunk.file_path,
                chunk.entity_type, chunk.qualified_name, chunk.start_line, chunk.end_line,
                digest(source.encode()), 8)
            records.append(Embedding(chunk.chunk_id, tuple(self.query), metadata))
        records.sort(key=lambda e: e.chunk_id)
        vectors = np.zeros((5, 384), dtype=np.float32)
        vectors[0, 0] = vectors[1, 0] = 1
        vectors[2, :2] = [0.6, 0.8]
        vectors[3, 1] = 1
        vectors[4, 0] = -1
        self.records = tuple(replace(r, vector=tuple(v)) for r, v in zip(records, vectors))
        self.embeddings = self.root / "embeddings"
        save_artifacts(self.embeddings, self.records, (), batch_size=32, input_count=5,
                       clearance_sha256=digest(self.clearance.read_bytes()))

    def build(self):
        return VectorIndex.build(self.embeddings, self.clearance,
                                 repository_id=self.spec.repository_id, commit_sha=self.spec.commit_sha)

    def test_creation_exact_cosine_and_provenance(self):
        index = self.build()
        self.assertEqual(5, index.count)
        results = index.search(self.query, 50)
        self.assertEqual([r.chunk_id for r in self.records], [r.chunk_id for r in results])
        np.testing.assert_allclose([r.score for r in results], [1, 1, 0.6, 0, -1], atol=1e-6)
        self.assertEqual(list(range(1, 6)), [r.rank for r in results])
        for record, result in zip(self.records, results):
            self.assertEqual(record.metadata, result.metadata)
            self.assertEqual("dense", result.strategy)

    def test_ties_at_cutoff_and_repeated_builds_are_deterministic(self):
        for _ in range(3):
            index = self.build()
            self.assertEqual(self.records[0].chunk_id, index.search(self.query, 1)[0].chunk_id)
            self.assertEqual(index.search(self.query, 3), index.search(self.query * 2, 3))

    def test_persistence_reload_and_repeat_bytes(self):
        index = self.build()
        output = self.root / "index-unicode-ខ្មែរ"
        index.save(output)
        loaded = VectorIndex.load(output, self.clearance)
        self.assertEqual(index.search(self.query), loaded.search(self.query))
        loaded.save(self.root / "second")
        for name in ("index.faiss", "metadata.json", "manifest.json"):
            self.assertEqual((output / name).read_bytes(), (self.root / "second" / name).read_bytes())
        with self.assertRaises(FileExistsError):
            index.save(output)

    def test_invalid_query_and_k(self):
        index = self.build()
        for query in (np.zeros(384), np.ones(383), np.ones((1, 384)),
                      np.full(384, np.nan), np.full(384, np.inf)):
            with self.subTest(shape=query.shape), self.assertRaises(ValueError):
                index.search(query)
        for k in (0, -1, True, 1.5):
            with self.subTest(k=k), self.assertRaises(ValueError):
                index.search(self.query, k)

    def test_missing_or_revoked_clearance_fails_build_and_load(self):
        self.build().save(self.root / "index")
        with self.assertRaises(FileNotFoundError):
            VectorIndex.load(self.root / "index", self.root / "missing.json")
        clearance = json.loads(self.clearance.read_text())
        clearance["repositories"][0]["unresolved_findings"] = 1
        write_json(self.clearance, clearance)
        with self.assertRaises(ValueError):
            self.build()
        with self.assertRaises(ValueError):
            VectorIndex.load(self.root / "index", self.clearance)

    def test_changed_clearance_requires_new_artifacts(self):
        self.clearance.write_bytes(self.clearance.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "Clearance differs"):
            self.build()

    def test_snapshot_isolation(self):
        other = APPROVED_CORPUS[1]
        with self.assertRaisesRegex(ValueError, "no accepted"):
            VectorIndex.build(self.embeddings, self.clearance,
                              repository_id=other.repository_id, commit_sha=other.commit_sha)
        with self.assertRaises(ValueError):
            VectorIndex.build(self.embeddings, self.clearance,
                              repository_id=self.spec.repository_id, commit_sha="0" * 40)

    def test_combined_run_selects_and_remaps_only_requested_snapshot(self):
        other = APPROVED_CORPUS[1]
        original = self.records[0]
        meta = replace(original.metadata, repository_id=other.repository_id, commit_sha=other.commit_sha)
        identity = [meta.repository_id, meta.commit_sha, meta.file_path, meta.entity_type,
                    meta.qualified_name, meta.start_line, meta.end_line, meta.content_sha256]
        cid = digest(json.dumps(identity, ensure_ascii=True, separators=(",", ":")).encode())
        records = sorted((*self.records, replace(original, chunk_id=cid, metadata=meta)),
                         key=lambda r: r.chunk_id)
        self.embeddings = self.root / "combined"
        save_artifacts(self.embeddings, records, (), batch_size=32, input_count=6,
                       clearance_sha256=digest(self.clearance.read_bytes()))
        index = self.build()
        self.assertEqual(5, index.count)
        self.assertEqual([r.chunk_id for r in self.records], [r.chunk_id for r in index.search(self.query)])
        second = VectorIndex.build(self.embeddings, self.clearance,
                                   repository_id=other.repository_id, commit_sha=other.commit_sha)
        self.assertEqual(1, second.count)
        self.assertEqual(cid, second.search(self.query)[0].chunk_id)

    def test_empty_artifacts_fail_explicitly(self):
        self.embeddings = self.root / "empty"
        save_artifacts(self.embeddings, (), (), batch_size=32, input_count=0,
                       clearance_sha256=digest(self.clearance.read_bytes()))
        with self.assertRaisesRegex(ValueError, "no accepted"):
            self.build()

    def test_invalid_index_vectors_and_runtime_are_rejected(self):
        output = self.root / "index"
        self.build().save(output)
        wrong = faiss.IndexFlatIP(384)
        wrong.add(np.asarray([r.vector for r in self.records], dtype=np.float32) * 2)
        (output / "index.faiss").write_bytes(faiss.serialize_index(wrong).tobytes())
        self.refresh_hash(output, "index.faiss")
        with self.assertRaisesRegex(ValueError, "normalized"):
            VectorIndex.load(output, self.clearance)
        manifest = json.loads((output / "manifest.json").read_text())
        manifest["packages"]["faiss-cpu"] = "different"
        write_json(output / "manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "runtime"):
            VectorIndex.load(output, self.clearance)

    def test_corruption_rejected_before_faiss_deserialization(self):
        output = self.root / "index"
        self.build().save(output)
        (output / "index.faiss").write_bytes(b"broken")
        with patch("src.retrieval.vector_index.faiss.deserialize_index") as reader:
            with self.assertRaisesRegex(ValueError, "integrity"):
                VectorIndex.load(output, self.clearance)
            reader.assert_not_called()

    def test_tampered_metadata_identity_even_with_updated_checksum(self):
        output = self.root / "index"
        self.build().save(output)
        rows = json.loads((output / "metadata.json").read_text())
        rows[0]["metadata"]["qualified_name"] = "incorrect"
        write_json(output / "metadata.json", rows)
        self.refresh_hash(output, "metadata.json")
        with self.assertRaisesRegex(ValueError, "identity"):
            VectorIndex.load(output, self.clearance)

    def test_wrong_index_type_even_with_updated_checksum(self):
        output = self.root / "index"
        self.build().save(output)
        wrong = faiss.IndexFlatL2(384)
        wrong.add(np.asarray([r.vector for r in self.records], dtype=np.float32))
        (output / "index.faiss").write_bytes(faiss.serialize_index(wrong).tobytes())
        self.refresh_hash(output, "index.faiss")
        with self.assertRaisesRegex(ValueError, "contract mismatch"):
            VectorIndex.load(output, self.clearance)

    @staticmethod
    def refresh_hash(output, name):
        manifest = json.loads((output / "manifest.json").read_text())
        manifest["artifacts"][name] = digest((output / name).read_bytes())
        write_json(output / "manifest.json", manifest)

    def test_embedding_contract_and_integrity_are_checked(self):
        path = self.embeddings / "run.json"
        manifest = json.loads(path.read_text())
        manifest["representation"] = "different"
        write_json(path, manifest)
        with self.assertRaisesRegex(ValueError, "contract"):
            self.build()
        manifest["representation"] = "source-strip-v1"
        write_json(path, manifest)
        (self.embeddings / "vectors.npy").write_bytes(b"broken")
        with self.assertRaisesRegex(ValueError, "integrity"):
            self.build()

    def test_local_only_and_external_storage(self):
        with patch.object(socket.socket, "connect", side_effect=AssertionError("Network prohibited")):
            index = self.build()
            index.save(self.root / "offline")
            self.assertEqual(index.search(self.query),
                             VectorIndex.load(self.root / "offline", self.clearance).search(self.query))
        with self.assertRaises(ValueError):
            index.save(PROJECT_ROOT / "indexes")


if __name__ == "__main__":
    unittest.main()
