# Phase 72 — Controlled Follow-Up / Recovery Evaluation

## Purpose and input

Phase 72 evaluates one exact Phase 71 `verify-execution` run after the Phase 65–70 planning, authorization, application, and test chain. It records bounded options for a developer to review. It does not decide or perform recovery. Phase 72 is the final currently committed implementation phase.

The required input is a 20-character Phase 71 run ID in an external `DeveloperWorkspace`. No “latest” lookup exists. The evaluator validates canonical metadata and payload bytes, the workspace and repository binding, the content-derived run ID, and Phase 71's deterministic `verification_id`. It follows and hashes the exact referenced Phase 65 plan, Phase 67 draft, Phase 68 authorization, Phase 69 application, and Phase 70 observation. Missing, duplicate, ambiguous, cross-repository, malformed, or altered links stop evaluation. Phase 71 findings and Phase 70 facts must agree. These local hashes detect ordinary alteration; they are not signatures against an attacker able to rewrite every linked record.

## RecoveryEvaluation contract

`RecoveryEvaluation` is a frozen, slotted dataclass serialized into an external `developer-local-recovery-evaluation` run. It records the repository ID/path, exact Phase 71 verification ID/run ID, Phase 69 execution ID/run ID, Phase 70 observation ID/run ID, verification status, classification, candidate actions, blocking conditions, reasons, unresolved uncertainty, rollback feasibility and candidate identity, retry eligibility/boundary, new-proposal requirement, and exact evidence references. It always says human review is required and execution is not authorized. Mutation, retry, rollback, and lifecycle transition flags are false. Large test output stays in Phase 70 external log files.

`evaluation_id` is deterministic for the exact verified input, repository state, classification, blockers, options, rollback identity, retry boundary, reasons, and uncertainty. The workspace `run_id` separately identifies the canonical full payload and workspace/repository snapshot under the existing content-addressed run-record convention. A repeated evaluation of identical facts has the same IDs; changed repository facts produce a different evaluation.

## Classification and human options

| Situation | Classification | Options recorded for human review |
| --- | --- | --- |
| Phase 71 verified and current state unchanged | `no_recovery_required` | Human lifecycle review; no recovery mutation proposed. |
| Failed/errored Phase 70 tests with otherwise trusted current chain | `failed_tests` | New proposal and manual inspection; a rollback candidate only if exact reverse checks pass. |
| Unexpected test repository side effect | `unexpected_side_effect` | Manual investigation; preserve the artifact and its path evidence. |
| Repository moved since Phase 69 | `stale_repository` | New planning against current evidence and manual investigation; historical rollback/retry blocked. |
| Other verification/evidence mismatch | `verification_mismatch` | Manual investigation; no mutation candidate. |
| Phase 71 uncertainty without definitive mismatch | `uncertain_verification` | Collect required evidence and review; no mutation candidate. |

Classification uses typed statuses, deviation identifiers, repository facts, and recorded side-effect paths. It does not interpret failure prose as a repair instruction. Blocking conditions retain exact state/deviation identifiers. A stale checkout invalidates a historical recovery candidate even when the historical Phase 71 result was verified.

## New proposal path

If source changes appear necessary, `new_proposal_required` means start a new developer goal using the existing Phase 65 plan → Phase 66 ProposedAction → Phase 67 PatchDraft → Phase 68 exact human approval → Phase 69 controlled application path. Phase 72 neither calls those stages nor drafts a repair. A changed patch is a new proposal, never a retry of the old authorization. Static evidence and test failures do not prove a proposed repair correct.

## Rollback feasibility

Rollback is evaluated only for a failed/errored test chain with no unrelated verification mismatch, unresolved required uncertainty, or unexpected side effect. Phase 72 revalidates the trusted Phase 69 application, Phase 67 draft, and Phase 68 authorization. Current HEAD, semantic Git index entries, refs, working-tree fingerprint, changed-path set, and target Git diff must match Phase 69's recorded poststate. The exact authorized target set must be the only changed set. No unrelated developer changes may be overwritten.

For each safe regular target, Phase 72 obtains the HEAD blob as the clean pre-application source. Because Windows checkout line endings may differ from Git blob bytes, it considers the blob's exact bytes and a CRLF checkout form. It accepts a preimage only when exactly one candidate, fed through the existing Phase 69 non-fuzzy patch interpreter, reproduces the current target bytes. Ambiguity or mismatch makes rollback unavailable. A candidate binds the Phase 69 run and execution IDs, repository ID/path, exact HEAD/poststate/index/refs, target paths, current postimage hashes, reverse-content hashes, and reverse-diff hash. The candidate contains no authority to run a reverse operation. Phase 72 never executes one, never uses fuzzy patching, and never calls Git reset, checkout, clean, staging, commit, or push on the target.

## Retry boundary

Phase 70 has no typed transient-cause proof. Phase 72 therefore records `retry_eligible: false` and never runs a test again. Its retry boundary names the prior exact observation run, execution run, test plan, test identities, repository state, HEAD, semantic index, and refs. It distinguishes the same operation from a changed test plan or patch, caps any separately considered future same-operation attempt at one, and requires new explicit human authorization. A changed test selection cannot inherit the old Phase 70 invocation. There is no automatic repeat or loop.

## CLI and lifecycle boundary

```text
prototype local evaluate-recovery REPOSITORY \
  --verification-run-id PHASE71_RUN_ID \
  --workspace EXTERNAL_WORKSPACE [--json]
```

Human output shows verification status, classification, candidate actions, blocking conditions, rollback feasibility, retry eligibility, human approval requirement, and the external record ID. JSON is sorted and includes the typed payload. An evaluation can be referenced by existing readiness/governance review evidence; it does not append a governance decision, approve a rollback, transition readiness, close lifecycle, deploy, or mutate the source. Even `no_recovery_required` leaves the lifecycle decision with the developer.

## Validation and bounded pilot

Focused tests cover verified/no-recovery, failed tests, exact safe rollback without execution, stale/unsafe rollback, unexpected test side effects with artifact preservation, uncertainty, tampered/missing/wrong-repository/wrong-chain/ambiguous evidence, and no source/Git mutation. The directly affected Phase 71 verification tests remain separate upstream regressions.

The disposable pilot at `C:\Apps\phase72-validation\pilot-20261006-3` completed a real Phase 65 plan, Phase 66 proposal, Phase 67 supplied candidate, Phase 68 approval, Phase 69 application, Phase 70 authorized unittest, Phase 71 verification, and Phase 72 CLI evaluation. A deterministic local fake embedder populated the external index; only retrieval was stubbed. One target unittest passed, Phase 71 was `verified`, and Phase 72 returned `no_recovery_required`. After an unrelated file was added, evaluating the same historical Phase 71 run returned `stale_repository` with no rollback or retry. Phase 72 preserved target bytes, HEAD, semantic index, Git status, and the unrelated file. No model download occurred. This is an internal architecture validation pilot, not the post-roadmap realistic fresh setup.

## Limits and next step

The evaluator checks a bounded local Git and evidence state. It does not prove untested behavior, infer transient failures, produce a correct repair, authenticate the developer, or provide a rollback executor. Any future mutation or retry requires a separate explicit human decision and the existing controlled path. Phase 72 creates no autonomous repair agent or recovery loop.

After Phase 72 implementation and validation, roadmap work stops. The next activity is an end-to-end architecture review followed by a realistic fresh setup/new-feature pilot on a separate project. No Phase 73 is created or started.
