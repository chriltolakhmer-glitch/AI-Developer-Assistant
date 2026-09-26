# ADR-012: Validate Deterministic Preprocessing Before Retrieval

## Status

Accepted and implemented as a validation tool for Phase 5.4 on 2026-09-26. Corpus-wide execution remains blocked until local snapshots are available.

## Context

The scanner, Python AST parser, and semantic chunker have independent tests, but their combined behavior and aggregate metrics must be checked against the approved nine pinned repositories before implementing retrieval. Validation must preserve revision identity, expose parse failures, demonstrate deterministic outputs, and keep source-derived data local.

## Decision

Implement an offline pipeline validation runner for the fixed Phase 4.5 corpus. The runner uses existing local checkouts only, verifies each expected commit with the scanner, rejects dirty tracked worktrees, and executes scanner → parser → chunker. It collects repository identity, commit, Python file/LOC counts, parse coverage, module/class/function/method counts, chunk counts, and chunk-size statistics. Successful parse and chunk results are repeated and compared.

Write aggregate JSON and Markdown reports only outside the thesis Git repository and corpus checkouts. Do not clone/fetch, call external services, send source elsewhere, generate embeddings, create vector indexes, or introduce user-facing UI/LLM/chat features in this phase.

## Rationale

Running the stages together reveals contract issues that unit tests alone may miss. Reconciliation against the published Phase 4.5 counts detects filter drift before annotation or retrieval. Repeated outputs and pinned revisions provide evidence of reproducibility; explicit parse failures avoid silent data loss. External aggregate reports preserve auditability without committing corpus-derived content.

## Consequences

- The pipeline runner is not a substitute for the secret/credential and personal/confidential-data audit; that remains a blocking pre-index gate under [ADR-008](ADR-008-source-code-privacy.md).
- Missing repositories, SHA mismatches, dirty trees, count deltas, parser failures, and nondeterminism block preprocessing readiness and must be recorded/dispositioned.
- The baseline includes all eligible tracked Python files, including ordinary test files, according to the existing Phase 4.5 filter.
- Chunk-size statistics are source-character and UTF-8-byte counts, not tokenizer/model token counts. Oversized chunks and deterministic splitting remain future design decisions.
- No embedding/vector-index readiness claim follows from this validation decision or a passing test suite.

## References

- [Phase 4.5 corpus manifest validation](../research/corpus-manifest-validation.md)
- [Phase 5.4 pipeline validation methodology and current result](../research/pipeline-validation.md)
- [Scanner architecture](../architecture/scanner-design.md)
- [AST parser architecture](../architecture/ast-parser-design.md)
- [Chunker architecture](../architecture/chunker-design.md)