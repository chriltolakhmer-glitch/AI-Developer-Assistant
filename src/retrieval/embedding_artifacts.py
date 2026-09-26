"""Shared validation of approved embedding inventories and provenance."""

import json
import re

from src.chunker import CodeChunker
from src.embedding.model import DIMENSIONS, MODEL_ID, MODEL_REVISION, external_path
from src.embedding.pipeline import check_clearance, digest
from src.models.corpus import RepositoryMetadata
from src.models.embedding import EmbeddingMetadata


def _contract(manifest):
    expected = {"schema_version": "1.0", "model": MODEL_ID, "revision": MODEL_REVISION,
                "dimensions": DIMENSIONS, "dtype": "float32", "normalization": "l2",
                "representation": "source-strip-v1", "input_policy": "reject-empty-or-over-256-v1",
                "snapshot_id": "corpus-snapshot-v1", "max_tokens": 256,
                "chunk_schema": "phase5.3", "device": "cpu"}
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("Unsupported embedding contract")


def _clearance(path, expected_hash, repository_id, commit_sha):
    raw = external_path(path).read_bytes()
    check_clearance((RepositoryMetadata(repository_id, commit_sha),), json.loads(raw))
    if digest(raw) != expected_hash:
        raise ValueError("Clearance differs from embedding run; regenerate approved artifacts")


def _metadata(rows, repository_id, commit_sha):
    """Validate and freeze the complete row-to-chunk mapping."""
    ids, records = [], []
    for position, row in enumerate(rows):
        if row["row"] != position:
            raise ValueError("Invalid vector row mapping")
        meta = EmbeddingMetadata(**row["metadata"])
        if ((meta.repository_id, meta.commit_sha) != (repository_id, commit_sha)
                or CodeChunker._validate_relative_path(meta.file_path) != meta.file_path
                or meta.entity_type not in {"module", "class", "function", "method"}
                or not isinstance(meta.qualified_name, str) or not meta.qualified_name.strip()
                or type(meta.start_line) is not int or type(meta.end_line) is not int
                or meta.start_line < 1 or meta.end_line < meta.start_line
                or type(meta.token_count) is not int or not 1 <= meta.token_count <= 256
                or not re.fullmatch(r"[0-9a-f]{64}", meta.content_sha256)):
            raise ValueError("Invalid chunk provenance")
        identity = [meta.repository_id, meta.commit_sha, meta.file_path, meta.entity_type,
                    meta.qualified_name, meta.start_line, meta.end_line, meta.content_sha256]
        expected = digest(json.dumps(identity, ensure_ascii=True, separators=(",", ":")).encode())
        if row["chunk_id"] != expected:
            raise ValueError("Chunk identity does not match provenance")
        ids.append(row["chunk_id"])
        records.append(meta)
    if ids != sorted(set(ids)):
        raise ValueError("Chunk IDs must be unique and sorted")
    return tuple(ids), tuple(records)
