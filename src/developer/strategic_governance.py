"""Manual developer recovery strategy; no scheduling, prioritization or execution."""
from copy import deepcopy
import os
import tempfile

from . import assurance, evolution, maturity, reliability
from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read

MODE = "developer-recovery-strategic-governance"
STATES = ("planned", "reviewing", "approved", "active", "completed", "retired")
TRANSITIONS = {"planned": {"reviewing", "retired"}, "reviewing": {"planned", "approved", "retired"},
               "approved": {"reviewing", "active", "retired"}, "active": {"reviewing", "completed", "retired"},
               "completed": {"retired"}, "retired": set()}
ROADMAP_STATES = ("proposed", "scheduled", "active", "completed", "deferred")
ROADMAP_TRANSITIONS = {"proposed": {"scheduled", "deferred"}, "scheduled": {"proposed", "active", "deferred"},
                      "active": {"completed", "deferred"}, "deferred": {"proposed", "scheduled"}, "completed": set()}
_now = assurance._now


def _root(workspace):
    evolution._root(workspace)
    return workspace._contained(workspace.root / "optimization" / "strategic-governance")


def _resolve(state, identifier):
    for record in state["governances"]:
        if record["governance_id"] == identifier:
            return record
    raise LocalWorkflowError("Unknown strategic governance ID.")


def _roadmap(record, identifier):
    for item in record["roadmap"]:
        if item["roadmap_id"] == identifier:
            return item
    raise LocalWorkflowError("Unknown roadmap ID for this objective.")


def _nodes(state):
    return {r["governance_id"]: r for r in state["governances"]} | {
        item["roadmap_id"]: item for r in state["governances"] for item in r["roadmap"]}


def _validate_dependencies(state):
    nodes = _nodes(state)
    for identifier, node in nodes.items():
        maturity._strings(node["dependencies"])
        for dependency in node["dependencies"]:
            if dependency.startswith(("governance-", "roadmap-")):
                if dependency not in nodes:
                    raise ValueError("Unknown objective or roadmap dependency")
                if identifier.startswith("governance-") != dependency.startswith("governance-"):
                    raise ValueError("Objective dependencies must reference objectives; roadmap dependencies must reference roadmap items")
    visiting, visited = set(), set()
    def visit(identifier):
        if identifier in visiting:
            raise ValueError("Cyclic strategic dependency")
        if identifier in visited:
            return
        visiting.add(identifier)
        for dependency in nodes[identifier]["dependencies"]:
            if dependency in nodes:
                visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)
    for identifier in nodes:
        visit(identifier)


def _objective_fields(event):
    for key in ("objective", "owner"):
        reliability._text(event[key])
    for key in ("capabilities", "evolution_ids", "dependencies", "review_notes", "risks"):
        maturity._strings(event[key], required=key == "capabilities")
    snapshots = event["evolution_snapshots"]
    if not isinstance(snapshots, list) or [r["evolution_id"] for r in snapshots] != event["evolution_ids"]:
        raise ValueError("Invalid linked evolution snapshots")


def _validate_snapshot(snapshot):
    if snapshot["digest"] != reliability._digest(snapshot["evidence"]):
        raise ValueError("Invalid strategic review evidence digest")
    for key in ("risks", "missing_evidence", "unresolved_dependencies"):
        if not isinstance(snapshot["evidence"][key], list):
            raise ValueError("Invalid strategic review evidence")


def _clear(snapshot):
    evidence = snapshot["evidence"]
    return not any(evidence[k] for k in ("risks", "missing_evidence", "unresolved_dependencies"))


