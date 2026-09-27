# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 17 — Benchmark Expansion Checklist

**Date:** 2026-09-27  
**Status:** Future-use checklist; all execution gates pending.  
**Authority:** [Benchmark expansion protocol](benchmark-expansion-protocol.md).

Phase 17 is documentation and planning only. Humanize stays frozen, the current benchmark stays unchanged, and expansion execution remains BLOCKED. The unchecked items below are future requirements, not instructions to execute now. Completing this document does not grant approval.

For each future check, record evidence location/digest, responsible person, date, and disposition in the controlled decision ledger. A check is complete only with evidence; `N/A` requires a recorded reason and gate-owner acceptance and cannot waive a mandatory threshold. Gate decisions identify the exact next activity authorized. Changed inputs reopen affected gates.

## Pre-selection checks

- [ ] G0: Benchmark owner accepts the versioned protocol and separately authorizes the bounded next phase.
- [ ] Existing candidate scope, pinned-snapshot policy, diversity goals, category quotas, difficulty distribution, budget, and sampling/order are declared without adding repositories.
- [ ] The historical 108-case / nine-repository / 12-per-repository / three-per-category target is reconciled with independence requirements; any change has a separate versioned decision and tooling plan.
- [ ] Humanize pilot exclusion and repository exposure register are defined; pilot cases cannot fill final slots, and Humanize cannot serve as an unseen repository.
- [ ] Repository-level development/blind split rule, related-repository grouping, access controls, and custodian are declared before annotation/tuning.
- [ ] Annotation lead, independent human reviewers, adjudicator, data/privacy steward, license reviewer, validation owner, and experiment owner are assigned with sufficient capacity.
- [ ] Schema/taxonomy mapping, query-ID collision policy, independent-review thresholds, and all quality thresholds are accepted.
- [ ] Approved external research-data storage, retention, backup, transmission, and distribution policies are recorded.
- [ ] Pilot and current benchmark preservation baselines are recorded; expansion staging and reports will be outside the pilot directory.
- [ ] Validator artifact policy addresses the known pilot report allowlist caveat without bypassing invariants; needed tooling work is separately scoped and authorized.

## Repository approval checklist

Repeat for each proposed repository within the existing candidate scope. Approval applies only to the named commit and activity.

- [ ] G1: Canonical repository identity, full commit SHA, origin, snapshot digest, and eligible/excluded-file policy are documented.
- [ ] Size, role, component/dependency structure, static-evidence suitability, annotation effort, and processing budget satisfy declared criteria.
- [ ] Prior inspection/tuning exposure and related forks/snapshots are recorded; partition assignment supports the intended claims.
- [ ] Secret-scan and personal/confidential-data findings are dispositioned; incomplete history scans have a completed review or explicitly approved alternative scope.
- [ ] Applicable licenses, file notices, attribution obligations, exceptions, and internal/derived/distribution permissions are documented by the responsible reviewer.
- [ ] Storage, processing, authorized readers, retention/deletion, external transmission, and incident handling are approved for this snapshot.
- [ ] No unresolved clearance finding remains; public availability is not used as a substitute for clearance.
- [ ] Benchmark owner and responsible clearance reviewers record G1 approval for bounded snapshot/inventory preparation only.

## Annotation readiness checklist

- [ ] G2: Inventory provenance, deterministic chunk identities, snapshot consistency, source coverage, and approved preprocessing contract are verified after G1.
- [ ] Repository/category allocation, case-ID ranges, difficulty targets, sampling/order, and exclusion rules are locked before authoring.
- [ ] Exact split manifest and exposure register are recorded and digested; custodian access controls separate blind material from developers.
- [ ] Category/difficulty rubrics and primary grade 2 / supporting grade 1 definitions are fixed; each case requires primary evidence and every necessary hop.
- [ ] Manual source authoring and human verification are understood; LLM-generated/verified ground truth and retrieval-derived labels are prohibited.
- [ ] Ledger records all required fields, source spans/IDs, rationale, ambiguity, authorship, dates, and review history.
- [ ] Every case has an independent reviewer; initial judgments will be retained before comparison, and disputed cases have an independent adjudication route.
- [ ] Correction, rejection, replacement, and calibration procedures preserve audit history and cannot remove cases based on retrieval performance.
- [ ] One canonical ledger will generate synchronized exports; schema 1.0 payload, category map, difficulty metadata, and digest boundaries are explicit.
- [ ] Annotation lead and custodian record G2 approval for annotation in isolated staging; no frozen pilot artifact will be edited.

