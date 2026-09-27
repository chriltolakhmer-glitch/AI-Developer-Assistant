# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 17 — Benchmark Expansion Protocol Design

**Date:** 2026-09-27  
**Status:** Proposed protocol; documentation only. Expansion execution remains BLOCKED.  
**Companion:** [Benchmark expansion checklist](benchmark-expansion-checklist.md).

## Objectives

Define a controlled, auditable path from the frozen Humanize pilot to a separately versioned multi-repository benchmark. Establish source-grounded annotation, independent review, reproducible evaluation, and explicit decisions before each future activity.

Phase 17 creates no repositories, questions, annotations, inventories, indexes, experiments, or freeze artifacts and changes no retrieval or validation code. Humanize remains frozen for pilot use only; the current benchmark remains unchanged. Approval of this design alone does not authorize expansion.

The external [Phase 16 readiness decision](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md) and [closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md) are the starting evidence. They report 12 accepted pilot cases and 19/20 evidence occurrences retrieved at five, but no independent validation. Those are historical diagnostics, not expansion acceptance thresholds or results of this phase.

## Repository selection criteria

Selection is a future gate, not an activity performed here. Assess only the existing approved candidate scope in [corpus final selection](corpus-final-selection.md) and [snapshot freeze](dataset-snapshot-freeze.md); this protocol nominates or adds no repository.

| Criterion | Required decision evidence |
|---|---|
| Immutable provenance | Canonical repository identity, full pinned commit SHA, snapshot digest, source origin, and reproducible eligible-file inventory. Mutable branches/tags are insufficient. |
| Scope compatibility | Eligible Python static evidence under the existing pipeline, explicit excluded/generated/vendor/test-file policy, and known parser/chunker limitations. |
| Diversity | Predeclared small/medium/large allocation, application/library roles, component structure, dependency patterns, and single-file/cross-file coverage. Record the limits of a Python-only sample. |
| Feasibility | Source availability, inventory size, long-chunk distribution, processing budget, annotation effort, and named reviewers. Do not select on favorable retrieval scores. |
| Evidence suitability | Sufficient statically verifiable evidence for all four categories without runtime speculation or reliance on external services. |
| Independence | Exposure register for prior source inspection, question authoring, tuning, and related forks/near-duplicates. Keep related snapshots in the same partition. |
| Clearance | Repository-specific privacy, license/notice, storage, processing, and transmission decisions, with unresolved findings explicitly blocking approval. |

The existing design target remains nine repositories, 12 cases each, three per category (108 total). It is a historical target, not a new authorization or proof of readiness. Humanize pilot cases cannot fill final benchmark slots. Any future Humanize cases belong to an exposed/development stratum and cannot support unseen-repository claims. If that prevents the intended independent allocation, stop at G0 and obtain a versioned scope decision; do not silently replace repositories, alter counts, or reuse pilot questions.

## Approval gates

All gates below are **pending future execution**. Each decision record must include protocol version, scope and artifact digests, evidence location, named accountable approver, date, outcome (`APPROVE`, `REVISE`, or `REJECT`), conditions, and the exact activity authorized. Missing evidence means the gate stays closed. A changed scope or digest invalidates affected downstream approvals.

