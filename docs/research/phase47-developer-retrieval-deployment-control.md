# Phase 47 — Developer Retrieval Configuration Deployment Control

## Scope and baseline

Phase 47 adds explicit deployment control for developer configuration references.
Research evaluation and retrieval methodology, benchmark datasets/artifacts,
Humanize artifacts, frozen release artifacts, and v0.1.1 behavior remain unchanged.
No developer repositories enter research snapshots. No quality scores, deployment
rankings, productivity metrics, or benchmark improvement claims are introduced.

The starting commit was `f21478808117a866f024e523ddc53b60fa4be3cc`.
The checkout retained the uncommitted Phase 46 implementation: modified CLI,
developer tests and CLI documentation, plus the new configuration module and
Phase 46 report. SHA-256 hashes of all 271 tracked files and both new Phase 46
files were captured outside the checkout before Phase 47 edits. The Phase 46
baseline command `python -m unittest tests.test_developer_mode -v` passed all
88 tests, with no skips, failures or errors.

Phase 46 already provided snapshots, lifecycle checks, configuration activation
and rollback references, append-only history, and settings diffs. It lacked a
distinct staged rollout, deployment validation records, deployment history,
pause/resume controls, and deployment rollback visibility.

## Deployment model

`src/developer/deployment.py` stores events in
`<external developer workspace>/optimization/deployments/`. Inspection does not
initialize an absent workspace. Existing checkout/research-root isolation and
contained-path checks apply to every read and write.

Each deployment contains `deployment_id`, `config_id`, `stage`, `created_at`,
`created_by`, `validation`, and `history`. It also preserves an immutable copy of
the configuration metadata/settings and `previous_deployment`. IDs are allocated
in workspace order (`deployment-001`, `deployment-002`, ...). Configuration
status is checked live, not frozen into the immutable settings snapshot.

There is one selected deployment per workspace. Its stage is active or paused.
`active_deployment` is null while paused; `selected_deployment` preserves its
reservation and rollback point. Staged and validated deployments remain visible
separately. No percentage rollout, remote deployment, or per-user targeting exists.

## Lifecycle and explicit controls

| Current stage | Allowed next stages |
| --- | --- |
| planned | staged, retired |
| staged | validated, retired |
| validated | active, retired |
| active | paused, retired, rolled_back |
| paused | active through explicit resume, retired, rolled_back |
| rolled_back | retired |
| retired | none, except restoration of an exact superseded rollback point |

Every transition appends an attributed event with a reason and timestamp.
Activating a replacement records the previous deployment's retirement and the new
activation atomically in one event. Rollback similarly records both restoration
and rollback histories in one event. Invalid transitions never append events.

```text
prototype local deploy-stage CONFIG_ID --reason "Stage approved configuration" --workspace EXTERNAL_PATH
prototype local deploy-validate DEPLOYMENT_ID --reason "Check rollout prerequisites" --workspace EXTERNAL_PATH
prototype local deploy-activate DEPLOYMENT_ID --reason "Select validated rollout" --workspace EXTERNAL_PATH
prototype local deploy-status --workspace EXTERNAL_PATH
prototype local deploy-diff DEPLOYMENT_A DEPLOYMENT_B --workspace EXTERNAL_PATH
prototype local deploy-pause DEPLOYMENT_ID --reason "Pause rollout reference" --workspace EXTERNAL_PATH
prototype local deploy-resume DEPLOYMENT_ID --reason "Recheck and resume" --workspace EXTERNAL_PATH
prototype local deploy-rollback DEPLOYMENT_ID --reason "Restore prior deployment" --workspace EXTERNAL_PATH
prototype local deploy-retire DEPLOYMENT_ID --reason "Close rollout" --workspace EXTERNAL_PATH
```

All commands emit JSON and accept `--json`. Mutations require `--reason` and accept
`--actor` (default `developer`). The Python API exposes `create_deployment` for a
planned record, `stage_deployment`, `transition_deployment`, `deployment_status`,
and `deployment_diff`.

`deploy-stage` requires a validated or already-active configuration and its
currently approved/promoted source. It records planned and staged events without
validating or activating the deployment. A second live deployment of the same
configuration is rejected. If publication stops after the planned event, retrying
`deploy-stage` resumes that plan. A stale plan must be retired before restaging.

## Validation evidence and activation

`deploy-validate` explicitly checks and records:

- `configuration_valid`: the referenced snapshot is still validated/active and
  its immutable settings and source metadata match.
- `policy_check_passed`: current governance checks pass; the full policy result
  is preserved, including warnings and individual checks.
