"""Manual developer recovery capability maturity; no scoring or automatic promotion."""
from copy import deepcopy
import os
import tempfile

from . import assurance, assurance_operations as operations, configuration, continuity
from . import recovery_governance as governance, reliability
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read

MODE = "developer-recovery-maturity"
LEVELS = ("initial", "defined", "managed", "measured", "improving")
CAPABILITIES = ("recovery-ownership", "recovery-evidence-validation", "recovery-review-cycle",
                "recovery-improvement-planning")
CRITERIA = {level: CAPABILITIES[:index] for index, level in enumerate(LEVELS)}
_now = assurance._now


def _root(workspace):
    governance._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "maturity")


def _resolve(state, identifier):
    for record in state["maturities"]:
        if record["maturity_id"] == identifier:
            return record
    raise LocalWorkflowError("Unknown maturity ID.")


def _strings(values, required=False):
    if not isinstance(values, list) or (required and not values) or len(values) != len(set(values)):
        raise ValueError("Expected a list of distinct text values")
    for value in values:
        reliability._text(value)


def _plan(record, identifier):
    for plan in record["plans"]:
        if plan["plan_id"] == identifier:
            return plan
    raise LocalWorkflowError("Unknown maturity plan ID.")


def _apply(state, event):
    for key in ("actor", "reason", "maturity_id"):
        reliability._text(event[key])
    assurance._timestamp(event["created_at"])
    action = event["action"]
    if action == "create":
        if event["maturity_id"] != f"maturity-{len(state['maturities']) + 1:03d}":
            raise ValueError("Invalid maturity ID")
        reliability._text(event["assurance_area"])
        reliability._text(event["owner"])
        _strings(event["assurance_ids"], required=True)
        if any(r["assurance_area"] == event["assurance_area"] for r in state["maturities"]):
            raise ValueError("Maturity area already exists")
        record = {"maturity_id": event["maturity_id"], "assurance_area": event["assurance_area"],
                  "level": "initial", "owner": event["owner"], "created_at": event["created_at"],
                  "updated_at": event["created_at"], "assurance_ids": event["assurance_ids"][:],
                  "required_capabilities": list(CAPABILITIES), "history": [], "assessments": [], "plans": []}
        state["maturities"].append(record)
        previous = None
    else:
        record = _resolve(state, event["maturity_id"])
        previous = record["level"]
        if action == "assign":
            reliability._text(event["owner"])
            record["owner"] = event["owner"]
        elif action == "assess":
            capability, evidence = event["capability"], event["evidence"]
            if capability not in CAPABILITIES or set(evidence) != {"references", "gaps"}:
                raise ValueError("Invalid capability assessment")
            _strings(event["gaps"])
            _strings(event["improvement_notes"])
            _strings(evidence["gaps"])
            for reference in evidence["references"]:
                if reference["digest"] != reliability._digest(reference["snapshot"]):
                    raise ValueError("Invalid assessment evidence digest")
                reliability._text(reference["reference"])
            old = next((a for a in reversed(record["assessments"]) if a["capability"] == capability), None)
            record["assessments"].append({"assessment_id": f"{record['maturity_id']}-assessment-{len(record['assessments']) + 1:03d}",
                "capability": capability, "level": record["level"], "owner": record["owner"],
                "sequence": event["sequence"], "created_at": event["created_at"], "actor": event["actor"],
                "evidence_references": deepcopy(evidence["references"]),
                "gaps": sorted(set(evidence["gaps"] + event["gaps"])), "manual_gaps": event["gaps"][:],
                "improvement_notes": event["improvement_notes"][:], "evidence_digest": reliability._digest(evidence),
                "evidence_changes": configuration.settings_diff(
                    {r["reference"]: r["snapshot"] for r in old["evidence_references"]} if old else {},
                    {r["reference"]: r["snapshot"] for r in evidence["references"]})})
        elif action == "transition":
            target = event["level"]
            if target not in LEVELS or abs(LEVELS.index(target) - LEVELS.index(record["level"])) != 1:
                raise ValueError("Maturity changes must move one adjacent level at a time")
            if LEVELS.index(target) > LEVELS.index(record["level"]):
                if event["criteria"] != list(CRITERIA[target]):
                    raise ValueError("Invalid maturity promotion criteria")
                for capability in CRITERIA[target]:
                    latest = next((a for a in reversed(record["assessments"]) if a["capability"] == capability), None)
                    if not latest or latest["gaps"] or latest["owner"] != record["owner"] or event["evidence_digests"].get(capability) != latest["evidence_digest"]:
                        raise ValueError("Promotion requires current gap-free assessments owned by the maturity owner")
            record["level"] = target
        elif action == "plan-add":
            _strings(event["capabilities"], required=True)
            _strings(event["improvements"], required=True)
            _strings(event["linked_findings"])
            if not set(event["capabilities"]).issubset(CAPABILITIES):
                raise ValueError("Unknown affected capability")
            supersedes = event["supersedes"]
            if supersedes:
                _plan(record, supersedes)
            record["plans"].append({"plan_id": f"{record['maturity_id']}-plan-{len(record['plans']) + 1:03d}",
                "status": "planned", "owner": record["owner"], "created_at": event["created_at"],
                "sequence": event["sequence"], "planned_improvements": event["improvements"][:],
                "affected_capabilities": event["capabilities"][:], "linked_findings": event["linked_findings"][:],
                "finding_snapshots": deepcopy(event["finding_snapshots"]), "supersedes": supersedes, "review_history": []})
        elif action == "plan-review":
            plan = _plan(record, event["plan_id"])
            if plan["status"] == "completed" or event["status"] not in {"reviewed", "deferred", "completed"}:
                raise ValueError("Invalid improvement plan review state")
            if event["status"] == "completed" and (plan["status"] != "reviewed" or event["review_evidence"]["gaps"]):
                raise ValueError("Completion requires a reviewed plan and current gap-free evidence")
            reliability._text(event["note"])
            plan["status"] = event["status"]
            plan["review_history"].append({key: deepcopy(event[key]) for key in
                                          ("sequence", "created_at", "actor", "reason", "status", "note", "review_evidence")})
        else:
            raise ValueError("Unknown maturity action")
    record["updated_at"] = event["created_at"]
    record["history"].append({"sequence": event["sequence"], "created_at": event["created_at"],
        "actor": event["actor"], "reason": event["reason"], "action": action,
        "previous_level": previous, "level": record["level"], "owner": record["owner"],
        "details": deepcopy({k: v for k, v in event.items() if k in
                             {"capability", "gaps", "improvement_notes", "plan_id", "status", "note", "improvements", "supersedes"}})})


