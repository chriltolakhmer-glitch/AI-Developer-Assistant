# Post-roadmap product development plan — UI first

Recorded: 2026-10-08. Status: planning/documentation only; no UI or productivity enhancement is implemented by this plan.

## Baseline and classification

The AIDA roadmap through Phase 72 is complete. Current published implementation authority is `d81d2faec77ff755516c197d7295eac955457b69`; `VERSION` remains `0.1.1`. Architecture authority remains the existing post-Phase-65 architecture authority. This plan does not replace it or rewrite historical architecture decisions.

The project owner reports successful real external GitHub project validation through repository evidence gathering, Phase 65 planning, Phase 67 patch drafting, Phase 68 human authorization, Phase 69 controlled patch application, Phase 70 authorized regression execution, Phase 71 execution verification, Phase 72 recovery evaluation, and direct feature-specific validation. That validation also produced and validated the oversized-container exact retained-leaf correction. This records the supplied post-validation outcome; it is not a new validation run or a benchmark claim.

The safety architecture is sufficiently validated for the next product-development stage. This is a **Post-roadmap product development plan**, with two tracks:

- **Track A — Developer Experience:** UI first.
- **Track B — Developer Productivity:** feature-specific test planning → implementation/test drafting → supervised orchestration.

These are product enhancements to the completed workflow, not Phase 73+, a roadmap extension, a replacement architecture, or a weakening of approval. The historical Phase 65–72 roadmap remains unchanged. Research evaluation, Humanize, frozen release artifacts, and the immutable `v0.1.1` release remain separate and unchanged.

## Strategic direction: UI First

Build AIDA UI v1 before implementing the next developer-productivity enhancements. Make the existing workflow understandable and usable through one coherent developer-facing surface instead of manual command coordination.

AIDA is already strong in evidence-grounded repository understanding, exact path/symbol scope control, human authorization, controlled mutation, deterministic regression binding, execution verification, fail-closed behavior, and auditability. Current usage is command-heavy and exposes internal phase coordination. The external project exercise required manual scan/index, planning, candidate generation, Phase 67 invocation, Phase 68 approval, Phase 69 application, Phase 70 execution, Phase 71 verification, Phase 72 evaluation, and direct feature validation.

The UI is a presentation and control layer over the existing trusted workflow. Existing safety contracts, evidence records, human approval, exact scope controls, execution verification, and fail-closed semantics remain authoritative.

The long-term vision is:

Developer states goal → AIDA researches repository → presents plan and evidence → drafts implementation/test proposals → developer reviews and approves → AIDA safely executes → verifies → developer receives final verified result.

UI v1 exposes only capabilities that already exist. Automatic implementation/test drafting must not appear as available until implemented and validated. Initially, candidate patches are externally supplied or obtained through a currently supported mechanism.

## UI v1 scope

### 1. Project / repository screen

Show repository path, Git branch, HEAD, clean/dirty state, AIDA workspace, index freshness, AIDA version/authority, supported languages, and scan/index state. Supported-language display must reflect the actual backend boundary (currently local Python `.py` support), not anticipated language support.

Actions: select/open repository, scan, and explicitly index/reindex when required. Do not allow silent repository mutation or silent reindexing. Keep generated indexes and evidence in the existing separate developer workspace.

### 2. Goal screen

Provide a prominent goal input, for example: “Update Calculator.divide so Decimal operands are supported while preserving existing behavior.” Submit the goal and run the existing Phase 65 evidence/planning workflow.

### 3. Evidence / plan screen

Present Phase 65 primary implementation targets, related/test targets, target paths/symbols, existing bound tests, evidence confidence, warnings, blocking evidence, non-blocking evidence, recommended validation, and proposal identity. Preserve the existing typed proposal binding where required by downstream contracts.

Clearly distinguish **BLOCKING** from **INFORMATIONAL / NON-BLOCKING**. Never hide blocking evidence. If Phase 65 is blocked, execution controls remain unavailable.

### 4. Proposed change screen

Support externally supplied or currently supported candidate patches. Show exact candidate diff, candidate files/symbols, allowed files/symbols, patch ID, patch SHA, warnings, and evidence references. Highlight every scope mismatch. Approval is unavailable unless Phase 67 accepts the candidate.

### 5. Human review / approval screen

Show developer goal, exact patch, changed files/symbols, expected tests, repository binding, patch hash, and unresolved warnings. Provide explicit **APPROVE** and **REJECT** actions using the existing Phase 68 authorization mechanism. Viewing or reviewing a patch never grants implicit approval. Authorization remains bound to the exact reviewed patch and repository state.

### 6. Execution screen

After approval, present a clear progress timeline: **Phase 69 — Apply → Phase 70 — Test → Phase 71 — Verify → Phase 72 — Evaluate**. Each stage shows current status, run ID, evidence/result, relevant exact hashes, and errors/blockers. Do not hide failure or uncertainty. Approval enables only the operations allowed by existing downstream contracts, including authorized regression execution.

### 7. Verification result screen

Summarize approved patch, actual mutation, changed files/symbols, tests executed, pass/fail totals, exact post-image integrity, deviations, unresolved uncertainty, verification status, and recovery classification.

Visually distinguish **VERIFIED**, **BLOCKED**, **FAILED**, **UNCERTAIN**, and **NO RECOVERY REQUIRED**. Keep execution-verification status and recovery classification separate: no recovery required alone does not prove successful verification. Preserve backend statuses and diagnostics in expandable detail. Show final verified success only when the evidence supports it.

