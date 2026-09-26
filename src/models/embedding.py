"""Versioned source-free embedding records."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmbeddingMetadata:
    repository_id: str
    commit_sha: str
    file_path: str
    entity_type: str
    qualified_name: str
    start_line: int
    end_line: int
    content_sha256: str
    token_count: int


@dataclass(frozen=True, slots=True)
class Embedding:
    chunk_id: str
    vector: tuple[float, ...]
    metadata: EmbeddingMetadata
