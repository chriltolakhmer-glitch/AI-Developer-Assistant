# Phase 52 - Developer retrieval recovery assurance and verification

## Scope and baseline

This phase centralizes developer recovery evidence, assurance lifecycle and
verification history. It adds current readiness visibility and history analysis
without executing recovery, changing retrieval behavior or introducing scores.
Research evaluation/retrieval methodology, benchmark data, Humanize, research
snapshots and frozen release artifacts remain outside this framework. No research
quality, user or productivity metrics or benchmark improvement claims are added.

The starting checkout contained modified `src/cli.py`, `tests/test_developer_mode.py`
and `docs/research/prototype-cli.md`, plus untracked Phase 46-51 documents and the
configuration/deployment/operations/reliability/continuity modules. Existing work
was preserved. No protected research paths appeared in the initial tracked diff.
`v0.1.1` initially resolved to `05688504f74ad51230ee1566fad8cda0f1b1ad97`. Before
edits, a SHA-256 inventory of tracked and nonignored untracked files was saved as
`phase52-baseline.json` in the system temporary directory, outside the checkout.

The baseline focused suite passed all 132 tests in 334.159 seconds, with zero
skips, failures or errors. The original CLI/test modules were imported before
implementation changes. Its log is `phase52-baseline-tests.log` in the system
temporary directory and includes all Phase 51 regressions.

Existing capabilities were disaster scenarios, continuity records, recovery
plans, recovery validation, simulation history and deployment audit history.
The gaps were centralized evidence, a clear assurance state, retained assurance
verification history, stale-evidence visibility, and combined recovery investigation.

## Assurance model

`src/developer/assurance.py` defines records with `assurance_id`, `scenario_id`,
`status`, `owner`, `created_at`, `checks`, and append-only `history`. Additional
fields retain the related deployment, original scenario snapshot, evidence and
validity policy. IDs use `assurance-001`. Creation starts pending, with an
attributed history event and empty checks/evidence.

| Current state | Allowed next states |
| --- | --- |
| `pending` | `verifying`, `expired` |
| `verifying` | `passed`, `failed`, `expired` |
| `passed` | `expired` |
| `failed` | `expired` |
| `expired` | None |

`assurance-verify` appends verifying, gathers live evidence, and atomically records
the derived passed/failed outcome and evidence snapshots. Callers cannot force a
pass that contradicts blockers. Interrupted verification can resume from verifying;
completed or expired records need a new assurance record. Unknown transitions,
repeated transitions, missing attribution/reasons and invalid validity windows
fail before publication. Scenario identity, owner, continuity/plan references and
retained history must still match the original linkage during verification.

The assurance owner is distinct from the scenario and recovery-plan owners.
All are local attribution, not authenticated identity. `recovery-assurance` returns
the latest record's owner, historical records/checks, simulations, evidence and
effective `recovery_readiness`. With no assurance record, readiness is pending
and no assurance owner is assigned. Available scenario/plan ownership is still
visible in evidence. Reports do not create assurance records implicitly.

## Immutable recovery evidence

Each completed verification stores nine evidence types:

| Evidence type | Source and meaning |
| --- | --- |
| `recovery_plan` | Selected plan exists and remains compatible with continuity references |
| `rollback_reference` | Recorded predecessor and configuration, or explicit empty initial rollback |
| `configuration_history` | Retained current/previous configuration snapshots |
| `deployment_audit` | Complete retained deployment audit timeline |
| `ownership` | Scenario and captured recovery-plan attribution |
| `previous_simulations` | Completed Phase 51 validation attempts and results |
| `continuity_record` | Dependencies, restoration knowledge and continuity validation history |
| `deployment_history` | Retained deployment record and lifecycle history |
| `live_validation` | Current disaster/reliability/governance findings; availability does not imply a pass |

An evidence record contains `evidence_id`, `evidence_type`, `status`, `source`,
`checked_at`, `expires_at`, `content`, `content_digest` and a descriptive finding.
For example, a rollback reference uses the recovery-plan ID as its source.
Evidence IDs combine assurance ID and evidence position. Stored status is either
available or missing, describing the observation at capture time. Missing includes
evidence that is absent, unreadable, superseded or cannot currently be trusted.
Such observations always appear as warnings in evidence reports. They also block
assurance verification rather than being treated as proof of readiness.

