"""Phase 44 developer-only optimization review queue and policy checks.

Review records are immutable snapshots stored in the external developer workspace.
They never apply optimization changes or modify candidate, retrieval, research,
benchmark, Humanize, or release artifacts.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from uuid import uuid4

from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _name, _read, _storage, show_candidates

SCHEMA = "developer-optimization-review-v1"
MODE = "developer-local-optimization-review"
REVIEW_STATES = ("pending", "approved", "rejected", "deferred", "withdrawn")
REVIEW_TRANSITIONS = {
    "pending": {"approved", "rejected", "deferred", "withdrawn"},
    "deferred": {"pending", "withdrawn"},
    "approved": set(),
    "rejected": set(),
    "withdrawn": set(),
}


def _review_root(workspace):
    workspace._prepare()
    return workspace._contained(workspace.root / "optimization" / "reviews")


def _review_directory(workspace, review_id):
    return workspace._contained(_review_root(workspace) / _name(review_id))


def _review_events(workspace, review_id):
    directory = _review_directory(workspace, review_id) / "events"
    if not directory.exists():
        return []
    records = [_read(workspace, path) for path in sorted(directory.glob("*.json"))]
    return sorted(records, key=lambda record: (record.get("sequence", -1),
                                                str(record.get("recorded_at", "")),
                                                str(record.get("id", ""))))


def _all_reviews(workspace):
    root = _review_root(workspace)
    if not root.exists():
        return []
    reviews = []
    for directory in sorted(root.iterdir()):
        workspace._contained(directory)
        if directory.is_dir():
            events = _review_events(workspace, directory.name)
            if events:
                reviews.append(events[-1])
    return sorted(reviews, key=lambda item: (str(item.get("created_at", "")),
                                              str(item.get("review_id", ""))))


def _write_event(workspace, review, recorded_at=None):
    review_id = _name(review["review_id"])
    sequence = review["sequence"]
    event_id = uuid4().hex
    timestamp = recorded_at or datetime.now(timezone.utc).isoformat()
    record = {"schema_version": SCHEMA, "mode": MODE, "id": event_id,
              "recorded_at": timestamp, **review}
    directory = _review_directory(workspace, review_id) / "events"
    directory.mkdir(parents=True, exist_ok=True)
    path = workspace._contained(directory / f"{sequence:06d}-{event_id}.json")
    try:
        with path.open("xb") as stream:
            stream.write(_json_bytes(record))
    except FileExistsError as error:
        raise LocalWorkflowError("Review event already exists; append a new review transition instead.") from error
    return record


def _validation_summary(candidate):
    validation = candidate.get("result")
    if not validation:
        return None
    return {key: deepcopy(validation.get(key)) for key in
            ("id", "recorded_at", "status", "passed", "gates", "before", "after", "retrieval_settings", "base_configuration")}


def _candidate_context(workspace, candidate):
    from .governance import optimize_history, optimize_health, maintenance_report

    lifecycle = [item for item in optimize_history(workspace, candidate["id"])["history"]
                 if item["event_type"] in {"lifecycle", "archived", "ownership_changed"}]
    maintenance = maintenance_report(workspace)
    findings = [item for item in maintenance["findings"]
                if candidate["id"] in item.get("affected_candidate_ids", [])]
    health = optimize_health(workspace)
    return lifecycle, findings, health


def create_review(workspace, candidate_id, reason, owner="developer", affected_cases=None,
                  conflict_note=None):
    """Open a pending review without performing or deciding the optimization."""
    if not isinstance(reason, str) or not reason.strip():
        raise LocalWorkflowError("Opening a review requires a nonempty reason.")
    if not isinstance(owner, str) or not owner.strip():
        raise LocalWorkflowError("Review ownership requires a nonempty owner.")
    if conflict_note is not None and (not isinstance(conflict_note, str) or not conflict_note.strip()):
        raise LocalWorkflowError("A conflict note must be nonempty when supplied.")
    candidate = show_candidates(workspace, _name(candidate_id))["candidates"][0]
    existing = [item for item in _all_reviews(workspace)
                if item.get("candidate_id") == candidate_id and item.get("status") == "pending"]
    if existing:
        raise LocalWorkflowError(f"Candidate '{candidate_id}' already has a pending review.")
    cases = sorted(set(affected_cases if affected_cases is not None else candidate["cases"]))
    if not cases or any(not isinstance(case, str) or not case.strip() for case in cases):
        raise LocalWorkflowError("A review requires at least one affected case.")
    if not set(cases) <= set(candidate["cases"]):
        raise LocalWorkflowError("Review affected cases must be a subset of the candidate's recorded cases.")
    lifecycle, findings, health = _candidate_context(workspace, candidate)
    review_id = f"review-{uuid4().hex}"
    created_at = datetime.now(timezone.utc).isoformat()
    item = {
        "review_id": review_id, "candidate_id": candidate_id, "sequence": 1,
        "status": "pending", "owner": owner.strip(), "reviewer": None,
        "reason": reason.strip(), "conflict_note": conflict_note.strip() if conflict_note else None,
        "affected_cases": cases, "created_at": created_at,
        "validation_summary": _validation_summary(candidate),
        "governance_health_status": health["health_status"],
        "related_candidate_history": deepcopy(candidate["history"]),
        "review_history": [{"sequence": 1, "status": "pending", "previous_status": None,
                             "reviewer": None, "reason": reason.strip(),
                             "conflict_note": conflict_note.strip() if conflict_note else None,
                             "recorded_at": created_at}],
        "candidate_lifecycle_history": lifecycle,
        "maintenance_findings": findings,
    }
    return _write_event(workspace, item, created_at)


def _resolve_review(workspace, identifier):
    reviews = _all_reviews(workspace)
    exact = [item for item in reviews if item.get("review_id") == identifier]
    if exact:
        return exact[0]
    matches = [item for item in reviews if item.get("candidate_id") == identifier]
    pending = [item for item in matches if item.get("status") == "pending"]
    if len(pending) == 1:
        return pending[0]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise LocalWorkflowError(f"Candidate '{identifier}' has multiple reviews; use a review ID.")
    raise LocalWorkflowError(f"No developer review found for '{identifier}'.")


def show_reviews(workspace, identifier=None):
    """List the review queue or show a complete review and its live candidate context."""
    if identifier is None:
        return {"mode": MODE, "reviews": _all_reviews(workspace)}
    review = _resolve_review(workspace, identifier)
    candidate = show_candidates(workspace, review["candidate_id"])["candidates"][0]
    from .governance import optimize_history, maintenance_report

    timeline = optimize_history(workspace, review["candidate_id"])["history"]
    maintenance = maintenance_report(workspace)
    findings = [item for item in maintenance["findings"]
                if review["candidate_id"] in item.get("affected_candidate_ids", [])]
    previous_decisions = [item for item in timeline if item["event_type"] == "decision"]
    return {
        "mode": MODE, "review": review, "candidate": candidate,
        "lifecycle_history": [item for item in timeline
                              if item["event_type"] in {"lifecycle", "archived", "ownership_changed"}],
        "validation_results": candidate["validations"],
        "maintenance_findings": findings,
        "previous_decisions": previous_decisions,
        "related_candidate_history": candidate["history"],
    }


def _policy_for_candidate(workspace, candidate, review, conflicts, audit):
    identifier = candidate["id"]
    passed, warnings, blocked = [], [], []

    required = ("id", "problem", "cases", "source", "repository_id", "proposed_change", "validation_method")
    missing = [field for field in required if not candidate.get(field)]
    if missing:
        blocked.append({"candidate_id": identifier, "check": "candidate_metadata",
                        "detail": "Required candidate metadata is missing or empty.", "fields": missing})
    else:
        passed.append({"candidate_id": identifier, "check": "candidate_metadata",
                       "detail": "Required candidate metadata is present."})

    from .governance import _lifecycle_events, STATES
    events = _lifecycle_events(workspace, identifier)
    latest = events[-1] if events else None
    if not latest or not isinstance(latest.get("owner"), str) or not latest["owner"].strip():
        blocked.append({"candidate_id": identifier, "check": "ownership",
                        "detail": "A lifecycle owner is required before approval."})
    else:
        passed.append({"candidate_id": identifier, "check": "ownership",
                       "detail": f"Lifecycle owner is {latest['owner']}."})
    state = latest.get("state") if latest else None
    audit_issues = [item for key in ("invalid_transitions", "missing_metadata", "orphaned_records", "inconsistent_states")
                    for item in audit[key] if item.get("candidate_id") == identifier]
    if state not in STATES or audit_issues:
        blocked.append({"candidate_id": identifier, "check": "lifecycle_state",
                        "detail": "Lifecycle state is missing or fails governance integrity checks.",
                        "state": state, "issues": audit_issues})
    elif state != "validated":
        blocked.append({"candidate_id": identifier, "check": "lifecycle_state",
                        "detail": "Approval requires a valid lifecycle in the validated state.", "state": state})
    else:
        passed.append({"candidate_id": identifier, "check": "lifecycle_state",
                       "detail": "Lifecycle integrity passed and state is validated."})

    validations = candidate.get("validations", [])
    latest_validation = validations[-1] if validations else None
    if (not latest_validation or not latest_validation.get("passed")
            or not isinstance(latest_validation.get("gates"), dict)
            or not latest_validation["gates"]
            or not all(latest_validation["gates"].values())):
        blocked.append({"candidate_id": identifier, "check": "validation_evidence",
                        "detail": "Approval requires persisted validation evidence with every gate passing."})
    else:
        passed.append({"candidate_id": identifier, "check": "validation_evidence",
                       "detail": "Latest persisted validation passed every gate.",
                       "validation_id": latest_validation.get("id")})

    decision = candidate.get("decision")
    rollback_required = state in {"accepted", "rolled_back"} or bool(decision and decision.get("status") == "accepted")
    if rollback_required:
        rollback = decision.get("rollback") if decision else None
        rollback_ok = (isinstance(rollback, dict) and bool(rollback.get("restore_to"))
                       and bool(rollback.get("instructions")))
        if state == "rolled_back":
            from .safety import _rollback_records
            rollback_ok = rollback_ok and bool(_rollback_records(workspace, identifier))
        if not rollback_ok:
            blocked.append({"candidate_id": identifier, "check": "rollback_information",
                            "detail": "Accepted or rolled-back candidates require a target and manual rollback instructions."})
        else:
            passed.append({"candidate_id": identifier, "check": "rollback_information",
                           "detail": "Required rollback target and instructions are present."})
    else:
        passed.append({"candidate_id": identifier, "check": "rollback_information",
                       "detail": "Rollback information is not required before a decision."})

    candidate_conflicts = [item for item in conflicts["conflicts"]
                           if identifier in item.get("candidates", [])]
    documented_note = (review or {}).get("conflict_note")
    if candidate_conflicts:
        if isinstance(documented_note, str) and documented_note.strip():
            warnings.append({"candidate_id": identifier, "check": "conflicts",
                             "detail": "Conflicts are documented for human review; this does not resolve them.",
                             "conflicts": candidate_conflicts, "documentation": documented_note})
        else:
            blocked.append({"candidate_id": identifier, "check": "conflicts",
                            "detail": "Optimization conflicts must be resolved or explicitly documented before approval.",
                            "conflicts": candidate_conflicts})
    else:
        passed.append({"candidate_id": identifier, "check": "conflicts",
                       "detail": "No unresolved optimization conflicts affect this candidate."})

    if not review:
        warnings.append({"candidate_id": identifier, "check": "review_record",
                         "detail": "No review queue record exists for this candidate."})
    return {"candidate_id": identifier, "status": "blocked" if blocked else "warnings" if warnings else "passed",
            "passed": passed, "warnings": warnings, "blocked": blocked}


def policy_check(workspace, identifier=None, conflict_note=None):
    """Read-only policy assessment; reports blockers without repairing records."""
    if conflict_note is not None and (not isinstance(conflict_note, str) or not conflict_note.strip()):
        raise LocalWorkflowError("A conflict note must be nonempty when supplied.")
    candidates = show_candidates(workspace, _name(identifier) if identifier else None)["candidates"]
    if not candidates:
        return {"mode": MODE, "passed": [], "warnings": [],
                "blocked": [{"check": "candidate_metadata", "detail": "No optimization candidates are available."}],
                "candidate_results": [], "automatic_changes": False}
    reviews = {item["candidate_id"]: item for item in _all_reviews(workspace)}
    audit = __import__("src.developer.governance", fromlist=["optimize_audit"]).optimize_audit(workspace)
    from .safety import detect_conflicts
    conflicts = detect_conflicts(workspace)
    results = []
    for candidate in candidates:
        review = reviews.get(candidate["id"])
        if conflict_note and review and review.get("candidate_id") == candidate["id"]:
            review = {**review, "conflict_note": conflict_note.strip()}
        results.append(_policy_for_candidate(workspace, candidate, review, conflicts, audit))
    return {"mode": MODE,
            "passed": [item for result in results for item in result["passed"]],
            "warnings": [item for result in results for item in result["warnings"]],
            "blocked": [item for result in results for item in result["blocked"]],
            "candidate_results": results, "automatic_changes": False}


def transition_review(workspace, identifier, status, reviewer, reason, conflict_note=None):
    if status not in REVIEW_STATES:
        raise LocalWorkflowError(f"Unknown review state '{status}'.")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise LocalWorkflowError("A review transition requires a nonempty reviewer.")
    if not isinstance(reason, str) or not reason.strip():
        raise LocalWorkflowError("A review transition requires a nonempty reason.")
    if conflict_note is not None and (not isinstance(conflict_note, str) or not conflict_note.strip()):
        raise LocalWorkflowError("A conflict note must be nonempty when supplied.")
    current = _resolve_review(workspace, identifier)
    if status not in REVIEW_TRANSITIONS.get(current["status"], set()):
        raise LocalWorkflowError(f"Invalid review transition from '{current['status']}' to '{status}'.")
    candidate = show_candidates(workspace, current["candidate_id"])["candidates"][0]
    lifecycle, findings, health = _candidate_context(workspace, candidate)
    recorded_at = max(datetime.now(timezone.utc),
                      datetime.fromisoformat(current["recorded_at"]).astimezone(timezone.utc)
                      + timedelta(microseconds=1)).isoformat()
    history = deepcopy(current["review_history"])
    event = {"sequence": current["sequence"] + 1, "status": status,
             "previous_status": current["status"], "reviewer": reviewer.strip(),
             "reason": reason.strip(),
             "conflict_note": conflict_note.strip() if conflict_note else current.get("conflict_note"),
             "recorded_at": recorded_at}
    history.append(event)
    updated = {key: deepcopy(value) for key, value in current.items()
               if key not in {"schema_version", "mode", "id", "recorded_at"}}
    updated.update({"sequence": current["sequence"] + 1, "status": status,
                    "reviewer": reviewer.strip(), "reason": reason.strip(),
                    "conflict_note": event["conflict_note"],
                    "validation_summary": _validation_summary(candidate),
                    "related_candidate_history": deepcopy(candidate["history"]),
                    "candidate_lifecycle_history": lifecycle,
                    "maintenance_findings": findings,
                    "governance_health_status": health["health_status"],
                    "review_history": history})
    return _write_event(workspace, updated, recorded_at)


def approve_review(workspace, identifier, reviewer, reason, conflict_note=None):
    current = _resolve_review(workspace, identifier)
    if current["status"] != "pending":
        raise LocalWorkflowError("Only a pending review can be approved.")
    policy = policy_check(workspace, current["candidate_id"], conflict_note)
    if policy["blocked"]:
        checks = sorted({item["check"] for item in policy["blocked"]})
        raise LocalWorkflowError("Review approval is blocked by policy checks: " + ", ".join(checks) + ".")
    return transition_review(workspace, identifier, "approved", reviewer, reason, conflict_note)


def reject_review(workspace, identifier, reviewer, reason):
    current = _resolve_review(workspace, identifier)
    if current["status"] != "pending":
        raise LocalWorkflowError("Only a pending review can be rejected.")
    return transition_review(workspace, identifier, "rejected", reviewer, reason)


def defer_review(workspace, identifier, reviewer, reason):
    return transition_review(workspace, identifier, "deferred", reviewer, reason)


def withdraw_review(workspace, identifier, reviewer, reason):
    return transition_review(workspace, identifier, "withdrawn", reviewer, reason)


def reopen_review(workspace, identifier, reviewer, reason):
    return transition_review(workspace, identifier, "pending", reviewer, reason)
