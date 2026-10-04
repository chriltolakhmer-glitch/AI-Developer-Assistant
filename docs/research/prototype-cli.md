# Prototype CLI

The `prototype` command exposes distinct research and personal developer workflows. The following Windows PowerShell setup uses the tested Python 3.14 runtime and complete pinned dependency set. Python 3.11 or newer is required by the package.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install .
python -m pip check
$env:PROTOTYPE_DATA_ROOT = "$HOME/prototype-data"
prototype --help
```

For a CLI-only install, `python -m pip install .` installs the declared base dependency. The lock file is for the complete retrieval/test environment; model-backed operations also need the pinned model cache. The packaged default YAML is available without a source checkout.

## Separate modes

The immutable v0.1.1 release tag remains unchanged. Main currently contains separate developer-mode work through Phase 65. The `local` command group operates on personal repositories without changing research data, retrieval methodology, Humanize artifacts, benchmark files, or research run records.

**This is a local developer workspace. Results are not benchmark results.**

| Research commands | Personal developer commands |
|---|---|
|  | `prototype local change-impact PATH [--base COMMIT] [--question TEXT]` — integrated read-only change, context, freshness, and test planning |
|  | `prototype local plan-change PATH --goal TEXT [--base COMMIT]` — deterministic evidence-grounded implementation planning; no source edits, tests, reindexing, or patches |
| `prototype validate` â€” fixed pinned-corpus preprocessing validation; never fetches | `prototype local scan PATH` â€” read-only local Git/Python inventory |
| `prototype evaluate` â€” generated-fixture smoke evaluation, not a benchmark | `prototype local index PATH` â€” local parser/chunker and temporary dense + BM25 index |
| `prototype reproduce RUN_ID` â€” replay research CLI smoke/validation records only | `prototype local query "question" [--repository PATH] [--top-k N]` â€” retrieve from a local index |
|  | `prototype local trace "query" [--repository PATH]` â€” explain selected evidence, relationships, and ranking factors |
|  | `prototype local diagnose CASE --cases PATH [--repository PATH]` â€” diagnose missing developer-case evidence and index freshness |
|  | `prototype local analyze-context "query" [--cases PATH --case-id ID]` â€” inspect selected, missing, extra, and duplicate context |
|  | `prototype local compare "query" [--repository PATH]` â€” compare with a previous matching local retrieval record |
|  | `prototype local explain "question" [--repository PATH] [--top-k N]` â€” retrieve and show context assembly reasons |
|  | `prototype local evaluate REPOSITORY --cases PATH` â€” measure developer retrieval cases |
|  | `prototype local evaluate REPOSITORY --cases PATH --compare` â€” compare with the prior developer evaluation |
| `prototype demo` â€” generated-fixture research plumbing demo | `prototype local demo` â€” generated-fixture local parser/chunker/BM25 demonstration |

Developer commands do not invoke the research validation runner, research `RunTracker`, benchmark/evaluation tools, or Humanize code paths. A smoke result or a local retrieval result is not a research or benchmark result.

## Commands

### Developer test execution (Phase 62)

`prototype local test` runs the small T0 validation tier. Use `--test` with a dotted
unittest method/class/module for targeted execution, `--component developer` for
the complete developer suite, or `--changed --dry-run` to inspect the conservative
source-import dependency selection. `--base COMMIT` includes committed changes
since that reference as well as staged, unstaged and untracked changes.

`prototype local test-timing` uses the same selectors and reports test durations,
module/class totals, fastest/slowest tests, skips, failures, errors and environment
limitations. `--profile` adds resource call counts/times with profiling overhead.
Both commands emit JSON; `--report NEW_EXTERNAL_PATH` retains a new report outside
the checkout. Tests run in a fresh subprocess with the current Python interpreter.
Unittest progress goes to stderr and failures propagate a nonzero command status.
For Phase 63 readiness/governance performance work, use targeted timing without
`--profile`; whole-test cProfile severely distorts replay-heavy lifecycle tests.
The opt-in `tests/phase63_readiness_timing.py` diagnostic uses `perf_counter()`
and writes aggregate counts/timings only to an external report path. Its default
measures lifecycle setup plus one explicit audit; `--test drift` runs the real
drift/expiry unittest once and records how often it invokes `readiness.audit()`.

```powershell
prototype local test
prototype local test --changed --dry-run
prototype local test --component developer
prototype local test --test tests.test_developer_mode.DeveloperModeTests.test_phase61_relationships_require_file_identity
prototype local test-timing --test tests.test_config --report C:/Apps/test-evidence/config.json
python -B tests/phase63_readiness_timing.py --report C:/Apps/Temp/phase63/audit.json
python -B tests/phase63_readiness_timing.py --test drift --report C:/Apps/Temp/phase63/drift.json
```

Unknown changes produce an explicit broader T4 plan and require `--final-gate`
before execution. Full discovery remains a final gate, after targeted/component
checks, developer regression when affected, and preservation checks. It is never
the normal development loop. Existing tests and cache-dependent skips are unchanged.
See the [Phase 62 policy and limitations](phase62-developer-test-execution-optimization.md)
and the repository's `AGENTS.md`. These commands run test fixtures; they do not
create developer workspace state or research run records.

### `prototype validate`

Runs the scanner, parser, and chunker over already-present local checkouts. It never clones, fetches, or writes into a source checkout.

```text
prototype validate
prototype validate --corpus-root C:/research/corpus --output-dir C:/research/validation
```

Defaults are external to the repository: `~/prototype-data/corpus` and `~/prototype-data/validation`. The root can be changed with `PROTOTYPE_DATA_ROOT`. Missing or mismatched checkouts are reported in aggregate output rather than treated as permission to recover from the network.

### `prototype evaluate`

Runs a deterministic evaluation smoke check over generated fixtures. It validates the evaluator and metric wiring without reading the frozen Humanize pilot.

```text
prototype evaluate
prototype evaluate --json
```

The JSON form is suitable for shell capture or a lightweight reproducibility check. It is not a new benchmark result.

### `prototype local scan|inspect|change-impact|plan-change|index|query|trace|diagnose|analyze-context|compare|demo`

For a developer's existing local Python repository, use the separate developer workspace:

```powershell
$repo = 'C:\work\my-application'
prototype local scan "$repo"
prototype local inspect "$repo" --json
prototype local inspect "$repo" --changes --json
prototype local change-impact "$repo"
prototype local change-impact "$repo" --workspace C:/work/developer-workspace --base HEAD~1 --question "What authentication code is affected?" --top-k 10 --json
prototype local plan-change "$repo" --goal "Add validation to the login token flow"
prototype local plan-change "$repo" --workspace C:/work/developer-workspace --base HEAD~1 --goal "Improve stale-index errors" --top-k 10 --json
prototype local index "$repo"
prototype local query "Where is the session token loaded?" --repository "$repo"
prototype local trace "Where is authentication handled?" --repository "$repo" --json
prototype local explain "Where is the session token loaded?" --repository "$repo"
prototype local evaluate "$repo" --cases tests/fixtures/developer_eval/cases.json --explain
prototype local evaluate "$repo" --cases tests/fixtures/developer_eval/cases.json --stability --compare
prototype local diagnose trust-missing-symbol --cases tests/fixtures/developer_eval/trust_cases.json --repository "$repo" --json
prototype local analyze-context "Where are login tokens generated?" --repository "$repo" --cases tests/fixtures/developer_eval/quality_cases.json --case-id quality-authentication-flow --json
prototype local compare "Where are login tokens generated?" --repository "$repo" --json
prototype local explain auth-login --cases tests/fixtures/developer_eval/cases.json --repository "$repo"
prototype local demo
```

All source-derived local outputs stay under `developer_workspace` (default `~/.prototype/developer-workspace`), separate from `PROTOTYPE_DATA_ROOT`. `scan` and `index` require an existing Git working-tree root and never clone, fetch, or write to it. The current parser supports `.py` files only; unsupported extensions are counted and ignored. `index` and `query` require the pinned local model cache and fail with acquisition instructions if it is missing. They do not create approvals or benchmark questions and do not run an evaluation. See [Phase 28 developer mode](phase28-developer-mode.md) for complete handling and reproducibility limits.

Start with `scan` before attempting an index. If it reports zero Python files,
indexing and querying that repository are unavailable. Queries now report that
Python support is required rather than suggesting an unusable index rebuild.

For a custom workspace, pass the same `--workspace PATH` to every local command.
Check the workspace's filesystem permissions before indexing; source-derived
tokens, vectors, and query records inherit the parent directory's access rules.
The CLI does not grant repository approval or rewrite existing filesystem
permissions. New workspace directories request private mode; verify the effective
ACL on Windows and shared storage. The workflow probes temporary-file creation
and rejects artifact paths redirected outside the workspace.

Queries return ranked file/symbol/line references, related symbols and grouped
file context, not generated answers or source previews. `local explain`
additionally shows lexical/vector contributions, symbol relevance, expansion
decisions and excluded overlapping context. Inspect source locations in your
editor. An index can succeed while
omitting empty or over-256-token chunks, including every chunk from a useful file;
review its rejection count before relying on a missing result. `local inspect`
lists files, exclusion reasons, parser failures, chunk spans and token eligibility,
and identifies chunks present in a current index. Without a cached tokenizer,
token eligibility is reported as unknown, not as supported coverage.

`scan`, `inspect`, `change-impact`, `plan-change`, `index`, `query`, `trace`, `diagnose`, `analyze-context`, `compare`, `explain`, and `evaluate` accept `--json`. Full diagnostics also stay
in `WORKSPACE/runs/RUN_ID/results.json`. Query records include raw lexical/vector
contributions, the base fused score, metadata/test/container/diversity factors,
final score and source provenance. These post-release developer preferences do
not modify research scoring. Overlapping source ranges are suppressed; repeated
files receive a soft diversity discount. Explicit test queries retain test results
without the implementation preference penalty.

`local change-impact REPOSITORY` compares the working tree with `HEAD`. With
`--base COMMIT`, it includes committed changes after that reference together
with current staged, unstaged, deleted, renamed, and untracked paths. Its stable
JSON mode is `developer-local-change-impact` and separates changed-code evidence,
static relationships, optional retrieved query evidence, and additional related
context. Unsupported changed files remain visible without fabricated symbols.
The command reports a current, stale, missing, or unsupported index; a stale or
missing index blocks `--question` retrieval and produces an explicit `local index`
recommendation instead of silently rebuilding or downloading a model.

The command accepts `--workspace PATH`, `--base COMMIT`, `--question TEXT`,
`--top-k N` (default 10, range 1–50), and `--json`. `--workspace` selects the
external developer workspace; `--question` requests optional retrieval, and
`--top-k` sets its result limit. `--json` prints the complete stable payload.

Affected tests come directly from the Phase 62 changed-file planner. The report
includes selected test identities/modules, tier, intentional omissions,
uncertainty, and required follow-up. `change-impact` never executes tests. Run the
reported `prototype local test --changed` command explicitly after review. Static
imports, calls, callers, parents, and configuration references are conservative
parsed-source evidence, not confirmation of runtime execution. See the
[Phase 64 workflow report](phase64-change-aware-developer-assistance.md).

`local plan-change REPOSITORY --goal TEXT` composes the Phase 64 change-impact
payload rather than duplicating Git, parsing, relationship, freshness, retrieval,
or Phase 62 test-selection logic. A current index permits direct and
relationship-expanded goal evidence. A stale or missing index blocks retrieval,
marks the plan limited or manual-review-required, and recommends an explicit
`local index` command without running it. Clean repositories are supported:
`current changes: none` remains separate from goal-derived proposed targets.

Targets carry source references, roles, evidence categories, reasons, change
status, current-index provenance, related symbols, and unresolved notes.
Preserved behavior is stated conservatively from parsed callers/imports,
configuration references, related tests, and current retrieval context. Tests to
run are separate from tests to review or possible human-approved regression
coverage. Validation proceeds from exact tests to affected modules/components,
with T2/T3 only where required and T4 reserved for the final gate. The command
never executes tests, edits source, drafts patches, reindexes, downloads a model,
or changes governance state. Unsupported, ambiguous, omitted, stale, and missing
evidence remains individually visible. See the
[Phase 65 workflow report](phase65-evidence-grounded-implementation-planning.md).

`local inspect --changes` compares current eligible-file hashes and symbols with
the active developer snapshot. `local index` reports changed files, rebuild
reasons, reused files/chunks, removed files and stale-symbol counts. A changed
file is reparsed and re-embedded while unchanged files are reused when the
commit identity permits it; a changed commit still requires a full rebuild.

`local evaluate --stability` repeats each developer query and reports stable and
changed ranked result sets. `local explain RUN_ID CASE` reopens a stored
developer evaluation case with its index state, expected/retrieved evidence and
ranking factors. These records remain under the developer workspace and are not
research evaluation records.

`local trace QUERY` adds per-result match reasons, statically observed import/call/
parent relationships, ranking factors, and context-expansion reasons while
preserving the existing ranking explanation. Its qualitative high/medium/low
confidence label summarizes observed local evidence only; it is not a correctness
probability, quality score, or benchmark metric. `local diagnose CASE --cases PATH`
compares case expectations with active-index results and current source inventory,
reporting available/missing evidence, freshness, and likely causes such as an
unsupported language, excluded/unparseable file, missing symbol, stale index,
deleted file, or undetected static relationship. If stale, returned evidence is
from the older snapshot and is not current-source evidence. Both commands are
developer-only and do not call research evaluation or alter retrieval ranking.

`local analyze-context QUERY` reports grouped selected files, missing expected
files/symbols/relationships, extra or allowed context, duplicate suppression,
and ranking explanations. Pass a developer case file (and `--case-id` when it
contains multiple cases) to assess declared evidence; without expectations, the
report states that completeness cannot be assessed. Context expansion now
prioritizes explicit static caller/importer/callee relationships, deduplicates
symbol names, and omits nearby-only chunks by default.

`local compare QUERY` compares current retrieval against the most recent matching
developer-local `query` or `trace` record for that question and repository. It
lists added/removed files/results, rank changes, and explanation/context changes.
The first call reports that no previous retrieval is available; repeat after a
query to retain a baseline. The report is descriptive and does not compute a
quality score. Developer navigation ranking v2 explicitly explains exact-symbol,
relationship-proximity, file-relevance, existing metadata/test/container and
diversity factors; exact duplicate symbol/content copies across files are
suppressed. Stale indexes are rejected before ranking, not treated as recent.
See [Phase 36 retrieval quality optimization](phase36-developer-retrieval-quality-optimization.md)
for the synthetic quality cases, comparison contract, and limitations.

Unchanged indexing verifies file hashes and artifact integrity, then reuses the
snapshot without parsing or loading the model. Within the same commit, only
new/changed files are parsed and embedded; deleted files are removed. A new commit
gets a full rebuild to preserve commit-bound chunk IDs. Output reports reused and
rebuilt files/searchable chunks. Snapshot assembly still rewrites the combined
index; this is file-level reuse, not in-place vector mutation.

Phase 30 uses `WORKSPACE/indexes/REPOSITORY_ID/v2/SNAPSHOT/`. Earlier developer
indexes remain untouched but must be indexed once in v2 before querying with the
current source. `state.json` now caches source chunk contents as well as file
hashes; protect it like the source repository. Runtime-incompatible or corrupt
snapshots fail closed. To reset, stop commands and move the affected repository's
`v2` directory to a retired directory **inside the same developer workspace**,
then rerun `local index`. Inspect the resolved path first. Do not move or delete
research storage or the source checkout. Keep or delete retired developer data
under your own retention policy; no automatic cleanup command is provided.

`prototype local demo --workspace PATH` demonstrates a generated, in-memory
fixture. It writes no run record and does not exercise model-cache availability,
repository indexing, or the selected workspace's write permissions. See the
[Phase 29 repository pilot](phase29-developer-repository-pilot.md) for observed
usability limitations.

See [Phase 30 hardening](phase30-developer-retrieval-hardening.md) for measured
developer timings, ranking tradeoffs, validation and post-release compatibility.
See [Phase 32 developer retrieval evaluation](phase32-developer-retrieval-evaluation.md)
for the developer-only case format, metrics and diagnostic limits.
See [Phase 33 retrieval calibration](phase33-retrieval-calibration.md) for
failure taxonomy, calibration cases and developer-only comparisons.
See [Phase 35 retrieval trust and explainability](phase35-retrieval-trust-explainability.md)
for evidence traces, confidence diagnostics, missing-context diagnosis, fixtures,
and the research-separation boundary.

### `prototype demo`

Shows the parser, chunker, and evaluator flow over generated Python code:

```text
prototype demo
```

The demo is offline, repeatable, and source-independent. It creates three chunks from a generated `demo.py`, scores two synthetic queries, and prints aggregate MRR/nDCG. The fixed fixture is designed to exercise the parsing/chunking/evaluator path, so perfect scores are not retrieval-quality results.

### `prototype reproduce RUN_ID`

Replays a prior tracked `demo`, `evaluate`, or `validate` command and compares the standardized output. Find the ID in `$env:PROTOTYPE_DATA_ROOT\runs` (default: `$HOME\prototype-data\runs`). To reproduce the latest demo specifically, inspect each run's metadata and select the newest one whose command is `demo`:

```powershell
$run = Get-ChildItem "$env:PROTOTYPE_DATA_ROOT/runs" -Directory |
	ForEach-Object {
		$metadata = Get-Content (Join-Path $_.FullName 'metadata.json') -Raw | ConvertFrom-Json
		if ($metadata.command -eq 'demo') {
			[pscustomobject]@{ Id = $_.Name; Created = $_.LastWriteTime }
		}
	} |
	Sort-Object Created -Descending |
	Select-Object -First 1
