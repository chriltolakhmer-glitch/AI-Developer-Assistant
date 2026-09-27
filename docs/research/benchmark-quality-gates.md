# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18 — Benchmark Quality Gates

**Date:** 2026-09-27  
**Status:** Gate specification for future controlled work; every gate is pending.  
**Authority:** [Phase 17 benchmark expansion protocol](benchmark-expansion-protocol.md).  
**Boundary:** This document creates no repositories, questions, annotations, inventories, retrieval results, or freeze artifacts. Humanize remains frozen.

Each gate decision must identify the exact protocol/scope version, candidate and artifact identities/digests, evidence location, accountable approver, date, outcome (`APPROVE`, `REVISE`, or `REJECT`), conditions, and the exact next activity authorized. Missing evidence means the gate remains closed. A changed input reopens affected gates. Approval at one gate never implies permission for a later activity.

## 1. Repository approval gate — G1

**Phase 19.6 operational clarification:** Apply this evidence checklist through the [simplified four-gate workflow](benchmark-research-workflow-final.md) and the [Gate 1 calibration](gate1-workflow-calibration.md), not as a renewed requirement for the historical G0-G6 approval chain. Required evidence is unchanged. Record collection progress separately from approval state; `READY FOR REVIEW` is not permission, and `APPROVED WITH CONTROLS` cannot conceal missing mandatory evidence. Use the [updated approval template](repository-approval-template.md) for ownership, scope, report-conflict, handling and decision fields. No candidate status changes through this clarification.

**Purpose:** Clear a specific existing repository snapshot for a specific bounded activity. Public availability, a root license, the corpus selection freeze, or a clean automated scan is not clearance.

**Required evidence for each candidate:**

- Canonical `owner/repository` ID, source origin, full pinned commit SHA, snapshot digest, and reproducible eligible-file inventory or approved inventory-preparation boundary.
- Declared Python-only eligibility, include/exclude/generated/vendor/test policy, file-level exceptions, and known parser/chunker limitations.
- Repository role/size/diversity rationale, prior inspection/tuning exposure, related fork/snapshot grouping, and the split implications for the intended claim.
- Applicable license/version, attribution and notice obligations, file-specific licensing, and separate dispositions for source use, copying, derived annotations, internal evaluation, external review, and redistribution.
- Secret/history scan and personal/confidential-data review outcomes, with findings dispositioned through the approved process. Incomplete history scans need a completed review or explicitly approved, justified alternative scope. Sensitive findings must not be copied into committed reports.
- Approved storage location, authorized readers, access controls, retention/deletion, backup, processing, transmission, and incident handling. External model/service transmission and external reviewer access require separate approval before use.
- Named clearance reviewers and benchmark-owner decision tied to this exact commit and activity.

**Pass criteria:** 100% of included snapshots are pinned and have attributable approval for the authorized activity; zero unresolved findings affecting that activity; all applicable license/notice, privacy, provenance, and handling decisions are explicit.

**Fail/hold:** Any missing evidence, unresolved relevant finding, scope mismatch, unclear rights, incomplete/unapproved history scope, or unapproved transmission keeps G1 closed for that candidate. Quarantine it; do not inspect/use its source or inventory for annotation. A changed snapshot requires renewed review and approval.

**Accountable decision:** Repository-specific privacy/data and license reviewers supply evidence; benchmark owner approves candidate scope. Current disposition: **all G1 decisions pending**. See the [candidate registry](benchmark-candidate-registry.md).

## 2. Annotation quality gate — G2 readiness and G3 completion

**Purpose:** Ensure annotations are manually source-grounded, complete, independently reviewed, and not selected or tuned using retrieval output.

**Readiness evidence at G2:**

- G1-approved repositories and verified inventory provenance; immutable snapshot, schema, rubric, split/access controls, predeclared allocation, IDs, difficulty/sampling rules, and exclusion policy.
- Named annotation lead, author capacity, independent human reviewer coverage for every case, independent adjudicator, evaluation custodian, and adequate time/budget.
- One canonical ledger with required query identity, category, difficulty, evidence, rationale, ambiguity, spans, authorship, date, exposure, and review history; controlled storage and synchronized-export plan.
- Explicit policy that ground truth is authored and verified manually; no LLM-generated or LLM-verified labels and no retrieval-ranking-guided selection or correction.

**Completion evidence at G3:**

