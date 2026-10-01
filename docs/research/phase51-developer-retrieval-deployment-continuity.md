# Phase 51 - Developer retrieval deployment continuity and disaster recovery

## Scope and baseline

This phase preserves developer operational recovery knowledge and records
validation of recovery scenarios. It adds scenario and continuity records,
read-only disaster checks, inspection and recovery simulation tracking. It does
not execute recovery or change retrieval behavior, research evaluation, research
retrieval methodology, benchmark data, Humanize, research snapshots or frozen
release artifacts. No quality, productivity or user metrics are introduced.
Phase 45 promotions remain the runtime authority.

The starting checkout contained modified `src/cli.py`, `tests/test_developer_mode.py`
and `docs/research/prototype-cli.md`; Phase 46-50 documents and developer
configuration/deployment/operations/reliability modules were untracked. Those
existing changes were preserved. The initial tracked diff included no protected
research paths. The `v0.1.1` tag object was
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. Before edits, a SHA-256 inventory of
tracked and nonignored untracked files was saved outside the checkout as
`phase51-baseline.json` in the system temporary directory.

The baseline focused suite passed all 123 tests in 301.527 seconds, with zero
skips, failures or errors and exit status 0. The original test/CLI modules were
imported before implementation edits. The log is `phase51-baseline-tests.log`
in the system temporary directory and includes all Phase 50 regressions.

Existing capabilities were readiness checks and freshness detection, recovery
plans, reliability validation, deployment audit history, incident management and
rollback tracking. The continuity gaps were named disaster scenarios, preserved
manual restoration instructions, durable validation attempts, and explicit
scenario ownership for incident handoffs.

## Disaster recovery model

`src/developer/continuity.py` defines scenarios with `scenario_id`, `deployment_id`,
`type`, `status`, `owner`, `created_at`, and append-only `history`. Scenarios also
link their `recovery_plan`, `continuity_id` and completed `tests`. IDs use
`disaster-001`. Supported type labels are `configuration_failure`,
`deployment_failure`, `rollback_unavailable`, and `history_loss`. Each uses the
same reference-validation checks; labels do not enable fault injection or
scenario-specific execution.

| Current state | Allowed next states |
| --- | --- |
| `planned` | `testing`, `retired` |
| `testing` | `validated`, `failed`, `retired` |
| `validated` | `testing`, `retired` |
| `failed` | `testing`, `retired` |
| `retired` | None |

Creation records an attributed planned event. Test outcomes derive from live
checks: blockers mean failed, otherwise validated, with warnings retained.
Callers cannot force an outcome contradicting the report. Repeated transitions,
unknown states/types, empty attribution/reasons and retired restarts are rejected
before publication. Retesting failed or validated scenarios appends a new attempt;
it never replaces the old one. Retirement retains all history.

## Continuity records and operational knowledge

Every scenario is created atomically with one continuity record containing
`continuity_id`, `deployment_id`, `recovery_plan`, `owner`, `created_at`, and
`history`. Additional fields track `validation_status`, deployment dependencies,
configuration dependencies, recovery references, and captured knowledge.

Captured knowledge includes the original full deployment record, its audit
timeline, the chosen recovery plan including its recorded verification, and
manual restoration instructions. Dependencies identify the current deployment
and configuration, plus the recorded predecessor and its configuration when
present. The initial rollout explicitly has no predecessor or previous
configuration; its rollback reference is null rather than a fabricated target.

Create a Phase 50 recovery plan before creating a scenario. The latest plan for
that deployment is chosen unless `--plan-id` selects another existing plan for
the same deployment. Unverified plans can be captured for planning, but their
live reliability findings block a successful test until verification passes.
A cross-deployment plan is rejected. If a plan is later superseded, the scenario's
original plan/owner remain intact and its live check blocks; create a new scenario
for the new handoff. The scenario owner is the person responsible for the exercise
or incident, while the captured plan retains its own recovery owner.

Default restoration instructions cover reviewing dependencies, confirming owners,
reviewing audit/incident/governance evidence, performing approved recovery manually,
and checking health/audit results before recording incident resolution. Repeated
`--step` arguments replace these with local instructions. Instructions are data,
not shell commands, and are never executed.

The continuity record begins with pending validation, then tracks testing,
validated/failed outcomes and retirement. Each outcome and its complete attempt
are appended to scenario and continuity histories in the same journal event.
`continuity-status` returns all retained knowledge and validation history, even
when live dependency journals are unavailable. It is historical data, not a live
health report or a backup restoration facility.

## Read-only scenario validation

`disaster-check SCENARIO_ID` returns `passed`, `warnings`, and `blocked` lists,
with named findings and live evidence:

| Check | Validation |
| --- | --- |
| `recovery_plan` | Captured plan still exists for the deployment, immutable references agree, and no newer plan supersedes it |
| `rollback_target` | Recorded predecessor exists and matches the captured configuration, or is explicitly empty for an initial rollout |
| `deployment_history` | Complete journal replay retains the captured deployment/configuration/history prefix |
| `configuration_history` | Both captured configuration snapshots exist and agree with retained configuration history |
| `audit_history` | Complete audit replay preserves the captured audit prefix |
| `ownership` | Scenario and captured recovery-plan attribution exist; creation/replay reject empty ownership |
| `reliability` | Live Phase 50 checks, including plan verification, rollback eligibility, governance, configuration eligibility and incident consistency |

Historical existence alone does not establish eligibility. A retired configuration
can still have valid retained history while live reliability blocks its use.
An initial deployment's empty rollback reference produces a warning. Active
incidents retain Phase 50 handoff warnings. Warnings do not block a validated
attempt; operators must still review them.

