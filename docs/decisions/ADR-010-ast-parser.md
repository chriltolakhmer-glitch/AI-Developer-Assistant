# ADR-010: Use Python AST for Initial Structural Code Analysis

## Status

Accepted and implemented for Phase 5.2 on 2026-09-26.

## Context

The retrieval prototype needs reproducible source structure and exact source locations before chunking. The research scope is Python-only, and Phase 4 selected the standard-library `ast` parser to avoid an additional grammar dependency. The Phase 5.1 scanner provides a pinned, read-only source inventory; this milestone adds structured modules and code entities without adding retrieval infrastructure.

## Decision

Use Python's standard-library `ast` module as the first structural code analysis method. Parse source without executing it and extract module identity, classes, functions, methods, imports, decorators, class bases, qualified names, and one-based inclusive line ranges. Represent results with immutable `Module`, `ClassEntity`, `FunctionEntity`, and `ImportEntity` data structures.

Reject paths that are absolute or traverse above the repository root. Surface syntax errors with repository-relative path and source location; do not silently skip malformed files. Keep the parser deterministic and read-only, use no runtime dependencies or external services, and do not add UI, LLM, chatbot, or vector-database functionality in this milestone.

## Rationale

Python AST provides syntax-aware definitions and spans using the parser built into the selected runtime. It is sufficient for the declared Python-only research scope, keeps the prototype small, and avoids grammar/package version drift. Stable entity ordering and explicit failure reporting improve manifest-to-entity traceability.

## Consequences

- Record the Python interpreter version with parser/corpus run metadata because Python grammar support can change across versions.
- AST does not preserve comments or formatting and does not resolve runtime/dynamic behavior; these limitations must be considered in later chunking and failure analysis.
- Nested definitions are represented using qualified names; methods are distinguished from nested local functions.
- Parse failures are explicit and must be counted/reviewed before the later chunker decides on a labeled fallback representation.
- This decision does not satisfy the separate corpus secret/privacy audit gate and does not authorize indexing of uncleared snapshots.

## References

- [ADR-005: technology selection](ADR-005-technology-selection.md)
- [Python AST documentation](https://docs.python.org/3/library/ast.html)
- [Phase 5.1 scanner architecture](../architecture/scanner-design.md)
- [Prototype architecture](../architecture/prototype-architecture.md)
- [AST parser design](../architecture/ast-parser-design.md)