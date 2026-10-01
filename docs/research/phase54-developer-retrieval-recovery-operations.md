# Phase 54 — Developer Mode Retrieval Recovery Assurance Operations

## Baseline and scope

Phase 53 provides assurance lifecycle management, ownership and responsibility
records, verification schedules, read-only reviews, stale evidence detection and
improvement history. Operational gaps remained: coverage of ungoverned scenarios,
repeated unresolved findings across reviews, explicit review cycles and linked
manual improvement actions. This phase adds those capabilities without changing
research evaluation, retrieval methodology, benchmark data, Humanize or releases.

The initial checkout retained uncommitted Phase 46–53 work: CLI, CLI guide and
developer test changes plus the earlier developer modules and phase documents.
These changes were preserved. A SHA-256 inventory of tracked and nonignored
untracked files was saved outside the checkout before implementation. The nine
Phase 53 governance regressions passed in 57.188 seconds, with zero skips,
failures or errors (`phase54-baseline-tests.log`). The starting tag object for
`v0.1.1` was `05688504f74ad51230ee1566fad8cda0f1b1ad97`.

## Operations and lifecycle

`src/developer/assurance_operations.py` maintains a separate external workspace
journal at `optimization/assurance-operations`. Events have schema version,
sequence, previous-event digest, actor, reason and UTC timestamp. Validated replay
reconstructs operations and findings. Exclusive atomic publication prevents a
concurrent append from replacing an existing event. The source and research path
guards run before reads and writes. Reports never create directories or events.

Each operation contains `operation_id` (`operation-001`), `assurance_id`, `owner`,
`status`, `created_at`, `last_reviewed`, `history`, `reviews`, `improvement_notes`
and a retained governance snapshot. Creation requires an existing Phase 53
governance anchor. Multiple operations can reference one assurance. An operation's
owner is its issue/review owner; assigning it does not rewrite governance or
recovery-plan ownership.

| Current state | Allowed transitions |
| --- | --- |
| open | reviewing |
| reviewing | improved, accepted |
| improved | reviewing, closed |
| accepted | reviewing, closed |
| closed | none |

Explicitly recording a review moves any nonclosed operation into `reviewing`,
including another review while already reviewing. A transition alone does not
capture a review or update `last_reviewed`. Both outcome states require a recorded
review. `improved` additionally requires no findings in the latest recorded
review, no current governance findings, and unchanged governance history since
that review. A clean historical review cannot override newly expired evidence.

`accepted` records a manual decision to accept the observed issues; it does not
resolve them or assert readiness. Closing an accepted operation leaves its open
findings visible. Closed operations are immutable; create another operation for
later work. Invalid transitions, blank attribution/notes and unknown IDs are
rejected before journal publication.

## Findings and review cycles

Only `assurance-operation-review` records findings. It captures the current
Phase 53 review, including governance and verification history, in one event.
Reports inspect live state but never persist an observation or resolve a finding.

Findings are scoped by assurance and stable governance key. Each contains
`finding_id` (for example `assurance-001:stale_evidence:recovery_plan`),
`assurance_id`, `description`, `severity`, `first_seen`, `last_seen`, `status`,
`related_operations` and append-only observations. They are shared across review
operations for the same anchor and remain distinct between different anchors.
Severity is a category: high for failed verification, unavailable histories or
blocked recovery references; info for lifecycle findings; warning for other
findings. These categories do not score or rank developers.

New findings start open. A later explicit complete review can mark findings
absent from that review resolved. A later observation reopens them while retaining
first-seen time and all prior observations. `last_seen` advances only when the
finding is present. Incomplete reviews with missing evidence or unavailable
histories retain older unresolved findings; absence under those conditions is
not treated as resolution. Failure to load governance rejects a mutation while
read-only review-cycle reports retain prior review snapshots and report the loss.

Repeated findings mean the same issue was observed in multiple manually recorded
reviews. They do not prove independent incidents. Reopened findings distinguish
recurrence after a recorded resolution. Trend visibility is chronological review
history and new/resolved/repeated/reopened finding sets, without rates, scores,
rankings or productivity measurements.

## Read-only commands

All commands accept `--workspace PATH` and `--json`; output is JSON.

| Command | Output |
| --- | --- |
| `prototype local assurance-operations` | All operations, active operations, owners, recorded review state and open findings |
| `prototype local assurance-findings` | Active, resolved and recurring findings with assurance and operation links |
| `prototype local assurance-review-cycle ASSURANCE_ID` | Previous reviews, live current findings, pending manual actions and improvement notes |
| `prototype local assurance-coverage` | Covered/uncovered rows, missing owners/schedules, verified scenarios, expired evidence, missing references and manual actions |
| `prototype local assurance-improvements` | Existing Phase 53 fields plus operations reviews, finding changes, notes and linked verification snapshots |

`assurance-improvements` preserves the Phase 53 report mode and fields, adding an
`operations` object for Phase 54 information. Earlier governance APIs and journals
retain their behavior. An operations report describes persisted review knowledge;
use review-cycle or coverage for live readiness changes. Reports exit zero even
when findings exist; callers must inspect the JSON.

