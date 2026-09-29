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

The immutable v0.1.1 release tag remains unchanged. The Phase 28 source tree adds a `local` command group for personal repositories without changing research data, retrieval methodology, Humanize artifacts, benchmark files, or research run records.

**This is a local developer workspace. Results are not benchmark results.**

| Research commands | Personal developer commands |
|---|---|
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

### `prototype local scan|inspect|index|query|trace|diagnose|analyze-context|compare|demo`

For a developer's existing local Python repository, use the separate developer workspace:

```powershell
$repo = 'C:\work\my-application'
prototype local scan "$repo"
prototype local inspect "$repo" --json
prototype local inspect "$repo" --changes --json
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

`scan`, `inspect`, `index`, `query`, `trace`, `diagnose`, `analyze-context`, `compare`, `explain`, and `evaluate` accept `--json`. Full diagnostics also stay
in `WORKSPACE/runs/RUN_ID/results.json`. Query records include raw lexical/vector
contributions, the base fused score, metadata/test/container/diversity factors,
final score and source provenance. These post-release developer preferences do
not modify research scoring. Overlapping source ranges are suppressed; repeated
files receive a soft diversity discount. Explicit test queries retain test results
without the implementation preference penalty.

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
