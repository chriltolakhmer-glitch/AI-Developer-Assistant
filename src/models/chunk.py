"""Immutable, provenance-aware semantic code chunks."""

from dataclasses import dataclass
from typing import Literal


ChunkEntityType = Literal["module", "class", "function", "method"]


@dataclass(frozen=True, slots=True)
class CodeChunk:
    """One deterministic source range associated with a parsed code entity."""

    chunk_id: str
    repository_id: str
    commit_sha: str
    file_path: str
    entity_type: ChunkEntityType
    qualified_name: str
    start_line: int
    end_line: int
    content: str