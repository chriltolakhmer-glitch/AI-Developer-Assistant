# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18.4 — Benchmark Expansion Readiness Checklist

**Date:** 2026-09-27  
**Workflow:** [Simplified research workflow](benchmark-research-workflow-final.md)  
**Execution status:** **NOT STARTED.** This checklist records preparation status; it grants no permission to process a repository, create questions, evaluate retrieval, or release data. Humanize remains frozen.

`[x]` means documented preparation or historical evidence exists. It does not mean a candidate is cleared or a future expansion gate has passed. `[ ]` means the expansion requirement remains future work. Record evidence references next to the relevant item; keep sensitive findings and source-derived artifacts in approved controlled storage.

## Repository readiness

- [x] Repository selected — existing Phase 9 candidate set is recorded; no repository added by Phase 18.4. See [frozen corpus selection](corpus-final-selection.md) and [candidate registry](benchmark-candidate-registry.md).
- [x] Exact commit recorded — full pinned SHAs are recorded in the Phase 9 selection and [candidate clearance matrix](benchmark-candidate-clearance-matrix.md); identity records are not privacy clearance.
- [ ] License verified for the intended activity — root-license screening exists, but candidate-specific file-notice/permission review and approval are incomplete. See [repository approval status](repository-approval-status-report.md).
- [ ] Privacy review completed for each proposed candidate — basic sensitive-file/history review and required dispositions remain incomplete; unresolved scan/history items remain documented. No candidate is cleared for expansion annotation/evaluation.

## Annotation readiness

- [ ] Questions created for expansion — no new benchmark questions may be created until the selected repository's approval and annotation conditions are satisfied.
- [ ] Evidence mapped — no expansion evidence mappings exist. Future mappings must resolve to the exact approved snapshot and include every necessary hop.
- [ ] Review completed — no expansion questions have independent review. Require a second human reviewer for every included question under the simplified thesis-quality workflow.
- [ ] Corrections resolved — no expansion corrections exist; future changes must preserve review history and be re-reviewed.

## Evaluation readiness

- [ ] Retrieval baseline measured for the expansion benchmark — Humanize's historical baseline and subsequent pilot runs are preserved as pilot-only results, not expansion measurements.
- [ ] Retrieval improvements tested on the declared expansion set — no expansion evaluation has run; do not modify retrieval code under this documentation phase.
- [ ] Regression checked — no expansion primary/supporting regression comparison exists. Future reporting must retain fixed denominators and distinguish primary from supporting evidence.

## Freeze readiness

- [ ] Dataset snapshot created for expansion — no new benchmark snapshot exists.
- [ ] Artifacts archived with verified digests — no expansion artifact package exists. Preserve prior versions and keep source-derived materials in approved controlled storage.
- [ ] Final documentation complete — Phase 18.4 workflow/checklist are prepared; future expansion-specific evidence and final results documentation remain pending.

## Historical evidence retained (not expansion completion)

- Humanize pilot: 12 existing cases were accepted after correction and the pilot remains frozen for pilot use. See the [pilot readiness decision](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md), [closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md), and [pilot analysis](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-analysis.md).
- Historical Humanize retrieval results, test/repeatability reports, and known limits remain traceable in that closure report and its linked reports. They are not an independent multi-repository evaluation and are not repeated or reclassified here.
- Repository approval evidence and known open findings remain in the [repository approval status report](repository-approval-status-report.md), [thesis scope risk acceptance](repository-approval-thesis-risk-acceptance.md), [Phase 9 selection](corpus-final-selection.md), and [candidate clearance matrix](benchmark-candidate-clearance-matrix.md). The thesis-level risk acceptance is not repository-specific clearance.

## Final status

- **Humanize Pilot:** **COMPLETE** — the existing bounded pilot is complete and remains **FROZEN**. No pilot question, annotation, answer, chunk map, or freeze digest is changed.
- **Research Workflow:** **SIMPLIFIED** — four gates replace the duplicated G0–G6/board workflow for future thesis work.
- **Expansion:** **READY FOR CONTROLLED PREPARATION** — the simplified procedure and checklist are ready to guide preparation. Repository approval remains a prerequisite before any repository-specific processing; this status does not say expansion annotation is cleared.
- **Execution:** **NOT STARTED** — no new repositories, questions, expansion retrieval runs, or dataset freeze have been created.

**Fail-closed reminder:** where License or Privacy boxes are unchecked, do not proceed with the affected repository. Humanize's limited pilot status does not grant expansion approval. No Phase 19 execution is authorized by this checklist.
