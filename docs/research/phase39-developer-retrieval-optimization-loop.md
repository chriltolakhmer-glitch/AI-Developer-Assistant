# Phase 39 — Developer Retrieval Optimization Loop

This phase adds developer-only experiment tracking and validation. Retrieval code,
research evaluation and methodology, benchmark datasets, Humanize artifacts and frozen
release artifacts remain unchanged. No quality score or benchmark improvement is claimed.
Developer repositories are never added to research snapshots. Commands do not edit
retrieval behavior, apply patches, update baselines, or roll back code.

## Baseline and inputs

The checkout retains existing Phase 27–38 work. The starting Phase 38 focused suite
passed 42 tests, with zero skips, failures or errors. The `v0.1.1` tag object is
`05688504f74ad51230ee1566fad8cda0f1b1ad97`, pointing to commit
`51329285a882c1b7942d0a5b1c571e628d63dfb4`.

Existing inputs include retrieval event records, `inspect-history`, `timeline`,
repeated failure patterns, regression history, context analysis, ranking explanations,
and repeat-run stability. Repeated missing symbols, missing dependencies, undeclared
context, unstable ranking, unsupported file types and stale-index diagnostics are
investigation inputs, not proof of a retrieval defect. `optimize` lists existing
candidates and the Phase 38 repeated patterns as suggestions; creation is explicit.

## Workflow

All examples use the same external developer workspace as the index and regression
history. `EVENT_ID` is an exact retrieval/regression event ID from `inspect-history`.
For regression observations it has the form `HISTORY_ID:CASE_ID`.

```text
prototype local inspect-history --workspace EXTERNAL_WORKSPACE --json
prototype local optimize --workspace EXTERNAL_WORKSPACE --json
prototype local optimize create --id dependency-gap --problem "Repeated missing dependency" --case auth-flow --source EVENT_ID --proposed-change "Review bounded dependency expansion" --validation-method "Run unchanged regression cases and compatibility gates" --workspace EXTERNAL_WORKSPACE --json
prototype local optimize show --id dependency-gap --workspace EXTERNAL_WORKSPACE --json
```

Repeat `--case` and `--source` for multiple cases/events. Evidence must exist, cover
every affected case and belong to exactly one developer repository. The candidate
records the problem, cases, evidence IDs, proposed change, validation method, status
and result. Query hash IDs are allowed, but validating them requires a baseline whose
case IDs include those IDs; regression case IDs are usually easier to reuse.

Investigate with `local trace`, `local diagnose` and `local analyze-context`. Apply a
targeted change manually and reindex if repository source changes. Keep the original
case definitions and baseline intact. Then run:

```text
prototype local optimize validate --id dependency-gap --repository REPOSITORY --cases CASES.json --before original-baseline --workspace EXTERNAL_WORKSPACE --json
prototype local compare --before original-baseline --after HISTORY_ID --workspace EXTERNAL_WORKSPACE --json
prototype local optimize accept --id dependency-gap --note "Reviewed evidence and all gates passed" --workspace EXTERNAL_WORKSPACE --json
```

If a ranking change is intentional, investigate it and rerun validation with
`--ranking-note "auth-flow=Explanation of the reviewed ranking change"`. Repeat this
option for each changed case. Notes are human assertions, not automatically verified
causal explanations. A note cannot override missing evidence, instability, removed
explanations, duplicate context or compatibility failures.

Reject an experiment with:

```text
prototype local optimize reject --id dependency-gap --note "Required evidence was lost" --workspace EXTERNAL_WORKSPACE --json
```

Rejection can happen before validation. Revert any applied code change manually.

## Lifecycle and storage

Records use `developer-optimization-v1`, mode `developer-local-optimization`, under:

```text
DEVELOPER_WORKSPACE/optimization/candidates/ID/candidate.json
DEVELOPER_WORKSPACE/optimization/candidates/ID/validations/UUID.json
DEVELOPER_WORKSPACE/optimization/candidates/ID/decision.json
```

Files are created exclusively and never overwritten by the workflow. The displayed
lifecycle is `candidate` → `validated` → `accepted` or `rejected`. Validation includes
`passed` and individual gate booleans; `validated` alone does not mean passing. Multiple
validations are retained, and acceptance uses the latest one. Final decisions cannot
be rewritten; further experiments require a new candidate ID. Acceptance records a
review of the specific saved experiment, not approval of later code changes.

Workspace containment checks reject checkout/research overlap and paths redirected
outside the workspace. Only fixed developer observability, regression and optimization
namespaces are read. No benchmark optimization records, Humanize changes or research
findings are created. Metadata and free-text notes remain local; users should keep
their content within this developer-only scope.

## Comparison semantics

`local compare --before VERSION --after VERSION` reads saved developer versions.
A version is an immutable baseline name or a regression history UUID, not a Git tag
or release version. Ambiguous or missing versions fail. Pass `--repository-id ID`
when multiple repositories have regression history. A live validation's `--before`
must be a named baseline. The original `local compare QUERY` behavior is preserved.