- Every included case has an independent initial review performed before the reviewer sees author labels or retrieval output; all initial judgments, disagreements, corrections, and adjudications are retained.
- Every included case has final disposition `ACCEPT`; zero unresolved disputes, unsupported claims, answerability-affecting ambiguity, or suspected duplicate/leakage issue.
- Pre-adjudication agreement numerators/denominators reported overall and per repository for exact evidence-set, exact graded-evidence, category, and difficulty agreement. Post-adjudication outcomes are separate.
- Exact graded-evidence agreement is at least 80% overall and in every repository, using unrounded ratios. If not met, pause the batch, calibrate on development material, independently re-review all affected cases, retain both rounds, and repeat.

**Pass criteria:** G2 authorizes only the declared manual annotation in isolated staging. G3 requires 100% independent review and final acceptance, the agreement threshold met, and zero unresolved quality issues. No author reviews their own case as the independent reviewer; a fresh model session is not a second human reviewer.

**Fail/hold:** Missing reviewers/adjudicator, incomplete initial records, threshold failure, unresolved disagreement, unauthorized source exposure, or retrieval-influenced labels blocks the affected batch. Keep rejected/deferred records and reasons in the audit trail; do not replace cases based on retrieval scores.

**Accountable decision:** Annotation lead and evaluation custodian approve G2; independent review lead and validation owner sign G3.

## 3. Evidence coverage gate — G3 validation

**Purpose:** Demonstrate that every label resolves to complete, correct, source-grounded evidence at the exact pinned snapshot—not merely that an identifier has valid syntax.

**Required checks:**

- Every case resolves to exactly the matching canonical repository ID and full commit SHA; no cross-snapshot evidence.
- Every evidence ID exists in that repository/commit's deterministic chunk inventory; every source file, symbol, and one-based inclusive span resolves to the pinned source and matches the inventory.
- Every case includes at least one grade-2 primary item. Grade 1 marks only necessary supporting context. Every required dependency/call-chain hop is verified at its actual call/import/reference site; nearby or semantically related code is not sufficient.
- Each evidence set is the smallest complete set that supports the answer; all necessary material is covered. Difficult/long evidence is retained rather than excluded to fit a retrieval limit.
- Category/taxonomy mapping, difficulty, rationale, ambiguity disposition, unique IDs, repository slug format, grade types/values, and exact target counts conform to the approved contract.
- Canonical ledger and all derived exports are synchronized. Zero duplicate IDs, orphan mappings, invalid grades, missing spans, mismatched digests, unexplained exclusions, or pilot/near-duplicate contamination.
- All protected Humanize pilot and prior benchmark digests match the preservation baseline. No pilot question or answer is edited or counted toward final slots.
- Structural validator version/output and supplemental artifact allowances are recorded precisely. A supplemental invocation must retain all invariants and must not be presented as an unmodified validator pass.

**Pass criteria:** Zero unresolved structural, provenance, span, evidence, taxonomy, or export issues; 100% evidence provenance resolution; 100% approved allocation complete; pilot/prior-version hashes verified. G3 sign-off is required before G4 can be considered.

**Fail/hold:** Any unresolvable ID/span, unsupported dependency, missing hop, inconsistent export, unresolved ambiguity, incomplete allocation, or failed protected hash blocks G3. Correct only in isolated staging, preserve prior records, independently re-review corrections, and rerun all affected validation. No repair in place of the frozen pilot.

**Accountable decision:** Validation owner, with independent review lead sign-off; benchmark owner confirms G4 separately.

## 4. Retrieval evaluation gate — G5

**Purpose:** Authorize only a preregistered run against the exact frozen benchmark, with blind separation, complete eligibility, valid metrics, and reproducibility controls.

**Required evidence before any run:**

- G0–G4 decisions and exact frozen benchmark/category-map, snapshot/inventory, ledger/review, split/exposure, schema/rubric, tool, and approval identities/digests.
- Repository-level development/blind assignment made before annotation/tuning, related snapshots grouped, access list recorded, and custodian-only access to blind queries/gold. Humanize and any retrieval-development-exposed repository are development/exposed, not blind.
- Locked code revision and dirty-worktree digest if relevant; model/tokenizer, runtime/dependencies, seeds, hardware, representation, token budgets, candidate universe, parent-child mapping, ranking/aggregation, cutoffs, tie-breaking, and task scope.
- Predeclared separate repository-scoped and pooled tasks if both are run; fixed candidate universe for paired comparisons; metric formulas, denominators, failure policy, uncertainty method/limitations, and score tolerance for trace comparisons.
- Evaluator compatibility verified for MRR/nDCG definitions. If incompatible, omit/block the metric pending a separately approved resolution; do not silently substitute a formula.
- Primary complete-inventory run has 100% declared-parent eligibility and 100% eligible gold occurrences, with no silent truncation, missing parents, duplicated ranked parents, or dropped evidence. Report eligibility denominators, including length exclusions.
- G5 approval from evaluation custodian and experiment owner for the exact systems/configuration, task, handling, compute, and run permission.

