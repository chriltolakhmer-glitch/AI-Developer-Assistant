# Phase 53 — Developer Mode Retrieval Deployment Recovery Governance

## Baseline and scope

Phase 52 already supplies assurance lifecycle management, immutable evidence,
verification, expiration detection, recovery history analysis and continuity
records. The missing governance capabilities were recurring check schedules,
explicit responsibility handoffs, comparisons between checks and persistent
improvement notes. This phase adds those capabilities exclusively to developer
workspaces. It does not execute recovery or alter deployment authority.

The starting checkout contained uncommitted Phase 46–52 work: changes to the CLI,
developer tests and CLI guide, plus configuration/deployment/operations/reliability/
continuity/assurance modules and their phase documents. These were preserved.
A SHA-256 inventory was saved outside the checkout before implementation.
Baseline `python -m unittest tests.test_developer_mode -v` passed all 141 tests
in 375.686 seconds, with no skips, failures or errors (`phase53-baseline-tests.log`).
The starting `v0.1.1` tag object was
`05688504f74ad51230ee1566fad8cda0f1b1ad97`.

## Governance model

`src/developer/recovery_governance.py` stores a separate append-only journal in
the external workspace's `optimization/recovery-governance` directory. Numbered
events contain actor, reason, timestamp, sequence and previous-event digest.
Replay validates the chain and lifecycle; exclusive atomic publication prevents
overwriting an existing event. The source/research workspace guards apply before
reads and writes. Reports do not create workspace directories or journal events.

Each record is anchored to an existing Phase 52 `assurance_id` and its
`scenario_id`. It contains `owner`, `responsibility`, `status`,
`verification_schedule`, `interval_hours`, `last_check`, `next_check`, `history`,
`review_notes`, `verification_history` and `improvement_notes`. The original
assurance snapshot is retained. Governance states are independent of the
Phase 52 pending/verifying/passed/failed/expired verification states.

| Current state | Allowed next states |
| --- | --- |
| draft | active, retired |
| active | paused, expired, retired |
| paused | active, expired, retired |
| expired | active, retired |
| retired | none |

Duplicate registration, same-state transitions, illegal transitions and changes
to retired records are rejected. Activation initially makes the first check due
immediately. Pausing retains deadlines and history. Reactivation does not refresh
old evidence or postpone an existing deadline. Time-based findings never silently
change the stored lifecycle state.

## Ownership and recurring verification

Registration and assignment require a nonempty owner and responsibility. Handoffs
retain prior ownership in history and create an ownership review finding until a
verification completed after the handoff is explicitly recorded. Review notes
document discussion; they cannot make stale evidence current.

Schedules use elapsed UTC intervals of 1–8760 integer hours, with no background
scheduler. `last_check` is the source evidence check time, not the later time at
which someone records it. `next_check` is that check time plus the interval.
Changing a schedule recomputes the deadline from the retained check time.
At the exact deadline, a check is overdue. Evidence also has its own independent
Phase 52 expiry; either limit can require a fresh check sooner.

An explicit record-check requires active governance and a completed Phase 52
verification for the same scenario. Each verification ID can be used only once
per governance record; its check time must be newer than the previous one and
cannot be in the future. Both passed and failed outcomes are retained. Recording
old or failed evidence does not imply readiness: current findings remain visible.
Source assurances and their immutable evidence are never rewritten by governance.

## Commands and reports

All commands accept `--workspace PATH` and `--json`. Reports always print JSON.
The five required reports are read-only:

| Command | Output |
| --- | --- |
| `prototype local assurance-status` | Records, ownership, last/next checks, active IDs and expired/overdue IDs |
| `prototype local assurance-history ASSURANCE_ID` | Lifecycle, responsibility changes, verification snapshots, evidence differences and notes |
| `prototype local assurance-review ASSURANCE_ID` | Stored state, missing evidence, stale checks, current findings and manual actions |
| `prototype local assurance-check` | `passed`, `warnings`, `expired`, `manual_actions` across all records |
| `prototype local assurance-improvements` | Previous findings, recorded resolutions, unresolved findings, live findings and manual notes |

Reports inspect evidence availability, freshness, prior completion, owner,
responsibility, schedule and live recovery references. They distinguish missing
source histories from retained snapshots. The `expired` list includes overdue or
stale evidence as well as explicitly expired governance; consult the stored
`status` to distinguish these. Draft, paused and retired records remain visible
with lifecycle findings. An empty workspace returns empty collections.

Explicit mutations require `--reason` and accept `--actor` (default `developer`):

