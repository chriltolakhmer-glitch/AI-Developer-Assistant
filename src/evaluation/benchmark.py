"""Deterministic JSON benchmark loading for retrieval evaluation."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    query_id: str
    repository_id: str
    commit_sha: str
    query: str
    relevance: tuple[tuple[str, int], ...]

    @property
    def relevant_ids(self) -> frozenset[str]:
        return frozenset(chunk_id for chunk_id, _ in self.relevance)

    @property
    def relevance_by_id(self) -> dict[str, int]:
        return dict(self.relevance)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BenchmarkCase":
        required = ("query_id", "repository_id", "commit_sha", "query", "relevance")
        if any(key not in value for key in required):
            raise ValueError("Benchmark case is missing a required field")
        query_id, repository_id, commit_sha, query = (
            value["query_id"], value["repository_id"], value["commit_sha"], value["query"]
        )
        if any(not isinstance(item, str) or not item.strip()
               for item in (query_id, repository_id, commit_sha, query)):
            raise ValueError("Benchmark identity and query fields must be nonempty text")
        raw_relevance = value["relevance"]
        if not isinstance(raw_relevance, dict) or not raw_relevance:
            raise ValueError("Benchmark relevance must be a nonempty object")
        relevance = []
        for chunk_id, grade in raw_relevance.items():
            if not isinstance(chunk_id, str) or not chunk_id.strip():
                raise ValueError("Relevant chunk IDs must be nonempty text")
            if type(grade) is not int or grade < 1:
                raise ValueError("Relevance grades must be positive integers")
            relevance.append((chunk_id, grade))
        return cls(query_id, repository_id, commit_sha, query,
                   tuple(sorted(relevance)))


@dataclass(frozen=True, slots=True)
class Benchmark:
    schema_version: str
    cases: tuple[BenchmarkCase, ...]


class BenchmarkLoader:
    """Load a source-independent JSON benchmark from a local file."""

    def load(self, path: str | Path) -> Benchmark:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
            raise ValueError("Unsupported benchmark schema")
        raw_cases = payload.get("cases")
        if not isinstance(raw_cases, list) or not raw_cases:
            raise ValueError("Benchmark must contain at least one case")
        cases = tuple(BenchmarkCase.from_dict(case) for case in raw_cases)
        query_ids = [case.query_id for case in cases]
        if len(query_ids) != len(set(query_ids)):
            raise ValueError("Benchmark query IDs must be unique")
        return Benchmark(payload["schema_version"], cases)


def load_benchmark(path: str | Path) -> Benchmark:
    return BenchmarkLoader().load(path)
