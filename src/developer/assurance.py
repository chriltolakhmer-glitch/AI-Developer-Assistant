"""Developer recovery assurance and immutable evidence; never executes recovery."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import os
import tempfile

from . import continuity, operations, reliability
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read

MODE = "developer-recovery-assurance"
STATES = {"pending": {"verifying", "expired"}, "verifying": {"passed", "failed", "expired"},
          "passed": {"expired"}, "failed": {"expired"}, "expired": set()}
CHECKS = {"previous_checks", "evidence_current", "recovery_plan", "rollback_reference",
          "continuity_records", "live_validation", "scenario_state"}
EVIDENCE_TYPES = ("recovery_plan", "rollback_reference", "configuration_history", "deployment_audit",
                  "ownership", "previous_simulations", "continuity_record", "deployment_history", "live_validation")


def _now():
    return datetime.now(timezone.utc)


def _root(workspace):
    continuity._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "assurance")


def _timestamp(value):
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError("Assurance timestamps require a timezone")
    return result


def _resolve(state, identifier):
    for record in state["assurances"]:
        if record["assurance_id"] == identifier:
            return record
    raise LocalWorkflowError("Unknown assurance ID.")


def _apply(state, event):
    for key in ("actor", "reason", "created_at"):
        reliability._text(event[key])
    timestamp = _timestamp(event["created_at"])
    if event["action"] == "create":
        reliability._text(event["owner"])
        hours = event["valid_for_hours"]
        if type(hours) is not int or not 1 <= hours <= 8760:
            raise ValueError("Evidence validity must be an integer from 1 to 8760 hours")
        scenario = event["scenario_snapshot"]
        for key in ("scenario_id", "deployment_id", "owner", "continuity_id", "recovery_plan"):
            reliability._text(scenario[key])
        if not scenario["history"] or scenario["status"] not in continuity.STATES:
            raise ValueError("Invalid scenario history")
        if event["assurance_id"] != f"assurance-{len(state['assurances']) + 1:03d}":
            raise ValueError("Invalid assurance ID")
        record = {"assurance_id": event["assurance_id"], "scenario_id": scenario["scenario_id"],
                  "deployment_id": scenario["deployment_id"], "status": "pending", "owner": event["owner"],
                  "created_at": event["created_at"], "valid_for_hours": hours, "checks": [], "evidence": [],
                  "scenario_snapshot": deepcopy(scenario), "history": []}
        continuity._history(record, event, None, "pending")
        state["assurances"].append(record)
        return
    if event["action"] != "transition":
        raise ValueError("Unknown assurance action")
    record = _resolve(state, event["assurance_id"])
    status, report = event["status"], event["report"]
    if status not in STATES[record["status"]]:
        raise LocalWorkflowError(f"Invalid assurance transition: {record['status']} -> {status}.")
    if status in {"passed", "failed"}:
        reliability._validate_report(report, CHECKS)
        if (report["scenario_id"] != record["scenario_id"]
                or status != ("failed" if report["blocked"] else "passed")
                or [e["evidence_type"] for e in report["evidence"]] != list(EVIDENCE_TYPES)):
            raise ValueError("Assurance outcome or evidence does not match verification")
        for index, evidence in enumerate(report["evidence"], 1):
            if (evidence["evidence_id"] != f"{record['assurance_id']}-evidence-{index:02d}"
                    or evidence["checked_at"] != event["created_at"]
                    or evidence["expires_at"] != (timestamp + timedelta(hours=record["valid_for_hours"])).isoformat()
                    or evidence["status"] not in {"available", "missing"}
                    or evidence["content_digest"] != reliability._digest(evidence["content"])):
                raise ValueError("Invalid immutable evidence record")
            reliability._text(evidence["source"])
            reliability._text(evidence["detail"])
        record["checks"] = reliability._checks(report)
        record["evidence"] = deepcopy(report["evidence"])
    elif report is not None:
        raise ValueError("Unexpected assurance evidence")
    continuity._history(record, event, record["status"], status)
    if report is not None:
        record["history"][-1]["verification"] = deepcopy(report)
    record["status"] = status


def _load(workspace):
    state = {"mode": MODE, "assurances": [], "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1 or event["sequence"] != sequence
                    or event["previous_digest"] != digest or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken assurance journal chain")
            _apply(state, event)
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
            raise LocalWorkflowError(f"Invalid assurance journal: {error}") from error
        state["events"].append(event)
        digest = reliability._digest(event)
    return state


def _append(workspace, state, action, identifier, reason, actor, **payload):
    report = payload.get("report")
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": reliability._digest(state["events"][-1]) if state["events"] else None,
             "action": action, "assurance_id": identifier, "reason": reason, "actor": actor,
             "created_at": report["evidence"][0]["checked_at"] if report else _now().isoformat(), **payload}
    result = deepcopy(state)
    try:
        _apply(result, event)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
        raise LocalWorkflowError(str(error)) from error
    directory = _root(workspace)
    workspace._prepare()
    directory.mkdir(parents=True, exist_ok=True)
    target = workspace._contained(directory / f"{event['sequence']:08d}.json")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, suffix=".tmp", delete=False) as stream:
            temporary = stream.name
            stream.write(_json_bytes(event))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    except OSError as error:
        raise LocalWorkflowError(f"Cannot append assurance event; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(result, identifier))


def _collect(workspace, scenario_id):
    """Stable content is separate from observation time, so repeated checks compare fairly."""
    _root(workspace)
    try:
        state = continuity._load(workspace)
        scenario = continuity._resolve(state, scenario_id)
        knowledge = continuity._continuity(state, scenario)
    except LocalWorkflowError as error:
        retained = _records(_load(workspace), scenario_id)
        if not retained:
            raise
        scenario = retained[-1]["scenario_snapshot"]
        detail = f"Live scenario/continuity history is unavailable: {error}"
        live = {"mode": continuity.MODE, "scenario_id": scenario_id, "deployment_id": scenario["deployment_id"],
                **reliability._report(), "evidence": {}}
        for check in sorted(continuity.CHECKS):
            reliability._finding(live, "blocked", check, detail)
        evidence = [{"evidence_type": kind, "status": "missing", "source": scenario_id,
                     "content": {"unavailable_reason": detail}, "content_digest": reliability._digest({"unavailable_reason": detail}),
                     "detail": detail} for kind in EVIDENCE_TYPES]
        return scenario, {"continuity_id": scenario["continuity_id"]}, live, evidence
    live = continuity.disaster_check(workspace, scenario_id)
    findings = {item["check"]: (bucket, item["detail"]) for bucket in ("passed", "warnings", "blocked")
                for item in live[bucket]}
    evidence = []
    def add(kind, source, available, content, detail):
        evidence.append({"evidence_type": kind, "status": "available" if available else "missing",
                         "source": source, "content": deepcopy(content),
                         "content_digest": reliability._digest(content), "detail": detail})
    mapping = (("recovery_plan", "recovery_plan", scenario["recovery_plan"], "recovery_plan"),
               ("rollback_reference", "rollback_target", scenario["recovery_plan"], "rollback_deployment"),
               ("configuration_history", "configuration_history", scenario["deployment_id"], "configurations"),
               ("deployment_audit", "audit_history", scenario["deployment_id"], "audit_history"))
    for kind, check, source, key in mapping:
        available = findings[check][0] != "blocked"
        content = {"finding": list(findings[check]), "record": live["evidence"].get(key)}
        if kind == "rollback_reference":
            content["reference"] = knowledge["recovery_references"]
        add(kind, source, available, content, findings[check][1])
    add("ownership", scenario_id, True,
        {"scenario_owner": scenario["owner"], "plan_owner": knowledge["knowledge"]["recovery_plan"]["owner"]},
        "Scenario and captured recovery-plan ownership are attributed.")
    add("previous_simulations", scenario_id, bool(scenario["tests"]), scenario["tests"],
        "Completed simulation history is available." if scenario["tests"] else "No previous simulation results exist.")
    add("continuity_record", knowledge["continuity_id"], True, knowledge, "Continuity dependencies and preserved knowledge replay completely.")
    add("deployment_history", scenario["deployment_id"], findings["deployment_history"][0] != "blocked",
        live["evidence"].get("deployment"), findings["deployment_history"][1])
    add("live_validation", scenario_id, True, live, "Live validation findings are available; inspect blockers separately.")
    return scenario, knowledge, live, evidence


def _stale(record, evidence, current, now):
    if record["status"] == "expired":
        return "Assurance was explicitly expired."
    if now >= _timestamp(evidence["expires_at"]):
        return "Evidence validity window elapsed."
    if (evidence["status"] != current["status"] or evidence["content_digest"] != current["content_digest"]
            or evidence["source"] != current["source"]):
        return "Evidence source or validation content changed."
    return None


def _verification(scenario, knowledge, live, evidence, previous=None, now=None):
    now = now or _now()
    report = {"mode": MODE, "scenario_id": scenario["scenario_id"], **reliability._report(),
              "evidence": deepcopy(evidence), "evidence_warnings": []}
    items = {e["evidence_type"]: e for e in evidence}
    def finding(bucket, check, detail):
        reliability._finding(report, bucket, check, detail)
    for item in evidence:
        if item["status"] == "missing":
            report["evidence_warnings"].append({"evidence_type": item["evidence_type"], "detail": item["detail"]})
    last_test = scenario["tests"][-1] if scenario["tests"] else None
    finding("passed" if last_test else "blocked", "previous_checks",
            "Previous completed simulations exist." if last_test else "Run disaster-test before assurance verification.")
    stale = bool(last_test and last_test["evidence_digest"] != reliability._digest(live))
    if previous and previous["evidence"]:
        stale = stale or any(_stale(previous, e, items[e["evidence_type"]], now) for e in previous["evidence"])
    missing = any(e["status"] == "missing" for e in evidence)
    finding("blocked" if stale or missing else "passed", "evidence_current",
            "Evidence is missing or changed, or retained evidence expired." if stale or missing
            else "Evidence is available and matches current simulation prerequisites.")
    for check, kind in (("recovery_plan", "recovery_plan"), ("rollback_reference", "rollback_reference"),
                        ("continuity_records", "continuity_record")):
        finding("passed" if items[kind]["status"] == "available" else "blocked", check, items[kind]["detail"])
    finding("blocked" if live["blocked"] else "warnings" if live["warnings"] else "passed",
            "live_validation", f"Disaster findings: {reliability._checks(live)}")
    finding("passed" if scenario["status"] == "validated" else "blocked", "scenario_state",
            f"Scenario is {scenario['status']}; assurance requires a validated scenario.")
    return report


def create_assurance(workspace, scenario_id, reason, owner="developer", actor="developer", valid_for_hours=24):
    state = _load(workspace)
    scenario = continuity._resolve(continuity._load(workspace), scenario_id)
    return _append(workspace, state, "create", f"assurance-{len(state['assurances']) + 1:03d}", reason, actor,
                   owner=owner, valid_for_hours=valid_for_hours, scenario_snapshot=scenario)


def _assessment(workspace, record):
    scenario, knowledge, live, evidence = _collect(workspace, record["scenario_id"])
    original = record["scenario_snapshot"]
    if (any(scenario[key] != original[key] for key in ("scenario_id", "deployment_id", "owner", "continuity_id", "recovery_plan"))
            or scenario["history"][:len(original["history"])] != original["history"]):
        raise LocalWorkflowError("Scenario no longer matches the assurance history reference.")
    now = _now()
    for index, item in enumerate(evidence, 1):
        item.update(evidence_id=f"{record['assurance_id']}-evidence-{index:02d}", checked_at=now.isoformat(),
                    expires_at=(now + timedelta(hours=record["valid_for_hours"])).isoformat())
    return _verification(scenario, knowledge, live, evidence, now=now)


def transition_assurance(workspace, identifier, status, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    if status not in STATES[record["status"]]:
        raise LocalWorkflowError(f"Invalid assurance transition: {record['status']} -> {status}.")
    report = _assessment(workspace, record) if status in {"passed", "failed"} else None
    return _append(workspace, state, "transition", identifier, reason, actor, status=status, report=report)


def verify_assurance(workspace, identifier, reason="Verify recovery assurance evidence", actor="developer"):
    record = _resolve(_load(workspace), identifier)
    if record["status"] == "pending":
        transition_assurance(workspace, identifier, "verifying", reason, actor)
    elif record["status"] != "verifying":
        raise LocalWorkflowError("Assurance must be pending or verifying; create a new record.")
    state = _load(workspace)
    report = _assessment(workspace, record)
    return _append(workspace, state, "transition", identifier, reason, actor,
                   status="failed" if report["blocked"] else "passed", report=report)


def _records(state, scenario_id):
    return [r for r in state["assurances"] if r["scenario_id"] == scenario_id]


def recovery_evidence(workspace, scenario_id):
    records = _records(_load(workspace), scenario_id)
    scenario, knowledge, live, evidence = _collect(workspace, scenario_id)
    now = _now()
    for item in evidence:
        item["checked_at"] = now.isoformat()
    current = {e["evidence_type"]: e for e in evidence}
    expired = []
    for record in records:
        for item in record["evidence"]:
            reason = _stale(record, item, current[item["evidence_type"]], now)
            if reason:
                expired.append({"assurance_id": record["assurance_id"], "evidence": item, "reason": reason})
    return {"mode": MODE, "scenario_id": scenario_id,
            "available": [e for e in evidence if e["status"] == "available"],
            "missing": [e for e in evidence if e["status"] == "missing"], "expired": expired,
            "recorded": [{"assurance_id": r["assurance_id"], "evidence": r["evidence"]} for r in records],
            "warnings": [{"evidence_type": e["evidence_type"], "detail": e["detail"]}
                         for e in evidence if e["status"] == "missing"],
            "related_records": {"deployment_id": scenario["deployment_id"], "continuity_id": knowledge["continuity_id"],
                                "recovery_plan": scenario["recovery_plan"], "assurances": [r["assurance_id"] for r in records]}}


def recovery_verify_history(workspace, scenario_id):
    records = _records(_load(workspace), scenario_id)
    scenario, knowledge, live, evidence = _collect(workspace, scenario_id)
    completed = [r for r in records if r["evidence"]]
    report = _verification(scenario, knowledge, live, evidence, completed[-1] if completed else None)
    report["previous_assurance"] = completed[-1]["assurance_id"] if completed else None
    report["previous_simulations"] = scenario["tests"]
    return report


def recovery_assurance(workspace, scenario_id):
    records = _records(_load(workspace), scenario_id)
    verification = recovery_verify_history(workspace, scenario_id)
    evidence = recovery_evidence(workspace, scenario_id)
    latest = records[-1] if records else None
    readiness = latest["status"] if latest else "pending"
    if latest and latest["evidence"] and any(e["assurance_id"] == latest["assurance_id"] for e in evidence["expired"]):
        readiness = "expired"
    elif readiness == "passed" and verification["blocked"]:
        readiness = "failed"
    return {"mode": MODE, "scenario_id": scenario_id, "recovery_readiness": readiness,
            "owner": latest["owner"] if latest else None, "assurances": records,
            "validation_history": [{"assurance_id": r["assurance_id"], "history": r["history"]} for r in records],
            "evidence": evidence, "verification": verification,
            "previous_simulations": verification["previous_simulations"]}


def recovery_history_analysis(workspace):
    state = _load(workspace)
    simulations, failures, unresolved = [], [], []
    try:
        scenarios = continuity._load(workspace)["scenarios"]
    except LocalWorkflowError as error:
        scenarios = []
        unresolved.append({"source": "continuity", "blocked": [{"check": "continuity_history", "detail": str(error)}]})
    for scenario in scenarios:
        simulations.extend(scenario["tests"])
        failures.extend({"kind": "simulation", "record": t} for t in scenario["tests"] if t["status"] == "failed")
    identifiers = {s["scenario_id"] for s in scenarios} | {r["scenario_id"] for r in state["assurances"]}
    for identifier in sorted(identifiers):
        report = recovery_verify_history(workspace, identifier)
        if report["warnings"] or report["blocked"] or report["evidence_warnings"]:
            unresolved.append({"scenario_id": identifier, "warnings": report["warnings"],
                               "blocked": report["blocked"], "evidence_warnings": report["evidence_warnings"]})
    failures.extend({"kind": "assurance", "record": r} for r in state["assurances"]
                    if any(h["status"] == "failed" for h in r["history"]))
    try:
        recovery = operations.recovery_history(workspace)
    except LocalWorkflowError as error:
        recovery = {"unavailable_reason": str(error)}
        unresolved.append({"source": "operations", "blocked": [{"check": "recovery_history", "detail": str(error)}]})
    return {"mode": MODE, "recovery_history": recovery, "simulation_history": simulations,
            "assurance_history": state["assurances"], "failures": failures, "unresolved_findings": unresolved}
