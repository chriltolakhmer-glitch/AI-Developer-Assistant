# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18.1 — Benchmark Expansion Gate Review

**Review date:** 2026-09-27  
**Review scope:** Readiness to move from documentation/preparation into controlled benchmark expansion.  
**Status:** Documentation-only assessment. **Expansion is not authorized.**  
**Protected state:** Humanize remains frozen; no repository, question, retrieval code, or benchmark artifact is changed by this review.

## Executive decision

**Decision: Remain in preparation.** The project is not ready to begin controlled expansion. Phase 18 has produced planning materials, but Phase 17 remains explicitly marked as a proposed protocol with all execution gates pending. No G0 authorization or candidate-specific G1 clearance is evidenced. Candidate readiness, staffing, split independence, and required handling decisions remain unresolved.

This review does not authorize repository inspection, snapshot/inventory processing, annotation, retrieval evaluation, freezing, or release. It identifies what is evidenced and the decisions still needed. Humanize stays frozen for pilot use only; its existing questions cannot fill final benchmark slots or support an unseen-repository claim.

## Phase 17 protocol status

The [Phase 17 protocol](benchmark-expansion-protocol.md) records:

- **Status:** “Proposed protocol; documentation only. Expansion execution remains BLOCKED.”
- Every gate G0–G6 is pending future execution; approval of the design alone does not authorize expansion.
- The historical target of nine repositories and 108 cases is a design target, not an authorization. G0 must reconcile it with repository-level development/blind independence and Humanize exposure.
- Repository clearance, independent annotation/review, validation, freeze, evaluation, and release require separate evidence-backed decisions.

The [Phase 17 checklist](benchmark-expansion-checklist.md) also records G0 and subsequent checks as unchecked. No signed decision record or approval evidence for G0–G6 was found among the reviewed materials.

## Phase 18 preparation status

The Phase 18 planning deliverables are present:

- [Candidate registry](benchmark-candidate-registry.md) records the nine already-selected snapshots, screening metadata, and explicitly pending approval/privacy/readiness states.
- [Expansion plan](benchmark-expansion-plan.md) defines the future stages, resources, reviewer workflow, gates, rollback criteria, and metrics.
- [Quality gates](benchmark-quality-gates.md) provides proposed pass/fail criteria for G1–G6.

These documents complete the **documentation-preparation task**, not the expansion gates. They do not establish that reviewers or budget are assigned, that a candidate is cleared, or that any G0–G6 decision has passed. No expansion execution is recorded.

## Candidate registry review

The registry contains only the nine snapshots in the frozen corpus selection; no repository has been added or substituted. Its entries are planning records and not approvals.

- All candidates remain pending repository-specific G1 authorization and clearance.
- The registry records known open concerns for Flask (six unresolved Gitleaks snapshot candidates), pytest (one unresolved candidate), and Sphinx (one unresolved candidate and a history-scan `.dot` error). These require authorized disposition; this review does not resolve them.
- Humanize is explicitly pilot-only and frozen. Its prior pilot clearance requirements remain unresolved; its 12 cases are excluded from final slots and the repository is exposed/development data.
- The corpus-level record still requires repository-specific privacy, history/secret, personal/confidential-data, licensing/notices, provenance, storage, and handling decisions. No candidate's public availability or license label constitutes approval.

## Quality gate readiness

| Gate | Readiness finding | Current disposition |
|---|---|---|
| G0 — Protocol and scope | Protocol and criteria are documented, but approval of allocation, taxonomy/schema, independent split, exposure policy, named roles, thresholds, budget, storage, and tooling policy is not evidenced. The 9/108 allocation versus independence needs an explicit decision. | **Not passed; blocks all execution.** |
| G1 — Repository approval | Registry lists existing candidates and known open findings; no repository-specific, commit-specific clearance/processing decision is evidenced. | **Not passed for every candidate.** |
| G2 — Annotation readiness | No verified post-clearance inventories, locked split/access manifest, allocation/IDs, named annotators/reviewers/custodian, or workload acceptance is evidenced. | **Not passed.** |
| G3 — Review and validation | No expansion annotations or independent review results exist. Phase 18 defines criteria only. | **Not started / not passed.** |
| G4 — Benchmark freeze | No expansion benchmark package, digests, or freeze approval exists. | **Not started / not passed.** |
| G5 — Retrieval evaluation | No G5 run approval or evaluation permission is evidenced; no run is authorized by this review. | **Not started / not passed.** |
| G6 — Release | No distribution approval, release manifest, audience decision, or rollback sign-off exists. | **Not started / not passed.** |

