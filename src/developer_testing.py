"""Developer-only unittest selection and diagnostics; never changes test policy at runtime.

Kept outside src.developer so planning does not import the retrieval environment.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import cProfile
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = "tests.test_developer_mode"
FAST = ("tests.test_config", "tests.test_developer_testing")
EXPENSIVE = ("embedding", "vector_retrieval", "bm25_retrieval", "hybrid_search",
             "parent_child_retrieval", "pipeline_validation", "repository_scanner", "rrf")
TIERS = {"T0": "Fast validation", "T1": "Changed component", "T2": "Developer workflow",
         "T3": "Affected expensive subsystem", "T4": "Final full regression gate"}
COMPONENTS = {
    "developer": (DEVELOPER,),
    "testing": ("tests.test_developer_testing", "tests.test_cli", "tests.test_tracking"),
    "cli": ("tests.test_cli", "tests.test_developer_testing", DEVELOPER),
    "configuration": ("tests.test_config", "tests.test_cli", DEVELOPER),
    "context": (DEVELOPER,), "ranking": (DEVELOPER, "tests.test_rrf"),
    "governance": (DEVELOPER,),
    "embedding": ("tests.test_embedding", "tests.test_parent_child_retrieval", DEVELOPER),
    "vector": ("tests.test_vector_retrieval", "tests.test_hybrid_search",
               "tests.test_parent_child_retrieval", DEVELOPER),
    "bm25": ("tests.test_bm25_retrieval", "tests.test_hybrid_search",
             "tests.test_parent_child_retrieval", DEVELOPER),
    "retrieval": tuple("tests.test_" + name for name in EXPENSIVE[:5]) + ("tests.test_rrf", DEVELOPER),
    "persistence": ("tests.test_embedding", "tests.test_vector_retrieval",
                    "tests.test_bm25_retrieval", "tests.test_tracking", DEVELOPER),
    "parser": ("tests.test_ast_parser", "tests.test_chunker", DEVELOPER),
    "repository": ("tests.test_repository_scanner", "tests.test_pipeline_validation", DEVELOPER),
}
COMPONENT_SOURCES = {
    "cli": ("src.cli",), "configuration": ("src.config", "src.developer.configuration"),
    "context": ("src.developer.context",), "ranking": ("src.developer.ranking",),
    "governance": ("src.developer.governance", "src.developer.governance_operations",
                   "src.developer.strategic_governance", "src.developer.recovery_governance"),
    "embedding": ("src.embedding",), "vector": ("src.retrieval.vector_index",),
    "bm25": ("src.retrieval.bm25_index", "src.retrieval.bm25_search"),
    "retrieval": ("src.retrieval",), "parser": ("src.parser", "src.chunker"),
    "repository": ("src.scanner",),
    "persistence": ("src.embedding.storage", "src.retrieval.vector_index",
                    "src.retrieval.bm25_index", "src.tracking"),
}


def _dependents(seeds: set[str], graph: dict[str, set[str]]) -> set[str]:
    affected = set(seeds)
    while True:
        expanded = affected | {module for module, imports in graph.items() if imports & affected}
        if expanded == affected:
            return affected
        affected = expanded


def catalog(root: Path = ROOT) -> dict[str, list[str]]:
    """Read test identities without importing modules or initializing resources."""
    result = {}
    for path in sorted((root / "tests").rglob("test*.py")):
        module = ".".join(path.relative_to(root).with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        result[module] = [f"{module}.{cls.name}.{method.name}"
                          for cls in tree.body if isinstance(cls, ast.ClassDef)
                          for method in cls.body if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and method.name.startswith("test")]
    return result


def changed_files(root: Path = ROOT, base: str | None = None) -> list[str]:
    """Include staged, unstaged, deleted, rename endpoints and untracked paths."""
    def git(*args):
        try:
            result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)
        except (OSError, subprocess.CalledProcessError) as error:
            raise ValueError("Cannot inspect Git changes; use --component or --test, or fix the Git/base reference.") from error
        return result.stdout.decode("utf-8", errors="surrogateescape")
    revision = "HEAD"
    if base:
        revision = git("rev-parse", "--verify", "--end-of-options", base + "^{commit}").strip()
    paths = git("diff", "--name-only", "--no-renames", "-z", revision, "--").split("\0")
    paths += git("ls-files", "--others", "--exclude-standard", "-z").split("\0")
    return sorted(set(filter(None, paths)))


def _dependencies(root: Path) -> dict[str, set[str]]:
    graph = {}
    for folder in ("src", "tests"):
        for path in (root / folder).rglob("*.py"):
            parts = path.relative_to(root).with_suffix("").parts
            module = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
            package = module if parts[-1] == "__init__" else module.rpartition(".")[0]
            imports = set()
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    prefix = node.module or ""
                    if node.level:
                        prefix = ".".join(package.split(".")[:len(package.split(".")) - node.level + 1]
                                          + ([prefix] if prefix else []))
                    imports.add(prefix)
                    imports.update(prefix + "." + alias.name for alias in node.names)
            # Importing a submodule also executes its package initializers.
            imports.update(".".join(module.split(".")[:index]) for index in range(1, len(module.split("."))))
            for dependency in tuple(imports):
                if dependency.startswith(("src.", "tests.")):
                    imports.update(".".join(dependency.split(".")[:index])
                                   for index in range(1, len(dependency.split("."))))
            graph[module] = imports
    return graph


def plan(*, root: Path = ROOT, changed=False, base=None, component=None,
         tests=(), tier=None, final_gate=False) -> dict:
    inventory = catalog(root)
    all_tests = {name for names in inventory.values() for name in names}
    diagnostics, files, selected_modules = [], [], set()
    uncertain = False
    if sum((bool(changed), bool(component), bool(tests), bool(tier))) > 1:
        raise ValueError("Choose one of --changed, --component, --test, or --tier.")
    if base and not changed:
        raise ValueError("--base requires --changed.")
    if tests:
        selected = set()
        for name in tests:
            matches = {item for item in all_tests if item == name or item.startswith(name + ".")}
            if not name.startswith("tests.test") or not matches:
                raise ValueError(f"Unknown test selector: {name}")
            selected.update(matches)
        selected_modules = {name for name in inventory if any(t.startswith(name + ".") for t in selected)}
        selected_tier = "T1"
    else:
        if changed:
            files = changed_files(root, base)
            graph = _dependencies(root)
            affected = set()
            for file in files:
                path = Path(file)
                if file.startswith("docs/") or file in {"README.md", "AGENTS.md"}:
                    diagnostics.append(f"Documentation-only: {file}; final gate still required.")
                    continue
                if path.suffix == ".py" and path.parts[0] in {"src", "tests"}:
                    parts = path.with_suffix("").parts
                    affected.add(".".join(parts[:-1] if parts[-1] == "__init__" else parts))
                else:
                    uncertain = True
                    diagnostics.append(f"Unmapped change: {file}; broader T4 required.")
            seeds = set(affected)
            for seed in seeds:
                reachable = _dependents({seed}, graph)
                affected.update(reachable)
                if not (set(inventory) & reachable):
                    uncertain = True
                    diagnostics.append(f"No test dependency path for {seed}; broader T4 required.")
            selected_modules = set(inventory) & affected
            if affected and not selected_modules:
                uncertain = True
                diagnostics.append("No test dependency path found; broader T4 required.")
            if not files:
                diagnostics.append("No worktree changes; comparing with HEAD. Use --base for committed changes.")
            if uncertain:
                selected_modules = set(inventory)
            elif not selected_modules:
                selected_modules = set(FAST) & set(inventory)
            diagnostics.append("Static imports include transitive and function-local dependencies. Dynamic imports and non-Python dependencies require manual review.")
        elif component:
            if component not in COMPONENTS:
                raise ValueError(f"Unknown component: {component}")
            selected_modules = set(COMPONENTS[component])
            if component in COMPONENT_SOURCES:
                graph = _dependencies(root)
                seeds = {module for module in graph if any(module == prefix or module.startswith(prefix + ".")
                         for prefix in COMPONENT_SOURCES[component])}
                selected_modules.update(set(inventory) & _dependents(seeds, graph))
                diagnostics.append("Component selection includes transitive source-import dependents.")
        elif tier:
            if tier == "T0":
                selected_modules = set(FAST)
            elif tier == "T2":
                selected_modules = {DEVELOPER}
            elif tier == "T4":
                selected_modules = set(inventory)
            else:
                raise ValueError("T1/T3 require --component, --changed, or explicit --test selectors.")
        else:
            selected_modules = set(FAST)
        if selected_modules - set(inventory):
            raise ValueError(f"Missing test modules: {sorted(selected_modules - set(inventory))}")
        selected = {test for module in selected_modules for test in inventory[module]}
        selected_tier = ("T4" if uncertain or tier == "T4" else "T3" if any(
            module.removeprefix("tests.test_") in EXPENSIVE for module in selected_modules)
            else "T2" if DEVELOPER in selected_modules else "T0" if not component and not changed else "T1")
    if tests and any(module.removeprefix("tests.test_") in EXPENSIVE for module in selected_modules):
        selected_tier = "T3"
    if tests and DEVELOPER in tests and selected_tier != "T3":
        selected_tier = "T2"
    if selected == all_tests:
        selected_tier = "T4"
        diagnostics.append("Selection covers the complete test inventory; execution is a final gate even when every dependency is known.")
    if final_gate and selected_tier != "T4":
        raise ValueError("--final-gate is only valid for a T4 selection.")
    return {"tier": selected_tier, "tier_description": TIERS[selected_tier],
            "changed_files": files, "selected_tests": sorted(selected),
            "selectors": sorted(selected_modules) if not tests else sorted(
                name for name in set(tests) if not any(name.startswith(other + ".") for other in tests if other != name)),
            "not_selected": [{"test": name, "reason": "Outside this selection; remains covered by the final full gate."}
                             for name in sorted(all_tests - selected)],
            "diagnostics": diagnostics, "uncertain": uncertain,
            "execution_blocked": selected_tier == "T4" and not final_gate,
            "required_followup": ["T2 developer suite", "T4 final gate"]
            if (tests and DEVELOPER in selected_modules and DEVELOPER not in tests) or component == "testing"
            else ([] if selected_tier == "T4" else ["T4 final gate"])}


def category(name: str) -> str:
    if "test_developer_mode" in name:
        return "developer workflow / repository and journal fixtures"
    for token in EXPENSIVE:
        if "test_" + token in name:
            return token
    return "unit / CLI"


def test_identity(test) -> str:
    name = test.id()
    if name.startswith("test_"):
        name = "tests." + name
    return name


def reproduction_selector(test) -> str:
    name = test_identity(test)
    if isinstance(test, unittest.loader._FailedTest):
        return test._testMethodName
    if name.startswith(("setUpClass (", "tearDownClass (", "setUpModule (", "tearDownModule (")):
        name = name.partition("(")[2].removesuffix(")")
        return "tests." + name if name.startswith("test_") else name
    return name.split(" (")[0]


class TimingResult(unittest.TextTestResult):
    """Observe standard unittest callbacks, preserving skips, failures and errors."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timings = []
        self._started = {}

    def startTest(self, test):
        self._started[id(test)] = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        self.timings.append({"test": test_identity(test), "seconds": time.perf_counter() - self._started.pop(id(test)),
                             "category": category(test_identity(test))})
        super().stopTest(test)