def _load(workspace):
    state = {"mode": MODE, "maturities": [], "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1 or event["sequence"] != sequence
                    or event["previous_digest"] != digest or path.name != f"{sequence:08d}.json"):
                raise ValueError("Broken maturity journal chain")
            _apply(state, event)
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
            raise LocalWorkflowError(f"Invalid maturity journal: {error}") from error
        state["events"].append(event)
        digest = reliability._digest(event)
    return state


def _append(workspace, state, action, identifier, reason, actor, **payload):
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": reliability._digest(state["events"][-1]) if state["events"] else None,
             "action": action, "maturity_id": identifier, "reason": reason, "actor": actor,
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
        raise LocalWorkflowError(f"Cannot append maturity event; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return deepcopy(_resolve(result, identifier))


def _evidence(workspace, record, capability):
    result = {"references": [], "gaps": []}
    def add(reference, snapshot):
        result["references"].append({"reference": reference, "snapshot": deepcopy(snapshot),
                                     "digest": reliability._digest(snapshot)})
    for identifier in record["assurance_ids"]:
        try:
            report = governance.review(workspace, identifier)
            source = report["record"]
            if capability == CAPABILITIES[0]:
                add(identifier + ":ownership", {k: source[k] for k in ("owner", "responsibility", "ownership_changed_at")})
                result["gaps"].extend(identifier + ":" + f for f in report["findings"] if f.startswith("ownership"))
            elif capability == CAPABILITIES[1]:
                add(identifier + ":verification", {"verification_history": source["verification_history"],
                    "status": source["status"], "schedule": source["verification_schedule"], "next_check": source["next_check"],
                    "findings": report["findings"], "missing_evidence": report["missing_evidence"]})
                result["gaps"].extend(identifier + ":" + f for f in report["findings"])
            elif capability == CAPABILITIES[2]:
                state = operations._load(workspace)
                reviews = [v for r in state["operations"] if r["assurance_id"] == identifier for v in r["reviews"]]
                reviews.sort(key=lambda v: v["sequence"])
                findings = [f for f in state["findings"] if f["assurance_id"] == identifier and f["status"] == "open"]
                add(identifier + ":operations", {"reviews": reviews, "open_findings": findings})
                if not reviews:
                    result["gaps"].append(identifier + ":review_missing")
                elif reviews[-1]["snapshot"]["record"] != source or reviews[-1]["snapshot"]["findings"] != report["findings"]:
                    result["gaps"].append(identifier + ":review_stale")
                result["gaps"].extend(f["finding_id"] for f in findings)
            else:
                add(identifier + ":current_findings", report["findings"])
                result["gaps"].extend(identifier + ":" + f for f in report["findings"])
        except LocalWorkflowError as error:
            add(identifier + ":unavailable", {"detail": str(error)})
            result["gaps"].append(identifier + ":source_history_unavailable")
    if capability == CAPABILITIES[3]:
        plans = record["plans"]
        add(record["maturity_id"] + ":plans", plans)
        superseded = {p["supersedes"] for p in plans if p["supersedes"]}
        current = [p for p in plans if p["plan_id"] not in superseded]
        if not current or any(p["status"] not in {"reviewed", "completed"} for p in current):
            result["gaps"].append("manually_reviewed_plan_missing")
        try:
            findings = operations._load(workspace)["findings"]
            linked = {f for p in current for f in p["linked_findings"]}
            snapshots = [f for f in findings if f["finding_id"] in linked]
            add(record["maturity_id"] + ":linked_findings", snapshots)
            result["gaps"].extend(f["finding_id"] for f in snapshots if f["status"] == "open")
            result["gaps"].extend("finding_unavailable:" + f for f in linked - {s["finding_id"] for s in snapshots})
        except LocalWorkflowError:
            result["gaps"].append("operations_history_unavailable")
    result["gaps"] = sorted(set(result["gaps"]))
    return result


def create(workspace, area, assurance_ids, owner, reason, actor="developer"):
    state = _load(workspace)
    try:
        _strings(assurance_ids, required=True)
    except (TypeError, ValueError) as error:
        raise LocalWorkflowError(str(error)) from error
    for identifier in assurance_ids:
        governance.history(workspace, identifier)
    return _append(workspace, state, "create", f"maturity-{len(state['maturities']) + 1:03d}", reason, actor,
                   assurance_area=area, assurance_ids=assurance_ids, owner=owner)


def assess(workspace, identifier, capability, reason, gaps=None, improvement_notes=None, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    if capability not in CAPABILITIES:
        raise LocalWorkflowError("Unknown recovery capability")
    return _append(workspace, state, "assess", identifier, reason, actor, capability=capability,
                   evidence=_evidence(workspace, record, capability), gaps=[] if gaps is None else gaps,
                   improvement_notes=[] if improvement_notes is None else improvement_notes)


def assign(workspace, identifier, owner, reason, actor="developer"):
    return _append(workspace, _load(workspace), "assign", identifier, reason, actor, owner=owner)


def transition(workspace, identifier, level, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    if level not in LEVELS:
        raise LocalWorkflowError("Unknown maturity level")
    evidence = {c: _evidence(workspace, record, c) for c in CRITERIA[level]} if LEVELS.index(level) > LEVELS.index(record["level"]) else {}
    if any(e["gaps"] for e in evidence.values()):
        raise LocalWorkflowError("Promotion is blocked by current capability gaps")
    return _append(workspace, state, "transition", identifier, reason, actor, level=level,
                   criteria=list(CRITERIA[level]), evidence_digests={c: reliability._digest(e) for c, e in evidence.items()})


def add_plan(workspace, identifier, improvements, capabilities, linked_findings, reason, supersedes=None, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    known = {f["finding_id"]: f for f in operations._load(workspace)["findings"] if f["assurance_id"] in record["assurance_ids"]}
    try:
        _strings(linked_findings)
        if not set(linked_findings).issubset(known):
            raise ValueError("Linked findings must exist within this maturity area's assurance scope")
    except (TypeError, ValueError) as error:
        raise LocalWorkflowError(str(error)) from error
    return _append(workspace, state, "plan-add", identifier, reason, actor, improvements=improvements,
                   capabilities=capabilities, linked_findings=linked_findings, supersedes=supersedes,
                   finding_snapshots=[known[f] for f in linked_findings])


def review_plan(workspace, identifier, plan_id, status, note, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    plan = _plan(record, plan_id)
    evidence = _evidence(workspace, record, CAPABILITIES[1])
    evidence["affected_capabilities"] = {capability: _evidence(workspace, record, capability)
                                         for capability in plan["affected_capabilities"] if capability != CAPABILITIES[3]}
    for assessed in evidence["affected_capabilities"].values():
        evidence["gaps"].extend(assessed["gaps"])
    findings = {f["finding_id"]: f for f in operations._load(workspace)["findings"]}
    for key in plan["linked_findings"]:
        if key not in findings or findings[key]["status"] != "resolved":
            evidence["gaps"].append(key)
    evidence["linked_findings"] = [findings[k] for k in plan["linked_findings"] if k in findings]
    return _append(workspace, state, "plan-review", identifier, reason, actor, plan_id=plan_id,
                   status=status, note=note, review_evidence=evidence)


def status(workspace):
    records = _load(workspace)["maturities"]
    return {"mode": MODE, "maturities": records,
            "recent_changes": [{"maturity_id": r["maturity_id"], "assurance_area": r["assurance_area"],
                                "changes": r["history"][-5:]} for r in records]}


def history(workspace, identifier):
    return {"mode": MODE, "record": deepcopy(_resolve(_load(workspace), identifier))}


def _review(workspace, record):
    assessments, missing, opportunities = [], [], []
    for capability in CAPABILITIES:
        evidence = _evidence(workspace, record, capability)
        latest = next((a for a in reversed(record["assessments"]) if a["capability"] == capability), None)
        gaps = evidence["gaps"][:]
        if latest is None:
            gaps.append("assessment_missing")
        else:
            gaps.extend(latest["manual_gaps"])
            if latest["evidence_digest"] != reliability._digest(evidence):
                gaps.append("assessment_stale")
            if latest["owner"] != record["owner"]:
                gaps.append("ownership_reassessment_required")
        entry = {"capability": capability, "level": record["level"], "latest_assessment": latest,
                 "current_evidence": evidence, "gaps": sorted(set(gaps))}
        assessments.append(entry)
        if gaps:
            missing.append({"capability": capability, "gaps": sorted(set(gaps))})
            opportunities.append({"capability": capability, "action": "Inspect capability gaps, manually update source evidence or plans, then record a fresh assessment."})
    return {"mode": MODE, "maturity_id": record["maturity_id"], "assurance_area": record["assurance_area"],
            "level": record["level"], "owner": record["owner"], "capabilities": assessments,
            "missing_evidence": missing, "improvement_opportunities": opportunities,
            "ready": not missing}


def review(workspace, area):
    for record in _load(workspace)["maturities"]:
        if record["assurance_area"] == area:
            return _review(workspace, record)
    raise LocalWorkflowError("Unknown assurance maturity area.")


def readiness(workspace):
    result = {"mode": MODE, "ready": [], "needs_attention": [], "missing_evidence": [], "manual_actions": []}
    for record in _load(workspace)["maturities"]:
        report = _review(workspace, record)
        result["ready" if report["ready"] else "needs_attention"].append(report)
        result["missing_evidence"].extend({"maturity_id": record["maturity_id"], **e} for e in report["missing_evidence"])
        result["manual_actions"].extend({"maturity_id": record["maturity_id"], **e} for e in report["improvement_opportunities"])
    return result


def plans(workspace):
    return {"mode": MODE, "plans": [{"maturity_id": r["maturity_id"], "assurance_area": r["assurance_area"], **p}
                                     for r in _load(workspace)["maturities"] for p in r["plans"]]}
