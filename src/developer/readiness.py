"""End-to-end developer readiness: integrate existing checks, record manual decisions.

This module has no retrieval, configuration activation, deployment or recovery writes.
Only its external append-only readiness journal is writable.
"""
from copy import deepcopy
import hashlib
import os
import tempfile

from . import (assurance, assurance_operations, configuration, continuity, deployment,
               evolution, governance, governance_operations as decisions, maturity, operations,
               promotion, recovery_governance, reliability,
               strategic_governance as strategic)
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read
from .read_context import DeveloperReadContext, operation_scoped_load

MODE = "developer-retrieval-operational-readiness"
STATES = {
    "not_ready": {"review_required"},
    "review_required": {"not_ready", "ready_for_manual_decision"},
    "ready_for_manual_decision": {"not_ready", "review_required", "approved"},
    "approved": {"not_ready", "review_required", "closed"},
    "closed": set(),
}
COMPONENTS = {"promotion", "configuration", "deployment", "operations", "recovery",
              "assurance", "maturity", "evolution", "governance", "validation", "evidence"}
_now = assurance._now


def _root(workspace):
    promotion._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "readiness")


def _readonly(workspace):
    _root(workspace)
    return promotion._readonly(workspace)


def _resolve(state, identifier):
    for record in state["readiness"]:
        if record["readiness_id"] == identifier:
            return record
    raise LocalWorkflowError("Unknown operational readiness ID.")


def _reference(component, record, key):
    return {"component": component, "record_id": record[key],
            "sha256": reliability._digest(record)}