if (-not $run) { throw 'Run prototype demo before looking up its run ID.' }
prototype reproduce $run.Id
```

Reproduction compares the saved standardized output payload, not timestamps, run IDs, duration, or scientific validity. Keep the same release, configuration, and inputs.

## Troubleshooting

- `prototype` is not recognized: activate `.venv` in the current PowerShell session, or invoke `& .\.venv\Scripts\prototype.exe ...`.
- Validation reports missing checkouts: the command still writes an aggregate report and exits successfully, but preprocessing readiness is `no`. Supply already-acquired, authorized pinned checkouts; it never fetches them.
- Invalid validation paths: check that the corpus root is a directory and the report output is writable and outside the project and source checkouts.
- Model-backed operations fail: configure the documented offline model cache and `HF_HUB_OFFLINE=1`; the CLI smoke commands do not require a model.

## Developer retrieval regression tracking (Phase 37)

`prototype local regression REPOSITORY --cases CASES.json --baseline NAME
--create-baseline --workspace EXTERNAL_WORKSPACE` captures a new immutable developer
baseline from an existing local index. Omit `--create-baseline` on later runs to report
evidence, ranking-explanation and context differences; add `--json` for machine-readable
output. `--top-k` defaults to 10 and must match the baseline. Both modes repeat every
query to check stability. Capture refuses unstable retrieval or an existing name.

Generated baselines and per-invocation history stay under the external developer
workspace's `regression/` directory. Checked-in synthetic baseline examples are format
fixtures only. Cases with changed definitions require a new baseline name. Findings
are descriptive and do not produce quality scores or research benchmark results.
Successful reporting exits zero even when potential regressions are found.

See [Phase 37 workflow, format and limitations](phase37-developer-retrieval-regression-tracking.md).


## Developer retrieval observability (Phase 38)

`prototype local inspect-history --workspace EXTERNAL_WORKSPACE --json` shows recent
retrieval metadata, descriptive behavior/ranking changes and repeated failure patterns.
Filter by exact `--query CASE_OR_QUERY_ID` or `--repository-id ID`; `--limit 20` limits
recent displayed events, while analysis uses all matching history.

`prototype local timeline --workspace EXTERNAL_WORKSPACE --json` shows observed
retrieval/index/configuration changes, baseline captures and regression invocations.
Add `--repository-id ID --note "Fix description"` to record a developer-supplied fix
note. Notes do not automatically verify that a failure was fixed.

Query (including trace) and diagnosis events stay under the external developer
workspace's `observability/events/`. Existing Phase 37 regression history is read
in place. No research records, benchmark scores or release versions are tracked.
See [Phase 38](phase38-developer-retrieval-observability.md) for schema, investigation
workflow, pattern semantics and limitations.

## Developer optimization loop (Phase 39)

`prototype local optimize --workspace EXTERNAL_WORKSPACE --json` lists developer
optimization candidates and repeated-pattern inputs. Use `optimize create --id ID
--problem TEXT --case CASE_ID --source EVENT_ID --proposed-change TEXT
--validation-method TEXT` to record a proposal; repeat `--case`/`--source` as needed.
Evidence IDs come from `inspect-history` and must cover the affected cases in one
repository. `optimize show --id ID` includes linked evidence and validation history.

Apply any proposed change manually, reindex when needed, then run `optimize validate
--id ID --repository REPOSITORY --cases CASES.json --before BASELINE`. This reruns all
unchanged baseline cases, stability checks and trace/diagnose compatibility. Ranking
changes require per-case `--ranking-note "CASE_ID=Review explanation"`. The JSON
`passed` field and individual gates describe the result; reporting exits zero even
when validation fails. `optimize accept --id ID --note TEXT` requires the latest
validation to pass every gate. `optimize reject --id ID --note TEXT` records rejection.
Neither decision modifies retrieval code or settings. Decisions are final; create a
new candidate for another experiment. Add `--workspace EXTERNAL_WORKSPACE --json`
to each command above.

`prototype local compare --before VERSION --after VERSION --workspace EXTERNAL_WORKSPACE
--json` compares saved developer baseline names or regression history UUIDs. Select
`--repository-id ID` if multiple repositories exist. It reports evidence, ranking,
context and explanation changes without scores. Version comparison requires unchanged
case definitions and top-k. Existing `local compare QUERY` remains available.

Candidate, validation and decision records stay in the external workspace's
`optimization/candidates/` directory. See [Phase 39 workflow, gates and limitations](phase39-developer-retrieval-optimization-loop.md).

## Developer retrieval optimization safety framework (Phase 40)

Decisions from `optimize accept`/`optimize reject` now also record the evidence event
IDs, a validation summary (`regressions`, `improvements`, `stability_passed`, `passed`),
and a `rollback` block naming the baseline to restore. Rejections still require a
nonempty `--note`, stored as both `note` and `reason`.

`optimize create` accepts an optional `--supersedes PRIOR_ID` to link a retry to a
previously **rejected** candidate in the same repository. `optimize`/`optimize show`
then report a per-candidate `history` (attempt number, status, rejection reason) and a
top-level `unresolved_candidates` list of candidates without a decision yet.

`prototype local rollback --id ID --workspace EXTERNAL_WORKSPACE --json` shows a
decided candidate's current state, previously observed baseline/history versions, the
latest validation's affected-case comparisons, and any recorded rollback attempts.
`rollback record --id ID --note TEXT` requires a previously **accepted** candidate and
records a rollback attempt (target baseline, note, manual-restoration instructions)
under `optimization/candidates/ID/rollback/`. Rollback never edits source files,
retrieval settings, research data or release artifacts; it only documents the intent
to manually revert to the named baseline.

`prototype local optimize-check --workspace EXTERNAL_WORKSPACE --json` reports
`conflicts`, `affected_cases` and `warnings` without resolving anything: repeated
independent attempts on the same case, duplicate proposed changes, a single
validation that improves some cases while regressing others, disagreeing outcomes
between independent candidates on the same case, repeatedly rejected attempt chains,
and undecided candidates.

See [Phase 40 lifecycle, decision-record schema and limitations](phase40-developer-retrieval-safety-framework.md).

## Developer retrieval governance and lifecycle (Phase 41)

`optimize register --id ID --owner NAME --purpose TEXT --case CASE_ID
--workspace EXTERNAL_WORKSPACE --json` starts explicit lifecycle tracking for an
existing candidate (`proposed` state). Repeat `--case` for every affected case; each
must already be recorded on the candidate. `optimize transition --id ID
--state STATE --note TEXT` advances the lifecycle. Allowed states are `proposed`,
`experimenting`, `validated`, `accepted`, `rejected`, `rolled_back` and `archived`.
Only the transitions `proposed→experimenting`, `experimenting→{validated,rejected}`,
`validated→{accepted,rejected}`, `accepted→rolled_back`, and any non-archived
state→`archived` are permitted; every other request is rejected. Every transition is
an immutable, append-only record (owner and purpose carry forward automatically);
nothing is rewritten or deleted.

`prototype local optimize-status --workspace EXTERNAL_WORKSPACE --json` groups every
registered candidate by lifecycle state (`active`, `validated`, `accepted`,
`rejected`, `rolled_back`, `archived`) and separately flags `stale` active candidates
(no lifecycle update in 30+ days).

`prototype local optimize-archive ID --note TEXT --workspace EXTERNAL_WORKSPACE
--json` archives an obsolete experiment from any non-archived state. Archiving only
appends a new lifecycle record; candidate, validation, decision and rollback records
are never deleted.

`prototype local optimize-maintenance --workspace EXTERNAL_WORKSPACE --json` reports
`stale_candidates` (registered candidates stuck in `proposed`/`experimenting` for
30+ days), `duplicates` (candidates proposing the same change, reused from
`optimize-check`), and `maintenance_notes` (repeatedly rejected attempt chains and
accepted candidates with an unused rollback path). This command only reports; it
never archives, deletes or modifies a candidate.

Lifecycle records stay in the external workspace's
`optimization/candidates/ID/lifecycle/` directory alongside the existing Phase 39/40
candidate, validation, decision and rollback records. No user scoring, productivity
metric or developer ranking is produced. See
[Phase 41 governance, lifecycle states and limitations](phase41-developer-retrieval-governance.md).

## Developer retrieval governance validation (Phase 42)

`prototype local optimize-audit --workspace EXTERNAL_WORKSPACE --json` performs a
read-only integrity check of lifecycle chains. It reports `audit_status` (`clean` or
`issues_found`), a combined `issues` list, and categorized findings for invalid
transitions, missing metadata, duplicate history entries, orphaned records, and
inconsistent states. A clean report uses `"audit_status": "clean"` and
`"issues": []`. The command never repairs, deletes, or rewrites records; findings
require developer review.

`prototype local optimize-history ID --workspace EXTERNAL_WORKSPACE --json` displays
an immutable, chronological view of the selected candidate's creation, lifecycle,
ownership changes, validation, decision, rollback and archive records. Lifecycle
sequence numbers remain available in the records. To record an ownership change on a
transition, pass `--owner NAME`; the prior and new owner are preserved in that
append-only event. A transition to `validated` requires `--last-validation-at` with an
ISO-8601 timestamp; this records validation time but does not run validation itself.

The extended `optimize-maintenance` report retains `stale_candidates`, `duplicates`
and `maintenance_notes`, and adds `abandoned_experiments`,
`incomplete_validation_records`, `missing_ownership_fields`,
`stale_accepted_candidates`, `archived_active_references`, `metadata_issues`, and
`recommendations`. These are advisory only; `automatic_changes` is always false.
Review the Phase 42 limitations: the checks diagnose record consistency, not manual
workspace tampering or external source-code state, and archived lifecycle states are
terminal rather than restorable.

All these commands remain developer-workspace-only. They do not read or write
research evaluation data, benchmark artifacts, Humanize artifacts, frozen release
artifacts, or research retrieval snapshots. See
[Phase 42 governance validation and safety limits](phase42-developer-retrieval-governance-validation.md).

## Developer retrieval governance automation (Phase 43)

`prototype local optimize-health --workspace EXTERNAL_WORKSPACE --json` runs the
read-only lifecycle audit, ownership/validation metadata checks, maintenance scan,
conflict detection and archived-reference consistency checks. `health_status` is
`clean`, `warnings` or `issues_found`; `checks` gives each category and its findings.
This command never repairs records or decides candidates.

`prototype local optimize-summary --workspace EXTERNAL_WORKSPACE --json` summarizes
counts in every lifecycle state, separately identifies optimization candidates not
registered with lifecycle governance, shows recent lifecycle activity (newest first),
pending reviews, stale items, archived items and unresolved conflicts. Use
`--recent-limit N` to select 1–1000 recent events (default 20). The report contains no
score, candidate ranking or developer productivity measure.

`prototype local optimize-checkpoint --workspace EXTERNAL_WORKSPACE --json` runs the
same health and summary checks and appends one immutable JSON snapshot under
`optimization/governance-checkpoints/UUID.json` inside the external developer
workspace. The snapshot contains a timestamp, health status, detected findings and
candidate lifecycle counts. Running it again creates a separate record; it does not
modify candidates, lifecycle history or prior checkpoints. It is a manual repeatable
check command, not an operating-system scheduler.

The maintenance report retains the Phase 42 compatibility fields and adds structured
`findings`. Each finding provides an issue type, `severity` (`error` or `warning`),
affected candidate IDs, a suggested manual review action and any related
lifecycle event IDs/sequences. Recommendations are advisory, and the report's
`automatic_changes` remains false. No suggested action is executed automatically.
Optimization candidates without lifecycle registration are included as
`unregistered_candidates` findings so missing governance ownership is visible; they
are not registered automatically.

All three commands operate solely in the developer workspace. Checkpoints are
append-only but are not cryptographically signed; workspace administrators can
change files outside the CLI. A checkpoint records the observation at one time and
does not prove subsequent state or replace human inspection. See
[Phase 43 governance automation and limitations](phase43-developer-retrieval-governance-automation.md).

## Developer retrieval governance review (Phase 44)

`prototype local optimize-review-create CANDIDATE_ID --reason TEXT --workspace
EXTERNAL_WORKSPACE --json` opens a pending developer-only review. `--owner` defaults
to `developer`; repeat `--case CASE_ID` to select affected cases. Use
`--conflict-note TEXT` to document a known conflict for human review. A candidate may
have only one pending review at a time.

`prototype local optimize-review REVIEW_ID --workspace EXTERNAL_WORKSPACE --json`
shows review metadata and the joined candidate details, lifecycle events, validation
results, maintenance findings, previous decisions and candidate attempt history. The
ID may be a review ID or an unambiguous candidate ID. Omit it to list the queue.
Review events retain reviewer, reason, owner, affected cases, validation summary,
governance-health status and an append-only review history.

`prototype local optimize-policy-check --workspace EXTERNAL_WORKSPACE --json` checks
all candidates; add `--id CANDIDATE_ID` to scope the report. It reports `passed`,
`warnings`, `blocked` and `automatic_changes: false`. Approval requires lifecycle
ownership, a valid `validated` lifecycle, persisted validation evidence with all
gates passing, required rollback information when applicable, and conflicts that are
resolved or explicitly documented. A conflict note documents but does not resolve a
conflict. Policy checks are read-only and never repair, promote or modify a candidate.

`prototype local optimize-approve REVIEW_ID --reviewer NAME --reason TEXT` records an
approval only after policy blockers are cleared. `prototype local optimize-reject
REVIEW_ID --reviewer NAME --reason TEXT` records a rejection reason. Reviews may also
be deferred, withdrawn or reopened from the deferred state with
`optimize-review-defer`, `optimize-review-withdraw` and `optimize-review-reopen`.
Invalid state transitions are rejected; each transition adds an immutable workspace
event. Approval is not the separate optimization `optimize accept` decision: no
command in this review workflow changes retrieval code, ranking, lifecycle state or
source files. Records remain in the external developer workspace and are not research
or benchmark results.

See [Phase 44 review workflow, policy and limitations](phase44-developer-retrieval-governance-review.md).


## Developer retrieval promotion (Phase 45)

Create a configuration candidate with `local optimize create --retrieval-settings
'{"relationship_factor": 1.5}'` plus the existing required candidate/evidence options.
Supported values are finite numbers from 1 to 2; the default multiplier is 1.25.
Validate the candidate using `local optimize validate`, record its validated lifecycle,
and obtain approval using the Phase 44 review commands. Validation and approval bind
the exact settings and prior active configuration. Prose-only proposals cannot be
promoted and must be recreated with explicit settings and fresh evidence.

```text
prototype local optimize-promote CANDIDATE_ID --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-promotion-status --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-promotion-check --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-retire PROMOTION_OR_CANDIDATE_ID --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-promote-rollback PROMOTION_OR_CANDIDATE_ID --workspace EXTERNAL_WORKSPACE --json
```

Promotion explicitly moves pending ? validated ? promoted and activates settings
only for the source developer repository. Status exposes active, pending and retired
promotions, complete records and rollback history. Retirement removes settings while
preserving history. Rollback restores the exact prior configuration; later changes
must be rolled back first. All records live in the external developer workspace.
The read-only check reports `passed`, `warnings` and `blocked` without repair or
activation. Candidate decisions, reviews and source-change rollback records remain
separate. No research/benchmark/Humanize/release artifacts are changed.

See [Phase 45](phase45-developer-retrieval-promotion-pipeline.md) for lifecycle states,
atomic storage, validation gates, pause/resume API and recovery limitations.

### Developer configuration snapshots (Phase 46)

Create a versioned snapshot from a currently promoted source. Settings are copied
from the approved promotion; changes require a new governed source and snapshot.

```text
prototype local config-create PROMOTION_ID --reason "Capture approved settings" --workspace EXTERNAL_WORKSPACE --json
prototype local config-validate CONFIG_ID --reason "Verify evidence" --workspace EXTERNAL_WORKSPACE --json
prototype local config-activate CONFIG_ID --reason "Select reference" --workspace EXTERNAL_WORKSPACE --json
prototype local config-status --workspace EXTERNAL_WORKSPACE --json
prototype local config-history --workspace EXTERNAL_WORKSPACE --json
prototype local config-diff 1 2 --workspace EXTERNAL_WORKSPACE --json
prototype local config-rollback CONFIG_ID --reason "Restore prior reference" --workspace EXTERNAL_WORKSPACE --json
prototype local config-retire CONFIG_ID --reason "Close snapshot" --workspace EXTERNAL_WORKSPACE --json
```

Mutation commands require a reason and accept `--actor` (default `developer`).
Configuration IDs such as `retrieval-config-001` identify immutable settings
versions; diff arguments are numeric versions. Status shows the active reference,
version, candidate/promotion, recent events and source eligibility findings.
History includes creation, validation, activation, superseded retirement,
explicit retirement and rollback events, with reasons and prior values.

Activation requires validated status, current approval and passing policy checks.
It preserves a rollback point. Rollback takes the current active ID and restores
its prior reference, rechecking the prior source's eligibility. Stale activations
and out-of-order rollbacks fail without changing history. Records remain in the
external workspace and never modify source files.

Configuration commands manage references; Phase 45 promotion commands remain the
authority for runtime settings. Rolling back a configuration reference does not
roll back its source promotion. There is one managed active reference per workspace.
See [Phase 46](phase46-developer-retrieval-configuration-management.md) for the
lifecycle, settings model, isolation boundary and recovery limitations.

### Developer deployment control (Phase 47)

Stage a validated (or already-active) configuration as an explicit developer
deployment reference. Staging checks its existing promotion approval and records
planned/staged events. It does not validate or activate the deployment automatically.

```text
prototype local deploy-stage CONFIG_ID --reason "Stage approved configuration" --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-validate DEPLOYMENT_ID --reason "Check deployment evidence" --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-activate DEPLOYMENT_ID --reason "Select validated rollout" --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-status --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-diff DEPLOYMENT_A DEPLOYMENT_B --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-pause DEPLOYMENT_ID --reason "Pause rollout reference" --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-resume DEPLOYMENT_ID --reason "Recheck and resume" --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-rollback DEPLOYMENT_ID --reason "Restore previous deployment" --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-retire DEPLOYMENT_ID --reason "Close rollout" --workspace EXTERNAL_WORKSPACE --json
```

Mutations require a reason and accept `--actor` (default `developer`). Validation
records configuration eligibility, policy results, source promotion/review, and
rollback availability. Activation requires validated status and rechecks evidence
and the saved previous deployment reference. Stale evidence requires restaging.
No command automatically approves a promotion or review.

Status shows selected/active and staged deployments, validation, complete history,
and current blockers. Pausing retains the selected reference but reports no active
deployment. Resume rechecks validation. Rollback restores the previous reference
only if its configuration and governance evidence remain eligible. Diff reports
configuration, deployment, validation, and lifecycle changes without scores.

These controls only manage deployment references. Phase 46 configuration history
and active references are preserved; Phase 45 promotions remain responsible for
runtime retrieval settings. No deployment command modifies source files or silently
changes retrieval behavior. Records stay in the external developer workspace.
See [Phase 47](phase47-developer-retrieval-deployment-control.md) for lifecycle,
staging recovery, rollback, concurrency, and developer-only limitations.

### Developer deployment governance and audit (Phase 48)

```text
prototype local deploy-history --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-audit DEPLOYMENT_ID --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-governance-check DEPLOYMENT_ID --workspace EXTERNAL_WORKSPACE --json
prototype local deploy-inspect DEPLOYMENT_ID --workspace EXTERNAL_WORKSPACE --json
```

These commands are read-only and require no actor or reason. History lists all
deployments and events newest first. Audit provides the complete chronological
timeline for one deployment, including actors, reasons, validation, rollback,
implicit retirement and restoration. Audit records append atomically with state
changes in the external developer deployment journal; Phase 47 history remains
readable without migration.

Governance reports `passed`, `warnings`, and `blocked` findings for ownership,
source configuration, promotion approval, validation evidence, rollback target,
lifecycle state and audit completeness. Missing validation blocks readiness;
an initial deployment's empty rollback reference is a warning. A generated
report exits successfully even when it contains blockers; automation must inspect
`blocked`. Inspection combines the configuration, source promotion, evidence,
governance status, audit timeline and rollback availability without taking action.

There are no quality scores or automatic repairs. Local actors are attribution,
not authenticated identities, and local hash chains are not tamper-proof storage.
See [Phase 48](phase48-developer-retrieval-deployment-governance-audit.md) for the
audit model, investigation workflow, compatibility and limitations.

### Developer deployment operations and incidents (Phase 49)

```text
prototype local deploy-health DEPLOYMENT_ID --workspace EXTERNAL_WORKSPACE --json
prototype local incident-create DEPLOYMENT_ID --owner "on-call" --reason "Unexpected behavior" --workspace EXTERNAL_WORKSPACE --json
prototype local incident-status --workspace EXTERNAL_WORKSPACE --json
prototype local incident-investigate INCIDENT_ID --reason "Review audit evidence" --workspace EXTERNAL_WORKSPACE --json
prototype local incident-inspect INCIDENT_ID --workspace EXTERNAL_WORKSPACE --json
prototype local incident-resolve INCIDENT_ID --reason "Recovery verified" --recovery-action "Describe the manually completed action" --workspace EXTERNAL_WORKSPACE --json
prototype local incident-close INCIDENT_ID --reason "Review complete" --workspace EXTERNAL_WORKSPACE --json
prototype local recovery-history --workspace EXTERNAL_WORKSPACE --json
prototype local incident-diff INCIDENT_A INCIDENT_B --workspace EXTERNAL_WORKSPACE --json
```

Use the returned `operation_id` (for example `operation-001`) as `INCIDENT_ID`.
Creation records an immutable owner (default `developer`), reason and `open`
state. Mutations require `--reason` and accept `--actor` (default `developer`).
The lifecycle is `open -> investigating -> resolved -> closed`; direct
`open -> resolved` is also allowed. Closed incidents cannot reopen.

Status groups active, resolved and closed incidents with ownership and deployment
links. Inspect combines the captured deployment/configuration history with live
deployment history, audit events, configuration/governance health and rollback
availability. Health is read-only: `blocked` means governance blockers, `warning`
means warnings or a non-active deployment, and `healthy` means neither. An initial
deployment restoring an empty reference carries a warning. Reports exit zero when
successfully generated, even when health is blocked; malformed journals fail.

Resolution appends an attributed resolution and a linked recovery operation in
one atomic event. `--recovery-action` records what a developer did; it executes
nothing. Optional `--rollback-reference AUDIT_EVENT_ID` must refer to a recorded
rollback for that deployment. Perform any approved rollback explicitly using the
existing deployment workflow before referencing its audit event. Resolution does
not grant approval or prove that health has recovered.

Recovery history retains incidents, recovery actions, rollback references and
resolution history. Diff compares affected deployments, captured configurations,
incident timelines and resolutions without scores. Records live only under the
external workspace's `optimization/operations`; no operational artifacts belong
in the checkout. See [Phase 49](phase49-developer-retrieval-deployment-operations.md)
for persistence, health semantics and limitations.

### Developer deployment reliability and recovery preparation (Phase 50)

```text
prototype local reliability-check DEPLOYMENT_ID --workspace EXTERNAL_WORKSPACE --json
prototype local recovery-plan-create DEPLOYMENT_ID --owner "on-call" --reason "Prepare recovery handoff" --workspace EXTERNAL_WORKSPACE --json
prototype local recovery-plan-status --workspace EXTERNAL_WORKSPACE --json
prototype local recovery-plan-inspect PLAN_ID --workspace EXTERNAL_WORKSPACE --json
prototype local recovery-verify PLAN_ID --workspace EXTERNAL_WORKSPACE --json
prototype local readiness-create DEPLOYMENT_ID --reason "Assess operational readiness" --workspace EXTERNAL_WORKSPACE --json
prototype local readiness-check READINESS_ID --workspace EXTERNAL_WORKSPACE --json
prototype local readiness-status --workspace EXTERNAL_WORKSPACE --json
prototype local readiness-expire READINESS_ID --reason "End handoff window" --workspace EXTERNAL_WORKSPACE --json
```

Recovery plan IDs use `recovery-plan-001`; readiness IDs use `readiness-001`.
Creation captures the deployment history and immutable configuration. A plan
also captures the recorded predecessor, rollback target, previous configuration
and owner. The latest plan for each deployment is its active planning record;
older plans remain inspectable. Creating a new plan provides an explicit ownership
handoff and requires fresh verification. An active plan is not execution approval.

`reliability-check`, both status commands and plan inspection are read-only.
Reliability reports `passed`, `warnings`, and `blocked` findings for audit
completeness, health availability, rollback eligibility, recovery plan existence
and verification, governance, and incident consistency. Active incidents produce
a handoff warning; inconsistent histories block readiness. Missing or unverified
plans block readiness. Initial deployments explicitly target an empty rollback
reference and receive warnings, not invented previous configurations.

`recovery-verify` appends verification findings and a `passed` or `failed`
validation state to the plan's history. It checks the deployment history, owner,
rollback reference, previous configuration, rollback eligibility and governance.
It executes no recovery, rollback or configuration change. Repeating verification
preserves previous findings. Live checks always reassess prerequisites; an old
verification does not override current governance or eligibility failures.

`readiness-check` records `pending -> checking -> passed|failed`. Interrupted
checks can resume from `checking`. Any non-expired state can explicitly expire;
expired and completed checks cannot restart, so create a new readiness record.
The result is derived from live reliability findings, not selected by the caller.
Status separates the recorded result from `evidence_current`; changed evidence
sets `requires_new_check` without rewriting history. There is no automatic expiry
timer. Warnings do not block a pass, and a pass never activates a deployment.

All mutations accept `--actor` (default `developer`). Creation and expiry require
`--reason`; verification/check commands provide default reasons and accept an
override. Plan ownership defaults to `developer`. Successfully generated findings
exit zero even if blocked or failed; callers must inspect their contents.
Records stay in the external workspace's `optimization/reliability` directory.
See [Phase 50](phase50-developer-retrieval-deployment-reliability.md) for lifecycle,
evidence freshness, recovery verification and limitations.

### Developer continuity and disaster recovery preparation (Phase 51)

```text
prototype local disaster-create DEPLOYMENT_ID --owner "on-call" --type configuration_failure --reason "Prepare incident handoff" --workspace EXTERNAL_WORKSPACE --json
prototype local disaster-status --workspace EXTERNAL_WORKSPACE --json
prototype local disaster-inspect SCENARIO_ID --workspace EXTERNAL_WORKSPACE --json
prototype local disaster-check SCENARIO_ID --workspace EXTERNAL_WORKSPACE --json
prototype local disaster-test SCENARIO_ID --workspace EXTERNAL_WORKSPACE --json
prototype local disaster-retire SCENARIO_ID --reason "Exercise complete" --workspace EXTERNAL_WORKSPACE --json
prototype local continuity-status --workspace EXTERNAL_WORKSPACE --json
```

Create and verify a Phase 50 recovery plan first. `disaster-create` captures its
latest plan by default; `--plan-id` selects an existing plan for the same
deployment. IDs use `disaster-001` and `continuity-001`. Scenario types are
`configuration_failure` (default), `deployment_failure`, `rollback_unavailable`,
and `history_loss`. These labels describe the planning context; no fault is injected.

Creation atomically captures a scenario and continuity record with ownership,
recovery references, deployment/configuration dependencies, original deployment
and audit history, the recovery plan, and manual restoration steps. Repeat
`--step "Instruction"` to replace the default steps with local recovery knowledge.
Steps are stored as text and never executed. Old records remain available after
plan ownership handoffs; a superseded plan blocks the old scenario's live check.

Check, status, inspection, and continuity status are read-only. `disaster-check`
returns `passed`, `warnings`, and `blocked` findings for plan existence, rollback
target, deployment/configuration/audit histories, ownership, and live Phase 50
reliability/governance. Missing dependencies block validation while captured
knowledge remains inspectable. Initial deployments explicitly restore an empty
reference and receive a warning. Status separates recorded state from current
validation and `evidence_current`.

`disaster-test` records `planned -> testing -> validated|failed`. Failed and
validated scenarios can be retested; an interrupted `testing` state can resume.
Every completed attempt retains its date, scenario, owner, actor, findings and
validation results. The continuity history records the same attempt atomically.
Any non-retired scenario may retire; retired scenarios cannot restart.

Testing validates recovery references only. It does not execute rollback, restore
data, edit configuration, change deployment state, certify recovery success or
measure recovery time. A passed attempt never overrides governance. Mutations
accept `--actor` (default `developer`); creation and retirement require `--reason`,
and test attempts have an overridable default reason. Owner defaults to `developer`.
Successfully generated reports return zero even when blocked or failed; callers
must inspect their findings. All new records stay in the external workspace's
`optimization/continuity` journal. See [Phase 51](phase51-developer-retrieval-deployment-continuity.md).

### Developer recovery assurance and evidence (Phase 52)

```text
prototype local recovery-assurance SCENARIO_ID --workspace EXTERNAL_WORKSPACE --json
prototype local recovery-evidence SCENARIO_ID --workspace EXTERNAL_WORKSPACE --json
prototype local recovery-verify-history SCENARIO_ID --workspace EXTERNAL_WORKSPACE --json
prototype local recovery-history-analysis --workspace EXTERNAL_WORKSPACE --json
prototype local assurance-create SCENARIO_ID --owner "on-call" --reason "Capture recovery assurance" --valid-for-hours 24 --workspace EXTERNAL_WORKSPACE --json
prototype local assurance-verify ASSURANCE_ID --workspace EXTERNAL_WORKSPACE --json
prototype local assurance-expire ASSURANCE_ID --reason "End assurance window" --workspace EXTERNAL_WORKSPACE --json
```

The four `recovery-*` commands above are read-only. They do not create records or
run simulations. Assurance shows recorded checks, ownership, previous simulations,
evidence and current recovery readiness. Evidence separates available, missing
and expired evidence and links related records. History verification checks
previous simulations, evidence freshness, plan/reference validity, continuity
completeness and live governance. Analysis preserves earlier failed simulations
and assurance attempts alongside current unresolved findings and Phase 49 recovery
history. These are operational findings, not scores or proof of successful recovery.

Use `assurance-create` to create a pending record (`assurance-001`) for an existing
scenario. `assurance-verify` records `pending -> verifying -> passed|failed` and
captures immutable evidence in one outcome event. It requires a currently validated
scenario with a completed simulation that matches live checks. Missing evidence
produces warnings in evidence reports and prevents a passing verification.
Interrupted verification can resume from `verifying`; completed records require
a new assurance record. Any non-expired record can explicitly expire.

Evidence has an ID, type, availability status, source, check time, expiration time,
content snapshot and digest. The validity window defaults to 24 hours and accepts
integer `--valid-for-hours` values from 1 through 8760. Time expiry, source changes
or explicit expiry are reported without rewriting stored evidence. Current
readiness can therefore be `expired` while the recorded result remains `passed`.
Repeat read-only checks compare content independently of observation timestamps.

Run `disaster-test` explicitly when simulation prerequisites change, then create
and verify a new assurance record. A new verification does not inherit an old
record's expiration. Old failures/evidence remain inspectable. If live continuity
history becomes unreadable, known assurance records preserve their captured
evidence and report missing evidence warnings and verification blockers.

Mutations accept `--actor` (default `developer`). Creation/expiry require reasons;
verification supplies an overridable default reason. Owner defaults to `developer`.
Reports and completed verifications exit zero even when findings are blocked or
failed; callers must inspect the payload. New records live only in the external
workspace's `optimization/assurance` directory. No command executes recovery or
changes deployment, configuration, incident or simulation state. See
[Phase 52](phase52-developer-retrieval-recovery-assurance.md) for evidence semantics,
verification history, analysis and limitations.

### Continuous recovery assurance governance (Phase 53)

The read-only commands `assurance-status`, `assurance-history ASSURANCE_ID`,
`assurance-review ASSURANCE_ID`, `assurance-check` and `assurance-improvements`
report ownership, lifecycle, recurring deadlines, missing/stale evidence and
manual follow-up. `assurance-check` returns `passed`, `warnings`, `expired` and
`manual_actions`; it never records a check or executes recovery. All accept
`--workspace PATH` and `--json` and print JSON.

Register an existing Phase 52 assurance with `assurance-register ASSURANCE_ID
--owner OWNER --responsibility TEXT --every-hours 24 --reason TEXT`. Activate it
with `assurance-transition ASSURANCE_ID active --reason TEXT`, then explicitly
retain a completed same-scenario verification with `assurance-record-check
ASSURANCE_ID --verification-id VERIFIED_ASSURANCE_ID --reason TEXT`.

Governance has separate `draft`, `active`, `paused`, `expired` and terminal
`retired` states. Allowed transitions, examples and report semantics are in
[Phase 53](phase53-developer-retrieval-recovery-governance.md). Existing Phase 52
`assurance-expire` semantics are unchanged; governance expiration uses
`assurance-transition ID expired`.

Use `assurance-assign ID --owner OWNER --responsibility TEXT --reason TEXT` for
handoffs, `assurance-schedule ID --every-hours HOURS --reason TEXT` to change an
interval, and `assurance-note ID --kind review|improvement --note TEXT --reason
TEXT` to append notes. Mutations accept `--actor` (default `developer`).

Intervals are 1–8760 elapsed UTC hours. Initial activation is due immediately;
deadlines subsequently derive from the source verification time. Reusing a
verification ID cannot refresh a deadline. Create/verify a new Phase 52 assurance
for renewal and record its ID under the original governance anchor. A handoff
requires fresh verification completed after the ownership change. Notes alone
do not clear evidence or ownership findings.

History retains original evidence, content differences, ownership changes and
manual notes. Improvements separates recorded resolutions from current live
findings. Reports may identify overdue/expired evidence while stored governance
remains active, and exit zero with warnings. New journal records live only in
the external workspace's `optimization/recovery-governance` directory. There is
no automatic scheduling, remediation, recovery execution or deployment change.

### Assurance operations and review cycles (Phase 54)

Use `assurance-operations`, `assurance-findings`, `assurance-review-cycle
ASSURANCE_ID` and `assurance-coverage` for read-only visibility into review
operations, recurring findings, pending actions and coverage gaps. Coverage
includes scenarios without assurance and assurance records without governance;
it reports `covered`, `missing_owner`, `missing_schedule`, `expired` and
`manual_actions`, plus verified scenarios, missing references and diagnostics.
It produces no scores or rankings.

Create an operation with `assurance-operation-create ASSURANCE_ID --owner OWNER
--reason TEXT`. Explicitly record current findings with `assurance-operation-review
OPERATION_ID --reason TEXT`. Every review retains a snapshot and links new,
resolved, repeated and reopened findings. Repeated report reads never record
observations or resolve findings. Missing evidence prevents implicit resolution.

Use `assurance-operation-assign ID --owner OWNER --reason TEXT` for operations
ownership, `assurance-operation-note ID --note TEXT --reason TEXT` for manual
improvement notes, and `assurance-operation-transition ID STATE --reason TEXT`
for lifecycle changes. States are `open`, `reviewing`, `improved`, `accepted` and
terminal `closed`; see [Phase 54](phase54-developer-retrieval-recovery-operations.md)
for allowed transitions. Improved requires a recorded clean review that is still
current. Accepted records a human disposition without resolving open findings.

The existing `assurance-improvements` report retains all Phase 53 fields and adds
an `operations` object containing finding changes, notes and linked verification
history. Renew evidence through existing assurance/governance commands, then
explicitly record another operations review. Notes do not refresh evidence.

All commands accept `--workspace PATH` and `--json`; mutations require `--reason`
and accept `--actor` (default `developer`). Reports print JSON and exit zero with
findings; inspect the payload. Records live only in the external workspace's
`optimization/assurance-operations` directory. Nothing automatically repairs
references, executes recovery, or changes deployments or prior-phase journals.

### Recovery capability maturity (Phase 55)

Read-only commands are `maturity-status`, `maturity-history MATURITY_ID`,
`maturity-review AREA`, `maturity-readiness` and `maturity-plan`. They show stored
levels, ownership, capability evidence/gaps, historical changes and improvement
plans. Readiness returns `ready`, `needs_attention`, `missing_evidence` and
`manual_actions`; it does not change levels or produce scores or rankings.

Create a scoped area with `maturity-create AREA --assurance-id ASSURANCE_ID
--owner OWNER --reason TEXT` (repeat `--assurance-id` for multiple existing
governance anchors). Records start `initial`. Record a capability with
`maturity-assess MATURITY_ID CAPABILITY --reason TEXT`, optionally repeating
`--gap TEXT` and `--note TEXT`. Supported capabilities are `recovery-ownership`,
`recovery-evidence-validation`, `recovery-review-cycle` and
`recovery-improvement-planning`.

Use `maturity-transition MATURITY_ID LEVEL --reason TEXT` for explicit adjacent
changes through `initial`, `defined`, `managed`, `measured`, `improving`.
Promotions require current gap-free assessments for the cumulative capabilities
specified in [Phase 55](phase55-developer-retrieval-recovery-maturity.md).
`measured` is qualitative reviewed evidence, not a numerical metric. Assigning
ownership with `maturity-assign ID --owner OWNER --reason TEXT` requires the new
owner to reassess before promotion. Readiness checks all four capabilities and
can require attention even when the stored level remains high.

Create a plan with `maturity-plan-add ID --improvement TEXT --capability NAME
--reason TEXT`; repeat improvements/capabilities and optionally `--finding ID`.
Finding links must belong to the scoped assurance anchors. Use `--supersedes
PLAN_ID` to append a new version while preserving the old plan. Manually review
with `maturity-plan-review ID PLAN_ID reviewed|deferred|completed --note TEXT
--reason TEXT`. Completion requires a previously reviewed plan, current evidence
and resolved linked findings. Completed plans remain immutable.

All commands accept `--workspace PATH` and `--json`; mutations require `--reason`
and accept `--actor` (default `developer`). Reports print JSON and exit zero even
when gaps exist. Records live only in the external workspace's
`optimization/maturity` directory. Assessments retain evidence snapshots and
differences; no command rewrites previous plans, source evidence or prior journals,
executes recovery, or automatically promotes maturity.


### Phase 56: developer recovery assurance evolution

The external developer workspace now supports manual evolution lifecycle, impact
history and strategic planning. All reports below are read-only JSON and accept
`--workspace PATH` and `--json`:

- `prototype local evolution-status`
- `prototype local evolution-history EVOLUTION_ID`
- `prototype local evolution-impact EVOLUTION_ID`
- `prototype local evolution-review EVOLUTION_ID`
- `prototype local evolution-plan`

Review returns `ready`, `warnings`, `missing_evidence`, `manual_actions` and current
maturity impact. It never approves evolution, changes maturity or activates retrieval.
Status groups planned, active (reviewing/approved/implemented), verified and retired
work. Reports preserve historical evidence when current sources become unavailable.

Explicit mutations require `--reason` and accept `--actor`:

- `evolution-create CAPABILITY --owner OWNER [--change-type improvement]`
- `evolution-impact-add EVOLUTION_ID --capability CAPABILITY --maturity-id MATURITY_ID [--finding ID] [--note TEXT] [--risk TEXT]`
- `evolution-transition EVOLUTION_ID STATE --note TEXT`
- `evolution-plan-add EVOLUTION_ID --owner OWNER --improvement TEXT --milestone TEXT [--dependency CAPABILITY] [--supersedes PLAN_ID]`

Use these after `prototype local`, with `--workspace PATH`. Repeat impact list
flags and plan improvement/dependency/milestone flags as needed. Affected capabilities
use Phase 55 capability keys; linked findings must belong to the linked maturity
scope. Approval and verification require current gap-free impact evidence and no
unresolved risks. Implementation is an explicit human attestation. Plan revisions
append records and preserve earlier owners, dependencies and review milestones.
Dependencies and milestones are descriptive, not executable or scheduled.

See [Phase 56 evolution management](phase56-developer-retrieval-recovery-evolution.md)
for transitions, complete examples, evidence rules and limitations. This layer
creates no scores or research metrics and changes no earlier runtime authority.


### Phase 57: developer recovery strategic governance

Read-only JSON reports (use `--json` for a single JSON object) accept `--workspace PATH`:

- `prototype local governance-status`
- `prototype local governance-history GOVERNANCE_ID`
- `prototype local governance-review GOVERNANCE_ID`
- `prototype local governance-dependencies`
- `prototype local governance-plan-review`

These expose strategic objectives, owners, roadmap progress, capability/evolution
relationships, unresolved prerequisites, risks, review evidence and manual actions.
They never approve, schedule, prioritize, resolve dependencies or execute changes.

Explicit mutations after `prototype local` require `--reason` and accept `--actor`:

- `governance-create OBJECTIVE --owner OWNER --capability LABEL [--evolution-id ID] [--dependency REF] [--note TEXT] [--risk TEXT]`
- `governance-update GOVERNANCE_ID --objective TEXT --owner OWNER --capability LABEL` with the same optional list flags; lists replace the current revision.
- `governance-record-review GOVERNANCE_ID --note TEXT`
- `governance-transition GOVERNANCE_ID STATE --note TEXT`
- `governance-roadmap-add GOVERNANCE_ID --description TEXT --owner OWNER --target-period TEXT [--dependency REF]`
- `governance-roadmap-update GOVERNANCE_ID --roadmap-id ID --description TEXT --owner OWNER --target-period TEXT [--dependency REF]`
- `governance-roadmap-transition GOVERNANCE_ID STATE --roadmap-id ID --note TEXT`
- `governance-dependency-review GOVERNANCE_ID DEPENDENCY resolved|unresolved --note TEXT [--roadmap-id ID]`

Objective states are planned, reviewing, approved, active, completed and retired.
Roadmap states are proposed, scheduled, active, completed and deferred. Historical
revisions, ownership, periods, links and decisions remain in the external journal.
Approval, activation and completion require current recorded reviews. Completion
also requires verified evolution links and completed roadmap work. Internal
prerequisites use objective/roadmap IDs; other labels require explicit human review.
All list flags may be repeated. No source or runtime state changes automatically.

See [Phase 57 strategic governance](phase57-developer-retrieval-recovery-strategic-governance.md)
for transition rules, dependencies, workflow examples, review gates and limitations.


### Phase 58: developer strategic governance operations

Read-only operational reports accept `--workspace PATH` and `--json`:

- `prototype local governance-decisions`
- `prototype local governance-actions`
- `prototype local governance-exceptions`
- `prototype local governance-decision DECISION_ID`
- `prototype local governance-followup`
- `prototype local governance-close-check`

They expose decision ownership, actions, overdue work, exceptions, review history,
closure evidence and manual follow-up. Expiry/overdue detection writes no state.
Closure checks return passed, warnings, blocked and manual_actions, and never close
records automatically. No command changes retrieval behavior or prioritizes work.

Explicit mutations after `prototype local` require `--reason` and accept `--actor`:

- `governance-decision-create GOVERNANCE_ID --decision TEXT --owner OWNER`
- `governance-decision-review DECISION_ID --note TEXT [--evidence PATH] [--closure-reason TEXT]`
- `governance-decision-transition DECISION_ID STATE --note TEXT`
- `governance-decision-assign DECISION_ID --owner OWNER`
- `governance-action-add DECISION_ID --description TEXT --owner OWNER --due-date YYYY-MM-DD`
- `governance-action-transition DECISION_ID ACTION_ID STATE --note TEXT [--evidence PATH] [--closure-reason TEXT]`
- `governance-action-defer DECISION_ID ACTION_ID --until YYYY-MM-DD --note TEXT`
- `governance-action-assign DECISION_ID ACTION_ID --owner OWNER --due-date YYYY-MM-DD`
- `governance-exception-add DECISION_ID --description TEXT --owner OWNER --expires-at TIMESTAMP [--action-id ACTION_ID]`
- `governance-exception-transition DECISION_ID EXCEPTION_ID STATE --note TEXT [--evidence PATH] [--closure-reason TEXT]`
- `governance-exception-assign DECISION_ID EXCEPTION_ID --owner OWNER`

Evidence paths are relative to the external developer workspace; repeat `--evidence`
for multiple files. Completion/cancellation, exception mitigation/closure and decision
closure require evidence or a separate explicit manual closure rationale. Changed
or missing referenced files remain visible. A current human review of the related
strategic objective is required before deciding or closing. Documented deferrals
and accepted unexpired exceptions permit closure with warnings; they remain tracked
after closure. Strategic readiness warnings do not constitute strategic approval.

See [Phase 58 governance operations](phase58-developer-retrieval-recovery-governance-operations.md)
for lifecycles, time semantics, closure gates, handoffs, examples and limitations.

## Phase 59: end-to-end operational readiness

Readiness consolidates existing developer lifecycle checks without executing
retrieval, activation, deployment, recovery or governance closure. Reports are
read-only; mutations append only to `optimization/readiness` in an external
workspace. The recorded manual status and computed current readiness are shown
separately, with evidence freshness, blockers, warnings and manual decisions.

```powershell
prototype local readiness --workspace C:\DeveloperWorkspace --json
prototype local readiness-audit --deployment-id deployment-001 --decision-id decision-001 --workspace C:\DeveloperWorkspace --json
prototype local readiness-record-create deployment-001 --decision-id decision-001 --owner developer --reason "Consolidate lifecycle" --workspace C:\DeveloperWorkspace --json
prototype local readiness-transition retrieval-readiness-001 review_required --reason "Request review" --workspace C:\DeveloperWorkspace --json
prototype local readiness-review retrieval-readiness-001 --owner developer --note "Current evidence inspected" --reason "Manual review" --workspace C:\DeveloperWorkspace --json
prototype local readiness-transition retrieval-readiness-001 ready_for_manual_decision --reason "No blocking findings" --workspace C:\DeveloperWorkspace --json
prototype local readiness-transition retrieval-readiness-001 approved --confirm --reason "Manual approval" --workspace C:\DeveloperWorkspace --json
prototype local readiness-evidence retrieval-readiness-001 --reason "Capture existing record references" --workspace C:\DeveloperWorkspace --json
prototype local readiness-close retrieval-readiness-001 --owner developer --reason "Lifecycle reviewed" --confirm --workspace C:\DeveloperWorkspace --json
prototype local readiness-history retrieval-readiness-001 --workspace C:\DeveloperWorkspace --json
prototype local readiness-audit retrieval-readiness-001 --workspace C:\DeveloperWorkspace --json
prototype local readiness-followup retrieval-readiness-001 --owner developer --component evidence --manual-action "Renew evidence manually" --due-at "2027-01-01T00:00:00+07:00" --reason "Plan next review" --workspace C:\DeveloperWorkspace --json
prototype local readiness-followup-complete retrieval-readiness-001 retrieval-readiness-001-followup-001 --owner developer --note "Review completed manually" --reason "Complete follow-up" --workspace C:\DeveloperWorkspace --json
```

Create follow-ups before closure: closed readiness records are immutable. Closure
with open non-blocking follow-ups requires `--outstanding-reason "Owner will follow
up manually"`. This reason cannot waive blocking findings. Approval and closure
recheck the full chain and reject changed evidence. Return to `review_required`,
record a fresh owner review and evidence bundle, then make a new explicit decision.

