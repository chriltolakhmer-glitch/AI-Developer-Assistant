# Phase 10 — Benchmark Schema

**Status:** Schema and annotation-record design only. No final benchmark questions or source-derived labels are created by this document. The corpus privacy gate remains open; source inspection, chunk-inventory use for annotation, and benchmark authoring are blocked until repository-specific clearance is documented.

## Purpose and boundary

This document defines the logical record needed to create the planned retrieval benchmark and the compatible projection consumed by the existing evaluation code. It does not change the implementation's `schema_version: "1.0"` contract. The record separates human annotation metadata from the smaller retrieval input so categories, difficulty, source spans, and rationale are not silently lost or represented as fields the loader does not support.

All questions, chunk IDs, source locations, annotations, and detailed review materials are source-derived research data. Keep working records and evaluation datasets outside the thesis Git repository in the approved, access-controlled local research-data area. Commit only this non-sensitive schema/protocol documentation and approved aggregate status.

## Logical annotation record

One record represents one question against one immutable repository snapshot. Field names below use the existing annotation utility's names where available; `query` is the natural-language question.

| Field | Type | Requirement and meaning |
|---|---|---|
| `query_id` | string | Required and unique across the benchmark. Format `<repository-slug>-NNN`, where `NNN` is a three-digit sequence and the slug is the final component of `repository_id` (for example, the repository named `owner/project` uses `project-001`). |
| `repository_id` | string | Required canonical `owner/repository` identity, matching the frozen snapshot manifest exactly. Do not substitute a local folder name or mutable branch. |
| `commit_sha` | string | Required full 40-character hexadecimal commit SHA for the selected repository snapshot. It must match the frozen snapshot map exactly. |
| `query` | string | Required concise, natural, single-line developer question answerable from eligible static evidence at that commit. Avoid revealing the target symbol/path unless identifier lookup is the intended task. |
| `category` | enum | Required one of `architecture_understanding`, `code_navigation`, `dependency_understanding`, or `bug_investigation`. Use the existing category definitions in the annotation guide. |
| `difficulty` | enum | Required researcher-assigned `easy`, `medium`, or `hard`; operational criteria are defined below. Assign before retrieval results are available. |
| `expected_evidence_chunks` | list of objects | Required, nonempty gold set. Each item identifies an exact deterministic `chunk_id` from the matching repository-and-commit inventory and a `relevance_grade`. Include the smallest complete evidence set, including every required hop. |
| `annotation_rationale` | string | Required in the private annotation ledger; explains why the evidence answers the question and why each supporting item is necessary. |
| `ambiguity_notes` | string | Required in the private annotation ledger; describe unresolved ambiguity or explicitly record that none remains. |
| `expected_files` | list of repository-relative paths | Required in the private annotation ledger; POSIX paths identifying files that contain the gold evidence. |
| `expected_spans` | list of objects | Required in the private annotation ledger; each item records `file`, `symbol`, and one-based inclusive `lines` at the pinned commit. |

The existing authoring utility calls `expected_evidence_chunks` `relevance`: a nonempty mapping from exact chunk IDs to integer grades. It calls the question `query`. The ledger's `expected_files`, `expected_spans`, `annotation_rationale`, and `ambiguity_notes` are required for human verification but are not part of the retrieval-loader case. Keep these naming correspondences explicit when transferring annotations; do not duplicate or hand-edit chunk IDs.

### Relevance grades

| Grade | Label | Definition |
|---:|---|---|
| `2` | Primary | Directly answers the central question or supplies its central implementation evidence. |
| `1` | Supporting | Necessary context or a required dependency/call-chain hop, but not sufficient as the central answer alone. |

Every case must have at least one gold chunk. No other grades are valid; grades must be integers (not booleans). Merely related code is not relevant. For a multi-hop question, annotate all necessary evidence chunks. This fixed mapping supports the existing graded nDCG evaluation and may only change through an explicit versioned protocol decision.

### Difficulty rubric

