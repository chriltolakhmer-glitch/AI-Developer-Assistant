"""Developer configuration references; immutable snapshots and an append-only journal.

This management layer never applies code changes or overrides promotion runtime gates.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
import tempfile

from .local_workflow import LocalWorkflowError, _json_bytes
from .optimization import _read
from . import promotion

MODE = "developer-retrieval-configuration"
STATES = {
    "draft": {"validated", "retired"},
    "validated": {"active", "retired"},
    "active": {"retired", "rolled_back"},
    "retired": set(),
    "rolled_back": {"retired"},
}


def _root(workspace):
    promotion._root(workspace)  # Same external-workspace and research isolation gates.
    return workspace._contained(workspace.root / "optimization" / "configurations")


def _resolve(state, identifier):
    for record in state["configurations"]:
        if record["config_id"] == identifier:
            return record
    raise LocalWorkflowError("Unknown configuration ID.")


def settings_diff(before, after):
    """Compare values without scoring; paths are arrays to avoid dotted-key ambiguity."""
    result = {"added": [], "removed": [], "changed": []}

    def visit(left, right, path):
        if isinstance(left, dict) and isinstance(right, dict):
            for key in sorted(left.keys() | right.keys()):
                child = path + [key]
                if key not in left:
                    result["added"].append({"path": child, "value": deepcopy(right[key])})
                elif key not in right:
                    result["removed"].append({"path": child, "previous": deepcopy(left[key])})
                else:
                    visit(left[key], right[key], child)
        elif type(left) is not type(right) or left != right:
            result["changed"].append({"path": path, "previous": deepcopy(left), "value": deepcopy(right)})

    visit(before, after, [])
    return result


def _apply(state, event):
    """Replay a single event, enforcing transitions and immutable snapshot metadata."""
    action = event["action"]
    if not all(isinstance(event[key], str) and event[key].strip()
               for key in ("reason", "actor", "recorded_at")):
        raise ValueError("Missing event attribution")
    if action == "create":
        record = deepcopy(event["configuration"])
        version = len(state["configurations"]) + 1
        if (record["version"] != version or record["config_id"] != f"retrieval-config-{version:03d}"
                or record["status"] != "draft" or record["created_by"] != event["actor"]
                or record["created_at"] != event["recorded_at"]):
            raise ValueError("Invalid configuration snapshot")
        for key in ("source_candidate", "source_promotion", "repository_id", "review_id"):
            if not isinstance(record[key], str) or not record[key].strip():
                raise ValueError("Missing source promotion metadata")
        if not promotion.validate_settings(record["settings"]):
            raise ValueError("Empty settings")
        if record["previous_active"] != state["active"]:
            raise ValueError("Invalid previous active reference")
        before = _resolve(state, state["active"])["settings"] if state["active"] else {}
        if record["changes"] != settings_diff(before, record["settings"]):
            raise ValueError("Invalid setting changes")
        state["configurations"].append(record)
        return
    record = _resolve(state, event["config_id"])
    if (event["source_promotion"] != record["source_promotion"]
            or event["source_candidate"] != record["source_candidate"]
            or event["previous_active"] != state["active"]
            or event["restored_active"] != (record["previous_active"] if action == "rollback" else None)
            or event["retired_configuration"] != (state["active"] if action == "activate" else None)):
        raise ValueError("Invalid transition references")
    target = {"validate": "validated", "activate": "active", "retire": "retired",
              "rollback": "rolled_back"}[action]
    if target not in STATES[record["status"]]:
        raise LocalWorkflowError(f"Invalid configuration transition from '{record['status']}' to '{target}'.")
    if action == "activate":
        if record["previous_active"] != state["active"]:
            raise LocalWorkflowError("Active reference changed; create and validate a fresh snapshot.")
        if state["active"]:
            _resolve(state, state["active"])["status"] = "retired"
        state["active"] = record["config_id"]
    elif action == "rollback":
        if state["active"] != record["config_id"]:
            raise LocalWorkflowError("Only the active configuration can be rolled back.")
        state["active"] = record["previous_active"]
        if state["active"]:
            prior = _resolve(state, state["active"])
            if prior["status"] != "retired":
                raise ValueError("Invalid rollback point")
            prior["status"] = "active"  # Only a recorded rollback point can be restored.
    elif action == "retire" and state["active"] == record["config_id"]:
        state["active"] = None
    record["status"] = target


def _load(workspace):
    state = {"mode": MODE, "configurations": [], "active": None, "events": []}
    digest = None
    for path in sorted(_root(workspace).glob("*.json")):
        event = _read(workspace, path)
        try:
            sequence = len(state["events"]) + 1
            if (event["mode"] != MODE or event["schema_version"] != 1 or event["sequence"] != sequence
                    or path.name != f"{sequence:08d}.json" or event["previous_digest"] != digest):
                raise ValueError("Broken configuration journal chain")
            _apply(state, event)
        except (KeyError, TypeError, ValueError, AttributeError, LocalWorkflowError) as error:
            raise LocalWorkflowError(f"Invalid configuration journal: {error}") from error
        state["events"].append(event)
        digest = hashlib.sha256(_json_bytes(event)).hexdigest()
    return state


def _append(workspace, state, action, reason, actor, **payload):
    event = {"mode": MODE, "schema_version": 1, "sequence": len(state["events"]) + 1,
             "previous_digest": (hashlib.sha256(_json_bytes(state["events"][-1])).hexdigest()
                                 if state["events"] else None),
             "action": action, "reason": reason, "actor": actor,
             "recorded_at": datetime.now(timezone.utc).isoformat(), **payload}
    if action == "create":
        event["configuration"]["created_at"] = event["recorded_at"]
    try:
        _apply(deepcopy(state), event)
    except (ValueError, TypeError, KeyError) as error:
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
        raise LocalWorkflowError(f"Cannot append configuration event; inspect history and retry: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)
    return event


def _source(workspace, identifier):
    workspace = promotion._ReadOnlyWorkspace(workspace.root, workspace.research_roots)
    source = promotion._resolve(promotion._load(workspace), identifier)
    if source["status"] != "promoted":
        raise LocalWorkflowError("Configuration requires a currently promoted source.")
    candidate, review, summary, _ = promotion._evidence(workspace, source["candidate_id"])
    if (review["review_id"] != source["review_id"] or summary != source["validation_summary"]
            or candidate["retrieval_settings"] != source["retrieval_settings"]):
        raise LocalWorkflowError("Source promotion approval or validation changed.")
    return source


def _check(workspace, record):
    source = _source(workspace, record["source_promotion"])
    if (source["retrieval_settings"] != record["settings"]
            or source["review_id"] != record["review_id"]
            or source["candidate_id"] != record["source_candidate"]
            or source["repository_id"] != record["repository_id"]):
        raise LocalWorkflowError("Configuration is incompatible with its approved promotion.")


def create_configuration(workspace, source_promotion, reason, actor="developer"):
    state = _load(workspace)
    source = _source(workspace, source_promotion)
    version = len(state["configurations"]) + 1
    settings = deepcopy(source["retrieval_settings"])
    before = _resolve(state, state["active"])["settings"] if state["active"] else {}
    record = {"config_id": f"retrieval-config-{version:03d}", "version": version,
              "status": "draft", "created_at": "", "created_by": actor,
              "source_candidate": source["candidate_id"], "source_promotion": source["promotion_id"],
              "repository_id": source["repository_id"], "review_id": source["review_id"],
              "settings": settings, "previous_active": state["active"],
              "changes": settings_diff(before, settings)}
    _append(workspace, state, "create", reason, actor, configuration=record)
    return record


def transition_configuration(workspace, identifier, action, reason, actor="developer"):
    if action not in {"validate", "activate", "retire", "rollback"}:
        raise LocalWorkflowError("Unknown configuration action.")
    state = _load(workspace)
    record = _resolve(state, identifier)
    if action in {"validate", "activate"}:
        _check(workspace, record)
    if action == "rollback" and record["previous_active"]:
        _check(workspace, _resolve(state, record["previous_active"]))
    _append(workspace, state, action, reason, actor, config_id=identifier,
            source_promotion=record["source_promotion"], source_candidate=record["source_candidate"],
            previous_active=state["active"],
            retired_configuration=state["active"] if action == "activate" else None,
            restored_active=record["previous_active"] if action == "rollback" else None)
    return deepcopy(_resolve(_load(workspace), identifier))


def configuration_history(workspace):
    return _load(workspace)


def configuration_status(workspace):
    state = _load(workspace)
    record = _resolve(state, state["active"]) if state["active"] else None
    blocked = []
    if record:
        try:
            _check(workspace, record)
        except LocalWorkflowError as error:
            blocked.append(str(error))
    return {"mode": MODE, "active": state["active"], "version": record["version"] if record else None,
            "source": record["source_candidate"] if record else None,
            "source_promotion": record["source_promotion"] if record else None,
            "configuration": record, "recent_changes": state["events"][-10:],
            "blocked": blocked, "runtime_authority": "developer-promotions"}


def configuration_diff(workspace, version_a, version_b):
    state = _load(workspace)
    def version(number):
        for record in state["configurations"]:
            if str(record["version"]) == str(number):
                return record
        raise LocalWorkflowError("Unknown configuration version.")
    left, right = version(version_a), version(version_b)
    return {"mode": MODE, "version_a": left["version"], "version_b": right["version"],
            **settings_diff(left["settings"], right["settings"])}
