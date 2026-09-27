# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18.2 — G0 Protocol and Scope Decision Record

> **Superseded as the active workflow by Phase 18.4.** This draft remains historical evidence that G0 was pending and no activity was authorized when written. Its proposed 8/96 scope and G0 approval fields were never adopted or signed. Use [the simplified workflow](benchmark-research-workflow-final.md) and [readiness checklist](benchmark-expansion-readiness-checklist.md) for current preparation status. This supersession does not authorize expansion; repository-specific approvals remain required and Humanize remains frozen.

**Record date:** 2026-09-27  
**Record type:** Draft decision request / fillable authorization record.  
**Current outcome:** **PENDING — NOT APPROVED — NO ACTIVITY AUTHORIZED.**  
**Phase 19 status:** **NOT AUTHORIZED.** Humanize remains frozen.

This record is prepared from the [Phase 17 protocol](benchmark-expansion-protocol.md), [Phase 17 checklist](benchmark-expansion-checklist.md), [Phase 18.1 gate review](benchmark-expansion-gate-review.md), and [Phase 18.2 protocol finalization proposal](benchmark-expansion-protocol-finalization.md). It is not a signature, governance approval, repository clearance, or permission to execute. All approval fields below are intentionally unassigned.

## Decision requested

The benchmark owner and required independent reviewers are asked to make an attributable G0 decision on the protocol and bounded scope. The recommendation for review is:

- Preserve the exact nine-candidate scope in the [candidate registry](benchmark-candidate-registry.md); add or substitute no repository.
- Keep `python-humanize/humanize` as the frozen, exposed pilot/development reference only; count zero pilot cases toward any final set and do not claim Humanize as unseen.
- Consider a versioned maximum target of **eight eligible non-Humanize repositories × 12 new cases = 96 cases**, three per category per repository, with claims restricted to the approved repository-held-out evaluation. This is only a proposal; exposure/clearance can reduce the usable set, and the existing 9/108 tooling contract must not be bypassed. Any adoption requires separately approved, tested schema/finalization tooling changes before annotation or freeze.
- If that target/claim is not accepted, choose a documented alternative or return the protocol for revision; do not silently retain 9/108 while presenting nine repositories as unseen.

## Proposed bounded authorization, if later approved

**No authorization is effective at present.** If the authorized benchmark owner accepts and signs this G0 record, the only proposed immediate activity is to prepare candidate-specific G1 clearance decision packages for the already-listed non-Humanize snapshots under the approved handling process. This would not authorize source-derived annotation, creation/use of inventories for gold work, indexing, embeddings, retrieval runs, code changes, benchmark freeze, or release. G1 activity must follow its own authorized handling boundary and decision record.

Do not treat the preceding conditional description as permission to begin. Until every required approval is signed and the effective outcome below is recorded, the permitted activity remains documentation-only.

## G0 review checklist

| Decision element | Proposed state | Approval/evidence state |
|---|---|---|
| Protocol version and gate sequence | Phase 17 controls, finalized only upon explicit decision | **Pending** |
| Candidate membership and pinned identities | Existing nine Phase 9 candidates; no additions/substitutions | **Pending approval of exact scope** |
| Allocation and claim | Recommend maximum 8 non-Humanize repositories / 96 cases; target change requires versioned approval and tooling plan | **Pending decision** |
| Humanize treatment | Frozen pilot only; excluded from new-case slots and blind/unseen claims | **Preservation boundary recorded; no new approval** |
| Development/blind split | Repository-level split and exposure audit before authoring/tuning; no candidate presumed blind | **Pending** |
| Taxonomy/schema and ID policy | Existing four categories and schema 1.0 only unless separately versioned; resolve collisions/count contract before authoring | **Pending** |
| Quality thresholds | Phase 17 quality thresholds; independent human review 100%, ≥80% exact graded-evidence agreement overall and per repository, zero unresolved validation issues | **Pending acceptance** |
| Roles and capacity | Benchmark owner, clearance reviewers, annotation/review/adjudication, custodian, validation and experiment owners, data steward, incident owner | **Unassigned** |
| Storage/handling | Controlled location, access, retention/deletion, backup, transmission, distribution and incident process | **Pending evidence/approval** |
| Validator/report policy | Preserve invariants; separately authorize/test any tooling policy change; no overstatement of supplemental validation | **Pending** |
| Exact activity authorized | None until record signed and outcome set | **None** |

## Required decision fields — intentionally blank

| Field | Entry |
|---|---|
| Benchmark owner / accountable approver | **Unassigned** |
| Independent reviewer(s) | **Unassigned** |
| Data/privacy steward | **Unassigned** |
| License reviewer | **Unassigned** |
| Protocol and scope version | **Proposed; version/digest to be recorded at decision** |
| Evidence bundle location and digest | **Pending** |
| Outcome (`APPROVE`, `REVISE`, `REJECT`) | **PENDING — NOT APPROVED** |
| Conditions / unresolved items | **Pending review; see checklist above** |
| Exact next activity authorized | **None** |
| Decision date | **Pending** |
| Signatures / attributable approval references | **None recorded** |

## Fail-closed effect

- Until a completed, attributable G0 record exists, all gates remain closed and no candidate clearance work is authorized by this document.
- An `APPROVE` outcome must enumerate one bounded next activity and its limits. It cannot authorize all of Phase 19 or imply G1–G6 passage.
- `REVISE` or `REJECT`, absent signatures, missing digests, unresolved scope/independence questions, or changed inputs leave the status **NOT AUTHORIZED**.
- No G0 outcome can clear repository-specific privacy/license findings. G1 decisions are separate and candidate-specific.
- Phase 19 execution—including source/inventory processing for annotation, question authoring, retrieval evaluation, freezing, or release—requires later explicit gate decisions and a separate instruction. It is not authorized here.

## References

- [Phase 17 protocol](benchmark-expansion-protocol.md) and [checklist](benchmark-expansion-checklist.md)
- [Phase 18.1 review](benchmark-expansion-gate-review.md) and [readiness checklist](expansion-readiness-checklist.md)
- [Phase 18.2 finalization proposal](benchmark-expansion-protocol-finalization.md), [candidate registry](benchmark-candidate-registry.md), and [quality gates](benchmark-quality-gates.md)
- [Phase 9 corpus selection](corpus-final-selection.md) and [Phase 16 Humanize readiness decision](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md)