Readiness states are `not_ready`, `review_required`, `ready_for_manual_decision`,
`approved` and `closed`. Closure requires approved state, current owner review,
current evidence bundle, validated recovery/assurance, reviewed governance,
completed or explicitly documented actions, documented exceptions and manual
confirmation. Audit outputs `passed`, `warnings`, `blocked`, `missing` and
`inconsistent`, plus traceable evidence references. Multiple governance decisions
require explicit selection. No numerical readiness/quality score is generated.

`readiness-evidence` can omit its ID and reason to append a bundle to the latest
existing readiness record. Create a record first when no readiness history exists.

See [Phase 59 operational readiness](phase59-developer-retrieval-operational-readiness.md)
for linkage verification, warning/blocking rules, freshness, isolation and limits.

## Phase 60: real repository pilot

Use authorized repositories and a fresh external developer workspace. Scan and
inspect before indexing, then run representative queries, trace, context analysis,
diagnose and developer evaluation/regression against declared navigation cases.
Keep all cases, indexes and operational evidence outside the project checkout.
No pilot source modification or research/benchmark registration is implied.

```powershell
$pilotWorkspace = 'C:\DeveloperPilot\workspace'
$pilotRepository = 'C:\AuthorizedRepositories\python-app'
$pilotCases = 'C:\DeveloperPilot\cases.json'
prototype local scan $pilotRepository --workspace $pilotWorkspace
prototype local inspect $pilotRepository --workspace $pilotWorkspace
prototype local index $pilotRepository --workspace $pilotWorkspace
prototype local trace "Where is configuration loaded?" --repository $pilotRepository --workspace $pilotWorkspace --json
prototype local evaluate $pilotRepository --cases $pilotCases --stability --explain --workspace $pilotWorkspace --json
prototype local regression $pilotRepository --cases $pilotCases --baseline pilot-v1 --create-baseline --workspace $pilotWorkspace --json
```

