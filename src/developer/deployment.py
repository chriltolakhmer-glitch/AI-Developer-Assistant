"""Explicit deployment control for developer configuration references only."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
import tempfile

from . import configuration, promotion
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read
from .read_context import operation_scoped_load

MODE = "developer-retrieval-deployment"
STAGES = {
    "planned": {"staged", "retired"}, "staged": {"validated", "retired"},
    "validated": {"active", "retired"}, "active": {"paused", "retired", "rolled_back"},
    "paused": {"active", "retired", "rolled_back"},
    "retired": set(), "rolled_back": {"retired"},
}
ACTIONS = {"stage": "staged", "validate": "validated", "activate": "active",
           "pause": "paused", "resume": "active", "retire": "retired", "rollback": "rolled_back"}
AUDIT_TYPES = {"plan": "created", "stage": "staged", "validate": "validated",
               "activate": "activated", "pause": "paused", "resume": "resumed",
               "rollback": "rolled_back", "retire": "retired",
               "superseded": "retired", "restored": "activated"}


def _audit_records(state, event):
    """Normalize every affected record, including implicit retirement/restoration."""
    records = []
    for deployment in state["deployments"]:
        change = deployment["history"][-1]
        if change["sequence"] != event["sequence"]:
            continue
        metadata = {"sequence": event["sequence"], "action": change["action"],
                    "previous_stage": change["previous_stage"], "stage": change["stage"],
                    "trigger_deployment_id": event["deployment_id"],
                    "previous_deployment": deployment["previous_deployment"]}
        evidence = (event.get("restoration_validation") if change["action"] == "restored"
                    else event.get("validation") if change["action"] in {"validate", "activate", "resume"}
                    else None)
        if evidence is not None:
            metadata["validation"] = deepcopy(evidence)
        if change["action"] == "rollback":
            metadata["restoration_validation"] = deepcopy(event["restoration_validation"])
        records.append({"event_id": f"audit-{event['sequence']:08d}-{deployment['deployment_id']}",
                        "deployment_id": deployment["deployment_id"],
                        "event_type": AUDIT_TYPES[change["action"]],
                        "created_at": event["recorded_at"], "actor": event["actor"],
                        "reason": event["reason"], "metadata": metadata})
    return records


def _root(workspace):
    configuration._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "deployments")


def _resolve(state, identifier):
    for record in state["deployments"]:
        if record["deployment_id"] == identifier:
            return record
    raise LocalWorkflowError("Unknown deployment ID.")


def _snapshot(record):
    return {key: deepcopy(value) for key, value in record.items() if key != "status"}


def _eligible(workspace, config_id, expected=None):
    state = configuration.configuration_history(workspace)
    record = configuration._resolve(state, config_id)
    if record["status"] not in {"validated", "active"}:
        raise LocalWorkflowError("Deployment requires a validated configuration.")
    if expected is not None and _snapshot(record) != expected:
        raise LocalWorkflowError("Deployment configuration snapshot changed.")
    configuration._check(workspace, record)
    return record, state


def _evidence(workspace, state, record, restoring=False):
    config, configs = _eligible(workspace, record["config_id"], record["configuration"])
    readonly = promotion._readonly(workspace)
    policy = promotion.policy_check(readonly, config["source_candidate"])
    if policy["blocked"]:
        raise LocalWorkflowError("Deployment blocked by governance policy.")
    prior_id = record["previous_deployment"]
    prior_config = None
    if prior_id:
        prior = _resolve(state, prior_id)
        _eligible(workspace, prior["config_id"], prior["configuration"])
        prior_config = prior["config_id"]
    if not restoring and state["selected"] not in {prior_id, record["deployment_id"]}:
        raise LocalWorkflowError("Deployment reference changed; stage a new deployment.")
    return {"configuration_valid": True, "policy_check_passed": True,
            "rollback_available": True, "source_promotion": config["source_promotion"],
            "review_id": config["review_id"], "policy": policy,
            "previous_deployment": prior_id, "previous_active_configuration": prior_config,
            "configuration_active_reference": configs["active"]}


def _history(record, stage, event, action=None):
    record["history"].append({"stage": stage, "previous_stage": record["stage"],
                              "action": action or event["action"], "sequence": event["sequence"],
                              "recorded_at": event["recorded_at"], "actor": event["actor"],
                              "reason": event["reason"], "deployment_id": event["deployment_id"]})
    record["stage"] = stage


def _validate_evidence(record, evidence):
    if (any(evidence[key] is not True for key in
            ("configuration_valid", "policy_check_passed", "rollback_available"))
            or evidence["source_promotion"] != record["configuration"]["source_promotion"]
            or evidence["review_id"] != record["configuration"]["review_id"]
            or evidence["previous_deployment"] != record["previous_deployment"]
            or evidence["policy"]["blocked"]):
        raise ValueError("Invalid deployment validation evidence")


def _apply(state, event):
    if not all(isinstance(event[key], str) and event[key].strip()
               for key in ("actor", "reason", "recorded_at")):
        raise ValueError("Deployment events require attribution and a reason")
    if datetime.fromisoformat(event["recorded_at"]).utcoffset() is None:
        raise ValueError("Deployment timestamps require a timezone")
    if event["previous_selected"] != state["selected"]:
        raise ValueError("Invalid deployment reference")
    action = event["action"]
    if action == "plan":
        record = deepcopy(event["deployment"])
        expected = f"deployment-{len(state['deployments']) + 1:03d}"
        if (record["deployment_id"] != expected or event["deployment_id"] != expected
                or record["stage"] != "planned" or record["validation"] or record["history"]
                or record["created_at"] != event["recorded_at"] or record["created_by"] != event["actor"]
                or record["previous_deployment"] != state["selected"]
                or record["config_id"] != record["configuration"]["config_id"]):
            raise ValueError("Invalid planned deployment")
        promotion.validate_settings(record["configuration"]["settings"])
        _history(record, "planned", event)
        record["history"][-1]["previous_stage"] = None
        state["deployments"].append(record)
        return
    record = _resolve(state, event["deployment_id"])
    stage = ACTIONS[action]
    if (stage not in STAGES[record["stage"]]
            or (action == "activate" and record["stage"] != "validated")
            or (action == "resume" and record["stage"] != "paused")):
        raise LocalWorkflowError(f"Invalid deployment transition: {record['stage']} -> {stage}.")
    if action in {"stage", "validate", "activate"} and record["previous_deployment"] != state["selected"]:
        raise LocalWorkflowError("Deployment reference changed; stage a new deployment.")
    if action in {"validate", "activate", "resume"}:
        _validate_evidence(record, event["validation"])
        prior = _resolve(state, record["previous_deployment"]) if record["previous_deployment"] else None
        if event["validation"]["previous_active_configuration"] != (prior["config_id"] if prior else None):
            raise ValueError("Invalid previous configuration reference")
        if action in {"activate", "resume"} and event["validation"] != record["validation"]:
            raise LocalWorkflowError("Deployment evidence changed; stage and validate a new deployment.")
        record["validation"] = deepcopy(event["validation"])
    if action == "activate":
        if state["selected"]:
            prior = _resolve(state, state["selected"])
            if prior["stage"] != "active":
                raise LocalWorkflowError("Resume, retire or roll back the paused deployment first.")
            _history(prior, "retired", event, "superseded")
        state["selected"] = record["deployment_id"]
    elif action in {"pause", "resume", "rollback"}:
        if state["selected"] != record["deployment_id"]:
            raise LocalWorkflowError("Only the selected deployment can be paused, resumed or rolled back.")
        if action == "rollback":
            state["selected"] = record["previous_deployment"]
            if state["selected"]:
                prior = _resolve(state, state["selected"])
                if prior["stage"] != "retired" or prior["history"][-1]["action"] != "superseded":
                    raise ValueError("Invalid deployment rollback point")
                _validate_evidence(prior, event["restoration_validation"])
                if event["restoration_validation"] != prior["validation"]:
                    raise LocalWorkflowError("Rollback evidence changed; stage a newly validated deployment.")
                _history(prior, "active", event, "restored")
            elif event["restoration_validation"] is not None:
                raise ValueError("Unexpected restoration evidence")
    elif action == "retire" and state["selected"] == record["deployment_id"]:
        state["selected"] = None
    _history(record, stage, event)


@operation_scoped_load("deployment", _root)
def _load(workspace):
    state = {"mode": MODE, "selected": None, "deployments": [], "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] not in {1, 2}
                    or event["sequence"] != sequence or event["previous_digest"] != digest
                    or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken deployment journal chain")
            _apply(state, event)
            if event["schema_version"] == 2 and event["audit_records"] != _audit_records(state, event):
                raise ValueError("Invalid deployment audit records")
        except (KeyError, TypeError, ValueError, AttributeError, LocalWorkflowError) as error:
            raise LocalWorkflowError(f"Invalid deployment journal: {error}") from error
        state["events"].append(event)
        digest = hashlib.sha256(_json_bytes(event)).hexdigest()
    return state


def _append(workspace, state, action, identifier, reason, actor, **payload):
    event = {"mode": MODE, "schema_version": 2, "sequence": len(state["events"]) + 1,
             "previous_digest": (hashlib.sha256(_json_bytes(state["events"][-1])).hexdigest()
                                 if state["events"] else None),
             "action": action, "deployment_id": identifier, "reason": reason, "actor": actor,
             "recorded_at": datetime.now(timezone.utc).isoformat(),
             "previous_selected": state["selected"], **payload}
    if action == "plan":
        event["deployment"]["created_at"] = event["recorded_at"]
    result = deepcopy(state)
    try:
        _apply(result, event)
        event["audit_records"] = _audit_records(result, event)
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
        raise LocalWorkflowError(f"Cannot append deployment event; inspect status and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(result, identifier))


def create_deployment(workspace, config_id, reason, actor="developer"):
    state = _load(workspace)
    config, _ = _eligible(workspace, config_id)
    if any(d["config_id"] == config_id and d["stage"] not in {"retired", "rolled_back"}
           for d in state["deployments"]):
        raise LocalWorkflowError("Configuration already has a live deployment.")
    identifier = f"deployment-{len(state['deployments']) + 1:03d}"
    record = {"deployment_id": identifier, "config_id": config_id, "stage": "planned",
              "created_at": "", "created_by": actor, "validation": {}, "history": [],
              "configuration": _snapshot(config), "previous_deployment": state["selected"]}
    return _append(workspace, state, "plan", identifier, reason, actor, deployment=record)


def transition_deployment(workspace, identifier, action, reason, actor="developer"):
    if action not in ACTIONS:
        raise LocalWorkflowError("Unknown deployment action.")
    state = _load(workspace)
    record = _resolve(state, identifier)
    payload = {}
    if action == "stage":
        _eligible(workspace, record["config_id"], record["configuration"])
    if action in {"validate", "activate", "resume"}:
        payload["validation"] = _evidence(workspace, state, record)
    if action == "rollback":
        prior = record["previous_deployment"]
        payload["restoration_validation"] = (_evidence(workspace, state, _resolve(state, prior), restoring=True)
                                             if prior else None)
    return _append(workspace, state, action, identifier, reason, actor, **payload)


def stage_deployment(workspace, config_id, reason, actor="developer"):
    planned = [d for d in _load(workspace)["deployments"]
               if d["config_id"] == config_id and d["stage"] == "planned"]
    record = planned[0] if planned else create_deployment(workspace, config_id, reason, actor)
    return transition_deployment(workspace, record["deployment_id"], "stage", reason, actor)


def deployment_status(workspace):
    state = _load(workspace)
    selected = _resolve(state, state["selected"]) if state["selected"] else None
    findings = []
    for record in state["deployments"]:
        if record["stage"] in {"retired", "rolled_back"}:
            continue
        try:
            evidence = _evidence(workspace, state, record)
            if record["validation"] and record["validation"] != evidence:
                raise LocalWorkflowError("Deployment validation evidence is stale.")
        except LocalWorkflowError as error:
            findings.append({"deployment_id": record["deployment_id"], "detail": str(error)})
    return {**state, "selected_deployment": state["selected"],
            "active_deployment": selected["deployment_id"] if selected and selected["stage"] == "active" else None,
            "staged_deployments": [d for d in state["deployments"] if d["stage"] in {"staged", "validated"}],
            "blocked": findings, "runtime_authority": "developer-promotions"}


def deployment_diff(workspace, deployment_a, deployment_b):
    state = _load(workspace)
    left, right = _resolve(state, deployment_a), _resolve(state, deployment_b)
    def fields(record):
        return {k: v for k, v in record.items() if k not in {"configuration", "validation", "history", "stage"}}
    return {"mode": MODE, "deployment_a": deployment_a, "deployment_b": deployment_b,
            "configuration": configuration.settings_diff(left["configuration"], right["configuration"]),
            "deployment": configuration.settings_diff(fields(left), fields(right)),
            "validation": configuration.settings_diff(left["validation"], right["validation"]),
            "lifecycle": configuration.settings_diff(
                {"stage": left["stage"], "history": left["history"]},
                {"stage": right["stage"], "history": right["history"]})}


def _timeline(state):
    replay = {"selected": None, "deployments": []}
    result = []
    for event in state["events"]:
        _apply(replay, event)
        result.extend(_audit_records(replay, event))
    return result


def deployment_audit(workspace, identifier):
    """Return detached audit records; legacy journals are projected without writes."""
    state = _load(workspace)
    _resolve(state, identifier)
    return {"mode": MODE, "deployment_id": identifier,
            "events": [e for e in _timeline(state) if e["deployment_id"] == identifier]}


def _rollback_availability(workspace, state, record):
    target = record["previous_deployment"]
    result = {"target": target, "empty_reference": target is None, "available": False}
    try:
        if target:
            prior = _resolve(state, target)
            evidence = _evidence(workspace, state, prior, restoring=True)
            if evidence != prior["validation"]:
                raise LocalWorkflowError("Rollback target evidence is stale.")
            expected = "retired" if record["stage"] in {"active", "paused"} else "active"
            if prior["stage"] != expected or (expected == "retired" and
                    prior["history"][-1]["action"] != "superseded"):
                raise LocalWorkflowError("Rollback target is not restorable.")
        result["available"] = True
        result["detail"] = "Prior deployment is eligible." if target else "Initial rollout restores an empty reference."
    except LocalWorkflowError as error:
        result["detail"] = str(error)
    result["action_available"] = (result["available"] and state["selected"] == record["deployment_id"]
                                  and record["stage"] in {"active", "paused"})
    return result


def deployment_governance_check(workspace, identifier):
    """Live operational checks only: never repair, approve, or alter a deployment."""
    workspace = promotion._readonly(workspace)
    result = {"passed": [], "warnings": [], "blocked": []}

    def finding(bucket, check, detail):
        result[bucket].append({"check": check, "detail": detail})

    try:
        state = _load(workspace)
    except LocalWorkflowError as error:
        finding("blocked", "audit_history", str(error))
        return result
    record = _resolve(state, identifier)
    finding("passed" if record["created_by"].strip() else "blocked", "ownership",
            f"Recorded owner: {record['created_by']}")
    finding("passed", "lifecycle_state", record["stage"])
    finding("passed", "audit_history", "Complete journal replay and audit records verified.")
    try:
        config = configuration._resolve(configuration.configuration_history(workspace), record["config_id"])
        if _snapshot(config) != record["configuration"] or config["status"] not in {"validated", "active"}:
            raise LocalWorkflowError("Source configuration is changed or ineligible.")
        finding("passed", "source_configuration", record["config_id"])
    except LocalWorkflowError as error:
        finding("blocked", "source_configuration", str(error))
    try:
        configuration._check(workspace, record["configuration"])
        finding("passed", "promotion_approval", record["configuration"]["source_promotion"])
    except LocalWorkflowError as error:
        finding("blocked", "promotion_approval", str(error))
    if not record["validation"]:
        finding("blocked", "validation_evidence", "Deployment has no recorded validation evidence.")
    else:
        try:
            evidence = _evidence(workspace, state, record, restoring=True)
            if evidence != record["validation"]:
                raise LocalWorkflowError("Deployment validation evidence is stale.")
            finding("passed", "validation_evidence", "Recorded evidence matches current prerequisites.")
        except LocalWorkflowError as error:
            finding("blocked", "validation_evidence", str(error))
    rollback = _rollback_availability(workspace, state, record)
    finding("warnings" if rollback["empty_reference"] else ("passed" if rollback["available"] else "blocked"),
            "rollback_target", rollback["detail"])
    if record["stage"] in {"retired", "rolled_back"}:
        finding("warnings", "historical_deployment", "Closed deployment; checks describe current prerequisites.")
    if record["stage"] in {"planned", "staged", "validated"} and record["previous_deployment"] != state["selected"]:
        finding("blocked", "deployment_reference", "Selected reference changed since staging.")
    return result


def deployment_history(workspace):
    state = _load(workspace)
    return {"mode": MODE, "selected_deployment": state["selected"],
            "deployments": [{key: record[key] for key in
                             ("deployment_id", "config_id", "stage", "created_at", "created_by")}
                            for record in reversed(state["deployments"])],
            "events": list(reversed(_timeline(state)))}


def deployment_inspect(workspace, identifier):
    workspace = promotion._readonly(workspace)
    state = _load(workspace)
    record = _resolve(state, identifier)
    source = {"promotion_id": record["configuration"]["source_promotion"], "record": None}
    try:
        source["record"] = deepcopy(promotion._resolve(promotion._load(workspace), source["promotion_id"]))
    except LocalWorkflowError as error:
        source["unavailable_reason"] = str(error)
    return {"mode": MODE, "deployment": deepcopy(record), "source_promotion": source,
            "validation_evidence": deepcopy(record["validation"]),
            "governance": deployment_governance_check(workspace, identifier),
            "audit_timeline": [e for e in _timeline(state) if e["deployment_id"] == identifier],
            "rollback": _rollback_availability(workspace, state, record),
            "runtime_authority": "developer-promotions"}
