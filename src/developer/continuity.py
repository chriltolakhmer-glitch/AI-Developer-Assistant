"""Developer continuity knowledge and recovery-reference validation, never execution."""
from copy import deepcopy
from datetime import datetime, timezone
import os
import tempfile

from . import configuration, deployment, promotion, reliability
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read

MODE = "developer-retrieval-continuity"
TYPES = {"configuration_failure", "deployment_failure", "rollback_unavailable", "history_loss"}
STATES = {"planned": {"testing", "retired"}, "testing": {"validated", "failed", "retired"},
          "validated": {"testing", "retired"}, "failed": {"testing", "retired"}, "retired": set()}
CHECKS = {"recovery_plan", "rollback_target", "deployment_history", "configuration_history",
          "audit_history", "ownership", "reliability"}
STEPS = ["Inspect the captured dependencies and live validation findings.",
         "Confirm the scenario owner and recovery-plan owner before handoff.",
         "Review deployment audit, incident history and current governance prerequisites.",
         "Perform any approved restoration manually through the existing governed workflows.",
         "Inspect deployment health and audit results, then record the incident resolution."]


def _root(workspace):
    reliability._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "continuity")


def _resolve(state, identifier):
    for record in state["scenarios"]:
        if record["scenario_id"] == identifier:
            return record
    raise LocalWorkflowError("Unknown disaster scenario ID.")


def _continuity(state, scenario):
    for record in state["continuity"]:
        if record["continuity_id"] == scenario["continuity_id"]:
            return record
    raise LocalWorkflowError("Missing continuity record.")


def _history(record, event, previous, status):
    record["history"].append({"sequence": event["sequence"], "created_at": event["created_at"],
                              "actor": event["actor"], "reason": event["reason"],
                              "previous_status": previous, "status": status})


def _apply(state, event):
    for key in ("created_at", "actor", "reason"):
        reliability._text(event[key])
    if datetime.fromisoformat(event["created_at"]).utcoffset() is None:
        raise ValueError("Continuity timestamps require a timezone")
    if event["action"] == "create":
        reliability._text(event["owner"])
        if event["type"] not in TYPES:
            raise ValueError("Unknown disaster scenario type")
        number = len(state["scenarios"]) + 1
        if event["scenario_id"] != f"disaster-{number:03d}":
            raise ValueError("Invalid disaster scenario ID")
        knowledge = deepcopy(event["knowledge"])
        dep, plan = knowledge["deployment"], knowledge["recovery_plan"]
        if (not dep["history"] or not knowledge["audit_history"]
                or dep["deployment_id"] != plan["deployment_id"]
                or not reliability._linked(plan["deployment_snapshot"], dep)
                or plan["rollback_target"] != dep["previous_deployment"]
                or plan["previous_deployment"] != plan["rollback_target"]
                or (plan["rollback_target"] is None) != (plan["previous_configuration"] is None)
                or any(a["deployment_id"] != dep["deployment_id"] for a in knowledge["audit_history"])):
            raise ValueError("Invalid continuity dependency references")
        for value in (plan["plan_id"], plan["owner"], dep["deployment_id"], dep["config_id"]):
            reliability._text(value)
        if dep["config_id"] != dep["configuration"]["config_id"]:
            raise ValueError("Invalid configuration dependency")
        promotion.validate_settings(dep["configuration"]["settings"])
        if not isinstance(knowledge["restoration_steps"], list) or not knowledge["restoration_steps"]:
            raise ValueError("Missing restoration steps")
        for step in knowledge["restoration_steps"]:
            reliability._text(step)
        target = plan["rollback_target"]
        configs = [dep["configuration"]] + ([plan["previous_configuration"]] if target else [])
        for config in configs:
            reliability._text(config["config_id"])
            promotion.validate_settings(config["settings"])
        continuity_id = f"continuity-{number:03d}"
        scenario = {"scenario_id": event["scenario_id"], "deployment_id": dep["deployment_id"],
                    "type": event["type"], "status": "planned", "owner": event["owner"],
                    "created_at": event["created_at"], "continuity_id": continuity_id,
                    "recovery_plan": plan["plan_id"], "history": [], "tests": []}
        continuity = {"continuity_id": continuity_id, "scenario_id": scenario["scenario_id"],
                      "deployment_id": dep["deployment_id"], "recovery_plan": plan["plan_id"],
                      "owner": event["owner"], "created_at": event["created_at"], "history": [],
                      "validation_status": "pending", "knowledge": knowledge,
                      "deployment_dependencies": [dep["deployment_id"]] + ([target] if target else []),
                      "configuration_dependencies": [c["config_id"] for c in configs],
                      "recovery_references": {"plan_id": plan["plan_id"], "rollback_target": target,
                                              "previous_configuration": (plan["previous_configuration"]["config_id"]
                                                                         if target else None)}}
        _history(scenario, event, None, "planned")
        _history(continuity, event, None, "pending")
        state["scenarios"].append(scenario)
        state["continuity"].append(continuity)
        return
    if event["action"] != "transition":
        raise ValueError("Unknown continuity action")
    scenario = _resolve(state, event["scenario_id"])
    continuity = _continuity(state, scenario)
    status = event["status"]
    if status not in STATES[scenario["status"]]:
        raise LocalWorkflowError(f"Invalid disaster transition: {scenario['status']} -> {status}.")
    report = event["report"]
    if status in {"validated", "failed"}:
        reliability._validate_report(report, CHECKS)
        if (report["scenario_id"] != scenario["scenario_id"] or report["deployment_id"] != scenario["deployment_id"]
                or status != ("failed" if report["blocked"] else "validated")):
            raise ValueError("Disaster outcome does not match validation findings")
        attempt = {"test_id": f"{scenario['scenario_id']}-test-{len(scenario['tests']) + 1:03d}",
                   "test_date": event["created_at"], "scenario_id": scenario["scenario_id"],
                   "owner": scenario["owner"], "actor": event["actor"], "reason": event["reason"],
                   "status": status, "method": "reference_validation_only",
                   "validation_results": deepcopy(report), "findings": reliability._checks(report),
                   "evidence_digest": reliability._digest(report)}
        scenario["tests"].append(attempt)
    elif report is not None:
        raise ValueError("Unexpected disaster validation evidence")
    _history(scenario, event, scenario["status"], status)
    _history(continuity, event, continuity["validation_status"], status)
    if status in {"validated", "failed"}:
        scenario["history"][-1]["test_id"] = attempt["test_id"]
        continuity["history"][-1]["validation_attempt"] = deepcopy(attempt)
    scenario["status"] = status
    continuity["validation_status"] = status


