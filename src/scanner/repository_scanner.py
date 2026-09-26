"""Build deterministic manifests from locally available Git commit objects."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

from src.models.corpus import CorpusManifest, FileMetadata, RepositoryMetadata


IGNORED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "site-packages",
        "build",
        "dist",
        "vendor",
        "vendors",
        "third_party",
        "generated",
        "fixtures",
        "testdata",
    }
)
_FULL_SHA1_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")


class ScannerError(RuntimeError):
    """Raised when a local repository cannot be scanned safely."""


class CommitMismatchError(ScannerError):
    """Raised when HEAD does not match the required pinned commit SHA."""


class RepositoryScanner:
    """Scan tracked Python files from an already-present, pinned Git snapshot.

    The scanner never clones, fetches, checks out, or writes inside the source
    repository. File content is read from Git's local object database so hashes
    and LOC do not vary with working-tree line-ending conversion.
    """

    def scan(
        self,
        repository_path: str | Path,
        expected_commit_sha: str,
        repository_id: str | None = None,
        repository_url: str | None = None,
    ) -> CorpusManifest:
        """Scan a local repository after verifying its full expected SHA."""
        root = Path(repository_path).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ScannerError(f"Repository path is not a directory: {root}")
        if not _FULL_SHA1_PATTERN.fullmatch(expected_commit_sha):
            raise ScannerError("expected_commit_sha must be a full 40-character SHA-1")

        git_root_bytes = self._git(root, ["rev-parse", "--show-toplevel"])
        git_root = Path(os.fsdecode(git_root_bytes).strip()).resolve(strict=True)
        if git_root != root:
            raise ScannerError("repository_path must be the Git working-tree root")

        actual_sha = os.fsdecode(
            self._git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
        ).strip().lower()
        expected_sha = expected_commit_sha.lower()
        if actual_sha != expected_sha:
            raise CommitMismatchError(
                f"Pinned commit mismatch: expected {expected_sha}, found {actual_sha}"
            )

        tree_records = self._git(root, ["ls-tree", "-r", "-z", "--full-tree", "HEAD"])
        candidates: list[tuple[str, str, str, str | None]] = []
        eligible_object_ids: list[str] = []

        for record in tree_records.split(b"\0"):
            if not record:
                continue
            header, separator, path_bytes = record.partition(b"\t")
            fields = header.split()
            if not separator or len(fields) != 3:
                raise ScannerError("Git returned a malformed tree entry")

            mode, object_type, object_id = (os.fsdecode(field) for field in fields)
            relative_path = os.fsdecode(path_bytes)
            if not relative_path.endswith(".py"):
                continue

            exclusion_reason = self._path_exclusion_reason(relative_path)
            if exclusion_reason is None and mode == "120000":
                exclusion_reason = "symbolic link"
            if exclusion_reason is None and (object_type != "blob" or mode not in {"100644", "100755"}):
                exclusion_reason = "not a regular tracked file"

            candidates.append((relative_path, mode, object_id, exclusion_reason))
            if exclusion_reason is None:
                eligible_object_ids.append(object_id)

        blob_contents = self._read_blobs(root, eligible_object_ids)
        files: list[FileMetadata] = []
        for relative_path, _mode, object_id, exclusion_reason in candidates:
            if exclusion_reason is not None:
                files.append(
                    FileMetadata(
                        relative_path=relative_path,
                        language="python",
                        included=False,
                        exclusion_reason=exclusion_reason,
                    )
                )
                continue

            content = blob_contents[object_id]
            files.append(
                FileMetadata(
                    relative_path=relative_path,
                    language="python",
                    included=True,
                    sha256=hashlib.sha256(content).hexdigest(),
                    size_bytes=len(content),
                    loc=self._count_loc(content),
                )
            )

        files.sort(key=lambda file: file.relative_path)
        return CorpusManifest(
            repository=RepositoryMetadata(
                repository_id=repository_id or root.name,
                commit_sha=actual_sha,
                repository_url=repository_url,
            ),
            files=tuple(files),
        )

    def scan_to_file(
        self,
        repository_path: str | Path,
        output_path: str | Path,
        expected_commit_sha: str,
        repository_id: str | None = None,
        repository_url: str | None = None,
    ) -> CorpusManifest:
        """Scan and write JSON outside the source repository.

        Keeping the output outside the checkout prevents accidental corpus data
        from being added to this research repository or changing the scanned tree.
        """
        root = Path(repository_path).expanduser().resolve(strict=True)
        destination = Path(output_path).expanduser().resolve(strict=False)
        if destination == root or destination.is_relative_to(root):
            raise ScannerError("manifest output must be outside the source repository")

        manifest = self.scan(
            root,
            expected_commit_sha,
            repository_id=repository_id,
            repository_url=repository_url,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(manifest.to_json(), encoding="utf-8", newline="\n")
        return manifest

    @staticmethod
    def _path_exclusion_reason(relative_path: str) -> str | None:
        path = PurePosixPath(relative_path)
        for component in path.parts[:-1]:
            if component in IGNORED_DIRECTORY_NAMES:
                return f"excluded directory: {component}"
        if path.name.endswith("_pb2.py"):
            return "generated protobuf file (*_pb2.py)"
        return None

    @staticmethod
    def _count_loc(content: bytes) -> int:
        """Count non-empty physical lines not beginning with a comment marker."""
        return sum(
            1
            for line in content.splitlines()
            if (stripped := line.strip()) and not stripped.startswith(b"#")
        )

    @classmethod
    def _read_blobs(cls, root: Path, object_ids: list[str]) -> dict[str, bytes]:
        unique_ids = list(dict.fromkeys(object_ids))
        if not unique_ids:
            return {}

        response = cls._git(
            root,
            ["cat-file", "--batch"],
            input_data=("\n".join(unique_ids) + "\n").encode("ascii"),
        )
        blobs: dict[str, bytes] = {}
        offset = 0
        for requested_id in unique_ids:
            header_end = response.find(b"\n", offset)
            if header_end < 0:
                raise ScannerError("Git returned an incomplete blob header")
            header = response[offset:header_end].split()
            if len(header) != 3 or header[1] != b"blob":
                raise ScannerError(f"Git object {requested_id} is not a blob")
            returned_id = os.fsdecode(header[0])
            try:
                size = int(header[2])
            except ValueError as error:
                raise ScannerError("Git returned an invalid blob size") from error
            if returned_id != requested_id or size < 0:
                raise ScannerError("Git returned an unexpected blob object")

            content_start = header_end + 1
            content_end = content_start + size
            if content_end >= len(response) or response[content_end : content_end + 1] != b"\n":
                raise ScannerError("Git returned an incomplete blob body")
            blobs[requested_id] = response[content_start:content_end]
            offset = content_end + 1
        if offset != len(response):
            raise ScannerError("Git returned unexpected data after the blob batch")
        return blobs

    @staticmethod
    def _git(
        root: Path,
        arguments: list[str],
        input_data: bytes | None = None,
    ) -> bytes:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            message = os.fsdecode(result.stderr).strip() or "unknown Git error"
            raise ScannerError(f"Git command failed: {message}")
        return result.stdout