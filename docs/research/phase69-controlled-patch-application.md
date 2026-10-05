# Phase 69 — Controlled Patch Application

## Purpose

Phase 69 applies one exact Phase 67 unified diff only when the matching Phase 68 authorization approves it.

## First mutation boundary

`apply-patch` is the first AIDA command that may modify target source. It accepts a repository and an external authorization run ID. It does not accept patch text or arbitrary commands.

## Execution contract

`PatchApplicationResult` records authorization, proposal, patch, repository revisions and fingerprints, target paths, patch hash, status, changed paths, actual Git diff, error, and time. Results use `developer-local-patch-application` in the external DeveloperWorkspace.

## Authorization validation

The executor reads the canonical Phase 68 run and validates the frozen typed record. It independently integrity checks the linked Phase 67 run and PatchDraft. Decision, operation, patch ID/hash, proposal ID, repository identity/path, commit, working-tree fingerprint, and exact target paths must match. The immutable Phase 68 record is not rewritten.

## Repository-state validation

The checkout is rescanned immediately before mutation. The bound commit and working-tree fingerprint must match, and Git status must be clean. The executor captures HEAD, index bytes, refs, status, and target pre-image bytes. It rechecks these bindings immediately before the first write.

## Application mechanism

The executor uses a narrow internal unified-diff interpreter. It does not expose Git arguments, shell commands, or general file editing. Hunk coordinates and every old/context line must match at the exact position. There is no fuzzy matching. Only existing regular files inside the repository may be replaced; adds, deletes, renames, traversal, absolute paths, and escaping symlinks fail closed.

## Preflight

The approved patch hash is recomputed. For every target, the executor captures original bytes and computes the expected post-image in memory before writing anything. UTF-8 is required. Invalid coordinates, malformed hunks, stale context, unsupported paths, or any target that would not change bytes stop before mutation.

## Expected post-state computation

The interpreter uses the approved hunk line numbers and exact old lines to construct each expected post-image. It preserves untouched source bytes and line endings and never formats or normalizes whole files.

## Mutation

Each resulting file is staged in its target directory and atomically renamed into place. The operation modifies only the approved paths.

## Post-application verification

After writes, the executor rereads every target and compares bytes with the computed post-image. It checks the Git changed-path set against the authorized paths, and confirms HEAD, index bytes, and refs are unchanged. The actual Git diff is recorded for human review; exact post-image bytes are the verification authority.

## Unexpected-change detection

Any target byte mismatch, changed-path mismatch, HEAD/index/ref change, or write error makes execution fail. Only after all checks pass is an `applied` result recorded.

## Atomicity

All target pre-images and expected post-images are held before mutation. Each target replacement is atomic within its directory. If any later step fails, every approved target is restored from the captured pre-image.

## Failure restoration

Restoration is verified by rereading all target bytes and comparing them to pre-images, then checking Git status, HEAD, index, and refs against the captured state. A failure observation is written externally when possible. If restoration cannot be proven, the command reports `restoration verification FAILED`. Preflight failures need no restoration because no target was changed.

## Scope/path safety

Paths must exactly match the validated PatchDraft and authorization. The executor rejects path traversal, absolute paths, symlink escapes, missing targets, and paths outside the repository. It accepts no caller-provided patch body at execution time.

## Replay prevention

An authorization is consumed only by a canonical, identity-checked external execution record with status `applied`. Failed or restored attempts do not consume it. Altered execution records fail closed. These local records are integrity checked but are not signed or tamper-proof.

## CLI

`prototype local apply-patch REPOSITORY --authorization-run-id RUN [--workspace PATH] [--json]`

## Execution records

Execution observations use the existing external DeveloperWorkspace run-record format. No AIDA metadata or backups are written into the target repository.

## Safety boundary

Phase 69 applies source changes but does not run target tests or commit them. It does not stage, push, deploy, invoke an LLM, repair a patch, retry, or transition lifecycle state.

## Pilot evidence

Success pilot: a disposable Python Git repository completed Phase 65 planning, Phase 67 drafting, Phase 68 approval, and Phase 69 application. A local fake embedder populated only the external pilot index, and retrieval was stubbed because the pinned model was unavailable offline. The plan selected `app.py`; the approved patch applied; resulting bytes and changed paths matched; HEAD and index stayed unchanged; no target tests or commit ran; and the execution record was external.

Stale-state and conflict pilots: separate disposable repositories completed planning, drafting, and approval. Each target was changed after approval. Both attempts failed before mutation, preserving the pre-attempt file bytes and Git status.

Replay pilot: a second attempt using the successful authorization was rejected with source bytes and status unchanged. Multi-file partial-write and post-write mismatch recovery are covered by focused fault-injection tests; captured bytes and Git state were verified restored.

## Testing evidence

Focused Phase 69 tests: 9 passed. Direct Phase 68 authorization regressions: 8 passed. The final phase-gate dry run selected exhaustive T4 (438 tests, uncertainty true) because `src/cli.py` is high risk and the test module uses dynamic fault injection. One phase completion gate then ran 438 tests in 3,660.504 seconds: 436 passed, the two existing real-model tests skipped because `EMBEDDING_MODEL_CACHE` is unavailable, 0 failures, 0 errors, exit code 0, terminal `OK (skipped=2)`. The gate report is external at `C:/Apps/phase69-validation/phase-gate-completion.json`.

## Limitations

The executor supports the existing Phase 67 Python target boundary. Git diff text is retained for review but is not the equality authority; exact resulting source bytes are compared instead. Pilot retrieval was stubbed because the pinned model was unavailable offline. Authorization and execution records are not cryptographic signatures.

## Deferred work

Authorized target test execution and observations, user-facing rollback, automatic commit, deployment, and lifecycle verification/closure belong to later phases.