Records are immutable through the application. New checks never overwrite earlier
evidence. Availability content is normalized to JSON-compatible structures before
publication, so newly returned evidence agrees with replayed evidence. Check times
are separated from stable content digests: repeated checks against unchanged
sources agree even when their observation timestamps differ.

`recovery-evidence` separates current available/missing observations, retained
recorded evidence and expired evidence views. Each expired view references the
original evidence and explains the cause; the original status/content is unchanged.
Related records include scenario, deployment, continuity, recovery plan and
assurance IDs. No read initializes the assurance journal.

## Expiration and current readiness

Evidence validity defaults to 24 hours after capture. Creation accepts integer
`--valid-for-hours` values from 1 through 8760. An evidence view expires when:

- Its validity deadline is reached (the deadline itself is expired).
- Current source, availability or content no longer matches its snapshot.
- Its assurance record was explicitly expired.

There is no scheduler or implicit expiration write. A recorded pass can remain
historically passed while current recovery readiness is expired. A fresh read
observes sources rather than refreshing the old validity deadline. Source-change
freshness is a live comparison, not a permanent mutation: if identical valid
sources return before the deadline, the comparison can agree again. Explicit
expiry and elapsed time still apply.

New assurance records have independent evidence windows. Verification uses fresh
observations and the latest simulation; it does not inherit old expiration.
However, changed simulation prerequisites require an explicit `disaster-test`
before a new assurance can pass. Old evidence and failures remain preserved.

## Read-only history verification

`recovery-verify-history SCENARIO_ID` checks:

| Check | Requirement |
| --- | --- |
| `previous_checks` | Completed simulation history exists |
| `evidence_current` | Required evidence is available, the latest simulation matches live prerequisites, and the latest completed assurance evidence is current if present |
| `recovery_plan` | Referenced plan remains available and compatible |
| `rollback_reference` | Recorded predecessor is valid, or explicitly empty for an initial rollout |
| `continuity_records` | Continuity knowledge and dependency history replay completely |
| `live_validation` | Existing disaster/reliability/governance findings have no blockers |
| `scenario_state` | Scenario is currently validated, not planned/testing/failed/retired |

It returns passed/warnings/blocked findings and separate missing-evidence warnings.
Before any assurance capture, current validated simulation history can satisfy
history verification while assurance readiness remains pending. Verification
reports identify the previous completed assurance, when one exists. They inspect
the latest completed evidence even if a newer pending assurance has not finished.

If continuity history is missing or corrupt for a known assurance scenario, the
captured scenario is used only to identify historical records. All live evidence
is marked unavailable with warnings and verification blockers; retained snapshots
are never substituted as current proof. Unknown scenario IDs without retained
assurance data are errors. Corrupt assurance journals fail rather than presenting
untrusted evidence as history. No command repairs or restores journal files.

## Recovery history analysis

`recovery-history-analysis` combines Phase 49 incidents/recovery actions and
resolution history, Phase 51 simulation attempts, assurance histories, earlier
failed simulations/assurances and current unresolved findings. Historical failures
remain visible after a later successful verification. Unresolved findings are
recomputed from current checks, so old failures are not automatically reported as
current blockers. Advisory warnings, including an initial empty rollback reference,
remain visible alongside blockers.

Unreadable operations or continuity history produces explicit unavailability
findings. Assurance snapshots remain in assurance history for investigation;
unavailable live simulation history is not fabricated from saved snapshots. There
are no recovery scores, success rates, user metrics or productivity metrics.

## CLI workflow

1. Prepare a Phase 50 recovery plan and run a Phase 51 scenario validation explicitly.
2. Inspect read-only `recovery-assurance SCENARIO_ID`, `recovery-evidence SCENARIO_ID`
   and `recovery-verify-history SCENARIO_ID` to identify missing or stale evidence.
