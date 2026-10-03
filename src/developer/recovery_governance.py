"""Developer-only recurring assurance governance; no scheduler or recovery execution."""
from copy import deepcopy
from datetime import timedelta
import os
import tempfile

from . import assurance, configuration, continuity, reliability
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read
from .read_context import operation_scoped_load

MODE = "developer-recovery-governance"
STATES = {"draft": {"active", "retired"}, "active": {"paused", "expired", "retired"},
          "paused": {"active", "expired", "retired"}, "expired": {"active", "retired"}, "retired": set()}
_now = assurance._now


def _root(workspace):
    continuity._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "recovery-governance")


def _resolve(state, identifier):
    return assurance._resolve(state, identifier)


def _hours(value):
    if type(value) is not int or not 1 <= value <= 8760:
        raise ValueError("Schedule must be an integer from 1 to 8760 hours")
    return value


def _apply(state, event):
    for key in ("actor", "reason", "assurance_id"):
        reliability._text(event[key])
    timestamp = assurance._timestamp(event["created_at"])
    action = event["action"]
    if action == "register":
        if any(r["assurance_id"] == event["assurance_id"] for r in state["assurances"]):
            raise ValueError("Assurance is already registered")
        source = event["source"]
        if source["assurance_id"] != event["assurance_id"]:
            raise ValueError("Mismatched source assurance")
        reliability._text(source["scenario_id"])
        record = {"assurance_id": event["assurance_id"], "scenario_id": source["scenario_id"],
                  "source": deepcopy(source), "status": "draft", "owner": "", "responsibility": "",
                  "last_check": None, "next_check": None, "history": [], "review_notes": [],
                  "improvement_notes": [], "verification_history": [], "ownership_changed_at": None}
        state["assurances"].append(record)
    else:
        record = _resolve(state, event["assurance_id"])
        if record["status"] == "retired":
            raise ValueError("Retired assurance governance is immutable")
    previous = record["status"] if action != "register" else None
    if action in {"register", "assign"}:
        for key in ("owner", "responsibility"):
            reliability._text(event[key])
            record[key] = event[key]
        if action == "assign":
            record["ownership_changed_at"] = event["created_at"]
    if action in {"register", "schedule"}:
        record["interval_hours"] = _hours(event["interval_hours"])
        record["verification_schedule"] = f"every {record['interval_hours']} hours"
        if record["status"] != "draft":
            base = assurance._timestamp(record["last_check"]) if record["last_check"] else timestamp
            record["next_check"] = (base + timedelta(hours=record["interval_hours"])).isoformat() if record["last_check"] else base.isoformat()
    elif action == "transition":
        if event["status"] not in STATES[record["status"]]:
            raise ValueError(f"Invalid governance transition: {record['status']} -> {event['status']}")
        record["status"] = event["status"]
        if event["status"] == "active" and record["next_check"] is None:
            record["next_check"] = event["created_at"]
    elif action == "note":
        if event["kind"] not in {"review", "improvement"}:
            raise ValueError("Unknown governance note kind")
        reliability._text(event["note"])
        record[event["kind"] + "_notes"].append({key: deepcopy(event[key]) for key in
                                                  ("sequence", "created_at", "actor", "reason", "note")})
    elif action == "record-check":
        if record["status"] != "active":
            raise ValueError("Recording verification requires active governance")
        source = event["source"]
        if source["scenario_id"] != record["scenario_id"] or source["status"] not in {"passed", "failed"} or not source["evidence"]:
            raise ValueError("A completed verification for the governed scenario is required")
        if any(v["verification_id"] == source["assurance_id"] for v in record["verification_history"]):
            raise ValueError("Verification already recorded; create a fresh Phase 52 assurance")
        checked = source["evidence"][0]["checked_at"]
        check_time = assurance._timestamp(checked)
        if check_time > timestamp or (record["last_check"] and check_time <= assurance._timestamp(record["last_check"])):
            raise ValueError("Verification must be newer than the last check and cannot be in the future")
        for evidence in source["evidence"]:
            if evidence["checked_at"] != checked or evidence["content_digest"] != reliability._digest(evidence["content"]):
                raise ValueError("Invalid verification evidence")
        findings = event["findings"]
        if not isinstance(findings, list) or any(not isinstance(f, str) or not f for f in findings):
            raise ValueError("Invalid recorded findings")
        prior = record["verification_history"][-1] if record["verification_history"] else None
        old_evidence = {e["evidence_type"]: e["content"] for e in prior["source"]["evidence"]} if prior else {}
        new_evidence = {e["evidence_type"]: e["content"] for e in source["evidence"]}
        record["verification_history"].append({"sequence": event["sequence"], "created_at": event["created_at"],
            "actor": event["actor"], "verification_id": source["assurance_id"], "owner": record["owner"],
            "responsibility": record["responsibility"], "checked_at": checked, "source": deepcopy(source),
            "findings": findings[:], "resolved_findings": sorted(set(prior["findings"] if prior else []) - set(findings)),
            "evidence_changes": configuration.settings_diff(old_evidence, new_evidence)})
        record["last_check"] = checked
        record["next_check"] = (check_time + timedelta(hours=record["interval_hours"])).isoformat()
    elif action not in {"register", "assign", "schedule"}:
        raise ValueError("Unknown governance action")
    continuity._history(record, event, previous, record["status"])
    record["history"][-1]["action"] = action
    record["history"][-1]["details"] = deepcopy({k: v for k, v in event.items() if k in
                                               {"owner", "responsibility", "interval_hours", "kind", "note", "source", "findings"}})


