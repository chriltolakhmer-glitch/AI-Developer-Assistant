"""Explicit developer configuration promotion; immutable, atomic state snapshots."""
from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import math
import os
import tempfile
from uuid import uuid4

from .local_workflow import DeveloperWorkspace, LocalWorkflowError, _json_bytes, _overlaps, _PROJECT_ROOT
from .optimization import _read, _name, show_candidates, _version
from .review import _all_reviews, _validation_summary, policy_check

MODE = "developer-retrieval-promotion"
STATES = {
    "pending": {"validated", "retired"},
    "validated": {"promoted", "retired"},
    "promoted": {"paused", "rolled_back", "retired"},
    "paused": {"promoted", "rolled_back", "retired"},
    "rolled_back": {"retired"}, "retired": set(),
}
EXPERIMENT = ContextVar("developer_promotion_experiment", default=None)


class _ReadOnlyWorkspace(DeveloperWorkspace):
    """Reuse prior-phase evidence readers without their initialization side effects."""

    def _prepare(self, repository=None):
        _root(self)
        if repository is not None:
            self._assert_isolated(self.root, (repository,), "Developer workspace")
            self._assert_isolated(repository, self.research_roots, "Repository")


def validate_settings(settings):
    if not isinstance(settings, dict) or set(settings) - {"relationship_factor"}:
        raise LocalWorkflowError("Unsupported developer retrieval settings.")
    for value in settings.values():
        if type(value) not in (int, float) or not math.isfinite(value) or not 1 <= value <= 2:
            raise LocalWorkflowError("relationship_factor must be a finite number between 1 and 2.")
    return deepcopy(settings)


def _root(workspace):
    # Inspection must not initialize or repair a workspace.
    if _overlaps(workspace.root, _PROJECT_ROOT):
        raise LocalWorkflowError("Promotion workspace must be outside the prototype checkout.")
    workspace._assert_isolated(workspace.root, workspace.research_roots, "Developer workspace")
    return workspace._contained(workspace.root / "optimization" / "promotions")


def _empty():
    return {"schema_version": "developer-promotion-v1", "mode": MODE, "sequence": 0, "promotions": [],
            "configuration": {"active_candidates": [], "entries": [], "updated_at": None}}


def _configuration(promotions, timestamp):
    entries = [{key: deepcopy(p[key]) for key in
                ("promotion_id", "candidate_id", "repository_id", "retrieval_settings",
                 "promoted_at", "validation_summary", "rollback_reference")}
               for p in promotions if p["status"] == "promoted"]
    return {"active_candidates": [p["candidate_id"] for p in entries],
            "entries": entries, "updated_at": timestamp}


def _load(workspace):
    state = _empty()
    digest = None
    configurations = {0: state["configuration"]}
    for path in sorted(_root(workspace).glob("*.json")):
        record = _read(workspace, path)
        try:
            if (record["mode"] != MODE or record["schema_version"] != "developer-promotion-v1"
                    or record["sequence"] != state["sequence"] + 1
                    or record["previous_digest"] != digest):
                raise ValueError("broken journal chain")
            prior = {p["promotion_id"]: p for p in state["promotions"]}
            seen = set()
            for p in record["promotions"]:
                identifier = p["promotion_id"]
                if identifier in seen:
                    raise ValueError("duplicate promotion")
                seen.add(identifier)
                old = prior.get(identifier)
                history = p["history"]
                if not history or history[-1]["status"] != p["status"]:
                    raise ValueError("invalid history")
                if old and p != old:
                    if (p["status"] not in STATES[old["status"]]
                            or history[:-1] != old["history"]):
                        raise ValueError("invalid transition or rewritten history")
                    mutable = {"status", "history", "promoted_at", "activated_configuration"}
                    if ({k: v for k, v in p.items() if k not in mutable}
                            != {k: v for k, v in old.items() if k not in mutable}):
                        raise ValueError("rewritten promotion metadata")
                elif not old and (p["status"] != "pending" or len(history) != 1):
                    raise ValueError("invalid initial state")
                for key in ("candidate_id", "created_at", "approved_by", "validation_summary",
                            "rollback_reference", "previous_configuration", "review_id"):
                    if not p.get(key):
                        raise ValueError("incomplete promotion metadata: " + key)
                validate_settings(p["retrieval_settings"])
                reference = p["rollback_reference"]
                if (not reference.get("instructions") or not reference.get("baseline")
                        or p["previous_configuration"] != configurations.get(reference.get("sequence"))):
                    raise ValueError("missing or inconsistent rollback reference")
            if set(prior) - seen:
                raise ValueError("deleted promotion")
            config = record["configuration"]
            if config != _configuration(record["promotions"], config["updated_at"]):
                raise ValueError("inconsistent active configuration")
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise LocalWorkflowError(f"Invalid promotion journal: {error}") from error
        state = record
        configurations[state["sequence"]] = state["configuration"]
        digest = hashlib.sha256(_json_bytes(record)).hexdigest()
    return state


