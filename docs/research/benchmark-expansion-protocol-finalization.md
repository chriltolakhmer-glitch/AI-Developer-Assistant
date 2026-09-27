# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18.2 — Benchmark Expansion Protocol Finalization

**Date:** 2026-09-27  
**Status:** Finalization proposal for accountable review; **not approved**. G0 remains pending and Phase 19 is not authorized.  
**Scope:** Documentation and governance closure only. No repository processing, question authoring, retrieval changes, evaluation, freeze, or release. Humanize remains frozen.

## Purpose and relationship to prior phases

This document consolidates the open issues in the [Phase 18.1 gate review](benchmark-expansion-gate-review.md) and specifies a proposed, fail-closed protocol disposition. It is not a signed governance decision. Existing authority remains the [Phase 17 protocol](benchmark-expansion-protocol.md), whose status is **Proposed protocol; documentation only. Expansion execution remains BLOCKED**, and [Phase 17 checklist](benchmark-expansion-checklist.md), whose gates are unchecked. Phase 18 preparation materials are [candidate registry](benchmark-candidate-registry.md), [expansion plan](benchmark-expansion-plan.md), and [quality gates](benchmark-quality-gates.md).

Preparation is complete as documentation. Approval, clearance, and execution are not complete. Only the accountable benchmark owner and required clearance approvers can accept the proposal or record authorization; this document cannot do so on their behalf.

## Proposed scope resolution for G0 review

The existing frozen corpus has nine snapshots, including Humanize. Humanize has a frozen, exposed 12-question pilot; those cases cannot enter final slots, Humanize cannot be called unseen, and its repository-specific clearance remains unresolved. Therefore the original nine-repository/108-case allocation cannot be represented as nine unseen evaluation repositories while retaining this frozen candidate set and excluding pilot questions.

**Recommendation for explicit G0 decision:** revise the future independent-evaluation claim and target to a maximum of the eight non-Humanize snapshots already in the frozen corpus, with 12 newly authored cases per cleared and eligible repository (maximum 96), three per category per repository. Humanize remains the existing pilot/development reference only and contributes zero cases and zero unseen-repository evidence. The eight repositories are not presumed blind: prior source/system exposure must be recorded before any split. If any cannot validly serve in the declared evaluation partition, the usable target is smaller or the claim must be narrowed further. No repository may be silently substituted or added.

This is a proposal, **not an adopted count change**. The current schema/finalization tooling expects 108 cases across nine repositories and three repositories per size band. An eight-repository target would have two small, three medium, and three large candidates; it requires a versioned scope/schema/finalization decision and separately authorized, tested tooling support before future annotation or freeze. No tooling is modified here. Until G0 explicitly accepts this scope (or adopts another valid, documented plan), the historical 9/108 target remains unchanged as a planning record and execution stays blocked.

If the benchmark owner does not accept the 8/96 proposal, alternatives are: (a) limit the future claim to a properly declared mixed development/exposed and blind scope without calling all nine repositories unseen, or (b) request a separate future scope decision for another repository. This phase adds none and adopts neither alternative.

## Finalized controls proposed for approval

1. **Authority and sequencing:** each G0–G6 decision names protocol/scope/artifact versions and digests, accountable approver, date, outcome, conditions, and exact next activity. Missing evidence, unsigned decisions, or changed inputs keep affected gates closed.
2. **Candidate identity:** use only exact Phase 9 IDs and full SHAs in the [candidate registry](benchmark-candidate-registry.md). Registry inclusion, a frozen corpus identity, a root-license entry, or a preprocessing pass is not privacy or use clearance.
3. **Repository clearance:** G1 is per repository, snapshot, and activity. Resolve source-use, history/secret findings, personal/confidential data, license/file notices, provenance, storage/access/retention, transmission, and incident controls before the permitted processing activity. The [candidate clearance matrix](benchmark-candidate-clearance-matrix.md) is a status register, not clearance evidence.
4. **Independence:** before annotation/tuning, record repository-level exposure and exact split/access rules. Humanize stays in the exposed/development stratum, its pilot questions remain excluded, and no output exposed to tuning remains blind. See [independence plan](benchmark-independence-plan.md).
5. **Annotation:** only after G2 approval and in controlled staging; manual source-grounded authoring, no retrieval-informed gold, independent human review of every case, adjudication, retained initial judgments, and the Phase 17 agreement thresholds. The [operating procedure](benchmark-annotation-operating-procedure.md) is proposed and not permission to begin.
6. **Validation and freeze:** G3 requires complete allocation, zero unresolved evidence/provenance/structural issues, final acceptance, and verified preservation of Humanize/prior artifacts. G4 freezes a separate immutable version before evaluation. No partial batch is a final benchmark.
7. **Evaluation and release:** G5 is a separate sealed-run authorization. G6 is separate distribution/release permission. Passing freeze, validation, or evaluation never implies release.
8. **Rollback:** stop at the earliest failed gate on clearance incidents, provenance mismatch, unauthorized scope/access change, unresolved gold/review failure, leakage, incomplete eligibility, nondeterminism, or distribution-rights failure. Correct in a new version; never overwrite the Humanize pilot or released artifacts.

## Current gate disposition

| Gate | Finalization state |
|---|---|
| G0 — protocol/scope approval and bounded authorization | **Pending.** This proposal recommends 8/96 maximum with restricted claims; it is not accepted or authorized. |
| G1 — candidate-specific clearance | **Pending for all candidates.** See [clearance matrix](benchmark-candidate-clearance-matrix.md). |
| G2 — annotation readiness | **Pending;** no inventories/readiness packages or owner assignments evidenced. |
| G3 — review and validation | **Not started.** No expansion cases exist. |
| G4 — benchmark freeze | **Not started / not authorized.** |
| G5 — retrieval evaluation | **Not started / not authorized.** |
| G6 — release | **Not started / not authorized.** |

## Approval boundary and next decision

The [G0 authorization record](benchmark-expansion-g0-authorization.md) is a draft decision sheet with all approval and authorization fields unexecuted. This finalization does not mark G0 closed. The next valid governance action is an attributable G0 review of the protocol/scope proposal, with explicit acceptance, revision, or rejection. Even a future G0 decision can authorize only its named bounded activity; it does not grant G1 clearance, annotation, retrieval evaluation, freeze, release, or Phase 19 execution.

**Phase 18.2 disposition:** proposed controls and scope resolution documented; approvals remain pending; Phase 19 is not authorized. Humanize pilot remains frozen.

## Existing references

- [Phase 17 protocol](benchmark-expansion-protocol.md) and [Phase 17 checklist](benchmark-expansion-checklist.md)
- [Phase 18.1 gate review](benchmark-expansion-gate-review.md) and [readiness checklist](expansion-readiness-checklist.md)
- [Phase 18 candidate registry](benchmark-candidate-registry.md), [expansion plan](benchmark-expansion-plan.md), and [quality gates](benchmark-quality-gates.md)
- [Phase 9 frozen corpus selection](corpus-final-selection.md), [benchmark schema](benchmark-schema.md), and [benchmark finalization contract](benchmark-finalization.md)
- [Phase 8 repository risk acceptance](repository-approval-thesis-risk-acceptance.md) and [Phase 16 Humanize readiness decision](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md)