def _audit_with_context(workspace, deployment_id, decision_id, context):
    """Internal audit implementation; context lifetime is controlled by caller."""
    workspace = _readonly(workspace)
    workspace._read_context = context
    now = _now()
    result = {"mode": MODE, "generated_at": now.isoformat(), "passed": [], "warnings": [],
              "blocked": [], "missing": [], "inconsistent": [], "stale_evidence": [],
              "evidence": [], "lifecycle": {}, "open_actions": [], "open_exceptions": [],
              "manual_decisions": []}

    def finding(bucket, component, check, detail):
        item = {"component": component, "check": check, "detail": str(detail)}
        result[bucket].append(item)
        if bucket in {"missing", "inconsistent"}:
            result["blocked"].append(item)
        if bucket != "passed" and any(word in (check + str(detail)).lower()
                                      for word in ("stale", "expired", "freshness", "changed")):
            if item not in result["stale_evidence"]:
                result["stale_evidence"].append(item)

    def checked(component, callback):
        try:
            return callback()
        except (LocalWorkflowError, OSError, KeyError, TypeError, ValueError) as error:
            finding("blocked", component, "source_unavailable", error)
            return None

    def merge(component, report):
        if report is not None:
            for bucket in ("passed", "warnings", "blocked"):
                for item in report.get(bucket, []):
                    if isinstance(item, dict):
                        finding(bucket, component, item.get("check", "source_check"), item.get("detail", item))
                    else:
                        finding(bucket, component, "source_check", item)

    sources = {
        "promotion": (promotion, "promotions", "promotion_id"),
        "configuration": (configuration, "configurations", "config_id"),
        "deployment": (deployment, "deployments", "deployment_id"),
        "operations": (operations, "operations", "operation_id"),
        "recovery": (reliability, "plans", "plan_id"),
        "continuity": (continuity, "scenarios", "scenario_id"),
        "assurance": (assurance, "assurances", "assurance_id"),
        "recovery_governance": (recovery_governance, "assurances", "assurance_id"),
        "assurance_operations": (assurance_operations, "operations", "operation_id"),
        "maturity": (maturity, "maturities", "maturity_id"),
        "evolution": (evolution, "evolutions", "evolution_id"),
        "governance": (strategic, "governances", "governance_id"),
        "decisions": (decisions, "decisions", "decision_id"),
    }
    states, records = {}, {}
    checked("closure", lambda: _load(workspace))
    for component, (module, collection, key) in sources.items():
        state = checked(component, lambda module=module: module._load(workspace))
        states[component] = state
        rows = state[collection] if state else []
        records[component] = {r[key]: r for r in rows}
        if state is not None:
            finding("passed", component, "audit_history", "Existing journal replay verified")

    health = checked("promotion", lambda: governance.optimize_health(workspace))
    if health:
        for name, check in health["checks"].items():
            if check["status"] == "failed":
                finding("blocked", "promotion", name, check.get("issues", check))
            elif check["status"] == "warnings":
                finding("warnings", "promotion", name, check.get("warnings", check.get("issues", check)))
        if health["checks"]["conflicts"]["unresolved_conflicts"]:
            finding("blocked", "promotion", "unresolved_conflicts", health["checks"]["conflicts"]["unresolved_conflicts"])
        for item in health["checks"]["maintenance"]["stale_candidates"]:
            finding("warnings", "promotion", "stale_evidence", item)

    journal_references = {}

    def link(component, identifier):
        row = records[component].get(identifier)
        if row is None:
            finding("missing", component, "missing_link", identifier or "No lifecycle reference")
        else:
            # Reference the replayed journal tip instead of serializing large source
            # histories into readiness evidence. Its hash chain covers earlier events.
            if component not in journal_references:
                paths = sorted(sources[component][0]._root(workspace).glob("*.json"))
                if not paths:
                    finding("missing", component, "journal_reference", identifier)
                    return row
                path = workspace._contained(paths[-1])
                digest = hashlib.sha256()
                try:
                    with path.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(chunk)
                except OSError as error:
                    finding("blocked", component, "journal_reference", error)
                    return row
                journal_references[component] = {"path": path.relative_to(workspace.root).as_posix(),
                                                 "sha256": digest.hexdigest()}
            result["evidence"].append({"component": component, "record_id": identifier,
                                       **journal_references[component]})
            result["lifecycle"].setdefault(component, []).append(
                {"record_id": identifier, "status": row.get("status", row.get("stage", row.get("level", row.get("validation_status")))),
                 "owner": row.get("owner", row.get("created_by", row.get("approved_by")))})
        return row

    # Detect orphaned references across the whole workspace, including unselected records.
    relations = [("configuration", "source_promotion", "promotion"),
                 ("deployment", "config_id", "configuration"),
                 ("operations", "deployment_id", "deployment"),
                 ("recovery", "deployment_id", "deployment"),
                 ("continuity", "deployment_id", "deployment"),
                 ("continuity", "recovery_plan", "recovery"),
                 ("assurance", "scenario_id", "continuity"),
                 ("recovery_governance", "assurance_id", "assurance"),
                 ("assurance_operations", "assurance_id", "assurance"),
                 ("decisions", "governance_id", "governance")]
    for component, field, target in relations:
        for row in records[component].values():
            if row.get(field) not in records[target]:
                finding("missing", component, "orphaned_record", f"{row[sources[component][2]]}:{field}={row.get(field)}")
    for component, rows in records.items():
        for row in rows.values():
            owner = row.get("owner", row.get("created_by", row.get("approved_by")))
            if not isinstance(owner, str) or not owner.strip():
                finding("missing", component, "ownership", row[sources[component][2]])
            if "created_at" in row:
                timestamp = checked(component, lambda row=row: assurance._timestamp(row["created_at"]))
                if timestamp and timestamp > now:
                    finding("inconsistent", component, "future_timestamp", row[sources[component][2]])

    dep_state = states["deployment"] or {}
    selected = dep_state.get("selected")
    deployment_id = deployment_id or selected
    result["selected_deployment"] = selected
    result["active_configuration"] = (states["configuration"] or {}).get("active")
    result["latest_promotion"] = next(reversed(records["promotion"]), None)
    dep = link("deployment", deployment_id)
    if dep:
        if dep["stage"] != "active" or selected != deployment_id:
            finding("blocked", "deployment", "deployment_state", "Selected deployment must be active")
        config = link("configuration", dep["config_id"])
        if config:
            if config["status"] != "active" or result["active_configuration"] != config["config_id"]:
                finding("blocked", "configuration", "active_reference", "Configuration is inactive or inconsistent with selection")
            checked("configuration", lambda: configuration._check(workspace, config))
            source = link("promotion", config["source_promotion"])
            if source:
                if source["status"] != "promoted":
                    finding("blocked", "promotion", "promotion_state", source["status"])
                proof = checked("promotion", lambda: promotion._evidence(workspace, source["candidate_id"]))
                if proof:
                    candidate, review, validation, _ = proof
                    result["evidence"].extend([_reference("candidate", candidate, "id"),
                                               _reference("review", review, "review_id"),
                                               {"component": "validation", "record_id": source["candidate_id"],
                                                "sha256": reliability._digest(validation)}])
                    if review["review_id"] != source["review_id"] or validation != source["validation_summary"]:
                        finding("inconsistent", "promotion", "stale_validation", "Approval or validation changed")
        merge("deployment", checked("deployment", lambda: deployment.deployment_governance_check(workspace, deployment_id)))
        merge("recovery", checked("recovery", lambda: reliability.reliability_check(workspace, deployment_id)))
        ops = [r for r in records["operations"].values() if r["deployment_id"] == deployment_id]
        if not ops:
            finding("missing", "operations", "operations_tracking", deployment_id)
        for row in ops:
            link("operations", row["operation_id"])
            if row["status"] not in {"resolved", "closed"}:
                finding("blocked", "operations", "unfinished_operation", row["operation_id"])
            if row["type"] == "incident" and row["status"] not in {"closed", "resolved"}:
                finding("blocked", "operations", "unresolved_incident", row["operation_id"])

    # Resolve governance through evolution -> maturity -> assurance -> recovery deployment.
    decision_rows = list(records["decisions"].values())
    if decision_id is None and len(decision_rows) == 1:
        decision_id = decision_rows[0]["decision_id"]
    elif decision_id is None and len(decision_rows) > 1:
        finding("blocked", "governance", "ambiguous_decision", "Specify a decision ID")
    decision = link("decisions", decision_id)
    if decision:
        report = checked("governance", lambda: decisions._close_report(workspace, decision))
        merge("governance", report)
        result["open_actions"] = [decisions._action_view(i) for i in decision["actions"]
                                  if i["status"] not in {"completed", "cancelled"}]
        result["open_exceptions"] = [decisions._exception_view(i) for i in decision["exceptions"]
                                      if i["status"] != "closed"]
        for item in result["open_exceptions"]:
            if item["expired"]:
                finding("blocked", "governance", "expired_exception", item["exception_id"])
        result["evidence"].extend(_reference("actions", i, "action_id") for i in decision["actions"])
        result["evidence"].extend(_reference("exceptions", i, "exception_id") for i in decision["exceptions"])
        gov = link("governance", decision["governance_id"])
        if gov:
            review = checked("governance", lambda: strategic.review(workspace, gov["governance_id"]))
            if review:
                for gap in review["missing_evidence"]:
                    finding("blocked", "governance", "governance_evidence", gap)
                for gap in review["warnings"] + review["risks"]:
                    finding("warnings", "governance", "governance_review", gap)
                if not review["review_current"]:
                    finding("blocked", "governance", "stale_review", gov["governance_id"])
                for dependency in review["dependencies"] + review["roadmap_dependencies"]:
                    if not dependency["resolved"]:
                        finding("blocked", "governance", "unresolved_dependency", dependency)
            if not gov["evolution_ids"]:
                finding("missing", "evolution", "missing_link", "Governance has no linked evolution")
            connected = set()
            for eid in gov["evolution_ids"]:
                evolved = link("evolution", eid)
                if not evolved:
                    continue
                review = checked("evolution", lambda eid=eid: evolution.review(workspace, eid))
                if review:
                    for gap in review["missing_evidence"]:
                        finding("blocked", "evolution", "evolution_evidence", gap)
                    for warning in review["warnings"]:
                        finding("warnings", "evolution", "evolution_risk", warning)
                if not evolved["impacts"]:
                    finding("missing", "maturity", "missing_link", eid)
                    continue
                for mid in evolved["impacts"][-1]["maturity_ids"]:
                    mature = link("maturity", mid)
                    if not mature:
                        continue
                    review = checked("maturity", lambda mature=mature: maturity._review(workspace, mature))
                    if review and not review["ready"]:
                        finding("blocked", "maturity", "readiness_disagreement", review["missing_evidence"])
                    for aid in mature["assurance_ids"]:
                        owned = link("recovery_governance", aid)
                        if owned:
                            review = checked("assurance", lambda aid=aid: recovery_governance.review(workspace, aid))
                            if review:
                                for gap in review.get("findings", []):
                                    finding("blocked", "assurance", "governance_gap", gap)
                        assured = link("assurance", aid)
                        if not assured:
                            continue
                        if assured["status"] != "passed":
                            finding("blocked", "assurance", "linked_assurance_state", assured["status"])
                        scenario = link("continuity", assured["scenario_id"])
                        if scenario:
                            connected.add(scenario["deployment_id"])
                            plan = link("recovery", scenario["recovery_plan"])
                            if plan:
                                merge("recovery", checked("recovery", lambda plan=plan: reliability._verify(workspace, plan)))
                                if plan["validation_status"] != "passed":
                                    finding("blocked", "recovery", "required_validation", plan["plan_id"])
                            view = checked("assurance", lambda scenario=scenario: assurance.recovery_assurance(workspace, scenario["scenario_id"]))
                            if view:
                                merge("assurance", view["verification"])
                                if view["recovery_readiness"] != "passed":
                                    finding("blocked", "assurance", "assurance_state", view["recovery_readiness"])
                                for stale in view["evidence"]["expired"]:
                                    if stale["assurance_id"] == aid:
                                        finding("blocked", "assurance", "stale_evidence", stale["reason"])
            if deployment_id not in connected:
                finding("inconsistent", "governance", "deployment_linkage", "Governance assurance chain does not reference this deployment")
            elif connected != {deployment_id}:
                finding("warnings", "governance", "broader_scope", "Governance also covers other deployments")
    # Global orphan checks for indirect array relationships.
    for component, field, target in (("maturity", "assurance_ids", "assurance"),
                                     ("governance", "evolution_ids", "evolution")):
        for row in records[component].values():
            for identifier in row[field]:
                if identifier not in records[target]:
                    finding("missing", component, "orphaned_record", identifier)
    for evolved in records["evolution"].values():
        if evolved["impacts"]:
            for identifier in evolved["impacts"][-1]["maturity_ids"]:
                if identifier not in records["maturity"]:
                    finding("missing", "evolution", "orphaned_record", identifier)
    result["deployment_id"], result["decision_id"] = deployment_id, decision_id
    result["manual_decisions"] = (["Resolve blocking findings manually and refresh readiness evidence"] if result["blocked"]
                                  else ["Inspect warnings, record readiness review, then explicitly approve and close"])
    # Stable digest deliberately excludes reporting time; freshness is supplied by source checks.
    stable = {k: v for k, v in result.items() if k not in {"generated_at", "manual_decisions"}}
    result["evidence_digest"] = reliability._digest(stable)
    return result


