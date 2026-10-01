# Phase 48 - Developer retrieval deployment governance and audit

## Scope and baseline

This phase adds developer-only deployment accountability, operational checks and
investigation. It does not change retrieval execution, research methodology,
evaluation, benchmark datasets, Humanize artifacts, research snapshots or frozen
release artifacts. Phase 45 promotions remain the runtime authority. No quality
scores, rankings, user metrics or benchmark improvement claims are introduced.

The starting checkout contained modified `src/cli.py`,
`tests/test_developer_mode.py` and `docs/research/prototype-cli.md`, plus untracked
Phase 46/47 documentation, `configuration.py` and `deployment.py`. These existing
changes were retained. The baseline `v0.1.1` tag object was
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. A SHA-256 inventory of checkout files
was recorded outside the repository before Phase 48 edits.

Phase 47 already provided deployment planning, staging, validation, activation,
pause/resume, retirement, rollback tracking, comparison, attributed lifecycle
events and an append-only journal. The remaining gaps were normalized audit
records (especially for implicit changes to another deployment), a consolidated
ownership/compliance report, and convenient historical investigation. Ownership
uses the existing immutable `created_by` attribution; this is not authentication.

## Audit model and persistence

Every new deployment journal event uses schema version 2 and embeds
`audit_records`. Each audit record contains:

```json
{
  "event_id": "audit-00000004-deployment-001",
  "deployment_id": "deployment-001",
  "event_type": "activated",
  "created_at": "2026-09-29T00:00:00+00:00",
  "actor": "developer",
  "reason": "Select validated rollout",
  "metadata": {
    "sequence": 4,
    "action": "activate",
    "previous_stage": "validated",
    "stage": "active",
    "trigger_deployment_id": "deployment-001",
    "previous_deployment": null
  }
}
```

Types are `created`, `staged`, `validated`, `activated`, `paused`, `resumed`,
`rolled_back`, and `retired`. Metadata also retains validation or restoration
evidence where applicable. IDs combine journal sequence and affected deployment,
so the two changes in a replacement/rollback transaction have distinct IDs.
Activation emits retirement for the superseded deployment; rollback emits
activation for the restored deployment. Both preserve the initiating actor,
reason and triggering deployment ID, with `superseded`/`restored` metadata.

Audit records and lifecycle events publish together through the existing
exclusive atomic hard-link journal writer. There is no separate audit write that
can succeed or fail independently. Existing events are never rewritten, and
there is no edit/delete audit API. Readers return detached data. Replay checks
the journal chain, timestamps, attribution, transitions and exact agreement
between stored audit records and the transitions they describe. Invalid events
are rejected before publication; corrupt stored audit records fail closed.

Schema version 1 Phase 47 events remain supported. Their audit records are
derived deterministically from replay, without migrating or rewriting files.
New schema version 2 events can append to legacy journals. Records live only in
the external developer workspace's `optimization/deployments` directory.

## Read-only governance

`deployment_governance_check` returns `passed`, `warnings`, and `blocked` lists
of objects containing `check` and `detail`. It checks:

| Check | Meaning |
| --- | --- |
| ownership | Deployment creator attribution exists |
| source_configuration | Source snapshot exists, matches and remains eligible |
| promotion_approval | Source promotion and its approval/evidence remain valid |
| validation_evidence | Recorded validation exists and matches current prerequisites |
| rollback_target | Prior deployment exists and can be restored with matching evidence |
| lifecycle_state | Journal replay establishes a legal current state |
| audit_history | Journal sequence, chain and all embedded audit records agree |

Missing validation is blocked even for staged deployments: the report describes
readiness, not just whether staging succeeded. The first deployment explicitly
restores an empty reference and gets a rollback warning, not a fabricated target.
Closed deployments receive a historical warning; current prerequisites may have
changed since their original approval. Stale staging references are blocked.
Malformed deployment journals produce an `audit_history` blocker; audit and
inspection refuse to present them as trusted history. Unknown deployment IDs
return an error. No report repairs files, approves promotions or changes state.

