# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18.1 — Expansion Readiness Checklist

**Review date:** 2026-09-27  
**Status:** Assessment checklist; completion records evidence found in the reviewed documents only. No expansion is authorized.  
**Protected state:** Humanize remains frozen. Do not add repositories, create benchmark questions, or modify retrieval code.

Use the owner/reviewer fields to assign accountable people in a future decision record. `Unassigned` means no named person was evidenced in the reviewed materials; it is not an assignment. A checkbox is complete only when the cited evidence establishes the requirement. This checklist records no gate approval.

## Completed requirements — preparation/documentation only

| State | Requirement completed | Owner / reviewer fields | Evidence reference |
|---|---|---|---|
| [x] | Phase 17 protocol and future gate model are documented. This completes protocol design only; the protocol itself remains proposed and expansion blocked. | Protocol author: **Not identified**; approving benchmark owner: **Unassigned / no approval evidenced** | [Phase 17 protocol](benchmark-expansion-protocol.md), especially status and G0–G6 gates. |
| [x] | Phase 18 candidate registry records the existing nine frozen snapshots, rationale, size, language/license screening, and pending readiness/clearance. | Registry maintainer: **Not identified**; G1 approvers: **Unassigned** | [Candidate registry](benchmark-candidate-registry.md); [frozen corpus selection](corpus-final-selection.md). |
| [x] | Phase 18 expansion plan documents future stages, milestones, resource categories, reviewer workflow, rollback criteria, and success metrics. | Plan owner: **Not identified**; accountable benchmark owner: **Unassigned** | [Expansion plan](benchmark-expansion-plan.md). |
| [x] | Phase 18 quality-gate criteria document G1–G6 evidence and pass/fail boundaries. | Gate-document owner: **Not identified**; gate approvers: **Unassigned** | [Quality gates](benchmark-quality-gates.md). |
| [x] | The Humanize pilot-only freeze/exclusion boundary and historical exposure are explicitly retained in the preparation records. | Pilot custodian: **Unassigned**; benchmark owner: **Unassigned** | [Humanize readiness decision](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md); [pilot closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md). |

“Completed” above means the document or evidence statement exists. It does not mean protocol approval, candidate clearance, gate passage, or expansion authorization.

## Pending requirements — decision or evidence not found