def environment() -> dict:
    missing = [name for name in ("yaml", "numpy", "faiss", "torch", "sentence_transformers")
               if importlib.util.find_spec(name) is None]
    cache = os.environ.get("EMBEDDING_MODEL_CACHE")
    return {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
            "missing_dependencies": missing, "embedding_model_cache_configured": bool(cache),
            "limitations": (["EMBEDDING_MODEL_CACHE is unavailable; existing real-model integration tests may skip."]
                            if not cache or not Path(cache).is_dir() else []),
            "offline": {key: os.environ.get(key) for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}}


def summarize(result, seconds: float, load_seconds: float = 0.0) -> dict:
    groups = {"modules": {}, "classes": {}}
    for row in result.timings:
        for label, length in (("modules", 2), ("classes", 3)):
            key = ".".join(row["test"].split(".")[:length])
            group = groups[label].setdefault(key, {"seconds": 0.0, "tests": 0})
            group["seconds"] += row["seconds"]
            group["tests"] += 1
    failures = [{"test": test_identity(t), "traceback": detail} for t, detail in result.failures]
    errors = [{"test": test_identity(t), "traceback": detail} for t, detail in result.errors]
    failed_ids = {row["test"].split(" (")[0] for row in failures + errors}
    return {"total_tests": result.testsRun,
            "passed": sum(1 for row in result.timings if row["test"] not in failed_ids
                          and row["test"] not in {test_identity(t).split(" (")[0] for t, _ in result.skipped + result.expectedFailures}
                          and row["test"] not in {test_identity(t) for t in result.unexpectedSuccesses}),
            "skipped": [{"test": test_identity(t), "reason": reason} for t, reason in result.skipped],
            "failures": failures, "errors": errors,
            "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses),
            "total_seconds": seconds, "load_seconds": load_seconds, "tests": result.timings,
            "slow_tests": sorted(result.timings, key=lambda r: r["seconds"], reverse=True)[:10],
            "fast_tests": sorted(result.timings, key=lambda r: r["seconds"])[:10], **groups,
            "reproduce": [[sys.executable, "-B", "-m", "unittest", name, "-v"] for name in sorted(
                {reproduction_selector(t) for t, _ in result.failures + result.errors}
                | {reproduction_selector(t) for t in result.unexpectedSuccesses})],
            "environment": environment(), "exit_code": 0 if result.wasSuccessful() else 1}


