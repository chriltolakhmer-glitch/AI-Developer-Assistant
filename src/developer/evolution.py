"""Developer-only manual recovery evolution records; never executes changes."""
from copy import deepcopy
import os
import tempfile

from . import assurance, maturity, reliability, recovery_governance as governance
from . import assurance_operations as operations
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read

MODE = "developer-recovery-evolution"
STATES = ("planned", "reviewing", "approved", "implemented", "verified", "retired")
TRANSITIONS = {"planned": {"reviewing", "retired"},
               "reviewing": {"planned", "approved", "retired"},
               "approved": {"reviewing", "implemented", "retired"},
               "implemented": {"reviewing", "verified", "retired"},
               "verified": {"retired"}, "retired": set()}
_now = assurance._now


def _root(workspace):
    governance._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "evolution")


def _resolve(state, identifier):
    for record in state["evolutions"]:
        if record["evolution_id"] == identifier:
            return record
    raise LocalWorkflowError("Unknown evolution ID.")


def _strings(values, required=False):
    maturity._strings(values, required)


def _validate_evidence(evidence):
    _strings(evidence["gaps"])
    if not isinstance(evidence["references"], list):
        raise ValueError("Invalid evidence references")
    for reference in evidence["references"]:
        reliability._text(reference["reference"])
        if reference["digest"] != reliability._digest(reference["snapshot"]):
            raise ValueError("Invalid evidence digest")


def _apply(state, event):
    for key in ("actor", "reason", "evolution_id"):
        reliability._text(event[key])
    assurance._timestamp(event["created_at"])
    action = event["action"]
    if action == "create":
        if event["evolution_id"] != f"evolution-{len(state['evolutions']) + 1:03d}":
            raise ValueError("Invalid evolution ID")
        for key in ("capability", "change_type", "owner"):
            reliability._text(event[key])
        record = {key: event[key] for key in ("evolution_id", "capability", "change_type", "owner", "created_at")}
        record.update(status="planned", history=[], impacts=[], plans=[])
        state["evolutions"].append(record)
        previous = None
    else:
        record = _resolve(state, event["evolution_id"])
        previous = record["status"]
        if previous == "retired":
            raise ValueError("Retired evolution is immutable")
        if action == "impact":
            if previous not in {"planned", "reviewing", "implemented"}:
                raise ValueError("Return to reviewing before changing approved scope")
            for key in ("affected_capabilities", "maturity_ids"):
                _strings(event[key], required=True)
            for key in ("related_findings", "review_notes", "risks"):
                _strings(event[key])
            if not set(event["affected_capabilities"]).issubset(maturity.CAPABILITIES):
                raise ValueError("Unknown affected recovery capability")
            if previous == "implemented" and any(event[key] != record["impacts"][-1][key]
                    for key in ("affected_capabilities", "maturity_ids", "related_findings")):
                raise ValueError("Return to reviewing before changing implemented scope")
            _validate_evidence(event["evidence"])
            record["impacts"].append({key: deepcopy(event[key]) for key in
                ("sequence", "created_at", "actor", "reason", "affected_capabilities", "maturity_ids",
                 "related_findings", "review_notes", "risks", "evidence")})
        elif action == "transition":
            target = event["status"]
            if target not in TRANSITIONS[previous]:
                raise ValueError("Invalid evolution state transition")
            reliability._text(event["note"])
            if target in {"approved", "verified"}:
                _validate_evidence(event["evidence"])
                if (not record["impacts"] or record["impacts"][-1]["risks"]
                        or event["evidence"]["gaps"] or event["evidence"] != record["impacts"][-1]["evidence"]):
                    raise ValueError("Decision requires current gap-free impact evidence and no unresolved risks")
            record["status"] = target
        elif action == "plan-add":
            if previous == "verified":
                raise ValueError("Verified evolution requires a new record for further planning")
            for key in ("improvements", "milestones"):
                _strings(event[key], required=True)
            _strings(event["dependencies"])
            reliability._text(event["owner"])
            supersedes = event["supersedes"]
            if supersedes is not None:
                if supersedes not in {p["plan_id"] for p in record["plans"]}:
                    raise ValueError("Unknown prior evolution plan")
                if supersedes in {p["supersedes"] for p in record["plans"]}:
                    raise ValueError("Plan already superseded; revise its successor")
            record["plans"].append({"plan_id": f"{record['evolution_id']}-plan-{len(record['plans']) + 1:03d}",
                **{key: deepcopy(event[key]) for key in ("sequence", "created_at", "actor", "reason", "owner",
                                                         "improvements", "dependencies", "milestones", "supersedes")}})
        else:
            raise ValueError("Unknown evolution action")
    record["updated_at"] = event["created_at"]
    record["history"].append({"previous_status": previous, "status": record["status"], **deepcopy(event)})


