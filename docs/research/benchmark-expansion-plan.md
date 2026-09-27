# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18 — Benchmark Expansion Plan

**Date:** 2026-09-27  
**Status:** Execution-preparation plan only; no expansion is authorized or performed.  
**Basis:** [Phase 17 benchmark expansion protocol](benchmark-expansion-protocol.md) and [Phase 17 checklist](benchmark-expansion-checklist.md).  
**Protected state:** Humanize remains frozen for pilot use; the current benchmark, retrieval code, candidate repositories, and source snapshots remain unchanged.

This document sequences future work; it does not mark any gate approved. The protocol records all execution gates as pending. Before any activity beyond this planning package, the accountable owners must record G0 acceptance and the exact bounded activity authorized. Repository-specific clearance is not implied. No repositories or questions are added by Phase 18, and this plan does not execute any stage.

## Stages and milestones

| Stage | Milestone and work boundary | Required exit evidence / gate | Status now |
|---|---|---|---|
| 0. Scope and authorization | Reconcile the frozen candidate list, historical nine-repository/108-case target, category/taxonomy mapping, difficulty distribution, Humanize exclusion/exposure, repository-level development/blind split, reviewer independence, budget, storage, and tooling policy. Identify accountable owners. | G0 decision record with protocol/scope digests, named approver, conditions, outcome, and exact next activity authorized. Any allocation change requires a versioned decision and migration plan. | **Not started; no execution authority recorded here.** |
| 1. Candidate-specific clearance | For each existing candidate, establish exact repository identity, pinned full commit, source origin, snapshot identity, eligible-file policy, provenance, applicable license/notices, secret/history and personal/confidential-data disposition, handling and transmission permissions. | G1 decision for each exact snapshot and bounded activity; zero unresolved clearance findings affecting that activity. | **Blocked; all candidates remain pending clearance.** |
| 2. Snapshot and inventory preparation | Only after that candidate's G1 approval, prepare/verify its read-only pinned snapshot and deterministic eligible-file/chunk inventory under the approved pipeline. Record exclusions, hashes, parser/chunker limits, and processing cost. Do not use inventories for annotation until G2. | Provenance/inventory evidence, deterministic identity checks, and approved storage/access record supplied to G2. | **Not started.** |
| 3. Annotation readiness | Freeze the ledger/rubric/schema contract, repository allocation and IDs, category/difficulty quotas, sampling/order, exclusions, exposure register, split manifest, access controls, storage, workload, and independent-review assignments. | G2 approval by annotation lead and evaluation custodian; inventory and access controls verified; reviewer capacity confirmed. | **Not started.** |
| 4. Manual authoring and independent review | In a separate controlled staging area, manually author only the approved allocation from pinned static source; independently review every case; retain initial judgments before comparison; adjudicate disputes; synchronize exports from one canonical ledger. Never use retriever rankings to create or tune labels. | Complete authoring/review ledger, retained agreement counts and adjudications, all cases finally accepted, and G3 validation evidence. | **Not started; no questions may be created in this phase.** |
| 5. Validation and benchmark freeze | Validate allocation, category/schema, provenance, IDs/spans, exact evidence, primary/supporting grades, dependencies, review, pilot exclusion, exports, and protected-artifact hashes. Freeze a separately versioned package before any evaluation. | G3 sign-off and G4 freeze decision, with verified immutable package digests and prior-version preservation. | **Not started.** |
| 6. Locked retrieval evaluation | Only after G5 approval, custodian runs the preregistered development/blind and repository-scoped/pooled tasks against the approved candidate universe. Retain complete rankings/traces, failures, metrics, and two fresh-process comparisons. | G5 authorization and a reproducible report that follows the predeclared metric/eligibility contract. Retrieval scores do not determine annotation validity. | **Not started; no retrieval run is authorized here.** |
| 7. Release decision and closeout | Review clearances, freeze identity, validation/evaluation reports, limitations, distribution rights, audience, and rollback readiness. Publish only the explicitly approved artifact set. | G6 decision, signed by benchmark owner and data steward, for the named version and audience. | **Not started; no release is authorized.** |

