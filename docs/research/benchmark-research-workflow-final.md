# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18.4 — Benchmark Research Workflow (Simplified)

**Date:** 2026-09-27  
**Status:** Current lightweight workflow proposal for controlled thesis preparation.  
**Execution:** **NOT STARTED.** No new repository work or benchmark questions are authorized by this document.  
**Protected state:** Humanize pilot remains frozen and unchanged.

## Purpose and supersession

This document replaces the enterprise-style G0–G6 approval chain as the **working thesis workflow** with four proportionate, evidence-based gates. It supersedes the operational gate sequence in the [Phase 17 protocol](benchmark-expansion-protocol.md), the [Phase 18.2 finalization proposal](benchmark-expansion-protocol-finalization.md), and the G0/board/dashboard structure in the [Phase 18.2 authorization record](benchmark-expansion-g0-authorization.md), [Phase 18.3 governance review](benchmark-governance-review.md), [Phase 18.3 dashboard](benchmark-gate-status-dashboard.md), and [Phase 18.2 release gate](benchmark-release-gate.md). Those documents remain historical evidence and must not be deleted or rewritten as if their prior decisions never occurred.

Simplification removes duplicate boards, sign-off layers, and role matrices; it does **not** waive repository-specific permission, source provenance, human evidence review, reproducibility, fixed metrics, or safe handling. The [Phase 18 candidate registry](benchmark-candidate-registry.md), [candidate clearance matrix](benchmark-candidate-clearance-matrix.md), [quality-gates document](benchmark-quality-gates.md), [annotation procedure](benchmark-annotation-operating-procedure.md), and [independence plan](benchmark-independence-plan.md) remain useful evidence/checklists subject to this simpler sequence.

## Four-gate workflow

### Gate 1 — Repository approval

Before using a repository for new benchmark work, record:

- canonical repository identity and exact full commit SHA from the existing frozen candidate set;
- applicable license and file-level notice check for the intended thesis activity;
- basic privacy/sensitive-file review, including the disposition of known scanner/history findings and exclusions;
- a clear approval status and permitted activity for that exact snapshot.

**Pass rule:** only repositories with documented approval for the specific next activity may proceed. If a privacy/sensitive-file finding, license condition, identity mismatch, or handling issue is unresolved, stop for that repository. Approval to inspect or prepare a snapshot does not automatically permit annotation, external processing, retrieval experiments, or redistribution. Do not add or substitute repositories under this workflow.

**Current status:** no candidate is documented as cleared for expansion annotation/evaluation. The existing Phase 9 list is selected and pinned, but candidate-specific approval evidence remains open. Humanize is not eligible for expansion work: its pilot is complete and frozen, and full expansion clearance is not granted.

### Gate 2 — Annotation review

Only after Gate 1 approval for the exact source activity:

- create questions manually from the pinned, permitted static source;
- confirm question clarity, answerability, category/difficulty, and absence of unsupported runtime claims;
- verify evidence IDs, files, symbols, spans, primary grade-2 evidence, and all necessary grade-1 supporting hops against the same snapshot;
- obtain independent human review of every proposed case, preserving the initial independent judgment before comparison;
- resolve corrections, disagreements, and ambiguity before locking labels.

**Thesis-quality controls retained:** every included question receives independent human review; all included cases are finally accepted; exact graded-evidence agreement is at least 80% overall and per repository, using unrounded ratios; unresolved disputes or evidence defects block the set. Keep corrections and rejected/deferred cases traceable. Never use retrieval output to select or revise ground truth. No LLM-generated or LLM-verified ground truth.

**Decision:** after review, record an annotation freeze decision for the exact question/evidence version before evaluation. This is a lock on reviewed labels, not permission to run retrieval or distribute data.

### Gate 3 — Retrieval evaluation

Only after the reviewed annotation set is locked and evaluation use is separately permitted:

