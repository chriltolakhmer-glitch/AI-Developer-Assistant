"""Developer-only retrieval evaluation over Phase 31 query payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_cases(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read developer evaluation cases '{path}': {error}") from error
    if not isinstance(payload, list) or not payload:
        raise ValueError("Developer evaluation cases must be a nonempty JSON list.")
    cases = []
    for case in payload:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"].strip():
            raise ValueError("Each developer evaluation case needs a nonempty id.")
        if not isinstance(case.get("query"), str) or not case["query"].strip():
            raise ValueError(f"Case '{case.get('id', '<unknown>')}' needs nonempty query text.")
        expected = case.get("expected", {})
        if not isinstance(expected, dict):
            raise ValueError(f"Case '{case['id']}' expected value must be an object.")
        for key in ("files", "symbols", "relationships"):
            if not all(isinstance(item, str) and item.strip() for item in expected.get(key, [])):
                raise ValueError(f"Case '{case['id']}' expected.{key} must contain text values.")
        for key in ("allowed_extra_context", "required_relationships"):
            values = case.get(key, expected.get("relationships", []) if key == "required_relationships" else [])
            if not isinstance(values, list) or not all(isinstance(item, str) and item.strip() for item in values):
                raise ValueError(f"Case '{case['id']}' {key} must be a list of nonempty text values.")
        tolerance = case.get("failure_tolerance", {})
        if (not isinstance(tolerance, dict)
                or any(key not in {"allow_extra_files", "allow_missing_relationships"}
                       or type(value) is not bool for key, value in tolerance.items())):
            raise ValueError(f"Case '{case['id']}' failure_tolerance must contain only boolean supported flags.")
        cases.append({
            "id": case["id"], "query": case["query"], "expected": expected,
            "allowed_extra_context": case.get("allowed_extra_context", []),
            "required_relationships": case.get("required_relationships", expected.get("relationships", [])),
            "failure_tolerance": case.get("failure_tolerance", {}),
        })
    return tuple(cases)


def evaluate_cases(cases: tuple[dict[str, Any], ...], payloads: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    details = []
    file_hits = symbol_hits = 0
    context_scores = []
    noise_scores = []
    explanation_hits = 0
    for case, payload in zip(cases, payloads):
        expected = case["expected"]
        results = payload.get("results", [])
        files = {row.get("file_path") for row in results}
        symbols = {row.get("qualified_name") for row in results}
        related_symbols = set()
        for row in results:
            related_symbols.update(item.get("symbol_name") for item in row.get("related_context", []) if item.get("symbol_name"))
            related_symbols.update(row.get("developer_context", {}).get("related_symbol_names", []))
            related_symbols.update(row.get("developer_context", {}).get("configuration_keys", []))
        all_symbols = symbols | related_symbols
        expected_files = set(expected.get("files", []))
        expected_symbols = set(expected.get("symbols", []))
        expected_relationships = set(expected.get("relationships", []))
        missing_files = sorted(expected_files - files)
        missing_symbols = sorted(expected_symbols - all_symbols)
        missing_relationships = sorted(expected_relationships - all_symbols)
        matched_requirements = (len(expected_symbols) - len(missing_symbols)) + (len(expected_relationships) - len(missing_relationships))
        total_requirements = len(expected_symbols) + len(expected_relationships)
        context_score = matched_requirements / total_requirements if total_requirements else 1.0
        extra_files = sorted(files - expected_files) if expected_files else sorted(files)
        duplicate_symbols = len([symbol for symbol in [row.get("qualified_name") for row in results] if symbol in symbols]) - len(symbols)
        noise_score = (len(extra_files) + max(duplicate_symbols, 0)) / max(len(results), 1)
        explained = all(
            row.get("ranking_reason", {}).get("context_expansion_reason")
            and "symbol_relevance" in row.get("ranking_reason", {})
            and row.get("developer_context") is not None
            for row in results
        ) and bool(payload.get("context", {}).get("excluded_context"))
        if not missing_files:
            file_hits += 1
        if not missing_symbols:
            symbol_hits += 1
        if explained:
            explanation_hits += 1
        context_scores.append(context_score)
        noise_scores.append(noise_score)
        failure_types = []
        if missing_files:
            failure_types.append("wrong_file" if files else "no_result")
        if missing_symbols:
            failure_types.append("correct_file_wrong_symbol" if not missing_files else "missing_symbol")
        if missing_relationships:
            failure_types.extend(("missing_dependency", "missing_caller_or_callee"))
        if extra_files:
            failure_types.append("too_much_context")
        if duplicate_symbols:
            failure_types.append("duplicate_context")
        if context_score < 1.0:
            failure_types.append("too_little_context")
        expected_ranks = [row.get("rank") for row in results
                          if row.get("file_path") in expected_files or row.get("qualified_name") in expected_symbols]
        if expected_ranks and min(expected_ranks) > 1:
            failure_types.append("ranking_order")
        if not explained:
            failure_types.append("explanation_mismatch")
        failure_types = sorted(set(failure_types))
        explanation = "No failures detected." if not failure_types else "; ".join(
            f"{failure}: {', '.join(values) or 'observed'}"
            for failure, values in (
                ("missing evidence", missing_files + missing_symbols + missing_relationships),
                ("extra context", extra_files),
            ) if values
        )
        details.append({
            "id": case["id"],
            "query": case["query"],
            "expected": expected,
            "failure_type": failure_types,
            "retrieved": sorted({row.get("file_path") for row in results}),
            "explanation": explanation,
            "file_hit": not missing_files,
            "symbol_hit": not missing_symbols,
            "missing_files": missing_files,
            "missing_symbols": missing_symbols,
            "missing_relationships": missing_relationships,
            "extra_files": extra_files,
            "context_completeness": context_score,
            "noise_rate": noise_score,
            "explanation_complete": explained,
            "results": results,
        })
    count = len(cases)
    return {
        "status": "completed",
        "mode": "developer-local-evaluation",
        "queries": count,
        "file_hits": file_hits,
        "symbol_hits": symbol_hits,
        "context_completeness": sum(context_scores) / count,
        "noise_rate": sum(noise_scores) / count,
        "explanation_coverage": explanation_hits / count,
        "details": details,
        "limitations": [
            "Metrics measure only the supplied developer cases and current Python parser output.",
            "They are not benchmark scores and do not establish general retrieval quality.",
        ],
    }


def compare_reports(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    previous = {item["id"]: item for item in baseline.get("details", [])}
    changed = []
    for item in candidate.get("details", []):
        old = previous.get(item["id"])
        if old is None:
            changed.append({"case": item["id"], "improved": False, "reason": "case was not present in baseline"})
            continue
        old_failures = len(old.get("failure_type", []))
        new_failures = len(item.get("failure_type", []))
        improved = (item["context_completeness"] > old.get("context_completeness", 0)
                    or item["noise_rate"] < old.get("noise_rate", 0)
                    or new_failures < old_failures)
        changed.append({
            "case": item["id"],
            "improved": improved,
            "reason": "context completeness/noise/failure count changed" if improved else "no measured improvement",
        })
    return {
        "baseline": {key: baseline.get(key) for key in ("symbol_hits", "file_hits", "context_completeness", "noise_rate", "explanation_coverage")},
        "candidate": {key: candidate.get(key) for key in ("symbol_hits", "file_hits", "context_completeness", "noise_rate", "explanation_coverage")},
        "changed_cases": changed,
    }