The current nine-snapshot list and screening metadata are recorded in the [candidate registry](benchmark-candidate-registry.md). Humanize's existing pilot remains a protected, exposed development artifact; it is not silently incorporated into a new evaluation set.

## Resource requirements

G0 must approve named owners, availability, budget, and a controlled research-data location before execution. No staffing or compute availability is assumed by this plan.

- **Governance and clearance:** benchmark owner; repository-specific data/privacy steward; license/notice reviewer; source-provenance reviewer; incident owner. Each must have time to resolve or block the exact candidate decision.
- **Annotation:** annotation lead and manual annotators with static-source expertise. The historical target corresponds to 108 new cases only if G0 retains that allocation; Humanize's 12 frozen cases do not count toward it.
- **Independent review:** qualified independent human reviewer coverage for 100% of included cases, plus an independent adjudicator for unresolved disputes. Authors cannot independently review their own cases. Capacity must account for review corrections and full re-review after failed calibration.
- **Evaluation custody:** evaluation custodian with access separation for blind query/gold data; experiment owner responsible for locked configurations, repeatability, and failure records.
- **Validation and data operations:** validation owner; controlled storage with authorized-reader controls, backup/retention/deletion policy, digested manifests, and incident handling; separate staging that does not alter the pilot or current benchmark.
- **Compute and tooling:** resources for the already approved local preprocessing and, only after G5, the locked retrieval runs and two fresh-process comparisons. Exact CPU/GPU, storage, token, time, and monetary budgets are to be measured from approved inventories and approved at G0/G5; this plan invents no numeric estimate.
- **Documentation and audit:** decision ledger and versioned protocol, inventory, annotation, review, split/exposure, validation, run, freeze, and release records. Source-derived materials remain in approved controlled storage, not committed reports, unless separate distribution approval exists.

## Reviewer workflow

1. Assign each case to an independent reviewer who has not authored it. Confirm qualifications, candidate exposure, and access authorization before review.
2. Have the reviewer independently inspect pinned static source and record a proposed evidence set, grades, category, difficulty, ambiguity, and rationale **before** exposing the author's labels or any retrieval output.
3. Preserve both initial records. Then compare and record `ACCEPT`, `REVISE`, or `REJECT` with reason codes for unsupported claims, missing dependency hops, span/ID errors, ambiguity, taxonomy/difficulty disagreement, privacy issue, or duplicate/leakage concern.
4. Return revised cases for renewed independent review. An independent adjudicator resolves remaining disputes from source evidence; unresolved disputes remain blocked. Rejection is not permission to silently discard a hard case or replace it based on retrieval results.
5. Retain pre-adjudication agreement counts and denominators overall and per repository: exact evidence-set, exact graded-evidence, category, and difficulty agreement. Report adjudicated outcomes separately; do not characterize post-adjudication unanimity as initial agreement.
6. Require 100% final acceptance and independent review for included cases. If exact graded-evidence agreement is below 80% overall or in any repository, pause, calibrate using development material, independently re-review all affected cases, retain both rounds, and repeat until the threshold is met.
7. Generate retrieval exports from the canonical ledger only. Keep corrections, rejected/deferred cases, replacement rationale, audit history, source spans, and review metadata in controlled records. No LLM-generated or LLM-verified ground truth.

## Validation gates

- **G0 — Protocol and scope:** approvals for allocation, taxonomy/schema, independence split, exposure, owners, thresholds, budget, handling, and tooling plan; authorization names the next bounded action.
- **G1 — Repository clearance:** exact repository/commit and source-use, license, privacy, history, storage, processing, reader, retention, and transmission decisions. Missing evidence or unresolved relevant findings block the candidate.
- **G2 — Annotation readiness:** verified inventory and provenance, locked allocation/split/access, frozen rubric, workload, case IDs, and independent-review/adjudication capacity.
- **G3 — Review and validation:** full independent review, thresholds met, zero unresolved structural/provenance/evidence issues, synchronized derived exports, and pilot/prior-benchmark preservation verified.
- **G4 — Benchmark freeze:** separate immutable version with snapshot/inventory, ledger/review, category map, split/exposure, protocol/schema/rubric, tool/version, approval, and timestamp identities/digests. Freeze precedes retrieval evaluation.
- **G5 — Retrieval evaluation:** custodian and experiment owner approve frozen identity, locked code/config/model/runtime, candidate universe, task scope, metric contract, seeds/hardware, compute/handling, and repeatability plan before any run.
- **G6 — Release:** benchmark owner and data steward accept the exact evaluation/validation evidence, limitations, rights, audience, manifest, and rollback readiness. Freeze is not release approval.

