"""Phase 41 developer-only optimization governance: lifecycle, ownership and maintenance.

Nothing here reads or writes research, benchmark, Humanize or release paths, and no
optimization candidate is deleted or auto-modified. Lifecycle records are immutable,
append-only history entries stored inside the developer workspace only.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from uuid import uuid4

from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read, _storage, show_candidates

SCHEMA = "developer-governance-v1"
MODE = "developer-local-governance"

STATES = ("proposed", "experimenting", "validated", "accepted", "rejected", "rolled_back", "archived")
TRANSITIONS = {
    "proposed": {"experimenting", "archived"},
    "experimenting": {"validated", "rejected", "archived"},
    "validated": {"accepted", "rejected", "archived"},
    "accepted": {"rolled_back", "archived"},
    "rejected": {"archived"},
    "rolled_back": {"archived"},
    "archived": set(),
}
STALE_AGE = timedelta(days=30)


def _write(workspace, path, document, recorded_at=None):
    path = workspace._contained(path)
    document = {"schema_version": SCHEMA, "mode": MODE,
                "recorded_at": (recorded_at or datetime.now(timezone.utc)).isoformat(), **document}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(_json_bytes(document))
    except FileExistsError as error:
        raise LocalWorkflowError("Lifecycle event already exists; record a new transition instead.") from error
    return document


def _timestamp(value):
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _age(value, now):
    try:
        return now - _timestamp(value)
    except (TypeError, ValueError):
        return None


def _history_time(value):
    try:
        return _timestamp(value)
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)


def _lifecycle_events(workspace, identifier):
    directory = _storage(workspace, identifier) / "lifecycle"
    if not directory.exists():
        return []
    return sorted((_read(workspace, path) for path in directory.glob("*.json")),
                  key=lambda item: (item.get("sequence") if type(item.get("sequence")) is int else -1,
                                    str(item.get("recorded_at", "")), str(item.get("id", ""))))


def register_candidate(workspace, identifier, owner, purpose, affected_cases):
    candidate = show_candidates(workspace, identifier)["candidates"][0]
    if _lifecycle_events(workspace, identifier):
        raise LocalWorkflowError(f"Candidate '{identifier}' already has a recorded lifecycle; use transition instead.")
    if not isinstance(owner, str) or not owner.strip():
        raise LocalWorkflowError("Lifecycle registration requires a nonempty owner.")
    if not isinstance(purpose, str) or not purpose.strip():
        raise LocalWorkflowError("Lifecycle registration requires a nonempty purpose.")
    cases = sorted({value for value in (affected_cases or [])})
    if not cases or any(not isinstance(value, str) or not value.strip() for value in cases):
        raise LocalWorkflowError("Lifecycle registration requires at least one affected case.")
    if not set(cases) <= set(candidate["cases"]):
        raise LocalWorkflowError("Affected cases must be a subset of the candidate's recorded cases.")
    event_id = uuid4().hex
    return _write(workspace, _storage(workspace, identifier) / "lifecycle" / f"{event_id}.json", {
        "id": event_id, "candidate_id": identifier, "sequence": 1, "state": "proposed", "previous_state": None,
        "owner": owner.strip(), "purpose": purpose.strip(), "affected_cases": cases,
        "note": "Candidate registered for lifecycle tracking.", "last_validation_at": None})


def transition_candidate(workspace, identifier, state, note, last_validation_at=None, owner=None):
    if state not in STATES:
        raise LocalWorkflowError(f"Unknown lifecycle state '{state}'.")
    if not isinstance(note, str) or not note.strip():
        raise LocalWorkflowError("Lifecycle transitions require a nonempty note.")
    events = _lifecycle_events(workspace, identifier)
    if not events:
        raise LocalWorkflowError(f"Candidate '{identifier}' has no recorded lifecycle; register it first.")
    current = events[-1]
    if state not in TRANSITIONS.get(current["state"], set()):
        raise LocalWorkflowError(f"Invalid lifecycle transition from '{current['state']}' to '{state}'.")
    if state == "validated":
        if not isinstance(last_validation_at, str) or not last_validation_at.strip():
            raise LocalWorkflowError("Validated lifecycle transitions require --last-validation-at.")
        try:
            datetime.fromisoformat(last_validation_at)
        except ValueError as error:
            raise LocalWorkflowError("Validation timestamp must be ISO-8601.") from error
    if owner is not None and (not isinstance(owner, str) or not owner.strip()):
        raise LocalWorkflowError("A changed owner must be nonempty text.")
    next_recorded_at = max(datetime.now(timezone.utc),
                           _timestamp(current["recorded_at"]) + timedelta(microseconds=1))
    next_owner = current["owner"] if owner is None else owner.strip()
    event_id = uuid4().hex
    event = {
        "id": event_id, "candidate_id": identifier, "sequence": current["sequence"] + 1,
        "state": state, "previous_state": current["state"], "owner": next_owner,
        "previous_owner": current["owner"] if next_owner != current["owner"] else None,
        "purpose": current["purpose"],
        "affected_cases": current["affected_cases"], "note": note.strip(),
        "last_validation_at": last_validation_at if state == "validated" else current["last_validation_at"]}
    return _write(workspace, _storage(workspace, identifier) / "lifecycle" / f"{event_id}.json",
                  event, recorded_at=next_recorded_at)


def _summarize(workspace, identifier):
    events = _lifecycle_events(workspace, identifier)
    if not events:
        return None
    first, last = events[0], events[-1]
    return {"candidate_id": identifier, "state": last.get("state"), "owner": last.get("owner"),
            "purpose": last.get("purpose"), "affected_cases": last.get("affected_cases", []),
            "created_at": first.get("recorded_at"), "updated_at": last.get("recorded_at"),
            "last_validation_at": last.get("last_validation_at"),
            "history": [{"sequence": event.get("sequence"), "state": event.get("state"),
                        "previous_state": event.get("previous_state"), "note": event.get("note"),
                        "recorded_at": event.get("recorded_at")} for event in events]}


def show_lifecycle(workspace, identifier=None):
    workspace._prepare()
    if identifier:
        summary = _summarize(workspace, identifier)
        if summary is None:
            raise LocalWorkflowError(f"Candidate '{identifier}' has no recorded lifecycle; register it first.")
        return {"mode": MODE, "candidates": [summary]}
    root = workspace._contained(workspace.root / "optimization" / "candidates")
    identifiers = sorted({path.parents[1].name for path in root.glob("*/lifecycle/*.json")})
    return {"mode": MODE, "candidates": [_summarize(workspace, value) for value in identifiers]}


def archive_candidate(workspace, identifier, note):
    return transition_candidate(workspace, identifier, "archived", note)


def _issue(candidate_id, detail, **extra):
    return {"candidate_id": candidate_id, "detail": detail, **extra}


def _maintenance_issue(workspace, kind, severity, candidate_ids, detail, recommendation):
    candidate_ids = sorted(set(candidate_ids))
    related = []
    for identifier in candidate_ids:
        try:
            events = _lifecycle_events(workspace, identifier)
        except (LocalWorkflowError, KeyError, TypeError, ValueError):
            events = []
        if events:
            event = events[-1]
            related.append({"candidate_id": identifier, "event_id": event.get("id"),
                            "sequence": event.get("sequence"), "state": event.get("state"),
                            "recorded_at": event.get("recorded_at")})
    return {"issue": kind, "type": kind, "severity": severity,
            "candidate_id": candidate_ids[0] if len(candidate_ids) == 1 else None,
            "affected_candidate_ids": candidate_ids, "candidate_ids": candidate_ids,
            "detail": detail, "recommendation": recommendation,
            "related_lifecycle_events": related}


def optimize_audit(workspace):
    """Inspect lifecycle record integrity without repairing or changing records."""
    workspace._prepare()
    buckets = {name: [] for name in ("invalid_transitions", "missing_metadata",
                                     "duplicate_history_entries", "orphaned_records",
                                     "inconsistent_states")}
    root = workspace._contained(workspace.root / "optimization" / "candidates")
    candidate_paths = {}
    lifecycle_paths = {}
    for directory in sorted(root.glob("*")):
        try:
            workspace._contained(directory)
            if not directory.is_dir():
                continue
            candidate_path = workspace._contained(directory / "candidate.json")
            if candidate_path.is_file():
                candidate_paths[directory.name] = candidate_path
            lifecycle_dir = workspace._contained(directory / "lifecycle")
            if lifecycle_dir.exists():
                lifecycle_paths[directory.name] = sorted(lifecycle_dir.glob("*.json"))
        except (OSError, LocalWorkflowError) as error:
            buckets["orphaned_records"].append(_issue(directory.name, f"Record path is unsafe: {error}"))

    for identifier, paths in lifecycle_paths.items():
        if identifier not in candidate_paths:
            buckets["orphaned_records"].append(_issue(identifier, "Lifecycle history has no candidate.json."))
        records = []
        for path in paths:
            try:
                record = _read(workspace, path)
            except LocalWorkflowError as error:
                buckets["inconsistent_states"].append(_issue(identifier, str(error), record=str(path.name)))
                continue
            records.append((path, record))
        ids = [json.dumps(record.get("id"), sort_keys=True) for _, record in records if record.get("id") is not None]
        sequences = [record.get("sequence") for _, record in records if type(record.get("sequence")) is int]
        for duplicate_id, count in Counter(ids).items():
            if count > 1:
                buckets["duplicate_history_entries"].append(_issue(identifier, "Duplicate lifecycle event ID.", event_id=duplicate_id))
        for sequence, count in Counter(sequences).items():
            if count > 1:
                buckets["duplicate_history_entries"].append(_issue(identifier, "Duplicate lifecycle sequence number.", sequence=sequence))
        signatures = Counter(json.dumps([record.get("sequence"), record.get("state"), record.get("previous_state"),
                         record.get("owner"), record.get("note")], sort_keys=True)
                     for _, record in records)
        for signature, count in signatures.items():
            if count > 1:
                buckets["duplicate_history_entries"].append(_issue(
                    identifier, "Duplicate lifecycle event content.", signature=signature))
        records.sort(key=lambda pair: (
            pair[1].get("sequence") if type(pair[1].get("sequence")) is int else -1,
            str(pair[1].get("recorded_at", "")), pair[0].name))
        previous = None
        for index, (path, record) in enumerate(records, start=1):
            required = ("schema_version", "mode", "recorded_at", "id", "candidate_id", "sequence", "state",
                        "previous_state", "owner", "purpose", "affected_cases", "note", "last_validation_at")
            missing = [key for key in required if key not in record or record[key] is None and key not in {"previous_state", "last_validation_at"}]
            for key in ("owner", "purpose"):
                if not isinstance(record.get(key), str) or not record[key].strip():
                    if key not in missing:
                        missing.append(key)
            if missing:
                buckets["missing_metadata"].append(_issue(identifier, "Required lifecycle metadata is missing or empty.",
                                                           record=path.name, fields=sorted(set(missing))))
            if record.get("schema_version") != SCHEMA or record.get("mode") != MODE:
                buckets["inconsistent_states"].append(_issue(identifier, "Lifecycle schema or mode is inconsistent.", record=path.name))
            if record.get("candidate_id") != identifier:
                buckets["orphaned_records"].append(_issue(identifier, "Lifecycle candidate_id does not match its directory.", record=path.name))
            if record.get("sequence") != index:
                buckets["inconsistent_states"].append(_issue(identifier, "Lifecycle sequence is not contiguous from 1.",
                                                              record=path.name, expected=index, actual=record.get("sequence")))
            try:
                _timestamp(record["recorded_at"])
            except (KeyError, TypeError, ValueError):
                buckets["missing_metadata"].append(_issue(identifier, "Lifecycle timestamp is missing or invalid.", record=path.name))
            state = record.get("state")
            if state not in STATES:
                buckets["inconsistent_states"].append(_issue(identifier, "Unknown lifecycle state.", record=path.name, state=state))
            elif previous is None:
                if state != "proposed" or record.get("previous_state") is not None:
                    buckets["invalid_transitions"].append(_issue(identifier, "Lifecycle must begin in proposed with no previous state.", record=path.name))
            else:
                if record.get("previous_state") != previous.get("state"):
                    buckets["inconsistent_states"].append(_issue(identifier, "previous_state does not match the prior event.", record=path.name))
                previous_state = previous.get("state")
                allowed = TRANSITIONS.get(previous_state, set()) if isinstance(previous_state, str) else set()
                if state not in allowed:
                    buckets["invalid_transitions"].append(_issue(identifier, "Recorded lifecycle transition is not allowed.",
                                                                  record=path.name, from_state=previous_state, to_state=state))
                prior_time = previous.get("recorded_at")
                try:
                    if _timestamp(record["recorded_at"]) <= _timestamp(prior_time):
                        buckets["inconsistent_states"].append(_issue(identifier, "Lifecycle timestamps are not strictly increasing.", record=path.name))
                except (KeyError, TypeError, ValueError):
                    pass
            if state == "validated":
                try:
                    _timestamp(record["last_validation_at"])
                except (KeyError, TypeError, ValueError):
                    buckets["missing_metadata"].append(_issue(identifier, "Validated event lacks a valid validation timestamp.", record=path.name))
            if record.get("previous_owner") is not None and record.get("previous_owner") == record.get("owner"):
                buckets["inconsistent_states"].append(_issue(identifier, "Ownership change records the same previous and current owner.", record=path.name))
            previous = record

        if identifier in candidate_paths and records:
            try:
                candidate = _read(workspace, candidate_paths[identifier])
                state = records[-1][1].get("state")
                decision_path = workspace._contained(candidate_paths[identifier].parent / "decision.json")
                decision = _read(workspace, decision_path) if decision_path.exists() else None
                if state == "accepted" and (not decision or decision.get("status") != "accepted"):
                    buckets["inconsistent_states"].append(_issue(identifier, "Lifecycle is accepted but candidate decision is not accepted."))
                if state == "rejected" and (not decision or decision.get("status") != "rejected"):
                    buckets["inconsistent_states"].append(_issue(identifier, "Lifecycle is rejected but candidate decision is not rejected."))
                rollback_dir = workspace._contained(candidate_paths[identifier].parent / "rollback")
                has_rollback = rollback_dir.exists() and any(rollback_dir.glob("*.json"))
                if state == "rolled_back" and not has_rollback:
                    buckets["inconsistent_states"].append(_issue(identifier, "Lifecycle is rolled_back without a rollback record."))
                if state == "validated":
                    validations = workspace._contained(candidate_paths[identifier].parent / "validations")
                    validation_records = ([_read(workspace, path) for path in validations.glob("*.json")]
                                          if validations.exists() else [])
                    validation_records.sort(key=lambda record: (str(record.get("recorded_at", "")),
                                                                 str(record.get("id", ""))))
                    if not validation_records:
                        buckets["inconsistent_states"].append(_issue(identifier, "Lifecycle is validated without a validation record."))
                    else:
                        try:
                            timestamp_matches = any(
                                _timestamp(record.get("recorded_at")) == _timestamp(records[-1][1].get("last_validation_at"))
                                for record in validation_records)
                        except (TypeError, ValueError):
                            timestamp_matches = False
                        if not timestamp_matches:
                            buckets["inconsistent_states"].append(_issue(
                                identifier, "Lifecycle validation timestamp does not match a persisted validation record."))
                if state == "accepted":
                    validations = workspace._contained(candidate_paths[identifier].parent / "validations")
                    latest_validations = ([_read(workspace, path) for path in validations.glob("*.json")]
                                          if validations.exists() else [])
                    latest_validations.sort(key=lambda record: (str(record.get("recorded_at", "")),
                                                                 str(record.get("id", ""))))
                    if not latest_validations or not latest_validations[-1].get("passed"):
                        buckets["inconsistent_states"].append(_issue(
                            identifier, "Accepted lifecycle lacks a passing optimization validation."))
                if candidate.get("schema_version") != "developer-optimization-v1":
                    buckets["inconsistent_states"].append(_issue(identifier, "Candidate schema is inconsistent with the optimization workflow."))
            except LocalWorkflowError as error:
                buckets["orphaned_records"].append(_issue(identifier, f"Candidate linkage cannot be inspected: {error}"))

    for name in ("validations", "rollback", "lifecycle"):
        for path in root.glob(f"*/{name}/*.json"):
            if path.parent.parent.name not in candidate_paths and name != "lifecycle":
                buckets["orphaned_records"].append(_issue(path.parent.parent.name, f"Orphaned {name} record.", record=path.name))
    for path in root.glob("*/decision.json"):
        if path.parent.name not in candidate_paths:
            buckets["orphaned_records"].append(_issue(path.parent.name, "Orphaned decision record.", record=path.name))
    issues = [item for name in buckets for item in buckets[name]]
    return {"mode": MODE, "audit_status": "clean" if not issues else "issues_found",
            "issues": issues, **buckets}


def optimize_history(workspace, identifier):
    """Return an immutable, chronological view of a candidate's developer records."""
    candidate = show_candidates(workspace, identifier)["candidates"][0]
    directory = _storage(workspace, identifier)
    entries = []

    def add(kind, record):
        timestamp = record.get("recorded_at")
        if not isinstance(timestamp, str):
            return
        entries.append({"event_type": kind, "recorded_at": timestamp, "record_id": record.get("id"),
                        "immutable": True, "record": record})

    add("candidate_created", _read(workspace, directory / "candidate.json"))
    lifecycle = _lifecycle_events(workspace, identifier)
    prior_owner = None
    for event in lifecycle:
        if prior_owner is not None and event.get("owner") != prior_owner:
            add("ownership_changed", {**event, "previous_owner": prior_owner})
        add("archived" if event.get("state") == "archived" else "lifecycle", event)
        prior_owner = event.get("owner")
    validations = workspace._contained(directory / "validations")
    if validations.exists():
        for path in validations.glob("*.json"):
            add("validation", _read(workspace, path))
    decision = workspace._contained(directory / "decision.json")
    if decision.exists():
        add("decision", _read(workspace, decision))
    rollback = workspace._contained(directory / "rollback")
    if rollback.exists():
        for path in rollback.glob("*.json"):
            add("rollback", _read(workspace, path))
    entries.sort(key=lambda item: (_history_time(item["recorded_at"]), item["event_type"], item["record_id"] or ""))
    return {"mode": MODE, "candidate_id": identifier, "history": entries,
            "ordering": "recorded_at ascending; lifecycle sequence is retained in each immutable record"}


