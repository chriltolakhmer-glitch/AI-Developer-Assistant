# Phase 49 - Developer retrieval deployment operations and incident management

## Scope and baseline

This phase adds operational records, read-only health, incident investigation and
manual recovery tracking for developer deployment references. It does not change
retrieval execution, research methodology, research evaluation, benchmark data,
Humanize, research snapshots or frozen release artifacts. There are no quality,
productivity or user scores. Phase 45 promotions retain runtime authority.

The initial checkout had modified `src/cli.py`, `tests/test_developer_mode.py`
and `docs/research/prototype-cli.md`, plus untracked `configuration.py`,
`deployment.py` and Phase 46-48 documents. Those changes were preserved.
`v0.1.1` initially resolved to `05688504f74ad51230ee1566fad8cda0f1b1ad97`.
The initial tracked diff contained no protected research paths. A SHA-256
inventory of tracked and nonignored untracked files was saved outside the checkout
as `phase49-baseline.json` in the system temporary directory before edits.

The baseline developer suite passed 106 tests in 310.701 seconds, with no skips,
failures or errors. That process imported the original modules and tests before
implementation edits, and includes all Phase 48 regressions.

Existing capabilities were attributed deployment audit history, governance checks,
deployment inspection/history, rollback tracking and configuration lifecycle
management. The operational gaps were a consolidated health state, incident
ownership, a persistent investigation timeline and explicit links between
incidents, recovery actions and deployments.

## Operational model and storage

`src/developer/operations.py` supports `health_check`, `incident`, `recovery`,
`rollback` and `investigation` operation types through `create_operation`.
An explicit health-check operation is a tracking record; calling
`deployment_health` never creates one. Likewise, rollback/recovery operation
types describe work and cannot execute it.

Every operation contains:

```json
{
  "operation_id": "operation-001",
  "deployment_id": "deployment-001",
  "type": "incident",
  "status": "open",
  "created_at": "2026-09-29T00:00:00+00:00",
  "owner": "developer",
  "reason": "Investigate deployment readiness",
  "history": [],
  "deployment_snapshot": {},
  "resolution": null
}
```

This abbreviated example omits history and snapshot contents. Actual records
include an initial attributed `open` event and an immutable deployment ID,
configuration snapshot and deployment history prefix. Journal replay checks that
the snapshot still corresponds to retained deployment history. Ownership stays
fixed; subsequent actors identify who recorded each action. IDs share one
operation sequence across all types, so incident IDs need not be contiguous.

Legal transitions are `open -> investigating`, `open -> resolved`,
`investigating -> resolved`, and `resolved -> closed`. All others, including
repeats and reopening, fail before publication. Nonempty attribution/reasons,
timezone-aware timestamps, types, IDs and deployment references are validated.

Records live in the external developer workspace's `optimization/operations`.
Existing checkout/research overlap and containment gates apply. Events are
numbered, hash chained and append-only through the application. Writers validate
in memory, flush a temporary file, and publish by exclusive atomic hard link.
Competing publication fails without overwriting earlier events. Reads replay the
journal and return detached records; they do not initialize a workspace.

Resolving an incident requires a nonempty recovery action description. One event
atomically resolves the incident and creates its linked, resolved `recovery`
operation, whose history records open and resolved states at that same sequence.
Both sides remain linked through incident/recovery IDs. There is no independent
second write that can leave a resolution without its recovery record. Optional
rollback references must identify a retained `rolled_back` audit event for the
same deployment; references to missing events or another deployment fail.

## Read-only health and inspection

`deployment_health` reuses Phase 48 inspection and live governance checks. It
reports deployment state, current configuration state, governance findings,
rollback target/action availability and the last ten audit events. It returns:

| Status | Meaning |
| --- | --- |
| `blocked` | One or more current governance blockers |
| `warning` | No blockers, but warnings or a deployment not currently active |
| `healthy` | Active deployment with neither blockers nor warnings |

An initial rollout has a warning because rollback restores an empty reference.
`rollback_available` means an action is currently available for the selected
active/paused deployment; the nested rollback object also distinguishes target
eligibility. Historical deployments are not reported healthy merely because
their old validation passed. Missing configuration is reported unavailable;
corrupt deployment journals or unknown IDs raise an error rather than a trusted
health report. Successful reports exit zero even when health is blocked.

These checks never fix evidence, append records, execute rollback or change
configuration, promotion or retrieval behavior. They evaluate operational
prerequisites, not service telemetry or retrieval quality. Health does not infer
failure from an open incident or infer recovery from a resolved incident.

