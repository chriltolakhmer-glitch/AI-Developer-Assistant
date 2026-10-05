"""Fixed unittest worker used only by the applied-patch test workflow."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest


IDENTITY = re.compile(r"^tests(?:\.[A-Za-z_]\w*){2,}$")


def _walk(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _walk(item)
        else:
            yield item


def run(request: dict) -> dict:
    started = time.perf_counter()
    identities = request.get("test_identities")
    root = Path(request.get("repository_path", "")).resolve(strict=True)
    if (not isinstance(identities, list) or not identities
            or any(not isinstance(name, str) or not IDENTITY.fullmatch(name) for name in identities)):
        return {"exit_code": 2, "tests_run": 0, "passed": 0, "failures": 0, "errors": 1,
                "skipped": 0, "expected_failures": 0, "unexpected_successes": 0,
                "failure_tests": [], "error_tests": ["invalid test identity"], "skip_tests": [],
                "stdout": "", "stderr": "Worker rejected an invalid test identity.",
                "duration_seconds": time.perf_counter() - started}
    sys.path.insert(0, str(root))
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    try:
        for identity in identities:
            suite.addTests(loader.loadTestsFromName(identity))
        loaded = list(_walk(suite))
        loaded_ids = [test.id() for test in loaded]
        if len(loaded_ids) != len(identities) or sorted(loaded_ids) != sorted(identities):
            raise ValueError("test loader expanded or changed the authorized identity set")
    except Exception as error:
        return {"exit_code": 2, "tests_run": 0, "passed": 0, "failures": 0, "errors": 1,
                "skipped": 0, "expected_failures": 0, "unexpected_successes": 0,
                "failure_tests": [], "error_tests": ["test selection"], "skip_tests": [],
                "stdout": "", "stderr": f"Cannot load exact unittest plan: {error}",
                "duration_seconds": time.perf_counter() - started}
    test_stdout, test_stderr, runner_output = io.StringIO(), io.StringIO(), io.StringIO()
    with redirect_stdout(test_stdout), redirect_stderr(test_stderr):
        result = unittest.TextTestRunner(stream=runner_output, verbosity=2).run(suite)
    failures = [test.id() for test, _ in result.failures]
    errors = [test.id() for test, _ in result.errors]
    skipped = [{"test": test.id(), "reason": reason} for test, reason in result.skipped]
    expected = len(result.expectedFailures)
    unexpected = [test.id() for test in result.unexpectedSuccesses]
    passed = max(0, result.testsRun - len(failures) - len(errors) - len(skipped) - expected - len(unexpected))
    return {
        "exit_code": 0 if result.wasSuccessful() else 1,
        "tests_run": result.testsRun, "passed": passed, "failures": len(failures),
        "errors": len(errors), "skipped": len(skipped), "expected_failures": expected,
        "unexpected_successes": len(unexpected), "failure_tests": failures,
        "error_tests": errors, "skip_tests": skipped, "unexpected_success_tests": unexpected,
        "stdout": test_stdout.getvalue(), "stderr": test_stderr.getvalue(),
        "runner_output": runner_output.getvalue(), "duration_seconds": time.perf_counter() - started,
    }


if __name__ == "__main__":
    protocol = sys.__stdout__
    try:
        report = run(json.load(sys.stdin))
    except BaseException as error:
        report = {"exit_code": 2, "tests_run": 0, "passed": 0, "failures": 0, "errors": 1,
                  "skipped": 0, "expected_failures": 0, "unexpected_successes": 0,
                  "failure_tests": [], "error_tests": ["worker startup"], "skip_tests": [],
                  "stdout": "", "stderr": f"Test worker error: {type(error).__name__}: {error}",
                  "duration_seconds": 0.0}
    protocol.write(json.dumps(report, sort_keys=True))
    protocol.flush()
    raise SystemExit(0)