## Coverage semantics

Coverage enumerates governance anchors, unregistered Phase 52 assurance records,
and disaster scenarios that have no assurance at all. Verification IDs already
linked to a governance anchor are not counted again as ungoverned renewals.
`missing_owner` means missing assurance governance accountability, even if a
scenario or one-time Phase 52 check has an owner. `missing_schedule` includes
unregistered records and draft records without an active deadline.

`covered` requires a governance owner/responsibility, active recurring schedule,
current completed verification, fresh evidence and valid live recovery references
without current governance findings. `verified_scenarios` identifies scenarios
with currently available passing evidence and valid references; they can still
lack governance coverage. `expired` includes overdue governance or stale/expired
evidence and does not change stored states. Missing reference findings and
unreadable source journals produce manual actions. Unreadable dependencies prevent
positive coverage claims; diagnostics distinguish that condition from an empty
workspace. No coverage percentage or comparative ranking is generated.

## Manual improvement workflow

Mutations require `--reason` and accept `--actor` (default `developer`):

```powershell
prototype local assurance-operation-create assurance-001 --owner operator --reason "Start review cycle" --workspace C:\DeveloperWorkspace
prototype local assurance-operation-review operation-001 --reason "Capture current findings" --workspace C:\DeveloperWorkspace
prototype local assurance-operation-assign operation-001 --owner next-operator --reason "Review handoff" --workspace C:\DeveloperWorkspace
prototype local assurance-operation-note operation-001 --note "Refresh rollback evidence before next review" --reason "Manual follow-up" --workspace C:\DeveloperWorkspace
prototype local assurance-review-cycle assurance-001 --workspace C:\DeveloperWorkspace
```

Perform any needed recovery-reference repairs manually. Use the existing
`disaster-test`, Phase 52 `assurance-create`/`assurance-verify` and Phase 53
`assurance-record-check` commands as appropriate to retain fresh verification.
Then explicitly record another operations review. Notes alone never resolve
findings or alter evidence. If the latest review is clean and still current:

```powershell
prototype local assurance-operation-transition operation-001 improved --reason "Fresh review confirms resolution" --workspace C:\DeveloperWorkspace
prototype local assurance-operation-transition operation-001 closed --reason "Review cycle complete" --workspace C:\DeveloperWorkspace
```

Alternatively use `accepted` after reviewing unresolved findings to document an
explicit manual disposition. Acceptance does not rewrite those findings. Every
review retains its verification snapshots, source histories and finding changes;
later operations and notes do not overwrite the original evidence.

## Limitations and isolation

This is a local operational evidence framework, not a recovery executor or
guarantee of successful real-world restoration. There is no automatic remediation,
scheduler, notification service or deployment mutation. Owners and actors are
local attribution rather than authenticated identities. Hash chains detect broken
history, not an adversary rewriting the entire local chain. Serialize related
mutations; independent journals do not provide cross-journal transactions.

Historical operation status remains historical if evidence later becomes stale;
live reports surface the change. Closing does not automatically resolve anything.
Recurrence depends on manually recorded review frequency. Findings resolution
means absence in a complete subsequent observation, not proof of a particular
repair's causal effect. Research evaluation/retrieval, benchmark, Humanize,
research snapshots and frozen release artifacts remain outside this workflow.

## Validation and preservation

Nine new regression tests cover operation lifecycle, recorded-review prerequisites,
finding creation/resolution/recurrence, shared findings across operations, review
cycles, owner handoffs, manual notes, ungoverned/unverified coverage, linked renewal
deduplication, expiry and reference loss, stale improvement rejection, retained
history during dependency loss, atomic publication failure, corruption, isolation,
CLI mutations/read-only reports and compatibility with prior journals and reports.
All use temporary external workspaces.

The targeted run passed all nine tests in 68.775 seconds, with zero skips,
failures or errors and exit status 0 (`phase54-operations-tests.log`). Required
focused and full suites run sequentially under Python 3.14.7. All test logs are
retained outside the checkout in the system temporary directory.

`python -m unittest tests.test_developer_mode -v` passed all 159 tests in
881.771 seconds with zero skips, failures or errors and exit status 0
(`phase54-focused.log`).

`python -m unittest discover -s tests -v` ran 303 tests in 526.645 seconds:
301 passed, 2 skipped, zero failures or errors, exit status 0
(`phase54-full.log`). The two skips require `EMBEDDING_MODEL_CACHE` for real
offline inference and embedding/index/query integration. Both suites emitted
the existing Transformer `cache_dir` deprecation warning. No dependency changes,
permission changes or environment repairs were needed.

`git diff --check` passed. Final SHA-256 comparison with the starting inventory
found changes only to `src/cli.py`, `tests/test_developer_mode.py` and
`docs/research/prototype-cli.md`, plus new `src/developer/assurance_operations.py`
and this document. Prior phase modules and documents retain their original bytes.
Benchmark datasets, Humanize, research evaluation/retrieval paths, snapshots and
frozen release artifacts remain unchanged. `v0.1.1` still resolves to
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. No generated assurance operations
journal directory exists inside the source checkout.
