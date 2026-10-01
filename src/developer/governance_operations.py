"""Developer governance operations: explicit decisions, follow-up and closure only."""
from copy import deepcopy
from datetime import date
import hashlib
import os
from pathlib import Path
import tempfile

from . import assurance, strategic_governance as strategic, maturity, reliability
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read

MODE = "developer-recovery-governance-operations"
DECISIONS = {"open": {"reviewing", "deferred"}, "reviewing": {"decided", "deferred", "open"},
             "decided": {"reviewing", "deferred", "closed"}, "deferred": {"reviewing", "open"}, "closed": set()}
ACTIONS = {"open": {"in_progress", "blocked", "cancelled"}, "in_progress": {"blocked", "completed", "cancelled"},
           "blocked": {"open", "in_progress", "cancelled"}, "completed": set(), "cancelled": set()}
EXCEPTIONS = {"open": {"accepted", "mitigated", "expired", "closed"},
              "accepted": {"mitigated", "expired", "closed"}, "mitigated": {"open", "closed"},
              "expired": {"mitigated", "closed"}, "closed": set()}
_now = assurance._now


def _root(workspace):
    strategic._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "governance-operations")


def _resolve(state, identifier):
    for record in state["decisions"]:
        if record["decision_id"] == identifier:
            return record
    raise LocalWorkflowError("Unknown governance decision ID.")


def _child(record, kind, identifier):
    for item in record[kind + "s"]:
        if item[kind + "_id"] == identifier:
            return item
    raise LocalWorkflowError("Unknown linked governance " + kind + " ID.")


def _date(value):
    reliability._text(value)
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Use an ISO due date: YYYY-MM-DD")
    return parsed


