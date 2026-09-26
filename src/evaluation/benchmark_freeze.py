"""Create deterministic, source-free metadata for a validated benchmark freeze."""

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from src.models.chunk import CodeChunk
from .benchmark import Benchmark, BenchmarkLoader
from .benchmark_validator import BenchmarkValidator


FREEZE_METADATA_SCHEMA = "1.0"
BENCHMARK_FORMAT_VERSION = "phase8.2-canonical-v1"
ANNOTATION_CATEGORIES = frozenset({
    "architecture_understanding",
    "code_navigation",
    "dependency_understanding",
    "bug_investigation",
})
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class RepositoryFreezeSummary:
    repository_id: str
    commit_sha: str
    query_count: int
    category_counts: tuple[tuple[str, int], ...]
    chunk_reference_count: int
    unique_chunk_reference_count: int


@dataclass(frozen=True, slots=True)
class BenchmarkFreezeMetadata:
    """Deterministic metadata; excludes source text and individual chunk IDs."""

    metadata_schema: str
    benchmark_format: str
    freeze_status: str
    validation_status: str
    benchmark_sha256: str
    snapshot_map_sha256: str
    annotation_ledger_sha256: str
    review_record_sha256: str | None
    freeze_bundle_sha256: str
    target_coverage_ready: bool
    query_count: int
    repository_count: int
    category_counts: tuple[tuple[str, int], ...]
    chunk_reference_count: int
    unique_chunk_reference_count: int
    chunk_inventory_count: int
    repositories: tuple[RepositoryFreezeSummary, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


class BenchmarkFreezeUtility:
    """Validate a benchmark and produce stable hashes and freeze metadata.

    A valid review-record digest is an explicit caller attestation that manual
    ground-truth review is complete. The utility verifies only its digest form;
    the review itself remains a controlled external record.
    """

    def freeze(
        self,
        benchmark: Benchmark | str | Path,
        chunks: Iterable[CodeChunk],
        expected_snapshots: Mapping[str, str],
        categories: Mapping[str, str],
        *,
        annotation_ledger_sha256: str,
        review_record_sha256: str | None = None,
        metadata_path: str | Path | None = None,
    ) -> BenchmarkFreezeMetadata:
        loaded = self._load_benchmark(benchmark)
        self._validate_digest("annotation_ledger_sha256", annotation_ledger_sha256)
        if review_record_sha256 is not None:
            self._validate_digest("review_record_sha256", review_record_sha256)

        chunk_rows = tuple(chunks)
        validation = BenchmarkValidator().validate(loaded, chunk_rows, expected_snapshots)
        if not validation.is_valid:
            raise ValueError(
                "Benchmark validation failed: " + ", ".join(validation.issues)
            )
        category_map = self._validate_categories(loaded, categories)

        canonical_benchmark = self._canonical_benchmark(loaded, category_map)
        benchmark_sha256 = self._sha256(canonical_benchmark)
        canonical_snapshots = {
            repository_id: commit_sha.lower()
            for repository_id, commit_sha in sorted(expected_snapshots.items())
        }
        snapshot_map_sha256 = self._sha256(self._canonical_json(canonical_snapshots))
        bundle = {
            "benchmark_sha256": benchmark_sha256,
            "snapshot_map_sha256": snapshot_map_sha256,
            "annotation_ledger_sha256": annotation_ledger_sha256.lower(),
            "review_record_sha256": (
                review_record_sha256.lower() if review_record_sha256 else None
            ),
        }
        freeze_bundle_sha256 = self._sha256(self._canonical_json(bundle))
        metadata = self._make_metadata(
            loaded,
            category_map,
            validation.inventory_chunk_count,
            benchmark_sha256,
            snapshot_map_sha256,
            annotation_ledger_sha256.lower(),
            review_record_sha256.lower() if review_record_sha256 else None,
            freeze_bundle_sha256,
        )
        if metadata_path is not None:
            self.write_metadata(metadata, metadata_path)
        return metadata

    @staticmethod
    def write_metadata(metadata: BenchmarkFreezeMetadata, path: str | Path) -> None:
        """Write new metadata outside the project; never overwrite a freeze record."""
        target = BenchmarkFreezeUtility._external_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(metadata.to_json())

    @staticmethod
    def _load_benchmark(benchmark: Benchmark | str | Path) -> Benchmark:
        if isinstance(benchmark, Benchmark):
            return benchmark
        if isinstance(benchmark, (str, Path)):
            source = BenchmarkFreezeUtility._external_path(benchmark)
            return BenchmarkLoader().load(source)
        raise ValueError("benchmark must be a loaded Benchmark or external JSON path")

    @staticmethod
    def _validate_categories(
        benchmark: Benchmark, categories: Mapping[str, str]
    ) -> dict[str, str]:
        if not isinstance(categories, Mapping):
            raise ValueError("categories must map every query ID to a known category")
        query_ids = {case.query_id for case in benchmark.cases}
        if set(categories) != query_ids:
            raise ValueError("categories must cover exactly the benchmark query IDs")
        normalized: dict[str, str] = {}
        for query_id, category in categories.items():
            if (not isinstance(query_id, str) or not isinstance(category, str)
                    or category not in ANNOTATION_CATEGORIES):
                raise ValueError("Benchmark contains an unknown query category")
            normalized[query_id] = category
        return normalized

    @staticmethod
    def _validate_digest(name: str, value: str) -> None:
        if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
            raise ValueError(f"{name} must be a 64-character SHA-256 hex digest")

    @staticmethod
    def _canonical_benchmark(benchmark: Benchmark, categories: Mapping[str, str]) -> bytes:
        cases = []
        for case in sorted(benchmark.cases, key=lambda item: item.query_id):
            cases.append({
                "query_id": case.query_id,
                "repository_id": case.repository_id,
                "commit_sha": case.commit_sha.lower(),
                "query": case.query,
                "category": categories[case.query_id],
                "relevance": {
                    chunk_id: grade for chunk_id, grade in sorted(case.relevance)
                },
            })
        return BenchmarkFreezeUtility._canonical_json({
            "schema_version": benchmark.schema_version,
            "cases": cases,
        })

    @staticmethod
    def _canonical_json(value: Any) -> bytes:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")

    @staticmethod
    def _sha256(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _make_metadata(
        benchmark: Benchmark,
        categories: Mapping[str, str],
        inventory_count: int,
        benchmark_sha256: str,
        snapshot_map_sha256: str,
        annotation_ledger_sha256: str,
        review_record_sha256: str | None,
        freeze_bundle_sha256: str,
    ) -> BenchmarkFreezeMetadata:
        grouped: dict[str, list[Any]] = {}
        for case in benchmark.cases:
            grouped.setdefault(case.repository_id, []).append(case)

        repository_summaries = []
        all_chunk_ids: set[str] = set()
        category_totals = {category: 0 for category in sorted(ANNOTATION_CATEGORIES)}
        total_references = 0
        for repository_id, cases in sorted(grouped.items()):
            category_counts = {category: 0 for category in sorted(ANNOTATION_CATEGORIES)}
            referenced_ids: set[str] = set()
            reference_count = 0
            for case in cases:
                category = categories[case.query_id]
                category_counts[category] += 1
                category_totals[category] += 1
                reference_count += len(case.relevance)
                referenced_ids.update(chunk_id for chunk_id, _ in case.relevance)
            total_references += reference_count
            all_chunk_ids.update(referenced_ids)
            repository_summaries.append(RepositoryFreezeSummary(
                repository_id=repository_id,
                commit_sha=cases[0].commit_sha.lower(),
                query_count=len(cases),
                category_counts=tuple(
                    (category, count) for category, count in sorted(category_counts.items())
                ),
                chunk_reference_count=reference_count,
                unique_chunk_reference_count=len(referenced_ids),
            ))

        target_coverage_ready = (
            len(benchmark.cases) == 108
            and len(grouped) == 9
            and all(
                len(cases) == 12
                and all(count == 3 for count in {
                    category: sum(categories[case.query_id] == category for case in cases)
                    for category in ANNOTATION_CATEGORIES
                }.values())
                for cases in grouped.values()
            )
        )
        freeze_status = (
            "frozen"
            if target_coverage_ready and review_record_sha256
            else "validated_pending_review"
            if not review_record_sha256
            else "validated_pending_target_coverage"
        )

        return BenchmarkFreezeMetadata(
            metadata_schema=FREEZE_METADATA_SCHEMA,
            benchmark_format=BENCHMARK_FORMAT_VERSION,
            freeze_status=freeze_status,
            validation_status="passed",
            benchmark_sha256=benchmark_sha256,
            snapshot_map_sha256=snapshot_map_sha256,
            annotation_ledger_sha256=annotation_ledger_sha256,
            review_record_sha256=review_record_sha256,
            freeze_bundle_sha256=freeze_bundle_sha256,
            target_coverage_ready=target_coverage_ready,
            query_count=len(benchmark.cases),
            repository_count=len(grouped),
            category_counts=tuple(sorted(category_totals.items())),
            chunk_reference_count=total_references,
            unique_chunk_reference_count=len(all_chunk_ids),
            chunk_inventory_count=inventory_count,
            repositories=tuple(repository_summaries),
        )

    @staticmethod
    def _external_path(path: str | Path) -> Path:
        target = Path(path).expanduser().resolve(strict=False)
        if target == _PROJECT_ROOT or target.is_relative_to(_PROJECT_ROOT):
            raise ValueError("Benchmark artifacts and freeze metadata must be outside the project")
        return target


def freeze_benchmark(
    benchmark: Benchmark | str | Path,
    chunks: Iterable[CodeChunk],
    expected_snapshots: Mapping[str, str],
    categories: Mapping[str, str],
    *,
    annotation_ledger_sha256: str,
    review_record_sha256: str | None = None,
    metadata_path: str | Path | None = None,
) -> BenchmarkFreezeMetadata:
    """Convenience wrapper for `BenchmarkFreezeUtility.freeze`."""
    return BenchmarkFreezeUtility().freeze(
        benchmark,
        chunks,
        expected_snapshots,
        categories,
        annotation_ledger_sha256=annotation_ledger_sha256,
        review_record_sha256=review_record_sha256,
        metadata_path=metadata_path,
    )