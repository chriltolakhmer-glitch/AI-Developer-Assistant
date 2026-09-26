"""Create the Phase 8.3 annotation scaffold and report aggregate progress."""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path
import re
from typing import Any

from src.evaluation.pipeline_validation import APPROVED_CORPUS
from .benchmark_freeze import ANNOTATION_CATEGORIES


TEMPLATE_SCHEMA_VERSION = "1.0"
TARGET_CASES_PER_REPOSITORY = 12
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_QUERY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*-\d{3}$")
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
_CATEGORY_ORDER = (
    "architecture_understanding",
    "code_navigation",
    "dependency_understanding",
    "bug_investigation",
)


@dataclass(frozen=True, slots=True)
class RepositoryProgress:
    repository_id: str
    expected_commit_sha: str
    case_slots: int
    authored_queries: int
    annotated_cases: int
    category_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class BenchmarkStatistics:
    template_schema_version: str | None
    case_slots: int
    target_query_count: int
    authored_query_count: int
    annotated_case_count: int
    annotation_completeness: float
    repository_count: int
    repositories_with_authored_queries: int
    category_distribution: tuple[tuple[str, int], ...]
    chunk_reference_count: int
    chunk_validation_status: str
    missing_chunk_reference_count: int | None
    issue_codes: tuple[str, ...]
    repositories: tuple[RepositoryProgress, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def create_annotation_template(output_path: str | Path) -> Path:
    """Create a blank, externally stored 108-case annotation scaffold.

    This is deliberately not valid input to `BenchmarkLoader`: blank questions
    and labels must be manually annotated before conversion/validation.
    Existing output is never overwritten.
    """
    output = _external_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    cases = []
    for repository in APPROVED_CORPUS:
        slug = repository.repository_id.rsplit("/", maxsplit=1)[-1].casefold()
        for sequence in range(TARGET_CASES_PER_REPOSITORY):
            category = _CATEGORY_ORDER[sequence // 3]
            cases.append({
                "query_id": f"{slug}-{sequence + 1:03d}",
                "repository_id": repository.repository_id,
                "commit_sha": repository.commit_sha,
                "category": category,
                "query": "",
                "relevance": {},
                "expected_files": [],
                "expected_spans": [],
                "annotation_rationale": "",
                "ambiguity_notes": "",
            })

    payload = {
        "template_schema_version": TEMPLATE_SCHEMA_VERSION,
        "status": "annotation_in_progress_not_a_validated_benchmark",
        "cases": cases,
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    return output


def calculate_benchmark_statistics(
    payload: Mapping[str, Any],
    chunk_ids_by_snapshot: Mapping[tuple[str, str], Iterable[str]] | None = None,
) -> BenchmarkStatistics:
    """Calculate annotation progress without exposing question/source content."""
    issues: set[str] = set()
    if not isinstance(payload, Mapping):
        return _empty_statistics("template_invalid")
    version = payload.get("template_schema_version")
    if version != TEMPLATE_SCHEMA_VERSION:
        issues.add("unsupported_template_schema")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        return _empty_statistics("cases_invalid", version)

    expected = {row.repository_id: row.commit_sha.lower() for row in APPROVED_CORPUS}
    grouped: dict[str, list[Mapping[str, Any]]] = {repository_id: [] for repository_id in expected}
    seen_query_ids: set[str] = set()
    all_categories = list(_CATEGORY_ORDER)
    category_counts: Counter[str] = Counter({category: 0 for category in all_categories})
    authored_count = 0
    annotated_count = 0
    annotated_by_repository: Counter[str] = Counter()
    chunk_reference_count = 0
    missing_chunk_references = 0

    inventory: dict[tuple[str, str], set[str]] | None = None
    if chunk_ids_by_snapshot is not None:
        inventory = {identity: set(ids) for identity, ids in chunk_ids_by_snapshot.items()}

    for case in raw_cases:
        if not isinstance(case, Mapping):
            issues.add("case_invalid")
            continue
        repository_id = case.get("repository_id")
        commit_sha = case.get("commit_sha")
        query_id = case.get("query_id")
        category = case.get("category")

        valid_identity = (
            isinstance(repository_id, str)
            and repository_id in expected
            and isinstance(commit_sha, str)
            and _COMMIT_PATTERN.fullmatch(commit_sha) is not None
            and expected.get(repository_id) == commit_sha.lower()
        )
        if not valid_identity:
            issues.add("snapshot_mismatch")
        elif repository_id in grouped:
            grouped[repository_id].append(case)

        query_id_valid = (
            isinstance(query_id, str)
            and _QUERY_PATTERN.fullmatch(query_id) is not None
            and isinstance(repository_id, str)
            and query_id.rsplit("-", maxsplit=1)[0]
            == repository_id.rsplit("/", maxsplit=1)[-1].casefold()
        )
        if not query_id_valid:
            issues.add("query_id_invalid")
        elif query_id in seen_query_ids:
            issues.add("duplicate_query_id")
            query_id_valid = False
        else:
            seen_query_ids.add(query_id)

        category_valid = isinstance(category, str) and category in ANNOTATION_CATEGORIES
        if not category_valid:
            issues.add("category_invalid")
        else:
            category_counts[category] += 1

        query = case.get("query")
        authored = (
            isinstance(query, str)
            and bool(query.strip())
            and query == query.strip()
            and not any(ord(character) < 32 or ord(character) == 127 for character in query)
        )
        if authored:
            authored_count += 1

        relevance = case.get("relevance")
        labels_valid = isinstance(relevance, Mapping) and bool(relevance)
        case_missing_references = 0
        if labels_valid:
            for chunk_id, grade in relevance.items():
                chunk_reference_count += 1
                valid_chunk_id = isinstance(chunk_id, str) and bool(chunk_id.strip())
                valid_grade = type(grade) is int and grade in {1, 2}
                if not valid_chunk_id or not valid_grade:
                    labels_valid = False
                    issues.add("relevance_invalid")
                if inventory is not None:
                    chunk_inventory = inventory.get((repository_id, commit_sha.lower())) \
                        if isinstance(repository_id, str) and isinstance(commit_sha, str) else None
                    if (not valid_chunk_id or chunk_inventory is None
                            or chunk_id not in chunk_inventory):
                        missing_chunk_references += 1
                        case_missing_references += 1

        rationale_valid = (
            isinstance(case.get("annotation_rationale"), str)
            and bool(case["annotation_rationale"].strip())
        )
        ambiguity_recorded = (
            isinstance(case.get("ambiguity_notes"), str)
            and bool(case["ambiguity_notes"].strip())
        )
        expected_files = case.get("expected_files")
        expected_spans = case.get("expected_spans")
        evidence_recorded = (
            isinstance(expected_files, list)
            and bool(expected_files)
            and all(isinstance(item, str) and item.strip() for item in expected_files)
            and isinstance(expected_spans, list)
            and bool(expected_spans)
            and all(_valid_span(span) for span in expected_spans)
        )
        if (
            authored
            and labels_valid
            and rationale_valid
            and ambiguity_recorded
            and evidence_recorded
            and valid_identity
            and query_id_valid
            and category_valid
            and (inventory is None or case_missing_references == 0)
        ):
            annotated_count += 1
            if isinstance(repository_id, str):
                annotated_by_repository[repository_id] += 1

    target_case_count = len(APPROVED_CORPUS) * TARGET_CASES_PER_REPOSITORY
    if len(raw_cases) != target_case_count:
        issues.add("target_case_count_mismatch")
    for repository_id, repository_cases in grouped.items():
        if len(repository_cases) != TARGET_CASES_PER_REPOSITORY:
            issues.add("repository_coverage_mismatch")
        per_repository_categories = Counter(
            case.get("category") for case in repository_cases
            if isinstance(case.get("category"), str)
        )
        if any(per_repository_categories[category] != 3 for category in all_categories):
            issues.add("category_distribution_mismatch")

    if inventory is not None and chunk_reference_count > 0 and missing_chunk_references == 0:
        chunk_validation_status = "passed"
    elif inventory is not None and missing_chunk_references > 0:
        chunk_validation_status = "failed"
        issues.add("chunk_reference_missing")
    else:
        chunk_validation_status = "not_run"

    repositories = []
    for repository_id, repository_cases in sorted(grouped.items()):
        local_categories = Counter(
            case.get("category") for case in repository_cases
            if isinstance(case.get("category"), str)
            and case.get("category") in ANNOTATION_CATEGORIES
        )
        repositories.append(RepositoryProgress(
            repository_id=repository_id,
            expected_commit_sha=expected[repository_id],
            case_slots=len(repository_cases),
            authored_queries=sum(
                isinstance(case.get("query"), str) and bool(case["query"].strip())
                for case in repository_cases
            ),
            annotated_cases=annotated_by_repository[repository_id],
            category_counts=tuple((category, local_categories[category]) for category in all_categories),
        ))

    return BenchmarkStatistics(
        template_schema_version=version if isinstance(version, str) else None,
        case_slots=len(raw_cases),
        target_query_count=target_case_count,
        authored_query_count=authored_count,
        annotated_case_count=annotated_count,
        annotation_completeness=annotated_count / target_case_count,
        repository_count=len(expected),
        repositories_with_authored_queries=sum(row.authored_queries > 0 for row in repositories),
        category_distribution=tuple((category, category_counts[category]) for category in all_categories),
        chunk_reference_count=chunk_reference_count,
        chunk_validation_status=chunk_validation_status,
        missing_chunk_reference_count=(missing_chunk_references if inventory is not None else None),
        issue_codes=tuple(sorted(issues)),
        repositories=tuple(repositories),
    )


def _empty_statistics(issue: str, version: str | None = None) -> BenchmarkStatistics:
    return BenchmarkStatistics(
        template_schema_version=version,
        case_slots=0,
        target_query_count=len(APPROVED_CORPUS) * TARGET_CASES_PER_REPOSITORY,
        authored_query_count=0,
        annotated_case_count=0,
        annotation_completeness=0.0,
        repository_count=len(APPROVED_CORPUS),
        repositories_with_authored_queries=0,
        category_distribution=tuple((category, 0) for category in _CATEGORY_ORDER),
        chunk_reference_count=0,
        chunk_validation_status="not_run",
        missing_chunk_reference_count=None,
        issue_codes=(issue,),
        repositories=(),
    )


def _valid_span(span: Any) -> bool:
    if not isinstance(span, Mapping):
        return False
    lines = span.get("lines")
    return (
        isinstance(span.get("file"), str)
        and bool(span["file"].strip())
        and isinstance(span.get("symbol"), str)
        and bool(span["symbol"].strip())
        and isinstance(lines, list)
        and len(lines) == 2
        and all(type(line) is int and line >= 1 for line in lines)
        and lines[0] <= lines[1]
    )


def _external_path(path: str | Path) -> Path:
    target = Path(path).expanduser().resolve(strict=False)
    if target == _PROJECT_ROOT or target.is_relative_to(_PROJECT_ROOT):
        raise ValueError("Annotation benchmark data must be stored outside the project")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--create-template", type=Path)
    mode.add_argument("--input", type=Path)
    arguments = parser.parse_args()
    if arguments.create_template:
        path = create_annotation_template(arguments.create_template)
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        path = _external_path(arguments.input)
        payload = json.loads(path.read_text(encoding="utf-8"))
    print(calculate_benchmark_statistics(payload).to_json(), end="")


if __name__ == "__main__":
    main()