"""Prepare externally stored benchmark annotations without freezing them."""

from collections.abc import Iterable, Mapping
from copy import deepcopy
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .benchmark_freeze import ANNOTATION_CATEGORIES

TEMPLATE_SCHEMA_VERSION = "1.0"
DRAFT_SCHEMA_VERSION = "1.0"
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
_QUERY_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*-\d{3}$")
_REQUIRED_ENTRY_FIELDS = frozenset({
    "query_id",
    "repository_id",
    "commit_sha",
    "category",
    "query",
    "relevance",
    "expected_files",
    "expected_spans",
    "annotation_rationale",
    "ambiguity_notes",
})
_ANNOTATION_FIELDS = (
    "query",
    "relevance",
    "expected_files",
    "expected_spans",
    "annotation_rationale",
    "ambiguity_notes",
)
_BENCHMARK_CASE_FIELDS = (
    "query_id",
    "repository_id",
    "commit_sha",
    "query",
    "relevance",
)


def load_annotation_template(path: str | Path) -> dict[str, Any]:
    """Load a blank or in-progress template from outside the project tree."""
    template_path = _external_path(path)
    payload = json.loads(template_path.read_text(encoding="utf-8"))
    _validate_template(payload)
    return payload


def validate_annotation_entry(
    entry: Mapping[str, Any],
    *,
    chunk_ids: Iterable[str] | None = None,
) -> None:
    """Reject incomplete or malformed labels and, optionally, unknown chunk IDs."""
    if not isinstance(entry, Mapping):
        raise ValueError("Annotation entry must be an object")
    missing = sorted(_REQUIRED_ENTRY_FIELDS.difference(entry))
    if missing:
        raise ValueError(f"Annotation entry is missing required fields: {', '.join(missing)}")

    for field in ("query_id", "repository_id", "commit_sha"):
        value = entry[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be nonempty text")
    if not _QUERY_ID_PATTERN.fullmatch(entry["query_id"]):
        raise ValueError("query_id must end in a three-digit sequence")
    if not _COMMIT_PATTERN.fullmatch(entry["commit_sha"]):
        raise ValueError("commit_sha must be a full 40-character SHA-1")
    if entry["query_id"].rsplit("-", maxsplit=1)[0] != (
        entry["repository_id"].rsplit("/", maxsplit=1)[-1].casefold()
    ):
        raise ValueError("query_id slug must match the repository ID")

    category = entry["category"]
    if not isinstance(category, str) or category not in ANNOTATION_CATEGORIES:
        raise ValueError("category is not one of the declared annotation categories")

    query = entry["query"]
    if (
        not isinstance(query, str)
        or not query
        or query != query.strip()
        or any(ord(character) < 32 or ord(character) == 127 for character in query)
    ):
        raise ValueError("query must be trimmed, nonempty, single-line text")

    relevance = entry["relevance"]
    if not isinstance(relevance, Mapping) or not relevance:
        raise ValueError("relevance must contain at least one chunk ID")
    known_chunk_ids = set(chunk_ids) if chunk_ids is not None else None
    for chunk_id, grade in relevance.items():
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise ValueError("relevance contains a missing or invalid chunk ID")
        if type(grade) is not int or grade not in {1, 2}:
            raise ValueError("relevance grades must be integer 1 or 2")
        if known_chunk_ids is not None and chunk_id not in known_chunk_ids:
            raise ValueError(f"Unknown chunk ID: {chunk_id}")

    expected_files = entry["expected_files"]
    if (
        not isinstance(expected_files, list)
        or not expected_files
        or any(not _valid_repository_path(path) for path in expected_files)
    ):
        raise ValueError("expected_files must be a nonempty list of paths")

    expected_spans = entry["expected_spans"]
    if not isinstance(expected_spans, list) or not expected_spans:
        raise ValueError("expected_spans must be a nonempty list")
    for span in expected_spans:
        if not _valid_span(span):
            raise ValueError("expected_spans must contain file, symbol, and valid inclusive lines")
        if span["file"] not in expected_files:
            raise ValueError("Every expected span file must appear in expected_files")

    for field in ("annotation_rationale", "ambiguity_notes"):
        value = entry[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be nonempty text (use an explicit none/clear note)")


def add_annotation_entry(
    template: Mapping[str, Any],
    entry: Mapping[str, Any],
    *,
    chunk_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Return a copy of the template with one validated, matching slot filled."""
    _validate_template(template)
    validate_annotation_entry(entry, chunk_ids=chunk_ids)
    updated = deepcopy(dict(template))
    updated["cases"] = [deepcopy(dict(case)) for case in template["cases"]]
    matches = [case for case in updated["cases"] if case["query_id"] == entry["query_id"]]
    if len(matches) != 1:
        raise ValueError("query_id must identify exactly one template slot")
    slot = matches[0]
    for field in ("repository_id", "commit_sha", "category"):
        if slot.get(field) != entry[field]:
            raise ValueError(f"{field} does not match the template slot")
    if any(_has_annotation_value(slot.get(field)) for field in _ANNOTATION_FIELDS):
        raise ValueError("Template slot is already annotated; refusing to overwrite it")

    slot.update(dict(entry))
    return updated


def save_annotation_template(template: Mapping[str, Any], path: str | Path) -> Path:
    """Persist an updated authoring template outside the project tree."""
    _validate_template(template)
    target = _external_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_canonical_json(dict(template)), encoding="utf-8", newline="\n")
    return target


def export_benchmark_draft(
    template: Mapping[str, Any],
    output_path: str | Path,
    *,
    chunk_ids_by_snapshot: Mapping[tuple[str, str], Iterable[str]] | None = None,
) -> Path:
    """Export authored cases in a deterministic, explicitly non-final envelope.

    The draft schema intentionally differs from the final ``schema_version``
    contract so it cannot be loaded as a benchmark by ``BenchmarkLoader``.
    """
    _validate_template(template)
    inventory = None
    if chunk_ids_by_snapshot is not None:
        inventory = {
            (repository_id, commit_sha.lower()): set(chunk_ids)
            for identity, chunk_ids in chunk_ids_by_snapshot.items()
            for repository_id, commit_sha in (identity,)
        }

    exported_cases = []
    for case in template["cases"]:
        if not any(_has_annotation_value(case.get(field)) for field in _ANNOTATION_FIELDS):
            continue
        chunk_ids = None
        if inventory is not None:
            identity = (case.get("repository_id"), str(case.get("commit_sha", "")).lower())
            chunk_ids = inventory.get(identity, set())
        validate_annotation_entry(case, chunk_ids=chunk_ids)
        exported_cases.append({field: case[field] for field in _BENCHMARK_CASE_FIELDS})

    if not exported_cases:
        raise ValueError("Cannot export a draft without completed annotation entries")
    payload = {
        "draft_schema_version": DRAFT_SCHEMA_VERSION,
        "status": "draft_not_validated_or_frozen",
        "cases": exported_cases,
    }

    target = _external_path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(_canonical_json(payload))
    return target


def _validate_template(payload: Any) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("Annotation template must be an object")
    if payload.get("template_schema_version") != TEMPLATE_SCHEMA_VERSION:
        raise ValueError("Unsupported annotation template schema")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("Annotation template cases must be a list")
    query_ids = []
    for case in cases:
        if not isinstance(case, Mapping):
            raise ValueError("Annotation template cases must be objects")
        query_id = case.get("query_id")
        if not isinstance(query_id, str) or not query_id:
            raise ValueError("Template slot query_id must be nonempty text")
        if not isinstance(case.get("repository_id"), str) or not isinstance(
            case.get("commit_sha"), str
        ):
            raise ValueError("Template slots require repository_id and commit_sha")
        category = case.get("category")
        if not isinstance(category, str) or category not in ANNOTATION_CATEGORIES:
            raise ValueError("Template slot has an invalid annotation category")
        query_ids.append(query_id)
    if len(query_ids) != len(set(query_ids)):
        raise ValueError("Template query IDs must be unique")


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


def _valid_repository_path(path: Any) -> bool:
    return (
        isinstance(path, str)
        and bool(path.strip())
        and "\\" not in path
        and not PurePosixPath(path).is_absolute()
        and all(part not in {"", ".", ".."} for part in path.split("/"))
    )


def _has_annotation_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (Mapping, list, tuple, set, frozenset)):
        return bool(value)
    return value is not None


def _external_path(path: str | Path) -> Path:
    target = Path(path).expanduser().resolve(strict=False)
    if target == _PROJECT_ROOT or target.is_relative_to(_PROJECT_ROOT):
        raise ValueError("Annotation benchmark data must be stored outside the project")
    return target


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"