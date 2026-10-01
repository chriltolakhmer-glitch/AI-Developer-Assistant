"""Developer deployment operations: attributed tracking, never remediation."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
import tempfile

from . import configuration, deployment, promotion
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read

MODE = "developer-retrieval-operations"
TYPES = {"health_check", "incident", "recovery", "rollback", "investigation"}
STATES = {"open": {"investigating", "resolved"}, "investigating": {"resolved"},
          "resolved": {"closed"}, "closed": set()}


def _root(workspace):
    deployment._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "operations")


def _resolve(state, identifier, incident=False):
    for record in state["operations"]:
        if record["operation_id"] == identifier:
            if incident and record["type"] != "incident":
                raise LocalWorkflowError("Operation is not an incident.")
            return record
    raise LocalWorkflowError("Unknown operation ID.")


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise LocalWorkflowError("Operations require nonempty attribution, reasons and recovery actions.")


def _history(record, event, status):
    record["history"].append({"sequence": event["sequence"], "created_at": event["created_at"],
                              "actor": event["actor"], "reason": event["reason"],
                              "previous_status": record["status"], "status": status})
    record["status"] = status


def _new(state, event, kind, snapshot, owner):
    _text(owner)
    if kind not in TYPES:
        raise LocalWorkflowError("Unknown operation type.")
    record = {"operation_id": f"operation-{len(state['operations']) + 1:03d}",
              "deployment_id": snapshot["deployment_id"], "type": kind, "status": None,
              "created_at": event["created_at"], "owner": owner, "reason": event["reason"],
              "deployment_snapshot": deepcopy(snapshot), "history": [], "resolution": None}
    _history(record, event, "open")
    state["operations"].append(record)
    return record


def _apply(state, event, deployments):
    for field in ("actor", "reason", "created_at"):
        _text(event[field])
    if datetime.fromisoformat(event["created_at"]).utcoffset() is None:
        raise ValueError("Operations timestamps require a timezone")
    if event["action"] == "create":
        snapshot = event["deployment_snapshot"]
        current = deployment._resolve(deployments, snapshot["deployment_id"])
        if (set(snapshot) != {"deployment_id", "configuration", "history"}
                or snapshot["configuration"] != current["configuration"]
                or not snapshot["history"]
                or snapshot["history"] != current["history"][:len(snapshot["history"])]):
            raise ValueError("Invalid deployment history reference")
        record = _new(state, event, event["type"], snapshot, event["owner"])
        if record["operation_id"] != event["operation_id"]:
            raise ValueError("Invalid operation ID")
        return
    if event["action"] != "transition":
        raise ValueError("Unknown operation action")
    record = _resolve(state, event["operation_id"])
    status = event["status"]
    if status not in STATES[record["status"]]:
        raise LocalWorkflowError(f"Invalid operation transition: {record['status']} -> {status}.")
    if status == "resolved" and record["type"] == "incident":
        _text(event["recovery_action"])
        reference = event["rollback_reference"]
        if reference is not None and not any(
                a["event_id"] == reference and a["deployment_id"] == record["deployment_id"]
                and a["event_type"] == "rolled_back" for a in deployment._timeline(deployments)):
            raise LocalWorkflowError("Rollback reference must identify this deployment's recorded rollback audit event.")
        recovery = _new(state, event, "recovery", record["deployment_snapshot"], event["actor"])
        recovery["incident_id"] = record["operation_id"]
        recovery["recovery_action"] = event["recovery_action"]
        recovery["rollback_reference"] = reference
        _history(recovery, event, "resolved")
        record["resolution"] = {"recovery_id": recovery["operation_id"],
                                "action": event["recovery_action"], "rollback_reference": reference,
                                "created_at": event["created_at"], "actor": event["actor"],
                                "reason": event["reason"]}
    elif event.get("recovery_action") is not None or event.get("rollback_reference") is not None:
        raise LocalWorkflowError("Recovery details are only allowed when resolving incidents.")
    _history(record, event, status)


def _load(workspace):
    directory = _root(workspace)
    deployments = deployment._load(workspace)
    state = {"mode": MODE, "operations": [], "events": []}
    digest = None
    for path in sorted(directory.glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1
                    or event["sequence"] != sequence or event["previous_digest"] != digest
                    or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken operations journal chain")
            _apply(state, event, deployments)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise LocalWorkflowError(f"Invalid operations journal: {error}") from error
        state["events"].append(event)
        digest = hashlib.sha256(_json_bytes(event)).hexdigest()
    return state


def _append(workspace, state, action, identifier, reason, actor, **payload):
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": (hashlib.sha256(_json_bytes(state["events"][-1])).hexdigest()
                                 if state["events"] else None),
             "action": action, "operation_id": identifier, "reason": reason, "actor": actor,
             "created_at": datetime.now(timezone.utc).isoformat(), **payload}
    result = deepcopy(state)
    try:
        _apply(result, event, deployment._load(workspace))
    except (KeyError, TypeError, ValueError, AttributeError) as error:
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
        raise LocalWorkflowError(f"Cannot append operation; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(result, identifier))


def create_operation(workspace, deployment_id, operation_type, reason, owner="developer", actor="developer"):
    state = _load(workspace)
    record = deployment._resolve(deployment._load(workspace), deployment_id)
    snapshot = {key: deepcopy(record[key]) for key in ("deployment_id", "configuration", "history")}
    return _append(workspace, state, "create", f"operation-{len(state['operations']) + 1:03d}",
                   reason, actor, type=operation_type, owner=owner, deployment_snapshot=snapshot)


def transition_operation(workspace, identifier, status, reason, actor="developer",
                         recovery_action=None, rollback_reference=None):
    return _append(workspace, _load(workspace), "transition", identifier, reason, actor,
                   status=status, recovery_action=recovery_action, rollback_reference=rollback_reference)


def create_incident(workspace, deployment_id, reason, owner="developer", actor="developer"):
    return create_operation(workspace, deployment_id, "incident", reason, owner, actor)


def transition_incident(workspace, identifier, status, reason, actor="developer",
                        recovery_action=None, rollback_reference=None):
    _resolve(_load(workspace), identifier, incident=True)
    return transition_operation(workspace, identifier, status, reason, actor, recovery_action, rollback_reference)


def incident_status(workspace):
    incidents = [r for r in _load(workspace)["operations"] if r["type"] == "incident"]
    return {"mode": MODE, "active": [r for r in incidents if r["status"] in {"open", "investigating"}],
            "resolved": [r for r in incidents if r["status"] == "resolved"],
            "closed": [r for r in incidents if r["status"] == "closed"]}


def deployment_health(workspace, identifier):
    workspace = promotion._ReadOnlyWorkspace(workspace.root, workspace.research_roots)
    view = deployment.deployment_inspect(workspace, identifier)
    record, governance = view["deployment"], view["governance"]
    warnings = deepcopy(governance["warnings"])
    if record["stage"] != "active":
        warnings.append({"check": "deployment_state", "detail": f"Deployment is {record['stage']}."})
    try:
        config = deepcopy(configuration._resolve(configuration.configuration_history(workspace), record["config_id"]))
    except LocalWorkflowError as error:
        config = {"config_id": record["config_id"], "status": "unavailable", "detail": str(error)}
    return {"mode": MODE, "deployment": identifier,
            "status": "blocked" if governance["blocked"] else "warning" if warnings else "healthy",
            "deployment_state": record["stage"], "configuration_state": config,
            "governance_state": governance, "warnings": warnings,
            "rollback_available": view["rollback"]["action_available"], "rollback": view["rollback"],
            "recent_audit_events": view["audit_timeline"][-10:]}


def incident_inspect(workspace, identifier):
    record = _resolve(_load(workspace), identifier, incident=True)
    view = deployment.deployment_inspect(workspace, record["deployment_id"])
    return {"mode": MODE, "incident": record, "deployment_history": view["deployment"]["history"],
            "audit_events": view["audit_timeline"], "health": deployment_health(workspace, record["deployment_id"]),
            "investigation_history": record["history"], "resolution": record["resolution"]}


def recovery_history(workspace):
    state = _load(workspace)
    incidents = [r for r in state["operations"] if r["type"] == "incident"]
    return {"mode": MODE, "incidents": incidents,
            "recovery_actions": [r for r in state["operations"] if r["type"] in {"recovery", "rollback"}],
            "resolution_history": [{"incident_id": r["operation_id"], **r["resolution"]}
                                   for r in incidents if r["resolution"]]}


def incident_diff(workspace, incident_a, incident_b):
    state = _load(workspace)
    left, right = (_resolve(state, identifier, incident=True) for identifier in (incident_a, incident_b))
    return {"mode": MODE, "incident_a": incident_a, "incident_b": incident_b,
            "affected_deployments": {"a": left["deployment_id"], "b": right["deployment_id"]},
            "configuration": configuration.settings_diff(left["deployment_snapshot"]["configuration"],
                                                          right["deployment_snapshot"]["configuration"]),
            "timeline": configuration.settings_diff({"history": left["history"]}, {"history": right["history"]}),
            "resolution": configuration.settings_diff(left["resolution"], right["resolution"])}
