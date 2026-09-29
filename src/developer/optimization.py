"""Evidence-linked developer experiments, with explicit decisions and no tuning."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
import re
from uuid import uuid4

from .local_workflow import LocalWorkflowError, _json_bytes, _safe_component
from .observability import collect, failure_patterns
from .regression import SCHEMA as BASELINE_SCHEMA, _evidence, compare_records, snapshot

MODE = "developer-local-optimization"
SCHEMA = "developer-optimization-v1"


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise LocalWorkflowError("Optimization IDs and versions require 1-64 letters, digits, underscores or hyphens.")
    return value


def _read(workspace, path):
    try:
        document = json.loads(workspace._contained(path).read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("record must be a JSON object")
        return document
    except (OSError, ValueError) as error:
        raise LocalWorkflowError(f"Cannot read developer optimization evidence '{path}': {error}") from error


def _write(workspace, path, document):
    path = workspace._contained(path)
    document = {"schema_version": SCHEMA, "mode": MODE,
                "recorded_at": datetime.now(timezone.utc).isoformat(), **document}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(_json_bytes(document))
    except FileExistsError as error:
        raise LocalWorkflowError("Optimization record already exists; choose a new candidate ID.") from error
    return document


def _storage(workspace, identifier):
    workspace._prepare()
    return workspace._contained(workspace.root / "optimization" / "candidates" / _name(identifier))


def create_candidate(workspace, identifier, problem, cases, source, proposed_change, validation_method, supersedes=None, retrieval_settings=None):
    from .promotion import validate_settings
    retrieval_settings = validate_settings({} if retrieval_settings is None else retrieval_settings)
    directory = _storage(workspace, identifier)
    if any(not isinstance(value, str) or not value.strip()
           for value in (problem, proposed_change, validation_method)):
        raise LocalWorkflowError("Problem, proposed change and validation method must be nonempty.")
    if not cases or not source or any(not isinstance(value, str) or not value.strip() for value in cases + source):
        raise LocalWorkflowError("Candidate requires affected cases and evidence event IDs.")
    events = {event["event_id"]: event for event in collect(workspace)}
    if any(value not in events or "record" not in events[value] for value in source):
        raise LocalWorkflowError("Evidence must reference existing developer retrieval or regression events.")
    evidence = [events[value] for value in source]
    repositories = {event["repository_id"] for event in evidence}
    if len(repositories) != 1 or not set(cases) <= {event["query_id"] for event in evidence}:
        raise LocalWorkflowError("Evidence must cover affected cases in exactly one repository.")
    if supersedes is not None:
        previous = show_candidates(workspace, supersedes)["candidates"][0]
        if previous["repository_id"] not in repositories:
            raise LocalWorkflowError("A superseding experiment must target the same repository.")
        if not previous["decision"] or previous["decision"]["status"] != "rejected":
            raise LocalWorkflowError("A new attempt may only supersede a previously rejected candidate.")
    return _write(workspace, directory / "candidate.json", {
        "id": identifier, "problem": problem.strip(), "cases": sorted(set(cases)),
        "source": sorted(set(source)), "repository_id": repositories.pop(),
        "proposed_change": proposed_change.strip(), "validation_method": validation_method.strip(),
        "supersedes": supersedes, "retrieval_settings": retrieval_settings, "status": "candidate", "result": None})


def show_candidates(workspace, identifier=None):
    workspace._prepare()
    root = workspace._contained(workspace.root / "optimization" / "candidates")
    paths = [_storage(workspace, identifier) / "candidate.json"] if identifier else sorted(root.glob("*/candidate.json"))
    events = collect(workspace)
    candidates = []
    for path in paths:
        candidate = _read(workspace, path)
        if candidate.get("schema_version") != SCHEMA or candidate.get("mode") != MODE:
            raise LocalWorkflowError("Unsupported optimization candidate schema or mode.")
        validations = workspace._contained(path.parent / "validations")
        candidate["validations"] = sorted((_read(workspace, p) for p in validations.glob("*.json")),
                                          key=lambda item: (item["recorded_at"], item["id"]))
        decision = workspace._contained(path.parent / "decision.json")
        candidate["decision"] = _read(workspace, decision) if decision.exists() else None
        candidate["status"] = (candidate["decision"]["status"] if candidate["decision"] else
                               "validated" if candidate["validations"] else "candidate")
        candidate["result"] = candidate["validations"][-1] if candidate["validations"] else None
        candidate["evidence"] = [event for event in events if event["event_id"] in candidate["source"]]
        candidates.append(candidate)
    cache = {}
    for candidate in candidates:
        lineage, seen, current = [], set(), candidate["id"]
        while current is not None and current not in seen:
            seen.add(current)
            lineage.append(_lineage_status(workspace, current, cache))
            current = lineage[-1]["supersedes"]
        lineage.reverse()
        candidate["history"] = [{"attempt": index + 1, "candidate_id": item["id"], "status": item["status"],
                                 "reason": item["reason"]} for index, item in enumerate(lineage)]
    unresolved = sorted(item["id"] for item in candidates if item["status"] in {"candidate", "validated"})
    return {"mode": MODE, "candidates": candidates, "suggested_inputs": failure_patterns(events),
            "unresolved_candidates": unresolved}


def _lineage_status(workspace, identifier, cache):
    if identifier in cache:
        return cache[identifier]
    path = _storage(workspace, identifier) / "candidate.json"
    candidate = _read(workspace, path)
    decision_path = workspace._contained(path.parent / "decision.json")
    decision = _read(workspace, decision_path) if decision_path.exists() else None
    validations_dir = workspace._contained(path.parent / "validations")
    has_validation = validations_dir.exists() and any(validations_dir.glob("*.json"))
    status = decision["status"] if decision else "validated" if has_validation else "candidate"
    entry = {"id": identifier, "status": status, "reason": decision["note"] if decision else None,
             "supersedes": candidate.get("supersedes")}
    cache[identifier] = entry
    return entry


def _version(workspace, repository_id, version):
    _name(version)
    storage = workspace._contained(workspace.root / "regression" / _safe_component(repository_id))
    paths = [workspace._contained(storage / namespace / f"{version}.json")
             for namespace in ("baselines", "history")]
    found = [path for path in paths if path.exists()]
    if len(found) != 1:
        raise LocalWorkflowError("Version must identify exactly one saved baseline or regression history ID.")
    value = _read(workspace, found[0])
    doc = value.get("snapshot", value)
    try:
        if (doc["schema_version"] != BASELINE_SCHEMA or doc["mode"] != "developer-local-regression"
                or doc["repository_id"] != repository_id or not doc["records"]
                or len({row["id"] for row in doc["records"]}) != len(doc["records"])):
            raise ValueError("schema, repository or cases differ")
        for record in doc["records"]:
            compare_records(record, record)
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise LocalWorkflowError(f"Invalid developer version: {error}") from error
    return doc, value.get("report")


def _duplicates(record):
    identities = [(item["file"], item["symbol"]) for item in record["ranking"]["order"]]
    identities += [(item.get("file_path"), item.get("symbol_name"))
                   for item in record["context"].get("expanded_symbols", [])]
    return sum(count - 1 for count in Counter(identities).values())


def _explanation_lost(before, after):
    if isinstance(before, dict):
        return not isinstance(after, dict) or any(
            key not in after or _explanation_lost(value, after[key]) for key, value in before.items())
    if isinstance(before, list):
        return not isinstance(after, list) or any(value not in after for value in before)
    return bool(before) and not after


def compare_versions(workspace, before, after, repository_id=None):
    workspace._prepare()
    if repository_id is None:
        repositories = {event["repository_id"] for event in collect(workspace) if event["kind"] == "regression"}
        if len(repositories) != 1:
            raise LocalWorkflowError("Pass --repository-id to select exactly one developer repository.")
        repository_id = repositories.pop()
    old, _ = _version(workspace, repository_id, before)
    new, report = _version(workspace, repository_id, after)
    if old["top_k"] != new["top_k"] or {r["id"] for r in old["records"]} != {r["id"] for r in new["records"]}:
        raise LocalWorkflowError("Versions must have identical case IDs and top-k.")
    previous = {r["id"]: r for r in old["records"]}
    comparisons = []
    for record in new["records"]:
        prior = previous[record["id"]]
        try:
            difference = compare_records(prior, record)
        except ValueError as error:
            raise LocalWorkflowError(str(error)) from error
        old_files, old_symbols, _ = _evidence(prior)
        new_files, new_symbols, _ = _evidence(record)
        required_files = set(record["expected"].get("files", []))
        required_symbols = set(record["expected"].get("symbols", [])) | set(record["required_relationships"])
        gained = {"files": sorted((new_files - old_files) & required_files),
                  "symbols": sorted((new_symbols - old_symbols) & required_symbols)}
        lost = {"files": sorted((old_files - new_files) & required_files),
                "symbols": sorted((old_symbols - new_symbols) & required_symbols)}
        removed_extra = sorted((old_files - new_files) - required_files - set(record["allowed_extra_context"]))
        regressions, improvements = [], []
        if any(lost.values()):
            regressions.append("expected_evidence_lost")
        if difference["newly_introduced_noise"] and not record["failure_tolerance"].get("allow_extra_files", False):
            regressions.append("undeclared_context_added")
        if any(gained.values()):
            improvements.append("expected_evidence_gained")
        if removed_extra:
            improvements.append("undeclared_context_removed")
        if _duplicates(record) > _duplicates(prior):
            regressions.append("duplicate_context_increased")
        if _duplicates(record) < _duplicates(prior):
            improvements.append("duplicate_context_reduced")
        old_reasons = {(item["file"], item["symbol"]): item for item in prior["ranking"]["reasons"]}
        explanation_lost = any(
            _explanation_lost(old_reasons[(item["file"], item["symbol"])].get("explanation", {}), item.get("explanation", {}))
            for item in record["ranking"]["reasons"] if (item["file"], item["symbol"]) in old_reasons)
        if explanation_lost or any(item["kind"] == "explanation_removed" for item in difference["changes"]):
            regressions.append("explanations_removed")
        if report and any(item["case_id"] == record["id"] and not item["stable"] for item in report["stability"]):
            regressions.append("unstable_ranking")
        comparisons.append({**difference, "added_evidence": {"files": sorted(new_files - old_files), "symbols": sorted(new_symbols - old_symbols)},
            "removed_evidence": {"files": sorted(old_files - new_files), "symbols": sorted(old_symbols - new_symbols)},
            "expected_gained": gained, "expected_lost": lost, "removed_undeclared_context": removed_extra,
            "improvements": improvements, "regressions": regressions,
            "classification": "regression" if regressions else "improved" if improvements else "observed_change" if difference["behavior_changed"] else "unchanged",
            "explanation_changes": None if prior["ranking"]["reasons"] == record["ranking"]["reasons"] else {
                "before": prior["ranking"]["reasons"], "after": record["ranking"]["reasons"]}})
    return {"mode": MODE, "repository_id": repository_id, "before": before, "after": after,
            "comparisons": comparisons, "limitations": ["Undeclared context is not proven unnecessary.",
                "Named baselines were stable when captured; history versions retain repeat-run checks.",
                "Descriptive developer evidence only; no quality scores or causal improvement claim."]}


def validate_candidate(workspace, identifier, repository, cases_path, before, ranking_notes=None):
    from .promotion import EXPERIMENT, active_configuration, validate_settings
    candidate = show_candidates(workspace, identifier)["candidates"][0]
    settings = validate_settings(candidate.get("retrieval_settings", {}))
    base = active_configuration(workspace)
    token = EXPERIMENT.set((candidate["repository_id"], settings))
    try:
        return _validate_candidate(workspace, identifier, repository, cases_path, before, ranking_notes,
                                   settings, base)
    finally:
        EXPERIMENT.reset(token)


def _validate_candidate(workspace, identifier, repository, cases_path, before, ranking_notes,
                        settings, base):
    from .local_workflow import scan_local_repository
    candidate = show_candidates(workspace, identifier)["candidates"][0]
    if candidate["decision"]:
        raise LocalWorkflowError("Candidate already decided; create a new candidate for further experiments.")
    workspace._prepare(repository)
    inventory = scan_local_repository(repository)
    if inventory.repository_id != candidate["repository_id"]:
        raise LocalWorkflowError("Candidate evidence belongs to another repository.")
    old, _ = _version(workspace, inventory.repository_id, before)
    if not set(candidate["cases"]) <= {row["id"] for row in old["records"]}:
        raise LocalWorkflowError("Baseline must cover every affected candidate case.")
    ranking_notes = ranking_notes or {}
    if (not isinstance(ranking_notes, dict) or set(ranking_notes) - {row["id"] for row in old["records"]}
            or any(not isinstance(note, str) or not note.strip() for note in ranking_notes.values())):
        raise LocalWorkflowError("Ranking notes require a nonempty explanation for each reviewed case.")
    # Only immutable named baselines can drive a live regression run.
    report = workspace.regression(repository, cases_path, baseline=before, top_k=old["top_k"])
    comparison = compare_versions(workspace, before, report["history_id"], inventory.repository_id)
    current, _ = _version(workspace, inventory.repository_id, report["history_id"])
    compatibility = []
    for record in current["records"]:
        checks = {"case_id": record["id"], "trace": False, "diagnose": False}
        try:
            trace = workspace.trace(record["query"], repository, old["top_k"])
            checks["trace"] = (trace["mode"] == "developer-local-retrieval-trace"
                and isinstance(trace["trace"]["selected_results"], list)
                and snapshot(record, trace, repository.name) == record)
            diagnosis = workspace.diagnose(record["id"], cases_path, repository, old["top_k"])
            diagnosed = snapshot(record, diagnosis, repository.name)
            expected_ranking = deepcopy(record["ranking"])
            # Query adds freshness to each ranking reason; diagnose reports it at the top level.
            for ranking in (expected_ranking, diagnosed["ranking"]):
                for reason in ranking["reasons"]:
                    reason["reason"].pop("index_freshness", None)
            checks["diagnose"] = (diagnosis["mode"] == "developer-local-context-diagnosis"
                and diagnosis["case_id"] == record["id"] and isinstance(diagnosis["missing_evidence"], list)
                and isinstance(diagnosis["likely_causes"], list)
                and diagnosis["index_freshness"]["status"] == "current"
                and diagnosed["retrieved"] == record["retrieved"]
                and diagnosed["ranking"] == expected_ranking)
        except (LocalWorkflowError, ValueError, KeyError, TypeError) as error:
            checks["error"] = str(error)
        compatibility.append(checks)
    rows = comparison["comparisons"]
    gates = {
        "regression_cases": not any(row["regressions"] for row in rows),
        "stability": bool(report["stability"]) and all(row["stable"] for row in report["stability"]),
        "ranking_review": all(not row["ranking_differences"] or bool(ranking_notes.get(row["case_id"], "").strip()) for row in rows),
        "duplicate_context": not any("duplicate_context_increased" in row["regressions"] for row in rows),
        "trace_compatibility": all(row["trace"] for row in compatibility),
        "diagnose_compatibility": all(row["diagnose"] for row in compatibility),
    }
    validation_id = uuid4().hex
    return _write(workspace, _storage(workspace, identifier) / "validations" / f"{validation_id}.json", {
        "id": validation_id, "candidate_id": identifier, "retrieval_settings": settings,
        "base_configuration": base, "before": before, "after": report["history_id"],
        "gates": gates, "passed": all(gates.values()), "ranking_notes": ranking_notes,
        "compatibility": compatibility, "comparison": comparison, "status": "validated"})


def decide_candidate(workspace, identifier, decision, note):
    if decision not in {"accepted", "rejected"} or not isinstance(note, str) or not note.strip():
        raise LocalWorkflowError("Decision requires accepted/rejected and a nonempty review note.")
    candidate = show_candidates(workspace, identifier)["candidates"][0]
    result = candidate["result"]
    if decision == "accepted" and (not result or not result["passed"] or not all(result["gates"].values())):
        raise LocalWorkflowError("Acceptance requires the latest validation to pass every gate.")
    validation_summary = None
    if result:
        rows = result["comparison"]["comparisons"]
        validation_summary = {"regressions": sum(bool(row["regressions"]) for row in rows),
                              "improvements": sum(bool(row["improvements"]) for row in rows),
                              "stability_passed": result["gates"]["stability"],
                              "passed": result["passed"]}
    return _write(workspace, _storage(workspace, identifier) / "decision.json", {
        "candidate_id": identifier, "status": decision, "reason": note.strip(), "note": note.strip(),
        "evidence": candidate["source"], "validation_id": result["id"] if result else None,
        "validation": validation_summary,
        "rollback": {"restore_to": result["before"] if result else None,
                     "instructions": "Manually revert the applied change and reindex; "
                                     "this tool does not modify source files."},
        "scope": "Decision applies only to the recorded experiment; no retrieval settings or code are modified."})