Replace the example paths with authorized local inputs and supply the pinned
developer model cache. Use a new baseline name for a new immutable capture.

`local diagnose` distinguishes an existing file absent from results from a file
deleted since indexing. Inspect reports token-limit exclusions; an indexed
repository can still contain unsearchable symbols. TypeScript-only repositories
cannot complete Python indexing or retrieval.

Optimization validation runs checks without approving a candidate. Failed gates
require manual investigation or rejection; do not bypass them to demonstrate a
deployment. Promotion requires the existing current approval and evidence. Do not
activate configurations, deploy, recover or close readiness automatically.
Readiness reports can exit zero while reporting blockers. Evidence capture,
follow-up and closure require an existing eligible readiness record; missing
history is not repaired by these commands.

Developer evidence digest verification preserves the existing canonical SHA-256
contract while hashing incrementally. Large lifecycle histories still need memory
for loading and replay. Run broad validation suites sequentially on constrained
hosts; retain terminal results and distinguish resource failures from gate findings.

See [Phase 60 pilot findings and limitations](phase60-developer-real-repository-pilot.md)
for real retrieval evidence, the diagnostic correction, failed candidate, and the
distinction between synthetic lifecycle coverage and real-pilot closure.

## Phase 61: developer retrieval candidate remediation

Phase 61 continues from the immutable Phase 60 failed candidate. It addresses
bounded configuration context, cross-result duplicate suppression, conservative
relationship resolution, explicit context diagnostics, and reduced copying during
developer evidence replay. It changes only developer-local retrieval/index behavior;
it does not alter research retrieval, chunking contracts, benchmark artifacts,
Humanize, or release files.