- `rollback_available`: the previous deployment/configuration can be restored,
  or there is an explicit empty initial reference to restore.
- `source_promotion` and `review_id`: the existing approved promotion and review.
- `previous_deployment` and `previous_active_configuration`: the deployment
  rollback point, distinct from the independently managed configuration reference.
- `configuration_active_reference`: the Phase 46 active reference at validation.

Validation does not approve a promotion or create a human review. Failed gates
return an error without recording a successful validation or changing the stage.

Activation requires the validated stage, unchanged evidence, and the same prior
deployment reference. It reruns configuration, approval, governance, and rollback
checks. A changed reference or evidence requires a newly staged and validated
deployment. Resume uses the same evidence checks and accepts only paused records.
A paused selected deployment must be resumed, retired, or rolled back before a
replacement can activate.

`deploy-status` includes all deployments, per-record validation and lifecycle
histories, the event journal, staged deployments, selected/active IDs, and live
`blocked` findings for stale or ineligible records. Inspection never repairs or
automatically approves records.

## Rollback and comparison

`deploy-rollback` takes the currently selected deployment ID, including a paused
selection, and restores its exact previous deployment reference. Rolling back the
first deployment restores no selection. Later deployments must be undone first.
The target must have been superseded by activation, and its saved validation must
still match current configuration and governance evidence. Retired/withdrawn
configurations or changed approvals block restoration. Records and configuration
history remain intact; no source files are restored or modified.

`deploy-diff` provides separate configuration, deployment metadata, validation,
and lifecycle differences. Differences report added/removed values and old/new
values, using arrays of path components. Lists such as history are compared as
values. There are no scores or deployment rankings.

## Runtime boundary and limitations

Deployment activation selects a **deployment reference**. It does not call
configuration activation, change the Phase 46 active reference, or apply settings
to retrieval. Phase 45 promotions remain the runtime authority, explicitly named
in deployment status. Deployment pause, retirement, and rollback likewise do not
pause or reverse runtime promotions. Runtime changes still require the existing
governed promotion workflow. Deployment controls cannot bypass that workflow.

Snapshots/events are flushed and published using exclusive atomic hard links.
Competing deployment writers cannot overwrite the same sequence; failures preserve
published history and remove temporary files. Events form a SHA-256 chain, and
replay checks enforce lifecycle transitions, evidence and reference consistency.
Local actor names are attribution, not authenticated identities. Hashes do not
prevent an authorized filesystem user from replacing an entire journal or
truncating its tail. Protect workspace files with filesystem permissions.

There is no transaction across configuration, promotion, review, and deployment
journals. Serialize their mutations in a workspace; fresh validation and status
checks detect changes but do not provide a cross-process governance lock. History
grows without pruning. Retiring a deployment removes its selection without
restoring its predecessor; use rollback for restoration.

## Verification and preservation

Regression tests cover creation and explicit staging, transitions, approval and
validation gates, stale evidence/reference rejection, activation, pause/resume,
retirement, exact and empty rollback, rollback eligibility, comparisons, CLI,
configuration/promotion/governance audit compatibility, failed atomic publication,
recovery of partially published staging, corruption detection, and isolation.

Verification used Python 3.14.7. The initial targeted deployment run passed all
10 tests, followed by an additional staging-recovery regression in the complete
suites. The focused command `python -m unittest tests.test_developer_mode -v`
passed all 99 tests (88 prior-phase tests and 11 deployment tests), with zero
skips, failures or errors and Python exit status 0.

The full command `python -m unittest discover -s tests -v` ran 243 tests:
241 passed, 2 skipped, zero failures/errors, and Python exit status 0. Both skips
require `EMBEDDING_MODEL_CACHE` for real offline embedding inference/integration.
A Transformer cache-directory deprecation warning was non-fatal. No dependency
changes or environment repairs were needed. Test output was captured directly by
a Python subprocess to avoid PowerShell classifying unittest stderr as a native
command error. All test logs remain outside the checkout.

Final SHA-256 comparison checked all 273 captured baseline files. Only the shared
CLI source, developer tests and CLI documentation changed during Phase 47. The
Phase 46 configuration implementation/report and all 58 identified protected
retrieval, evaluation, benchmark, Humanize and release-related paths matched
their baseline hashes. New Phase 47 files are the deployment module and this
report. No generated deployment JSON records exist inside the checkout.
`git diff --check` passed.

The v0.1.1 tag object remains `05688504f74ad51230ee1566fad8cda0f1b1ad97`.
Research is unchanged; benchmark work remains unchanged/deferred; Humanize
remains unchanged/frozen. Existing uncommitted Phase 46 work was preserved.
