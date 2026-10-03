"""Developer readiness and recovery preparation; never executes recovery."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
import tempfile

from . import configuration, deployment, operations, promotion
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read
from .read_context import operation_scoped_load

MODE = "developer-retrieval-reliability"
STATES = {"pending": {"checking", "expired"}, "checking": {"passed", "failed", "expired"},
          "passed": {"expired"}, "failed": {"expired"}, "expired": set()}
CHECKS = {"audit_completeness", "health_availability", "rollback_availability",
          "recovery_plan", "recovery_validation", "governance", "incident_consistency"}
VERIFY_CHECKS = {"deployment_history", "rollback_reference", "recovery_owner",
                 "previous_configuration", "rollback_availability", "governance"}


def _root(workspace):
    deployment._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "reliability")


def _readonly(workspace):
    _root(workspace)
    return promotion._readonly(workspace)


def _resolve(state, collection, identifier):
    key = "readiness_id" if collection == "readiness" else "plan_id"
    for record in state[collection]:
        if record[key] == identifier:
            return record
    raise LocalWorkflowError(f"Unknown {collection} ID.")


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Reliability records require nonempty attribution and reasons")


def _digest(value):
    # Preserve the journal's canonical bytes without materializing a second
    # full JSON snapshot merely to verify its digest during read-only replay.
    digest = hashlib.sha256()
    buffer = bytearray()
    encoder = json.JSONEncoder(ensure_ascii=False, indent=2, sort_keys=True)
    for fragment in encoder.iterencode(value):
        buffer.extend(fragment.encode("utf-8"))
        if len(buffer) >= 65536:
            digest.update(buffer)
            buffer.clear()
    buffer.extend(b"\n")
    digest.update(buffer)
    return digest.hexdigest()


def _report():
    return {"passed": [], "warnings": [], "blocked": []}


def _finding(report, bucket, check, detail):
    report[bucket].append({"check": check, "detail": detail})


def _checks(report):
    return [{"status": bucket, **item} for bucket in ("passed", "warnings", "blocked")
            for item in report[bucket]]


def _validate_report(report, expected):
    found = set()
    for bucket in ("passed", "warnings", "blocked"):
        if not isinstance(report[bucket], list):
            raise ValueError("Invalid reliability findings")
        for item in report[bucket]:
            if item["check"] not in expected or item["check"] in found:
                raise ValueError("Invalid or duplicate reliability check")
            _text(item["detail"])
            found.add(item["check"])
    if found != expected:
        raise ValueError("Incomplete reliability checks")


def _history(record, event, previous, status):
    record["history"].append({"sequence": event["sequence"], "created_at": event["created_at"],
                              "actor": event["actor"], "reason": event["reason"],
                              "previous_status": previous, "status": status})


def _apply(state, event, *, copy_evidence=True):
    # Replayed JSON belongs exclusively to this load. Its evidence is immutable
    # during replay and can be shared by the event and its materialized view.
    # Mutation paths retain defensive copies of caller-owned payloads.
    copy = deepcopy if copy_evidence else lambda value: value
    for key in ("created_at", "actor", "reason"):
        _text(event[key])
    if datetime.fromisoformat(event["created_at"]).utcoffset() is None:
        raise ValueError("Reliability timestamps require a timezone")
    action = event["action"]
    if action in {"readiness-create", "plan-create"}:
        snapshot = event["deployment_snapshot"]
        for key in ("deployment_id",):
            _text(snapshot[key])
        if not isinstance(snapshot["history"], list) or not snapshot["history"]:
            raise ValueError("Missing deployment history")
        promotion.validate_settings(snapshot["configuration"]["settings"])
        collection = "readiness" if action == "readiness-create" else "plans"
        key, prefix = ("readiness_id", "readiness") if collection == "readiness" else ("plan_id", "recovery-plan")
        if event["identifier"] != f"{prefix}-{len(state[collection]) + 1:03d}":
            raise ValueError("Invalid reliability record ID")
        record = {key: event["identifier"], "deployment_id": snapshot["deployment_id"],
                  "created_at": event["created_at"], "created_by": event["actor"],
                  "deployment_snapshot": copy(snapshot), "history": []}
        if collection == "readiness":
            record.update(status="pending", checks=[], evidence_digest=None)
        else:
            _text(event["owner"])
            prior = event["previous_configuration"]
            target = snapshot["previous_deployment"]
            if (target is None) != (prior is None):
                raise ValueError("Invalid previous configuration reference")
            if prior is not None:
                _text(target)
                _text(prior["config_id"])
                promotion.validate_settings(prior["settings"])
            record.update(owner=event["owner"], rollback_target=target, previous_deployment=target,
                          previous_configuration=copy(prior), validation_status="pending", verification=None)
        _history(record, event, None, "pending")
        state[collection].append(record)
        return
    if action == "plan-verify":
        record = _resolve(state, "plans", event["identifier"])
        report = event["verification"]
        _validate_report(report, VERIFY_CHECKS)
        status = "failed" if report["blocked"] else "passed"
        _history(record, event, record["validation_status"], status)
        record["validation_status"] = status
        record["verification"] = copy(report)
        record["history"][-1]["verification"] = copy(report)
        return
    if action != "readiness-transition":
        raise ValueError("Unknown reliability action")
    record = _resolve(state, "readiness", event["identifier"])
    status = event["status"]
    if status not in STATES[record["status"]]:
        raise LocalWorkflowError(f"Invalid readiness transition: {record['status']} -> {status}.")
    report = event["report"]
    if status in {"passed", "failed"}:
        _validate_report(report, CHECKS)
        if report["deployment_id"] != record["deployment_id"] or status != ("failed" if report["blocked"] else "passed"):
            raise ValueError("Readiness outcome does not match validation findings")
        record["checks"] = _checks(report)
        record["evidence_digest"] = _digest(report)
    elif report is not None:
        raise ValueError("Unexpected readiness evidence")
    _history(record, event, record["status"], status)
    if report is not None:
        record["history"][-1]["report"] = copy(report)
    record["status"] = status


@operation_scoped_load("reliability", _root)
def _load(workspace):
    state = {"mode": MODE, "readiness": [], "plans": [], "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1 or event["sequence"] != sequence
                    or event["previous_digest"] != digest or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken reliability journal chain")
            _apply(state, event, copy_evidence=False)
        except (KeyError, ValueError, TypeError, AttributeError) as error:
            raise LocalWorkflowError(f"Invalid reliability journal: {error}") from error
        state["events"].append(event)
        digest = _digest(event)
    return state


def _append(workspace, state, action, identifier, reason, actor, **payload):
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": _digest(state["events"][-1]) if state["events"] else None,
             "action": action, "identifier": identifier, "reason": reason, "actor": actor,
             "created_at": datetime.now(timezone.utc).isoformat(), **payload}
    result = deepcopy(state)
    try:
        _apply(result, event)
    except (KeyError, ValueError, TypeError, AttributeError) as error:
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
        raise LocalWorkflowError(f"Cannot append reliability event; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(result, "plans" if action.startswith("plan-") else "readiness", identifier))


def _snapshot(workspace, identifier):
    state = deployment._load(workspace)
    record = deployment._resolve(state, identifier)
    return state, {key: deepcopy(record[key]) for key in
                   ("deployment_id", "configuration", "history", "previous_deployment")}


def _linked(snapshot, record):
    return (snapshot["deployment_id"] == record["deployment_id"]
            and snapshot["configuration"] == record["configuration"]
            and snapshot["previous_deployment"] == record["previous_deployment"]
            and snapshot["history"] == record["history"][:len(snapshot["history"])])


def create_readiness(workspace, deployment_id, reason, actor="developer"):
    state = _load(workspace)
    _, snapshot = _snapshot(workspace, deployment_id)
    return _append(workspace, state, "readiness-create", f"readiness-{len(state['readiness']) + 1:03d}",
                   reason, actor, deployment_snapshot=snapshot)


def create_recovery_plan(workspace, deployment_id, reason, owner="developer", actor="developer"):
    state = _load(workspace)
    deployments, snapshot = _snapshot(workspace, deployment_id)
    target = snapshot["previous_deployment"]
    prior = deepcopy(deployment._resolve(deployments, target)["configuration"]) if target else None
    return _append(workspace, state, "plan-create", f"recovery-plan-{len(state['plans']) + 1:03d}",
                   reason, actor, deployment_snapshot=snapshot, owner=owner, previous_configuration=prior)


def _verify(workspace, plan):
    """Live preparation evidence; retained verification never authorizes rollback."""
    workspace = _readonly(workspace)
    report = _report()
    _finding(report, "passed" if isinstance(plan["owner"], str) and plan["owner"].strip() else "blocked",
             "recovery_owner", f"Recorded owner: {plan['owner']!r}")
    try:
        state = deployment._load(workspace)
        record = deployment._resolve(state, plan["deployment_id"])
        if not _linked(plan["deployment_snapshot"], record):
            raise LocalWorkflowError("Plan snapshot no longer matches deployment history.")
        _finding(report, "passed", "deployment_history", "Deployment history and captured snapshot agree.")
    except LocalWorkflowError as error:
        for check in sorted(VERIFY_CHECKS - {"recovery_owner"}):
            _finding(report, "blocked", check, str(error))
        return report
    target = plan["rollback_target"]
    try:
        if target != record["previous_deployment"] or target != plan["previous_deployment"]:
            raise LocalWorkflowError("Rollback reference differs from the deployment's recorded predecessor.")
        if target:
            prior = deployment._resolve(state, target)
            if prior["configuration"] != plan["previous_configuration"]:
                raise LocalWorkflowError("Previous deployment configuration differs from the recovery plan.")
        _finding(report, "passed" if target else "warnings", "rollback_reference",
                 target or "Initial deployment explicitly restores an empty reference.")
    except LocalWorkflowError as error:
        _finding(report, "blocked", "rollback_reference", str(error))
    try:
        if target:
            saved = plan["previous_configuration"]
            if saved is None:
                raise LocalWorkflowError("Previous configuration snapshot is missing.")
            deployment._eligible(workspace, saved["config_id"], saved)
        elif plan["previous_configuration"] is not None:
            raise LocalWorkflowError("Empty rollback target has an unexpected configuration.")
        _finding(report, "passed" if target else "warnings", "previous_configuration",
                 plan["previous_configuration"]["config_id"] if target else "No previous configuration for the initial deployment.")
    except LocalWorkflowError as error:
        _finding(report, "blocked", "previous_configuration", str(error))
    rollback = deployment._rollback_availability(workspace, state, record)
    eligible = (rollback["available"] and record["stage"] not in {"retired", "rolled_back"}
                and (record["stage"] in {"active", "paused"} or state["selected"] == target))
    _finding(report, "passed" if eligible else "blocked", "rollback_availability",
             rollback["detail"] if eligible else "Deployment or rollback target is not currently eligible for recovery preparation.")
    governance = deployment.deployment_governance_check(workspace, record["deployment_id"])
    _finding(report, "blocked" if governance["blocked"] else "warnings" if governance["warnings"] else "passed",
             "governance", str(governance))
    return report


def verify_recovery(workspace, plan_id, reason="Verify recovery prerequisites", actor="developer"):
    state = _load(workspace)
    plan = _resolve(state, "plans", plan_id)
    return _append(workspace, state, "plan-verify", plan_id, reason, actor, verification=_verify(workspace, plan))


def _latest_plans(state):
    return {p["deployment_id"]: p for p in state["plans"]}


def reliability_check(workspace, deployment_id):
    workspace = _readonly(workspace)
    report = {"mode": MODE, "deployment_id": deployment_id, **_report(), "evidence": {}}
    evidence = report["evidence"]
    try:
        state = deployment._load(workspace)
    except LocalWorkflowError as error:
        _finding(report, "blocked", "audit_completeness", str(error))
    else:
        deployment._resolve(state, deployment_id)  # Unknown IDs are caller errors.
        evidence["audit"] = deployment.deployment_audit(workspace, deployment_id)["events"]
        _finding(report, "passed", "audit_completeness", "Deployment journal replay and complete audit timeline verified.")
    try:
        health = operations.deployment_health(workspace, deployment_id)
        evidence["health"] = health
        _finding(report, "passed", "health_availability", f"Health report available: {health['status']}.")
        rollback = health["rollback"]
        preparable = health["deployment_state"] not in {"retired", "rolled_back"} and rollback["available"]
        _finding(report, "blocked" if not preparable else "warnings" if rollback["empty_reference"] else "passed",
                 "rollback_availability", rollback["detail"] if preparable else "Deployment has no eligible recovery preparation target.")
        governance = health["governance_state"]
        _finding(report, "blocked" if governance["blocked"] else "warnings" if governance["warnings"] else "passed",
                 "governance", str(governance))
    except LocalWorkflowError as error:
        for check in ("health_availability", "rollback_availability", "governance"):
            _finding(report, "blocked", check, str(error))
    try:
        plan = _latest_plans(_load(workspace)).get(deployment_id)
        if plan is None:
            raise LocalWorkflowError("Create a recovery plan for this deployment.")
        evidence["plan"] = plan
        _finding(report, "passed", "recovery_plan", plan["plan_id"])
        verification = _verify(workspace, plan)
        evidence["recovery_verification"] = verification
        bucket = ("blocked" if plan["validation_status"] != "passed" or verification["blocked"]
                  else "warnings" if verification["warnings"] else "passed")
        _finding(report, bucket, "recovery_validation",
                 f"Recorded verification: {plan['validation_status']}; live findings: {verification}")
    except LocalWorkflowError as error:
        # Report both unavailable checks, preserving any already established existence finding.
        if not any(x["check"] == "recovery_plan" for x in report["passed"]):
            _finding(report, "blocked", "recovery_plan", str(error))
        _finding(report, "blocked", "recovery_validation", str(error))
    try:
        history = operations.recovery_history(workspace)
        incidents = [r for r in history["incidents"] if r["deployment_id"] == deployment_id]
        evidence["incidents"] = incidents
        active = [r["operation_id"] for r in incidents if r["status"] in {"open", "investigating"}]
        _finding(report, "warnings" if active else "passed", "incident_consistency",
                 f"History is consistent; active incidents require handoff: {active}." if active
                 else "Incident and recovery history replay consistently; no active incidents.")
    except LocalWorkflowError as error:
        _finding(report, "blocked", "incident_consistency", str(error))
    return report


def transition_readiness(workspace, readiness_id, status, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, "readiness", readiness_id)
    if status not in STATES[record["status"]]:
        raise LocalWorkflowError(f"Invalid readiness transition: {record['status']} -> {status}.")
    report = reliability_check(workspace, record["deployment_id"]) if status in {"passed", "failed"} else None
    return _append(workspace, state, "readiness-transition", readiness_id, reason, actor, status=status, report=report)


def check_readiness(workspace, readiness_id, reason="Check deployment readiness", actor="developer"):
    record = _resolve(_load(workspace), "readiness", readiness_id)
    if record["status"] == "pending":
        transition_readiness(workspace, readiness_id, "checking", reason, actor)
    elif record["status"] != "checking":
        raise LocalWorkflowError("Readiness must be pending or checking; create a new readiness record.")
    state = _load(workspace)
    report = reliability_check(workspace, record["deployment_id"])
    return _append(workspace, state, "readiness-transition", readiness_id, reason, actor,
                   status="failed" if report["blocked"] else "passed", report=report)


def readiness_status(workspace):
    state = _load(workspace)
    reports = {}
    for record in state["readiness"]:
        if record["evidence_digest"] is None:
            record["evidence_current"] = None
        else:
            identifier = record["deployment_id"]
            if identifier not in reports:
                try:
                    reports[identifier] = _digest(reliability_check(workspace, identifier))
                except LocalWorkflowError:
                    reports[identifier] = None
            record["evidence_current"] = record["evidence_digest"] == reports[identifier]
        record["requires_new_check"] = record["status"] == "expired" or record["evidence_current"] is False
    return {"mode": MODE, "readiness": state["readiness"]}


def recovery_plan_status(workspace):
    state = _load(workspace)
    latest = _latest_plans(state)
    for plan in state["plans"]:
        verification = _verify(workspace, plan)
        plan["active"] = latest[plan["deployment_id"]]["plan_id"] == plan["plan_id"]
        plan["live_verification"] = verification
        plan["verification_current"] = plan["verification"] == verification
    return {"mode": MODE, "plans": state["plans"]}


def recovery_plan_inspect(workspace, plan_id):
    plan = _resolve(_load(workspace), "plans", plan_id)
    view = deployment.deployment_inspect(workspace, plan["deployment_id"])
    return {"mode": MODE, "plan": plan, "deployment": view["deployment"],
            "rollback": view["rollback"], "audit_history": view["audit_timeline"],
            "incident_history": [r for r in operations.recovery_history(workspace)["incidents"]
                                 if r["deployment_id"] == plan["deployment_id"]],
            "readiness": [r for r in readiness_status(workspace)["readiness"]
                          if r["deployment_id"] == plan["deployment_id"]],
            "live_verification": _verify(workspace, plan)}