## Validation checklist

- [ ] G3: Every approved slot is complete and conforms to declared counts and taxonomy; incomplete batches remain staging.
- [ ] Every case has independent source review and final acceptance; zero unresolved ambiguity, unsupported claims, or review disputes remain.
- [ ] Pre-adjudication exact evidence, graded-evidence, category, and difficulty agreement counts/denominators are retained overall and per repository.
- [ ] Exact graded-evidence agreement meets 80% overall and in each repository; failed batches have documented calibration and complete independent re-review with all rounds retained.
- [ ] Every span/ID resolves to the correct pinned source; dependencies are verified directly, with at least one primary item and all required supports per case.
- [ ] Zero duplicate IDs, cross-snapshot labels, missing evidence, invalid grades, or inconsistent exports remain; manual metadata checks supplement loader checks.
- [ ] Duplicate/near-duplicate pilot questions and development exposure are absent from the claimed blind evaluation partition.
- [ ] Validation owner records actual tooling versions, outputs, zero unresolved errors, and exact supplemental allowances, if any; no ordinary validator pass is claimed from a modified invocation.
- [ ] Required future tooling migrations have their own approvals and passing checks; current final freeze invariants are preserved.
- [ ] Pilot/prior benchmark hashes match the preservation baseline; no protected artifact or code change was made by annotation work.
- [ ] Review lead and validation owner sign G3; benchmark owner verifies G4 freeze criteria before evaluation.
- [ ] G4: Separate versioned freeze package retains benchmark/category-map, snapshot/inventory, ledger, review, split/exposure and protocol identities/digests, approval references, and timestamp.
- [ ] G5: Custodian approves frozen benchmark, locked system/configuration/model/runtime identities, hardware/seeds, task scope, metric formulas, cutoffs, and run permissions before evaluation.
- [ ] Declared candidate universe is common to paired systems; primary experiments have 100% parent/gold eligibility and no truncation, orphan mappings, or duplicate ranked parents.
- [ ] Metrics retain all cases and fixed denominators, distinguish micro and per-question recall, separate primary/supporting evidence, and report repository/category/difficulty/task/partition strata.
- [ ] MRR/nDCG formulas match the evaluator; any incompatibility is resolved under a separate approval before those metrics run.
- [ ] Raw rankings/traces, failure dispositions, uncertainty method/limitations, and two fresh-process comparisons are retained; ordered results/metrics match and score tolerance was declared in advance.
- [ ] Any system-promotion score/regression/resource thresholds were approved before blind results; otherwise only descriptive measurement claims are made.

## Release checklist

- [ ] G6: G0–G5 evidence and decisions are complete for the exact candidate version; there are no unresolved quality, clearance, reproducibility, or exposure failures.
- [ ] Freeze hashes verify retained bytes; previous benchmark versions and the frozen Humanize pilot are intact.
- [ ] Valid evaluation report includes complete results, coverage, denominators, per-repository outcomes, residual failures, and limits on independence/generalization.
- [ ] No retrieval score is used to reject valid hard questions; no claim of answer quality or operational scalability is inferred from retrieval recall.
- [ ] Release artifact list, audience, license/notice obligations, and privacy review are explicit; committed reports contain approved aggregate metadata/digests only.
- [ ] Raw questions, gold labels, source paths/spans, inventories, and sensitive findings remain in controlled storage unless their distribution is separately approved.
- [ ] Rollback owner, incident route, withdrawal procedure, prior approved release reference, and resume criteria are recorded and checked for readiness.
- [ ] Benchmark owner and data steward sign the release decision; the release record distinguishes benchmark validity from any system-promotion decision.
- [ ] Post-release correction policy requires a new version and renewed affected gates; no released artifact or pilot digest is overwritten.

**Current disposition:** Checklist designed, no execution boxes completed. Humanize pilot frozen. Current benchmark unchanged. No expansion execution.
