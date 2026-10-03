"""Manual recovery assurance reviews and operational findings, outside research."""
from copy import deepcopy
import os
import tempfile

from . import assurance, continuity, recovery_governance as governance, reliability
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read
from .read_context import operation_scoped_load

MODE = "developer-assurance-operations"
STATES = {"open": {"reviewing"}, "reviewing": {"improved", "accepted"},
          "improved": {"reviewing", "closed"}, "accepted": {"reviewing", "closed"}, "closed": set()}
_now = assurance._now


def _root(workspace):
    governance._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "assurance-operations")


def _resolve(state, identifier):
    for record in state["operations"]:
        if record["operation_id"] == identifier:
            return record
    raise LocalWorkflowError("Unknown assurance operation ID.")


def _severity(key):
    if key.startswith("recovery_reference:") or key.endswith("unavailable") or key == "verification_not_passed":
        return "high"
    return "info" if key.startswith("lifecycle:") else "warning"


def _observe(state, record, event):
    report = event["review"]
    if report["assurance_id"] != record["assurance_id"] or report["record"]["assurance_id"] != record["assurance_id"]:
        raise ValueError("Review belongs to a different assurance")
    keys = report["findings"]
    if not isinstance(keys, list) or any(not isinstance(k, str) or not k.strip() for k in keys) or len(set(keys)) != len(keys):
        raise ValueError("Invalid review findings")
    reviewed = {"review_id": f"{record['operation_id']}-review-{len(record['reviews']) + 1:03d}",
                "sequence": event["sequence"], "created_at": event["created_at"], "actor": event["actor"],
                "reason": event["reason"], "snapshot": deepcopy(report), "new_findings": [],
                "resolved_findings": [], "repeated_findings": [], "reopened_findings": []}
    existing = {f["key"]: f for f in state["findings"] if f["assurance_id"] == record["assurance_id"]}
    for key in keys:
        finding = existing.get(key)
        if finding is None:
            finding = {"finding_id": f"{record['assurance_id']}:{key}", "key": key,
                       "assurance_id": record["assurance_id"], "description": governance._manual_action(key),
                       "severity": _severity(key), "first_seen": event["created_at"], "last_seen": event["created_at"],
                       "status": "open", "related_operations": [], "observations": []}
            state["findings"].append(finding)
            reviewed["new_findings"].append(finding["finding_id"])
        else:
            reviewed["repeated_findings"].append(finding["finding_id"])
            if finding["status"] == "resolved":
                reviewed["reopened_findings"].append(finding["finding_id"])
        finding["status"] = "open"
        finding["last_seen"] = event["created_at"]
        _finding_history(finding, record, reviewed, "observed")
    complete = not report["missing_evidence"] and not any(key.endswith("unavailable") for key in keys)
    for key, finding in existing.items():
        if complete and key not in keys and finding["status"] == "open":
            finding["status"] = "resolved"
            reviewed["resolved_findings"].append(finding["finding_id"])
            _finding_history(finding, record, reviewed, "resolved")
    record["reviews"].append(reviewed)
    record["last_reviewed"] = event["created_at"]
    record["status"] = "reviewing"


def _finding_history(finding, record, review, status):
    if record["operation_id"] not in finding["related_operations"]:
        finding["related_operations"].append(record["operation_id"])
    finding["observations"].append({"sequence": review["sequence"], "review_id": review["review_id"],
        "operation_id": record["operation_id"], "created_at": review["created_at"], "status": status})


def _apply(state, event):
    for key in ("actor", "reason", "operation_id"):
        reliability._text(event[key])
    assurance._timestamp(event["created_at"])
    action = event["action"]
    if action == "create":
        if event["operation_id"] != f"operation-{len(state['operations']) + 1:03d}":
            raise ValueError("Invalid operation ID")
        source = event["assurance_snapshot"]
        reliability._text(source["assurance_id"])
        reliability._text(source["scenario_id"])
        reliability._text(event["owner"])
        record = {"operation_id": event["operation_id"], "assurance_id": source["assurance_id"],
                  "owner": event["owner"], "status": "open", "created_at": event["created_at"],
                  "last_reviewed": None, "history": [], "reviews": [], "improvement_notes": [],
                  "assurance_snapshot": deepcopy(source)}
        state["operations"].append(record)
        previous = None
    else:
        record = _resolve(state, event["operation_id"])
        previous = record["status"]
        if previous == "closed":
            raise ValueError("Closed operations are immutable; create a new operation")
        if action == "review":
            _observe(state, record, event)
        elif action == "transition":
            if event["status"] not in STATES[previous]:
                raise ValueError(f"Invalid operation transition: {previous} -> {event['status']}")
            if event["status"] in {"improved", "accepted"} and not record["reviews"]:
                raise ValueError("Record a review before declaring an outcome")
            if event["status"] == "improved" and record["reviews"][-1]["snapshot"]["findings"]:
                raise ValueError("Improved requires a recorded review without unresolved findings")
            record["status"] = event["status"]
        elif action == "assign":
            reliability._text(event["owner"])
            record["owner"] = event["owner"]
        elif action == "note":
            reliability._text(event["note"])
            record["improvement_notes"].append({key: event[key] for key in
                                               ("sequence", "created_at", "actor", "reason", "note")})
        else:
            raise ValueError("Unknown assurance operation action")
    continuity._history(record, event, previous, record["status"])
    record["history"][-1].update({"action": action, "owner": record["owner"]})