def _resource_profile(profiler) -> list[dict]:
    import pstats
    rows = []
    for (file, line, name), (primitive, calls, own, cumulative, _) in pstats.Stats(profiler).stats.items():
        normalized = file.replace("\\", "/")
        kind = None
        if name in {"setUp", "tearDown", "cleanup_temporary_repository", "git"} and "/tests/" in normalized:
            kind = "filesystem/repository fixture"
        elif name == "_embedding_stub" and "/tests/" in normalized:
            kind = "mock embedding fixture (not model inference)"
        elif name in {"load_model", "encode", "embed_chunks", "_embed_chunks", "_embed_developer_chunks"} and any(
                part in normalized for part in ("/embedding/", "/developer/", "/sentence_transformers/")):
            kind = "model initialization / embedding"
        elif "/retrieval/" in normalized or "/developer/" in normalized:
            if name in {"build", "_create", "_write_index", "index", "save", "load", "query", "search"}:
                kind = "retrieval" if name in {"query", "search"} else "index construction / persistence"
        if kind:
            rows.append({"function": f"{file}:{line}:{name}", "category": kind,
                         "calls": calls, "self_seconds": own, "cumulative_seconds": cumulative})
    return sorted(rows, key=lambda row: row["cumulative_seconds"], reverse=True)