def optimize_status(workspace):
    summaries = show_lifecycle(workspace)["candidates"]
    buckets = {"active": [], "validated": [], "accepted": [], "rejected": [], "rolled_back": [], "archived": [], "stale": []}
    now = datetime.now(timezone.utc)
    for item in summaries:
        state = item.get("state")
        if isinstance(state, str) and state in {"proposed", "experimenting"}:
            buckets["active"].append(item)
            age = _age(item.get("updated_at"), now)
            if age is not None and age > STALE_AGE:
                buckets["stale"].append(item)
        elif isinstance(state, str) and state in buckets:
            buckets[state].append(item)
    return {"mode": MODE, **buckets}


def optimize_summary(workspace, recent_limit=20):
    """Summarize lifecycle and conflict state without scoring or ranking candidates."""
    if type(recent_limit) is not int or not 1 <= recent_limit <= 1000:
        raise LocalWorkflowError("Recent lifecycle activity limit must be an integer from 1 to 1000.")
    candidates = show_candidates(workspace)["candidates"]
    state_counts = {state: 0 for state in STATES}
    untracked = []
    pending_reviews = []
    archived = []
    activity = []
    for candidate in candidates:
        events = _lifecycle_events(workspace, candidate["id"])
        state = events[-1].get("state") if events else None
        if isinstance(state, str) and state in state_counts:
            state_counts[state] += 1
        else:
            untracked.append(candidate["id"])
        if (state == "validated" or candidate.get("status") == "validated") and not candidate.get("decision"):
            pending_reviews.append(candidate["id"])
        if state == "archived":
            archived.append({"candidate_id": candidate["id"], "owner": events[-1].get("owner"),
                             "recorded_at": events[-1].get("recorded_at")})
        for event in events:
            activity.append({"candidate_id": candidate["id"], "event_id": event.get("id"),
                             "sequence": event.get("sequence"), "state": event.get("state"),
                             "previous_state": event.get("previous_state"),
                             "owner": event.get("owner"), "note": event.get("note"),
                             "recorded_at": event.get("recorded_at")})
    activity.sort(key=lambda event: (_history_time(event.get("recorded_at")),
                                     event.get("candidate_id", ""), event.get("sequence", 0)))
    maintenance = maintenance_report(workspace)
    from .safety import detect_conflicts
    conflicts = detect_conflicts(workspace)
    stale_items = [*maintenance["stale_candidates"], *maintenance["stale_accepted_candidates"]]
    return {
        "mode": MODE,
        "summary": {
            "candidate_state_counts": state_counts,
            "untracked_candidate_count": len(untracked),
            "untracked_candidate_ids": sorted(untracked),
            "candidate_records_total": len(candidates),
            "recent_lifecycle_activity": list(reversed(activity[-recent_limit:])),
            "pending_review_candidate_ids": sorted(set(pending_reviews)),
            "pending_review_count": len(set(pending_reviews)),
            "stale_items": stale_items,
            "archived_items": sorted(archived, key=lambda item: item["candidate_id"]),
            "unresolved_conflicts": conflicts["conflicts"],
            "unresolved_conflict_count": len(conflicts["conflicts"]),
        },
    }


