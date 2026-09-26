"""Generate deterministic source chunks from parsed Python entities."""

from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath, PureWindowsPath
import re

from src.models.chunk import ChunkEntityType, CodeChunk
from src.models.code_entity import Module
from src.models.corpus import RepositoryMetadata


_FULL_SHA1_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")


class ChunkingError(ValueError):
    """Raised when entity ranges or provenance cannot be validated."""


class CodeChunker:
    """Create module, class, function, and method chunks from one parsed module.

    Chunk content is sliced from the exact source text supplied alongside the
    AST result. The chunker never opens or writes source files itself.
    """

    def chunk_module(
        self,
        module: Module,
        source: str,
        repository: RepositoryMetadata,
    ) -> tuple[CodeChunk, ...]:
        """Return a stable module-first sequence of provenance-aware chunks."""
        if not repository.repository_id.strip():
            raise ChunkingError("repository_id must not be empty")
        if not _FULL_SHA1_PATTERN.fullmatch(repository.commit_sha):
            raise ChunkingError("commit_sha must be a full 40-character SHA-1")
        file_path = self._validate_relative_path(module.relative_path)

        lines = source.splitlines(keepends=True)
        line_count = len(source.splitlines())
        if line_count != module.end_line:
            raise ChunkingError(
                "source line count does not match the parsed module; parse and chunk the same source"
            )

        chunks = [
            self._make_chunk(
                repository=repository,
                commit_sha=repository.commit_sha.lower(),
                file_path=file_path,
                entity_type="module",
                qualified_name=module.name,
                start_line=module.start_line,
                end_line=module.end_line,
                lines=lines,
            )
        ]

        entities: list[tuple[ChunkEntityType, str, int, int]] = []
        entities.extend(
            ("class", entity.qualified_name, entity.start_line, entity.end_line)
            for entity in module.classes
        )
        entities.extend(
            (entity.kind, entity.qualified_name, entity.start_line, entity.end_line)
            for entity in module.functions
        )
        entities.sort(key=lambda entity: (entity[2], entity[3], entity[0], entity[1]))

        for entity_type, qualified_name, start_line, end_line in entities:
            chunks.append(
                self._make_chunk(
                    repository=repository,
                    commit_sha=repository.commit_sha.lower(),
                    file_path=file_path,
                    entity_type=entity_type,
                    qualified_name=qualified_name,
                    start_line=start_line,
                    end_line=end_line,
                    lines=lines,
                )
            )
        return tuple(chunks)

    @classmethod
    def _make_chunk(
        cls,
        repository: RepositoryMetadata,
        commit_sha: str,
        file_path: str,
        entity_type: ChunkEntityType,
        qualified_name: str,
        start_line: int,
        end_line: int,
        lines: list[str],
    ) -> CodeChunk:
        if start_line < 1 or end_line < start_line - 1 or end_line > len(lines):
            raise ChunkingError(
                f"invalid source range for {qualified_name}: {start_line}-{end_line}"
            )
        if end_line == start_line - 1 and not (entity_type == "module" and not lines):
            raise ChunkingError(f"empty source range is only valid for an empty module: {qualified_name}")

        content = "".join(lines[start_line - 1 : end_line])
        content_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        identity = json.dumps(
            [
                repository.repository_id,
                commit_sha,
                file_path,
                entity_type,
                qualified_name,
                start_line,
                end_line,
                content_sha,
            ],
            ensure_ascii=True,
            separators=(",", ":"),
        )
        chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        return CodeChunk(
            chunk_id=chunk_id,
            repository_id=repository.repository_id,
            commit_sha=commit_sha,
            file_path=file_path,
            entity_type=entity_type,
            qualified_name=qualified_name,
            start_line=start_line,
            end_line=end_line,
            content=content,
        )

    @staticmethod
    def _validate_relative_path(file_path: str) -> str:
        normalized = file_path.replace("\\", "/")
        posix_path = PurePosixPath(normalized)
        windows_path = PureWindowsPath(file_path)
        if (
            not normalized
            or normalized.endswith("/")
            or not posix_path.parts
            or posix_path.is_absolute()
            or windows_path.is_absolute()
            or windows_path.drive
            or ".." in posix_path.parts
        ):
            raise ChunkingError("file_path must be a repository-relative path")
        return posix_path.as_posix()