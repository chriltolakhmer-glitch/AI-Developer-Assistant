# Phase 8.3 — Benchmark Annotation Guide

**Scope:** Manual authoring and ground-truth labeling for the planned 108-query retrieval benchmark. This guide does not authorize source inspection or indexing while the corpus privacy gate is open.

## Before annotation

1. Close and document the secret/credential and personal/confidential-data reviews for the proposed snapshots. Disposition all candidate findings and address the incomplete history scan recorded in [dataset-snapshot-freeze.md](dataset-snapshot-freeze.md). Do not read repository source or generate/consume its chunk inventory before this prerequisite is satisfied.
2. Use only the nine exact repository/commit pairs from the snapshot freeze. The branch name is not the snapshot identity. Keep checkouts read-only and local.
3. Predeclare the held-out unit and split, pilot exclusions, and independent review sample before authoring final cases. Do not use retrieval output to choose questions or evidence.
4. Store working annotations, source paths/spans, chunk inventories, query text, and review evidence under `C:\Apps\Temp\Phase8\benchmark` or another approved external, access-controlled research-data location. Do not commit these source-derived artifacts.

The generated `annotation-template.json` is only a blank authoring scaffold: its 108 rows are **slots**, not authored questions, and it cannot be loaded or validated as the final benchmark until completed.

## Question categories and quota

Create 12 cases per repository: three in each category below. The category is recorded in the external annotation ledger and supplied separately to the freeze utility because retrieval schema 1.0 does not carry a category field.

| Category | Count per repository | Total target | What the question asks |
|---|---:|---:|---|
| `architecture_understanding` | 3 | 27 | Explain a component boundary, static workflow, or architectural relationship supported by code/config. |
| `code_navigation` | 3 | 27 | Locate the implementation of a behavior; one identifier-heavy lookup may disclose its target identifier. |
| `dependency_understanding` | 3 | 27 | Trace a static caller/callee or cross-file dependency; every required hop must be labeled. |
| `bug_investigation` | 3 | 27 | Identify a source-based failure possibility, guard, or condition without asserting an untested runtime defect. |
| **Total** | **12** | **108** | |

Balance natural conceptual wording and identifier-heavy wording, single-file and multi-file evidence, and straightforward and challenging cases. Questions must be answerable from static evidence in the pinned snapshot; exclude external runtime facts unless represented in the checked-in code/config. Avoid wording that gives away a file or symbol except when identifier lookup is the intended task.

## Case fields and authoring record

Every slot must be completed with:

- `query_id`: `<repository-slug>-NNN`, unique across the benchmark.
- `repository_id`: canonical owner/repository identity.
- `commit_sha`: exact full frozen commit SHA.
- `category`: one of the four categories above.
- `query`: concise, grammatical, natural developer language; trimmed and one line in the final payload.
- `relevance`: a non-empty mapping from exact deterministic chunk ID to integer grade (`2` primary, `1` supporting).
- `expected_files`, `expected_spans`, `annotation_rationale`, and `ambiguity_notes` in the external ledger. Spans use repository-relative POSIX paths and one-based inclusive line bounds at the pinned commit.

Keep the question and gold labels separate from retriever outputs. Do not use an LLM to generate or verify ground truth. Manual annotation reads the source only after the privacy prerequisite has passed.

## Evidence selection rules

1. Select the smallest set of chunks that fully supports a correct answer, while retaining every necessary cross-file/dependency hop. Do not add chunks solely because they are semantically related.
2. Choose exact deterministic chunk IDs from the same repository and commit as the case. A relevant ID must exist in the pinned chunk inventory and must not refer to another snapshot.
3. Record the source file, symbol, and exact inclusive line span for every gold item. Confirm the span against the immutable source; for chunk IDs, confirm provenance against the inventory. Chunk boundaries and IDs are upstream-owned and must not be altered to make a label fit.
4. Use grade 2 for the central evidence that directly answers the question. Use grade 1 only for necessary supporting context (for example, a caller or configuration entry needed to understand the primary implementation). Assign one grade per chunk ID and do not duplicate an ID.
5. For multi-hop questions, annotate all needed hops. A query with only one of several necessary evidence chunks is incomplete even if that chunk is primary.
6. If multiple implementations plausibly answer the query, either clarify the question without disclosing its answer or enumerate valid evidence and explain the ambiguity. Do not silently choose one path.
7. For bug-investigation items, phrase claims as source-level possibilities and label the code conditions that support them; do not claim runtime reproduction unless separately established and in scope.
8. Do not label test fixtures, generated files, or out-of-scope languages unless the question intentionally evaluates eligible Python source and the protocol explicitly includes that evidence.

## Relevance grade mapping

| Ledger label | Final integer | Operational definition |
|---|---:|---|
| `primary` | **2** | Direct implementation/evidence that answers the core question. |
| `supporting` | **1** | Necessary context or an additional required hop, but not the core answer alone. |

No other grades are valid; `bool` values are not integer grades for this purpose. Every query must have at least one gold chunk. This fixed mapping is used by graded nDCG. Any protocol change requires an explicit versioned decision before evaluation.

## Review and completion criteria

- Author labels by inspecting the pinned source manually, not retriever results or unreviewed generated content.
- Predeclare an independent second-review sample targeting at least 20% of the cases where a second reviewer is available. Review independently before comparing, adjudicate disagreements, and retain the redacted process record externally. If unavailable, document the single-annotator limitation and do not report inter-rater agreement.
- Exclude pilot queries that influenced annotation instructions or retrieval/fusion tuning from the final evaluation set.
- A case counts as annotated only when query, category, snapshot, non-empty graded gold IDs, rationale, ambiguity disposition, and file/span evidence are present. A completed annotation is not chunk-validated until checked against the matching frozen inventory.
- Use `benchmark_statistics` for aggregate progress and `BenchmarkValidator` for final structural/snapshot/chunk checks. Require 108/108 complete cases, nine repositories at 12 each, exactly three per category per repository, zero unresolved validation issues, and a closed privacy gate before calling the real benchmark ready or frozen.
- Freeze the canonical benchmark only after review and validation; retain its digests outside Git. The committed freeze report may contain aggregate counts/digests only and must never claim a hash for a missing artifact.

See [benchmark-finalization.md](benchmark-finalization.md), [benchmark-validation.md](benchmark-validation.md), and [benchmark-freeze-report.md](benchmark-freeze-report.md).