# Test-Gating Architecture Redesign

## Problem

The prior completion sequence ran affected tests, the complete developer suite
(T2), and then full discovery (T4). T2 selects `tests.test_developer_mode`, and
T4 discovery includes that module. When both gates are required, T2 repeats test
execution already contained in T4. The separate T2 run still helps diagnose and
localize a failure before an exhaustive run, and remains useful when developer
workflow coverage is itself the completion gate. It adds no independent test
coverage when full discovery follows.

## Historical evidence

Phase 67 recorded 216 developer-mode tests in 3,195.92 seconds and full discovery
of 414 tests in 3,283.265 seconds. The two workloads overlap in the full developer
module. Phase 63 recorded 216 T2 tests in 3,182.077 seconds and 386 T4 tests in
3,336.060 seconds. Phase 62 recorded 215 T2 tests in 4,489.695 seconds and 385
T4 tests in 3,986.838 seconds. Historical measurements are retained as evidence;
they were not rerun for this redesign and are not a controlled performance
benchmark. An avoided second run saves its actual elapsed time, but no percentage
or guaranteed wall-clock saving is claimed.

## Existing architecture

`src/developer_testing.py` catalogs unittest method identities from test files,
builds a static AST import graph for `src` and `tests`, and traverses reverse
dependencies. It includes relative and function-local imports and package
initializer execution. Changed-file discovery includes staged and unstaged
changes, untracked paths, deletions and rename endpoints. Explicit overlapping
selectors are deduplicated before suite loading. T4 uses unittest discovery and
the catalog/discovery inventory regression test detects disagreement.

The mapping is module-level. A dependency on one function in a test module selects
the whole module. For example, the Phase 67 patch-drafting path currently reaches
CLI and developer modules through static imports, so its phase gate selects 295
tests including the developer suite's lifecycle cases. This is conservative and
can retain expensive unrelated cases. It does not establish that every selected
method is materially affected. Method-level pruning is not introduced because
the current AST graph cannot prove safety of such pruning.

## Duplication analysis

The full developer suite is wholly included in full discovery. If T4 is required,
run it once. Its per-test results, tracebacks and module/class aggregates provide
diagnostics without running T2 separately. Run T2 on its own for iterative
developer feedback, failure localization, affected developer workflows, or a
high-risk developer change whose prescribed gate is T2 and for which exhaustive
acceptance is not required.

## Alternatives considered

| Option | Feedback and confidence | Diagnostics | Mapping risk and maintenance | Decision |
| --- | --- | --- | --- | --- |
| A. Affected, T2, then T4 | Broadest sequence; repeats every T2 test in T4 | Strong early isolation | Simple, high repeat cost | Rejected as routine policy; use T2 during diagnosis when useful |
| B. Affected, then T4 | Exhaustive confidence | Full-run failure output | Still pays full inventory cost | Retained for exhaustive acceptance, not every phase |
| C. Risk-based mapped phase gate | Good routine scope if selection is complete | Affected module results | Static/dynamic dependency risk; deterministic escalation required | Used with fail-upward rules |
| D. Standard phase gate plus exhaustive suite | Distinguishes routine completion from release/milestone assurance | One authoritative run per gate | Two clear policies to maintain | Chosen policy model |
| E. Validated lifecycle snapshots | May reduce setup in tests | Keeps separate executions | Fixture integrity and migration complexity; Phase 63 already reuses validated seeds for several scenarios | No new fixture optimization in this work |

## Decision

Implement named `development`, `phase`, and `exhaustive` gates without renaming
T0-T4. Development feedback stays targeted. The phase gate runs the changed-file
dependents plus fast safety modules and can finish without exhaustive discovery
when mapping is known and the selection is smaller than the inventory. A single
planned session must not run the same test twice. Exhaustive acceptance runs the
full discovered inventory. If the phase gate escalates to full discovery, that
same execution serves as exhaustive acceptance.

## Validation profiles / gate semantics

- `prototype local test --test tests.MODULE.CLASS.METHOD` selects a focused
  method. Existing `--component`, `--changed`, and T0-T4 selectors remain.
- `prototype local test --gate development` uses the changed-file selector as
  development feedback; `--changed --dry-run` shows selection without running.
- `prototype local test --gate phase` plans from the whole working tree, selects
  changed-file-dependent modules, and adds available fast safety modules. An
  explicitly uncertain or high-risk plan selects all tests and runs exhaustive
  discovery once.
- `prototype local test --gate exhaustive` explicitly runs unittest discovery.
  The direct `python -m unittest discover -s tests -v` command remains supported.

Plans expose changed files, selected test identities, component/module, known
cost class, selection reason, uncertainty, escalation reasons, exhaustive
requirement, mandatory follow-up and intentionally unselected identities. Actual
reports retain per-test timing and module/class aggregate timing. Cost classes
are scheduling metadata only: `fast_unit`, `normal_integration`,
`expensive_integration`, `exhaustive_lifecycle`, and `environment_dependent`.
The known slow readiness-chain methods are labeled exhaustive lifecycle; the two
real-model cases that may skip without `EMBEDDING_MODEL_CACHE` are labeled
environment-dependent. No class label lowers a test's importance or removes it
from discovery.