def _append(workspace, previous, state):
    workspace._prepare()
    directory = _root(workspace)
    directory.mkdir(parents=True, exist_ok=True)
    state["sequence"] = previous["sequence"] + 1
    state["previous_digest"] = (hashlib.sha256(_json_bytes(previous)).hexdigest()
                                if previous["sequence"] else None)
    target = workspace._contained(directory / f"{state['sequence']:08d}.json")
    # Publish a complete snapshot atomically; exclusive hard link detects competing writers.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, suffix=".tmp", delete=False) as stream:
            temporary = stream.name
            stream.write(_json_bytes(state))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    except OSError as error:
        raise LocalWorkflowError(f"Cannot append promotion state; retry after inspecting status: {error}") from error
    finally:
        if temporary:
            os.unlink(temporary)


def active_configuration(workspace):
    return deepcopy(_load(workspace)["configuration"])


def retrieval_settings(workspace, repository_id):
    settings = {}
    for entry in active_configuration(workspace)["entries"]:
        if entry["repository_id"] == repository_id:
            settings.update(entry["retrieval_settings"])
    experiment = EXPERIMENT.get()
    if experiment and experiment[0] == repository_id:
        settings.update(experiment[1])
    return settings


def _evidence(workspace, candidate_id):
    candidate = show_candidates(workspace, _name(candidate_id))["candidates"][0]
    if candidate["status"] == "rejected":
        raise LocalWorkflowError("Rejected candidates cannot be promoted.")
    reviews = [r for r in _all_reviews(workspace) if r["candidate_id"] == candidate_id]
    review = reviews[-1] if reviews else None
    if not review or review["status"] != "approved":
        raise LocalWorkflowError("Promotion requires the latest review to be approved.")
    if not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip() or not review.get("review_id"):
        raise LocalWorkflowError("Approved review metadata is incomplete.")
    policy = policy_check(workspace, candidate_id)
    if policy["blocked"]:
        raise LocalWorkflowError("Promotion blocked by policy checks: " +
                                 ", ".join(p["check"] for p in policy["blocked"]))
    summary = _validation_summary(candidate)
    if review["validation_summary"] != summary:
        raise LocalWorkflowError("Approval is stale; validation evidence changed.")
    settings = validate_settings(candidate.get("retrieval_settings", {}))
    if not settings or summary.get("retrieval_settings") != settings:
        raise LocalWorkflowError("Promotion requires explicit settings bound to validation and approval.")
    _version(workspace, candidate["repository_id"], summary["before"])
    if not isinstance(summary.get("base_configuration"), dict):
        raise LocalWorkflowError("Validation must preserve its base configuration for rollback.")
    return candidate, review, summary, policy


def create_promotion(workspace, candidate_id):
    previous = _load(workspace)
    candidate, review, summary, policy = _evidence(workspace, candidate_id)
    if summary["base_configuration"] != previous["configuration"]:
        raise LocalWorkflowError("Active configuration changed since validation; revalidate and review.")
    if any(p["candidate_id"] == candidate_id and p["status"] not in {"retired", "rolled_back"}
           for p in previous["promotions"]):
        raise LocalWorkflowError("Candidate already has a live promotion.")
    if any(p["repository_id"] == candidate["repository_id"] for p in previous["configuration"]["entries"]):
        raise LocalWorkflowError("Retire the existing repository promotion before replacing its settings.")
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {"promotion_id": "promotion-" + uuid4().hex, "candidate_id": candidate_id,
              "repository_id": candidate["repository_id"], "status": "pending",
              "created_at": timestamp, "approved_by": review["reviewer"], "review_id": review["review_id"],
              "validation_summary": summary, "policy": policy,
              "retrieval_settings": candidate["retrieval_settings"], "promoted_at": None,
              "previous_configuration": deepcopy(previous["configuration"]),
              "rollback_reference": {"sequence": previous["sequence"], "baseline": summary["before"],
                                     "instructions": "Restore the preserved active configuration via optimize-promote-rollback."},
              "history": [{"status": "pending", "previous_status": None, "recorded_at": timestamp}]}
    state = deepcopy(previous)
    state["promotions"].append(record)
    _append(workspace, previous, state)
    return record