def _apply(state, event):
    for key in ("actor", "reason", "governance_id"):
        reliability._text(event[key])
    assurance._timestamp(event["created_at"])
    action = event["action"]
    road = None
    previous_roadmap_status = None
    if action == "create":
        if event["governance_id"] != f"governance-{len(state['governances']) + 1:03d}":
            raise ValueError("Invalid strategic governance ID")
        _objective_fields(event)
        record = {"governance_id": event["governance_id"], "created_at": event["created_at"], "status": "planned",
                  "history": [], "reviews": [], "roadmap": [], "dependency_reviews": []}
        record.update({k: deepcopy(event[k]) for k in
                       ("objective", "owner", "capabilities", "evolution_ids", "dependencies", "review_notes", "risks")})
        state["governances"].append(record)
        previous = None
    else:
        record = _resolve(state, event["governance_id"])
        previous = record["status"]
        if previous == "retired" or (previous == "completed" and action != "transition"):
            raise ValueError("Terminal strategic records require a new objective")
        if action == "update":
            if previous not in {"planned", "reviewing"}:
                raise ValueError("Return to reviewing before revising objective scope or ownership")
            _objective_fields(event)
            record.update({k: deepcopy(event[k]) for k in
                           ("objective", "owner", "capabilities", "evolution_ids", "dependencies", "review_notes", "risks")})
        elif action == "review-record":
            reliability._text(event["note"])
            _validate_snapshot(event["snapshot"])
            record["reviews"].append(deepcopy(event))
        elif action == "transition":
            target = event["status"]
            if target not in TRANSITIONS[previous]:
                raise ValueError("Invalid strategic governance transition")
            reliability._text(event["note"])
            if target in {"approved", "active", "completed"}:
                _validate_snapshot(event["snapshot"])
                if (not record["reviews"] or record["reviews"][-1]["snapshot"] != event["snapshot"]
                        or not _clear(event["snapshot"])):
                    raise ValueError("Decision requires a current recorded review without risks, dependency issues or evidence gaps")
                if target == "completed" and event["snapshot"]["evidence"]["completion_gaps"]:
                    raise ValueError("Completion requires verified evolutions and completed roadmap items")
            record["status"] = target
        elif action in {"roadmap-add", "roadmap-update", "roadmap-transition"}:
            if action == "roadmap-add":
                expected = f"roadmap-{sum(len(r['roadmap']) for r in state['governances']) + 1:03d}"
                if event["roadmap_id"] != expected:
                    raise ValueError("Invalid roadmap ID")
                road = {"roadmap_id": expected, "governance_id": record["governance_id"], "status": "proposed",
                        "created_at": event["created_at"], "history": [], "dependency_reviews": []}
                record["roadmap"].append(road)
            else:
                road = _roadmap(record, event["roadmap_id"])
                previous_roadmap_status = road["status"]
                if road["status"] == "completed":
                    raise ValueError("Completed roadmap items are immutable")
            if action in {"roadmap-add", "roadmap-update"}:
                if road["status"] not in {"proposed", "scheduled", "deferred"}:
                    raise ValueError("Defer active roadmap work before revising its plan")
                for key in ("description", "owner", "target_period"):
                    reliability._text(event[key])
                maturity._strings(event["dependencies"])
                road.update({k: deepcopy(event[k]) for k in ("description", "owner", "target_period", "dependencies")})
            else:
                target = event["status"]
                reliability._text(event["note"])
                if target not in ROADMAP_TRANSITIONS[road["status"]]:
                    raise ValueError("Invalid roadmap transition")
                if target in {"active", "completed"}:
                    if record["status"] != "active" or event["dependency_issues"]:
                        raise ValueError("Roadmap work requires an active objective and resolved dependencies")
                    _validate_snapshot(event["snapshot"])
                    if not _clear(event["snapshot"]):
                        raise ValueError("Roadmap work requires current gap-free objective evidence")
                road["status"] = target
        elif action == "dependency-review":
            node = _roadmap(record, event["roadmap_id"]) if event["roadmap_id"] else record
            if node["status"] == "completed":
                raise ValueError("Completed roadmap items are immutable")
            dependency = event["dependency"]
            if dependency not in node["dependencies"] or dependency.startswith(("governance-", "roadmap-")):
                raise ValueError("Only declared external prerequisites accept manual dependency reviews")
            if event["resolution"] not in {"resolved", "unresolved"}:
                raise ValueError("Unknown dependency resolution")
            reliability._text(event["note"])
            node["dependency_reviews"].append(deepcopy(event))
            if node is not record:
                road = node
                previous_roadmap_status = road["status"]
        else:
            raise ValueError("Unknown strategic governance action")
    _validate_dependencies(state)
    record["updated_at"] = event["created_at"]
    record["history"].append({"previous_status": previous, "current_status": record["status"], **deepcopy(event)})
    if road is not None:
        road["updated_at"] = event["created_at"]
        road["history"].append({"previous_status": previous_roadmap_status, "current_status": road["status"], **deepcopy(event)})


def _load(workspace):
    state = {"mode": MODE, "governances": [], "events": []}
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
             "action": action, "governance_id": identifier, "reason": reason, "actor": actor,
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


def _dependency_entries(state, identifier, node):
    nodes = _nodes(state)
    result = []
    for dependency in node["dependencies"]:
        if dependency in nodes:
            target = nodes[dependency]
            upstream = _dependency_entries(state, dependency, target)
            satisfied = target["status"] == "completed" and all(d["resolved"] for d in upstream)
            detail = {"kind": "record", "status": target["status"], "owner": target["owner"],
                      "unresolved_upstream": [d for d in upstream if not d["resolved"]]}
        else:
            latest = next((r for r in reversed(node["dependency_reviews"]) if r["dependency"] == dependency), None)
            satisfied = latest is not None and latest["resolution"] == "resolved"
            detail = {"kind": "external", "review": latest}
        result.append({"item_id": identifier, "dependency": dependency, "resolved": satisfied, **detail})
    return result