The existing Humanize pilot's review, structural validation, and retrieval diagnostics apply only to that frozen pilot. They do not satisfy expansion G1–G6 and do not establish blind or cross-repository validity.

## Missing approvals and evidence

1. **G0 decision record:** named benchmark-owner acceptance of the versioned protocol, target allocation and its independence feasibility, taxonomy/schema mapping, split/exposure policy, reviewer assignments, thresholds, budget, approved storage/handling, and validator artifact policy. It must state the exact bounded next activity authorized.
2. **Named owners and capacity:** accountable benchmark owner, data/privacy steward, license reviewer, annotation lead, independent reviewers and adjudicator, evaluation custodian, validation owner, experiment owner, and incident/rollback owner; reviewer independence and sufficient workload capacity must be evidenced.
3. **Candidate-specific G1 decisions:** attributable privacy/history/secrets and personal/confidential-data review, notice/license disposition, immutable provenance, scope/file policy, storage/reader/retention/backup/incident controls, and separate transmission/distribution decisions for each exact snapshot.
4. **Open finding disposition:** authorized resolution for the identified Flask, pytest, and Sphinx scan findings and Sphinx history-scan error; completion of other required candidate-specific reviews, including Humanize's existing unresolved status if any future activity is separately proposed.
5. **Allocation and independence resolution:** documented repository-level development/blind split and exposure register, grouping related sources, with a determination whether the historical nine-repository/108-new-case target can support the intended independent claim without using Humanize pilot cases. Any changed target requires a versioned scope decision and tooling plan.
6. **G2 readiness evidence:** after applicable G1 approvals, verified inventory/provenance, controlled storage/access, locked split and allocation, rubric/schema, manual workflow, reviewer/adjudicator assignments, and accepted workload.
7. **Future G3–G6 evidence:** these cannot be passed at preparation time. They require completed review/validation, a pre-evaluation freeze, separate G5 run approval, and G6 rights/release approval respectively.

## Principal risks

- **Unauthorized processing or use:** treating protocol design, registry inclusion, or a license label as permission could breach unresolved privacy or rights boundaries.
- **False independence/generalization:** the small, pilot-informed Humanize set and exposed repositories could be misrepresented as blind evaluation; the nine/108 target may not yield the intended independent partition.
- **Open screening findings:** unresolved secret/history findings or the Sphinx history-scan error may affect permitted scope and cannot be waived by this review.
- **Reviewer bottleneck or compromised review:** 100% independent case review and an adjudication path are required; no evidence of named capacity is present.
- **Stale or misleading validation:** the known pilot validator filename allowlist caveat must be handled without weakening invariants or overstating a supplemental pass.
- **Scope drift and frozen-artifact damage:** unversioned candidate/count changes, pilot reuse, or edits to Humanize could invalidate provenance and existing freeze records.
- **Premature evaluation/release:** G4 freeze, G5 evaluation, and G6 distribution are distinct permissions and must not be inferred from an earlier gate.

## Decision options

### Option A — Proceed to controlled expansion

**Not supported now.** This would be appropriate only after an explicit G0 decision authorizes the exact bounded next stage. Candidate work must then remain gated by G1; G0 must not be treated as clearance to annotate or evaluate. Current evidence does not satisfy these conditions, so this option is not selected and no expansion is authorized.

### Option B — Remain in preparation

**Selected.** Keep Humanize frozen and the expansion blocked. The next governance work is to assemble G0 evidence, name accountable owners/reviewers, resolve the target/split question and handling/tooling policy, and plan candidate-specific G1 review. Any activity beyond documentation must wait for a recorded G0 authorization and remain within its exact boundary.

### Option C — Revise protocol

**Conditional alternative.** Reopen and version the protocol if G0 cannot reconcile the 9/108 target with the blind repository claim, if taxonomy/schema or ID rules need change, if the validator policy cannot preserve existing invariants, or if reviewer/handling requirements cannot be met. A revision must document its rationale and receive a new approval; revision itself does not authorize execution.

## Final disposition

**Remain in preparation; not ready to move into controlled benchmark expansion.** Phase 18 preparation documentation is complete, but Phase 17 is still proposed, G0 is not evidenced, and no G1–G6 approval is evidenced. No work is authorized by this assessment beyond documentation. Humanize pilot remains frozen; no repositories or benchmark questions are added.
