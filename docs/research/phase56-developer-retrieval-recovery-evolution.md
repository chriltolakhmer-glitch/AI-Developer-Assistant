# Phase 56 — Developer Mode Retrieval Recovery Assurance Evolution Management

## Baseline and scope

Phase 55 already provides qualitative maturity levels (`initial`, `defined`,
`managed`, `measured`, `improving`), capability assessments, readiness reports,
improvement plans, ownership tracking and historical maturity transitions.
The remaining gaps are explicit capability direction, evolution decisions,
change impact history, dependency visibility and long-term review milestones.
Phase 56 adds developer-only manual records for those purposes.

The starting checkout contained uncommitted Phase 46–55 work. Its tracked and
nonignored untracked files were inventoried by SHA-256 outside the checkout at
`C:/Apps/Temp/Phase56/baseline.json`; status was retained beside it. The nine
Phase 55 baseline tests passed in 110.806 seconds, with no skips or failures.
The starting `v0.1.1` tag object was
`05688504f74ad51230ee1566fad8cda0f1b1ad97`.

## Evolution model

`src/developer/evolution.py` maintains an independent append-only journal under
`<external developer workspace>/optimization/evolution`. Events include actor,
reason, UTC timestamp, sequence and previous-event SHA-256 digest. Validated
replay reconstructs records. Exclusive atomic publication rejects competing
writers without overwriting prior events. Existing workspace guards apply to
both reads and writes; reports do not create directories or records.

Each record has `evolution_id` (for example `evolution-001`), `capability`,
`change_type`, `owner`, `created_at`, `updated_at`, `status`, `history`, `impacts`
and `plans`. Capability and change type are nonempty local descriptive labels;
`improvement` is the CLI default change type. A record begins `planned`.

| Current state | Allowed next states |
| --- | --- |
| planned | reviewing, retired |
| reviewing | planned, approved, retired |
| approved | reviewing, implemented, retired |
| implemented | reviewing, verified, retired |
| verified | retired |
| retired | None |

Transitions require an explicit note, actor and reason. Approval and verification
additionally require a recorded impact whose evidence exactly matches current
sources, no evidence gaps and no unresolved manual risks. Every decision and its
evidence remains in history. An `implemented` transition records the operator's
attestation of work performed elsewhere. It executes no code or deployment.
A `verified` record is historical; later source drift appears in review reports
without silently changing its state. Retired records are immutable. New work
after verification requires a new evolution record.

## Impact and evidence

Impact revisions retain affected capabilities, related finding IDs, linked maturity
IDs, evidence references with snapshots/digests, manual review notes and unresolved
risks. Affected capabilities are the Phase 55 capability keys:
`recovery-ownership`, `recovery-evidence-validation`, `recovery-review-cycle`,
`recovery-improvement-planning`. At least one capability and maturity record are
required. Findings are optional but must exist within the linked maturity records'
assurance scope. Unknown references and invalid capability keys are rejected.

Current evidence includes the linked maturity records and their assessments plus
live readiness evidence for each affected capability. Missing assessments,
ownership reassessment, stale assessments, missing source journals and assurance
evidence expiry become review gaps. Only affected capability gaps gate a decision;
all changes to a linked maturity record conservatively require refreshing impact
evidence. Linked operations findings must be explicitly resolved through the
existing operations workflow. Evolution reports never resolve them.

Impact updates append a new version. They are allowed in planned, reviewing and
implemented states. Approved scope must first return to reviewing. Implemented
records may refresh evidence and notes, but changes to capability, maturity or
finding links require returning to reviewing and obtaining approval again.
Manual risks are cleared only by an explicit impact revision after human review.
Prior notes, risks and evidence remain visible.

## Read-only CLI

All commands accept `--workspace PATH` and `--json`. Default output includes the
developer notice followed by JSON; `--json` emits one JSON object with the notice.

| Command | Output |
| --- | --- |
| `prototype local evolution-status` | All records and planned, active, verified and retired groups |
| `prototype local evolution-history EVOLUTION_ID` | State transitions, evidence updates, review decisions, verification events and plans |
| `prototype local evolution-impact EVOLUTION_ID` | Current impact and every prior impact revision |
| `prototype local evolution-review EVOLUTION_ID` | Current state, live maturity impact, ready, warnings, missing_evidence and manual_actions |
| `prototype local evolution-plan` | All strategic plan versions, ownership, dependencies and milestones |

Active work means reviewing, approved or implemented. Review returns lists for
`ready`, `warnings`, `missing_evidence`, `manual_actions`; readiness identifies a
manual approval or manual verification opportunity only in the corresponding
state. Reports never approve evolution, change maturity or activate retrieval.
A report with gaps exits zero: inspect its fields. Unknown IDs, malformed journals
and invalid mutation requests fail through the existing CLI error handling.
Empty workspaces produce empty status and plan lists without creating a journal.

## Explicit manual workflow

Mutations require `--reason` and accept `--actor` (default `developer`).

