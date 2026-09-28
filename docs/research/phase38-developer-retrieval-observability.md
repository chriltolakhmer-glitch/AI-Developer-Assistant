# Phase 38 ? Developer Retrieval Observability

This is developer-only software work. Research evaluation, benchmark datasets,
Humanize artifacts, research retrieval algorithms and frozen release artifacts are
unchanged. No quality scores, research metrics or benchmark improvement claims are
produced. Developer repositories are never added to research snapshots.

## Baseline

The checkout began at `9512581d382ff1b66ff40d0eb90ccef6d14aabb9`, with existing
Phase 27?37 changes retained. The `v0.1.1` tag object remains
`05688504f74ad51230ee1566fad8cda0f1b1ad97`, pointing to commit
`51329285a882c1b7942d0a5b1c571e628d63dfb4`.
The starting Phase 37 focused suite passed 38 tests, with zero skips, errors or failures.

Existing capabilities include regression tracking, immutable baseline comparison,
local trace and diagnose, context analysis, ranking explanations, stability checks,
and incremental indexing. Gaps were investigation across invocations, recurring
missing evidence/noise, and a chronology of retrieval and baseline changes.
The new layer describes these observations without changing retrieval algorithms.

## Workflow

Use the same external developer workspace as indexing and Phase 37 regression:

```text
prototype local query "Where is authentication handled?" --repository REPOSITORY --workspace EXTERNAL_WORKSPACE
prototype local regression REPOSITORY --cases CASES.json --baseline phase37 --workspace EXTERNAL_WORKSPACE
prototype local inspect-history --workspace EXTERNAL_WORKSPACE --json
prototype local inspect-history --query auth-flow --workspace EXTERNAL_WORKSPACE --json
prototype local timeline --workspace EXTERNAL_WORKSPACE --json
prototype local timeline --repository-id REPOSITORY_ID --note "Adjusted local context expansion after investigating auth-flow" --workspace EXTERNAL_WORKSPACE
```

`--query` matches an exact case ID or generated query identifier; `--repository-id`
is an exact identifier available in the history output. `--limit` (1?1000, default
20) limits displayed recent events, newest first. Patterns and behavior changes
use all matching history. Both commands print structured descriptive JSON, also
available via the standard `--json` output wrapper.

Investigate a pattern using `local diagnose CASE --cases CASES.json`, then use
`local trace QUERY` for ranking reasons. Review the suspected cause before changing
code or case expectations. Reindex after source changes, compare with the existing
baseline, and capture a separately named baseline only after review. Record an
optional fix note to explain the local change; notes are developer assertions,
not automatically verified fixes.

## Event format and storage

New query and diagnosis metadata is stored only in:

```text
DEVELOPER_WORKSPACE/observability/events/UUID.json
```

Schema `developer-retrieval-event-v1`, mode `developer-local-observability`, contains:

- Unique event ID and UTC timestamp; identical invocations remain separate events.
- Query ID, repository ID, retrieval version, index schema/generation, and top-k.
- Retrieved file/symbol identities, ordered ranking reasons and explanations.
- Context expansion decisions, duplicate suppression and exclusions.
- Freshness, confidence limitations, missing evidence and likely diagnostic causes
  when available for that command.

Raw query IDs use a stable hash of trimmed query text. Diagnosis uses its case ID.
Trace delegates to query and therefore records one underlying retrieval event.
Other developer workflows that call query also capture their underlying retrievals.
No raw source bodies or retrieval scores are copied into event records; queries,
paths and symbol names remain local metadata and can still be sensitive.

Phase 37 `regression/*/history/*.json` records are read in place and projected into
per-case events, retaining their original timestamps and invocation IDs. No migration
or duplicate baseline capture is needed. Their context exclusions are retained;
repository inventory exclusions were not recorded in Phase 37 and are explicitly
marked unavailable. Older query/trace runs without timestamps are not backfilled.