Versions must have identical repository identity, top-k, case IDs and definitions.
The output includes added/removed evidence, expected evidence gained/lost, ranking
differences, context differences and explanation changes. Context-expanded evidence
is included. Each case is classified as `improved`, `regression`, `observed_change`
or `unchanged`; regressions take precedence when gains and losses coexist.

Expected evidence gained and duplicate context reduced are improvements. Removal of
undeclared files is also described as an improvement relative to the case declaration,
but does not prove that those files were unnecessary. Expected evidence lost,
explanations removed, unstable repeat-run ranking, duplicate context increased, and
new undeclared files (unless explicitly tolerated) are regressions. Ordinary ranking
changes are observations requiring review, not evidence of instability by themselves.

## Validation rules

Every validation runs all baseline cases, including unaffected cases, through the
Phase 37 regression workflow. Each query runs twice. Changed definitions or missing
cases are refused rather than used to hide a regression. Acceptance requires:

- No new regression in expected evidence, explanations, or declared context allowances.
- Stable repeated retrieval for every case.
- A nonempty per-case review explanation for every ranking difference.
- No increase in duplicate context, including overlap between selected and expanded symbols.
- Trace compatibility: expected payload contract and identical normalized retrieval snapshot.
- Diagnose compatibility: current index, expected payload contract, identical evidence,
  ranking and explanations. Query-only per-result freshness metadata is normalized
  because diagnose supplies freshness at the top level.

All six gates must pass in the latest validation. Existing missing evidence remains
visible but does not fail a no-new-regressions gate by itself. Passing gates therefore
does not prove that the candidate problem was solved; inspect the comparison before
accepting. A no-change control can pass. Operational errors abort validation and do
not create a passing result. Compatibility failures are stored as failed checks.
Successful reporting exits zero even when `passed` is false; scripts must inspect
that field. An attempted acceptance with failing gates returns an error.

## Limitations

This is a local, single-writer review workflow, not a merge/deployment enforcement
service. There is no automatic tuning, patch application, rollback, scoring or research
evaluation. Static Python relationships and case declarations are incomplete. Two
repetitions catch observed instability, not every possible nondeterministic behavior.
History loads in memory and has no retention policy. Records are not cryptographically
signed; filesystem owners can edit them outside the workflow. Decisions apply to the
saved validation rather than certifying the currently running code indefinitely.

## Validation and preservation

Validation uses `C:/Apps/.venv/Scripts/python.exe`, `HF_HUB_OFFLINE=1`, and the existing
external Phase 37 model cache; no new model downloads are needed. Required commands:

```text
python -m unittest tests.test_developer_mode -v
python -m unittest discover -s tests -v
git diff --check
```

Final results:

- Phase 38 baseline: 42 tests passed; zero skips, failures or errors.
- Phase 39 focused suite: 50 tests passed; zero skips, failures or errors.
- Full suite: 194 tests passed; zero skips, failures or errors.
- `git diff --check`: passed.
- CLI list, show and saved-version comparison smoke checks: passed.

Eight new tests cover evidence-linked candidate creation, the CLI workflow, before/after
classification, accepted/rejected decisions, latest-validation enforcement, stability,
ranking review, trace/diagnose compatibility, invalid arguments and redirected storage.
Preservation hashes verify 306 existing files unchanged, including all 81 selected
protected files. Only `src/cli.py`, `tests/test_developer_mode.py` and
`docs/research/prototype-cli.md` changed from the starting workspace. Only this phase
document and `src/developer/optimization.py` were added. Research retrieval/evaluation,
experiment/data/benchmark paths, VERSION and release manifest have no diff against
`v0.1.1`; its tag object and peeled commit remain unchanged. No generated optimization
records exist inside the checkout. The existing developer retrieval implementation,
Phase 38 observability code and earlier user changes were preserved.

Logs are external at `C:/Apps/Temp/phase39-{baseline,focused,full}.log`.
Starting file hashes and git status are in `C:/Apps/Temp/phase39-start.json`;
final preservation results are in `C:/Apps/Temp/phase39-preservation.json`.

An actual evidence-linked candidate, `phase39-context-review`, is stored in the
external Phase 37 workspace at
`C:/Apps/Temp/Phase37-developer-regression-20260928/developer-workspace/optimization/candidates/phase39-context-review/candidate.json`.
It captures repeated undeclared route context across five cases, remains a candidate,
and makes no claim of a proven defect or accepted fix. A read-only comparison of the
existing baseline with its later history found all seven cases unchanged. Smoke
outputs are `C:/Apps/Temp/phase39-candidate-smoke.json` and
`C:/Apps/Temp/phase39-compare-smoke.json`.

Research: unchanged. Benchmark: unchanged/deferred. Humanize: unchanged/frozen.
Release: `v0.1.1` unchanged.
