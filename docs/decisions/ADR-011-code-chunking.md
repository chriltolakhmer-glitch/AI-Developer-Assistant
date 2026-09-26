# ADR-011: Use AST-Based Semantic Code Chunks

## Status

Accepted and implemented for Phase 5.3 on 2026-09-26.

## Context

The retrieval experiment requires comparable units that retain code structure and exact provenance. Phase 5.2 provides Python module, class, function, method, and line-span entities. Fixed-size text windows would impose boundaries independently of those entities and could split definitions without providing an AST-based baseline.

## Decision

Use AST-based semantic chunks as the initial chunking method instead of fixed-size text chunks. Emit one module chunk and one chunk for each class, function, and method using the parser's source ranges. Each immutable chunk records repository ID, commit SHA, relative file path, entity type, qualified name, inclusive line range, and exact source content.

Generate a deterministic SHA-256 chunk ID from the repository/commit/path identity, entity identity and span, plus the source-content digest. Return chunks in a stable order and keep them in memory; do not persist them, split oversized entities, add an index, or introduce an external service in this milestone.

## Rationale

AST-defined chunks preserve syntactic boundaries and source locations needed for evidence-grounded retrieval and later span validation. Module/class/function/method granularity retains both broad context and focused definitions. Provenance-aware stable IDs allow the same chunk units to be shared by future BM25 and dense retrieval without silently conflating revisions or content changes.

## Consequences

- The chunker must receive the same decoded source text used to create its `Module`; it validates module line count and slices inclusive parser ranges.
- Class and module chunks overlap their child chunks by design. Future evaluation must use the same chunk inventory across retrieval strategies and define how overlapping evidence is scored.
- AST ranges can produce large chunks. Chunk-size limits, deterministic splitting, and overlap policy remain open protocol decisions and must be frozen before held-out evaluation.
- Keep chunk text and derived artifacts outside Git under [ADR-008](ADR-008-source-code-privacy.md); the secret/privacy audit still gates corpus indexing.
- The decision makes no claim that semantic chunks improve retrieval scores; that remains an empirical question.

## References

- [ADR-010: Python AST parser](ADR-010-ast-parser.md)
- [AST parser architecture](../architecture/ast-parser-design.md)
- [Chunker architecture](../architecture/chunker-design.md)
- [Evaluation plan](../research/evaluation-plan.md)