```powershell
prototype local evolution-create recovery-verification --owner maintainer --change-type improvement --reason "Plan assurance evolution" --workspace C:\DeveloperWorkspace
prototype local evolution-impact-add evolution-001 --capability recovery-ownership --maturity-id maturity-001 --note "Ownership scope reviewed" --reason "Capture current impact" --workspace C:\DeveloperWorkspace
prototype local evolution-transition evolution-001 reviewing --note "Begin human review" --reason "Review proposal" --workspace C:\DeveloperWorkspace
prototype local evolution-review evolution-001 --workspace C:\DeveloperWorkspace
prototype local evolution-transition evolution-001 approved --note "Impact and risks reviewed" --reason "Manual approval" --workspace C:\DeveloperWorkspace
prototype local evolution-transition evolution-001 implemented --note "Procedure updated outside this workflow" --reason "Record completed work" --workspace C:\DeveloperWorkspace
prototype local evolution-transition evolution-001 verified --note "Evidence reviewed after implementation" --reason "Manual verification" --workspace C:\DeveloperWorkspace
```

The linked maturity records and affected capability assessments must already
exist and be current. Repeat `--capability`, `--maturity-id`, `--finding`, `--note`
and `--risk` on impact recording as needed. If sources change during implementation,
renew the underlying evidence and assessments, then explicitly refresh impact
before verification. No command performs these source updates automatically.

## Strategic planning

```powershell
prototype local evolution-plan-add evolution-001 --owner maintainer --improvement "Document evidence renewal" --dependency recovery-ownership --milestone "Review at next quarterly meeting" --reason "Record long-term direction" --workspace C:\DeveloperWorkspace
prototype local evolution-plan-add evolution-001 --owner next-maintainer --improvement "Review renewal procedure" --dependency recovery-evidence-validation --milestone "Review after evidence renewal" --supersedes evolution-001-plan-001 --reason "Revise direction" --workspace C:\DeveloperWorkspace
prototype local evolution-plan --workspace C:\DeveloperWorkspace
```

Plans contain improvements, descriptive capability dependencies, review milestones,
owner, actor, reason, creation time and optional `supersedes`. Improvements and
milestones must be nonempty lists. Repeat their flags for multiple items.
Superseding creates a new record and retains the old one unchanged. A prior plan
must belong to the same evolution and cannot be superseded twice; revise its
successor. Reports mark current versions while showing the entire history.
Dependencies and milestones are manually maintained descriptions, not executable
prerequisites, scheduled jobs, dates enforced by software or automatic approvals.
Plan ownership is independent of the evolution's original accountable owner.

## Limitations and isolation

This is local assurance change tracking, not proof of successful real-world recovery.
Actors and owners are attribution, not authenticated identities. Hash chaining
exposes broken history but does not prevent an actor from rewriting an entire
local chain. Serialize related mutations to obtain consistent cross-journal
observations. Evidence is checked at decision time; there is no background watcher.
There is no automatic implementation, maturity promotion, recovery execution,
remediation, scheduler or retrieval activation. No scores, rankings or user metrics
are introduced. Research evaluation/retrieval methodology, benchmark datasets,
Humanize, frozen release artifacts and research snapshots remain outside this
workflow. Developer repositories are not added to research snapshots.

## Validation and preservation

Regression tests cover lifecycle and invalid transitions, impact revision history,
risks, stale maturity evidence, assurance expiry, unavailable sources, source finding
resolution, manual planning revisions, CLI reporting, read-only compatibility,
atomic publication failure, journal corruption and research workspace isolation.
Tests and generated records use temporary external workspaces. Validation logs
are retained in `C:/Apps/Temp/Phase56`.

The targeted evolution run passed all nine tests in 89.990 seconds with no skips,
failures or errors (`evolution-verified.log`, exit 0). Two preliminary runs exposed
test-harness issues (the existing `StringIO` import and the CLI `--json` flag);
both were corrected before the successful run. Required suites run sequentially
under Python 3.14.7. `EMBEDDING_MODEL_CACHE` is unset.

`python -m unittest tests.test_developer_mode -v` passed all 177 tests in
845.853 seconds with zero skips, failures or errors (`focused.log`, exit 0).

`python -m unittest discover -s tests -v` ran 321 tests in 1059.644 seconds:
319 passed, two skipped, zero failures or errors (`full.log`, exit 0). The skips
are real offline embedding repeatability and embedding/index/query integration,
which require `EMBEDDING_MODEL_CACHE`. Both suites emitted the existing Transformer
`cache_dir` deprecation warning. No dependency or environment changes were needed.

Final SHA-256 comparison confirms that 287 of the 290 baseline files retain their
original bytes. Only `src/cli.py`, `tests/test_developer_mode.py` and
`docs/research/prototype-cli.md` changed; the only new files are
`src/developer/evolution.py` and this document. Earlier phase modules and documents,
benchmark datasets, Humanize, research evaluation/retrieval, research snapshots
and frozen release artifacts remain unchanged. The `v0.1.1` tag remains
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. `git diff --check` passes.
No generated evolution journals exist inside the source checkout. External
`preservation.json`, `test-results.json`, the baseline inventory and test logs
retain the verification evidence.
