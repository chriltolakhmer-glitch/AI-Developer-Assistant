"""Developer-only descriptive history. Never reads research or benchmark records."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from .regression import snapshot, compare_records, _portable

MODE = "developer-local-observability"
SCHEMA = "developer-retrieval-event-v1"


def _write(workspace, document):
    from .local_workflow import _json_bytes
    workspace._prepare()
    identifier = uuid4().hex
    path = workspace._contained(workspace.root / "observability" / "events" / f"{identifier}.json")
    document = {"schema_version": SCHEMA, "mode": MODE, "event_id": identifier,
                "timestamp": datetime.now(timezone.utc).isoformat(), **document}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(_json_bytes(document))
    return document


def record_retrieval(workspace, payload, inventory, index, command, top_k):
    from .local_workflow import _INDEX_SCHEMA
    from .ranking import RANKING_VERSION
    query = payload.get("question", payload.get("query", ""))
    query_id = payload.get("case_id") or "query-" + hashlib.sha256(query.strip().encode()).hexdigest()[:16]
    case = {"id": query_id, "query": query, "expected": payload.get("expected_evidence", {})}
    record = snapshot(case, payload, inventory.root.name)
    return _write(workspace, {
        "kind": "retrieval", "command": command, "query_id": query_id,
        "repository_id": inventory.repository_id, "index_version": _INDEX_SCHEMA if index else None,
        "index_generation": index.path.name if index else None,
        "retrieval_version": RANKING_VERSION, "configuration": {"top_k": top_k},
        "record": record, "retrieved_files": record["retrieved"]["files"],
        "retrieved_symbols": record["retrieved"]["symbols"],
        "ranking_reasons": record["ranking"]["reasons"], "context_changes": record["context"],
        "exclusions": [item for item in inventory.file_decisions if not item["included"]],
        "diagnostics": {key: _portable(payload[key]) for key in
                        ("index_freshness", "likely_causes", "missing_evidence", "confidence") if key in payload},
    })


def _read(workspace, pattern):
    from .local_workflow import LocalWorkflowError
    # Check the root before globbing, and each file before opening (including junctions).
    workspace._contained(workspace.root / pattern.split("/")[0])
    for path in sorted(workspace.root.glob(pattern)):
        workspace._contained(path)
        try:
            yield json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise LocalWorkflowError(f"Cannot read developer history '{path}': {error}") from error


def collect(workspace):
    from .local_workflow import LocalWorkflowError
    workspace._prepare()
    events = []
    for item in _read(workspace, "observability/events/*.json"):
        if item.get("schema_version") != SCHEMA or item.get("mode") != MODE:
            raise LocalWorkflowError("Unsupported developer event schema or mode.")
        events.append(item)
    # Phase 37 history is read in place; no migration or duplicate captures.
    for item in _read(workspace, "regression/*/history/*.json"):
        doc, report = item.get("snapshot", {}), item.get("report", {})
        if doc.get("schema_version") != "developer-retrieval-baseline-v1" or doc.get("mode") != "developer-local-regression":
            raise LocalWorkflowError("Unsupported developer regression history.")
        for record in doc["records"]:
            comparison = next(row for row in report["comparisons"] if row["case_id"] == record["id"])
            events.append({"schema_version": SCHEMA, "mode": MODE, "kind": "regression",
                "event_id": report["history_id"] + ":" + record["id"], "timestamp": item["recorded_at"],
                "query_id": record["id"], "repository_id": doc["repository_id"],
                "index_version": doc["index_version"], "index_generation": doc["index_generation"],
                "retrieval_version": doc["retrieval_version"], "configuration": {"top_k": doc["top_k"], "runtime": doc["index_runtime"]},
                "baseline": report["baseline"], "baseline_created": report["baseline_created"],
                "record": record, "comparison": comparison, "diagnostics": comparison["changes"],
                "retrieved_files": record["retrieved"]["files"], "retrieved_symbols": record["retrieved"]["symbols"],
                "ranking_reasons": record["ranking"]["reasons"], "context_changes": record["context"],
                "exclusions": {"context": record["context"].get("excluded_context"),
                               "inventory": "not recorded by Phase 37"}})
    return sorted(events, key=lambda row: (row["timestamp"], row["event_id"]))


def failure_patterns(events):
    groups = {}
    causes = {"missing_symbol": "Parser coverage or candidate selection gap.",
              "missing_relationship": "Static relationship detection or dependency expansion gap.",
              "unrelated_context": "Undeclared context; inspect case allowances before treating it as excessive.",
              "unstable_ranking": "Repeated retrieval differs; inspect ties and model determinism.",
              "unsupported_file_type": "Local indexing supports Python only."}
    for event in events:
        findings = []
        comparison = event.get("comparison", {})
        missing = comparison.get("missing_evidence", {})
        for key, kind in (("symbols", "missing_symbol"), ("relationships", "missing_relationship")):
            findings.extend((kind, value) for value in missing.get(key, []))
        record = event.get("record")
        for value in missing.get("files", []):
            if not value.endswith(".py"):
                findings.append(("unsupported_file_type", value))
        if event["kind"] == "regression" and record:
            from .regression import _evidence
            files, _, _ = _evidence(record)
            allowed = set(record["expected"].get("files", [])) | set(record["allowed_extra_context"])
            findings.extend(("unrelated_context", value) for value in sorted(files - allowed))
        if any(row["kind"] == "unstable_ranking_changes" for row in comparison.get("changes", [])):
            findings.append(("unstable_ranking", "repeated retrieval"))
        diagnostics = event.get("diagnostics", {})
        if isinstance(diagnostics, dict):
            for row in diagnostics.get("missing_evidence", []):
                if row["type"] in ("symbol", "relationship"):
                    findings.append(("missing_" + row["type"], row["value"]))
            for cause in diagnostics.get("likely_causes", []):
                if cause.startswith("unsupported language or file type:"):
                    findings.append(("unsupported_file_type", cause.split(":", 1)[1].strip()))
        for kind, evidence in set(findings):
            key = (event["repository_id"], kind, evidence)
            group = groups.setdefault(key, {"repository_id": key[0], "pattern": kind, "evidence": evidence,
                "cases": set(), "event_ids": set(), "possible_cause": causes[kind], "related_diagnostics": []})
            group["cases"].add(event["query_id"])
            group["event_ids"].add(event["event_id"])
            group["related_diagnostics"].append({"event_id": event["event_id"], "diagnostics": diagnostics})
    return [{**group, "cases": sorted(group["cases"]), "event_ids": sorted(group["event_ids"])}
            for _, group in sorted(groups.items()) if len(group["event_ids"]) >= 2]


def inspect_history(workspace, query=None, repository_id=None, limit=20):
    from .local_workflow import LocalWorkflowError
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise LocalWorkflowError("History limit must be between 1 and 1000.")
    events = [event for event in collect(workspace)
              if (query is None or event.get("query_id") == query)
              and (repository_id is None or event["repository_id"] == repository_id)]
    previous, changes = {}, []
    for event in events:
        if "record" not in event:
            continue
        key = (event["repository_id"], event["query_id"], event["kind"], event.get("command"))
        old = previous.get(key)
        if old:
            try:
                difference = compare_records(old["record"], event["record"])
            except ValueError:
                difference = {"behavior_changed": True, "note": "Case definition changed; evidence is not directly comparable."}
            if difference["behavior_changed"]:
                changes.append({"event_id": event["event_id"], "previous_event_id": old["event_id"], **difference})
        previous[key] = event
    return {"mode": MODE, "events": list(reversed(events[-limit:])), "behavior_changes": changes,
            "failure_patterns": failure_patterns(events), "matching_events": len(events),
            "analysis_scope": "All matching history; limit applies only to displayed recent events."}


def timeline(workspace, repository_id=None, note=None):
    from .local_workflow import LocalWorkflowError
    if note is not None:
        if not repository_id or not note.strip():
            raise LocalWorkflowError("A fix note requires --repository-id and nonempty --note.")
        _write(workspace, {"kind": "fix_applied", "repository_id": repository_id,
                           "note": note.strip(), "provenance": "developer supplied; not automatically verified"})
    events = collect(workspace)
    entries, previous, seen = [], {}, set()
    for event in events:
        repo = event["repository_id"]
        if repository_id is not None and repo != repository_id:
            continue
        base = {"timestamp": event["timestamp"], "repository_id": repo, "event_id": event["event_id"]}
        if event["kind"] == "fix_applied":
            entries.append({**base, "kind": "fix_applied", "note": event["note"], "provenance": event["provenance"]})
            continue
        state = {key: event.get(key) for key in ("retrieval_version", "index_version", "index_generation", "configuration")}
        # Runtime details exist only on regression records; keep observation streams separate.
        stream = (repo, event["kind"], event.get("command"))
        if previous.get(stream) != state:
            entries.append({**base, "kind": "retrieval_state", "previous": previous.get(stream), "current": state})
            previous[stream] = state
        if event["kind"] == "regression":
            identity = (repo, event["event_id"].split(":", 1)[0])
            if identity not in seen:
                entries.append({**base, "kind": "baseline_created" if event["baseline_created"] else "regression",
                                "baseline": event["baseline"]})
                seen.add(identity)
    return {"mode": MODE, "entries": entries}
