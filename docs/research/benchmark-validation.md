# Phase 8.1 — Benchmark Validation

## Purpose and current status

This gate validates the final local JSON benchmark against the chunk inventory and immutable repository commits selected for the study. It does not index repositories, run a retriever, calculate experiment metrics, or grant privacy clearance. Validation uses only supplied metadata and generated test fixtures; benchmark query/gold data and source-derived inventories remain local and outside Git.

The target design remains 12 questions per repository across nine repositories (108 total), balanced across the four predeclared categories. Passing a small validation fixture proves the validator's contract only; it does not mean that the target benchmark has been annotated, reviewed, or frozen.

## Benchmark structure

The existing JSON envelope is `schema_version: "1.0"` with a non-empty `cases` array. Each case contains a unique `query_id`, `repository_id`, full `commit_sha`, natural-language `query`, and non-empty `relevance` mapping of chunk IDs to grades. Query IDs follow `<repository-slug>-<three-digit-sequence>`; the slug is the final component of the repository identity. Query text is a trimmed, non-empty, single-line string. Category, annotation rationale, and ambiguity notes belong in the authoring/ground-truth record and are not required by the retrieval loader's current version-1 payload.

The final relevance mapping uses integer grade **2 for primary** evidence and **1 for supporting** evidence. Other values (including booleans, zero, and values above 2) are invalid. This explicit mapping preserves the two relevance classes in [benchmark-design.md](benchmark-design.md) and the graded ranking requirement in [evaluation-framework.md](evaluation-framework.md).

## Validation rules

`BenchmarkValidator.validate` receives a loaded `Benchmark`, the exact iterable of generated `CodeChunk` records, and a repository-to-commit mapping for the intended frozen snapshots. It returns a source-free `BenchmarkValidationReport`; `is_valid` is true only when `issues` is empty.

The validator checks:

1. Supported schema and at least one well-formed case.
2. Unique query IDs with the repository-slug/three-digit format, and non-empty, trimmed, single-line query text without control characters.
3. Unique, non-empty chunk IDs in the supplied inventory; every inventory record belongs to the declared repository snapshot.
4. Every case's repository and full commit SHA exactly match the supplied frozen snapshot map.
5. Every relevance entry has a unique ID present in the inventory, belongs to that case's same repository and commit, and has grade 1 or 2.

Issues are stable machine-readable codes (for example `missing_chunk_id`, `snapshot_mismatch`, and `relevance_grade_invalid`), sorted in the returned report. Counts and issue codes deliberately omit query text, source paths, and source content.

## Ground-truth verification process

1. Author each question from static evidence in the exact pinned checkout. Phrase it in natural developer language and do not reveal the target symbol/path unless testing identifier lookup.
2. Independently inspect each gold file/symbol/span at the pinned commit. Confirm inclusive lines and that grade 2 directly answers the question while grade 1 is necessary supporting context. Include every required hop for cross-file questions.
3. Record annotation rationale, ambiguity, and source references in the separate local annotation ledger; do not derive labels from retriever output or unreviewed LLM output.
4. Before annotation, declare the second-review sample (target at least 20%); have a second reviewer independently label it, adjudicate disagreements, and retain the review record locally. If a second reviewer is unavailable, document the single-annotator limitation and do not claim inter-rater agreement.
5. Exclude pilot questions that informed annotation-instruction refinement or retrieval tuning from the final evaluation set.
6. Run the automated validator over the final benchmark and exact chunk inventory, then manually sign off the annotations and freeze the resulting benchmark artifact/hash before experiment execution.

## Snapshot consistency and freeze checks

- The expected snapshot map must contain a full 40-character SHA-1 for every benchmark repository. No branch name or moving ref is accepted as a snapshot identity.
- Each query commit must equal its repository's expected SHA. Each relevant chunk must exist and match both the case repository ID and commit; matching IDs from a different snapshot are rejected.
- The supplied inventory itself is checked for duplicate IDs and repository/commit mismatches, catching mixed-snapshot inputs before scoring.
- Rebuild or verify the exact inventory deterministically from the pinned checkout before validation. The validator does not scan a checkout or independently prove that chunk IDs were correctly generated; scanner/parser/chunker provenance is an upstream gate.
- At freeze, retain a SHA-256 digest of the canonical benchmark JSON, snapshot-map digest, schema/grade mapping, annotation-review record, and validator version in the controlled local research record. Any post-freeze label/query/split change requires a new benchmark version and explicit protocol note; do not silently overwrite the frozen artifact.
- Benchmark validation is separate from source privacy clearance. Current corpus records still state that secret and personal/confidential-data reviews are open, so validation cannot authorize corpus indexing or experiments.

## Readiness interpretation

The validator and synthetic unit tests establish the mechanical rules. Benchmark readiness remains **pending** until the complete target cases are authored, independently checked as available, validated against the frozen chunk inventory, and frozen with recorded hashes. Experiment readiness remains **blocked** while benchmark freeze or privacy clearance is incomplete. No full experiment is run in Phase 8.1.

See [ADR-021](../decisions/ADR-021-benchmark-freeze.md) for the freeze decision.