# Phase 67 - Evidence-Grounded Patch Drafting

## Post-roadmap pilot-readiness integration

The `draft-patch` CLI validates the canonical Phase 65 plan run and its linked Phase 64 change-impact run before it accepts the embedded Phase 66 proposal. It checks workspace/repository/state binding, content-derived run IDs, recomputed proposal identity, targets, symbols, evidence references, unresolved uncertainty, and expected-test selection. Missing, modified, cross-workspace, or stale evidence fails before a candidate is retained. The accepted draft records its exact source plan run ID for later test execution and verification.

`target_paths` in the proposal and draft are the allowed maximum scope. `candidate_paths` is calculated from the supplied diff and may be a strict subset. Any path outside the allowed scope remains invalid. The full proposal evidence and uncertainty are retained.

## Purpose

Phase 67 adds an externally recorded, reviewable unified-diff artifact linked to a Phase 66 `ProposedAction`. A candidate is accepted only for the proposal's exact repository and working-tree state.

## Architecture boundary

`ProposedAction -> PatchDraft -> human review`. This phase has no application, authorization, execution, or lifecycle transition path.

## PatchDraft contract

`src.developer.patch_drafting.PatchDraft` is a frozen, slotted dataclass with stable JSON serialization. It records the deterministic patch ID, source action, repository and working-tree identities, goal, target paths and symbols, unified diff, evidence and unresolved evidence, validation requirements, and review-only state.

## Proposal binding

Drafting requires a `proposal-` action ID and preserves proposal repository, revision, goal, target, evidence, and uncertainty fields. Missing or malformed proposal identity fails closed.

## Repository-state binding

The repository root, derived repository ID, current commit, base reference resolution, and working-tree fingerprint must match the proposal. Drift requires new planning; Phase 67 never refreshes a proposal. Authorized Python target context is limited to 256 KiB per file; larger context is reported as a blocking error rather than silently truncated.

## Patch format

Only paired unified-diff file headers and counted hunks are accepted. Adds, deletes, renames, absolute paths, traversal, duplicate files, malformed hunks, and paths outside the proposal target list are rejected. Validation parses text only and never applies it.

## Generator boundary

`PatchDraftGenerator` is a pure candidate-text interface. `SuppliedPatchGenerator` supports deterministic test or externally authored candidate input. AIDA has a local retrieval embedding model but no patch-authoring model; production-quality patch generation is not provided. No network LLM is used.

## Deterministic validation

The validator checks proposal identity, repository state, path containment, `.py` target support, unified-diff structure, and exact target scope. It does not execute commands, tests, or patch application.

## Evidence provenance

The draft copies Phase 66 evidence references unchanged, retaining their evidence categories such as `changed_code`, `static_relationship`, `retrieval_evidence`, `additional_related_context`, and `test_selection`. Static and retrieval evidence remain non-runtime evidence.

## Unresolved evidence

Proposal uncertainty is copied intact. Missing evidence references, stale-index requirements, ambiguous or unsupported targets, parser failures, and omitted required context produce `blocked` with no retained patch body. Informational unresolved items such as the standard `runtime_behavior_unverified` reminder remain visible without blocking an otherwise evidenced draft. Additional candidate scope is rejected.

## CLI contract

`prototype local draft-patch REPOSITORY --proposal-run-id RUN --patch-file CANDIDATE.diff [--workspace PATH] [--json]` loads the proposal from the existing developer run record and reads a supplied candidate outside the target repository. Human output explicitly says PATCH DRAFT, NOT APPLIED, and HUMAN REVIEW REQUIRED.

## Workspace storage

The stable payload uses `developer-local-patch-draft` and the existing `DeveloperWorkspace/runs` record structure. Candidate files and generated records are not placed in the target checkout.

## Failure behavior

Stale state, unsupported targets, bad identity, malformed diff, and unauthorized paths fail closed. Insufficient or unresolved evidence produces a blocked artifact. A new Phase 66 plan is required after repository drift.

## Safety boundary

Phase 67 does NOT modify target source, apply patches, execute target tests, authorize actions, commit target code, use arbitrary shell execution, automatically repair failures, or transition lifecycle state. Applying the diff is deferred to Phase 69; authorization is deferred to Phase 68.

## Validation record

Phase 67 focused suite: 9 tests passed, 0 skipped, 0 failures, 0 errors (5.18 seconds). Phase 66 and CLI regressions: 21 passed, 0 skipped, 0 failures, 0 errors (14.35 seconds). Developer-mode component suite: 216 passed, 0 skipped, 0 failures, 0 errors (3,195.92 seconds). Changed-file planner: T2, 282 selected, 131 intentionally unselected, uncertainty false, executed false, T4 final gate required. Final synchronous full discovery from C:/Apps/.venv: exit code 0; 414 tests in 3,283.265 seconds; OK (skipped=2). The skips were test_real_model_offline_repeatability (requires EMBEDDING_MODEL_CACHE for real offline inference) and test_real_embedding_to_persisted_indexes_to_text_query_offline (requires EMBEDDING_MODEL_CACHE for offline integration).

## Pilot record

Bounded temporary Python Git repository under `C:/Apps/phase67-validation/pilot-repository2`; external records and candidate under `C:/Apps/phase67-validation/developer-workspace2` and the pilot root. Phase 65 plan `run_id` linked to proposal `proposal-8d8a130aed89`; Phase 67 draft `patch-32213679c00dc951` has status `draft` and contains a reviewable unified diff. A fake local embedder populated the fixture index and a supplied candidate adapter provided patch text; no production patch model was used. Source bytes, HEAD, Git status, and Git index matched before and after; patch not applied. Runtime behavior uncertainty remained visible.

## Limitations

No production patch-generation model is configured. Candidate text must be supplied. The current source-context boundary supports Python targets only. Unified diff validation is structural and is not equivalent to testing whether a patch applies.

## Deferred work

Human authorization (Phase 68), controlled patch application (Phase 69), target test execution, observations, rollback, repair loops, deployment, and lifecycle closure remain deferred.

## Candidate symbol scope

Phase 67 independently applies the unified diff to the exact source pre-image, then attributes changed old lines against the parsed pre-image and changed new lines against the parsed post-image. It records allowed and candidate scope separately as sorted path-qualified pairs. The smallest enclosing parsed class/function/method is used; module statements map to `<module>`. An exact symbol match is allowed, and a class may authorize a member only when the parser proves that membership. A strict candidate subset is valid. An unlisted sibling or module edit, invalid Python image, malformed hunk, or unresolved attribution blocks drafting before approval. File-level permission never implies permission for every symbol in that file.

The immutable PatchDraft distinguishes `target_paths` (allowed file scope) from `candidate_paths` (actual diff paths), just as it distinguishes allowed symbol scope from candidate symbol scope. Candidate paths must be the exact canonical paths parsed from the diff and a subset of allowed paths.