| Gate | Required evidence and accountable decision | Activity permitted after approval |
|---|---|---|
| G0 — Protocol and scope | Benchmark owner approves allocation, taxonomy/schema mapping, independent split, exposure policy, reviewer assignments, thresholds, budget, storage, and validation-tooling plan. Separate explicit authorization to begin the bounded next phase is recorded. | Repository approval preparation within the declared scope only. |
| G1 — Repository clearance | Data/privacy steward and license reviewer document repository-specific clearance; benchmark owner approves the exact repository/commit and processing scope. Clearance inspections follow their own authorized handling process. | Approved local snapshot/inventory preparation and verification; no annotation yet. |
| G2 — Annotation readiness | Annotation lead and evaluation custodian approve validated inventory, split/access controls, frozen rubric, workload, independent review coverage, and case/ID allocation. | Manual annotation in an isolated, versioned staging area. |
| G3 — Review and validation | Independent review lead signs all dispositions and agreement report; validation owner records zero unresolved structural/provenance issues and synchronized exports. | Preparation of a candidate freeze package. |
| G4 — Benchmark freeze | Benchmark owner verifies all freeze criteria and immutable metadata, with independent review sign-off. | Versioned benchmark freeze only; no experiment permission implied. |
| G5 — Retrieval evaluation | Evaluation custodian and experiment owner approve the sealed run plan, frozen benchmark identity, systems/configurations, candidate universe, metric contract, compute/handling approval, and repeatability checks. | Only the predeclared evaluation runs; holdout labels remain custodian-controlled. |
| G6 — Release | Benchmark owner and data steward accept validation/evaluation reports, limitations, distribution permissions, manifest, and rollback readiness. | Release of the explicitly approved artifact set to the approved audience. |

Roles may be combined for administration, but an author cannot act as the independent reviewer of their own cases. A fresh model session is not a second human reviewer. No reviewer availability means G2/G3 remain blocked under this proposed protocol. This strengthens the earlier optional 20% review sample and requires G0 acceptance; it does not retroactively alter the pilot review.

## Privacy/licensing requirements

These are proposed process requirements, not a legal clearance determination. Record source-use, copying, derived-artifact, internal experiment, external-review, and redistribution permissions separately. Public availability or a top-level license alone does not complete this gate.

- Retain the applicable license version, attribution/notice obligations, file-specific exceptions, dependency/vendor treatment, and permitted audiences. Unclear rights require the responsible reviewer to resolve them before processing.
- Disposition secret-scanner findings and personal/confidential-data findings without copying sensitive findings into public reports. Resolve incomplete history scans or obtain an explicit, justified alternative-scope decision. Earlier corpus records contain open findings; this protocol does not close them.
- Approve local storage location, authorized readers, access controls, retention/deletion schedule, incident owner, and backup handling. Keep source-derived questions, gold labels, paths, spans, inventories, and review records outside Git in the approved research-data area.
- Approve any external model/service transmission or external reviewer access separately before it occurs. Manual human annotation remains the policy; do not use an LLM to generate or verify ground truth.
- Publish only approved aggregate metadata and digests by default. Raw benchmark/source distribution requires a separate rights and disclosure decision at G6.
- Quarantine unresolved material. If exclusion changes a snapshot or evidence inventory, require a new version and renewed approval; never sanitize a frozen artifact in place.

## Annotation workflow

1. After G2, create a separate staging version with pinned snapshot, inventory, schema, rubric, and split identities. Preserve all Humanize pilot artifacts and digests. Predeclare case allocation, category quotas, difficulty distribution, and deterministic sampling/order; record exclusions before retrieval is observed.
2. Follow [benchmark schema](benchmark-schema.md) and [annotation guide](benchmark-annotation-guide.md). Use the existing four categories: `architecture_understanding`, `code_navigation`, `dependency_understanding`, and `bug_investigation`. Map any legacy names explicitly; do not introduce aliases silently.
3. Author manually from eligible pinned source, independent of rankings. Record unique query ID, repository/full commit SHA, question, category, difficulty, exact files/symbols/inclusive spans, canonical chunk IDs, grades, rationale, ambiguity disposition, author, date, and exposure history.
4. Label grade 2 as primary and grade 1 as necessary supporting evidence. Require at least one primary item per case as an explicit manual Phase 17 quality rule, beyond the loader's nonempty-gold check. Verify every dependency at its actual call/import/reference site and include each necessary hop. Similar names or nearby helpers do not establish a dependency.
5. Resolve static ambiguity before review; do not assert an unverified runtime defect. Assign difficulty from reasoning burden before evaluation, using the existing easy/medium/hard rubric. Retain long or difficult evidence; do not simplify labels to accommodate input limits.
6. Send each case to independent review. Corrections include a reason, source evidence, old/new record identities, and renewed review. Keep rejected/deferred cases and exclusion reasons in the audit trail; replacements must follow the approved allocation and remain independent of retrieval performance.
7. Generate all derived exports from one canonical ledger. Schema 1.0 retrieval cases use `query_id`, `repository_id`, `commit_sha`, `query`, and `relevance`. Supply category separately to freeze tooling; difficulty, rationale, spans, and review metadata remain in the digested ledger. Do not assume the loader validates or hashes omitted fields.