Difficulty describes the evidence-reasoning burden of the question, not how well a retriever answers it, how long the source is, or an annotator's familiarity with the repository. Assign it from the pinned source before running retrieval:

| Level | Operational criterion |
|---|---|
| `easy` | One direct, distinctive evidence chunk normally suffices; the requested behavior or location is explicit and has little interpretive ambiguity. |
| `medium` | The answer requires interpreting multiple evidence details or a short relationship/call path; typically more than one chunk or a non-obvious distinction is needed. |
| `hard` | A complete answer requires multiple linked hops, cross-file/component reasoning, or resolving plausible competing paths/conditions. The question remains answerable from the declared static scope and its gold set must include all necessary evidence. |

The category quotas remain three questions per category per repository (12 per repository, 108 total). Retain the pre-existing design goal of including a deliberately challenging question in each category/repository allocation where feasible. Predeclare and report the difficulty distribution before annotation; the current validator does not enforce difficulty labels or difficulty quotas.

## Retrieval dataset projection

The current `BenchmarkLoader` consumes a JSON object with `schema_version: "1.0"` and a nonempty `cases` array. Each case contains exactly the retrieval identity, query, and gold labels needed by the existing validator:

| Loader field | Source in logical record |
|---|---|
| `query_id` | `query_id` |
| `repository_id` | `repository_id` |
| `commit_sha` | `commit_sha` |
| `query` | `query` |
| `relevance` | Projection of `expected_evidence_chunks` to `{chunk_id: relevance_grade}` |

The current retrieval payload does not carry `category` or `difficulty`. Categories are supplied separately as an exact query-ID-to-category map to the freeze utility and are incorporated in its canonical benchmark digest. Keep difficulty in the private annotation ledger; include it under the ledger's controlled digest and preserve the ledger with the frozen research record. Do not add fields to schema 1.0 or assume the loader hashes them. If future evaluation needs these fields in the payload, first version and implement a new schema and validator contract.

## Structural and provenance invariants

- Query IDs are unique, use the required slug/three-digit format, and match the repository slug.
- Repository IDs and full commit SHAs match the frozen snapshot map; branch names are not valid identities.
- Query text is nonempty, trimmed, single-line text without control characters.
- Each gold chunk ID exists in the deterministic inventory for the same repository and exact commit as its case.
- The inventory itself contains no duplicate chunk IDs or mixed/unexpected snapshots.
- Each case has a nonempty relevance mapping with only integer grades `1` and `2`.
- Each annotation-ledger span uses a repository-relative POSIX path, a symbol, and valid one-based inclusive line bounds; the file is included in `expected_files`.
- Annotation records and retriever outputs remain separate. Do not select or revise ground truth using retrieval rankings or unreviewed model-generated content.

Mechanical validation checks shape, IDs, grades, and supplied snapshot/inventory consistency. It does not establish privacy clearance, source-level correctness, human review, or correctness of claimed evidence. Apply the privacy and manual-review gates before calling a real dataset ready or frozen.

## Target coverage and readiness

The planned final target is 108 cases: nine frozen repository snapshots, 12 cases per repository, and three cases in each of the four categories per repository. This is a target allocation, not evidence that cases have been authored. The annotation guide and finalization protocol specify the review sample, pilot exclusion, validation, and freeze conditions.

As of this phase, the committed records state that the final benchmark is not annotated/frozen and the humanize pilot is not cleared. The current schema can therefore be considered specified for documentation purposes, but the benchmark dataset is **not ready for retrieval evaluation**. No real question or gold label may be produced until the applicable repository-specific privacy, history/secret disposition, personal/confidential-data, license/notice, and handling approvals are recorded.

See [benchmark-design.md](benchmark-design.md), [benchmark-annotation-guide.md](benchmark-annotation-guide.md), [benchmark-validation.md](benchmark-validation.md), [benchmark-finalization.md](benchmark-finalization.md), [corpus-final-selection.md](corpus-final-selection.md), and [corpus-preparation-workflow.md](corpus-preparation-workflow.md).