def worker(request: dict) -> dict:
    started = time.perf_counter()
    profiler = cProfile.Profile() if request.get("profile") else None
    if profiler:
        profiler.enable()
    with contextlib.redirect_stdout(sys.stderr):
        loader = unittest.TestLoader()
        suite = (loader.discover("tests", pattern="test*.py", top_level_dir=".") if request["tier"] == "T4"
                 else loader.loadTestsFromNames(request["selectors"]))
        load_seconds = time.perf_counter() - started
        result = unittest.TextTestRunner(verbosity=2, resultclass=TimingResult).run(suite)
    if profiler:
        profiler.disable()
    report = summarize(result, time.perf_counter() - started, load_seconds)
    if not result.testsRun and not result.errors and not result.skipped:
        report.update(exit_code=2, message="No tests executed; this is not a successful validation.")
    report["resource_profile"] = _resource_profile(profiler) if profiler else []
    report["profile_enabled"] = bool(profiler)
    report["timing_scope"] = "Per test includes setUp, tearDown and cleanup. Total also includes imports and class/module fixtures. Profile cumulative times overlap."
    return report


def execute(selection: dict, *, profile=False, root: Path = ROOT) -> dict:
    if selection["execution_blocked"]:
        return {**selection, "exit_code": 2, "executed": False,
                "message": "T4 fallback is planned, not executed. Complete focused validation, then use --final-gate at the final gate."}
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run([sys.executable, "-B", "-m", "src.developer_testing", "--worker"],
                               input=json.dumps({**selection, "profile": profile}), text=True,
                               stdout=subprocess.PIPE, cwd=root, env=env, check=False)
    try:
        report = json.loads(completed.stdout)
    except (ValueError, TypeError):
        return {**selection, "exit_code": completed.returncode or 2, "executed": False,
                "environment": environment(), "message": "Test worker did not produce a complete report; inspect stderr. This is not a pass."}
    return {**selection, **report, "executed": True, "exit_code": completed.returncode or report["exit_code"]}


