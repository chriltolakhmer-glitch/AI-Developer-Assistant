"""Phase 40 developer-only optimization safety: rollback visibility and conflict diagnostics.

Nothing here reads or writes research, benchmark, Humanize or release paths, and no
source file is edited. Rollback records only describe manual restoration steps inside
the developer workspace; conflicts are reported, never auto-resolved.
"""
from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read, _storage, show_candidates

ROLLBACK_SCHEMA = "developer-rollback-v1"
ROLLBACK_MODE = "developer-local-rollback"
CONFLICT_MODE = "developer-local-optimize-check"


def _write_rollback(workspace, path, document):
    path = workspace._contained(path)
    document = {"schema_version": ROLLBACK_SCHEMA, "mode": ROLLBACK_MODE,
                "recorded_at": datetime.now(timezone.utc).isoformat(), **document}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(_json_bytes(document))
    except FileExistsError as error:
        raise LocalWorkflowError("Rollback record already exists; record a new rollback attempt.") from error
    return document


def _rollback_records(workspace, identifier):
    directory = _storage(workspace, identifier) / "rollback"
    if not directory.exists():
        return []
    return sorted((_read(workspace, path) for path in directory.glob("*.json")),
                  key=lambda item: (item["recorded_at"], item["id"]))


def show_rollback(workspace, identifier=None):
    candidates = show_candidates(workspace, identifier)["candidates"]
    reports = []
    for candidate in candidates:
        decision = candidate["decision"]
        result = candidate["result"]
        previous_states = []
        for validation in candidate["validations"]:
            for key, kind in (("before", "baseline"), ("after", "history")):
                entry = {"version": validation[key], "kind": kind}
                if entry not in previous_states:
                    previous_states.append(entry)
        reports.append({
            "candidate_id": candidate["id"],
            "current_state": decision["status"] if decision else candidate["status"],
            "previous_states": previous_states,
            "affected_behavior": result["comparison"]["comparisons"] if result else [],
            "rollback_available": bool(decision) and decision["status"] == "accepted",
            "rollback_records": _rollback_records(workspace, candidate["id"]),
        })
    return {"mode": ROLLBACK_MODE, "candidates": reports}


def record_rollback(workspace, identifier, note):
    if not isinstance(note, str) or not note.strip():
        raise LocalWorkflowError("Rollback requires a nonempty note describing the restoration.")
    candidate = show_candidates(workspace, identifier)["candidates"][0]
    decision = candidate["decision"]
    if not decision or decision["status"] != "accepted":
        raise LocalWorkflowError("Rollback requires a previously accepted candidate.")
    result = candidate["result"]
    rollback_id = uuid4().hex
    return _write_rollback(workspace, _storage(workspace, identifier) / "rollback" / f"{rollback_id}.json", {
        "id": rollback_id, "candidate_id": identifier, "note": note.strip(),
        "target_version": result["before"] if result else None,
        "instructions": "Manually revert the applied change and reindex; this tool does not modify source files.",
        "scope": "Rollback state is recorded in the developer workspace only; research, benchmark and release paths are untouched."})


def _chain_roots(candidates):
    by_id = {item["id"]: item for item in candidates}

    def root(identifier, seen=None):
        seen = seen or set()
        if identifier in seen or identifier not in by_id:
            return identifier
        parent = by_id[identifier].get("supersedes")
        return identifier if not parent else root(parent, seen | {identifier})

    return {item["id"]: root(item["id"]) for item in candidates}


def detect_conflicts(workspace, repository_id=None):
    candidates = show_candidates(workspace)["candidates"]
    if repository_id is not None:
        candidates = [item for item in candidates if item["repository_id"] == repository_id]
    chains = _chain_roots(candidates)
    conflicts, warnings = [], []

    case_owners = defaultdict(list)
    for candidate in candidates:
        for case in candidate["cases"]:
            case_owners[case].append(candidate["id"])
    for case, owners in case_owners.items():
        if len({chains[identifier] for identifier in owners}) > 1:
            conflicts.append({"type": "repeated_case_target", "cases": [case], "candidates": sorted(set(owners)),
                              "detail": f"Case '{case}' is targeted by more than one independent optimization attempt."})

    change_owners = defaultdict(list)
    for candidate in candidates:
        key = (candidate["repository_id"], candidate["proposed_change"].strip().lower())
        change_owners[key].append(candidate)
    for owners in change_owners.values():
        if len(owners) > 1 and len({chains[item["id"]] for item in owners}) > 1:
            conflicts.append({"type": "duplicate_attempt", "candidates": sorted({item["id"] for item in owners}),
                              "cases": sorted({case for item in owners for case in item["cases"]}),
                              "detail": "Multiple independent candidates propose the same change."})

    for candidate in candidates:
        result = candidate["result"]
        if not result:
            continue
        classifications = {row["case_id"]: row["classification"] for row in result["comparison"]["comparisons"]}
        if "regression" in classifications.values() and "improved" in classifications.values():
            conflicts.append({"type": "mixed_outcome", "candidates": [candidate["id"]],
                              "cases": sorted(classifications),
                              "detail": "The latest validation improves some cases while regressing others."})

    per_case = defaultdict(dict)
    for candidate in candidates:
        result = candidate["result"]
        if not result:
            continue
        for row in result["comparison"]["comparisons"]:
            per_case[row["case_id"]][candidate["id"]] = row["classification"]
    for case, by_candidate in per_case.items():
        roots = {chains[identifier] for identifier in by_candidate}
        if len(roots) > 1 and {"regression", "improved"} <= set(by_candidate.values()):
            conflicts.append({"type": "conflicting_ranking_adjustment", "cases": [case],
                              "candidates": sorted(by_candidate),
                              "detail": f"Independent candidates disagree on the outcome for case '{case}'."})

    roots_map = defaultdict(list)
    for candidate in candidates:
        roots_map[chains[candidate["id"]]].append(candidate)
    for members in roots_map.values():
        rejected = sorted(item["id"] for item in members if item["status"] == "rejected")
        if len(rejected) > 1:
            warnings.append({"type": "repeated_failed_experiments", "candidates": rejected,
                             "detail": "This optimization attempt chain has been rejected more than once."})
    for candidate in candidates:
        if candidate["status"] in {"candidate", "validated"}:
            warnings.append({"type": "unresolved_candidate", "candidates": [candidate["id"]],
                             "detail": "No accept/reject decision has been recorded yet."})

    affected_cases = sorted({case for conflict in conflicts for case in conflict["cases"]})
    return {"mode": CONFLICT_MODE, "conflicts": conflicts, "affected_cases": affected_cases, "warnings": warnings}
