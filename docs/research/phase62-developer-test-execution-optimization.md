# Phase 62 - Developer test execution optimization

This phase adds developer-only test selection, execution diagnostics and a local
testing policy. It does not change test assertions, retrieval behavior, research
evaluation, benchmark data, Humanize artifacts or the frozen release.

## Baseline

The initial checkout was clean on `main`, at
`8a8e24f822a80f5efb450b1787315cac1a835380`, with origin
`https://github.com/chriltolakhmer-glitch/AI-Developer-Assistant.git`.
Local and remote `v0.1.1` tag object:
`05688504f74ad51230ee1566fad8cda0f1b1ad97`; peeled commit:
`51329285a882c1b7942d0a5b1c571e628d63dfb4`.

Phase 61's historical developer run contained 215 tests, zero skips/failures/errors,
and took 3919 seconds. Its full discovery ran 359 tests in 3965.040 seconds:
357 passed, two skipped, zero failures/errors. The prior report's phrase
"359 tests passed, 2 skipped" means 359 executed total, including the skips.
Both skips required unavailable `EMBEDDING_MODEL_CACHE`.
The historical developer suite itself took about 65 minutes; running the whole
developer module on every edit is therefore also too expensive for iteration.

Before implementation, all 11 `phase61` developer regression tests passed in
17.637 seconds, without skips/failures/errors. Historical full discovery was not
repeated for baseline collection. Current validation results are recorded below.

## Tiers and commands

| Tier | Scope | Invocation |
|---|---|---|
| T0 | Small configuration and runner unit tests; test syntax inventory and imports | `prototype local test` |
| T1 | Explicit method/class/module or affected component | `prototype local test --test tests.test_cli` |
| T2 | Complete developer workflow module | `prototype local test --component developer` or `--tier T2` |
| T3 | Affected expensive subsystem, including dependent workflow coverage | `prototype local test --component embedding` |
| T4 | Complete discovery, final gate only | `python -m unittest discover -s tests -v` |

The timing runner also supports `--tier T4 --final-gate`; it uses unittest
discovery with the same `test*.py` pattern and explicitly anchors imports at the
checkout root. T1 and T3 require a component/change/test selector rather than
selecting a generic broad suite. Explicit methods remain T1, or T3 for expensive
subsystems; choosing the complete developer module is T2.

```powershell
prototype local test --changed --dry-run
prototype local test --changed --base HEAD~1 --dry-run
prototype local test --component testing
prototype local test --test tests.test_developer_mode.DeveloperModeTests.test_phase61_relationships_require_file_identity
prototype local test-timing --test tests.test_config --report C:/Apps/test-evidence/config-timing.json
prototype local test-timing --component developer --report C:/Apps/test-evidence/developer-timing.json
prototype local test-timing --test tests.test_developer_mode.DeveloperModeTests.test_index_and_query_reuse_dense_bm25_and_are_repeatable --profile
```

Use `--test` repeatedly to combine explicit targets. Overlapping selectors are
deduplicated. Use `--dry-run` to inspect without importing or executing test
modules. Both commands emit complete JSON diagnostics (also accept `--json`);
unittest progress/tracebacks go to stderr. `test-timing` exposes the same timing
data as `test`, with the same safe default selection. `--profile` additionally
collects resource call counts and function durations; it adds measurement overhead.
There are no quality or productivity scores.

## Changed-file selection

`--changed` compares the entire working tree with HEAD and includes staged,
unstaged, deleted and untracked files. Renames include both endpoints. `--base`
compares with an explicitly resolved commit, including current worktree changes;
it is not an automatic merge-base comparison. A clean tree is reported explicitly.

The runner builds a static import graph from Python ASTs, including relative and
function-local imports, and follows reverse dependencies to complete test modules.
For example, changing `src/developer/context.py` includes developer workflows and
their CLI dependents without automatically selecting unrelated embedding tests.
Whole-module selection is intentionally conservative: this does not claim every
method in a module is cheap. Use an explicit method for initial feedback, then the
complete affected module(s), then T2 when developer behavior is affected.

The plan lists selected test identities, all intentionally unselected identities
and reasons, changed paths, diagnostics and required follow-up. Documentation-only
changes use T0. Unknown dependencies/files, deleted unmapped modules, or a source
file with no reachable test module produce an explicit T4 fallback. This fallback
is blocked from execution until `--final-gate` is supplied at the final gate; it
does not silently omit unknown coverage or accidentally start full discovery.
Git failures and invalid selectors return errors rather than an empty success.
Even a fully understood change is treated as T4 when its dependency graph selects
the complete test inventory; changing a root package initializer cannot bypass
the final-gate requirement.

