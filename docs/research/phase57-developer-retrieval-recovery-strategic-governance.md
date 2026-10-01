# Phase 57 - Developer Mode Retrieval Recovery Assurance Strategic Governance

## Baseline and scope

Phase 56 provides capability evolution lifecycle, append-only impact evidence,
evolution reviews and strategic plans. Phase 55 supplies maturity assessments and
readiness, while earlier assurance operations preserve findings and ownership.
The remaining gaps are explicit long-term objectives, roadmap ownership, linked
improvement dependencies, strategic review history and visible planning decisions.

This phase adds a developer-only strategic governance layer. It does not change
research evaluation or retrieval methodology, benchmark datasets, Humanize, frozen
release artifacts, research snapshots or v0.1.1 behavior. It introduces no developer
performance scores, productivity metrics, rankings or automatic prioritization.

The starting checkout contained uncommitted Phase 46-56 work. All 292 tracked and
nonignored untracked files were inventoried by SHA-256 outside the checkout in
`C:/Apps/Temp/Phase57/baseline.json`; git status and the tracked diff path list were
saved alongside it. The baseline diff contained only the existing CLI, developer
tests and CLI guide edits. Protected research paths were unchanged. All nine
Phase 56 regression tests passed in 70.786 seconds with zero skips, failures or
errors (`baseline-tests.log`). The tag object was and must remain
`05688504f74ad51230ee1566fad8cda0f1b1ad97`.

## Strategic governance records

`src/developer/strategic_governance.py` stores independent events in
`<external developer workspace>/optimization/strategic-governance`. The existing
Phase 41 governance module and Phase 53 recovery governance are unchanged.
Events have a schema version, mode, timestamp, actor, reason, ordered sequence and
previous-event SHA-256 digest. Replay validates the chain and lifecycle. Exclusive
atomic publication rejects concurrent appends without overwriting previous files.
Read-only reports do not create a workspace or journal.

Records contain `governance_id` (for example `governance-001`), `objective`, `owner`,
`status`, `created_at`, `updated_at`, `history`, `capabilities`, `evolution_ids`,
`dependencies`, `review_notes`, `risks`, `reviews`, `dependency_reviews`, and `roadmap`.
Capabilities are nonempty descriptive labels, such as `evidence-validation` or a
Phase 55 capability key. Evolution links must exist and their creation/update
snapshots are retained in the objective history. Empty evolution links are allowed
for early planning but block approval until the proposal is sufficiently defined.

| Current state | Allowed next states |
| --- | --- |
| planned | reviewing, retired |
| reviewing | planned, approved, retired |
| approved | reviewing, active, retired |
| active | reviewing, completed, retired |
| completed | retired |
| retired | None |

Every transition requires a note, actor and reason. Objective revisions replace
the current description, owner, capabilities, links, dependencies, notes and risks;
earlier values remain in history. Revisions are allowed only while planned or
reviewing. Return to reviewing before changing approved or active scope. Completed
and retired objectives require a new record for follow-up work.

## Review evidence and manual decisions

`governance-review` is read-only. `governance-record-review` explicitly appends a
human review note and immutable evidence snapshot. Snapshots include the objective,
roadmap, dependency resolution, linked evolution histories and live evolution
reviews. Evolution evidence in turn exposes maturity and assurance evidence gaps.
Missing source journals are reported without losing historical strategic evidence.

Approval, activation and completion each require the most recent recorded review
to match current evidence exactly. Any objective, roadmap, linked evolution or
prerequisite change can make that review stale. A new review is needed after
approval before activation, because the objective state changed. Recorded reviews
may retain gaps for investigation; merely recording one never clears those gaps.

Approval and activation require at least one roadmap item and linked evolution,
no current evidence gaps, no declared or source risks, and resolved objective
prerequisites. Linked evolution work may still be planned. Roadmap dependencies
remain visible and block the affected item, but do not prevent approval of the
overall plan. Completion additionally requires all linked evolutions to be verified,
all roadmap items completed, and no unresolved roadmap dependencies. Deferred work
therefore prevents objective completion. Retired evolution links require review
and replacement, rather than being treated as current completion evidence.

Readiness names a possible manual transition. It performs no approval, evolution
transition, maturity change, recovery action or retrieval activation. Later source
drift does not rewrite stored completion; reports expose it for human follow-up.

## Roadmap management