## Investigation and history

```text
prototype local deploy-history --workspace EXTERNAL_PATH
prototype local deploy-audit DEPLOYMENT_ID --workspace EXTERNAL_PATH
prototype local deploy-governance-check DEPLOYMENT_ID --workspace EXTERNAL_PATH
prototype local deploy-inspect DEPLOYMENT_ID --workspace EXTERNAL_PATH
```

All four commands emit JSON and accept `--json`. No actor/reason or mutation
flags are needed. Governance findings are JSON data; blocked findings do not
make a successfully generated report return a nonzero CLI exit status.

Start with history to locate a deployment and its current state. Deployments
are newest-created first; events are newest-sequence first, with no truncation.
Use audit for the complete chronological per-deployment timeline, including
actors, reasons, validation and rollback. Inspect combines the deployment and
configuration snapshot, source promotion record, validation evidence, live
governance findings, audit timeline and rollback availability. A missing source
promotion is represented with its identifier and an unavailable reason, while
the historical deployment snapshot remains available.

Rollback inspection distinguishes eligible target availability from
`action_available`, which additionally requires the selected active/paused
deployment. Inspection never invokes rollback. Reviewing a deployment does not
activate configuration or promotion settings.

## Limitations

Local attribution is not an authenticated identity or a transferable ownership
system. Hash chains and application append-only behavior do not provide signed,
remote or filesystem-level immutable storage. A privileged filesystem writer
can replace the entire chain or truncate its tail; an external trusted head is
not maintained. Protect external workspace files with filesystem permissions.

History is complete relative to the retained valid journal. Failed transition
attempts do not change deployment state and are not successful lifecycle audit
events. There is no scheduler, automatic remediation, retention policy or audit
export service. Histories are unbounded. Configuration, promotion and deployment
journals have no shared transaction lock; serialize their mutations for a
consistent live governance view. Checks are operational evidence, not research
quality measurements or formal compliance certification.

## Validation and preservation

Seven added regression tests exercise audit lifecycle creation, immutable prior
bytes and detached results, invalid event rejection, atomic replacement and
restoration audit, legacy journal compatibility, live governance prerequisites,
all four CLI commands, read-only inspection and source/research isolation.
Existing Phase 46/47 tests cover configuration/promotion compatibility and
lifecycle regressions. Tests use temporary external workspaces.

The initial focused baseline process was interrupted before a final result was
available. The original Phase 47 deployment module was subsequently reconstructed
outside the checkout, verified byte-for-byte against its initial SHA-256 hash,
and loaded for an independent run of its 11 existing deployment tests. All 11
passed with zero skips, failures or errors (69.950 seconds, exit status 0).
The seven new focused audit tests also passed (29.737 seconds).

Final verification used Python 3.14.7:

| Command | Tests | Passed | Skipped | Failures/errors | Exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| `python -m unittest tests.test_developer_mode -v` | 106 | 106 | 0 | 0 | 0 |
| `python -m unittest discover -s tests -v` | 250 | 248 | 2 | 0 | 0 |

Focused duration was 395.433 seconds; full duration was 400.002 seconds. Both
include the existing Phase 47 regressions. The two skips require
`EMBEDDING_MODEL_CACHE` for real offline embedding inference/integration.
No dependency changes or environment repairs were needed. Test logs were kept
outside the checkout as `phase48-focused.log`, `phase48-full.log`, and
`phase48-phase47-baseline.log` in the system temporary directory.

`git diff --check` passed. A final SHA-256 comparison against the starting
inventory found changes only to `src/developer/deployment.py`, `src/cli.py`,
`tests/test_developer_mode.py`, and `docs/research/prototype-cli.md`, plus this
new document. Benchmark, Humanize, research evaluation/retrieval, configuration
implementation and prior-phase documents were unchanged from the baseline.
The `v0.1.1` tag still resolves to the baseline object above. No generated
deployment/audit records exist inside the source checkout.