All destinations and input files use existing workspace containment checks. Source
checkout, repository overlap and configured research storage remain disallowed.
Redirected paths outside the workspace are rejected. History reads only the two
fixed developer namespaces, never research runs, benchmark history or Humanize data.

## Failure analysis

`inspect-history` includes repeated missing symbols, missing relationships,
undeclared context, unstable ranking and unsupported file types. Patterns require
at least two distinct events containing the same evidence in the same repository.
Each names affected cases, event IDs, possible cause and related diagnostics.
Regression records supply declared expectations, context allowances and repeat-run
stability; diagnosis events add explicit unsupported-language evidence. Missing
non-Python expected files in regression also indicate unsupported file types.

Undeclared context is a review candidate, not proof of irrelevance or an objective
threshold of excessive context. Cross-version ranking changes are descriptive;
only Phase 37 repeat-run instability establishes the unstable-ranking pattern.
Adjacent matching query/case observations show ranking, context and evidence changes.
Changed case definitions are marked non-comparable instead of silently compared.

## Timeline and limitations

The timeline shows initial and changed retrieval/index/configuration states,
baseline creation, regression invocations and optional fix notes. Observation
streams are separated by command/kind because available configuration metadata
varies. Index changes appear on the next observed retrieval, not at index-build time.
No research benchmark versions or release versions are tracked.

Python static relationships remain incomplete. Suspected causes are hypotheses.
Case relationships follow Phase 37 symbol-name matching, which can be ambiguous.
Without declared expectations, ordinary query events cannot establish missing
required evidence. A failed query before retrieval completes creates no event.
A diagnosis without a repository creates no repository event. Corrupt/unsupported
history causes an actionable error; it is not silently discarded.

History is local, append-only and currently has no retention policy. Inspection
loads all matching developer history before limiting display; large workspaces may
need future pagination. Repeated invocations count as repeated observations, not
independent experiments. There is no overall score, user ranking, export service,
automatic remediation or claim of causal improvement.

## Validation and preservation

Commands used the existing `C:/Apps/.venv/Scripts/python.exe` environment:

```text
python -m unittest tests.test_developer_mode -v
python -m unittest discover -s tests -v
git diff --check
```

- Baseline: 38 tests passed; zero skips, failures or errors.
- Focused: 42 tests passed; zero skips, failures or errors.
- Full: 186 tests passed; zero skips, failures or errors.
- `git diff --check`: passed.

Full validation used `HF_HUB_OFFLINE=1` and `EMBEDDING_MODEL_CACHE` pointing to
`C:/Apps/Temp/Phase37-developer-regression-20260928/developer-workspace/model-cache`.
No packages or models were downloaded. Test coverage includes event creation,
repeated invocation IDs, history filtering, all five pattern categories, repository
separation, ranking changes, timeline/configuration changes, fix notes, Phase 37
compatibility, trace/diagnose compatibility, CLI JSON output and storage isolation.

Both commands also read the existing external Phase 37 workspace successfully:
the authentication-flow filter returned two regression observations; the timeline
returned the observed initial state, baseline creation and comparison invocation.
These are software checks, not benchmark results.

Logs and smoke output are outside the checkout at
`C:/Apps/Temp/phase38-{baseline,focused,full}.log` and
`C:/Apps/Temp/phase38-{history,timeline}-smoke.json`.
`C:/Apps/Temp/phase38-preservation.json` records the preservation comparison.
Hashes verify 253 existing files unchanged, including 62 protected files selected
by research/retrieval paths and benchmark/Humanize/release/freeze names. Only
`src/cli.py`, `src/developer/local_workflow.py`, `tests/test_developer_mode.py` and
`docs/research/prototype-cli.md` changed from the starting workspace; only this
phase document and `src/developer/observability.py` were added. Research evaluation,
retrieval, evaluation/experiment directories, VERSION and release manifest have no
diff against `v0.1.1`. Tag object and peeled commit remain unchanged.
No generated developer observability records exist inside the source checkout.

Research: unchanged. Benchmark: unchanged/deferred. Humanize: unchanged/frozen.
Release: `v0.1.1` unchanged.
