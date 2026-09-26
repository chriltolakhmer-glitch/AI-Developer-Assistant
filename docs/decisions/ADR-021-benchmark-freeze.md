# ADR-021: Freeze the benchmark before experiment execution

- **Status:** Accepted
- **Date:** 2026-09-27
- **Decision owners:** Thesis author

## Context

Retrieval comparisons are only interpretable if questions, gold evidence, relevance grades, and repository snapshots are fixed independently of system outputs and before held-out experiment execution. The existing benchmark design requires manually verified evidence at pinned commits and separates ground truth from retriever output. Its primary/supporting labels must map unambiguously to the integer grades consumed by the evaluation framework.

## Decision

Freeze the complete benchmark before running any retrieval experiment. The frozen artifact must:

- use the versioned benchmark schema and the declared query-ID/query-text format;
- identify each case's repository and full immutable commit SHA;
- use grade 2 for primary evidence and grade 1 for supporting evidence;
- pass `BenchmarkValidator` against the exact chunk inventory for the frozen snapshot map, with no validation issues;
- have manually verified ground truth, rationale/ambiguity records, and a documented independent-review sample or single-annotator limitation;
- exclude pilot questions that influenced instructions or retrieval tuning; and
- be recorded with canonical benchmark and snapshot-map SHA-256 digests in the controlled local research record.

The frozen benchmark is not edited in place. A correction, changed label, or changed split creates a new benchmark version, preserves the prior digest, and documents the deviation before any subsequent experiment. Retriever results must never be used to modify the gold labels during evaluation.

## Consequences

- No full experiment may begin until the complete benchmark is authored, validated, reviewed, and frozen.
- Phase 8.1 unit tests use generated synthetic chunks only; they do not assert that real benchmark annotations exist or are correct.
- Passing benchmark validation does not close repository secret/privacy clearance. Corpus processing and experiments remain blocked until that independent gate is closed.
- Any protocol change to query content, snapshot selection, relevance mapping, or held-out membership requires explicit versioning and reporting.

## References

- [Benchmark validation process](../research/benchmark-validation.md)
- [Benchmark design](../research/benchmark-design.md)
- [Dataset design](../research/dataset-design.md)
- [Evaluation framework](../research/evaluation-framework.md)
- [ADR-020: retrieval evaluation](ADR-020-retrieval-evaluation.md)
- [Dataset snapshot freeze](../research/dataset-snapshot-freeze.md)