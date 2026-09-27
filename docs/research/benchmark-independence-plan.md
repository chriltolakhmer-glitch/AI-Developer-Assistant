# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18.2 — Benchmark Independence and Split Plan

**Date:** 2026-09-27  
**Status:** Proposed plan for G0 review; **not approved and not an active split**.  
**Boundary:** No split manifest or benchmark cases are created here. No repositories are added. Humanize remains frozen and excluded from blind evaluation.

## Existing constraints

The [Phase 17 protocol](benchmark-expansion-protocol.md) requires repository-level development/blind separation, related-source grouping, predeclared access controls, and custodian-held blind labels. It states Humanize and any repository used for retrieval development are exposed/development data. The [Phase 9 corpus selection](corpus-final-selection.md) contains nine pinned snapshots, one of which is Humanize. Phase 18 records the pilot as frozen and ineligible for final slots ([candidate registry](benchmark-candidate-registry.md), [Phase 18.1 review](benchmark-expansion-gate-review.md)).

Accordingly, the currently available scope contains at most **eight non-Humanize repository snapshots** for a repository-held-out evaluation claim. This is an arithmetic ceiling, not evidence that all eight are clear, unexposed, or fit for a blind partition. The historical nine/108 plan cannot be called nine unseen repositories if Humanize is excluded from that claim.

## Recommended G0 scope proposal

Subject to explicit benchmark-owner approval and per-candidate G1 clearance:

- Use the existing Humanize pilot as an **exposed development/reference stratum only**, preserving all 12 questions, answers, chunk-map entries, hashes, and reports unchanged. Do not create additional Humanize questions under this proposal.
- Treat the eight other frozen snapshots as the maximum potential repository-held-out candidate set. The initial proposed final target is 12 new cases per eligible repository, three per existing category, up to **96 cases**. No placeholder cases or substitutions.
- Report the size composition honestly: at most two Small, three Medium, and three Large snapshots because the frozen small Humanize snapshot is excluded. Revise any size-balanced/generalization claim accordingly.
- Assign repositories to roles only after a documented exposure audit. A repository is eligible for blind evaluation only when the custodian can demonstrate that its queries/gold and evaluation results have not informed authoring, tuning, or system selection. Known source familiarity, related forks, tuning exposure, or leaked outputs can disqualify it or narrow the claim.
- If fewer than eight remain eligible, reduce the declared scope or seek a separately approved versioned scope decision. Do not add repositories, silently substitute, or call an exposed repository blind.

This proposal changes the historic nine/108 allocation. It therefore requires an accepted G0 versioned decision and separately approved/tested updates to target-dependent schema/freeze/validation tooling before any annotation or freeze. Current tooling's 108/9 invariants must not be bypassed. No such decision or tooling change is made here.

## Split and custody contract, if approved

| Data or asset | Proposed role/access | Rule |
|---|---|---|
| Existing Humanize pilot artifacts | Exposed/development reference; authorized readers only under existing controls | Frozen and unchanged. Never counted as blind evaluation cases or unseen repository evidence. |
| Eligible non-Humanize repositories, snapshots and inventories | Repository-level blind evaluation candidates under custodian control | Candidate assignment, prior exposure, related-source groups, and access are fixed before annotation/tuning. Clearance precedes authorized processing. |
| Development instructions/rubric and any development labels | Development | Version and digest before blind evaluation; no post-result rubric changes applied to the same blind set. |
| Blind questions and gold labels | Evaluation custodian only | Do not provide to system developers; custodian runs the locked configuration. Any exposure for tuning retires that blind status. |
| Run outputs/metrics | Custodian first; access logged | Do not reveal per-query outputs before the decision on system tuning/promotion is locked. Exposure invalidates affected holdout claim for subsequent tuning. |
| Related forks, snapshots, or close derivatives | Same partition / grouped unit | Prevent source overlap from creating a false independence claim. |

Before assignment, the controlled exposure register must record for each repository: canonical ID/SHA, source-reading history, prior question/annotation work, retrieval-development/tuning use, reported or viewed results, related repositories/forks, known staff access, planned partition, rationale, and reviewer/custodian. Use only approved aggregate references in committed documentation.

## Leakage and reclassification rules

- Assignment is repository-level, not random query-level, for any unseen-repository claim.
- Record the split rule, seed or deterministic assignment method, manifest digest, access list, and assignment date before annotation or tuning.
- If queries, labels, rankings, or holdout results are exposed to an author/developer who can tune the system, reclassify that material as exposed/development; do not restore blind status by renaming the partition.
- If all eight candidate repositories are exposed or fail clearance, no repository-held-out evaluation is available under this fixed scope. Stop and request a revised claim/scope decision; do not invent a blind set.
- Keep scoped-known-repository and pooled-distractor evaluation as separate predeclared tasks. Do not combine their metrics.
- The evaluation custodian reports all case failures and fixed denominators. Do not remove difficult cases, repositories, or evidence after results.

## Approval and readiness status

**Pending G0:** acceptance of the 8/96 maximum proposal or a separately versioned alternative, intended claim, taxonomy/count contract, exposure policy, named custodian, access policy, and tooling plan.  
**Pending G1:** candidate-specific clearance; no candidate is presumed eligible.  
**Pending G2:** verified inventories, approved split manifest, access controls, allocation, reviewers, and workload.  
**Not authorized:** creation of the controlled split manifest, annotations, retrieval runs, benchmark freeze, or release under this Phase 18.2 document.

## Existing references

- [Phase 17 protocol](benchmark-expansion-protocol.md), [Phase 17 checklist](benchmark-expansion-checklist.md), and [Phase 18.1 review](benchmark-expansion-gate-review.md)
- [Phase 18 candidate registry](benchmark-candidate-registry.md), [expansion plan](benchmark-expansion-plan.md), and [G0 decision record](benchmark-expansion-g0-authorization.md)
- [Phase 9 corpus selection](corpus-final-selection.md), [benchmark schema](benchmark-schema.md), and [benchmark finalization contract](benchmark-finalization.md)
- [Phase 16 Humanize readiness decision](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md) and [pilot closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md)