- measure the declared baseline on the same eligible candidate universe as the comparison system;
- compare baseline and proposed retrieval configurations using fixed cases and denominators;
- report evidence-occurrence micro Recall@5 and mean per-question Recall@5 separately, with primary/supporting variants and complete-evidence success; report other metrics only if evaluator compatibility is verified;
- retain all cases, failures, eligibility/exclusion counts, per-repository/category/difficulty breakdowns, and the run configuration/provenance;
- check regressions in primary and supporting evidence separately and perform two fresh-process repeatability runs with ranking/metric agreement and a predeclared trace-score tolerance.

No minimum recall score makes a benchmark valid or invalid. Do not remove difficult cases, tune labels to a score, or present the Humanize pilot's retrieval results as independent expansion evidence. Retrieval implementation remains unchanged by this workflow phase.

### Gate 4 — Dataset freeze and release decision

After annotation review and any authorized evaluation:

- retain the final dataset snapshot, annotation/review record, category mapping, repository/SHA and inventory references, evaluation manifest/results where authorized, and reproducibility record with verifiable digests;
- confirm the Humanize pilot and earlier benchmark artifacts remain byte-for-byte unchanged;
- archive controlled source-derived artifacts in the approved local location; commit only permitted non-sensitive documentation and aggregate results;
- record a final decision: internal thesis use only, restricted archive, or release to a named audience. Release only artifacts whose license/privacy terms permit that exact distribution. No raw question/gold/source-derived artifacts are public by default.

A changed question, label, snapshot, or metric contract creates a new version and requires the affected review/evaluation checks again. Preserve earlier snapshots and results; do not overwrite the frozen pilot.

## Simplified records and ownership

No standing approval board or enterprise ownership matrix is required. For each gate, record a short dated decision note with: repository/version or dataset identity, evidence links/digests, reviewer(s), outcome (`PASS`, `HOLD`, or `REVISE`), conditions, and the next permitted activity. The thesis researcher maintains the research log; a second human reviewer remains necessary for independent annotation review. The responsible repository/privacy or license approver must be identifiable for any external or otherwise restricted permission decision. A missing decision-maker or missing evidence is a **HOLD**, not implied approval.

## Existing evidence preserved

- The frozen candidate set, pinned SHAs, language/size screening, and prior preprocessing evidence remain in [Phase 9 corpus selection](corpus-final-selection.md), [dataset snapshot freeze](dataset-snapshot-freeze.md), and the [repository approval status report](repository-approval-status-report.md). The status report states the eight non-Humanize repositories remain blocked for annotation and Humanize's scope is limited to its pilot.
- Humanize pilot history remains in the Phase 16 [readiness decision](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md), [closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md), and the pilot's analysis. It records 12 accepted cases, pilot-only freeze, and historical retrieval results, including 19/20 evidence occurrences at Recall@5 and one primary miss. These are pilot-only results, not expansion results or a generalization claim.
- Existing Phase 17/18 quality thresholds, direct source-hop checks, fixed denominators, primary/supporting distinctions, reproducibility, and pilot preservation remain; duplicate approval layers are removed.

## Current phase status

- **Humanize Pilot:** **COMPLETE** as the bounded, reviewed pilot; **FROZEN** for pilot use. This does not assert full repository clearance or authorize new Humanize work.
- **Research Workflow:** **SIMPLIFIED** to the four gates above.
- **Expansion:** **READY FOR CONTROLLED PREPARATION** means the documentation/workflow is ready to guide the next preparation activities. It does not mean candidate clearance, annotation readiness, or evaluation approval.
- **Execution:** **NOT STARTED.** No new questions, repositories, expansion retrieval runs, or freeze artifacts were created by Phase 18.4.

Before any source inspection or data-derived work, check the relevant repository's approval evidence and local handling conditions. The existing record says all non-Humanize candidate annotation is not authorized; that remains fail-closed until its required approval evidence is recorded. No Phase 19 execution is authorized by this document.