@operation_scoped_load("recovery_governance", _root)
def _load(workspace):
    state = {"mode": MODE, "assurances": [], "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1 or event["sequence"] != sequence
                    or event["previous_digest"] != digest or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken governance journal chain")
            _apply(state, event)
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
            raise LocalWorkflowError(f"Invalid governance journal: {error}") from error
        state["events"].append(event)
        digest = reliability._digest(event)
    return state


def _append(workspace, state, action, identifier, reason, actor, **payload):
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": reliability._digest(state["events"][-1]) if state["events"] else None,
             "action": action, "assurance_id": identifier, "reason": reason, "actor": actor,
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
        raise LocalWorkflowError(f"Cannot append governance event; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(result, identifier))


def register(workspace, identifier, reason, owner="developer", responsibility="maintain recovery verification evidence",
             interval_hours=24, actor="developer"):
    state = _load(workspace)
    source = assurance._resolve(assurance._load(workspace), identifier)
    return _append(workspace, state, "register", identifier, reason, actor, source=source, owner=owner,
                   responsibility=responsibility, interval_hours=interval_hours)


def change(workspace, identifier, action, reason, actor="developer", **payload):
    if action not in {"transition", "assign", "schedule", "note"}:
        raise LocalWorkflowError("Unknown explicit governance change")
    return _append(workspace, _load(workspace), action, identifier, reason, actor, **payload)


def _evidence_findings(workspace, record, source):
    findings = []
    if not source or not source["evidence"]:
        return ["verification_missing"], list(assurance.EVIDENCE_TYPES)
    if source["status"] != "passed":
        findings.append("verification_not_passed")
    missing = []
    try:
        _, _, live, evidence = assurance._collect(workspace, record["scenario_id"])
        current = {e["evidence_type"]: e for e in evidence}
        for item in source["evidence"]:
            kind = item["evidence_type"]
            if current[kind]["status"] == "missing":
                missing.append(kind)
            if assurance._stale(source, item, current[kind], _now()):
                findings.append("stale_evidence:" + kind)
        findings.extend("recovery_reference:" + item["check"] for item in live["blocked"])
    except LocalWorkflowError:
        findings.append("recovery_history_unavailable")
        missing = list(assurance.EVIDENCE_TYPES)
    return sorted(set(findings)), missing


def record_check(workspace, identifier, verification_id, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    source = assurance._resolve(assurance._load(workspace), verification_id)
    findings, _ = _evidence_findings(workspace, record, source)
    return _append(workspace, state, "record-check", identifier, reason, actor, source=source, findings=findings)


def _review(workspace, record):
    findings = []
    previous = record["verification_history"][-1] if record["verification_history"] else None
    source = previous["source"] if previous else None
    if source:
        try:
            source = assurance._resolve(assurance._load(workspace), source["assurance_id"])
        except LocalWorkflowError:
            findings.append("verification_history_unavailable")
    evidence_findings, missing = _evidence_findings(workspace, record, source)
    findings.extend(evidence_findings)
    if not record["owner"] or not record["responsibility"]:
        findings.append("ownership_missing")
    if record["ownership_changed_at"] and (not previous or
            assurance._timestamp(previous["checked_at"]) < assurance._timestamp(record["ownership_changed_at"])):
        findings.append("ownership_review_due")
    if record["status"] != "active":
        findings.append("lifecycle:" + record["status"])
    overdue = bool(record["next_check"] and _now() >= assurance._timestamp(record["next_check"]))
    if overdue:
        findings.append("scheduled_check_overdue")
    if not record["next_check"]:
        findings.append("scheduled_check_missing")
    findings = sorted(set(findings))
    return {"mode": MODE, "assurance_id": record["assurance_id"], "record": deepcopy(record),
            "missing_evidence": missing, "stale_checks": [f for f in findings if f.startswith("stale_") or f.endswith("overdue")],
            "findings": findings, "expired": record["status"] == "expired" or overdue or bool([f for f in findings if f.startswith("stale_evidence:")]),
            "manual_actions": [{"finding": f, "action": _manual_action(f)} for f in findings]}


def _manual_action(finding):
    if finding.startswith("lifecycle:"):
        return "Review the lifecycle history; explicitly activate eligible governance when responsibility resumes. Retired records remain terminal."
    if finding.startswith("ownership"):
        return "Confirm the owner and responsibility, append a review note, and record a fresh verification completed after the handoff."
    if finding.startswith("scheduled"):
        return "Review the recurring interval and explicitly create, verify and record a fresh Phase 52 assurance when due."
    if finding.endswith("unavailable") or finding.startswith("recovery_reference:"):
        return "Inspect and manually restore missing recovery history or references, then verify again."
    return "Inspect missing or stale evidence, explicitly create and verify a fresh Phase 52 assurance for this scenario, then record its ID."


def review(workspace, identifier):
    return _review(workspace, _resolve(_load(workspace), identifier))


def history(workspace, identifier):
    return {"mode": MODE, "record": deepcopy(_resolve(_load(workspace), identifier))}


def check(workspace):
    result = {"mode": MODE, "passed": [], "warnings": [], "expired": [], "manual_actions": []}
    for record in _load(workspace)["assurances"]:
        report = _review(workspace, record)
        result["warnings" if report["findings"] else "passed"].append(report)
        if report["expired"]:
            result["expired"].append(record["assurance_id"])
        result["manual_actions"].extend({"assurance_id": record["assurance_id"], **action} for action in report["manual_actions"])
    return result


def status(workspace):
    report = check(workspace)
    records = [r["record"] for r in report["passed"] + report["warnings"]]
    return {"mode": MODE, "assurances": records, "active": [r["assurance_id"] for r in records if r["status"] == "active"],
            "expired": report["expired"]}


def improvements(workspace):
    result = []
    for record in _load(workspace)["assurances"]:
        verifications = record["verification_history"]
        result.append({"assurance_id": record["assurance_id"], "previous_findings": [
            {"sequence": v["sequence"], "verification_id": v["verification_id"], "findings": v["findings"]} for v in verifications],
            "resolved_findings": [{"sequence": v["sequence"], "findings": v["resolved_findings"]} for v in verifications],
            "unresolved_findings": verifications[-1]["findings"] if verifications else ["verification_missing"],
            "current_findings": _review(workspace, record)["findings"], "manual_improvement_notes": record["improvement_notes"]})
    return {"mode": MODE, "improvements": result}