Detailed pass/fail requirements are in [benchmark quality gates](benchmark-quality-gates.md). A validator pass is structural evidence only; it is not privacy clearance, source-level correctness, human review, retrieval effectiveness, or release authorization. The known validator artifact-allowlist caveat must be handled only through a separately authorized, tested tooling/policy decision without bypassing existing invariants.

## Rollback and stop criteria

Immediately stop the affected stage and suspend downstream approvals for any of the following:

- clearance, license/notice, privacy, or handling incident;
- source/snapshot/inventory hash or provenance mismatch;
- unauthorized repository, scope, allocation, access, or artifact change;
- unsupported or unresolvable gold evidence, failed quality threshold, or unresolved reviewer dispute;
- pilot contamination, holdout leakage, or loss of the declared independence claim;
- incomplete parent/gold eligibility, silent truncation, evaluator/metric mismatch, or unexplained nondeterminism;
- incomplete release permissions, invalid freeze digest, or inability to verify rollback readiness.

The stage owner records the incident and affected artifacts in the approved internal process; the benchmark owner suspends downstream decisions. Quarantine candidate artifacts and restrict access/distribution as directed by the data steward. Do not put sensitive findings in committed reports. Before release, return to the earliest failed gate in isolated staging. After release, withdraw the affected version, invalidate dependent results, and restore a prior approved reference only if its integrity and clearance remain valid. Never overwrite a frozen/released artifact or the Humanize pilot. Corrections require a new version and renewed affected gates; leakage retires the exposed partition's blind claim. Resume only after accountable approvers accept documented remediation.

Low retrieval scores alone are not a rollback or benchmark-rejection criterion.

## Success metrics

These are protocol acceptance measures, not claims that any have been achieved. Any target/allocation change requires the G0 versioned decision.

- **Scope and clearance:** 100% of included repository snapshots are exact-pinned and cleared for the named activity; zero unresolved relevant findings. The candidate registry records all nine frozen snapshots without additions or substitutions.
- **Allocation:** if the historical target is reaffirmed at G0, complete exactly nine approved repositories and 108 new cases, 12 per repository and three per category per repository, subject to the independence decision. Humanize's existing cases are excluded from final slots. No partial batch is represented as a complete benchmark.
- **Review quality:** 100% of included cases independently reviewed and finally accepted; zero unresolved disputes/ambiguities/unsupported claims; exact graded-evidence agreement at least 80% overall and in every repository before adjudication, using unrounded ratios.
- **Evidence and structural integrity:** 100% of gold evidence resolves to the correct pinned snapshot; each case has at least one primary grade-2 item and all necessary supporting hops; zero unresolved span/ID/export/schema errors or pilot contamination.
- **Eligibility:** 100% declared-parent and gold eligibility for any primary complete-inventory evaluation; zero silent exclusions, truncations, duplicate result parents, or dropped evidence.
- **Evaluation repeatability:** two fresh-process runs agree on ordered parent rankings and metric artifacts, with numeric trace-score tolerance declared before runs; unexplained differences block acceptance.
- **Reporting completeness:** retain fixed denominators and report evidence-occurrence micro and mean per-question recall, complete-evidence success, MRR/nDCG only after evaluator compatibility verification, plus repository/category/difficulty/partition/task breakdowns and failures. Retrieval quality has no minimum pass score; no system-promotion claim without preapproved numeric thresholds.
- **Freeze and release integrity:** 100% of expected digests verify; zero changes to the frozen Humanize pilot or prior benchmark versions; release, if ever separately approved, contains only authorized artifacts and audience.

**Phase 18 disposition:** Execution materials prepared only. All gates remain pending; no repository, question, annotation, inventory, retrieval run, freeze, or release has been created or performed. Humanize pilot remains frozen.
