"""Privacy-gated, ordered chunk-to-vector transformation."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import numpy as np

from src.chunker import CodeChunker
from src.evaluation.pipeline_validation import APPROVED_CORPUS
from src.models.chunk import CodeChunk
from src.models.embedding import Embedding, EmbeddingMetadata
from .model import DIMENSIONS, MAX_TOKENS, load_model, external_path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_vector_matrix(vectors, count: int) -> np.ndarray:
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.shape != (count, DIMENSIONS) or not np.isfinite(vectors).all():
        raise ValueError("Invalid embedding shape or non-finite values")
    norms = np.linalg.norm(vectors, axis=1)
    if not np.isfinite(norms).all() or np.any(norms <= 0):
        raise ValueError("Invalid embedding norms")
    return np.ascontiguousarray(vectors / norms[:, None], dtype=np.float32)


def validate_chunk(chunk: CodeChunk) -> str:
    content_hash = digest(chunk.content.encode("utf-8"))
    if (CodeChunker._validate_relative_path(chunk.file_path) != chunk.file_path
            or chunk.entity_type not in {"module", "class", "function", "method"}
            or not chunk.qualified_name or chunk.start_line < 1
            or chunk.end_line < chunk.start_line - 1
            or len(chunk.content.splitlines()) != chunk.end_line - chunk.start_line + 1):
        raise ValueError("Invalid chunk provenance")
    identity = [chunk.repository_id, chunk.commit_sha, chunk.file_path, chunk.entity_type,
                chunk.qualified_name, chunk.start_line, chunk.end_line, content_hash]
    expected = digest(json.dumps(identity, ensure_ascii=True, separators=(",", ":")).encode())
    if expected != chunk.chunk_id:
        raise ValueError("Chunk identity/content mismatch")
    return content_hash


def check_clearance(chunks, clearance):
    if not isinstance(clearance, dict) or clearance.get("schema_version") != "1.0":
        raise ValueError("Missing or invalid privacy clearance")
    if clearance.get("snapshot_id") != "corpus-snapshot-v1":
        raise ValueError("Invalid snapshot identity")
    approved = {(s.repository_id, s.commit_sha) for s in APPROVED_CORPUS}
    records = clearance.get("repositories", [])
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        raise ValueError("Invalid privacy clearance records")
    for identity in {(c.repository_id, c.commit_sha) for c in chunks}:
        matches = [r for r in records if (r.get("repository_id"), r.get("commit_sha")) == identity]
        if identity not in approved or len(matches) != 1:
            raise ValueError("Snapshot is not approved and uniquely cleared")
        record = matches[0]
        if (record.get("secret_review") != "passed" or record.get("privacy_review") != "passed"
                or type(record.get("unresolved_findings")) is not int
                or record.get("unresolved_findings") != 0
                or not all(isinstance(record.get(k), str) and record[k].strip()
                           for k in ("reviewer", "reviewed_at", "audit_record"))):
            raise ValueError("Privacy review is incomplete or unresolved")


class EmbeddingPipeline:
    def __init__(self, cache: Path, batch_size: int = 32):
        if type(batch_size) is not int or batch_size < 1:
            raise ValueError("batch_size must be a positive integer")
        self.cache = external_path(cache)
        self.batch_size = batch_size
        self._model = None

    def run(self, chunks: tuple[CodeChunk, ...], clearance_path: Path, output: Path):
        from .storage import save_artifacts
        external_path(output)
        clearance_bytes = external_path(clearance_path).read_bytes()
        check_clearance(chunks, json.loads(clearance_bytes))
        embeddings, rejections = self._generate_validated(chunks)
        return save_artifacts(output, embeddings, rejections, batch_size=self.batch_size,
                              input_count=len(chunks), clearance_sha256=digest(clearance_bytes),
                              input_manifest={
                                  "chunk_ids_sha256": digest(json.dumps(sorted(c.chunk_id for c in chunks)).encode()),
                                  "snapshots": [list(identity) for identity in sorted({
                                      (c.repository_id, c.commit_sha) for c in chunks})],
                              })

    def generate(self, chunks: tuple[CodeChunk, ...], clearance_path: Path):
        """Return embeddings and explicit length rejections; fail closed otherwise."""
        clearance_path = external_path(clearance_path)
        clearance = json.loads(clearance_path.read_text(encoding="utf-8"))
        check_clearance(chunks, clearance)
        return self._generate_validated(chunks)

    def _generate_validated(self, chunks):
        # Private shared core also exercised with generated, non-corpus fixtures.
        chunks = sorted(chunks, key=lambda c: c.chunk_id)
        if len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError("Duplicate chunk IDs")
        hashes = [validate_chunk(c) for c in chunks]
        if self._model is None:
            self._model = load_model(self.cache)
        accepted, rejected, texts = [], [], []
        for chunk, content_hash in zip(chunks, hashes):
            # SentenceTransformers strips outer whitespace before tokenization.
            text = chunk.content.strip()
            count = len(self._model.tokenizer(text, add_special_tokens=True,
                        truncation=False, padding=False, verbose=False)["input_ids"])
            if count > MAX_TOKENS or not text:
                rejected.append({"chunk_id": chunk.chunk_id, "parent_chunk_id": chunk.chunk_id,
                                 "token_count": count, "reason": "over_limit" if text else "empty"})
                continue
            metadata = asdict(chunk)
            metadata.pop("chunk_id")
            metadata.pop("content")
            accepted.append((chunk.chunk_id, EmbeddingMetadata(
                **metadata, content_sha256=content_hash, token_count=count)))
            texts.append(text)
        if not texts:
            return (), tuple(rejected)
        vectors = self._model.encode(texts, batch_size=self.batch_size,
                    show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=False)
        vectors = validate_vector_matrix(vectors, len(texts))
        return tuple(Embedding(cid, tuple(float(v) for v in vector), meta)
                     for (cid, meta), vector in zip(accepted, vectors)), tuple(rejected)