ID collisions across repository slugs, schema changes, taxonomy changes, or altered target counts must be resolved through a versioned contract decision before annotation. Tooling work needed to support that decision is a separately authorized task; this phase implements none.

## Reviewer workflow

Every future case receives independent human source review before freeze. The reviewer records an initial evidence set, grades, category, difficulty, and ambiguity assessment before seeing the author's labels or retrieval output. Compare the two records only after both initial judgments are retained.

Use `ACCEPT`, `REVISE`, or `REJECT` with reason codes for unsupported claims, missing hops, span/ID errors, ambiguity, taxonomy/difficulty disagreements, privacy issues, or duplicates/leakage. Revised cases return for review; rejection is not permission to silently remove a hard case. An independent adjudicator resolves remaining disagreements using source evidence. If no qualified independent adjudicator is available for a disputed case, keep it blocked.

Report pre-adjudication exact evidence-set agreement, exact graded-evidence agreement, category agreement, and difficulty agreement as matched cases divided by double-reviewed cases, overall and per repository. Also retain disagreement counts and adjudicated outcomes. Do not present post-adjudication unanimity as initial inter-rater agreement. Do not invent an agreement statistic for the historical pilot.

## Retrieval evaluation protocol

### Separation and preregistration

At G0, assign repository-level development and blind evaluation partitions before new annotation/tuning. Keep all snapshots/forks with shared evidence together. Humanize and any repository already used for retrieval development are development/exposed data. Record exact repository assignments, counts, selection rule/seed, access list, and rationale in the controlled split manifest at G2. Without enough unexposed repositories for the declared claim, stop and revise the claim or seek a new scope decision.

The evaluation custodian holds blind queries and gold. Developers receive development data only; the custodian runs the locked system on blind queries. Exposure of queries, gold, or results for tuning ends that partition's blind status. Any subsequent tuning comparison needs a newly approved independent evaluation version; do not relabel exposed results as blind.

Before G5, pin code revision plus dirty-worktree digest if applicable, model/tokenizer revision, runtime/dependencies, seeds, hardware, schema, source/inventory hashes, representation rules, token budgets, aggregation, fusion/call-expansion settings, cutoffs, tie-breaking, and all metric formulas. No retrieval implementation or configuration changes occur in Phase 17.

### Candidate and ranking contract

Predeclare two separate tasks if both are desired: repository-scoped retrieval (known repository) and pooled multi-repository retrieval (distractors across approved repositories). Never combine their scores. Use the same declared canonical-parent universe for paired system comparisons; record inventory differences in separate diagnostics.

Verify eligibility before evaluation. Report eligible parents / all declared parents and eligible gold occurrences / all gold occurrences, including length-related exclusions. Require complete eligibility for the primary complete-inventory experiment. Historical restricted baselines can remain explicitly labeled diagnostics; their exclusions never shrink gold denominators.

Return distinct canonical parent IDs. Internal child passages and expanded dependencies map to immutable parents; duplicate children cannot occupy multiple ranking slots or multiply credit. Overlapping canonical chunks remain distinct gold identities. Freeze deterministic tie rules and retain full returned rankings, scores, channel ranks, parent-child mapping, rejection reasons, and expansion traces in controlled storage. No gold-dependent boosts, representation construction, or query-specific exception rules.

### Metrics and reporting