Roadmap items contain `roadmap_id` (workspace-wide `roadmap-001`), linked
`governance_id`, description, owner, target period, dependencies, status, creation
and update times, dependency reviews and append-only history.

| Current state | Allowed next states |
| --- | --- |
| proposed | scheduled, deferred |
| scheduled | proposed, active, deferred |
| active | completed, deferred |
| deferred | proposed, scheduled |
| completed | None |

Creation starts proposed. Scheduling is an explicit record of human intent; target
periods are nonempty descriptive text and trigger no timer or automatic scheduling.
Owner, description, target period and dependencies may be revised while proposed,
scheduled or deferred. Defer active work before revising its plan. Completed items
are immutable. Reports retain insertion order and never prioritize or reorder work.

Starting or completing a roadmap item requires an active objective, resolved item
dependencies and current gap-free objective evidence. Roadmap completion records
human-confirmed progress; it does not implement the linked evolution. Each event
retains previous and current roadmap state, actor, note/reason and timestamp.

## Dependencies

Objective dependencies beginning `governance-` reference existing objectives;
roadmap dependencies beginning `roadmap-` reference existing roadmap items.
Cross-kind references and unknown reserved IDs are rejected. Self-dependencies
and cycles in these explicit graphs are rejected before publication. Internal
prerequisites require the target record to be completed and its declared upstream
prerequisites resolved. Retirement or reopening of prerequisite work becomes
visible in later reports. Completion is historical evidence, not an ongoing audit
of all source evidence belonging to unrelated prerequisite objectives.

Other dependency strings are external prerequisite labels, for example
`verification-scheduling`. They remain unresolved until explicitly reviewed with
`governance-dependency-review ... resolved --note ...`. A later explicit unresolved
review reopens them. These attestations have no automatic expiry; operators must
revisit them when circumstances change. They cannot override internal record
states. Reports never resolve dependencies or reorder roadmap items.

Dependency reports show each prerequisite, its owning item, resolution, unresolved
upstream prerequisites, capability/evolution relationships, blocked entries and
manual actions. Direct graph-cycle validation cannot prove that a human plan is
feasible; review cross-objective sequencing and external constraints manually.

## CLI reports

All commands accept `--workspace PATH` and `--json`. Default output includes the
developer notice followed by JSON; `--json` emits one JSON object with the notice.

| Read-only command | Result |
| --- | --- |
| `prototype local governance-status` | Objectives, active objectives, roadmap items, owners and states |
| `prototype local governance-history GOVERNANCE_ID` | Objective revisions, decisions, evolution snapshots, reviews and roadmap history |
| `prototype local governance-review GOVERNANCE_ID` | Current objective, dependencies, risks, missing evidence, readiness, progress and manual actions |
| `prototype local governance-dependencies` | dependencies, blocked, manual_actions and capability relationships |
| `prototype local governance-plan-review` | ready, warnings, risks, manual_actions, active objectives, roadmap progress and improvement history |

Reports exit zero even with gaps; inspect their result fields. Unknown IDs and
corrupt journals fail through the existing CLI error handling. Empty workspace
status/dependency/plan-review reports contain empty lists and create no journal.
Plan review retains historical objectives as well as explicitly listing active ones.

## Explicit objective workflow

Mutations require `--reason` and accept `--actor` (default `developer`).

```powershell
prototype local governance-create "Improve recovery verification reliability" --owner maintainer --capability recovery-ownership --evolution-id evolution-001 --reason "Define long-term direction" --workspace C:\DeveloperWorkspace
prototype local governance-roadmap-add governance-001 --description "Review ownership procedure" --owner maintainer --target-period "2027 Q1" --reason "Plan review milestone" --workspace C:\DeveloperWorkspace
prototype local governance-transition governance-001 reviewing --note "Begin strategic review" --reason "Review proposal" --workspace C:\DeveloperWorkspace
prototype local governance-review governance-001 --workspace C:\DeveloperWorkspace
prototype local governance-record-review governance-001 --note "Evidence and dependencies inspected" --reason "Record manual review" --workspace C:\DeveloperWorkspace
prototype local governance-transition governance-001 approved --note "Direction approved manually" --reason "Approval decision" --workspace C:\DeveloperWorkspace
prototype local governance-record-review governance-001 --note "Recheck approved plan before activation" --reason "Activation review" --workspace C:\DeveloperWorkspace
prototype local governance-transition governance-001 active --note "Begin planned governance work" --reason "Manual activation" --workspace C:\DeveloperWorkspace
```