3. Create an attributed record with `assurance-create SCENARIO_ID --owner OWNER
   --reason REASON`, optionally setting its validity window.
4. Use `assurance-verify ASSURANCE_ID` to retain the outcome and immutable evidence.
5. Revisit the reports and `recovery-history-analysis` during handoff. When evidence
   or prerequisites change, update the relevant records through their existing
   explicit workflows, rerun simulation as necessary, and create a new assurance.
6. Use `assurance-expire ASSURANCE_ID --reason REASON` to explicitly end its validity.

All commands emit JSON and accept `--workspace EXTERNAL_WORKSPACE` and `--json`.
Mutations accept `--actor` (default `developer`); creation/expiry require reasons
and verification provides an overridable default reason. Owner defaults to
`developer`. Successfully generated reports and recorded failed verifications
exit zero; callers must inspect their findings. The [CLI guide](prototype-cli.md)
contains full examples.

## Isolation and limitations

Records live only in the external workspace's `optimization/assurance` directory.
Existing checkout/research overlap and containment guards apply. Numbered events
are hash chained, replay validated, flushed and published by exclusive atomic
hard link. A competing publication cannot overwrite existing events. An outcome,
checks and evidence publish together. Readers return detached data and never
write deployment, configuration, plan, incident or simulation journals.

Local attribution is not authentication. Hash chains are not signed or protected
against a privileged writer replacing the entire chain or truncating its tail.
There is no external trusted head, cross-journal lock, background monitor, backup
restoration, automatic recovery, rollback or activation. Histories and evidence
snapshots are unbounded and reports replay retained journals; no retention or
archival service is provided. Clock-based expiry uses the local UTC clock.
Serialize related mutations for a consistent operational view. Assurance is
point-in-time evidence about reference readiness, not a guarantee that real
recovery will succeed, and does not change promotion runtime authority.

## Validation and preservation

Nine regression tests cover creation/lifecycle, invalid and forced transitions,
immutable evidence, repeatability, exact expiration boundaries, manual expiry,
source changes, renewal, missing evidence, lost continuity, read-only verification,
historical failures versus current findings, interrupted publication, evidence
corruption, source/research isolation, CLI behavior and prior-phase compatibility.
All use temporary external workspaces. Existing Phase 51 regressions are retained.

The initial assurance-specific run completed nine tests in 51.732 seconds with
one failure: newly returned evidence used tuples for finding pairs, while JSON
replay returned lists. Capture was corrected to use lists consistently; the
preservation assertion was retained. Its log is `phase52-assurance-tests.log`.
The targeted retry passed all nine tests in 50.536 seconds, with zero skips,
failures or errors and exit status 0 (`phase52-assurance-retry.log`). The required
focused and full suites run sequentially with Python subprocess logging to retain
actual exit statuses. All logs are outside the checkout in the system temporary
directory.

Final verification used Python 3.14.7:

| Command | Tests | Passed | Skipped | Failures/errors | Exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| `python -m unittest tests.test_developer_mode -v` | 141 | 141 | 0 | 0 / 0 | 0 |
| `python -m unittest discover -s tests -v` | 285 | 283 | 2 | 0 / 0 | 0 |

Focused duration was 473.049 seconds (`phase52-focused.log`); full duration was
429.972 seconds (`phase52-full.log`). Both retain all Phase 51 regressions. The
two full-suite skips require `EMBEDDING_MODEL_CACHE` for real offline inference
and embedding/index/query integration. Both runs emitted the existing Transformer
`cache_dir` deprecation warning. No dependency changes, permission changes or
environment repairs were needed.

`git diff --check` passed. Final SHA-256 comparison against the starting inventory
found changes only to `src/cli.py`, `tests/test_developer_mode.py` and
`docs/research/prototype-cli.md`, plus new `src/developer/assurance.py` and this
document. Phase 46-51 implementations and documents retain their original bytes.
Benchmark datasets, Humanize, research evaluation/retrieval paths, snapshots and
frozen release artifacts are unchanged. `v0.1.1` still resolves to
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. No generated recovery assurance journal
records exist inside the source checkout.
