# Phase 34 - Developer Mode Workflow Hardening

**Status:** Implemented as developer-only post-release work on 2026-09-28.
Research evaluation, benchmark artifacts, Humanize files, frozen release
artifacts and v0.1.1 behavior remain unchanged.

## Baseline

Phase 33 provided developer evaluation, failure taxonomy, calibration cases,
case explanations, import-to-symbol expansion and comparison reports. Remaining
workflow gaps were large-repository cost, index freshness, changed-file and
symbol invalidation, retrieval drift after edits, and developer trust in stale
results.

## Change-aware indexing

Use:

```text
prototype local inspect PATH --changes
prototype local index PATH
```

`inspect --changes` compares the current eligible Python file hashes with the
active v2 snapshot and reports added, modified and deleted files, unchanged
files, files that would be reindexed, stale symbols and per-file reasons.
`index` exposes the same change reasons after applying incremental reuse.

Within the same commit, unchanged files and their accepted embeddings are
reused. Added or modified files are reparsed and embedded; deleted files are
removed from the assembled snapshot. A changed commit still triggers a full
rebuild because chunk IDs bind commit identity. Source changes during indexing
continue to fail closed rather than publishing a mixed snapshot.

The change fixtures cover new-file discovery, symbol rename, deletion and
dependency replacement in:

```text
tests/fixtures/developer_eval/change_scenarios.json
tests/fixtures/developer_eval/change_scenarios/
```

## Stability checks

```text
prototype local evaluate PATH --cases CASES.json --stability --json
```

Each case is queried twice in the same developer evaluation. The report records
query count, stable results, changed results and changed-case reasons based on
ranked chunk ID sequences. This is a deterministic drift check, not a benchmark
metric or quality claim. Repeated query records and the aggregate report stay in
the developer workspace.

## Explainability and trust

```text
prototype local explain RUN_ID CASE_ID
```

The command reopens a prior developer evaluation record and shows the indexed
working-tree version, index path, expected evidence, retrieved evidence,
failure categories, ranking factors and context explanations. Existing
`local explain QUESTION` and `local explain CASE_ID --cases CASES.json` forms
remain available. An evaluation run must be a developer-local evaluation record;
research runs are rejected.

## Calibration boundary

The only retrieval behavior change in this phase is the bounded, same-repository
incremental relationship refresh already established from Phase 33 failures:
changed files rebuild their context metadata and imported symbols are remapped
to current indexed chunks. No arbitrary ranking weights, research fusion rules,
benchmark evaluator behavior or release code were changed. Regression tests
cover before/after file changes, stale symbols, deletion, stability and run-case
explanation.

## Limitations

Large repositories still pay model startup and parsing costs for changed files;
there is no persistent indexing daemon. Static symbol invalidation is limited to
the supported Python AST and conservative import/name matching. Dynamic imports,
runtime dispatch, generated code and unsupported languages remain outside the
workflow. Stability checks detect observed ranking drift but do not explain
external model/runtime causes. Developer reports measure local workflow health,
not task success or research retrieval quality.

## Validation and isolation

```text
python -m unittest tests.test_developer_mode -v
python -m unittest discover -s tests -v
git diff --check
```

Final checks verify the v0.1.1 commit and tag identities, protected research
paths, benchmark/Humanize/evaluation immutability, and absence of generated
developer artifacts inside the source checkout. No developer repository is
added to a research snapshot, and no benchmark improvement is claimed.