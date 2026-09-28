# Phase 37 — Developer Retrieval Regression Tracking

Implemented as developer-only post-release software work. This framework describes
retrieval behavior changes; it produces no quality score, benchmark score, overall
ranking number, or research evaluation result.

## Starting baseline and preservation

The checkout started at `9512581d382ff1b66ff40d0eb90ccef6d14aabb9`, with the existing
Phase 27–36 tracked and untracked changes retained. The `v0.1.1` tag object was
`05688504f74ad51230ee1566fad8cda0f1b1ad97`, pointing to commit
`51329285a882c1b7942d0a5b1c571e628d63dfb4`. Protected research evaluation, retrieval,
benchmark, experiment, and release paths matched the tag before implementation.

Available developer capabilities were ranking `developer-navigation-v2`, context
analysis, retrieval comparison, local trace and diagnose, failure taxonomy,
stability checks, and incremental indexing. Their retrieval algorithms remain
unchanged. No research snapshots gain developer repositories.

The initial Phase 36 suite ran 32 tests with one failure, zero errors and zero skips:
the quality-fixture test required a positive duplicate-suppression event count.
Tied synthetic embeddings can allow overlapping module ranges to exclude a duplicate
before that event is recorded. The test now checks unique selected symbol/content
identities, with a separate controlled-candidate test requiring duplicate suppression.
This corrects the test invariant without modifying ranking or context behavior.

## Workflow

Use an existing indexed local Git repository and a developer-only case file:

```text
prototype local index REPOSITORY --workspace EXTERNAL_WORKSPACE
prototype local regression REPOSITORY --cases CASES.json --workspace EXTERNAL_WORKSPACE --baseline phase36 --create-baseline
prototype local regression REPOSITORY --cases CASES.json --workspace EXTERNAL_WORKSPACE --baseline phase36 --json
```

The capture runs each case twice. Unstable capture is rejected. Subsequent comparisons
also repeat each case and report instability separately from version-to-version
changes. Refresh the local index after source edits. After reviewing a desired change,
capture a new named baseline; existing baselines are never overwritten automatically.

`tests/fixtures/developer_eval/quality_cases.json` supplies seven synthetic workflows.
To use its paired repository, copy `quality_repository/` outside the checkout,
initialize and commit it as a local Git repository, then index it in an external
developer workspace. Model acquisition is a separate explicit operation; regression
uses the existing offline local index/model contract.

## Baseline format and storage

Generated records live only under:

```text
DEVELOPER_WORKSPACE/regression/REPOSITORY_ID/baselines/NAME.json
DEVELOPER_WORKSPACE/regression/REPOSITORY_ID/history/INVOCATION_ID.json
```

Baseline schema `developer-retrieval-baseline-v1` includes the repository identity,
source snapshot and commit, retrieval version, index schema and generation, runtime
contract, top-k, and case records. Each record stores query ID/text, repository fixture,
expected files/symbols/relationships, allowed context, failure tolerances, selected
files/symbols, ordered evidence identities, ranking explanations, and context assembly
decisions (expanded symbols, exclusions, suppressed duplicates and configuration keys).

The checked-in `tests/fixtures/developer_eval/baseline_records/` directory contains
hand-authored synthetic format/comparison examples only. It contains no generated
baseline capture, external repository snapshot, Humanize data, or benchmark results.
Runtime output paths are fixed under the developer workspace and checked for overlap
with the source checkout, repository, research storage, and redirected paths.

Each invocation writes a separate timestamped history record, including the current
snapshot, query cases, retrieval/index versions, comparison report, and baseline name.
Repeated identical runs retain separate history entries. Baseline creation and comparison
do not invoke the research evaluator or research run tracker.

## Comparison and classification

Comparison uses file/symbol identities and ordered evidence, excluding volatile chunk
IDs and aggregate retrieval scores. It preserves explanatory factors. Reports list
added/removed selected files and symbols, ranking order/reason differences, full context
differences, missing expected evidence, and newly introduced undeclared files.