def maintenance_report(workspace):
    from .safety import detect_conflicts, show_rollback
    audit = optimize_audit(workspace)
    candidates = show_candidates(workspace)["candidates"]
    summaries = []
    for candidate in candidates:
        try:
            summary = _summarize(workspace, candidate["id"])
        except (LocalWorkflowError, KeyError, TypeError, ValueError):
            continue
        if summary is not None:
            summaries.append(summary)
    now = datetime.now(timezone.utc)
    candidates_by_id = {item["id"]: item for item in candidates}
    registered_ids = {item["candidate_id"] for item in summaries}
    unregistered_candidates = [
        {"candidate_id": candidate["id"], "optimization_status": candidate["status"]}
        for candidate in candidates if candidate["id"] not in registered_ids]
    stale_candidates = []
    abandoned_experiments = []
    stale_accepted_candidates = []
    for item in summaries:
        age = _age(item.get("updated_at"), now)
        state = item.get("state")
        details = {"candidate_id": item["candidate_id"], "state": state,
                   "owner": item.get("owner"), "updated_at": item.get("updated_at"),
                   "days_since_update": age.days if age is not None else None}
        if isinstance(state, str) and state in {"proposed", "experimenting"} and age is not None and age > STALE_AGE:
            stale_candidates.append(details)
        if state == "experimenting" and age is not None and age > STALE_AGE:
            abandoned_experiments.append(details)
        if state == "accepted":
            validation_at = item.get("last_validation_at")
            validation_age = _age(validation_at, now)
            if validation_age is None or validation_age > STALE_AGE:
                stale_accepted_candidates.append({**details, "last_validation_at": validation_at,
                                                  "days_since_validation": validation_age.days if validation_age else None})

    metadata_issues = list(audit["missing_metadata"])
    incomplete_validation_records = []
    for item in summaries:
        candidate = candidates_by_id.get(item["candidate_id"], {})
        if isinstance(item.get("state"), str) and item["state"] in {"validated", "accepted"}:
            if not candidate.get("validations"):
                incomplete_validation_records.append(_issue(item["candidate_id"],
                    "Lifecycle claims validation but no optimization validation record exists."))
            elif not item.get("last_validation_at"):
                incomplete_validation_records.append(_issue(item["candidate_id"],
                    "Lifecycle validation timestamp is missing."))
            elif item["state"] == "accepted" and not candidate["validations"][-1].get("passed"):
                incomplete_validation_records.append(_issue(item["candidate_id"],
                    "Accepted lifecycle has a latest validation that did not pass."))
    metadata_issues.extend(incomplete_validation_records)

    archived_active_references = []
    for item in summaries:
        if item.get("state") != "archived":
            continue
        referencing = [candidate["id"] for candidate in candidates
                       if candidate.get("supersedes") == item["candidate_id"]
                       and candidate["status"] in {"candidate", "validated"}]
        if referencing:
            archived_active_references.append({"candidate_id": item["candidate_id"],
                                               "referenced_by": sorted(referencing)})

    conflicts = detect_conflicts(workspace)
    duplicates = [item for item in conflicts["conflicts"] if item["type"] == "duplicate_attempt"]
    maintenance_notes = [f"Repeated failed experiments: {', '.join(warning['candidates'])} — {warning['detail']}"
                         for warning in conflicts["warnings"] if warning["type"] == "repeated_failed_experiments"]
    for report in show_rollback(workspace)["candidates"]:
        if report["rollback_available"] and not report["rollback_records"]:
            maintenance_notes.append(
                f"Candidate '{report['candidate_id']}' is accepted with an unused rollback state; "
                "no rollback has been recorded.")
    findings = []
    for item in unregistered_candidates:
        findings.append(_maintenance_issue(workspace, "governance_not_registered", "warning", [item["candidate_id"]],
            "Optimization candidate has no lifecycle ownership record.",
            "Register lifecycle ownership if governance tracking is required; existing decisions remain unchanged."))
    for item in stale_candidates:
        findings.append(_maintenance_issue(workspace, "stale_candidate", "warning", [item["candidate_id"]],
            f"Lifecycle has not changed for {item['days_since_update']} days.", "Review candidate history and decide whether work should continue."))
    for item in abandoned_experiments:
        findings.append(_maintenance_issue(workspace, "abandoned_experiment", "warning", [item["candidate_id"]],
            f"Experimenting lifecycle has had no update for {item['days_since_update']} days.", "Review the latest lifecycle event with the owner."))
    for item in incomplete_validation_records:
        findings.append(_maintenance_issue(workspace, "incomplete_validation", "error", [item["candidate_id"]],
            item["detail"], "Inspect validation records; only record a lifecycle decision after human review."))
    for item in metadata_issues:
        fields = item.get("fields", [])
        candidate_id = item.get("candidate_id")
        findings.append(_maintenance_issue(workspace, "missing_metadata", "error", [candidate_id] if candidate_id else [],
            item["detail"], "Review the referenced lifecycle event and supply missing ownership/metadata through a new valid event; do not edit history."))
    for item in stale_accepted_candidates:
        findings.append(_maintenance_issue(workspace, "stale_accepted_candidate", "warning", [item["candidate_id"]],
            "Accepted candidate has stale or missing validation freshness metadata.", "Review the validation and candidate history; do not infer current behavior from an old acceptance."))
    for item in archived_active_references:
        findings.append(_maintenance_issue(workspace, "archived_active_reference", "warning",
            [item["candidate_id"], *item["referenced_by"]], "An unresolved candidate still supersedes an archived candidate.",
            "Review the lineage and decide manually whether the active attempt is still intended."))
    for conflict in conflicts["conflicts"]:
        findings.append(_maintenance_issue(workspace, conflict["type"], "warning", conflict["candidates"],
            conflict["detail"], "Review the conflicting candidates, affected cases and their histories; do not resolve automatically."))
    for warning in conflicts["warnings"]:
        findings.append(_maintenance_issue(workspace, warning["type"], "warning",
            warning["candidates"], warning["detail"], "Review the candidate chain and record a human decision when appropriate."))
    audit_severity = {"invalid_transitions": "error", "missing_metadata": "error",
                      "duplicate_history_entries": "warning", "orphaned_records": "error",
                      "inconsistent_states": "error"}
    audit_recommendations = {
        "invalid_transitions": "Inspect lifecycle sequence and preserve the original events; do not repair automatically.",
        "missing_metadata": "Review the named record and document any correction as a new workflow event where supported.",
        "duplicate_history_entries": "Inspect duplicate sequence/event IDs and preserve all original evidence.",
        "orphaned_records": "Review candidate-directory linkage and workspace containment before taking manual action.",
        "inconsistent_states": "Compare lifecycle, validation, decision and rollback records; resolve only through the supported workflow.",
    }
    for category, items in audit.items():
        if category not in audit_severity:
            continue
        for item in items:
            findings.append(_maintenance_issue(workspace, category, audit_severity[category],
                [item["candidate_id"]] if item.get("candidate_id") else [], item["detail"], audit_recommendations[category]))
    severity_order = {"error": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda item: (severity_order[item["severity"]], item["issue"],
                                    item["candidate_ids"], item["detail"]))
    recommendations = []
    recommendations.extend(item["recommendation"] for item in findings)
    recommendations.extend(maintenance_notes)
    return {"mode": MODE, "stale_candidates": stale_candidates, "duplicates": duplicates,
            "unregistered_candidates": unregistered_candidates,
            "abandoned_experiments": abandoned_experiments,
            "incomplete_validation_records": incomplete_validation_records,
            "missing_ownership_fields": [item for item in metadata_issues
                                         if "owner" in item.get("fields", []) or "purpose" in item.get("fields", [])],
            "stale_accepted_candidates": stale_accepted_candidates,
            "archived_active_references": archived_active_references,
            "metadata_issues": metadata_issues, "recommendations": recommendations,
            "maintenance_notes": maintenance_notes,
            "findings": findings,
            "automatic_changes": False}


