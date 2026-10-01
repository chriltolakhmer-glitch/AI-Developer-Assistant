# Phase 55 — Developer Mode Retrieval Recovery Assurance Maturity Management

## Baseline and scope

Phase 54 already provides operations lifecycle management, recurring findings,
review cycles, coverage reports, improvement tracking and ownership records.
The remaining gaps were explicit capability definitions, readiness criteria,
historical maturity changes and reviewed improvement plans. This phase introduces
qualitative capability management only for explicitly scoped developer assurance
areas. It creates no research quality metrics, performance scores, developer
rankings or user measurements.

The starting checkout contained uncommitted Phase 46–54 work: changes to the CLI,
developer tests and CLI guide, together with earlier developer modules and phase
documents. These were preserved. Before implementation, tracked and nonignored
untracked files were inventoried by SHA-256 outside the checkout. The nine Phase
54 operations regressions passed in 53.251 seconds with no skips, failures or
errors (`phase55-baseline-tests.log`). The starting `v0.1.1` tag object was
`05688504f74ad51230ee1566fad8cda0f1b1ad97`.

## Maturity model

`src/developer/maturity.py` stores a separate append-only journal in the external
developer workspace's `optimization/maturity` directory. Each numbered event has
actor, reason, UTC timestamp, sequence and previous-event digest. Validated replay
reconstructs the records; exclusive atomic publication prevents overwriting a
concurrent event. Existing source/research workspace guards apply before reads
and writes. Read-only reports do not create directories or events.

A record contains `maturity_id` (`maturity-001`), `assurance_area`, `level`,
`owner`, `created_at`, `updated_at`, `history`, scoped `assurance_ids`,
`required_capabilities`, `assessments` and `plans`. An area is a unique local label,
such as `recovery-verification`, bound to one or more existing Phase 53 governance
anchors. Unregistered areas are not implicitly assessed; use Phase 54 coverage
to find missing assurance governance across the workspace.

Records start at `initial`. Level changes are explicit and may move only one
adjacent level forward or backward. Same-level and skipped-level changes are
rejected. Downgrades document a manual reassessment and preserve earlier evidence.
Promotions require the latest assessments for all target-level capabilities to
be gap-free, attributed to the current maturity owner, and match live evidence.

| Target level | Cumulative required capability assessments |
| --- | --- |
| initial | No capability claim yet |
| defined | `recovery-ownership` |
| managed | Ownership plus `recovery-evidence-validation` |
| measured | Previous capabilities plus `recovery-review-cycle` |
| improving | All four, including `recovery-improvement-planning` |

These are qualitative local criteria. In particular, `measured` means there is
reviewed operational evidence; it does not introduce numerical measurements.
Neither readiness reports nor assessment recording changes the stored level.
Later source drift produces attention findings without silently downgrading it.

## Capability assessment and evidence

Each explicit assessment retains capability name, the maturity level at the time
of assessment, owner, actor, timestamp, sequence, evidence references, known gaps
and improvement notes. References include immutable source snapshots and content
digests. Assessments also retain evidence differences from the prior assessment
of that capability. Prior levels, gaps, references and notes remain inspectable.

The four required capabilities use these sources:

| Capability | Evidence and readiness checks |
| --- | --- |
| recovery-ownership | Scoped governance owners, responsibilities and handoff review requirements |
| recovery-evidence-validation | Recorded verification history, active governance schedule, current evidence availability/freshness and live findings |
| recovery-review-cycle | Phase 54 reviews, comparison with current governance, and unresolved operation findings |
| recovery-improvement-planning | Manually reviewed current plans, linked findings and live governance findings |

Readiness compares the latest assessment against current evidence for each
capability. Missing assessments, changed evidence, unavailable journals, manual
gaps, stale reviews, open findings and maturity ownership handoffs require manual
attention. Assigning a new maturity owner does not rewrite governance owners;
the new owner must explicitly reassess before promotion. Earlier assessments
retain their original owners and levels.

Manually supplied `--gap` values remain unresolved in that assessment even if
live evidence appears clean. Record another assessment after review to clear
them. Missing source history is reported as a gap, while earlier maturity
snapshots remain readable. No report repairs missing evidence or resolves
Phase 54 findings.

## Read-only commands

All commands accept `--workspace PATH` and `--json`; output is JSON.

| Command | Output |
| --- | --- |
| `prototype local maturity-status` | Areas, stored levels, owners and the five most recent events per record |
| `prototype local maturity-history MATURITY_ID` | Historical levels, assessments, evidence differences, plans and improvement events |
| `prototype local maturity-review AREA` | Current capability state, missing/stale evidence, gaps and improvement opportunities |
| `prototype local maturity-readiness` | `ready`, `needs_attention`, `missing_evidence`, `manual_actions` |
| `prototype local maturity-plan` | All plan versions, linked findings, affected capabilities and manual review history |

Readiness is comprehensive: `ready` requires current gap-free assessments for all
four capabilities, regardless of the stored level. A lower level can therefore
be ready without being promoted, while a historically higher level can need
attention. Promotion gates use the cumulative subset in the table above. There
are no percentages, scores or rankings. An empty workspace returns empty lists.
Reports exit zero even with gaps; callers must inspect the returned fields.

## Explicit maturity workflow

Mutations require `--reason` and accept `--actor` (default `developer`):