Oversized configuration chunks are measured with the pinned developer tokenizer
before embedding. The index retains whole-line excerpts within the existing
256-token input budget where possible, preserves source symbol identity, and records
original and retained ranges/hashes plus truncation or omission reason. `inspect`
reports bounded chunks separately from excluded chunks. Query diagnostics separate
selected context, relationship-expanded context, duplicate suppression, unresolved
relationships, and oversized/bounded/omitted context. A file or symbol absent from
the final context remains explicit evidence, not an inferred deletion.

Duplicate checks span all direct results and all caller/callee/importer/dependency
expansion paths. Each source identity or identical-content digest is emitted at most
once; relationship references remain available when duplicate context is suppressed.
Inter-file graph links require matching module/import evidence, same-file calls
require an unambiguous target, and ambiguous/unresolved same-name symbols are
reported rather than guessed. Graph expansion remains static source evidence, not
proof of runtime execution.

Phase 61 writes indexes under the developer-only `indexes/REPOSITORY/v4/` namespace
and records that schema in inspection/query diagnostics. Phase 60 v2 and interim v3
snapshots are not loaded as v4; run `prototype local index` to build a compatible developer index.
The v6 developer ranking contract also avoids relationship boosts based only on
generic one-token overlap; exact qualified-symbol or multiple specific-term evidence
is required.
No generated index or candidate/review/evidence record belongs in the source tree.

Create a successor using `prototype local optimize create` with new ID, owner,
purpose, affected cases, source evidence, remediation description, validation
requirements, and `--supersedes phase60-config-context`. The failed original and its
pending review are retained unchanged. Re-run regression and candidate validation
with the same authorized pilot repositories and declared cases. Validation reports
regression, completeness, declared-context, duplicate-context, stability, ranking,
trace and diagnose gates. A candidate with a failed required gate is not eligible
for review. The Phase 61 successor passed the recorded pilot gates and has a new
pending review; human approval remains outstanding. Review items retain candidate
lineage and validation evidence. No candidate is automatically approved, activated, deployed, rolled back,
recovered, or used to close readiness.

The TypeScript-only pilot remains explicitly unsupported by this Python indexer.
Do not describe its scan/query rejection as successful cross-language retrieval.
See [Phase 61 remediation and re-validation](phase61-developer-retrieval-candidate-remediation.md)
for the measured pilot results, gate outcomes, limitations, and preservation checks.