The single full run's per-test, module and class reports are sufficient for
diagnosis. The redesign does not emit overlapping synthetic subset pass counts
for developer, governance and patch-drafting groups: those subsets overlap, and
their totals could be mistaken for separately executed suites. The selected plan
does preserve each test's component and cost metadata alongside the one result.

## Risk escalation rules

The phase gate deterministically requires exhaustive discovery for:

- test selection/runner or CLI testing infrastructure changes;
- `src` package initializers;
- governance, readiness, reliability, journal/storage, repository identity,
  shared configuration, serialization or integrity source paths;
- changed Python files using `__import__`, `importlib.import_module`, `exec`,
  `eval`, or a custom `load_tests` hook;
- a change touching three or more distinct `src` package roots;
- unknown, deleted/unmapped, non-Python or unsupported dependencies, no mapped
  test path, or a selection that already covers the full test inventory;
- a release or milestone policy, or an explicit request for exhaustive acceptance.

External release/milestone status and explicit acceptance requests are policy
inputs and are honored by selecting the exhaustive gate; the selector does not
infer them from a vague risk score. Uncertainty escalates to broader coverage;
it never reduces selected tests. Test-runner and mapping changes are themselves
high risk, so this redesign's own phase gate is exhaustive.

## Changed-file selection

Static mapping is authoritative only for statically visible Python imports and
the repository's checked-in test modules. Relative and function-local imports,
transitive reverse dependencies and package initialization are included. The
planner reports the full selected inventory and preserves exclusions with a
reason.

The mapping cannot establish dependencies created by dynamic imports not found
in changed files, plugins, generated tests, external services, configuration
files, environment variables, arbitrary data files or runtime dispatch. Changed
non-Python inputs and unsupported mappings therefore escalate. A clean working
tree maps to no changed paths; use explicit test/component selectors for feedback
or `--base` when committed changes must be included. The selector does not claim
that AST reachability proves runtime behavior.

## Expensive test scheduling

Known exhaustive lifecycle cases include readiness complete-chain/history,
incomplete transition/follow-up, drift/expiry compatibility, missing/orphaned
links, and CLI/manual outstanding items. These tests remain ordinary discoverable
tests. Governance, readiness, journal and reliability source changes escalate to
exhaustive acceptance. Other well-mapped features run selected dependent modules;
module-level selection may still include lifecycle tests due shared imports.
Phase 63's validated seed reuse remains in place; this redesign adds no fixture
snapshots and changes no assertion, expected outcome or skip policy.

## Deduplication

Unittest suite loading receives each selected module once, and explicit selector
overlap is collapsed. During exhaustive acceptance, no standalone T2 is run in
the same planned session. If exhaustive execution is required, its inclusion of
T2 is sufficient. A developer suite run may precede exhaustive discovery only
for a concrete failure-localization or reproduction reason; report that as a
separate diagnostic session, not as routine completion coverage.

## Exhaustive acceptance

Full discovery remains easy to invoke and discovers newly added `test*.py`
modules automatically. The deterministic integrity test compares unittest
discovery's test-case count with the static catalog. The complete inventory,
expensive governance/readiness scenarios and existing environment-dependent skips
are preserved. No permanent skip or test exclusion was added.

## Coverage preservation

Focused tests cover phase selection, safety tests, high-risk escalation,
dynamic-loading uncertainty, explicit exhaustive execution, selector deduplication,
known lifecycle cost labels and discovery/catalog inventory equality. Unknown
mapping falls upward. Plan diagnostics expose the selected and unselected tests;
unittest execution counts and terminal status remain authoritative.

## Validation evidence

Pre-change baseline: clean `main` at
`12b6f86a05f882d5625224ad2ab328173d14c9ba`.

- Focused runner and CLI tests: 42 run in 14.814 seconds; `OK`, zero failures,
  errors or skips; process exit 0.
- Phase-gate dry run against the redesign's five changed paths: uncertain due to
  test-runner/CLI mapping changes, deterministic escalation to T4, 421 selected,
  zero intentionally unselected.
- Executed phase gate and exhaustive acceptance were the same invocation: 421
  run, 419 passed, two existing environment-dependent skips, zero failures/errors;
  unittest duration 3,289.658 seconds, process exit 0, terminal `OK (skipped=2)`.
  The skipped tests were `test_real_model_offline_repeatability` and
  `test_real_embedding_to_persisted_indexes_to_text_query_offline`; both require
  the unavailable `EMBEDDING_MODEL_CACHE`. No T2 suite was run separately.
- The full JSON report and terminal log are outside the checkout at
  `C:/Apps/test-gating-validation/phase-gate-result-final.json` and
  `C:/Apps/test-gating-validation/phase-gate-run-final.log`.

Historical Phase 62/63 measurements were not rerun. Protected-path hashes, tag
identity, final diff and Git synchronization are checked separately at task close.

## Limitations

The import graph selects whole test modules, so some known or unrelated slow
methods can enter an affected selection. False-negative risk remains for dynamic
behavior that cannot be recognized from changed files; explicit risk rules and
manual review are required. No exact runtime target is promised. Cost classes
identify known scheduling groups and do not substitute for observed run results.

## Phase 68 implications

This is test architecture only and is not Phase 68. It does not implement
authorization, approval, execution, patch application or any later feature.
Phase 68 eligibility is assessed only after deterministic escalation coverage,
preserved discovery inventory and this redesign's exhaustive acceptance have
passed.