```powershell
prototype local maturity-create recovery-verification --assurance-id assurance-001 --owner maintainer --reason "Define area and accountability" --workspace C:\DeveloperWorkspace
prototype local maturity-assess maturity-001 recovery-ownership --note "Responsibilities reviewed" --reason "Capture ownership evidence" --workspace C:\DeveloperWorkspace
prototype local maturity-transition maturity-001 defined --reason "Ownership capability confirmed" --workspace C:\DeveloperWorkspace
prototype local maturity-assess maturity-001 recovery-evidence-validation --reason "Capture current verification evidence" --workspace C:\DeveloperWorkspace
prototype local maturity-transition maturity-001 managed --reason "Verification capability confirmed" --workspace C:\DeveloperWorkspace
```

Repeat `--assurance-id` during creation to scope multiple anchors. Repeat `--gap`
or `--note` on `maturity-assess` to record known gaps or improvement notes. Use
`maturity-assign MATURITY_ID --owner OWNER --reason TEXT` for ownership changes.
Renew underlying evidence using existing assurance/governance commands and
record fresh operations reviews where required, then reassess the affected
capabilities. The maturity commands never mutate those earlier journals.

## Controlled improvement plans

Plans retain an ID, owner at creation, planned improvements, affected capabilities,
linked finding IDs and their original snapshots, optional `supersedes` reference,
status and review history. Findings must exist in Phase 54 operations history and
belong to an assurance anchor in the area's scope. Unknown findings and
capabilities are rejected. Empty finding links are allowed for preventive work.

```powershell
prototype local maturity-plan-add maturity-001 --improvement "Review recovery evidence renewal instructions" --capability recovery-evidence-validation --reason "Plan preventive improvement" --workspace C:\DeveloperWorkspace
prototype local maturity-plan-review maturity-001 maturity-001-plan-001 reviewed --note "Scope and evidence reviewed manually" --reason "Review plan" --workspace C:\DeveloperWorkspace
```

Repeat `--improvement`, `--capability` and `--finding` as needed. Use
`--supersedes PLAN_ID` on a new plan to revise an existing plan within the same
maturity record. Previous plans are retained unchanged. Superseded plans remain
visible in reports; all current, nonsuperseded plans must be reviewed or completed
for the planning capability to have no missing-review gap.

Plans start `planned`. Explicit review may mark a noncompleted plan `reviewed`
or `deferred`, with an attributed note; repeated reviews append history. Only a
`reviewed` plan may become `completed`, and completion additionally requires
current gap-free verification, gap-free evidence for its affected capabilities
(excluding the plan's own planning-status prerequisite), and resolved linked
findings. A completed plan is immutable; create another version for later work.

Plan review or completion never clears a manual assessment gap, resolves a source
finding or promotes maturity. For example, fresh verification alone does not
resolve a persisted operations finding: explicitly record an operations review
confirming resolution before completing the linked maturity plan.

## Limitations and isolation

Maturity describes locally documented capabilities, not a guarantee that real
recovery will succeed. Planning readiness checks for reviewed planning activity;
historical plan completion is not continually re-executed or automatically revoked.
Live readiness reports expose subsequent source gaps. There is no automated
promotion, remediation, recovery execution, scheduler or deployment change.

Owners/actors are local attribution, not authenticated identities. Hash chains
detect broken journal history but cannot prevent a party from rewriting an
entire local chain. Serialize related mutations for consistent cross-journal
observations. Research evaluation/retrieval, benchmark data, Humanize, frozen
release artifacts and research snapshots remain outside this workflow; developer
repositories are not added to research snapshots.

## Validation and preservation

Nine new regression tests cover the full maturity lifecycle, invalid transitions,
scope validation, capability assessments, manual gaps, owner reassessment, evidence
expiry/differences, readiness, retained history, reviewed plan revisions, linked
finding resolution, operations/evidence compatibility, CLI mutations/read-only
reports, journal corruption, atomic publication failure and workspace isolation.
Tests use temporary external workspaces and retain all prior phase regressions.

The targeted run passed all nine tests in 75.897 seconds, with zero skips,
failures or errors and exit status 0 (`phase55-maturity-tests.log`). Required
focused and full suites run sequentially under Python 3.14.7. Logs are retained
outside the checkout in the system temporary directory.

`python -m unittest tests.test_developer_mode -v` passed all 168 tests in
578.513 seconds with zero skips, failures or errors and exit status 0
(`phase55-focused.log`). The initial full-suite process ended during deployment
tests without a final result or available exit status. Its partial log is retained
as `phase55-full.log`; it is not counted as a passing run. On continuation, no
test process remained, so the full suite was restarted with a separate log,
`phase55-full-retry.log`.

The completed retry of `python -m unittest discover -s tests -v` ran 312 tests
in 672.084 seconds: 310 passed, 2 skipped, zero failures or errors, exit status 0.
The two skips require `EMBEDDING_MODEL_CACHE` for real offline inference and
embedding/index/query integration. Both completed suites emitted the existing
Transformer `cache_dir` deprecation warning. No dependency changes, permission
changes or environment repairs were needed.

`git diff --check` passed. Final SHA-256 comparison with the starting inventory
found changes only to `src/cli.py`, `tests/test_developer_mode.py` and
`docs/research/prototype-cli.md`, plus new `src/developer/maturity.py` and this
document. Earlier phase modules and documents retain their original bytes.
Benchmark datasets, Humanize, research evaluation/retrieval, research snapshots
and frozen release artifacts remain unchanged. `v0.1.1` still resolves to
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. No generated maturity journal
directory exists inside the source checkout.