### 8. Evidence / history screen

Expose scan IDs, index IDs, Phase 65 run/proposal, Phase 67 run/patch, Phase 68 authorization, Phase 69 execution, Phase 70 observation, Phase 71 verification, and Phase 72 recovery evaluation, including important SHA/hash bindings and any existing intermediate proposal identity. Make the audit trail understandable without requiring manual JSON inspection.

## UI design and safety boundaries

- **Safety architecture remains authoritative:** call existing AIDA contracts; do not duplicate security/scope logic in the frontend. Frontend state never becomes execution authority. Backend evidence remains authoritative.
- **Human control:** mutation is impossible before explicit Phase 68 approval. Approval does not bypass Phase 69–72 prerequisites or authorize arbitrary execution.
- **Fail closed:** state, evidence, hash, branch, repository identity, or phase-contract mismatch stops the workflow and displays the reason. Never silently repair, retry, or bypass a blocker.
- **Developer simplicity:** the default view explains what will change, why, what will be tested, what blocks progress, what requires approval, and what actually happened.
- **Progressive detail:** show a simple developer summary by default with expandable full evidence, run IDs, hashes, and diagnostics. Simplification must not suppress uncertainty or blockers.
- **Local-first:** preserve the current developer-local architecture unless existing architecture explicitly says otherwise. Do not introduce cloud infrastructure for UI convenience.
- **Recovery remains controlled:** Phase 72 displays its evaluation and existing permitted follow-up proposals; a UI recovery control must not invent automatic rollback or new authority.

## Intended first workflow

1. Open repository.
2. Verify repository state.
3. Scan/index if required through explicit supported actions.
4. Enter developer goal.
5. Run Phase 65 planning.
6. Review evidence and plan.
7. Supply/import a candidate patch; AIDA UI v1 does not generate implementation patches.
8. Run Phase 67 with the existing required proposal contracts.
9. Review exact patch.
10. Explicitly approve or reject through Phase 68.
11. Apply through Phase 69 after all contract checks pass.
12. Run authorized tests through Phase 70.
13. Verify execution through Phase 71.
14. Evaluate recovery through Phase 72.
15. Show the final verified result, or the actual blocked, failed, or uncertain outcome.

Internally, the existing phases and their contracts remain intact. The UI presents one coherent workflow. Direct feature validation remains distinct from regression evidence; UI v1 must not claim that existing regressions prove newly requested behavior without supporting evidence.

## Post-UI productivity enhancement sequence

### Enhancement 1 — Feature-specific test planning

Compare developer-requested behavior against existing test evidence. Identify what existing tests prove, what requested behavior is unproven, and which new feature-specific tests are needed. Automatically propose the missing tests once this enhancement exists.

In the real Decimal experiment, existing tests proved ordinary division, existing zero division, and `last_answer`. Missing feature proof covered Decimal operands, Decimal result value, Decimal result type, Decimal `last_answer`, and Decimal-specific zero behavior. Existing regression success must not be presented as proof of these missing behaviors.

### Enhancement 2 — Evidence-grounded implementation and test drafting

Draft both an implementation patch and feature-specific tests from Phase 65 evidence. Drafts remain non-mutating; Phase 67 still validates exact scope and human Phase 68 approval remains mandatory. AI reasoning proposes; deterministic AIDA contracts authorize. This is future capability, not an assertion that automatic drafting already exists.

### Enhancement 3 — Supervised workflow orchestration

Reduce manual phase coordination: developer enters goal → AIDA performs required research/planning → drafts implementation and tests → presents one review surface → developer approves → AIDA performs controlled Phase 69–72 lifecycle → returns a verified result.

Retain internal phases for safety and auditability. Never collapse or bypass their contracts. UI v1 coordinates existing supported actions; this later enhancement adds supervision of the expanded planning/drafting workflow.

## Long-term developer experience

**Current:** developer goal → manually coordinate evidence/planning → external agent creates candidate → manually run Phase 67 → manually approve → manually run execution/verification phases → manually add feature-specific tests.

**Target:** developer goal → AIDA researches → identifies existing and missing test evidence → drafts code and tests → developer reviews once → AIDA safely applies/tests/verifies → developer receives a concise verified result.

“Reviews once” describes the intended coherent review surface; changed patch or repository bindings still require fresh authorization under existing contracts.

## Priority order and completion expectations

1. Build AIDA UI v1 over existing Phase 65–72 capabilities.
2. Validate UI with the existing developer workflow.
3. Implement feature-specific test planning.
4. Implement evidence-grounded implementation/test drafting.
5. Implement supervised workflow orchestration.
6. Validate the combined experience on new real development tasks.

Do not start item 3 before UI v1 is complete unless a UI implementation dependency requires a small supporting backend change. Such a dependency must preserve the existing safety contracts and does not authorize the broader enhancement early.

UI v1 completion requires a usable existing workflow with explicit approval, visible blockers/failures/uncertainty, authoritative evidence bindings, and inspectable history. Validate it through the existing developer workflow before proceeding to productivity enhancements. This planning update performs no implementation, execution, tests, scan/index, or new phase creation.

Implementation design: [AIDA UI v1 architecture](ui-v1-architecture.md).