Use `k = 5` as the primary cutoff; other cutoffs must be declared before evaluation. Let `Gq` be a question's frozen gold parent set and `Rq(k)` its unique top-k returned parents.

- Evidence-occurrence micro Recall@k: `sum_q |Gq intersect Rq(k)| / sum_q |Gq|`. Compute overall, primary-only, and supporting-only variants with their own fixed denominators. The same chunk for different questions counts as separate occurrences.
- Mean per-question Recall@k: mean of `|Gq intersect Rq(k)| / |Gq|`. Report separately from micro recall.
- Complete-evidence success@k: fraction of questions for which all required gold parents are retrieved. Report gold-set sizes, including cases with more than k required items.
- MRR@k: mean reciprocal rank of the first grade-1-or-2 item within k, or zero when absent. nDCG@k: gains `2^grade - 1`, discount `log2(rank + 1)`, ideal ranking from the full frozen gold set truncated at k. Verify evaluator compatibility before execution; any mismatch blocks that metric until a separately approved resolution.
- Report each repository, category, difficulty, partition, and task separately, with counts, numerator/denominator, and failures; include equal-weight repository macro recall so large repositories do not dominate. Zero supporting denominators are `N/A`, never zero or perfect recall; state their exclusion from that macro average.
- Preserve all declared cases. Record failed queries as failures with zero retrieval credit; infrastructure failures invalidate the run and require an explained full rerun, never selective removal. Report uncertainty with a preregistered repository-clustered method when the repository count supports it; otherwise report descriptive ranges and explicitly limit inference.

Rebuild and evaluate in two fresh processes using the same pinned inputs. Compare ordered parent rankings and metric artifacts exactly; compare numeric trace scores under a tolerance declared before runs. Preserve volatile run metadata separately. Any unexplained difference blocks acceptance. Measure latency, memory, or answer quality only under separate predeclared procedures; retrieval recall does not establish them.

## Quality thresholds

These are proposed governance thresholds to approve at G0, not measured Phase 17 results.

| Measure | Required threshold / failure action |
|---|---|
| Repository clearance and provenance | 100% of included snapshots cleared and pinned; zero unresolved findings affecting authorized use. Otherwise stop G1. |
| Allocation and record completion | 100% of approved slots and required fields; exact declared repository/category counts. Existing final tooling requires 108 / 9 / 12 / 3. Incomplete batches are staging only. |
| Independent source review | 100% of included cases independently reviewed; 100% finally accepted; zero unresolved disputes, unsupported claims, or ambiguity affecting answerability. |
| Initial agreement calibration | At least 80% exact graded-evidence agreement overall and in every repository, using unrounded ratios. Below threshold: pause that batch, calibrate on development material, independently re-review all affected cases, retain both rounds, and repeat until the threshold is met. Category/difficulty disagreements must all be adjudicated. |
| Structural and evidence integrity | Zero validation errors, duplicate IDs, unresolved spans, missing/cross-snapshot IDs, orphan mappings, or mismatched derived exports; 100% gold provenance resolution. |
| Independence | Zero pilot cases or near-duplicate pilot questions in final evaluation; zero known development exposure in the claimed blind repository partition. |
| Complete-inventory experiment | 100% declared-parent and gold eligibility; zero silent truncations or dropped evidence. Otherwise block the primary run and report the coverage defect. |
| Reproducibility | Two fresh-process runs agree on all ordered results and metrics; trace-score tolerance fixed in advance; no unexplained difference. |
| Freeze preservation | Zero changes to protected pilot artifacts or prior benchmark versions; all expected hashes verified. |

There is no minimum retrieval score for accepting a well-formed benchmark: low recall is a valid finding. The pilot's 95% is not a generalization target. Any system-promotion target, tolerated regression, or resource budget must be numeric and approved at G5 before blind results are available; absent such a target, report measurements only and make no system-promotion decision. Do not reject questions or revise labels to meet a score threshold.

## Freeze criteria

