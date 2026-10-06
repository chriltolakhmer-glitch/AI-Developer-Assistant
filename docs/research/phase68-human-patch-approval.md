# Phase 68 — Human Patch Approval

## Post-roadmap pilot-readiness integration

An approval retains the draft's allowed target paths and binds the exact supplied patch hash and repository state. The patch may modify a strict subset of the allowed paths. Approval never authorizes a path outside that maximum scope or a different diff, and it does not authorize test execution.

## Purpose

Phase 68 records a solo developer's explicit decision about one Phase 67
PatchDraft. It grants narrow future authority for the exact reviewed patch and
repository state. Phase 68 does not apply patches.

## Solo-developer design

There are two commands: `approve-patch` and `reject-patch`. The developer chooses
one explicitly. `approved_by` is a short audit label, defaulting to
`local-developer`; it is not identity verification or authentication. An optional
short note records review context without changing the authorized scope.

## Architecture boundary

`ProposedAction → PatchDraft → human decision → AuthorizationRecord → stop`.
Proposed, drafted, approved, and executed are distinct states. An approval
permits a later phase to consider applying the patch; `executed` remains false.
No Phase 69 operation is implemented here.

## AuthorizationRecord

`AuthorizationRecord` is a frozen, slotted dataclass. Its fields are
`authorization_id`, `schema_version`, `source_action_id`, `source_patch_id`,
`source_patch_run_id`, `repository_id`, `repository_path`, `current_commit`,
`working_tree_sha256`, `patch_sha256`, `target_paths`, `decision`, `decided_at`,
`approved_by`, `execution_authorized`, `allowed_operation`, `executed`, and
`note`. The patch run ID lets a later phase locate the exact stored draft.
The authorization ID detects ordinary record alteration by hashing the record
fields; it is not a signature or an identity claim.

## Approve/reject model

Approval requires a nonblocked, intact PatchDraft and matching live repository
state. It records `decision=approve`, `execution_authorized=true`, and
`allowed_operation=apply_exact_patch`. Rejection records `decision=reject`,
`execution_authorized=false`, and `allowed_operation=none`. Both record
`executed=false`. A blocked draft may be rejected but cannot be approved.
The record validator rejects missing or unknown decisions and inconsistent flags.

## Patch binding

The decision retains the Phase 66 action ID, Phase 67 patch ID and run ID, the
SHA-256 hash of the complete diff text, and the exact target paths. Before a
decision, the loader checks the Phase 67 run's canonical JSON, deterministic
run identity, metadata, typed PatchDraft identity, and diff structure. A changed
artifact requires a new draft. `validate_exact_patch_authorization` is a
read-only binding check for a later phase; it rejects a changed patch or record.

## Repository-state binding

Approval checks the repository's resolved path, repository ID, current commit,
and working-tree fingerprint against the draft. A changed state fails closed
with a replan/redraft instruction. The same read-only binding check repeats
these comparisons when a later phase inspects an approval. Rejection does not
grant authority even if the repository has since changed.

## CLI

```text
prototype local approve-patch REPOSITORY --patch-run-id RUN [--workspace PATH] [--approved-by LABEL] [--note TEXT] [--json]
prototype local reject-patch REPOSITORY --patch-run-id RUN [--workspace PATH] [--approved-by LABEL] [--note TEXT] [--json]
```

Approval output says `APPROVED FOR FUTURE PATCH APPLICATION — NOT APPLIED`;
rejection output says `PATCH REJECTED — NO EXECUTION AUTHORITY`. Both show the
decision record, patch and repository IDs, target paths, allowed operation and
developer audit label. JSON output includes the typed record and external run ID.

## Storage

Decisions are immutable run records under the existing external
`DeveloperWorkspace/runs` structure. The target repository stores no decision
artifact. Repeated decisions may create separate records; no supersession or
multi-reviewer workflow is introduced.

## Safety

Approval performs read-only Git and source inspection. It does not apply the
patch, change target source or Git state, run target tests, call a network model,
or perform a governance, readiness, release or deployment transition. The only
future operation named by an approval is `apply_exact_patch`.

## Validation

Focused authorization and Phase 67 regression tests, the changed-file phase
gate, and an external Git repository pilot validate the boundary. Counts,
durations, skips, and pilot results are recorded in the Phase 68 completion
report. Generated logs and pilot state remain outside the source checkout.

## Limitations

The audit label is not authenticated. Deterministic IDs and hashes detect
ordinary alteration but do not provide signatures or protection from an actor
who rewrites all related records. The diff validator checks format and scope;
Phase 68 does not establish that the patch applies or passes target tests.

## Deferred work

Phase 69 will handle controlled patch application. Target tests, observations,
rollback, repair, deployment, and lifecycle closure remain deferred.