Components include developer, testing, CLI, configuration, context, ranking,
governance, parser, repository, embedding, vector, BM25, retrieval and persistence.
`testing` is the runner/CLI/tracking component; developer CLI behavior also requires T2.
An explicit target is always partial validation, not proof that all dependencies
have been covered. Full discovery remains mandatory for the final gate.

## Timing and resource costs

Every execution uses a fresh Python subprocess with the current interpreter and
bytecode generation disabled. `TimingResult` observes standard unittest callbacks;
it preserves setup/cleanup, skips, errors, failures, expected failures, unexpected
successes and subtests. Reports include per-test category/duration, module/class
aggregates, fastest/slowest tests, imports/loading duration, total duration,
executed/passed/skipped/failure/error counts, tracebacks and reproduction commands.
Per-test times include instance fixtures and cleanup. Class/module fixtures and
import overhead are included in the total, not assigned to individual tests.

The optional cProfile report identifies model/embedding calls, index construction,
persistence, retrieval and repository/fixture calls, with counts, self time and
cumulative time. Repeated builds/loads are visible as call counts. Cumulative
times overlap and must not be added together. Mocked model paths do not measure
real model initialization or inference. Missing cache integrations remain explicit
environment limitations rather than invented timing measurements.

The two-test profiled sample (`resources-final.json`) exercised index/query reuse
and an unchanged index, with real local vector/BM25 structures and mocked
embeddings. It passed both tests. The following cumulative measurements overlap:

| Resource/function | Calls | Seconds |
|---|---:|---:|
| Developer index operation | 4 | 1.467 |
| Developer workspace query | 2 | 1.074 |
| Repository `setUp` | 2 | 0.445 |
| Git fixture commands | 10 | 0.437 |
| Developer index load | 4 | 0.083 |
| Index persistence (`_write_index`) | 2 | 0.061 |
| Vector construction (`_create`) | 4 | 0.0019 |
| BM25 construction (`_create`) | 4 | 0.0005 |
| Mock embedding fixture | 2 | 0.0003 |

There were no real model loads in this sample. Real model initialization/inference
cost is unmeasured because the approved cache is unavailable. No cache was fetched.
These are illustrative execution costs on this host, with profiling overhead and
a concurrent developer regression process, not comparative performance claims.

Tests with their own temporary repositories can be invoked independently using a
full dotted unittest identity. Governance and journal fixture tests may still be
expensive independently. Real-model integrations and unaffected model, persistence,
retrieval and repository subsystems remain outside routine T0/T1 validation; run
T3 when affected and include all existing tests at T4.

## Policy and failure reproduction

The root `AGENTS.md` makes this policy apply to future phases. Development follows:
targeted test -> affected component -> developer suite when necessary.
Final validation follows: targeted tests -> developer suite -> preservation checks
-> full suite once. Full discovery is never the normal development loop.

On failure, run the failing test independently, determine whether the current
change caused it, fix the underlying issue, rerun the target and affected suite,
and run T4 only after implementation is otherwise complete. Reports supply command
argument arrays so quoting does not change a test identity. Nothing automatically
reruns the suite, repairs state, converts errors to skips or suppresses failures.

## Environment, storage and limitations

Run from the source checkout using the pinned environment, here
`C:/Apps/.venv/Scripts/python.exe`. `python -B -m src.cli local test` is equivalent
to the entry point when the installed executable is unavailable. A packaged wheel
without the source test directory cannot run these repository tests. For minimal
environments, `python -B -m src.developer_testing --dry-run` avoids CLI imports.
Install the existing lock files for retrieval tests; do not install dependencies
or download models automatically. Real-model tests require the approved pinned
cache via `EMBEDDING_MODEL_CACHE`. Environment reports disclose missing packages,
cache availability, interpreter/platform and inherited offline settings. Missing
imports stay unittest errors; existing cache-dependent skips remain unchanged.
This environment did not contain `C:/Apps/.venv/Scripts/prototype.exe`; validation
therefore used the module invocation against the existing CLI entry-point function.
An isolated import-layout check launched from `tests/` failed with missing `src`;
rerunning the same module from the checkout root with discovery-style module names
passed all 26 tests in 11.870 seconds. This was a working-directory limitation,
not a full-suite failure or a reason to skip a test.