def _snapshot(workspace, state, record):
    objective = {k: deepcopy(record[k]) for k in
                 ("governance_id", "objective", "owner", "status", "capabilities", "evolution_ids", "dependencies", "review_notes", "risks")}
    roadmap = [{k: deepcopy(item[k]) for k in
                ("roadmap_id", "governance_id", "description", "owner", "target_period", "dependencies", "status")}
               for item in record["roadmap"]]
    dependencies = _dependency_entries(state, record["governance_id"], record)
    roadmap_dependencies = [d for item in record["roadmap"] for d in _dependency_entries(state, item["roadmap_id"], item)]
    evidence = {"objective": objective, "roadmap": roadmap, "dependencies": dependencies,
                "roadmap_dependencies": roadmap_dependencies, "evolutions": [], "risks": record["risks"][:],
                "missing_evidence": [], "unresolved_dependencies": [d for d in dependencies if not d["resolved"]],
                "completion_gaps": []}
    if not record["evolution_ids"]:
        evidence["missing_evidence"].append("linked_evolution_missing")
    if not roadmap:
        evidence["missing_evidence"].append("roadmap_missing")
    for identifier in record["evolution_ids"]:
        try:
            source = evolution.history(workspace, identifier)["record"]
            report = evolution.review(workspace, identifier)
            evidence["evolutions"].append({"evolution_id": identifier, "record": source, "review": report})
            evidence["missing_evidence"].extend(identifier + ":" + gap for gap in report["missing_evidence"])
            evidence["risks"].extend(identifier + ":" + risk for risk in report["warnings"])
            if source["status"] == "retired":
                evidence["missing_evidence"].append(identifier + ":evolution_retired")
            if source["status"] != "verified":
                evidence["completion_gaps"].append(identifier + ":verification_required")
        except LocalWorkflowError as error:
            evidence["evolutions"].append({"evolution_id": identifier, "unavailable": str(error)})
            evidence["missing_evidence"].append(identifier + ":evolution_unavailable")
    evidence["completion_gaps"].extend(item["roadmap_id"] + ":not_completed" for item in roadmap if item["status"] != "completed")
    evidence["completion_gaps"].extend(d["item_id"] + ":dependency:" + d["dependency"] for d in roadmap_dependencies if not d["resolved"])
    return {"evidence": evidence, "digest": reliability._digest(evidence)}


def _fields(workspace, objective, owner, capabilities, evolution_ids, dependencies, review_notes, risks):
    try:
        maturity._strings(evolution_ids)
    except (TypeError, ValueError) as error:
        raise LocalWorkflowError(str(error)) from error
    return dict(objective=objective, owner=owner, capabilities=capabilities, evolution_ids=evolution_ids,
                dependencies=dependencies, review_notes=review_notes, risks=risks,
                evolution_snapshots=[evolution.history(workspace, key)["record"] for key in evolution_ids])


def create(workspace, objective, owner, capabilities, evolution_ids, dependencies, review_notes, risks, reason, actor="developer"):
    state = _load(workspace)
    return _append(workspace, state, "create", f"governance-{len(state['governances']) + 1:03d}", reason, actor,
                   **_fields(workspace, objective, owner, capabilities, evolution_ids, dependencies, review_notes, risks))


def update(workspace, identifier, objective, owner, capabilities, evolution_ids, dependencies, review_notes, risks, reason, actor="developer"):
    return _append(workspace, _load(workspace), "update", identifier, reason, actor,
                   **_fields(workspace, objective, owner, capabilities, evolution_ids, dependencies, review_notes, risks))