Missing or corrupt dependency journals produce explicit blockers rather than
repairs. Captured knowledge remains inspectable. Corrupt continuity journals or
unknown scenario IDs raise errors because the scenario itself cannot be trusted.
Inspection combines original scenario/continuity history with live deployment
history, plan, audit and validation results. Unavailable live fields are null;
their captured versions remain under continuity knowledge.

`disaster-status` shows related deployments, ownership, active status, retained
validation attempts and live findings. Active means non-retired, not successful.
`evidence_current` compares the latest attempt's evidence digest with live checks.
Changes to audit, plan, configuration, governance or incident evidence can make
an old validated attempt stale without rewriting its history.

## Recovery simulation tracking

`disaster-test SCENARIO_ID` is a reference-validation exercise, not a recovery
execution engine. It appends testing, gathers the same read-only checks, and
atomically records the resulting validated/failed state and a test record with:

- A unique scenario-local test ID and timezone-aware test date.
- Scenario ID, scenario owner, recording actor and reason.
- Validation results, all findings, and the evidence digest.
- `method: reference_validation_only` to identify what was actually tested.

If publication of the outcome fails after testing was recorded, repeating the
command resumes testing and writes one completed attempt. Earlier attempts and
knowledge remain unchanged. No test executes rollback, modifies configurations,
changes deployment state, resolves incidents or bypasses governance. A manual
rollback performed elsewhere remains visible through audit/reliability; a closed
deployment may no longer be eligible for preparation and can produce a failed
subsequent attempt. Neither result proves that real restoration succeeded.

## CLI workflow

1. Review and verify a Phase 50 recovery plan for the deployment.
2. Create a scenario using `disaster-create DEPLOYMENT_ID --owner OWNER --reason REASON`.
   Optionally select `--type`, `--plan-id`, and repeated `--step` instructions.
3. Inspect the preserved plan/dependencies with `disaster-inspect SCENARIO_ID`.
4. Run read-only `disaster-check SCENARIO_ID` and address any blockers explicitly
   through the existing governed workflows.
5. Use `disaster-test SCENARIO_ID` to retain a dated validation attempt. Review
   `disaster-status` and `continuity-status` during handoff.
6. Retire an obsolete scenario with `disaster-retire SCENARIO_ID --reason REASON`;
   create a new scenario when the recovery plan or ownership changes.

All commands emit JSON and accept `--workspace EXTERNAL_WORKSPACE` and `--json`.
Mutations accept `--actor` (default `developer`). Creation and retirement require
reasons; test attempts have an overridable default reason. Owner defaults to
`developer`. Successful report generation exits zero even if findings are blocked
or the attempt failed; automation must inspect the payload. The
[CLI guide](prototype-cli.md) contains full examples.

## Persistence, isolation and limitations

All new records live under the external developer workspace's
`optimization/continuity` directory. Checkout/research overlap and path containment
guards are reused. Events are numbered and hash chained, replay validated,
flushed and published through exclusive atomic hard links. Competing writers
cannot overwrite existing events. Scenario/continuity creation and each completed
attempt are single-event transactions. Readers return detached records and do
not initialize workspaces. Only this new journal is written by continuity commands.

Owner names provide attribution rather than authentication. Local hash chains
are not signed or filesystem-enforced immutability: privileged writers can
replace the chain or truncate its tail. There is no external trusted head,
cross-journal transaction lock, remote/offline backup, backup export, restore
engine, scheduler, fault injection, automatic activation or automatic recovery.
Captured metadata cannot recreate lost source, indexes, configurations or journal
files. Histories are unbounded, and dependency reads are point-in-time; serialize
related mutations when a consistent view matters. These checks do not measure
recovery time, recovery point objectives or research quality.

## Validation and preservation

Nine added tests cover supported scenario types, atomic continuity capture,
lifecycle/retesting/retirement, invalid transitions and forced outcomes,
ownership and plan links, dependency capture, recorded simulation attempts,
missing/corrupt live dependencies with historical knowledge preserved, ownership
handoffs, stale evidence, manual rollback and incident compatibility, Phase 50
reliability/governance compatibility, interrupted writes, journal corruption,
read-only reports, external-workspace isolation, and all new CLI commands.
Tests use temporary external workspaces. Existing Phase 50 tests are retained.

The nine new tests passed separately in 38.093 seconds, with zero skips, failures
or errors and exit status 0 (`phase51-continuity-tests.log`). The required focused
and full suites run sequentially. Python subprocess logging preserves the actual
test exit codes, and logs stay in the system temporary directory outside the
checkout.

Final verification used Python 3.14.7:

| Command | Tests | Passed | Skipped | Failures/errors | Exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| `python -m unittest tests.test_developer_mode -v` | 132 | 132 | 0 | 0 / 0 | 0 |
| `python -m unittest discover -s tests -v` | 276 | 274 | 2 | 0 / 0 | 0 |

Focused duration was 333.309 seconds (`phase51-focused.log`); full duration was
342.386 seconds (`phase51-full.log`). Both retain all Phase 50 regressions. The
two full-suite skips require `EMBEDDING_MODEL_CACHE` for real offline inference
and embedding/index/query integration. Both runs emitted the existing Transformer
`cache_dir` deprecation warning. No Git access failures, dependency changes or
environment repairs occurred during Phase 51 verification.

`git diff --check` passed. Final SHA-256 comparison against the initial inventory
found changes only to `src/cli.py`, `tests/test_developer_mode.py` and
`docs/research/prototype-cli.md`, plus new `src/developer/continuity.py` and this
document. Phase 46-50 implementations and documents retain their initial bytes.
Benchmark datasets, Humanize, research evaluation/retrieval paths, snapshots and
frozen release artifacts are unchanged. `v0.1.1` still resolves to
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. No generated continuity/disaster recovery
journal records exist inside the source checkout.
