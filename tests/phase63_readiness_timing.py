"""Opt-in, low-overhead Phase 63 readiness diagnostics (no cProfile).

Run from the repository root with an external, new --report path. The script
constructs one real developer lifecycle, times one explicit readiness audit,
and writes only timing/count metadata; source and journal contents are omitted.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import ExitStack
import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODULES = {
    "promotion": "src.developer.promotion",
    "configuration": "src.developer.configuration",
    "deployment": "src.developer.deployment",
    "operations": "src.developer.operations",
    "reliability": "src.developer.reliability",
    "continuity": "src.developer.continuity",
    "assurance": "src.developer.assurance",
    "recovery_governance": "src.developer.recovery_governance",
    "assurance_operations": "src.developer.assurance_operations",
    "maturity": "src.developer.maturity",
    "evolution": "src.developer.evolution",
    "governance": "src.developer.governance",
    "strategic_governance": "src.developer.strategic_governance",
    "governance_operations": "src.developer.governance_operations",
    "readiness": "src.developer.readiness",
}

SETUP_STAGES = {
    "configuration_activation": ("configuration", "transition_configuration"),
    "deployment_transition": ("deployment", "transition_deployment"),
    "operation_create": ("operations", "create_operation"),
    "operation_transition": ("operations", "transition_operation"),
    "recovery_create": ("reliability", "create_recovery_plan"),
    "recovery_verify": ("reliability", "verify_recovery"),
    "continuity_create": ("continuity", "create_scenario"),
    "continuity_test": ("continuity", "test_scenario"),
    "assurance_create": ("assurance", "create_assurance"),
    "assurance_verify": ("assurance", "verify_assurance"),
    "recovery_governance_register": ("recovery_governance", "register"),
    "recovery_governance_change": ("recovery_governance", "change"),
    "recovery_governance_record": ("recovery_governance", "record_check"),
    "assurance_operation_create": ("assurance_operations", "create"),
    "assurance_operation_review": ("assurance_operations", "record_review"),
    "maturity_create": ("maturity", "create"),
    "maturity_add_plan": ("maturity", "add_plan"),
    "maturity_review_plan": ("maturity", "review_plan"),
    "maturity_assess": ("maturity", "assess"),
    "evolution_create": ("evolution", "create"),
    "evolution_impact": ("evolution", "record_impact"),
    "strategic_create": ("strategic_governance", "create"),
    "strategic_add_roadmap": ("strategic_governance", "add_roadmap"),
    "strategic_record_review": ("strategic_governance", "record_review"),
    "decision_create": ("governance_operations", "create"),
    "decision_transition": ("governance_operations", "transition"),
    "decision_review": ("governance_operations", "record_review"),
    "readiness_create": ("readiness", "create"),
}

AUDIT_CHECKS = {
    "governance.optimize_health": ("governance", "optimize_health"),
    "configuration._check": ("configuration", "_check"),
    "promotion._evidence": ("promotion", "_evidence"),
    "deployment.deployment_governance_check": ("deployment", "deployment_governance_check"),
    "reliability.reliability_check": ("reliability", "reliability_check"),
    "reliability._verify": ("reliability", "_verify"),
    "decisions._close_report": ("governance_operations", "_close_report"),
    "strategic.review": ("strategic_governance", "review"),
    "evolution.review": ("evolution", "review"),
    "maturity._review": ("maturity", "_review"),
    "recovery_governance.review": ("recovery_governance", "review"),
    "assurance.recovery_assurance": ("assurance", "recovery_assurance"),
}


def _counter():
    return defaultdict(lambda: {"calls": 0, "seconds": 0.0, "max_seconds": 0.0})


def _record(metrics, key, elapsed):
    row = metrics[key]
    row["calls"] += 1
    row["seconds"] += elapsed
    row["max_seconds"] = max(row["max_seconds"], elapsed)


def _wrap(module, name, metrics, key, on_result=None):
    original = getattr(module, name)

    def measured(*args, **kwargs):
        started = time.perf_counter()
        try:
            result = original(*args, **kwargs)
        finally:
            _record(metrics, key, time.perf_counter() - started)
        if on_result:
            on_result(result)
        return result

    return original, measured


def _install_load_metrics(stack, modules, metrics, extras):
    """Count nested loads/replays, shared _read calls and _apply time."""
    for name, module in modules.items():
        if not hasattr(module, "_load"):
            continue
        def count_events(result, name=name):
            events = result.get("events", []) if isinstance(result, dict) else []
            extras["state_event_counts_returned"][name] += len(events)
            extras["load_calls"][name] += 1

        # on_result only runs for successful loads; failures are still timed.
        _, measured = _wrap(module, "_load", metrics, f"loads.{name}", count_events)
        stack.enter_context(_patch(module, "_load", measured))
        if hasattr(module, "_apply"):
            _, apply_wrapper = _wrap(module, "_apply", metrics, f"apply.{name}")
            stack.enter_context(_patch(module, "_apply", apply_wrapper))

    optimization = importlib.import_module("src.developer.optimization")
    reader_metrics = metrics
    def timed_read(original):
        def read(workspace, path):
            caller = sys._getframe(1).f_globals.get("__name__", "?")
            try:
                extras["read_bytes"] += Path(path).stat().st_size
                extras["file_reads_by_module"][caller] += 1
            except OSError:
                pass
            started = time.perf_counter()
            try:
                return original(workspace, path)
            finally:
                _record(reader_metrics, "file_read_and_json_decode", time.perf_counter() - started)
        return read

    # Each module imports _read by value, so patch each local alias as well.
    for module in [optimization, *modules.values()]:
        if hasattr(module, "_read"):
            original = module._read
            wrapped = timed_read(original)
            stack.enter_context(_patch(module, "_read", wrapped))


def _patch(module, name, replacement):
    from unittest.mock import patch
    return patch.object(module, name, replacement)


def _instrument_audit(modules, readiness, metrics, extras, stack):
    _install_load_metrics(stack, modules, metrics, extras)
    reliability = modules["reliability"]
    original_digest = reliability._digest

    def digest(value):
        caller = sys._getframe(1)
        key = f"{caller.f_globals.get('__name__', '?')}.{caller.f_code.co_name}"
        shallow_bytes = sys.getsizeof(value)
        if isinstance(value, dict):
            for index, (item_key, item_value) in enumerate(value.items()):
                if index == 128:
                    break
                shallow_bytes += sys.getsizeof(item_key) + sys.getsizeof(item_value)
        elif isinstance(value, (list, tuple)):
            shallow_bytes += sum(sys.getsizeof(item) for item in value[:128])
        started = time.perf_counter()
        try:
            return original_digest(value)
        finally:
            elapsed = time.perf_counter() - started
            _record(metrics, "digest.reliability._digest", elapsed)
            digest_row = extras["digest_by_callsite"][key]
            digest_row["calls"] += 1
            digest_row["seconds"] += elapsed
            digest_row["max_seconds"] = max(digest_row["max_seconds"], elapsed)
            digest_row["shallow_input_bytes_estimate"] += shallow_bytes
            extras["digest_callsites"][key] += 1
            extras["digest_shallow_input_bytes"] += shallow_bytes

    stack.enter_context(_patch(reliability, "_digest", digest))
    for label, (module_name, function_name) in AUDIT_CHECKS.items():
        module = modules[module_name]
        _, wrapper = _wrap(module, function_name, metrics, f"checks.{label}")
        stack.enter_context(_patch(module, function_name, wrapper))
    original_audit = readiness._audit_with_context

    def audit_wrapper(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_audit(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - started
            _record(metrics, "audit.readiness._audit_with_context", elapsed)
            extras["audit_seconds"].append(elapsed)
            tested_case = extras.get("tested_case")
            workspace_path = getattr(tested_case, "workspace_path", None)
            role = ("test_workspace" if workspace_path is not None and
                    Path(args[0].root) == Path(workspace_path) else "prepared_seed")
            extras["audit_calls_by_workspace"][role] += 1
            extras["audit_seconds_by_workspace"][role].append(elapsed)

    stack.enter_context(_patch(readiness, "_audit_with_context", audit_wrapper))


def _instrument_setup(modules, metrics, stack):
    for label, (module_name, function_name) in SETUP_STAGES.items():
        module = modules[module_name]
        _, wrapper = _wrap(module, function_name, metrics, f"setup.{label}")
        stack.enter_context(_patch(module, function_name, wrapper))


def _instrument_fixture_methods(case, metrics, stack):
    for label, method_name in (("deployment_prerequisites", "_deployment_setup"),
                               ("governance_decision_review", "_governance_ops_decide")):
        _, wrapper = _wrap(case, method_name, metrics, f"setup.{label}")
        stack.enter_context(_patch(case, method_name, wrapper))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--test", choices=("complete-audit", "drift"), default="complete-audit",
                        help="Measure one explicit audit or execute the drift/expiry unittest with audit counters.")
    options = parser.parse_args()
    report_path = options.report.resolve()
    if report_path == ROOT or ROOT in report_path.parents or report_path.exists():
        parser.error("--report must be a new path outside the checkout")

    from tests.test_developer_mode import DeveloperModeTests

    modules = {name: importlib.import_module(path) for name, path in MODULES.items()}
    test_name = ("test_operational_readiness_complete_chain_closure_and_history"
                 if options.test == "complete-audit" else
                 "test_operational_readiness_drift_expiry_and_compatibility")
    case = DeveloperModeTests(test_name)
    output = {"notice": "Developer-only diagnostic timings; not a benchmark or productivity score.",
              "profiled": False, "report_path": str(report_path), "phase62_head_expected": "c08fe30b39ec8dedf6f42ebbe361c14d169f714f",
              "setup": {}, "audit": {}, "environment": {"python": sys.version, "platform": sys.platform}}
    if options.test == "drift":
        # Build/copy the prepared lifecycle before instrumentation. The diagnostic
        # window should cover the real drift test, not the fixture's own seed audit.
        case.setUp()
        audit_metrics = _counter()
        extras = {"load_calls": defaultdict(int), "state_event_counts_returned": defaultdict(int),
                  "audit_seconds": [],
                  "tested_case": case,
                  "audit_calls_by_workspace": defaultdict(int),
                  "audit_seconds_by_workspace": defaultdict(list),
                  "digest_callsites": defaultdict(int), "digest_by_callsite": defaultdict(
                      lambda: {"calls": 0, "seconds": 0.0, "max_seconds": 0.0,
                               "shallow_input_bytes_estimate": 0}),
                  "digest_shallow_input_bytes": 0, "read_bytes": 0,
                  "file_reads_by_module": defaultdict(int)}
        contexts = []
        readiness_module = modules["readiness"]
        original_context = readiness_module.DeveloperReadContext

        def tracked_context():
            context = original_context()
            contexts.append(context)
            return context

        with ExitStack() as stack:
            _instrument_audit(modules, readiness_module, audit_metrics, extras, stack)
            stack.enter_context(_patch(case, "setUp", lambda: None))
            stack.enter_context(_patch(readiness_module, "DeveloperReadContext", tracked_context))
            result = unittest.TestResult()
            started = time.perf_counter()
            case.run(result)
            elapsed = time.perf_counter() - started
        output["test"] = {"name": test_name, "seconds": elapsed, "run": result.testsRun,
                          "failures": [{"test": str(row[0]), "traceback": row[1]}
                                       for row in result.failures],
                          "errors": [{"test": str(row[0]), "traceback": row[1]}
                                     for row in result.errors],
                          "skipped": [str(row[0]) for row in result.skipped]}
        output["audit"] = {"audit_calls": audit_metrics["audit.readiness._audit_with_context"]["calls"],
                   "seconds_total": audit_metrics["audit.readiness._audit_with_context"]["seconds"],
                   "seconds_max": audit_metrics["audit.readiness._audit_with_context"]["max_seconds"],
                           "seconds_each_call": extras["audit_seconds"],
                           "calls_by_workspace": dict(extras["audit_calls_by_workspace"]),
                           "seconds_by_workspace": dict(extras["audit_seconds_by_workspace"]),
                           "metrics": dict(audit_metrics),
                           "contexts": [context.summary() for context in contexts],
                           "digest_callsites": dict(extras["digest_callsites"]),
                           "digest_by_callsite": dict(extras["digest_by_callsite"]),
                           "journal_file_reads": dict(extras["file_reads_by_module"]),
                           "file_bytes_read": extras["read_bytes"]}
        output["exit_code"] = int(bool(result.failures or result.errors or not result.testsRun))
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("x", encoding="utf-8") as stream:
            json.dump(output, stream, indent=2)
        if output["exit_code"]:
            raise SystemExit(output["exit_code"])
        return
    try:
        case.setUp()
        setup_metrics = _counter()
        with ExitStack() as stack:
            _instrument_setup(modules, setup_metrics, stack)
            _instrument_fixture_methods(case, setup_metrics, stack)
            started = time.perf_counter()
            record, _, _ = case._operational_readiness_setup()
            output["setup"] = {"total_seconds": time.perf_counter() - started,
                               "stages": dict(setup_metrics)}

        audit_metrics = _counter()
        context = modules["readiness"].DeveloperReadContext()
        extras = {"load_calls": defaultdict(int), "state_event_counts_returned": defaultdict(int),
                  "audit_seconds": [],
                  "tested_case": case,
                  "audit_calls_by_workspace": defaultdict(int),
                  "audit_seconds_by_workspace": defaultdict(list),
                  "digest_callsites": defaultdict(int), "digest_by_callsite": defaultdict(
                      lambda: {"calls": 0, "seconds": 0.0, "max_seconds": 0.0,
                               "shallow_input_bytes_estimate": 0}),
                  "digest_shallow_input_bytes": 0,
                  "read_bytes": 0, "file_reads_by_module": defaultdict(int)}
        with ExitStack() as stack:
            _instrument_audit(modules, modules["readiness"], audit_metrics, extras, stack)
            started = time.perf_counter()
            result = modules["readiness"]._audit_with_context(
                case.developer, record["deployment_id"], record["decision_id"], context)
            audit_seconds = time.perf_counter() - started
        output["audit"] = {"seconds": audit_seconds, "passed_count": len(result["passed"]),
                           "seconds_each_call": extras["audit_seconds"],
                           "warning_count": len(result["warnings"]), "blocked_count": len(result["blocked"]),
                           "metrics": dict(audit_metrics),
                           "journal_load_calls": dict(extras["load_calls"]),
                           "state_event_counts_returned": dict(extras["state_event_counts_returned"]),
                           "read_context": context.summary(),
                           "digest_callsites": dict(extras["digest_callsites"]),
                           "digest_by_callsite": dict(extras["digest_by_callsite"]),
                           "digest_shallow_input_bytes_estimate": extras["digest_shallow_input_bytes"],
                           "file_bytes_read": extras["read_bytes"],
                           "journal_file_reads": dict(extras["file_reads_by_module"])}
    except BaseException:
        output["error"] = traceback.format_exc()
        raise
    finally:
        try:
            case.doCleanups()
        finally:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with report_path.open("x", encoding="utf-8") as stream:
                json.dump(output, stream, indent=2)


if __name__ == "__main__":
    main()
