# Phase 8.5 — Annotation Pilot Plan

**Status:** **PLANNED — NOT STARTED; blocked by repository-specific privacy clearance**

**Pilot size:** 12 real, manually authored questions in one repository

**Purpose:** Refine and verify the annotation procedure only; not a retrieval experiment.

## Scope and repository

The proposed pilot uses the small-stratum repository `python-humanize/humanize`, pinned to `392aef707c0e74341ab4a51420984e9ea6b566c5`. The committed aggregate checkout report records 13 eligible Python files and 126 deterministic chunks for this snapshot, making it a bounded single-repository candidate. These counts are planning evidence only; they do **not** prove privacy clearance or authorize generating/using a chunk inventory.

The pilot is conditional on the repository-specific approval criteria in [privacy-clearance-report.md](privacy-clearance-report.md). Until written clearance is recorded for this exact SHA, do not inspect source for annotation, create/consume its inventory, or populate pilot annotations. If it cannot be cleared, stop and select a replacement only through a documented, versioned protocol decision; do not silently switch repositories.

This pilot is deliberately separate from the final 108-question benchmark. The 12 pilot cases are expected to expose workflow/instruction changes and therefore **will not be reused in the final benchmark**. A later final set must be independently authored after the protocol is fixed. The pilot is not counted toward the 108-question target and must never be represented as frozen benchmark data.

No query text, chunk ID, source span, label, or benchmark entry is created by this plan. The allocation below is a plan, not authored data.

## Planned allocation

After clearance, author 12 real questions from static evidence at the pinned snapshot: three in each category.

| Category | Planned pilot questions | Annotation emphasis |
|---|---:|---|
| `architecture_understanding` | 3 | A static component/workflow relationship supported by code or configuration |
| `code_navigation` | 3 | Locate implementation of a behavior; identifier disclosure only when lookup is the task |
| `dependency_understanding` | 3 | Trace a caller/callee or cross-file path and label every necessary hop |
| `bug_investigation` | 3 | Describe a source-grounded failure possibility or guard, not an untested runtime defect |
| **Total** | **12** | |

Mix conceptual and identifier-heavy wording, single-file and cross-file evidence, and straightforward and challenging questions. Questions must be answerable from eligible Python evidence in the pinned commit. Do not use retriever output or unreviewed model output to select questions or labels.

## Evidence mapping record

Keep the pilot ledger and artifacts in a dedicated external location, for example `C:\Apps\Temp\Phase8\benchmark\pilot\python-humanize\`. Do not add them to Git. For each real pilot case, map:

| Record element | Required evidence |
|---|---|
| Identity | A pilot-local case reference, canonical repository ID, exact full commit SHA, and one declared category. Pilot references remain separate from final benchmark IDs. |
| Question | Manually authored, concise, trimmed, one-line developer language; answerable from static evidence at the pinned commit. |
| Source evidence | Repository-relative POSIX path, symbol, and one-based inclusive line span for each evidence item, verified against the pinned checkout. |
| Chunk evidence | Exact deterministic chunk ID from the inventory for the same repository and SHA; retain every necessary cross-file/dependency hop. Never alter chunk boundaries or IDs. |
| Relevance | Integer `2` for direct primary evidence and `1` for necessary supporting evidence. Each question has at least one gold chunk; no other values are valid. |
| Rationale and ambiguity | Explain how the selected evidence supports the answer and record ambiguity or an explicit no-unresolved-ambiguity disposition. |
| Review record | Independent labels, disagreement/adjudication outcome, reviewer reference, and pilot exclusion rationale; held externally. |

Choose the smallest complete evidence set; do not label merely related chunks. Do not quote source into committed documentation or routine logs. Keep case text, file paths/spans, IDs, and detailed review material external and access-controlled.

## Execution sequence — only after clearance

1. **Freeze pilot protocol.** Record the pilot objective, the one-repository SHA, category allocation, exclusion-from-final policy, evidence rules, held-out protections for later work, review sample, storage path, and responsible reviewer/approver before authoring.
2. **Verify the approved snapshot and inventory.** Keep the checkout read-only and verify its full SHA. Only after privacy clearance, build or verify the deterministic eligible chunk inventory using the already approved preprocessing pipeline. Retain inventory and provenance externally. Do not embed or retrieve.
3. **Author 12 questions manually.** Fill the category quotas from the source, not search/ranking results. Maintain the authoring ledger separately from any system outputs.
4. **Map evidence.** Verify each source span and corresponding chunk ID against the same pinned snapshot. Include all necessary hops; assign `2`/`1` by the declared policy; record rationale and ambiguity.
5. **Review independently.** Predeclare review of at least 20%; for 12 cases, review at least 3 cases (25%) when a second reviewer is available. The reviewer labels independently before comparison. Adjudicate disagreements. If no second reviewer is available, record the single-annotator limitation and do not claim inter-rater agreement.
6. **Validate structure and provenance.** Use the Phase 8.4 `validate_annotation_entry()` checks for required fields, grades, spans, and query form; supply the exact pilot inventory to check chunk IDs. Then create a clearly labeled, external pilot-only schema-1.0 validation projection from the completed cases, load it with `BenchmarkLoader`, and run `BenchmarkValidator` against the exact pilot inventory and `{repository_id: commit_sha}` snapshot map. Separately check the ledger's 3-per-category balance and the 12-case total; the generic validator does not enforce category quotas.
7. **Resolve and document.** Resolve every structural, snapshot, inventory, or review issue before declaring the pilot procedure complete. Record protocol changes and exclusions. The pilot projection and ledger remain pilot artifacts; do not pass them to retrieval evaluation or `BenchmarkFreezeUtility` as the final benchmark.

## Pilot acceptance and stop conditions

The annotation-process pilot is complete only when it contains 12 real manually authored questions (three per category), each has complete evidence/rationale/ambiguity records, every reference matches the exact snapshot inventory, the predeclared review disposition is documented, and validation has zero unresolved issues. Completion demonstrates only that the annotation workflow was exercised on one cleared repository; it does not establish readiness of the other repositories or the full benchmark.

Stop without authoring if privacy clearance is absent, scanner findings remain undispositioned, review/history coverage is unresolved, the intended snapshot differs, an inventory cannot be reconciled, or a file's processing permission is unclear. Exclude rather than guess. If any pilot case influences annotation instructions or later tuning, retain the pilot exclusion; do not move it into the final benchmark.

## Explicit non-goals

- No pilot execution, source reading, inventory generation, indexing, embedding, retrieval, metrics, tuning, or experiment is performed by this plan.
- No scanner, parser, chunker, embedding, FAISS, BM25, RRF, or evaluation-metric implementation is changed.
- No synthetic, placeholder, fabricated, or model-generated benchmark entries are created.
- No pilot is frozen or counted among the final 108 questions.

See the [benchmark annotation workflow](benchmark-annotation-workflow.md), [annotation guide](benchmark-annotation-guide.md), [benchmark validation protocol](benchmark-validation.md), and [finalization protocol](benchmark-finalization.md).