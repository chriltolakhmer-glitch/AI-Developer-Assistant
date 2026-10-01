# Phase 46 — Developer Retrieval Configuration Management

## Scope and baseline

This phase adds a developer-only configuration management layer over Phase 45
promotions. It does not change research retrieval, evaluation, benchmark datasets,
Humanize artifacts, frozen release artifacts, or tagged v0.1.1 behavior. It adds no
research quality, user scoring, or productivity metrics and makes no benchmark
improvement claim. Developer repositories remain outside research snapshots.

The initial checkout was clean at
`f21478808117a866f024e523ddc53b60fa4be3cc`.
The local v0.1.1 tag object was
`05688504f74ad51230ee1566fad8cda0f1b1ad97`.
The pre-change Phase 45 focused suite passed all 80 tests.

Existing capabilities included evidence-backed validation, governance approvals,
promotion lifecycle records, active runtime settings, retirement, and promotion
rollback. Missing capabilities were named configuration snapshots, independent
configuration versions, settings comparisons, and visible configuration-reference
activation and rollback history.

## Model and storage

`src/developer/configuration.py` stores immutable creation snapshots and lifecycle
events under `<external developer workspace>/optimization/configurations/`.
Read-only inspection does not initialize storage. Workspaces overlapping the
source checkout or configured research roots are rejected.

Each snapshot contains `config_id`, a workspace-wide increasing `version`,
`status`, `created_at`, `created_by`, `source_candidate`, `source_promotion`,
`repository_id`, `review_id`, `settings`, `previous_active`, and `changes`.
IDs use `retrieval-config-001`, `retrieval-config-002`, and so on. Lifecycle events
do not allocate new settings versions. Replaying events derives current statuses;
the original creation records are never rewritten or deleted.

Settings are copied from an existing, currently promoted source, preserving its
approved values. The supported executable setting remains Phase 45's
`relationship_factor` (finite numeric value from 1 through 2). Arbitrary ranking
weights, context limits, or duplicate-suppression controls are not introduced.
To change settings, use candidate validation, approval and promotion first, then
create a new snapshot. There is no command to edit an existing snapshot.

Creation records include differences from the active reference, including old
values. Events record reason, actor, timestamp, and linked promotion/candidate.
The diff utility recursively reports added, removed and changed settings using
arrays of path components; it can compare nested settings without quality scores.

## Lifecycle and workflow

Normal lifecycle: `draft → validated → active → retired`.
Drafts and validated snapshots may also be retired. Active snapshots may be
rolled back, and rolled-back snapshots may be retired. Other transitions fail.
The only restoration exception is rollback to the recorded previous active
snapshot, which returns that superseded snapshot from retired to active.

```text
prototype local config-create PROMOTION_ID --reason "Capture approved settings" --workspace EXTERNAL_PATH
prototype local config-validate retrieval-config-001 --reason "Check source evidence" --workspace EXTERNAL_PATH
prototype local config-activate retrieval-config-001 --reason "Select managed reference" --workspace EXTERNAL_PATH
prototype local config-status --workspace EXTERNAL_PATH
prototype local config-history --workspace EXTERNAL_PATH
prototype local config-diff 1 2 --workspace EXTERNAL_PATH
prototype local config-rollback retrieval-config-001 --reason "Restore prior reference" --workspace EXTERNAL_PATH
prototype local config-retire retrieval-config-001 --reason "Close snapshot" --workspace EXTERNAL_PATH
```

All commands emit JSON and accept `--json`. Mutations require `--reason` and
accept `--actor` (default `developer`). The Python API exposes
`create_configuration`, `transition_configuration`, `configuration_status`,
`configuration_history`, and `configuration_diff`.

Validation and activation require the source promotion to remain promoted, the
latest review to remain approved, validation evidence to match, and policy checks
to pass. Settings and source metadata must match the approved promotion.
Activation requires validated status and an unchanged prior active reference.
If another snapshot became active after creation, create and validate a fresh
snapshot; the stale draft cannot overwrite it.