def audit(workspace, deployment_id=None, decision_id=None):
    """Read-only audit with validated journal reuse limited to this invocation."""
    return _audit_with_context(workspace, deployment_id, decision_id, DeveloperReadContext())


def _apply(state, event):
    for key in ("actor", "reason", "readiness_id"):
        reliability._text(event[key])
    assurance._timestamp(event["created_at"])
    action = event["action"]
    if action == "create":
        if event["readiness_id"] != f"retrieval-readiness-{len(state['readiness']) + 1:03d}":
            raise ValueError("Invalid readiness ID")
        for key in ("owner", "deployment_id", "decision_id"):
            reliability._text(event[key])
        record = {k: event[k] for k in ("readiness_id", "owner", "deployment_id", "decision_id", "created_at")}
        record.update(status="not_ready", history=[], evidence_bundles=[], reviews=[], followups=[], closure=None)
        state["readiness"].append(record)
    else:
        record = _resolve(state, event["readiness_id"])
        if record["status"] == "closed":
            raise ValueError("Closed readiness is immutable; create a new readiness record")
    report = event["evidence"]
    if (not isinstance(report["evidence"], list) or
            report["deployment_id"] != record["deployment_id"] or report["decision_id"] != record["decision_id"]):
        raise ValueError("Mismatched readiness evidence")
    stable = {k: v for k, v in report.items() if k not in {"generated_at", "manual_decisions", "evidence_digest"}}
    if reliability._digest(stable) != report["evidence_digest"]:
        raise ValueError("Invalid readiness evidence digest")
    if action == "evidence":
        record["evidence_bundles"].append({"sequence": event["sequence"], "created_at": event["created_at"],
                                           "references": report["evidence"], "digest": report["evidence_digest"]})
    elif action == "review":
        if record["status"] != "review_required" or event["owner"] != record["owner"]:
            raise ValueError("Review requires review_required and the readiness owner")
        reliability._text(event["note"])
        record["reviews"].append({"owner": event["owner"], "note": event["note"],
                                   "digest": report["evidence_digest"], "created_at": event["created_at"]})
    elif action == "transition":
        target = event["status"]
        if target not in STATES[record["status"]]:
            raise ValueError("Invalid readiness transition")
        if target in {"ready_for_manual_decision", "approved", "closed"}:
            if report["blocked"]:
                raise ValueError("Readiness has blocking findings")
            if not record["reviews"] or record["reviews"][-1]["digest"] != report["evidence_digest"]:
                raise ValueError("A current explicit readiness review is required")
        if target in {"approved", "closed"} and event["confirmed"] is not True:
            raise ValueError("Manual confirmation is required")
        if target == "closed":
            if event["owner"] != record["owner"]:
                raise ValueError("Closure owner must match readiness owner")
            if not record["evidence_bundles"] or record["evidence_bundles"][-1]["digest"] != report["evidence_digest"]:
                raise ValueError("A current readiness evidence bundle is required")
            outstanding = [i for i in record["followups"] if i["status"] == "open"]
            if outstanding and not event["outstanding_reason"]:
                raise ValueError("Document outstanding non-blocking follow-ups before closure")
            if event["outstanding_reason"] is not None:
                reliability._text(event["outstanding_reason"])
            record["closure"] = {"owner": event["owner"], "reason": event["reason"],
                                  "created_at": event["created_at"], "references": report["evidence"],
                                  "outstanding_items": outstanding + report["warnings"] + report["open_actions"] + report["open_exceptions"],
                                  "outstanding_reason": event["outstanding_reason"]}
        record["status"] = target
    elif action == "followup":
        item = event["followup"]
        for key in ("owner", "reason", "recommended_manual_action"):
            reliability._text(item[key])
        if item["component"] not in COMPONENTS or item["status"] != "open":
            raise ValueError("Invalid follow-up component or state")
        if assurance._timestamp(item["due_at"]) <= assurance._timestamp(event["created_at"]):
            raise ValueError("Follow-up due_at must be in the future")
        if item["created_at"] != event["created_at"] or item["followup_id"] != f"{record['readiness_id']}-followup-{len(record['followups']) + 1:03d}":
            raise ValueError("Invalid follow-up identity")
        record["followups"].append(deepcopy(item))
    elif action == "followup-complete":
        item = next((i for i in record["followups"] if i["followup_id"] == event["followup_id"]), None)
        if item is None or item["status"] != "open" or item["owner"] != event["owner"]:
            raise ValueError("Completion requires an open follow-up and its owner")
        reliability._text(event["note"])
        item.update(status="completed", completed_at=event["created_at"], completion_reason=event["note"],
                    completion_references=report["evidence"])
    elif action != "create":
        raise ValueError("Unknown readiness action")
    record["latest_evidence"] = deepcopy(report)
    record["history"].append({"sequence": event["sequence"], "action": action, "status": record["status"],
                               "created_at": event["created_at"], "actor": event["actor"], "reason": event["reason"]})


