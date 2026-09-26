"""Validate scanner → parser → chunker over approved pinned repositories."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
import platform
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tokenize
from typing import Any

from src.chunker import CodeChunker
from src.models.code_entity import Module
from src.parser import ParserError, PythonAstParser
from src.scanner import CommitMismatchError, RepositoryScanner, ScannerError


@dataclass(frozen=True, slots=True)
class RepositorySpec:
    """Approved identity and Phase 4.5 screening baseline for a repository."""

    repository_id: str
    checkout_name: str
    commit_sha: str
    expected_python_file_count: int
    expected_python_loc: int


APPROVED_CORPUS = (
    RepositorySpec("theskumar/python-dotenv", "python-dotenv", "a00cb2eed0704cd6d2071b2004c37e95ccc86ee5", 20, 2776),
    RepositorySpec("python-humanize/humanize", "humanize", "392aef707c0e74341ab4a51420984e9ea6b566c5", 13, 2915),
    RepositorySpec("python-validators/validators", "validators", "70de324322def13a49a93d222f798ec1ab700885", 64, 4353),
    RepositorySpec("pallets/flask", "flask", "d73fa1cdcbd8b1465c151db8924ba58b1dd14e35", 83, 13301),
    RepositorySpec("encode/httpx", "httpx", "b5addb64f0161ff6bfe94c124ef76f6a1fba5254", 60, 13800),
    RepositorySpec("Textualize/rich", "rich", "9d8f9a372cc5916fd4781fec207ced7ddac2f08f", 213, 45223),
    RepositorySpec("pytest-dev/pytest", "pytest", "8721173580390a9d297e5af06cac3f0b6841f425", 245, 93998),
    RepositorySpec("python/mypy", "mypy", "0861bb6450d6d3658e44dbca9cd2ba478faf3c1d", 444, 144316),
    RepositorySpec("sphinx-doc/sphinx", "sphinx", "b04a2101295ac3fb725b16111eda0284b6da4cca", 774, 118987),
)


@dataclass(frozen=True, slots=True)
class RepositoryValidationResult:
    repository_id: str
    expected_commit_sha: str
    verified_commit_sha: str | None
    status: str
    issue_codes: tuple[str, ...]
    python_file_count: int | None
    expected_python_file_count: int
    eligible_python_loc: int | None
    expected_python_loc: int
    source_read_failure_count: int | None
    parse_success_count: int | None
    parse_failure_count: int | None
    module_count: int | None
    class_count: int | None
    function_count: int | None
    method_count: int | None
    chunk_count: int | None
    chunk_failure_count: int | None
    deterministic: bool | None
    chunk_size_statistics: dict[str, dict[str, int | float | None]] | None


@dataclass(frozen=True, slots=True)
class PipelineValidationReport:
    schema_version: str
    python_version: str
    expected_repository_count: int
    validated_repository_count: int
    preprocessing_ready: bool
    embedding_readiness: str
    repositories: tuple[RepositoryValidationResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    def to_markdown(self) -> str:
        rows = [
            "# Pipeline Validation — Phase 5.4",
            "",
            f"- Python version: `{self.python_version}`",
            f"- Approved repositories: {self.expected_repository_count}",
            f"- Repositories validated at the expected SHA: {self.validated_repository_count}",
            f"- Preprocessing readiness: **{'PASS' if self.preprocessing_ready else 'BLOCKED'}**",
            f"- Embedding readiness: **{self.embedding_readiness}**",
            "",
            "| Repository | Commit | Status | Python files (actual / expected) | Parse success / failure | Read failures | Modules | Classes | Functions | Methods | Chunks | Chunk failures | Chunk chars (p50 / p95 / max) | Issues |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
        for result in self.repositories:
            sizes = result.chunk_size_statistics
            chars = sizes["characters"] if sizes else None
            p50_p95_max = (
                f"{chars['p50']} / {chars['p95']} / {chars['max']}"
                if chars
                else "—"
            )
            files = self._pair(result.python_file_count, result.expected_python_file_count)
            parsed = self._pair(result.parse_success_count, result.parse_failure_count)
            values = (
                result.repository_id,
                result.verified_commit_sha or result.expected_commit_sha,
                result.status,
                files,
                parsed,
                self._display(result.source_read_failure_count),
                self._display(result.module_count),
                self._display(result.class_count),
                self._display(result.function_count),
                self._display(result.method_count),
                self._display(result.chunk_count),
                self._display(result.chunk_failure_count),
                p50_p95_max,
                ", ".join(result.issue_codes) or "—",
            )
            rows.append("| " + " | ".join(values) + " |")
        rows.extend(
            [
                "",
                "Reports contain aggregate metadata only; no source text, per-file paths, or checkout paths are written.",
                "The runner does not perform the required secret/privacy audit. Embedding remains blocked until that gate is independently completed and documented.",
                "",
            ]
        )
        return "\n".join(rows)

    @staticmethod
    def _display(value: int | None) -> str:
        return str(value) if value is not None else "—"

    @classmethod
    def _pair(cls, actual: int | None, expected: int | None) -> str:
        return f"{cls._display(actual)} / {cls._display(expected)}"


class PipelineValidationRunner:
    """Run offline preprocessing validation and write aggregate reports externally."""

    def __init__(self) -> None:
        self.scanner = RepositoryScanner()
        self.parser = PythonAstParser()
        self.chunker = CodeChunker()
        self.project_root = Path(__file__).resolve().parents[2]

    def run(
        self,
        corpus_root: str | Path,
        output_directory: str | Path,
        repositories: tuple[RepositorySpec, ...] = APPROVED_CORPUS,
    ) -> PipelineValidationReport:
        root = Path(corpus_root).expanduser().resolve(strict=False)
        output = Path(output_directory).expanduser().resolve(strict=False)
        self._ensure_external_output(output)

        results = tuple(
            self._validate_repository(root / spec.checkout_name, spec, output)
            for spec in repositories
        )
        fully_reconciled = all(
            result.status == "validated"
            and result.python_file_count == result.expected_python_file_count
            and result.eligible_python_loc == result.expected_python_loc
            and result.parse_success_count == result.python_file_count
            and result.parse_failure_count == 0
            and result.source_read_failure_count == 0
            and result.chunk_failure_count == 0
            and result.deterministic is True
            for result in results
        ) and len(results) == len(APPROVED_CORPUS)

        report = PipelineValidationReport(
            schema_version="1.0",
            python_version=platform.python_version(),
            expected_repository_count=len(APPROVED_CORPUS),
            validated_repository_count=sum(
                result.verified_commit_sha == result.expected_commit_sha
                for result in results
            ),
            preprocessing_ready=fully_reconciled,
            embedding_readiness="blocked_pending_privacy_audit",
            repositories=results,
        )
        output.mkdir(parents=True, exist_ok=True)
        (output / "pipeline-validation.json").write_text(
            report.to_json(), encoding="utf-8", newline="\n"
        )
        (output / "pipeline-validation.md").write_text(
            report.to_markdown(), encoding="utf-8", newline="\n"
        )
        return report

    def _validate_repository(
        self,
        repository_path: Path,
        spec: RepositorySpec,
        output_directory: Path,
    ) -> RepositoryValidationResult:
        base = self._empty_result(spec, "missing_checkout", ("missing_checkout",))
        if not repository_path.is_dir():
            return base
        if output_directory == repository_path.resolve() or output_directory.is_relative_to(
            repository_path.resolve()
        ):
            raise ValueError("report output must be outside every corpus checkout")

        try:
            manifest = self.scanner.scan(
                repository_path,
                expected_commit_sha=spec.commit_sha,
                repository_id=spec.repository_id,
            )
        except CommitMismatchError:
            return self._empty_result(spec, "commit_mismatch", ("commit_mismatch",))
        except ScannerError:
            return self._empty_result(spec, "scanner_error", ("scanner_error",))

        if self._has_tracked_changes(repository_path):
            return self._empty_result(
                spec,
                "dirty_worktree",
                ("dirty_worktree",),
                verified_commit_sha=manifest.repository.commit_sha,
                python_file_count=manifest.eligible_python_file_count,
                eligible_python_loc=manifest.eligible_python_loc,
            )

        counts = {
            "source_read_failure_count": 0,
            "parse_success_count": 0,
            "parse_failure_count": 0,
            "module_count": 0,
            "class_count": 0,
            "function_count": 0,
            "method_count": 0,
            "chunk_count": 0,
            "chunk_failure_count": 0,
        }
        character_sizes: list[int] = []
        byte_sizes: list[int] = []
        deterministic = True
        files_by_path = {file.relative_path: file for file in manifest.files if file.included}

        for relative_path in sorted(files_by_path):
            source_path = repository_path.joinpath(*PurePosixPath(relative_path).parts)
            try:
                with tokenize.open(source_path) as source_file:
                    source = source_file.read()
            except (OSError, SyntaxError, UnicodeError):
                counts["source_read_failure_count"] += 1
                deterministic = False
                continue

            first_module, first_error = self._parse(source, relative_path)
            second_module, second_error = self._parse(source, relative_path)
            if first_error != second_error or (first_module is None) != (second_module is None):
                deterministic = False
            if first_module is None or second_module is None:
                counts["parse_failure_count"] += 1
                continue
            if first_module != second_module:
                deterministic = False

            counts["parse_success_count"] += 1
            counts["module_count"] += 1
            counts["class_count"] += len(first_module.classes)
            counts["function_count"] += sum(
                entity.kind == "function" for entity in first_module.functions
            )
            counts["method_count"] += sum(
                entity.kind == "method" for entity in first_module.functions
            )
            try:
                first_chunks = self.chunker.chunk_module(
                    first_module, source, manifest.repository
                )
                second_chunks = self.chunker.chunk_module(
                    second_module, source, manifest.repository
                )
            except (ValueError, UnicodeError):
                counts["chunk_failure_count"] += 1
                deterministic = False
                continue
            if first_chunks != second_chunks:
                deterministic = False

            counts["chunk_count"] += len(first_chunks)
            for chunk in first_chunks:
                character_sizes.append(len(chunk.content))
                byte_sizes.append(len(chunk.content.encode("utf-8")))

        issues: list[str] = []
        if manifest.eligible_python_file_count != spec.expected_python_file_count:
            issues.append("python_file_count_mismatch")
        if manifest.eligible_python_loc != spec.expected_python_loc:
            issues.append("eligible_python_loc_mismatch")
        if counts["parse_failure_count"]:
            issues.append("parse_failures_present")
        if counts["source_read_failure_count"]:
            issues.append("source_read_failures_present")
        if counts["chunk_failure_count"]:
            issues.append("chunk_failures_present")
        if not deterministic:
            issues.append("nondeterministic_or_unreadable_input")
        if self._has_tracked_changes(repository_path):
            issues.append("source_tree_changed_during_validation")

        status = "validated" if not issues else "validated_with_issues"
        return RepositoryValidationResult(
            repository_id=spec.repository_id,
            expected_commit_sha=spec.commit_sha,
            verified_commit_sha=manifest.repository.commit_sha,
            status=status,
            issue_codes=tuple(issues),
            python_file_count=manifest.eligible_python_file_count,
            expected_python_file_count=spec.expected_python_file_count,
            eligible_python_loc=manifest.eligible_python_loc,
            expected_python_loc=spec.expected_python_loc,
            source_read_failure_count=counts["source_read_failure_count"],
            parse_success_count=counts["parse_success_count"],
            parse_failure_count=counts["parse_failure_count"],
            module_count=counts["module_count"],
            class_count=counts["class_count"],
            function_count=counts["function_count"],
            method_count=counts["method_count"],
            chunk_count=counts["chunk_count"],
            chunk_failure_count=counts["chunk_failure_count"],
            deterministic=deterministic,
            chunk_size_statistics={
                "characters": self._size_statistics(character_sizes),
                "utf8_bytes": self._size_statistics(byte_sizes),
            },
        )

    def _parse(
        self,
        source: str,
        relative_path: str,
    ) -> tuple[Module | None, tuple[object, ...] | None]:
        try:
            return self.parser.parse(source, relative_path), None
        except ParserError as error:
            return None, ("syntax", error.line, error.column, error.message)
        except (ValueError, RecursionError) as error:
            return None, (type(error).__name__, str(error))

    @staticmethod
    def _has_tracked_changes(repository_path: Path) -> bool:
        result = subprocess.run(
            ["git", "-C", str(repository_path), "diff", "--quiet", "HEAD", "--"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode != 0

    def _ensure_external_output(self, output_directory: Path) -> None:
        if output_directory == self.project_root or output_directory.is_relative_to(
            self.project_root
        ):
            raise ValueError("validation reports must be written outside the source repository")

    @staticmethod
    def _empty_result(
        spec: RepositorySpec,
        status: str,
        issue_codes: tuple[str, ...],
        *,
        verified_commit_sha: str | None = None,
        python_file_count: int | None = None,
        eligible_python_loc: int | None = None,
    ) -> RepositoryValidationResult:
        return RepositoryValidationResult(
            repository_id=spec.repository_id,
            expected_commit_sha=spec.commit_sha,
            verified_commit_sha=verified_commit_sha,
            status=status,
            issue_codes=issue_codes,
            python_file_count=python_file_count,
            expected_python_file_count=spec.expected_python_file_count,
            eligible_python_loc=eligible_python_loc,
            expected_python_loc=spec.expected_python_loc,
            source_read_failure_count=None,
            parse_success_count=None,
            parse_failure_count=None,
            module_count=None,
            class_count=None,
            function_count=None,
            method_count=None,
            chunk_count=None,
            chunk_failure_count=None,
            deterministic=None,
            chunk_size_statistics=None,
        )

    @staticmethod
    def _size_statistics(values: list[int]) -> dict[str, int | float | None]:
        if not values:
            return {"count": 0, "min": None, "p50": None, "p95": None, "mean": None, "max": None}
        ordered = sorted(values)

        def nearest_rank(percentile: float) -> int:
            return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]

        return {
            "count": len(ordered),
            "min": ordered[0],
            "p50": nearest_rank(0.50),
            "p95": nearest_rank(0.95),
            "mean": round(sum(ordered) / len(ordered), 2),
            "max": ordered[-1],
        }


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-root",
        required=True,
        type=Path,
        help="Directory containing one local checkout per approved repository slug.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Existing or new report directory outside this Git repository and the checkouts.",
    )
    options = parser.parse_args(arguments)
    report = PipelineValidationRunner().run(options.corpus_root, options.output_dir)
    print(
        f"Pipeline report written; validated={report.validated_repository_count}/"
        f"{report.expected_repository_count}; preprocessing_ready={report.preprocessing_ready}; "
        f"embedding_readiness={report.embedding_readiness}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())