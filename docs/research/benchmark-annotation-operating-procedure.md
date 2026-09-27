# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18.2 — Benchmark Annotation Operating Procedure

**Date:** 2026-09-27  
**Status:** Proposed SOP for later approval; **not active and not authorization to annotate**.  
**Boundary:** No source is inspected and no questions/labels are created by this document. Humanize remains frozen. No repositories are added; retrieval code is unchanged.

## Authority and prerequisites

This procedure operationalizes the manual annotation and review controls in the [Phase 17 protocol](benchmark-expansion-protocol.md), [Phase 17 checklist](benchmark-expansion-checklist.md), and [Phase 18 quality gates](benchmark-quality-gates.md). It also references the existing [benchmark schema](benchmark-schema.md), [annotation guide](benchmark-annotation-guide.md), [Phase 18.1 gate review](benchmark-expansion-gate-review.md), and proposed [independence plan](benchmark-independence-plan.md).

**No annotation may begin** until all of the following are evidenced: accepted G0 scope and exact authorization; candidate-specific G1 approval for the relevant source activity; approved snapshots and verified deterministic inventories; accepted G2 split/access controls, schema/rubric/allocation/ID policy, storage, workload, and named roles; and independent reviewer/adjudicator capacity. This SOP itself closes none of those gates. Phase 17's full independent review standard supersedes any earlier optional/partial review description for future expansion; reviewers cannot be authors of their assigned cases.

## Roles and separation of duties

| Role | Responsibility | Required record |
|---|---|---|
| Benchmark owner | Accepts scope, protocol version, and gate-specific activity | Attributable G0/G4/G6 decision records |
| Annotation lead | Assigns approved case slots and author workload; enforces canonical ledger | Allocation and change log |
| Case author | Manually derives a question and evidence from authorized pinned static source | Author identity, date, exposure declaration, source-backed ledger entry |
| Independent reviewer | Creates an initial independent judgment before seeing author labels or retrieval output | Separate timestamped review record and disposition |
| Adjudicator | Resolves remaining reviewer/author disagreement independently | Reasoned adjudication and evidence reference |
| Evaluation custodian | Controls blind material and access; preserves partition status | Access/exposure log and split-manifest custody |
| Validation owner | Checks structural/provenance invariants and export consistency | Tool versions, inputs/digests, outputs, issues/dispositions |
| Data/privacy and license reviewers | Confirm bounded permitted handling; resolve clearance issues | Candidate G1 decision evidence |

Roles can be administratively combined only where Phase 17 permits, but no author may independently review their own cases. Reviewer unavailability, conflict, or unknown exposure blocks the case/batch.

## Controlled record and fixed annotation contract

Use a single canonical ledger outside the committed research repository, in the G1/G2-approved storage. For each approved case preserve at minimum:

- unique query ID, canonical repository ID, full pinned commit SHA, query, one of the four existing categories, and easy/medium/hard difficulty;
- exact repository-relative file, symbol, one-based inclusive source span, deterministic chunk ID(s), and integer relevance grades (`2` primary; `1` necessary support);
- concise rationale, ambiguity disposition, author/date, source/exposure history, independent review record, correction history, and final disposition.

Each case needs at least one primary grade-2 item and all necessary supporting hops. Verify dependencies at the actual source call/import/reference site. Keep the existing schema 1.0 projection separate from ledger-only fields; do not silently change loader fields, query IDs, taxonomy, target counts, chunk boundaries, or grading. Any contract change needs a versioned decision and separately authorized tooling/test plan. Generate derived exports from the canonical ledger; never hand-edit duplicate copies into apparent agreement.

## Procedure — only after G2

1. **Allocate before retrieval:** issue approved repository/case/category slots, difficulty targets, order/sampling rule, inclusion/exclusion policy, and IDs. Record the accepted split/exposure manifest and keep blind gold in custodian control. No selection based on retrieval rankings.
2. **Author manually:** from the approved pinned static snapshot, author concise, answerable questions without runtime speculation. Record exact source evidence, all required hops, grades, rationale and ambiguity. Do not use LLM-generated or LLM-verified ground truth.
3. **Self-check source claims:** verify each claimed call/dependency at the call/import/reference site, exact path/symbol/span and chunk identity against the same snapshot. Search plausible alternatives where needed. Do not treat nearby or similar helpers as evidence.
4. **Independent first review:** reviewer, without seeing author labels or any retrieval output, records an independent evidence set, grades, category, difficulty, ambiguity and rationale. Preserve the initial timestamped record before comparison.
5. **Disposition:** compare only after both initial records exist. Record `ACCEPT`, `REVISE`, or `REJECT` plus reason code. Corrections retain old/new record identities, change reason and source evidence, and return to independent review. Keep rejected/deferred cases and reasons; do not silently replace a hard case.
6. **Adjudicate:** use an independent adjudicator for unresolved conflicts. If no qualified adjudicator is available, the case remains blocked. Do not use a fresh model session as an independent human judgment.
7. **Measure agreement:** calculate pre-adjudication exact evidence-set, exact graded-evidence, category and difficulty agreement as matches/double-reviewed cases, overall and per repository. Report disagreement and adjudication separately. No invented pilot agreement statistic.
8. **Apply threshold:** require at least 80% exact graded-evidence agreement overall and in each repository using unrounded ratios. If below threshold, pause the batch, calibrate on development material, independently re-review every affected case, retain all rounds and repeat. Require 100% of included cases independently reviewed and finally accepted; zero unresolved disputes or ambiguity affecting answerability.
9. **Validate and synchronize:** validate snapshot, IDs, spans, inventory resolution, grades, category/difficulty, primary/supporting completeness, duplicate/leakage, counts, and derived exports. Preserve validator version/output and exact supplemental allowlist; do not claim a normal validator pass if invocation was modified.
10. **Close G3:** independent review lead and validation owner sign the report only after all thresholds and integrity checks pass. Benchmark owner decides G4 separately. Annotation acceptance does not authorize freeze, retrieval evaluation, release, or alteration of Humanize.

## Records, access, and stop conditions

Source, chunk inventories, questions, gold labels, exact paths/spans, reviewer notes, scan findings, and raw artifacts remain in approved controlled storage. Committed documentation contains only authorized aggregate status/digests. No external model/service or reviewer receives content absent separate explicit approval.

Stop the affected work on any clearance issue, snapshot mismatch, unauthorized access/scope change, source/evidence ambiguity, unsupported dependency, split leakage, reviewer conflict, failed threshold, or inconsistent export. Quarantine affected material, preserve permitted audit records, and return to the earliest failed gate. Corrections are versioned and re-reviewed. Never modify the Humanize pilot or silently overwrite a frozen/released version.

## Current status

All procedural steps are **future requirements**, not completed work. G0 and all G1–G6 approvals remain pending in the reviewed records. No inventory, annotation, review, or validation activity is authorized by this SOP.

## Existing references

- [Phase 17 protocol](benchmark-expansion-protocol.md) and [Phase 17 checklist](benchmark-expansion-checklist.md)
- [Phase 18 quality gates](benchmark-quality-gates.md), [candidate registry](benchmark-candidate-registry.md), and [G0 decision record](benchmark-expansion-g0-authorization.md)
- [Phase 18.1 gate review](benchmark-expansion-gate-review.md) and [readiness checklist](expansion-readiness-checklist.md)
- [Benchmark schema](benchmark-schema.md), [annotation guide](benchmark-annotation-guide.md), and [independence plan](benchmark-independence-plan.md)
- [Phase 16 Humanize readiness decision](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md)
