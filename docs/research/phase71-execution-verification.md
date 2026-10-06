# Phase 71 — Execution Verification and Lifecycle Evidence

## Post-roadmap pilot-readiness integration

For a linked draft, Phase 71 loads its exact source plan run rather than searching by a proposal ID that can be shared by repeated plans with different expected tests. It checks the planned exact identities and their evidence against the Phase 70 executed set, and reports unknown or unevidenced selection as uncertainty. Proposal and approval paths are allowed scope; the approved diff and Phase 69 recorded paths define actual scope. Verification requires actual paths to remain within approval and match the observed patch, including Git diffs whose hunk headers add a function-context label.

## Purpose

Phase 70 records bounded test execution facts. Phase 71 verifies that one exact Phase 65–70 evidence chain matches its approved intent and records a compact external evidence summary for human lifecycle review. Verification does not decide whether an action should be closed, approved, rejected, repaired, retried, rolled back, or advanced.

The flow is:

`Phase 65 plan → Phase 66 ProposedAction → Phase 67 PatchDraft → Phase 68 approval → Phase 69 application → Phase 70 test plan/observation → Phase 71 verification evidence → human review → STOP`.

Phase 72 owns controlled follow-up and recovery evaluation and is not invoked here.

## Evidence inputs and integrity

The command accepts exact Phase 69 application and Phase 70 observation run IDs. It resolves the unique Phase 68 authorization, Phase 67 patch run, and Phase 65 plan linked through their recorded identities. Each consumed run must have canonical JSON, the expected command and mode, a matching workspace binding, and a content-derived run ID. Phase 66, Phase 67, and Phase 68 typed contracts are reconstructed and validated with their existing validators. Phase 69 is revalidated using the Phase 70 historical binding checks.

The verifier compares the plan's repository identity and path, ProposedAction identity, PatchDraft identity and SHA-256, authorization identity and decision, Phase 69 execution identity/status, Phase 70 plan identity, test observation bindings, and external log references and hashes. Missing, malformed, tampered, ambiguous, or cross-repository links are recorded as specific deviations when safe evidence remains available; records that cannot be trusted fail closed.

## Scope and execution comparisons

Phase 65 implementation targets are compared with the Phase 66 target paths, symbols, evidence references, and unresolved evidence. The Phase 67 patch paths must be a nonempty subset of the proposed paths, with the same proposal symbols and evidence references. Phase 68 must approve the exact patch hash, repository state, and patch paths. Phase 69 actual paths must equal the approved paths and stay within the Phase 66 scope.

The verifier compares the current Git diff to the recorded Phase 69 post-application diff, checks its file sections and hunk lines against the approved PatchDraft, and validates the patch hash against both Phase 67 and Phase 68. It checks the recorded Phase 69 applied status, HEAD-before/after, semantic Git index evidence, and refs evidence. The Phase 69 run records the semantic index digest from `git ls-files --stage -z` and the refs digest after application, alongside whether each remained unchanged.

## Test comparison and factual outcome

The Phase 65 exact selected test identities are compared as a sorted set with the exact Phase 70 `TestExecutionPlan` and `TestExecutionObservation` identities. Missing and unexpected identities are listed separately. A Phase 65 plan that recommends modules but does not record exact tests cannot establish an exact test match. Phase 70 identities must be unique, canonical, and present in the repository's unittest catalog. The Phase 70 deterministic test-plan identity, observation/run link, counts, exit status, stdout/stderr references, and log SHA-256 values are checked.

The summary retains test count, passed, failed, error, skipped, exit code, status, log hashes/references, before/after source state, and unexpected repository changes. Failure, error, side effects, inconsistent counts, or a test-set mismatch never becomes a verified result.

## `ExecutionVerificationSummary`

The frozen, slotted summary records a deterministic `verification_id`, upstream IDs, repository identity/path, planned, approved, and actual target paths, expected and executed tests plus their differences, factual test outcome, historical/current repository comparison, deviations, unexpected changes, uncertainty, warnings, and external evidence references. Large test logs remain external. The verification ID is derived from the two exact upstream run IDs and the compared result/state; the external `run_id` follows the existing workspace content-addressed record convention.

Statuses are `verified`, `not_verified`, and `uncertain`. `verified` requires all chain comparisons to pass, exact test agreement, a passing Phase 70 outcome, no unexpected changes, current repository agreement, and no blocking unresolved evidence. `not_verified` records an observed mismatch or drift. `uncertain` represents unresolved required evidence without a definitive mismatch. Neither result causes lifecycle rejection, rollback, or follow-up.

The Phase 65 generic static-analysis notes `runtime_behavior_unverified` and `token_limit_exclusion_summary` are preserved as warnings because they describe limits outside the exact execution scope. An uncertain test plan remains blocking unless it escalated to a complete exhaustive catalog and Phase 70 executed every exact identity in that catalog; this deterministic case is recorded as a warning. Other unresolved Phase 65 evidence remains blocking.

## Historical and current repository state

The summary keeps the recorded Phase 69 HEAD and working-tree post-state separate from current HEAD, current source fingerprint, current changed paths, current semantic Git index digest, and current refs digest. Semantic index state uses the bounded shared Git helper and `GIT_OPTIONAL_LOCKS=0`; physical `.git/index` bytes are never compared. A repository that has moved since execution is reported as stale/drifted and cannot be verified. The historical execution record is not rewritten.

## Lifecycle evidence integration

The summary is written as a content-addressed external developer-workspace run record and includes hashes/references for the exact upstream evidence. Existing readiness/governance evidence workflows can reference that run artifact for human review. Phase 71 does not append governance decisions, transition readiness, close a lifecycle, assign roles, or treat verification as approval.

## CLI and failure behavior

```text
prototype local verify-execution REPOSITORY \
  --execution-run-id PHASE69_RUN_ID \
  --observation-run-id PHASE70_RUN_ID \
  [--workspace EXTERNAL_WORKSPACE] [--json]
```

The command verifies one exact chain and records the external summary. It does not run tests, execute arbitrary commands, change target files, stage, commit, push, deploy, repair, retry, roll back, close, or transition lifecycle state. JSON output is stable and sorted. Specific evidence mismatches are retained in `deviations`; stale state, missing evidence, failed tests, side effects, and uncertainty remain distinguishable.

## Validation and pilot

Focused coverage includes a complete positive chain; approved-scope and patch evidence mismatches; exact test-set differences; failed tests; unexpected test side effects; stale repository state; wrong repository; tampered run evidence; and blocking uncertainty. Positive assertions verify the target patch remains applied and HEAD, semantic staged state, commit state, and lifecycle state remain unchanged.

The bounded disposable pilot is recorded outside the checkout at `C:\Apps\phase71-validation\pilot-20261006`. It used a fresh Python Git repository, an external DeveloperWorkspace, deterministic local 384-dimensional fake vectors, and a retrieval stub only. The real Phase 65 planner/index freshness, Phase 67 diff validation, Phase 68 approval binding, Phase 69 application, Phase 70 unittest worker, and Phase 71 CLI were exercised. One real unittest passed; Phase 71 returned `verified`. A second run after repository drift returned `not_verified`. No model was downloaded.

## Limitations and deferred work

Verification establishes consistency of the recorded chain and current repository facts; it does not prove untested behavior or replace human code review. Generic static-analysis uncertainty remains visible in warnings. Phase 72 follow-up/recovery evaluation, any repair/retry/rollback decision, and every lifecycle closure remain deferred to a separate explicitly reviewed phase.
