"""Validate frozen benchmark cases against a pinned chunk inventory."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re

from src.models.chunk import CodeChunk
from .benchmark import Benchmark, BenchmarkCase


_FULL_SHA1_PATTERN = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
_QUERY_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*-\d{3}$")
_ALLOWED_RELEVANCE_GRADES = frozenset({1, 2})


@dataclass(frozen=True, slots=True)
class BenchmarkValidationReport:
    """Aggregate, source-free outcome of benchmark validation."""

    schema_version: str | None
    case_count: int
    validated_case_count: int
    inventory_chunk_count: int
    issues: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


class BenchmarkValidator:
    """Check query, gold-label, chunk-inventory, and snapshot contracts.

    Relevance grades are frozen as 2 for primary evidence and 1 for supporting
    evidence. The supplied inventory should be the exact deterministic chunk
    inventory generated for the expected repository snapshots.
    """

    def validate(
        self,
        benchmark: Benchmark,
        chunks: Iterable[CodeChunk],
        expected_snapshots: Mapping[str, str],
    ) -> BenchmarkValidationReport:
        issues: set[str] = set()
        if not isinstance(benchmark, Benchmark):
            return BenchmarkValidationReport(None, 0, 0, 0, ("benchmark_invalid",))

        if benchmark.schema_version != "1.0":
            issues.add("unsupported_schema")

        snapshots: dict[str, str] = {}
        if not isinstance(expected_snapshots, Mapping) or not expected_snapshots:
            issues.add("snapshot_manifest_invalid")
        else:
            for repository_id, commit_sha in expected_snapshots.items():
                if (not isinstance(repository_id, str) or not repository_id.strip()
                        or not isinstance(commit_sha, str)
                        or not _FULL_SHA1_PATTERN.fullmatch(commit_sha)):
                    issues.add("snapshot_manifest_invalid")
                    continue
                snapshots[repository_id] = commit_sha.lower()

        inventory: dict[str, tuple[str, str]] = {}
        inventory_count = 0
        try:
            chunk_rows = tuple(chunks)
        except TypeError:
            chunk_rows = ()
            issues.add("chunk_inventory_invalid")

        for chunk in chunk_rows:
            inventory_count += 1
            if (not isinstance(chunk, CodeChunk)
                    or not isinstance(chunk.chunk_id, str)
                    or not chunk.chunk_id.strip()
                    or not isinstance(chunk.repository_id, str)
                    or not chunk.repository_id.strip()
                    or not isinstance(chunk.commit_sha, str)
                    or not _FULL_SHA1_PATTERN.fullmatch(chunk.commit_sha)):
                issues.add("chunk_inventory_invalid")
                continue
            if chunk.chunk_id in inventory:
                issues.add("duplicate_inventory_chunk_id")
                continue
            identity = (chunk.repository_id, chunk.commit_sha.lower())
            inventory[chunk.chunk_id] = identity
            expected_sha = snapshots.get(chunk.repository_id)
            if expected_sha is None or identity[1] != expected_sha:
                issues.add("inventory_snapshot_mismatch")

        cases = benchmark.cases
        if not isinstance(cases, tuple) or not cases:
            issues.add("benchmark_cases_invalid")
            cases = ()

        query_ids: set[str] = set()
        validated_case_count = 0
        for case in cases:
            case_valid = True
            if not isinstance(case, BenchmarkCase):
                issues.add("benchmark_case_invalid")
                continue

            if not isinstance(case.query_id, str) or not case.query_id.strip():
                issues.add("query_id_invalid")
                case_valid = False
            elif case.query_id in query_ids:
                issues.add("duplicate_query_id")
                case_valid = False
            else:
                query_ids.add(case.query_id)

            expected_slug = (
                case.repository_id.rsplit("/", maxsplit=1)[-1].casefold()
                if isinstance(case.repository_id, str) else ""
            )
            if (not isinstance(case.query_id, str)
                    or not _QUERY_ID_PATTERN.fullmatch(case.query_id)
                    or not expected_slug
                    or case.query_id.rsplit("-", maxsplit=1)[0] != expected_slug):
                issues.add("query_id_format_invalid")
                case_valid = False

            if (not isinstance(case.query, str) or not case.query.strip()
                    or case.query != case.query.strip()
                    or any(ord(character) < 32 or ord(character) == 127 for character in case.query)):
                issues.add("query_format_invalid")
                case_valid = False

            if (not isinstance(case.repository_id, str) or not case.repository_id.strip()
                    or not isinstance(case.commit_sha, str)
                    or not _FULL_SHA1_PATTERN.fullmatch(case.commit_sha)):
                issues.add("case_identity_invalid")
                case_valid = False
                case_identity = None
            elif snapshots.get(case.repository_id) != case.commit_sha.lower():
                issues.add("snapshot_mismatch")
                case_valid = False
                case_identity = (case.repository_id, case.commit_sha.lower())
            else:
                case_identity = (case.repository_id, case.commit_sha.lower())

            if not isinstance(case.relevance, tuple) or not case.relevance:
                issues.add("relevance_invalid")
                case_valid = False
                relevance_rows = ()
            else:
                relevance_rows = case.relevance

            relevant_ids: set[str] = set()
            for entry in relevance_rows:
                if (not isinstance(entry, tuple) or len(entry) != 2
                        or not isinstance(entry[0], str) or not entry[0].strip()):
                    issues.add("relevance_invalid")
                    case_valid = False
                    continue
                chunk_id, grade = entry
                if chunk_id in relevant_ids:
                    issues.add("duplicate_relevance_chunk_id")
                    case_valid = False
                relevant_ids.add(chunk_id)
                if type(grade) is not int or grade not in _ALLOWED_RELEVANCE_GRADES:
                    issues.add("relevance_grade_invalid")
                    case_valid = False
                identity = inventory.get(chunk_id)
                if identity is None:
                    issues.add("missing_chunk_id")
                    case_valid = False
                elif case_identity is not None and identity != case_identity:
                    issues.add("relevant_chunk_snapshot_mismatch")
                    case_valid = False

            if case_valid:
                validated_case_count += 1

        return BenchmarkValidationReport(
            benchmark.schema_version,
            len(cases),
            validated_case_count,
            inventory_count,
            tuple(sorted(issues)),
        )