Reports are stdout-only unless `--report` names a new external file. Existing files
and paths resolving into the checkout are rejected before execution, including
symlink targets. No timing database, cache, workspace or research run is created.
Validation evidence for this phase is under `C:/Apps/phase62-validation`.
Eleven pre-existing Python/pytest cache directories were archived there under
`preexisting-caches`; the source checkout contains no new test reports or caches.

Static selection cannot prove dynamic imports, plugin loading, external services,
inherited/generated test cases or arbitrary non-Python dependencies. The current
suite uses explicit unittest methods; dynamic/custom `load_tests` suites should
be run by full discovery and require manual mapping review. Static inventories are
plans, while unittest's executed count is authoritative. No test parallelism,
fixture sharing, persistent model reuse, assertion changes or permanent skips are
introduced. Timing is machine/environment dependent and is not a benchmark claim.

## Validation results

Validation used Python 3.14.7 from `C:/Apps/.venv/Scripts/python.exe` on Windows
Server 2022, with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`. The approved
`EMBEDDING_MODEL_CACHE` was not configured; the two existing full-suite skips
below require that cache. No failures or errors occurred.

Development-loop checks:

- T0 final fast tier: 33 passed in 12.652 seconds; zero skips, failures or errors.
- T1 runner/CLI/testing component (`tests.test_developer_testing`,
  `tests.test_cli`, `tests.test_tracking`): 39 passed in 11.740 seconds; zero
  skips, failures or errors. This covers selection, CLI, changed-file and component
  mapping, timing, and report behavior.
- T1 timing/report smoke check (`tests.test_config`): 7 passed in 0.053 seconds;
  no skips, failures or errors. The report was written outside the checkout.
- The current `--changed --dry-run` plan selected 254 tests across four modules
  from the six Phase 62 worktree paths (131 tests were explicitly listed as
  outside that selection); final discovery was still required. Earlier targeted
  validations and edge-case additions are retained in the external validation
  directory, not in the source tree.
- T3 was not run: no expensive subsystem was changed or selected as affected.

Required developer regression:

- `prototype local test-timing --component developer` selected and ran the
  complete `tests.test_developer_mode` module in a fresh worker process: 215 run,
  215 passed, zero skips, failures or errors; 4489.695 seconds (74 minutes 50
  seconds wall time). This was the existing instrumented developer-suite run,
  not a second rerun of the module.
- The slowest developer tests were operational-readiness drift/expiry (1352.970
  seconds), complete-chain closure/history (1167.423 seconds), CLI/manual
  outstanding items (353.810 seconds), missing/orphaned links (339.863 seconds),
  and incomplete-chain transitions/follow-up (123.020 seconds).

Final full regression:

- `python -m unittest discover -s tests -v`: 385 run in 3986.838 seconds
  (66 minutes 27 seconds unittest time; 3988.472 seconds process wall time):
  383 passed, two skipped, zero failures or errors.
- The skips were `tests.test_embedding.EmbeddingTests.test_real_model_offline_repeatability`
  and `tests.test_rrf.HybridSearchTests.test_real_embedding_to_persisted_indexes_to_text_query_offline`;
  both require the unavailable approved `EMBEDDING_MODEL_CACHE`. The tests were
  not changed or disabled.
- The slowest full-suite tests were complete-chain closure/history (1072.698
  seconds), drift/expiry compatibility (971.297 seconds), CLI/manual outstanding
  items (350.675 seconds), missing/orphaned links (340.279 seconds), and
  incomplete-chain transitions/follow-up (128.153 seconds).
- The historical full-suite baseline was 359 tests in 3965.040 seconds
  (357 passed, two skipped). The current run contains 26 additional tests and is
  not directly comparable as a performance measurement; no speedup is claimed.

Preservation checks:

- `git diff --check` and the staged diff whitespace check passed. The only
  changed paths are the six intended Phase 62 files; no generated logs, reports,
  bytecode, or caches were added to the checkout.
- `v0.1.1` tag object and peeled commit remain
  `05688504f74ad51230ee1566fad8cda0f1b1ad97` and
  `51329285a882c1b7942d0a5b1c571e628d63dfb4`. `VERSION`,
	`release-manifest.json`, benchmark/Humanize artifacts, and research evaluation
	and retrieval paths have no changes in the Phase 62 diff.
- The full discovery gate passed, including the existing research and retrieval
  tests. Static changed-file analysis cannot prove coverage of dynamic imports,
  plugins, external services, or non-Python dependencies; full discovery remains
  the final gate.