def optimize_health(workspace):
    """Run a complete, non-mutating governance integrity and maintenance check."""
    audit = optimize_audit(workspace)
    maintenance = maintenance_report(workspace)
    from .safety import detect_conflicts
    conflicts = detect_conflicts(workspace)
    lifecycle_issues = [*audit["invalid_transitions"], *audit["inconsistent_states"], *audit["orphaned_records"]]
    metadata_issues = [*audit["missing_metadata"], *maintenance["incomplete_validation_records"]]
    lifecycle_passed = not lifecycle_issues
    metadata_passed = not metadata_issues
    archive_issues = maintenance["archived_active_references"]
    warning_findings = [item for item in maintenance["findings"] if item["severity"] == "warning"]
    if not lifecycle_passed or not metadata_passed:
        status = "issues_found"
    elif warning_findings or conflicts["conflicts"]:
        status = "warnings"
    else:
        status = "clean"
    return {
        "mode": MODE,
        "health_status": status,
        "checks": {
            "lifecycle": {"status": "passed" if lifecycle_passed else "failed", "issues": lifecycle_issues},
            "metadata": {"status": "passed" if metadata_passed else "failed", "issues": metadata_issues},
            "maintenance": {"status": "warnings" if warning_findings else "passed",
                            "warnings": warning_findings, "stale_candidates": maintenance["stale_candidates"],
                            "stale_accepted_candidates": maintenance["stale_accepted_candidates"]},
            "conflicts": {"status": "warnings" if conflicts["conflicts"] else "passed",
                          "unresolved_conflicts": conflicts["conflicts"],
                          "warnings": conflicts["warnings"]},
            "archive_consistency": {"status": "warnings" if archive_issues else "passed", "issues": archive_issues},
        },
        "issues": maintenance["findings"],
        "automatic_changes": False,
    }


def create_governance_checkpoint(workspace):
    """Append an immutable health snapshot under the developer workspace."""
    workspace._prepare()
    health = optimize_health(workspace)
    summary = optimize_summary(workspace)["summary"]
    identifier = uuid4().hex
    record = {
        "schema_version": "developer-governance-checkpoint-v1",
        "mode": "developer-local-governance-checkpoint",
        "id": identifier,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "health_status": health["health_status"],
        "detected_issues": health["issues"],
        "candidate_state_counts": summary["candidate_state_counts"],
        "untracked_candidate_count": summary["untracked_candidate_count"],
    }
    path = workspace._contained(workspace.root / "optimization" / "governance-checkpoints" / f"{identifier}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(_json_bytes(record))
    except FileExistsError as error:
        raise LocalWorkflowError("Governance checkpoint already exists; create a new checkpoint instead.") from error
    return {**record, "path": str(path)}
