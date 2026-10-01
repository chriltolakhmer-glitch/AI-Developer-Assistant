# Phase 50 - Developer retrieval deployment reliability and recovery framework

## Scope and baseline

This framework prepares developer deployment operations for handoff and manual
recovery. It adds readiness records, recovery plans, live reliability checks and
recorded verification. It changes no research evaluation, retrieval methodology,
benchmark data, Humanize, research snapshots, frozen release artifacts or runtime
retrieval behavior. There are no research quality, productivity or user metrics,
and no benchmark improvement claims. Phase 45 promotions remain runtime authority.

The starting checkout contained modified `src/cli.py`, `tests/test_developer_mode.py`
and `docs/research/prototype-cli.md`, plus untracked Phase 46-49 documents and
`configuration.py`, `deployment.py`, and `operations.py`. Those changes were
preserved. No protected research paths appeared in the initial tracked diff.
`v0.1.1` resolved to `05688504f74ad51230ee1566fad8cda0f1b1ad97`. Before edits,
a SHA-256 inventory of tracked and nonignored untracked files was saved outside
the checkout as `phase50-baseline.json` in the system temporary directory.

The initial developer suite passed all 114 tests in 265.221 seconds, with zero
skips, failures or errors and exit status 0. It imported the original CLI and test
module before implementation changes. The baseline log is `phase50-baseline-tests.log`
in the system temporary directory and includes the eight Phase 49 regressions.

Existing capabilities were deployment operations, read-only health checks,
incident ownership/lifecycle, recovery history, deployment audits and governance
validation. The gaps were consolidated readiness evidence, explicit recovery
requirements, validation of a recovery plan, and a durable ownership handoff.

## Readiness model

`src/developer/reliability.py` stores readiness records with `readiness_id`,
`deployment_id`, `status`, `created_at`, `checks`, and append-only `history`.
It also retains creation attribution, the captured deployment/configuration/history
snapshot and an evidence digest. IDs are sequential, such as `readiness-001`.
Actual records start with an attributed `pending` history event and empty checks.

| Current state | Allowed next states |
| --- | --- |
| `pending` | `checking`, `expired` |
| `checking` | `passed`, `failed`, `expired` |
| `passed` | `expired` |
| `failed` | `expired` |
| `expired` | None |

`readiness-check` appends `checking`, gathers live reliability evidence, then
appends `passed` if there are no blockers, or `failed` otherwise. Warnings remain
visible but do not block a pass. Callers cannot force a passing outcome that
contradicts the findings. Missing checks, repeated transitions, unknown states,
and invalid attribution fail before publication. An interrupted check that already
recorded `checking` can resume without repeating that event. Completed/expired
records require a new assessment rather than overwriting the original result.

Outcome events retain the full evidence report. `readiness-status` recomputes a
digest of live evidence, including deployment audit/health, the latest plan,
verification and incident history. It returns `evidence_current` separately from
the recorded result. Changed evidence sets `requires_new_check`; it never rewrites
a historical pass into a failure. Explicit expiry also requires a new check.
There is no timer or implicit expiry event. A historical pass is neither current
approval nor an activation instruction.

## Recovery planning and operational handoff

A plan includes `plan_id`, `deployment_id`, `rollback_target`, `owner`,
`created_at`, and `history`, plus `previous_deployment`, the immutable
`previous_configuration` snapshot, captured deployment history and
`validation_status`. Plan IDs use `recovery-plan-001`. Plans start with pending
validation and an attributed creation event.

The rollback target comes from the deployment's recorded predecessor, never a
caller-selected arbitrary deployment. Its configuration is captured for later
comparison. For an initial deployment, the predecessor, rollback target and
previous configuration are explicitly null. This means restoring an empty
reference; it is reported as a warning instead of fabricating a rollback target.

The newest plan per deployment is the active planning record. Creating a new plan
captures a new owner for handoff while preserving earlier plans, ownership and
verification histories. It starts unverified and blocks readiness until checked.
"Active" identifies the latest plan, not a live deployment, an eligible rollback,
or permission to execute. Plan status includes both recorded validation and live
verification, with `verification_current` indicating whether the findings agree.

Plan inspection combines the captured plan with live deployment details, rollback
information, incident history, audit history, and readiness records with evidence
freshness. Historical snapshots and current findings remain distinct.

## Reliability checks

`prototype local reliability-check DEPLOYMENT_ID` is strictly read-only. It emits
`passed`, `warnings`, and `blocked` lists with named checks and descriptive findings:

| Check | Evidence and blocking conditions |
| --- | --- |
| `audit_completeness` | Complete deployment journal replay and audit projection; malformed history blocks |
| `health_availability` | Health report can be produced; its availability alone does not imply healthy state |
| `rollback_availability` | Eligible recorded target for recovery preparation; closed deployments block |
| `recovery_plan` | Latest retained recovery plan exists |
| `recovery_validation` | Plan has a recorded pass and live verification has no blockers |
| `governance` | Existing deployment governance and configuration/promotion prerequisites |
| `incident_consistency` | Phase 49 incident/recovery journal replay, including rollback references; active incidents warn for handoff |

Evidence includes full deployment audit history, health, the selected plan, live
verification and related incidents. Corrupt dependency journals become explicit
blockers where a diagnostic report can still be produced. Unknown deployment IDs
in a valid journal are caller errors. Untrusted reliability records cannot be
presented through status/inspection as valid history. Checks neither initialize
nor repair workspaces and create no operational records.

Readiness can be evaluated before activation. Therefore rollback preparation
eligibility is distinct from whether an immediate rollback command is allowed.
Live governance still blocks stale deployment references. Verification and
readiness do not bypass existing activation/rollback gates.