def _load(workspace):
    state = {"mode": MODE, "evolutions": [], "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1 or event["sequence"] != sequence
                    or event["previous_digest"] != digest or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken evolution journal chain")
            _apply(state, event)
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
            raise LocalWorkflowError(f"Invalid evolution journal: {error}") from error
        state["events"].append(event)
        digest = reliability._digest(event)
    return state


def _append(workspace, state, action, identifier, reason, actor, **payload):
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": reliability._digest(state["events"][-1]) if state["events"] else None,
             "action": action, "evolution_id": identifier, "reason": reason, "actor": actor,
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
        raise LocalWorkflowError(f"Cannot append evolution event; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(result, identifier))


def create(workspace, capability, change_type, owner, reason, actor="developer"):
    state = _load(workspace)
    return _append(workspace, state, "create", f"evolution-{len(state['evolutions']) + 1:03d}", reason, actor,
                   capability=capability, change_type=change_type, owner=owner)


def _evidence(workspace, impact):
    result = {"references": [], "gaps": []}
    def add(reference, snapshot):
        result["references"].append({"reference": reference, "snapshot": deepcopy(snapshot),
                                     "digest": reliability._digest(snapshot)})
    scope = set()
    for identifier in impact["maturity_ids"]:
        try:
            record = maturity.history(workspace, identifier)["record"]
            scope.update(record["assurance_ids"])
            add(identifier, record)
            report = maturity._review(workspace, record)
            for entry in report["capabilities"]:
                if entry["capability"] in impact["affected_capabilities"]:
                    add(identifier + ":" + entry["capability"], entry)
                    result["gaps"].extend(identifier + ":" + entry["capability"] + ":" + gap for gap in entry["gaps"])
        except LocalWorkflowError as error:
            add(identifier + ":unavailable", {"detail": str(error)})
            result["gaps"].append(identifier + ":maturity_unavailable")
    if impact["related_findings"]:
        try:
            findings = {f["finding_id"]: f for f in operations._load(workspace)["findings"]}
            for identifier in impact["related_findings"]:
                finding = findings.get(identifier)
                if finding is None or finding["assurance_id"] not in scope:
                    result["gaps"].append(identifier + ":finding_unavailable_or_outside_scope")
                else:
                    add(identifier, finding)
                    if finding["status"] != "resolved":
                        result["gaps"].append(identifier + ":finding_unresolved")
        except LocalWorkflowError:
            result["gaps"].append("operations_history_unavailable")
    result["gaps"] = sorted(set(result["gaps"]))
    return result


def record_impact(workspace, identifier, affected_capabilities, maturity_ids, related_findings,
                  review_notes, risks, reason, actor="developer"):
    state = _load(workspace)
    payload = dict(affected_capabilities=affected_capabilities, maturity_ids=maturity_ids,
                   related_findings=related_findings, review_notes=review_notes, risks=risks)
    try:
        for key, values in payload.items():
            _strings(values, required=key in {"affected_capabilities", "maturity_ids"})
        scope = set()
        for key in maturity_ids:
            scope.update(maturity.history(workspace, key)["record"]["assurance_ids"])
        known = {f["finding_id"] for f in operations._load(workspace)["findings"] if f["assurance_id"] in scope}
        if not set(related_findings).issubset(known):
            raise ValueError("Findings must exist within the linked maturity scope")
    except (TypeError, ValueError) as error:
        raise LocalWorkflowError(str(error)) from error
    return _append(workspace, state, "impact", identifier, reason, actor, **payload, evidence=_evidence(workspace, payload))


def transition(workspace, identifier, status, note, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    evidence = _evidence(workspace, record["impacts"][-1]) if status in {"approved", "verified"} and record["impacts"] else {"references": [], "gaps": ["impact_missing"]}
    return _append(workspace, state, "transition", identifier, reason, actor, status=status, note=note, evidence=evidence)


def add_plan(workspace, identifier, improvements, dependencies, milestones, owner, reason, supersedes=None, actor="developer"):
    return _append(workspace, _load(workspace), "plan-add", identifier, reason, actor,
                   improvements=improvements, dependencies=dependencies, milestones=milestones,
                   owner=owner, supersedes=supersedes)


def status(workspace):
    records = _load(workspace)["evolutions"]
    return {"mode": MODE, "evolutions": records, "planned": [r for r in records if r["status"] == "planned"],
            "active": [r for r in records if r["status"] in {"reviewing", "approved", "implemented"}],
            "verified": [r for r in records if r["status"] == "verified"],
            "retired": [r for r in records if r["status"] == "retired"]}


def history(workspace, identifier):
    return {"mode": MODE, "record": deepcopy(_resolve(_load(workspace), identifier))}


def impact(workspace, identifier):
    record = _resolve(_load(workspace), identifier)
    return {"mode": MODE, "evolution_id": identifier, "current": record["impacts"][-1] if record["impacts"] else None,
            "impact_history": record["impacts"]}


def review(workspace, identifier):
    record = _resolve(_load(workspace), identifier)
    result = {"mode": MODE, "evolution_id": identifier, "status": record["status"],
              "ready": [], "warnings": [], "missing_evidence": [], "manual_actions": [], "maturity_impact": []}
    if not record["impacts"]:
        result["missing_evidence"].append("impact_missing")
    else:
        latest = record["impacts"][-1]
        evidence = _evidence(workspace, latest)
        result["maturity_impact"] = evidence["references"]
        result["missing_evidence"].extend(evidence["gaps"])
        result["warnings"].extend(latest["risks"])
        if evidence != latest["evidence"]:
            result["missing_evidence"].append("impact_evidence_stale")
    if result["missing_evidence"] or result["warnings"]:
        result["manual_actions"].append("Review risks and source gaps, refresh maturity assessments, then explicitly record updated impact evidence.")
    elif record["status"] in {"reviewing", "implemented"}:
        result["ready"].append("manual_approval" if record["status"] == "reviewing" else "manual_verification")
    if record["status"] not in {"verified", "retired"}:
        result["manual_actions"].append("Record the next lifecycle decision explicitly; implementation takes place outside this workflow.")
    return result


def plans(workspace):
    records = _load(workspace)["evolutions"]
    return {"mode": MODE, "plans": [{"evolution_id": r["evolution_id"], "capability": r["capability"],
        "current": p["plan_id"] not in {v["supersedes"] for v in r["plans"]}, **p} for r in records for p in r["plans"]]}