The evolution record and its current impact evidence must already exist. Required
source corrections use existing evolution, maturity and assurance workflows.
`governance-update GOVERNANCE_ID --objective TEXT --owner OWNER --capability LABEL`
uses the same optional repeated `--evolution-id`, `--dependency`, `--note`, and
`--risk` flags as creation. Updates replace these lists; omitted optional lists
become empty. Previous objective revisions and linked snapshots remain in history.

## Explicit roadmap and dependency workflow

```powershell
prototype local governance-roadmap-transition governance-001 scheduled --roadmap-id roadmap-001 --note "Schedule agreed manually" --reason "Roadmap decision" --workspace C:\DeveloperWorkspace
prototype local governance-roadmap-transition governance-001 active --roadmap-id roadmap-001 --note "Start reviewed work" --reason "Roadmap decision" --workspace C:\DeveloperWorkspace
prototype local governance-roadmap-transition governance-001 completed --roadmap-id roadmap-001 --note "Work confirmed outside this workflow" --reason "Record completion" --workspace C:\DeveloperWorkspace
```

`governance-roadmap-update GOVERNANCE_ID --roadmap-id ROADMAP_ID --description TEXT
--owner OWNER --target-period TEXT [--dependency REF]` appends a plan revision.
Creation and update accept repeated dependencies. To review an external prerequisite:

```powershell
prototype local governance-dependency-review governance-001 verification-scheduling resolved --note "Scheduling prerequisite checked externally" --reason "Record manual evidence" --workspace C:\DeveloperWorkspace
```

The dependency must already be declared. Add `--roadmap-id ROADMAP_ID` to review an
item's prerequisite. Use `unresolved` to reopen it. After all evolution records are
verified and roadmap work completed, record a fresh strategic review, then explicitly
transition the objective to completed. All earlier records remain unchanged.

## Limitations and preservation

This is local planning and accountability, not proof of recovery success. Owners
and actors are attribution, not authenticated identities. Hash chains detect broken
history but cannot prevent rewriting an entire local chain. Serialize related
mutations for consistent cross-journal observations. There is no scheduler,
automatic approval, prioritization, dependency resolution or execution. No developer
repositories are added to research snapshots. Existing runtime authority is unchanged.

Tests use external temporary workspaces. Logs, baseline inventories and preservation
evidence are retained in `C:/Apps/Temp/Phase57`.

## Validation results

Nine new regression tests cover strategic lifecycle and completion gates, invalid
transitions, objective revisions, linked evolution history, roadmap revisions and
deferrals, dependency cycles and manual reopening, stale reviews, unavailable
sources, evolution/maturity/assurance compatibility, all CLI report and mutation
routes, read-only reports, journal corruption, atomic publication failure and
workspace isolation. The final targeted run passed all nine tests in 90.730 seconds
with no skips, failures or errors (`strategic-final.log`, exit 0). The initial
eight-test run also passed before the final dependency coverage was added.

`python -m unittest tests.test_developer_mode -v` passed all 186 tests in
753.159 seconds with zero skips, failures or errors (`focused.log`, exit 0).
Required suites run sequentially under Python 3.14.7. `EMBEDDING_MODEL_CACHE`
is unset; no dependency or environment changes were made.

`python -m unittest discover -s tests -v` ran 330 tests in 704.970 seconds:
328 passed, two skipped, zero failures or errors (`full.log`, exit 0). The skips
are real offline embedding repeatability and embedding/index/query integration,
which require `EMBEDDING_MODEL_CACHE`. Both suites emitted the existing Transformer
`cache_dir` deprecation warning. No environment repairs were required.

The final SHA-256 comparison preserves 289 of the 292 baseline files byte for byte.
Only `src/cli.py`, `tests/test_developer_mode.py` and `docs/research/prototype-cli.md`
changed. The only new files are `src/developer/strategic_governance.py` and this
phase document. Earlier phase modules and documents, benchmark datasets, Humanize,
research evaluation/retrieval paths, research snapshots and frozen release
artifacts remain unchanged. The `v0.1.1` tag still resolves to
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. `git diff --check` passes.
No generated strategic governance records exist inside the source checkout.
External `preservation.json`, `test-results.json`, baseline inventories and test
logs retain the verification evidence.