## Recovery verification workflow

1. Create a plan with `recovery-plan-create DEPLOYMENT_ID --owner OWNER --reason REASON`.
2. Inspect it with `recovery-plan-inspect PLAN_ID`, and review deployment history,
   related incidents and the predecessor configuration.
3. Run `recovery-verify PLAN_ID`. It validates retained deployment history and
   snapshot agreement, rollback reference existence, owner attribution, previous
   configuration availability/eligibility, current rollback eligibility and
   governance. The command appends the findings and a passed/failed validation
   event to the plan; it executes nothing. Repeated verification retains every
   earlier outcome. Missing/retired configurations or withdrawn approval block.
4. Create a readiness record with `readiness-create DEPLOYMENT_ID --reason REASON`,
   then run `readiness-check READINESS_ID`. Review all warnings, especially active
   incidents and an initial deployment's empty rollback reference.
5. Use `readiness-status`, `recovery-plan-status` and `reliability-check` for a
   current handoff. Expire a completed assessment explicitly when its handoff
   window ends. Changed evidence requires a new assessment.
6. If recovery is needed, execute it manually through existing governed workflows
   and use Phase 49 incident resolution to record the action/audit reference.

Verification is a recovery-preparation check, not proof that recovery was executed
or succeeded. After a deployment is rolled back or retired, re-verification reports
that it is no longer eligible for recovery preparation and preserves the previous
verification history. It does not reverse that deployment transition.

All new commands emit JSON and accept `--workspace EXTERNAL_WORKSPACE` and
`--json`. Mutations accept `--actor`, defaulting to `developer`. Plan/readiness
creation and expiry require reasons; check and verification commands provide
default reasons and accept overrides. Successful reports return exit zero even
when they contain blockers or failed validation; automation must inspect the
result. The [CLI guide](prototype-cli.md) contains full command examples.

## Persistence, isolation and limitations

Readiness and plan events share a separate `optimization/reliability` journal in
the external developer workspace. Existing checkout/research overlap and path
containment guards apply. Numbered events are hash chained, replay validated,
flushed and published by exclusive atomic hard link. No existing event is edited,
and a competing writer cannot overwrite a published event. Readers return detached
records. Verification changes only this journal; it never writes deployment,
configuration, promotion, incident, source or research artifacts.

Owner/actor fields provide local attribution rather than authenticated identity.
Hash chaining is not signed or filesystem-enforced immutability: a privileged
writer could replace the chain or truncate its tail. There is no external trusted
head, shared cross-journal lock, scheduler, automatic rollback, automatic repair,
automatic activation, service telemetry, or recovery execution. Serialize related
journal mutations when a consistent live view matters. Checks are point-in-time
operational evidence, not a guarantee of availability or successful recovery.
Readiness snapshots are complete relative to retained valid histories. Histories
are unbounded; no retention or archival policy is implemented.

## Validation and preservation

Nine added regression tests cover readiness creation/lifecycle, failed and passed
outcomes, explicit expiry, invalid transitions and forced-pass rejection,
stale evidence, plan creation and ownership handoff, initial and nonempty rollback
targets, recovery verification, interrupted writes/check resumption, incident and
manual rollback compatibility, audit/governance/configuration compatibility,
journal corruption, read-only reports, workspace isolation and every new CLI
command. Tests use temporary external workspaces. The focused/full suites retain
all Phase 49 regressions unchanged.

The nine new tests passed separately in 41.246 seconds, with zero skips, failures
or errors and exit status 0 (`phase50-reliability-tests.log`).

The first required focused run completed 123 tests in 474.494 seconds with one
failure, zero skips and exit status 1. The unchanged
`test_regression_rejects_unstable_baseline_and_reports_unstable_comparison` expected
an unstable-ranking error but Git instead returned `Permission denied` while
entering its temporary repository. All nine Phase 50 tests passed. The full suite
running alongside it passed the same existing regression test. The cause of the
temporary Git access failure was not established; no code, permission or
dependency changes were made to hide it. Its log is retained as
`phase50-focused.log`. The focused suite was rerun on its own.

The required full suite completed 267 tests in 479.709 seconds: 265 passed, two
skipped, zero failures/errors, exit status 0 (`phase50-full.log`). Both skips require
`EMBEDDING_MODEL_CACHE` for real offline inference and embedding/index/query
integration. An existing Transformer `cache_dir` deprecation warning is unrelated
to this framework. All logs are in the system temporary directory, outside the
checkout. Python subprocess logging retains actual test exit codes.

Final verification used Python 3.14.7:

| Command/run | Tests | Passed | Skipped | Failures/errors | Exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| `python -m unittest tests.test_developer_mode -v` (initial) | 123 | 122 | 0 | 1 / 0 | 1 |
| `python -m unittest tests.test_developer_mode -v` (isolated retry) | 123 | 123 | 0 | 0 / 0 | 0 |
| `python -m unittest discover -s tests -v` | 267 | 265 | 2 | 0 / 0 | 0 |

The isolated focused retry passed in 374.191 seconds, including the test that
previously encountered the Git access failure. Its log is
`phase50-focused-retry.log`. No implementation changes were needed between runs.
No dependency or permission changes were needed.

`git diff --check` passed. Final SHA-256 comparison with the initial inventory
found changes only to `src/cli.py`, `tests/test_developer_mode.py` and
`docs/research/prototype-cli.md`, plus new `src/developer/reliability.py` and this
document. Phase 46-49 implementations and documents retain their initial bytes.
Benchmark datasets, Humanize, research evaluation/retrieval paths, snapshots and
frozen release artifacts are unchanged. `v0.1.1` still resolves to
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. No generated reliability directory or
reliability journal records exist inside the source checkout.
