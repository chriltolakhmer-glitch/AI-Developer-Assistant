"""Shared immutable dense and lexical search results."""

from dataclasses import dataclass

from .embedding import EmbeddingMetadata


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Keep the original result shape and expose convenient provenance fields.

    metadata.token_count is the embedding tokenizer count, not BM25 length.
    """

    chunk_id: str
    rank: int
    score: float
    metadata: EmbeddingMetadata
    strategy: str = "dense"

    @property
    def repository_id(self) -> str:
        return self.metadata.repository_id

    @property
    def commit_sha(self) -> str:
        return self.metadata.commit_sha

    @property
    def file_path(self) -> str:
        return self.metadata.file_path

    @property
    def entity_type(self) -> str:
        return self.metadata.entity_type

    @property
    def qualified_name(self) -> str:
        return self.metadata.qualified_name

    @property
    def start_line(self) -> int:
        return self.metadata.start_line

    @property
    def end_line(self) -> int:
        return self.metadata.end_line

    @property
    def line_range(self) -> tuple[int, int]:
        return self.start_line, self.end_line


RetrievalResult = SearchResult