@operation_scoped_load("readiness", _root)
def _load(workspace):
    state = {"mode": MODE, "readiness": [], "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1 or event["sequence"] != sequence
                    or event["previous_digest"] != digest or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken readiness journal chain")
            _apply(state, event)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise LocalWorkflowError(f"Invalid readiness journal: {error}") from error
        state["events"].append(event)
        digest = reliability._digest(event)
    return state


def _append(workspace, state, action, identifier, reason, actor, evidence, **payload):
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": reliability._digest(state["events"][-1]) if state["events"] else None,
             "action": action, "readiness_id": identifier, "reason": reason, "actor": actor,
             "created_at": evidence["generated_at"], "evidence": evidence, **payload}
    replay = deepcopy(state)
    try:
        _apply(replay, event)
    except (KeyError, TypeError, ValueError, AttributeError) as error:
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
        raise LocalWorkflowError(f"Cannot append readiness event; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(replay, identifier))


def create(workspace, deployment_id, decision_id, owner, reason, actor="developer"):
    state = _load(workspace)
    report = audit(workspace, deployment_id, decision_id)
    # Existing records are mandatory; incomplete chains can still be recorded as not_ready.
    deployment._resolve(deployment._load(_readonly(workspace)), deployment_id)
    decisions._resolve(decisions._load(_readonly(workspace)), decision_id)
    return _append(workspace, state, "create", f"retrieval-readiness-{len(state['readiness']) + 1:03d}",
                   reason, actor, report, deployment_id=deployment_id, decision_id=decision_id, owner=owner)


def _current(workspace, state, identifier):
    record = _resolve(state, identifier)
    return record, audit(workspace, record["deployment_id"], record["decision_id"])


def status(workspace, identifier=None, deployment_id=None, decision_id=None):
    state = _load(workspace)
    if identifier:
        record, report = _current(workspace, state, identifier)
    else:
        record = state["readiness"][-1] if state["readiness"] and not (deployment_id or decision_id) else None
        report = audit(workspace, record["deployment_id"], record["decision_id"]) if record else audit(workspace, deployment_id, decision_id)
    computed = "not_ready" if report["blocked"] else "review_required" if report["warnings"] else "ready_for_manual_decision"
    stale = bool(record and record["latest_evidence"]["evidence_digest"] != report["evidence_digest"])
    return {"mode": MODE, "generated_at": report["generated_at"],
            "status": record["status"] if record else computed, "current_readiness": computed,
            "readiness_id": record["readiness_id"] if record else None, "owner": record["owner"] if record else None,
            "recorded_evidence_stale": stale, "blocking": report["blocked"], "warnings": report["warnings"],
            "manual_decisions": report["manual_decisions"], "stale_evidence": report["stale_evidence"],
            "open_actions": report["open_actions"], "open_exceptions": report["open_exceptions"],
            "active_configuration": report["active_configuration"], "latest_promotion": report["latest_promotion"],
            "lifecycle": report["lifecycle"], "evidence": report["evidence"],
            "evidence_freshness": "stale" if stale or report["stale_evidence"] else "missing" if report["missing"] else "current",
            "followups": deepcopy(record["followups"]) if record else []}


def history(workspace, identifier):
    return {"mode": MODE, "record": deepcopy(_resolve(_load(workspace), identifier))}


def evidence(workspace, identifier=None, reason="Capture end-to-end readiness evidence references", actor="developer"):
    state = _load(workspace)
    if identifier is None:
        if not state["readiness"]:
            raise LocalWorkflowError("Create an operational readiness record before capturing its evidence bundle")
        identifier = state["readiness"][-1]["readiness_id"]
    _, report = _current(workspace, state, identifier)
    return _append(workspace, state, "evidence", identifier, reason, actor, report)


def review(workspace, identifier, owner, note, reason, actor="developer"):
    state = _load(workspace)
    _, report = _current(workspace, state, identifier)
    return _append(workspace, state, "review", identifier, reason, actor, report, owner=owner, note=note)


def transition(workspace, identifier, target, reason, confirmed=False, actor="developer"):
    if target == "closed":
        raise LocalWorkflowError("Use readiness-close with closure owner and manual confirmation")
    state = _load(workspace)
    _, report = _current(workspace, state, identifier)
    return _append(workspace, state, "transition", identifier, reason, actor, report, status=target, confirmed=confirmed)


def close(workspace, identifier, owner, reason, confirmed=False, outstanding_reason=None, actor="developer"):
    state = _load(workspace)
    _, report = _current(workspace, state, identifier)
    return _append(workspace, state, "transition", identifier, reason, actor, report, status="closed", owner=owner,
                   confirmed=confirmed, outstanding_reason=outstanding_reason)


def followup(workspace, identifier, owner, component, recommended_action, due_at, reason, actor="developer"):
    state = _load(workspace)
    record, report = _current(workspace, state, identifier)
    item = {"followup_id": f"{identifier}-followup-{len(record['followups']) + 1:03d}", "owner": owner,
            "component": component, "reason": reason, "recommended_manual_action": recommended_action,
            "created_at": report["generated_at"], "due_at": due_at, "status": "open"}
    return _append(workspace, state, "followup", identifier, reason, actor, report, followup=item)


def complete_followup(workspace, identifier, followup_id, owner, note, reason, actor="developer"):
    state = _load(workspace)
    _, report = _current(workspace, state, identifier)
    return _append(workspace, state, "followup-complete", identifier, reason, actor, report,
                   followup_id=followup_id, owner=owner, note=note)