@operation_scoped_load("assurance_operations", _root)
def _load(workspace):
    state = {"mode": MODE, "operations": [], "findings": [], "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1 or event["sequence"] != sequence
                    or event["previous_digest"] != digest or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken assurance operations journal chain")
            _apply(state, event)
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
            raise LocalWorkflowError(f"Invalid assurance operations journal: {error}") from error
        state["events"].append(event)
        digest = reliability._digest(event)
    return state


def _append(workspace, state, action, identifier, reason, actor, **payload):
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": reliability._digest(state["events"][-1]) if state["events"] else None,
             "action": action, "operation_id": identifier, "reason": reason, "actor": actor,
             "created_at": _now().isoformat(), **payload}
    result = deepcopy(state)
    try:
        _apply(result, event)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
        raise LocalWorkflowError(str(error)) from error
    directory = _root(workspace)
    workspace._prepare()
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, suffix=".tmp", delete=False) as stream:
            temporary = stream.name
            stream.write(_json_bytes(event))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, workspace._contained(directory / f"{event['sequence']:08d}.json"))
    except OSError as error:
        raise LocalWorkflowError(f"Cannot append assurance operation; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(result, identifier))


def create(workspace, assurance_id, reason, owner="developer", actor="developer"):
    state = _load(workspace)
    source = governance.history(workspace, assurance_id)["record"]
    return _append(workspace, state, "create", f"operation-{len(state['operations']) + 1:03d}",
                   reason, actor, assurance_snapshot=source, owner=owner)


def record_review(workspace, identifier, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    report = governance.review(workspace, record["assurance_id"])
    return _append(workspace, state, "review", identifier, reason, actor, review=report)


def change(workspace, identifier, action, reason, actor="developer", **payload):
    if action not in {"transition", "assign", "note"}:
        raise LocalWorkflowError("Unknown explicit assurance operation change")
    state = _load(workspace)
    record = _resolve(state, identifier)
    if action == "transition" and payload.get("status") == "improved":
        # A historical clean review cannot override a newly stale assurance.
        current = governance.review(workspace, record["assurance_id"])
        if current["findings"] or not record["reviews"] or current["record"] != record["reviews"][-1]["snapshot"]["record"]:
            raise LocalWorkflowError("Record a fresh clean review before declaring improvement")
    return _append(workspace, state, action, identifier, reason, actor, **payload)


def operations(workspace):
    state = _load(workspace)
    return {"mode": MODE, "operations": state["operations"],
            "active": [r for r in state["operations"] if r["status"] != "closed"],
            "open_findings": [f for f in state["findings"] if f["status"] == "open"]}


def findings(workspace):
    records = _load(workspace)["findings"]
    return {"mode": MODE, "active": [f for f in records if f["status"] == "open"],
            "resolved": [f for f in records if f["status"] == "resolved"],
            "recurring": [f for f in records if sum(o["status"] == "observed" for o in f["observations"]) > 1]}


def review_cycle(workspace, assurance_id):
    state = _load(workspace)
    records = [r for r in state["operations"] if r["assurance_id"] == assurance_id]
    try:
        current = governance.review(workspace, assurance_id)
    except LocalWorkflowError as error:
        if not records:
            raise
        current = {"findings": ["assurance_history_unavailable"], "manual_actions": [
            {"finding": "assurance_history_unavailable", "action": f"Restore assurance history: {error}"}]}
    reviews = sorted([v for r in records for v in r["reviews"]], key=lambda v: v["sequence"])
    return {"mode": MODE, "assurance_id": assurance_id, "operations": records, "previous_reviews": reviews,
            "current_findings": current["findings"], "pending_actions": current["manual_actions"],
            "improvement_history": sorted([{"operation_id": r["operation_id"], **n} for r in records
                                           for n in r["improvement_notes"]], key=lambda n: n["sequence"])}


def coverage(workspace):
    """Enumerate scenarios and unregistered assurances as well as governance anchors."""
    _root(workspace)
    result = {"mode": MODE, "covered": [], "missing_owner": [], "missing_schedule": [], "expired": [],
              "manual_actions": [], "verified_scenarios": [], "missing_recovery_references": [],
              "uncovered": [], "diagnostics": []}
    def load(module, key):
        try:
            return module._load(workspace)[key]
        except LocalWorkflowError as error:
            result["diagnostics"].append({"source": module.MODE, "detail": str(error)})
            return []
    governed = load(governance, "assurances")
    sources = load(assurance, "assurances")
    scenarios = load(continuity, "scenarios")
    linked = {r["assurance_id"] for r in governed} | {v["verification_id"] for r in governed for v in r["verification_history"]}
    rows = [(r["assurance_id"], r["scenario_id"], r, None) for r in governed]
    rows.extend((r["assurance_id"], r["scenario_id"], None, r) for r in sources if r["assurance_id"] not in linked)
    known = {row[1] for row in rows}
    rows.extend((None, r["scenario_id"], None, None) for r in scenarios if r["scenario_id"] not in known)
    for identifier, scenario_id, record, source in rows:
        row = {"assurance_id": identifier, "scenario_id": scenario_id}
        reasons = []
        if not record or not record["owner"] or not record["responsibility"]:
            result["missing_owner"].append(row)
            reasons.append("Assign an assurance governance owner and responsibility")
        if not record or not record["verification_schedule"] or not record["next_check"]:
            result["missing_schedule"].append(row)
            reasons.append("Register and activate a recurring assurance schedule")
        if record:
            report = governance._review(workspace, record)
            if report["findings"]:
                reasons.extend(report["findings"])
            expired = report["expired"]
            source = record["verification_history"][-1]["source"] if record["verification_history"] else None
            if source:
                source = next((s for s in sources if s["assurance_id"] == source["assurance_id"]), source)
        else:
            expired = bool(source and source["status"] == "expired")
        evidence_findings, _ = governance._evidence_findings(workspace, {"scenario_id": scenario_id}, source)
        expired = expired or any(f.startswith("stale_evidence:") for f in evidence_findings)
        if expired:
            result["expired"].append(row)
        if evidence_findings:
            reasons.extend(evidence_findings)
        try:
            _, _, live, _ = assurance._collect(workspace, scenario_id)
            missing = [f["check"] for f in live["blocked"]]
        except LocalWorkflowError:
            missing = ["recovery_history_unavailable"]
        if missing:
            result["missing_recovery_references"].append({**row, "findings": missing})
            reasons.extend(missing)
        if (not evidence_findings and not missing and not result["diagnostics"] and source
                and any(s["assurance_id"] == source["assurance_id"] for s in sources)
                and scenario_id not in result["verified_scenarios"]):
            result["verified_scenarios"].append(scenario_id)
        if result["diagnostics"]:
            reasons.append("Restore unreadable source histories before assessing coverage")
        result["uncovered" if reasons else "covered"].append(row)
        if reasons:
            result["manual_actions"].append({**row, "actions": sorted(set(reasons))})
    result["manual_actions"].extend({"action": "Restore unreadable history", **d} for d in result["diagnostics"])
    return result


def improvements(workspace):
    # Preserve the Phase 53 report's mode and fields for existing consumers.
    result = governance.improvements(workspace)
    state = _load(workspace)
    reviews = sorted([{"operation_id": r["operation_id"], "assurance_id": r["assurance_id"], **v}
                      for r in state["operations"] for v in r["reviews"]], key=lambda v: v["sequence"])
    result["operations"] = {"mode": MODE, "reviews": reviews,
        **{key: [{"sequence": v["sequence"], "operation_id": v["operation_id"], "assurance_id": v["assurance_id"],
                  "findings": v[key]} for v in reviews] for key in
           ("new_findings", "resolved_findings", "repeated_findings", "reopened_findings")},
        "improvement_notes": [{"operation_id": r["operation_id"], "assurance_id": r["assurance_id"], **n}
                              for r in state["operations"] for n in r["improvement_notes"]],
        "linked_verification_history": [{"sequence": v["sequence"], "assurance_id": v["assurance_id"],
             "verification_history": v["snapshot"]["record"]["verification_history"]} for v in reviews]}
    return result
