"""Exact cosine retrieval with deterministic ties and immutable provenance."""

from dataclasses import asdict
from importlib.metadata import version
import json
from pathlib import Path
import platform

import faiss
import numpy as np

from src.embedding.model import DIMENSIONS, external_path
from src.embedding.pipeline import digest, validate_vector_matrix
from src.embedding.storage import load_artifacts, write_json
from src.models.retrieval_result import SearchResult
from .embedding_artifacts import _contract, _clearance, _metadata


class VectorIndex:
    """Build from validated embedding artifacts; query with a compatible vector.

    Public build/load operations require the embedding run's local clearance.
    No query text, embedding service, or corpus checkout is opened here.
    """

    @classmethod
    def build(cls, embedding_directory: Path, clearance_path: Path, *,
              repository_id: str, commit_sha: str):
        directory = external_path(embedding_directory)
        run_bytes = (directory / "run.json").read_bytes()
        manifest = json.loads(run_bytes)
        _contract(manifest)
        _clearance(clearance_path, manifest["clearance_sha256"], repository_id, commit_sha)
        vectors, rows, verified_manifest = load_artifacts(directory)
        if verified_manifest != manifest:
            raise ValueError("Embedding manifest changed while loading")
        positions = [i for i, row in enumerate(rows)
                     if (row["metadata"]["repository_id"], row["metadata"]["commit_sha"])
                     == (repository_id, commit_sha)]
        if not positions:
            raise ValueError("Snapshot has no accepted embeddings")
        selected = [{**rows[i], "row": j} for j, i in enumerate(positions)]
        instance = cls._create(vectors[positions], selected, repository_id, commit_sha)
        instance._embedding_run = manifest
        instance._embedding_run_sha256 = digest(run_bytes)
        return instance

    @classmethod
    def _create(cls, vectors, rows, repository_id, commit_sha):
        ids, metadata = _metadata(rows, repository_id, commit_sha)
        vectors = np.asarray(vectors)
        validate_vector_matrix(vectors, len(ids))
        if vectors.dtype != np.float32 or not np.allclose(
                np.linalg.norm(vectors, axis=1), 1, rtol=0, atol=1e-6):
            raise ValueError("Index vectors must be normalized float32")
        faiss.omp_set_num_threads(1)
        instance = cls()
        instance._index = faiss.IndexFlatIP(DIMENSIONS)
        instance._index.add(np.ascontiguousarray(vectors))
        instance._ids, instance._metadata = ids, metadata
        instance._repository_id, instance._commit_sha = repository_id, commit_sha
        return instance

    @property
    def repository_id(self):
        return self._repository_id

    @property
    def commit_sha(self):
        return self._commit_sha

    @property
    def count(self):
        return len(self._ids)

    def search(self, query_vector, k: int = 50) -> tuple[SearchResult, ...]:
        if type(k) is not int or k < 1:
            raise ValueError("k must be a positive integer")
        query = np.asarray(query_vector, dtype=np.float32)
        if query.shape != (DIMENSIONS,):
            raise ValueError("Query must be one 384-dimensional vector")
        query = validate_vector_matrix(query[None, :], 1)
        if not self.count:
            return ()
        faiss.omp_set_num_threads(1)
        # A top-k FAISS heap can discard tied rows arbitrarily at its boundary.
        # Score the full exact index, then impose the total order before slicing.
        scores, positions = self._index.search(query, self.count)
        if not np.isfinite(scores).all():
            raise ValueError("Non-finite retrieval scores")
        candidates = sorted(zip(scores[0], positions[0]),
                            key=lambda item: (-float(item[0]), self._ids[int(item[1])]))
        return tuple(SearchResult(self._ids[int(row)], rank, float(score), self._metadata[int(row)])
                     for rank, (score, row) in enumerate(candidates[:k], start=1))

    def save(self, output: Path):
        output = external_path(output)
        output.mkdir(parents=True, exist_ok=False)
        # Serialize to bytes to support Unicode Windows paths without native I/O.
        (output / "index.faiss").write_bytes(faiss.serialize_index(self._index).tobytes())
        write_json(output / "metadata.json", [
            {"row": i, "chunk_id": cid, "metadata": asdict(meta)}
            for i, (cid, meta) in enumerate(zip(self._ids, self._metadata))])
        manifest = {
            "schema_version": "1.0", "index_type": "IndexFlatIP", "metric": "cosine",
            "dimensions": DIMENSIONS, "count": self.count,
            "repository_id": self.repository_id, "commit_sha": self.commit_sha,
            "tie_policy": "score-desc-chunk-id-asc-v1", "device": "cpu", "threads": 1,
            "python": platform.python_version(), "os": platform.platform(),
            "packages": {p: version(p) for p in ("faiss-cpu", "numpy")},
            "embedding_run": self._embedding_run,
            "embedding_run_sha256": self._embedding_run_sha256,
            "artifacts": {name: digest((output / name).read_bytes())
                          for name in ("index.faiss", "metadata.json")},
        }
        write_json(output / "manifest.json", manifest)

    @classmethod
    def load(cls, directory: Path, clearance_path: Path):
        directory = external_path(directory)
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if (manifest["schema_version"] != "1.0" or manifest["index_type"] != "IndexFlatIP"
                or manifest["metric"] != "cosine" or manifest["dimensions"] != DIMENSIONS
                or manifest["tie_policy"] != "score-desc-chunk-id-asc-v1"
                or manifest["packages"] != {p: version(p) for p in ("faiss-cpu", "numpy")}):
            raise ValueError("Unsupported index contract or runtime; rebuild the index")
        run = manifest["embedding_run"]
        _contract(run)
        _clearance(clearance_path, run["clearance_sha256"], manifest["repository_id"], manifest["commit_sha"])
        payloads = {name: (directory / name).read_bytes() for name in ("index.faiss", "metadata.json")}
        for name, data in payloads.items():
            if digest(data) != manifest["artifacts"][name]:
                raise ValueError("Index artifact integrity mismatch")
        # Only deserialize trusted local artifacts after integrity checking.
        index = faiss.deserialize_index(np.frombuffer(payloads["index.faiss"], dtype=np.uint8).copy())
        rows = json.loads(payloads["metadata.json"])
        if (type(index) is not faiss.IndexFlatIP or index.d != DIMENSIONS
                or index.metric_type != faiss.METRIC_INNER_PRODUCT
                or index.ntotal < 1 or index.ntotal != len(rows) or index.ntotal != manifest["count"]):
            raise ValueError("Index and metadata contract mismatch")
        instance = cls._create(index.reconstruct_n(0, index.ntotal), rows,
                               manifest["repository_id"], manifest["commit_sha"])
        instance._index = index
        instance._embedding_run = run
        instance._embedding_run_sha256 = manifest["embedding_run_sha256"]
        return instance