```powershell
prototype local assurance-register assurance-001 --owner maintainer --responsibility "Review recovery evidence" --every-hours 24 --reason "Start governance" --workspace C:\DeveloperWorkspace
prototype local assurance-transition assurance-001 active --reason "Begin recurring review" --workspace C:\DeveloperWorkspace
prototype local assurance-record-check assurance-001 --verification-id assurance-001 --reason "Record completed Phase 52 check" --workspace C:\DeveloperWorkspace
prototype local assurance-assign assurance-001 --owner next-maintainer --responsibility "Maintain rollback evidence" --reason "Handoff" --workspace C:\DeveloperWorkspace
prototype local assurance-schedule assurance-001 --every-hours 12 --reason "Increase review frequency" --workspace C:\DeveloperWorkspace
prototype local assurance-note assurance-001 --kind review --note "Handoff reviewed; fresh verification required" --reason "Ownership review" --workspace C:\DeveloperWorkspace
prototype local assurance-note assurance-001 --kind improvement --note "Document missing recovery reference" --reason "Manual follow-up" --workspace C:\DeveloperWorkspace
```

For renewal, explicitly run the relevant existing `disaster-test` if needed,
then `assurance-create SCENARIO_ID` and `assurance-verify NEW_ASSURANCE_ID`.
Record the new ID with `assurance-record-check ORIGINAL_ASSURANCE_ID
--verification-id NEW_ASSURANCE_ID --reason ...`. The original governance anchor
stays stable. Existing `assurance-expire` still expires Phase 52 evidence; use
`assurance-transition ID expired` to expire governance itself.

## Improvement history and limitations

Each recorded check captures stable finding keys, evidence content differences,
its source verification, owner and responsibility. `resolved_findings` compares
consecutive explicitly recorded evidence findings; all earlier findings remain
in history. Latest recorded unresolved findings and current live findings are
separate fields. Manual improvement notes carry event sequence, actor and reason
and do not automatically resolve findings. Ownership and schedule findings are
live governance findings, not recorded evidence-resolution claims.

There is no automated remediation, notification service, wall-clock scheduler,
recovery execution, developer scoring, productivity metric or research quality
metric. Actors/owners are local attribution, not authenticated identities. Hash
chains detect broken history, not malicious rewriting of the entire local chain.
Serialize related mutations to obtain a consistent view across journals. A
passing check is reference/evidence assurance, not proof that real recovery will
succeed. Reports return exit zero even when warnings exist; inspect JSON fields.

Research evaluation/retrieval, benchmark datasets, Humanize, frozen release
artifacts and research snapshots are outside the implementation scope. No
developer repository is added to a research snapshot.

## Validation and preservation

Nine governance regressions cover lifecycle, append-only history, ownership,
handoff freshness, recurring schedules, exact expiry boundaries, replay rejection,
fresh evidence renewal, missing history, evidence differences, improvement
resolution, CLI registration/mutations/read-only reports, invalid sources, journal
corruption, atomic publication failure and external workspace isolation. Tests
use temporary external workspaces and retain the prior Phase 52 regressions.

The initial eight-test governance run passed in 40.101 seconds with no skips,
failures or errors (`phase53-governance-tests.log`). A ninth test was added to
exercise CLI registration and ensure evidence predating a handoff cannot clear
the ownership review finding merely by being recorded later.

The final targeted run passed all nine tests in 54.231 seconds with no skips,
failures or errors (`phase53-governance-final.log`). Validation uses Python
3.14.7; the focused and full suites run sequentially, with logs in the system
temporary directory outside the checkout.

`python -m unittest tests.test_developer_mode -v` passed all 150 tests in
545.401 seconds with no skips, failures or errors and exit status 0
(`phase53-focused.log`).

`python -m unittest discover -s tests -v` ran 294 tests in 519.899 seconds:
292 passed, 2 skipped, zero failures or errors, exit status 0
(`phase53-full.log`). Both skips require `EMBEDDING_MODEL_CACHE`, for real offline
inference and embedding/index/query integration. Both suites emitted the existing
Transformer `cache_dir` deprecation warning. No environment repairs or dependency
changes were needed.

`git diff --check` passed. Final SHA-256 comparison with the starting inventory
found changes only to `src/cli.py`, `tests/test_developer_mode.py` and
`docs/research/prototype-cli.md`, plus new `src/developer/recovery_governance.py`
and this document. Earlier phase modules and documents retain their original
bytes. Benchmark datasets, Humanize, research evaluation/retrieval, snapshots and
frozen release artifacts are unchanged. `v0.1.1` still resolves to
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. No generated governance journal
directory exists inside the source checkout.