def record_review(workspace, identifier, note, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    return _append(workspace, state, "review-record", identifier, reason, actor, note=note, snapshot=_snapshot(workspace, state, record))


def transition(workspace, identifier, status, note, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    snapshot = _snapshot(workspace, state, record) if status in {"approved", "active", "completed"} else None
    return _append(workspace, state, "transition", identifier, reason, actor, status=status, note=note, snapshot=snapshot)


def add_roadmap(workspace, identifier, description, owner, target_period, dependencies, reason, actor="developer"):
    state = _load(workspace)
    return _append(workspace, state, "roadmap-add", identifier, reason, actor,
                   roadmap_id=f"roadmap-{sum(len(r['roadmap']) for r in state['governances']) + 1:03d}",
                   description=description, owner=owner, target_period=target_period, dependencies=dependencies)


def update_roadmap(workspace, identifier, roadmap_id, description, owner, target_period, dependencies, reason, actor="developer"):
    return _append(workspace, _load(workspace), "roadmap-update", identifier, reason, actor, roadmap_id=roadmap_id,
                   description=description, owner=owner, target_period=target_period, dependencies=dependencies)


def transition_roadmap(workspace, identifier, roadmap_id, status, note, reason, actor="developer"):
    state = _load(workspace)
    record = _resolve(state, identifier)
    item = _roadmap(record, roadmap_id)
    issues = [d for d in _dependency_entries(state, roadmap_id, item) if not d["resolved"]]
    snapshot = _snapshot(workspace, state, record) if status in {"active", "completed"} else None
    return _append(workspace, state, "roadmap-transition", identifier, reason, actor, roadmap_id=roadmap_id,
                   status=status, note=note, dependency_issues=issues, snapshot=snapshot)


def review_dependency(workspace, identifier, dependency, resolution, note, reason, roadmap_id=None, actor="developer"):
    return _append(workspace, _load(workspace), "dependency-review", identifier, reason, actor, roadmap_id=roadmap_id,
                   dependency=dependency, resolution=resolution, note=note)


def status(workspace):
    records = _load(workspace)["governances"]
    return {"mode": MODE, "objectives": records, "active_objectives": [r for r in records if r["status"] == "active"],
            "roadmap": [item for record in records for item in record["roadmap"]]}


def history(workspace, identifier):
    return {"mode": MODE, "record": deepcopy(_resolve(_load(workspace), identifier))}


def _review(workspace, state, record):
    snapshot = _snapshot(workspace, state, record)
    evidence = snapshot["evidence"]
    current = bool(record["reviews"] and record["reviews"][-1]["snapshot"] == snapshot)
    warnings = [] if current else ["recorded_review_missing_or_stale"]
    road_issues = [d for d in evidence["roadmap_dependencies"] if not d["resolved"]]
    if road_issues:
        warnings.append("roadmap_dependencies_unresolved")
    ready = []
    if _clear(snapshot) and current:
        target = {"reviewing": "approved", "approved": "active", "active": "completed"}.get(record["status"])
        if target and (target != "completed" or not evidence["completion_gaps"]):
            ready.append("manual_" + target)
    actions = []
    if record["status"] not in {"completed", "retired"}:
        if evidence["risks"] or evidence["missing_evidence"]:
            actions.append("Review risks and linked evolution evidence; revise the objective or refresh source records explicitly.")
        if evidence["unresolved_dependencies"] or road_issues:
            actions.append("Inspect prerequisite records or record a manual external dependency review; no dependency is resolved here.")
        if not current:
            actions.append("Record a fresh strategic review after inspecting current evidence.")
        actions.append("Record lifecycle and roadmap decisions explicitly; target periods trigger no scheduling or execution.")
    elif evidence["risks"] or evidence["missing_evidence"] or evidence["unresolved_dependencies"]:
        actions.append("Inspect historical evidence drift and create a new objective for follow-up work.")
    return {"mode": MODE, "governance_id": record["governance_id"], "objective": record["objective"],
            "owner": record["owner"], "status": record["status"], "ready": ready, "warnings": warnings,
            "risks": evidence["risks"], "missing_evidence": evidence["missing_evidence"],
            "dependencies": evidence["dependencies"], "roadmap_dependencies": evidence["roadmap_dependencies"],
            "roadmap": evidence["roadmap"], "completion_gaps": evidence["completion_gaps"],
            "linked_evolutions": evidence["evolutions"], "review_current": current, "manual_actions": actions}


def review(workspace, identifier):
    state = _load(workspace)
    return _review(workspace, state, _resolve(state, identifier))


def dependencies(workspace):
    state = _load(workspace)
    entries, relationships = [], []
    for record in state["governances"]:
        entries.extend(_dependency_entries(state, record["governance_id"], record))
        for item in record["roadmap"]:
            entries.extend(_dependency_entries(state, item["roadmap_id"], item))
        relationships.append({"governance_id": record["governance_id"], "capabilities": record["capabilities"],
                              "evolution_ids": record["evolution_ids"]})
    blocked = [d for d in entries if not d["resolved"]]
    return {"mode": MODE, "dependencies": entries, "capability_relationships": relationships, "blocked": blocked,
            "manual_actions": [{"item_id": d["item_id"], "dependency": d["dependency"],
                                "action": "Inspect prerequisite and explicitly record its resolution in the owning workflow."} for d in blocked]}


def plan_review(workspace):
    state = _load(workspace)
    reports = [_review(workspace, state, r) for r in state["governances"]]
    result = {"mode": MODE, "objectives": reports, "active_objectives": [r for r in reports if r["status"] == "active"],
              "ready": [], "warnings": [], "risks": [], "manual_actions": [],
              "improvement_history": [{"governance_id": r["governance_id"], "history": r["history"]} for r in state["governances"]]}
    for report in reports:
        for key in ("ready", "warnings", "risks", "manual_actions"):
            result[key].extend({"governance_id": report["governance_id"], "detail": value} for value in report[key])
        result["warnings"].extend({"governance_id": report["governance_id"], "detail": value}
                                  for value in report["missing_evidence"])
    return result