**Evaluation acceptance criteria:** Preserve every declared case; a failed query receives zero retrieval credit and remains visible. Infrastructure failure invalidates the run and requires an explained full rerun, not selective case removal. Report evidence-occurrence micro Recall@5, mean per-question Recall@5, complete-evidence success@5, compatible MRR@5/nDCG@5, primary/supporting variants, repository/category/difficulty/partition/task strata, fixed denominators, failures, and limitations. Report repository macro recall and handle zero supporting denominators as N/A. Retain full rankings, scores, traces, mappings, rejection reasons, and run manifest in controlled storage. Two fresh-process runs must match ordered parent rankings and metric artifacts; trace-score tolerance must be preregistered.

**Success interpretation:** There is no minimum retrieval score for benchmark acceptance. Low recall is a valid result, not grounds to remove difficult cases or alter labels. System promotion, regression, latency, memory, or answer-quality thresholds require separate numeric preapproval; retrieval recall alone proves none of those properties.

**Fail/hold:** Missing G5 approval, leakage, incomplete primary eligibility, metric mismatch, gold-dependent tuning, unrecorded configuration drift, or unexplained repeatability differences blocks the run/result. Leakage retires the exposed partition's blind claim. Remediate under a separately approved version and rerun only with proper authorization.

**Accountable decision:** Evaluation custodian and experiment owner. Current disposition: **not authorized**.

## 5. Release freeze gate — G4 freeze and G6 release

**Purpose:** Prevent an evaluation from mutating labels and distinguish an immutable benchmark freeze from permission to distribute or claim a released benchmark.

### G4 — pre-evaluation benchmark freeze

G4 requires G0–G3 approvals, completed approved allocation, final independent review, all annotation/evidence/structural thresholds, locked split/exposure and metric plan, and verified preservation of pilot/prior artifacts. Freeze a separately versioned package with digests for the canonical benchmark and category map, snapshots/inventories, annotation ledger, review records, split/exposure manifest, protocol/schema/rubric/tool versions, approvals, and timestamp. Verify retained bytes against digests and retain the prior version. A tool's `frozen` flag or review digest alone is not evidence of correctness or clearance.

**Pass:** All required records and hashes validate, exact version is immutable, and benchmark owner approves the freeze. Freeze occurs before retrieval evaluation. G4 does not authorize a retrieval run or release.

### G6 — release authorization

G6 additionally requires accepted G5 evidence when evaluation is in scope, complete limitations and residual-failure reporting, explicit distribution permissions and audience, approved artifact manifest, data-steward review, and tested rollback/withdrawal readiness. Raw questions, labels, paths/spans, inventories, and source-derived records remain restricted unless separately cleared for distribution. Publish only the explicitly approved artifact set.

**Pass:** Benchmark owner and data steward sign the named version, audience, and artifact list; all digests and rights/handling evidence verify; rollback owner and procedure are recorded.

**Fail/hold:** Any changed digest, missing approval, unresolved quality/clearance issue, unauthorized distribution, incomplete rollback readiness, or disagreement between frozen and released artifacts blocks freeze/release as applicable. After release, withdraw the affected version, invalidate dependent results, preserve permitted audit evidence, and restore a prior version only if its integrity and clearance remain valid. Never overwrite or silently repair a release or the Humanize pilot; corrections require a new version and renewed affected gates.

**Accountable decision:** Benchmark owner for G4; benchmark owner and data steward for G6. Current disposition: **no freeze or release authorized**.

## Current disposition

All gates remain pending. This is a criteria document, not evidence of passing any gate. No expansion has been executed; the candidate registry is a record of the already frozen candidate scope only. Humanize pilot remains frozen and full benchmark expansion remains blocked pending explicit decisions and clearances.