def add_arguments(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--changed", action="store_true", help="Select tests through the source import graph.")
    group.add_argument("--component", choices=sorted(COMPONENTS))
    group.add_argument("--test", action="append", default=[], help="Dotted module, class, or method; repeatable.")
    group.add_argument("--tier", choices=TIERS)
    parser.add_argument("--base", help="Compare all changes with this commit, including worktree changes.")
    parser.add_argument("--final-gate", action="store_true", help="Explicitly execute a T4 selection.")
    parser.add_argument("--dry-run", action="store_true", help="Print selection without importing or running tests.")
    parser.add_argument("--profile", action="store_true", help="Measure resource call counts/times with cProfile (adds overhead).")
    parser.add_argument("--report", type=Path, help="New JSON report file outside the source checkout.")
    parser.add_argument("--json", action="store_true")


def run_command(options) -> int:
    report_path = options.report.resolve() if options.report else None
    if report_path and (report_path == ROOT or ROOT in report_path.parents or report_path.exists()):
        raise ValueError("--report must be a new file outside the source checkout.")
    try:
        selection = plan(changed=options.changed, base=options.base, component=options.component,
                         tests=options.test, tier=options.tier, final_gate=options.final_gate)
    except SyntaxError as error:
        raise ValueError(f"Cannot inventory tests/source with invalid syntax: {error}") from error
    print(f"{selection['tier']}: {len(selection['selected_tests'])} selected; {len(selection['not_selected'])} intentionally not selected.", file=sys.stderr)
    payload = ({**selection, "executed": False, "exit_code": 0} if options.dry_run
               else execute(selection, profile=options.profile))
    payload["notice"] = "Developer test execution diagnostic; not a benchmark or productivity score."
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2)
    # Both commands always expose complete selection, omissions, and results.
    print(json.dumps(payload, indent=2))
    return payload["exit_code"]


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        payload = worker(json.load(sys.stdin))
        print(json.dumps(payload))
        raise SystemExit(payload["exit_code"])
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    try:
        raise SystemExit(run_command(parser.parse_args()))
    except (OSError, ValueError, SyntaxError) as error:
        parser.exit(2, f"developer testing: {error}\n")