def _resolve(state, identifier):
    exact = [p for p in state["promotions"] if p["promotion_id"] == identifier]
    matches = exact or [p for p in state["promotions"] if p["candidate_id"] == identifier
                        and p["status"] not in {"retired", "rolled_back"}]
    if len(matches) != 1:
        raise LocalWorkflowError("Use an existing, unambiguous promotion ID.")
    return matches[0]


def transition_promotion(workspace, identifier, status):
    previous = _load(workspace)
    state = deepcopy(previous)
    record = _resolve(state, identifier)
    old = record["status"]
    if status not in STATES[old]:
        raise LocalWorkflowError(f"Invalid promotion transition from '{old}' to '{status}'.")
    if status in {"validated", "promoted"}:
        _, review, summary, _ = _evidence(workspace, record["candidate_id"])
        if review["review_id"] != record["review_id"] or summary != record["validation_summary"]:
            raise LocalWorkflowError("Promotion approval or validation changed.")
        if previous["configuration"] != record["previous_configuration"]:
            raise LocalWorkflowError("Configuration changed; retire this promotion and revalidate.")
    if status in {"rolled_back", "paused"}:
        # Never silently overwrite later, unrelated configuration changes.
        expected = (record["previous_configuration"] if old == "paused"
                    else record.get("activated_configuration"))
        if previous["configuration"] != expected:
            raise LocalWorkflowError("Rollback requires the activation configuration; undo later changes first.")
    timestamp = datetime.now(timezone.utc).isoformat()
    record["status"] = status
    record["history"].append({"status": status, "previous_status": old, "recorded_at": timestamp})
    if status == "promoted":
        record["promoted_at"] = timestamp
    if status == "rolled_back":
        state["configuration"] = deepcopy(record["previous_configuration"])
    elif status == "paused":
        state["configuration"] = deepcopy(record["previous_configuration"])
    elif status == "promoted" or old == "promoted":
        state["configuration"] = _configuration(state["promotions"], timestamp)
    if status == "promoted":
        record["activated_configuration"] = deepcopy(state["configuration"])
    _append(workspace, previous, state)
    return record


def promote(workspace, candidate_id):
    record = create_promotion(workspace, candidate_id)
    transition_promotion(workspace, record["promotion_id"], "validated")
    return transition_promotion(workspace, record["promotion_id"], "promoted")


def retire(workspace, identifier):
    return transition_promotion(workspace, identifier, "retired")


def rollback(workspace, identifier):
    return transition_promotion(workspace, identifier, "rolled_back")


def promotion_status(workspace):
    state = _load(workspace)
    return {"mode": MODE, "configuration": state["configuration"], "promotions": state["promotions"],
            "active_promotions": [p for p in state["promotions"] if p["status"] == "promoted"],
            "pending_promotions": [p for p in state["promotions"] if p["status"] in {"pending", "validated"}],
            "retired_promotions": [p for p in state["promotions"] if p["status"] == "retired"],
            "rollback_history": [{"promotion_id": p["promotion_id"], **h} for p in state["promotions"]
                                 for h in p["history"] if h["status"] == "rolled_back"]}


def promotion_check(workspace):
    report = {"mode": MODE, "passed": [], "warnings": [], "blocked": [], "automatic_changes": False}
    workspace = _ReadOnlyWorkspace(workspace.root, workspace.research_roots)
    try:
        state = _load(workspace)
        report["passed"].append({"check": "configuration_consistency"})
        for p in state["promotions"]:
            try:
                if p["status"] not in {"retired", "rolled_back"}:
                    _, review, summary, policy = _evidence(workspace, p["candidate_id"])
                    if review["review_id"] != p["review_id"] or summary != p["validation_summary"]:
                        raise LocalWorkflowError("Approval or evidence changed since promotion.")
                    report["warnings"].extend(policy["warnings"])
                    if p["status"] in {"promoted", "paused"}:
                        target = (p["previous_configuration"] if p["status"] == "paused"
                                  else p.get("activated_configuration"))
                        if state["configuration"] != target:
                            report["warnings"].append({"promotion_id": p["promotion_id"],
                                                       "check": "rollback_order",
                                                       "detail": "Undo later configuration changes before rollback."})
                report["passed"].append({"promotion_id": p["promotion_id"], "check": "promotion_metadata_and_evidence"})
            except LocalWorkflowError as error:
                report["blocked"].append({"promotion_id": p["promotion_id"], "detail": str(error)})
    except LocalWorkflowError as error:
        report["blocked"].append({"check": "configuration_consistency", "detail": str(error)})
    return report