def _load(workspace):
    state = {"mode": MODE, "scenarios": [], "continuity": [], "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1 or event["sequence"] != sequence
                    or event["previous_digest"] != digest or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken continuity journal chain")
            _apply(state, event)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise LocalWorkflowError(f"Invalid continuity journal: {error}") from error
        state["events"].append(event)
        digest = reliability._digest(event)
    return state


def _append(workspace, state, action, identifier, reason, actor, **payload):
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": reliability._digest(state["events"][-1]) if state["events"] else None,
             "action": action, "scenario_id": identifier, "reason": reason, "actor": actor,
             "created_at": datetime.now(timezone.utc).isoformat(), **payload}
    result = deepcopy(state)
    try:
        _apply(result, event)
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
        raise LocalWorkflowError(f"Cannot append continuity event; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(result, identifier))


def create_scenario(workspace, deployment_id, reason, owner="developer", scenario_type="configuration_failure",
                    plan_id=None, actor="developer", restoration_steps=None):
    state = _load(workspace)
    deployments = deployment._load(workspace)
    dep = deployment._resolve(deployments, deployment_id)
    plans = reliability._load(workspace)
    plan = (reliability._resolve(plans, "plans", plan_id) if plan_id else
            reliability._latest_plans(plans).get(deployment_id))
    if plan is None or plan["deployment_id"] != deployment_id:
        raise LocalWorkflowError("Create or select a recovery plan for this deployment first.")
    knowledge = {"deployment": deepcopy(dep), "recovery_plan": deepcopy(plan),
                 "audit_history": deployment.deployment_audit(workspace, deployment_id)["events"],
                 "restoration_steps": deepcopy(STEPS if restoration_steps is None else restoration_steps)}
    return _append(workspace, state, "create", f"disaster-{len(state['scenarios']) + 1:03d}", reason, actor,
                   owner=owner, type=scenario_type, knowledge=knowledge)


def disaster_check(workspace, identifier):
    state = _load(workspace)
    scenario = _resolve(state, identifier)
    continuity = _continuity(state, scenario)
    knowledge = continuity["knowledge"]
    workspace = promotion._ReadOnlyWorkspace(workspace.root, workspace.research_roots)
    report = {"mode": MODE, "scenario_id": identifier, "deployment_id": scenario["deployment_id"],
              **reliability._report(), "evidence": {}}
    evidence = report["evidence"]
    def finding(bucket, check, detail):
        reliability._finding(report, bucket, check, detail)
    finding("passed", "ownership", f"Scenario owner: {scenario['owner']}; captured plan owner: {knowledge['recovery_plan']['owner']}.")
    try:
        plans = reliability._load(workspace)
        plan = reliability._resolve(plans, "plans", scenario["recovery_plan"])
        saved = knowledge["recovery_plan"]
        immutable = ("plan_id", "deployment_id", "owner", "created_at", "deployment_snapshot",
                     "rollback_target", "previous_deployment", "previous_configuration")
        if any(plan[key] != saved[key] for key in immutable):
            raise LocalWorkflowError("Recovery plan differs from captured continuity knowledge.")
        if reliability._latest_plans(plans)[scenario["deployment_id"]]["plan_id"] != plan["plan_id"]:
            raise LocalWorkflowError("Recovery plan was superseded; create a new scenario for the ownership handoff.")
        evidence["recovery_plan"] = plan
        finding("passed", "recovery_plan", plan["plan_id"])
    except LocalWorkflowError as error:
        finding("blocked", "recovery_plan", str(error))
    try:
        deployments = deployment._load(workspace)
        dep = deployment._resolve(deployments, scenario["deployment_id"])
        if not reliability._linked(knowledge["deployment"], dep):
            raise LocalWorkflowError("Captured deployment dependencies no longer match retained history.")
        evidence["deployment"] = dep
        finding("passed", "deployment_history", "Retained deployment history matches captured dependencies.")
    except LocalWorkflowError as error:
        deployments = None
        finding("blocked", "deployment_history", str(error))
    try:
        if deployments is None:
            raise LocalWorkflowError("Cannot trust rollback references without deployment history.")
        target = continuity["recovery_references"]["rollback_target"]
        if target != dep["previous_deployment"]:
            raise LocalWorkflowError("Rollback target differs from captured dependency.")
        if target:
            prior = deployment._resolve(deployments, target)
            if prior["configuration"] != knowledge["recovery_plan"]["previous_configuration"]:
                raise LocalWorkflowError("Rollback target configuration differs from captured dependency.")
            evidence["rollback_deployment"] = prior
        finding("passed" if target else "warnings", "rollback_target",
                target or "Initial deployment restores an explicitly empty reference.")
    except LocalWorkflowError as error:
        finding("blocked", "rollback_target", str(error))
    try:
        configs = configuration.configuration_history(workspace)
        snapshots = [knowledge["deployment"]["configuration"]]
        if knowledge["recovery_plan"]["previous_configuration"] is not None:
            snapshots.append(knowledge["recovery_plan"]["previous_configuration"])
        evidence["configurations"] = []
        for snapshot in snapshots:
            current = configuration._resolve(configs, snapshot["config_id"])
            if deployment._snapshot(current) != snapshot:
                raise LocalWorkflowError("Configuration history differs from captured dependency.")
            evidence["configurations"].append(current)
        finding("passed", "configuration_history", "Current and previous configuration snapshots exist in retained history.")
    except LocalWorkflowError as error:
        finding("blocked", "configuration_history", str(error))
    try:
        audit = deployment.deployment_audit(workspace, scenario["deployment_id"])["events"]
        if audit[:len(knowledge["audit_history"])] != knowledge["audit_history"]:
            raise LocalWorkflowError("Captured audit prefix differs from retained audit history.")
        evidence["audit_history"] = audit
        finding("passed", "audit_history", "Complete audit replay preserves captured history.")
    except LocalWorkflowError as error:
        finding("blocked", "audit_history", str(error))
    try:
        live = reliability.reliability_check(workspace, scenario["deployment_id"])
        evidence["reliability"] = live
        finding("blocked" if live["blocked"] else "warnings" if live["warnings"] else "passed",
                "reliability", f"Current reliability findings: {reliability._checks(live)}")
    except LocalWorkflowError as error:
        finding("blocked", "reliability", str(error))
    return report


def transition_scenario(workspace, identifier, status, reason, actor="developer"):
    state = _load(workspace)
    scenario = _resolve(state, identifier)
    if status not in STATES[scenario["status"]]:
        raise LocalWorkflowError(f"Invalid disaster transition: {scenario['status']} -> {status}.")
    report = disaster_check(workspace, identifier) if status in {"validated", "failed"} else None
    return _append(workspace, state, "transition", identifier, reason, actor, status=status, report=report)


def test_scenario(workspace, identifier, reason="Validate recovery references without execution", actor="developer"):
    scenario = _resolve(_load(workspace), identifier)
    if scenario["status"] != "testing":
        transition_scenario(workspace, identifier, "testing", reason, actor)
    state = _load(workspace)
    report = disaster_check(workspace, identifier)
    return _append(workspace, state, "transition", identifier, reason, actor,
                   status="failed" if report["blocked"] else "validated", report=report)


def disaster_status(workspace):
    state = _load(workspace)
    for scenario in state["scenarios"]:
        scenario["active"] = scenario["status"] != "retired"
        report = disaster_check(workspace, scenario["scenario_id"])
        scenario["live_validation"] = report
        scenario["evidence_current"] = (reliability._digest(report) == scenario["tests"][-1]["evidence_digest"]
                                        if scenario["tests"] else None)
    return {"mode": MODE, "scenarios": state["scenarios"]}


def continuity_status(workspace):
    return {"mode": MODE, "continuity": _load(workspace)["continuity"]}


def disaster_inspect(workspace, identifier):
    state = _load(workspace)
    scenario = _resolve(state, identifier)
    report = disaster_check(workspace, identifier)
    return {"mode": MODE, "scenario": scenario, "continuity": _continuity(state, scenario),
            "validation": report, "deployment_history": report["evidence"].get("deployment", {}).get("history"),
            "recovery_plan": report["evidence"].get("recovery_plan"),
            "audit_history": report["evidence"].get("audit_history")}