G4 requires G0–G3 approvals, completed allocation, accepted independent review, all quality/integrity thresholds, and a locked split and metric plan. Freeze occurs before retrieval evaluation to avoid outcome-driven labels; G6 additionally requires valid evaluation evidence.

Preserve a separately versioned package with benchmark/category-map canonical digest, snapshot and inventory manifests/digests, annotation-ledger and review-record digests, split/exposure manifest digest, protocol/schema/rubric versions, validator/tool versions and outputs, approval references, and freeze timestamp. Verify the retained bytes against their digests and retain the prior version. A freeze-tool `frozen` flag or review digest alone is not evidence of human correctness or clearance.

The [existing finalization contract](benchmark-finalization.md) and [validation contract](benchmark-validation.md) remain unchanged. A changed allocation/schema requires a separately approved, tested tooling migration before a final freeze; never bypass final-target checks to freeze a partial batch.

The pilot validator's report-filename allowlist predates later reports. Keep expansion documents and staging data outside the pilot directory. At G0 record an exact artifact policy and, if tooling changes are needed, require separately authorized implementation and tests before G3. Supplemental validation must list its exact allowances and preserved checks; it cannot be described as an unmodified validator pass. Phase 17 edits no validator and makes no new validation-pass claim for the frozen pilot.

## Rollback criteria

Stop the affected stage on a clearance incident, provenance/hash mismatch, unauthorized scope change, unresolvable gold error, threshold failure, holdout leakage, nonreproducible evaluation, or incomplete release permissions. Low retrieval scores alone do not invalidate the benchmark.

The stage owner records the incident and affected artifacts; the benchmark owner suspends downstream approvals. Quarantine candidate artifacts and stop distribution/access where required by the data steward. Preserve permitted audit evidence and notify the recorded internal owners under the approved incident process. Do not copy sensitive findings into committed reports.

Before release, return to the earliest failed gate in isolated staging. After release, mark the affected release withdrawn, invalidate dependent results, and restore the last approved release reference only if its integrity and clearance still hold; otherwise publish no active replacement. Never overwrite or silently repair a released version or the Humanize pilot. Corrections require a new version, renewed review/validation/freeze, and fresh evaluation where relevant. Leakage requires retiring the independence claim for the exposed partition. Resume only after the accountable gate approvers sign the remediation evidence.

## Risks and mitigations

| Risk | Mitigation and owner |
|---|---|
| Pilot overfitting presented as generalization | Custodian excludes pilot cases, records repository exposure, and isolates a blind repository partition. |
| Plausible but unsupported dependency labels | Annotation lead requires direct source-hop verification and independent review of every case. |
| Long chunks excluded or supports lost | Experiment owner checks complete eligibility and reports primary/supporting recall separately with fixed denominators. |
| Selection/cherry-picking after results | Benchmark owner locks sampling, quotas, exclusions, and metric plans before evaluation; all failures remain visible. |
| Reviewer bottleneck or agreement overstated | Review lead budgets full review, preserves independent initial judgments, and blocks disputed cases without adjudication. |
| Source/model/schema drift | Validation owner pins versions/digests, verifies exports and manifests, and requires a new version for contract changes. |
| Rights/privacy breach | Data steward enforces repository clearance, restricted storage, transmission approvals, and withdrawal procedures. |
| Tooling gives false readiness | Validation owner distinguishes structural checks from source review, records allowlist caveats, and tests any future migration separately. |
| Multi-repository aggregate hides failures | Evaluation custodian reports strata, repository macro metrics, pooled versus scoped tasks, and limits small-sample claims. |
| Existing scope conflicts with independence/counts | Benchmark owner resolves allocation and exposure at G0; no silent target changes or pilot reuse. |

## Phase 17 disposition

This protocol and its checklist are design deliverables only. No gate is recorded as approved, no repository or question is added, no retrieval run occurs, and no release or re-freeze is performed. Humanize remains frozen; the current benchmark is unchanged; expansion execution remains blocked pending a separate decision.