| State | Requirement pending | Owner / reviewer fields to assign | Evidence reference / closure record required |
|---|---|---|---|
| [ ] | Record G0 approval of the versioned protocol/scope and separately authorize the exact bounded next activity. | Benchmark owner / approving authority: **Unassigned**; independent reviewer: **Unassigned** | [Phase 17 protocol](benchmark-expansion-protocol.md), G0; signed decision record with scope/artifact digests, date, conditions, outcome, and authorized activity. |
| [ ] | Resolve historical nine-repository / 108-new-case allocation versus repository-level development/blind independence; define exposure policy and related-snapshot grouping. | Benchmark owner: **Unassigned**; evaluation custodian: **Unassigned**; independent methods reviewer: **Unassigned** | [Phase 17 checklist](benchmark-expansion-checklist.md), pre-selection checks; versioned allocation/split decision and controlled exposure manifest specification. |
| [ ] | Approve category/taxonomy and schema mapping, ID-collision policy, difficulty allocation, sampling/order, exclusion rules, thresholds, and any required tooling migration. | Benchmark owner: **Unassigned**; schema/validation owner: **Unassigned**; reviewer: **Unassigned** | [Benchmark schema](benchmark-schema.md); [Phase 17 protocol](benchmark-expansion-protocol.md); recorded G0 decision and separately authorized tooling plan if needed. |
| [ ] | Name and confirm capacity for all governance, annotation, independent review, adjudication, validation, evaluation custody, experiment, data/privacy, license, and incident/rollback roles. | Assign each role and named reviewer: **Unassigned** | [Expansion plan](benchmark-expansion-plan.md), resource requirements; named-role roster, conflict/exposure declarations, and capacity acceptance. |
| [ ] | Approve controlled research-data storage, access, backup, retention/deletion, incident response, and external transmission/distribution policy. | Data/privacy steward: **Unassigned**; security reviewer: **Unassigned** | [Phase 17 protocol](benchmark-expansion-protocol.md), privacy/licensing requirements; attributable handling/storage approval. |
| [ ] | Complete G1 privacy, source-use, license/notice, provenance, history/secret, personal/confidential-data, and handling review for each exact candidate commit and activity. | Candidate data/privacy reviewer: **Unassigned**; license reviewer: **Unassigned**; benchmark owner: **Unassigned** | [Candidate registry](benchmark-candidate-registry.md); per-candidate clearance decision, scan/review evidence, source/snapshot identities, and approved activity. |
| [ ] | Disposition known Flask, pytest, and Sphinx scan findings and the Sphinx history-scan error under authorized review. | Data/privacy steward: **Unassigned**; scan/history reviewer: **Unassigned** | [Candidate registry](benchmark-candidate-registry.md); protected evidence in approved internal record, with only safe disposition references here. |
| [ ] | Complete remaining candidate-specific reviews, including file-level notice review where identified; do not infer clearance from public availability or root license. | License reviewer: **Unassigned**; privacy reviewer: **Unassigned** | [Candidate registry](benchmark-candidate-registry.md); attributable G1 record for each candidate. |
| [ ] | After G1 only, verify approved snapshots/inventories and deterministic provenance; then lock annotation allocation, split/access, rubric, case IDs, workload, and independent review assignments for G2. | Inventory/validation owner: **Unassigned**; annotation lead: **Unassigned**; evaluation custodian: **Unassigned** | [Phase 17 checklist](benchmark-expansion-checklist.md), annotation readiness; G2 evidence package. |
| [ ] | Complete 100% manual annotation and independent review, agreement measurement/calibration, evidence checks, structural validation, and synchronized exports at G3. | Annotation lead: **Unassigned**; independent review lead: **Unassigned**; adjudicator: **Unassigned**; validation owner: **Unassigned** | [Quality gates](benchmark-quality-gates.md), annotation/evidence gates; future controlled ledger and signed G3 report. No annotation is authorized by this checklist. |
| [ ] | Obtain G4 benchmark freeze approval, later G5 evaluation authorization, and G6 release approval as separate decisions. | Benchmark owner: **Unassigned**; evaluation custodian/experiment owner: **Unassigned**; data steward: **Unassigned** | [Phase 17 protocol](benchmark-expansion-protocol.md), G4–G6; versioned freeze, run, and release decision records. |

## Blocking items

1. **Protocol/scope blocker:** Phase 17 is marked proposed; no G0 acceptance or explicit bounded authorization is evidenced.
2. **Candidate clearance blocker:** No G1 clearance is evidenced for any candidate. Known open findings and the Sphinx history-scan error remain unresolved in the reviewed registry.
3. **Independence blocker:** No approved split/exposure manifest is evidenced, and the historical target has not been reconciled with the blind-evaluation requirement. Humanize is exposed and its pilot cases cannot be reused.
4. **Governance/capacity blocker:** No named owner/reviewer roster or capacity acceptance is evidenced.
5. **Handling blocker:** Repository-specific storage, access, retention, transmission, and distribution decisions are not evidenced.
6. **Downstream gate blocker:** G2–G6 require future evidence and approvals; none is passed or authorized by this review.

## Decision record fields — fill only when evidence exists

| Field | Entry |
|---|---|
| Decision requested | Remain in preparation / revise protocol / other: **Not yet approved** |
| Protocol and scope version/digest | **Pending** |
| Evidence bundle location/digest | **Pending** |
| Accountable benchmark owner | **Unassigned** |
| Independent reviewer / approver | **Unassigned** |
| Data/privacy and license reviewers | **Unassigned** |
| Date and decision outcome | **Pending** |
| Conditions and exact next activity authorized | **None; expansion not authorized** |
| Humanize pilot preservation verified | **No new verification performed by this documentation review; pilot remains frozen by existing record** |

## Current readiness disposition

**Not ready to proceed to controlled benchmark expansion. Remain in preparation.** This checklist records documentary completion and outstanding gates; it does not grant approval. Do not begin source/inventory processing, annotation, retrieval evaluation, benchmark freeze, or release. Keep Humanize frozen.
