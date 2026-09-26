"""Deterministic data structures for repository scan manifests."""

from dataclasses import asdict, dataclass
import json


MANIFEST_SCHEMA_VERSION = "1.0"
FILE_FILTER_VERSION = "phase4.5-python-v1"


@dataclass(frozen=True, slots=True)
class RepositoryMetadata:
    """Stable identity of one scanned repository snapshot."""

    repository_id: str
    commit_sha: str
    repository_url: str | None = None


@dataclass(frozen=True, slots=True)
class FileMetadata:
    """Metadata for a tracked Python file, eligible or excluded."""

    relative_path: str
    language: str
    included: bool
    sha256: str | None = None
    size_bytes: int | None = None
    loc: int | None = None
    exclusion_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CorpusManifest:
    """A deterministic, source-text-free inventory of a repository snapshot."""

    repository: RepositoryMetadata
    files: tuple[FileMetadata, ...]

    @property
    def eligible_python_file_count(self) -> int:
        return sum(file.included for file in self.files)

    @property
    def eligible_python_loc(self) -> int:
        return sum(file.loc or 0 for file in self.files if file.included)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation with reproducible ordering."""
        return {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "file_filter_version": FILE_FILTER_VERSION,
            "repository": asdict(self.repository),
            "summary": {
                "eligible_python_file_count": self.eligible_python_file_count,
                "eligible_python_loc": self.eligible_python_loc,
                "tracked_python_file_count": len(self.files),
            },
            "files": [asdict(file) for file in self.files],
        }

    def to_json(self) -> str:
        """Serialize the manifest consistently, independent of checkout path."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"