Activation records the prior reference and retires the superseded snapshot in
the same event. History exposes this through `retired_configuration`.
Rollback accepts the currently active configuration ID, records the event, and
restores its saved prior reference (or no reference after the first activation).
Restoring a previous snapshot rechecks its promotion and policy evidence.
Out-of-order rollback or restoration of an ineligible source fails without a write.

## Runtime boundary and limitations

These commands manage **configuration references**. Phase 45's promotion journal
remains the authority for executable developer retrieval settings. Configuration
activation, retirement, and rollback do not promote, retire, or roll back source
promotions, and do not change source files or retrieval code. Use the existing
`optimize-promote`, `optimize-retire`, and `optimize-promote-rollback` workflow for
runtime changes. This separation prevents configuration records from bypassing
promotion governance. `config-status` declares `runtime_authority` and reports
`blocked` findings when a selected reference's source is no longer eligible.

There is one managed active reference per workspace; each snapshot identifies
its source repository. It is not an aggregate deployment of every repository's
settings. Snapshots remain recoverable for inspection and comparison even when
their promotion is retired; restoration requires an eligible source. Rollback
does not restore historical approvals or bypass current policy.

Events form a SHA-256 chain and are replay-validated. Complete events are flushed
and atomically published using exclusive hard links; competing configuration
writers fail rather than overwrite a sequence. Filesystem hard-link support is
required. There is no distributed transaction with the promotion/review stores;
serialize governance and configuration mutations in a workspace. Actor names
are local attribution, not authenticated identities. Hash chains detect broken
links and invalid replay but are not signatures and cannot prevent an authorized
filesystem user from rewriting the entire journal or truncating its tail. No
history pruning is performed.

## Validation and preservation

Regression coverage includes creation, validation, transitions, nested settings
diffs, version lookup, activation, retirement, exact reference rollback, history
preservation, stale-reference rejection, policy/approval compatibility, promotion
and governance audit compatibility, CLI dispatch, failed atomic publication,
corruption detection, read-only inspection, and protected-root isolation.

Verification used Python 3.14.7:

| Run | Tests | Passed | Skipped | Failures / errors |
| --- | ---: | ---: | ---: | ---: |
| Phase 45 focused baseline | 80 | 80 | 0 | 0 / 0 |
| `python -m unittest tests.test_developer_mode -v` | 88 | 88 | 0 | 0 / 0 |
| `python -m unittest discover -s tests -v` | 232 | 230 | 2 | 0 / 0 |

Both full-suite skips require `EMBEDDING_MODEL_CACHE` for real offline model
inference/integration. No dependency installation or research-code workaround was
needed. An initial targeted run exposed a test-helper import typo (one NameError);
it was corrected and its rerun passed. In-progress runs using that earlier test
module were stopped and replaced by the final complete runs above. A Transformer
cache-directory deprecation warning did not affect the results.
Windows PowerShell also labeled redirected unittest stderr as `NativeCommandError`
and returned wrapper status 1 despite the final unittest `OK` summaries. A separate
zero-exit Python stderr probe reproduced that labeling; the test counts above
come from the completed unittest summaries, not PowerShell's stderr classification.

Final preservation compared all 271 initially tracked paths with the starting
commit. Only the intended existing CLI source, developer test module, and CLI
documentation changed. All 58 identified retrieval/evaluation, benchmark,
Humanize, and release-related paths remained unchanged. The two new files are
the developer configuration module and this report. No generated configuration or
promotion JSON records were found in the checkout; tests used external temporary
workspaces. `git diff --check` passed.

The v0.1.1 tag object remains `05688504f74ad51230ee1566fad8cda0f1b1ad97`, pointing
to `51329285a882c1b7942d0a5b1c571e628d63dfb4`. Research is unchanged, benchmark
work remains unchanged/deferred, and Humanize remains unchanged/frozen.