Expected changes include additional declared symbol coverage, fewer repeated context
items, and additional required relationship expansion. Potential regressions include
lost prior symbols, new undeclared files, removed explanations, inconsistent repeated
retrieval, and lost expanded symbols. Other ranking/context changes are descriptive
observations. Every classified event names the case, previous/current behavior, and a
suspected cause; causes are hypotheses for trace/diagnose follow-up.

Missing expected evidence is reported even when already absent in the baseline. It
does not automatically mean a newly introduced regression. `behavior_changed` separates
baseline differences from persistent evidence gaps. Allowed extra files are excluded
from noise; tolerance flags are retained as case metadata but do not hide missing or
new evidence in this descriptive report. A newly undeclared file is possible noise,
not a proven irrelevant result.

## Limitations and unsupported cases

- Python static evidence only; dynamic dispatch, generated code and runtime links may
  be absent. Expected relationships are matched by symbol name and may be ambiguous.
- Cases and top-k must match the baseline. Changed IDs, query text, expectations,
  allowed context or tolerances require a separately named baseline. Duplicate IDs,
  malformed records, cross-repository baselines and in-checkout outputs are rejected.
- Repository identity includes its local path. Moving the repository requires a new
  baseline. Renames appear as removal/addition, not semantic equivalence.
- Ranking order can vary across index generations when retrieval candidates tie.
  Repeat checks establish stability within a current index, not across all platforms.
- Unchanged explanations do not establish correctness. No universal quality judgment,
  correctness probability, benchmark improvement claim, or research result is made.
- Comparison findings do not change the CLI exit status: successful reporting returns
  zero; invalid input or failed capture returns the existing CLI error status.
- Baseline/history files contain local query and evidence metadata. Existing workspace
  filesystem permissions apply. Capture does not export source text.

## Validation

The seven Phase 36 synthetic cases were captured with the existing cached pinned model
at top-k 50 in `C:/Apps/Temp/Phase37-developer-regression-20260928/`. The copied fixture
repository and generated developer workspace are both outside the source checkout.
Baseline `phase36-ranking-v2` retains selected files/symbols, ranking reasons and context
decisions for all seven cases. A separate comparison invocation reported stable repeated
retrieval, no behavior changes and no missing declared evidence. These observations
apply only to this synthetic developer fixture; they are not benchmark results.

The system Python initially lacked `sentence-transformers`: its full run recorded
181 tests, 45 dependency errors, two skipped model integration tests and zero assertion
failures. Final validation uses the existing `C:/Apps/.venv/Scripts/python.exe` environment
and sets `EMBEDDING_MODEL_CACHE` to the copied developer cache, with `HF_HUB_OFFLINE=1`.
No packages, models or repositories were downloaded. `pip check` reports no broken
requirements.

Final focused suite: **38 tests passed**, zero skips, failures or errors. Final full
suite: **182 tests passed**, zero skips, failures or errors, including cached-model
integration tests. Commands were `python -m unittest tests.test_developer_mode -v`
and `python -m unittest discover -s tests -v`, using the virtual-environment interpreter.
Logs are outside the checkout at `C:/Apps/Temp/phase37-focused-venv.log` and
`C:/Apps/Temp/phase37-full-venv.log`.

`git diff --check` passed. Hash comparison verified 65 protected files unchanged;
protected research evaluation/retrieval, evaluation/experiment and release paths also
have no diff against `v0.1.1`. Both tag object and peeled commit retain the identities
recorded above. All pre-existing files outside the four edited Phase 37 files were
preserved. Only the intended regression module, phase document, and two hand-authored
fixture files were added. No generated developer baseline/history data exists in the
source checkout.

Tests cover capture, immutable baseline/history persistence, ranking
and context changes, missing evidence/noise, classifications, repeated retrieval,
trace/diagnose compatibility, CLI JSON output and storage isolation.

Research is unchanged. Benchmark work is unchanged/deferred. Humanize remains
unchanged/frozen. The `v0.1.1` release tag and release artifacts remain unchanged.