Incident inspection includes the original snapshot, live deployment history,
audit events, live health/configuration/governance, rollback availability,
investigation history and resolution. This preserves the distinction between
what was captured when the issue was opened and what is true now.

## Developer workflow

1. Use `deploy-health DEPLOYMENT_ID` to inspect readiness and audit evidence.
2. Use `incident-create DEPLOYMENT_ID --owner OWNER --reason REASON`; retain the
   returned `operation_id` as the incident ID.
3. Use `incident-investigate INCIDENT_ID --reason REASON`, `incident-status`, and
   `incident-inspect INCIDENT_ID` to record investigation and review evidence.
4. Perform any recovery explicitly through existing governed workflows. Operations
   tracking never invokes those workflows. For a manual deployment rollback,
   obtain its audit event ID from `deploy-audit` after it succeeds.
5. Use `incident-resolve INCIDENT_ID --reason REASON --recovery-action DESCRIPTION`,
   optionally with `--rollback-reference AUDIT_EVENT_ID`, to record the outcome.
6. Use `incident-close INCIDENT_ID --reason REASON` after review, and
   `recovery-history` to inspect previous incidents, recovery actions, rollback
   references and resolutions.

All commands accept `--workspace EXTERNAL_WORKSPACE` and `--json` and emit JSON.
Mutations accept `--actor` with default `developer`; owner defaults to `developer`.
`incident-diff INCIDENT_A INCIDENT_B` compares affected deployments, captured
configuration values, incident timelines and resolution details. It creates no
scores. The [CLI guide](prototype-cli.md) provides full command examples.

## Limitations

Owner/actor names are local attribution, not authenticated identities. Recovery
descriptions are developer attestations, not execution evidence. Resolution is
allowed without changing deployment state and does not bypass governance or
certify successful recovery. There is no automatic fix, rollback, scheduler,
alerting, source edit, ownership reassignment, reopening or free-form note API.

Hash chains detect broken retained sequences and modified preceding events, but
are not signed or filesystem-enforced immutability. A privileged writer can
rewrite the whole chain or truncate its tail. Histories are unbounded; there is
no shared cross-journal transaction lock. Serialize configuration, promotion,
deployment and operation mutations when a consistent live view matters. A
missing/corrupt deployment journal prevents trusting linked operation records.

## Validation and preservation

Eight operations regression tests cover all operation types, ownership and
deployment links, lifecycle and invalid transitions, atomic resolution/failure,
append-only bytes, read-only health/inspection, governance changes, manual
rollback audit references, recovery history, comparisons, malformed journals,
external-workspace isolation and the complete CLI workflow. Existing Phase 48
tests remain in the focused and full suites. Tests use temporary external
workspaces; no operational records are generated in the checkout.

The initial operations-only run passed all eight tests in 35.682 seconds with
zero skips, failures or errors. Windows PowerShell's direct `2>&1` redirection
wrapped unittest's normal stderr progress as `NativeCommandError` and returned
shell status 1 despite unittest reporting `OK`. The required final suites use
Python subprocess logging to preserve the actual Python exit status. No dependency
or environment repair was required. An existing Transformer `cache_dir`
deprecation warning was also emitted by the baseline suite.

Final verification used Python 3.14.7:

| Command | Tests | Passed | Skipped | Failures/errors | Exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| `python -m unittest tests.test_developer_mode -v` | 114 | 114 | 0 | 0 | 0 |
| `python -m unittest discover -s tests -v` | 258 | 256 | 2 | 0 | 0 |

Focused duration was 392.128 seconds; full duration was 397.141 seconds. Both
include the unchanged Phase 48 regression tests. The two full-suite skips require
`EMBEDDING_MODEL_CACHE` for real offline inference and embedding/index/query
integration. Logs remain outside the checkout in the system temporary directory
as `phase49-focused.log`, `phase49-full.log` and `phase49-operations.log`.

`git diff --check` passed. Final SHA-256 comparison against the initial inventory
found modifications only to `src/cli.py`, `tests/test_developer_mode.py` and
`docs/research/prototype-cli.md`, plus new `src/developer/operations.py` and this
document. Existing configuration/deployment implementations and Phase 46-48
documents are unchanged from the starting checkout. Benchmark datasets, Humanize,
research evaluation/retrieval paths, snapshots and frozen release artifacts
remain unchanged. `v0.1.1` still resolves to
`05688504f74ad51230ee1566fad8cda0f1b1ad97`. No generated operations directory or
operational journal records exist inside the source checkout.