def _proof(proof, required=False):
    if proof["manual_reason"] is not None:
        reliability._text(proof["manual_reason"])
    if not isinstance(proof["references"], list):
        raise ValueError("Invalid closure evidence")
    for reference in proof["references"]:
        reliability._text(reference["path"])
        if (Path(reference["path"]).is_absolute() or Path(reference["path"]).drive or ".." in Path(reference["path"]).parts
                or len(reference["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in reference["sha256"])
                or type(reference["size"]) is not int or reference["size"] < 0):
            raise ValueError("Invalid closure evidence reference")
    if required and not proof["references"] and not proof["manual_reason"]:
        raise ValueError("Completion requires evidence or an explicit manual closure reason")


def _source_valid(source):
    if source["digest"] != reliability._digest(source["snapshot"]):
        raise ValueError("Invalid governance source digest")


def _closure_invariants(record, timestamp):
    _proof(record["reviews"][-1]["proof"], required=True)
    for item in record["actions"]:
        reliability._text(item["owner"])
        if item["status"] in {"completed", "cancelled"}:
            _proof(item["completion_evidence"], required=True)
        elif not (item["status"] == "blocked" and item["deferral"] and
                  item["deferral"]["owner"] == item["owner"] and _date(item["deferral"]["until"]) >= timestamp.date()):
            raise ValueError("Closure contains an unfinished action without a current explicit deferral")
    for item in record["exceptions"]:
        reliability._text(item["owner"])
        if item["status"] == "accepted" and assurance._timestamp(item["expires_at"]) > timestamp:
            continue
        if item["status"] not in {"mitigated", "closed"}:
            raise ValueError("Closure contains an unresolved or expired exception")
        _proof(item["closure_evidence"], required=True)


def _apply(state, event):
    for key in ("actor", "reason", "decision_id"):
        reliability._text(event[key])
    timestamp = assurance._timestamp(event["created_at"])
    action = event["action"]
    item, prior_item = None, None
    if action == "create":
        if event["decision_id"] != f"decision-{len(state['decisions']) + 1:03d}":
            raise ValueError("Invalid decision ID")
        for key in ("governance_id", "decision", "owner"):
            reliability._text(event[key])
        _source_valid(event["source"])
        if event["source"]["snapshot"]["record"]["governance_id"] != event["governance_id"]:
            raise ValueError("Mismatched governance objective")
        record = {k: event[k] for k in ("decision_id", "governance_id", "decision", "owner", "created_at")}
        record.update(status="open", history=[], reviews=[], actions=[], exceptions=[])
        state["decisions"].append(record)
        previous = None
    else:
        record = _resolve(state, event["decision_id"])
        previous = record["status"]
        if previous == "closed" and action not in {"action-transition", "action-defer", "action-assign", "exception-transition", "exception-assign"}:
            raise ValueError("Closed decisions allow only follow-up on existing actions and exceptions")
        if action == "assign":
            reliability._text(event["owner"])
            record["owner"] = event["owner"]
        elif action == "review":
            reliability._text(event["note"])
            _source_valid(event["source"])
            if event["source"]["snapshot"]["record"]["governance_id"] != record["governance_id"]:
                raise ValueError("Review references a different governance objective")
            _proof(event["proof"])
            if event["owner"] != record["owner"]:
                raise ValueError("Review owner does not match decision owner")
            record["reviews"].append(deepcopy(event))
        elif action == "transition":
            target = event["status"]
            reliability._text(event["note"])
            if target not in DECISIONS[previous]:
                raise ValueError("Invalid decision transition")
            if target in {"decided", "closed"}:
                _source_valid(event["source"])
                if (not record["reviews"] or record["reviews"][-1]["source"] != event["source"]
                        or record["reviews"][-1]["owner"] != record["owner"]):
                    raise ValueError("A current explicit review by the current owner is required")
            if target == "closed":
                _closure_invariants(record, timestamp)
                if event["closure"]["blocked"] or event["closure"]["decision_id"] != record["decision_id"]:
                    raise ValueError("Decision closure is blocked; inspect governance-close-check")
            record["status"] = target
        elif action in {"action-add", "exception-add"}:
            kind = action.split("-")[0]
            expected = f"{kind}-{sum(len(r[kind + 's']) for r in state['decisions']) + 1:03d}"
            if event[kind + "_id"] != expected:
                raise ValueError("Invalid governance item ID")
            for key in ("owner", "description"):
                reliability._text(event[key])
            item = {kind + "_id": expected, "decision_id": record["decision_id"], "governance_id": record["governance_id"],
                    "owner": event["owner"], "description": event["description"], "status": "open",
                    "created_at": event["created_at"], "history": []}
            if kind == "action":
                _date(event["due_date"])
                item.update(due_date=event["due_date"], completion_evidence=None, deferral=None)
            else:
                expiry = assurance._timestamp(event["expires_at"])
                if expiry <= timestamp:
                    raise ValueError("New exceptions require a future expiration")
                if event["action_id"] is not None:
                    _child(record, "action", event["action_id"])
                item.update(reason=event["reason"], related_item=event["action_id"] or record["decision_id"],
                            expires_at=event["expires_at"], review_history=[], closure_evidence=None)
            record[kind + "s"].append(item)
        elif action.startswith(("action-", "exception-")):
            kind, operation = action.split("-", 1)
            item = _child(record, kind, event[kind + "_id"])
            prior_item = item["status"]
            terminal = {"completed", "cancelled"} if kind == "action" else {"closed"}
            if prior_item in terminal:
                raise ValueError("Terminal governance items are immutable")
            if operation == "assign":
                reliability._text(event["owner"])
                item["owner"] = event["owner"]
                if kind == "action":
                    _date(event["due_date"])
                    item["due_date"] = event["due_date"]
                    item["deferral"] = None
                elif item["status"] == "accepted":
                    item["status"] = "open"
            elif operation == "defer" and kind == "action":
                reliability._text(event["note"])
                if _date(event["deferred_until"]) <= timestamp.date():
                    raise ValueError("Deferral must end on a future UTC date")
                item["status"] = "blocked"
                item["deferral"] = {"until": event["deferred_until"], "note": event["note"], "actor": event["actor"], "owner": item["owner"]}
            elif operation == "transition":
                target = event["status"]
                reliability._text(event["note"])
                if target not in (ACTIONS if kind == "action" else EXCEPTIONS)[prior_item]:
                    raise ValueError("Invalid governance " + kind + " transition")
                _proof(event["proof"], required=target in {"completed", "cancelled", "mitigated", "closed"})
                if kind == "exception" and target == "accepted" and assurance._timestamp(item["expires_at"]) <= timestamp:
                    raise ValueError("Expired exceptions cannot be accepted")
                item["status"] = target
                if kind == "action":
                    item["deferral"] = None
                    if target in {"completed", "cancelled"}:
                        item["completion_evidence"] = deepcopy(event["proof"])
                else:
                    item["review_history"].append(deepcopy(event))
                    if target in {"mitigated", "closed"}:
                        item["closure_evidence"] = deepcopy(event["proof"])
            else:
                raise ValueError("Unknown governance item action")
        else:
            raise ValueError("Unknown governance operations action")
    record["updated_at"] = event["created_at"]
    record["history"].append({"previous_status": previous, "current_status": record["status"], **deepcopy(event)})
    if item is not None:
        item["updated_at"] = event["created_at"]
        item["history"].append({"previous_status": prior_item, "current_status": item["status"], **deepcopy(event)})


def _load(workspace):
    state = {"mode": MODE, "decisions": [], "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1 or event["sequence"] != sequence
                    or event["previous_digest"] != digest or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken decision journal chain")
            _apply(state, event)
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
            raise LocalWorkflowError(f"Invalid decision journal: {error}") from error
        state["events"].append(event)
        digest = reliability._digest(event)
    return state


def _append(workspace, state, action, identifier, reason, actor, **payload):
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": reliability._digest(state["events"][-1]) if state["events"] else None,
             "action": action, "decision_id": identifier, "reason": reason, "actor": actor,
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
        raise LocalWorkflowError(f"Cannot append decision event; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(result, identifier))


def _source(workspace, identifier):
    snapshot = {"record": strategic.history(workspace, identifier)["record"], "review": strategic.review(workspace, identifier)}
    return {"snapshot": snapshot, "digest": reliability._digest(snapshot)}


def _capture(workspace, references, manual_reason):
    _root(workspace)
    try:
        maturity._strings(references)
        result = {"references": [], "manual_reason": manual_reason}
        for reference in references:
            path = Path(reference)
            if path.is_absolute() or path.drive or ".." in path.parts:
                raise ValueError("Evidence must use a contained relative developer-workspace path")
            data = workspace._contained(workspace.root / path).read_bytes()
            result["references"].append({"path": path.as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
        _proof(result)
        return result
    except (OSError, TypeError, ValueError) as error:
        raise LocalWorkflowError(str(error)) from error


def _proof_gaps(workspace, proof):
    if proof is None or (not proof["references"] and not proof["manual_reason"]):
        return ["closure_evidence_missing"]
    gaps = []
    for reference in proof["references"]:
        try:
            live = _capture(workspace, [reference["path"]], None)["references"][0]
            if live != reference:
                gaps.append("evidence_changed:" + reference["path"])
        except LocalWorkflowError:
            gaps.append("evidence_unavailable:" + reference["path"])
    return gaps


def create(workspace, governance_id, decision, owner, reason, actor="developer"):
    state = _load(workspace)
    return _append(workspace, state, "create", f"decision-{len(state['decisions']) + 1:03d}", reason, actor,
                   governance_id=governance_id, decision=decision, owner=owner, source=_source(workspace, governance_id))


def assign(workspace, identifier, owner, reason, actor="developer"):
    return _append(workspace, _load(workspace), "assign", identifier, reason, actor, owner=owner)


def record_review(workspace, identifier, note, references, manual_reason, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    return _append(workspace, state, "review", identifier, reason, actor, note=note, owner=record["owner"],
                   proof=_capture(workspace, references, manual_reason), source=_source(workspace, record["governance_id"]))


def transition(workspace, identifier, status, note, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    source = _source(workspace, record["governance_id"]) if status in {"decided", "closed"} else None
    closure = _close_report(workspace, record) if status == "closed" else None
    return _append(workspace, state, "transition", identifier, reason, actor, status=status, note=note, source=source, closure=closure)


def add_action(workspace, identifier, description, owner, due_date, reason, actor="developer"):
    state = _load(workspace)
    return _append(workspace, state, "action-add", identifier, reason, actor,
                   action_id=f"action-{sum(len(r['actions']) for r in state['decisions']) + 1:03d}",
                   description=description, owner=owner, due_date=due_date)


def assign_action(workspace, identifier, action_id, owner, due_date, reason, actor="developer"):
    return _append(workspace, _load(workspace), "action-assign", identifier, reason, actor,
                   action_id=action_id, owner=owner, due_date=due_date)


def transition_action(workspace, identifier, action_id, status, note, references, manual_reason, reason, actor="developer"):
    return _append(workspace, _load(workspace), "action-transition", identifier, reason, actor, action_id=action_id,
                   status=status, note=note, proof=_capture(workspace, references, manual_reason))


def defer_action(workspace, identifier, action_id, deferred_until, note, reason, actor="developer"):
    return _append(workspace, _load(workspace), "action-defer", identifier, reason, actor, action_id=action_id,
                   deferred_until=deferred_until, note=note)


def add_exception(workspace, identifier, description, owner, expires_at, reason, action_id=None, actor="developer"):
    state = _load(workspace)
    return _append(workspace, state, "exception-add", identifier, reason, actor,
                   exception_id=f"exception-{sum(len(r['exceptions']) for r in state['decisions']) + 1:03d}",
                   description=description, owner=owner, expires_at=expires_at, action_id=action_id)


def assign_exception(workspace, identifier, exception_id, owner, reason, actor="developer"):
    return _append(workspace, _load(workspace), "exception-assign", identifier, reason, actor, exception_id=exception_id, owner=owner)


def transition_exception(workspace, identifier, exception_id, status, note, references, manual_reason, reason, actor="developer"):
    return _append(workspace, _load(workspace), "exception-transition", identifier, reason, actor, exception_id=exception_id,
                   status=status, note=note, proof=_capture(workspace, references, manual_reason))


def _action_view(item):
    deferred = bool(item["status"] == "blocked" and item["deferral"] and
                    _date(item["deferral"]["until"]) >= _now().date() and item["deferral"]["owner"] == item["owner"])
    return {**deepcopy(item), "deferred": deferred,
            "overdue": item["status"] not in {"completed", "cancelled"} and not deferred and _date(item["due_date"]) < _now().date()}


def _exception_view(item):
    expired = item["status"] == "expired" or (item["status"] in {"open", "accepted"} and assurance._timestamp(item["expires_at"]) <= _now())
    return {**deepcopy(item), "expired": expired, "unresolved": expired or item["status"] == "open"}


def decisions(workspace):
    records = _load(workspace)["decisions"]
    return {"mode": MODE, "decisions": records, "open": [r for r in records if r["status"] in {"open", "reviewing", "decided"}],
            "recent": sorted(records, key=lambda r: r["history"][-1]["sequence"], reverse=True)[:10],
            "deferred": [r for r in records if r["status"] == "deferred"], "closed": [r for r in records if r["status"] == "closed"]}


def actions(workspace):
    items = [_action_view(i) for r in _load(workspace)["decisions"] for i in r["actions"]]
    return {"mode": MODE, "actions": items, "open": [i for i in items if i["status"] in {"open", "in_progress"}],
            "blocked": [i for i in items if i["status"] == "blocked"], "overdue": [i for i in items if i["overdue"]],
            "deferred": [i for i in items if i["deferred"]], "completed": [i for i in items if i["status"] == "completed"],
            "cancelled": [i for i in items if i["status"] == "cancelled"]}


def exceptions(workspace):
    items = [_exception_view(i) for r in _load(workspace)["decisions"] for i in r["exceptions"]]
    return {"mode": MODE, "exceptions": items, "active": [i for i in items if i["status"] in {"open", "accepted"} and not i["expired"]],
            "expired": [i for i in items if i["expired"]], "mitigated": [i for i in items if i["status"] == "mitigated"],
            "unresolved": [i for i in items if i["unresolved"]]}


def _close_report(workspace, record):
    blocked, warnings = [], []
    if record["status"] not in {"decided", "closed"}:
        blocked.append("decision_not_decided")
    if not record["owner"].strip():
        blocked.append("decision_owner_missing")
    latest = record["reviews"][-1] if record["reviews"] else None
    if latest is None:
        blocked.append("decision_review_missing")
    else:
        blocked.extend(_proof_gaps(workspace, latest["proof"]))
        if latest["owner"] != record["owner"]:
            blocked.append("decision_owner_review_stale")
    try:
        source = _source(workspace, record["governance_id"])
        if latest and latest["source"] != source:
            blocked.append("governance_review_stale")
        report = source["snapshot"]["review"]
        warnings.extend("related_governance:" + gap for gap in report["warnings"] + report["risks"] + report["missing_evidence"])
        if any(not d["resolved"] for d in report["dependencies"] + report["roadmap_dependencies"]):
            warnings.append("related_governance_dependencies_unresolved")
    except LocalWorkflowError:
        blocked.append("related_governance_unavailable")
    for raw in record["actions"]:
        item = _action_view(raw)
        identifier = item["action_id"]
        if not item["owner"].strip():
            blocked.append(identifier + ":owner_missing")
        if item["status"] in {"completed", "cancelled"}:
            blocked.extend(identifier + ":" + gap for gap in _proof_gaps(workspace, item["completion_evidence"]))
            if item["status"] == "cancelled":
                warnings.append(identifier + ":explicitly_cancelled")
        elif item["deferred"]:
            warnings.append(identifier + ":explicitly_deferred_until:" + item["deferral"]["until"])
        else:
            blocked.append(identifier + ":unresolved_action")
    for raw in record["exceptions"]:
        item = _exception_view(raw)
        identifier = item["exception_id"]
        if not item["owner"].strip():
            blocked.append(identifier + ":owner_missing")
        if item["unresolved"]:
            blocked.append(identifier + ":unresolved_exception")
        elif item["status"] == "accepted":
            warnings.append(identifier + ":documented_acceptance_until:" + item["expires_at"])
        elif item["status"] in {"mitigated", "closed"}:
            blocked.extend(identifier + ":" + gap for gap in _proof_gaps(workspace, item["closure_evidence"]))
    return {"decision_id": record["decision_id"], "status": record["status"], "blocked": blocked, "warnings": warnings,
            "manual_actions": (["Resolve blockers or explicitly document permitted deferrals/exceptions, then inspect closure again."] if blocked else
                               ["Inspect warnings and record closure explicitly; this report changes no state."] if record["status"] != "closed" else [])}


def close_check(workspace):
    reports = [_close_report(workspace, r) for r in _load(workspace)["decisions"]]
    return {"mode": MODE, "passed": [r for r in reports if not r["blocked"]], "blocked": [r for r in reports if r["blocked"]],
            "warnings": [{"decision_id": r["decision_id"], "detail": w} for r in reports for w in r["warnings"]],
            "manual_actions": [{"decision_id": r["decision_id"], "action": a} for r in reports for a in r["manual_actions"]]}


def decision(workspace, identifier):
    record = _resolve(_load(workspace), identifier)
    try:
        related = _source(workspace, record["governance_id"])["snapshot"]
    except LocalWorkflowError as error:
        related = {"unavailable": str(error)}
    return {"mode": MODE, "record": record, "related_governance": related,
            "actions": [_action_view(i) for i in record["actions"]], "exceptions": [_exception_view(i) for i in record["exceptions"]],
            "closure": _close_report(workspace, record)}


def followup(workspace):
    records = _load(workspace)["decisions"]
    action_items = [_action_view(i) for r in records for i in r["actions"]]
    exception_items = [_exception_view(i) for r in records for i in r["exceptions"]]
    reports = [_close_report(workspace, r) for r in records]
    return {"mode": MODE, "decisions": [r for r in records if r["status"] != "closed"],
            "blocked_actions": [i for i in action_items if i["status"] == "blocked"],
            "overdue_actions": [i for i in action_items if i["overdue"]],
            "exceptions": [i for i in exception_items if i["status"] != "closed"],
            "missing_evidence": [{"decision_id": r["decision_id"], "detail": gap} for r in reports for gap in r["blocked"]
                                 if any(word in gap for word in ("evidence", "review", "unavailable"))],
            "ownership_gaps": [{"decision_id": r["decision_id"], "detail": gap} for r in reports for gap in r["blocked"] if "owner" in gap],
            "manual_actions": [{"decision_id": r["decision_id"], "action": a} for r in reports for a in r["manual_actions"]]}
