# Phase 5.3 — Deterministic Code Chunker

**Status:** Implemented semantic chunk generation for parser-produced Python modules. The chunker is an in-memory transformation and does not persist code or build an index.

## Chunk generation flow

```text
Verified repository metadata + parsed Module + same decoded source text
  -> validate repository identity, SHA, path, and source line count
  -> slice full module source and each AST entity's inclusive line range
  -> create module, class, function, and method CodeChunk records
  -> derive SHA-256 chunk IDs from provenance, entity identity, span, and content hash
  -> return module first, then entities in stable source order
```

## Input and output

`CodeChunker.chunk_module(module, source, repository)` receives the immutable `Module` produced by `PythonAstParser`, the exact same decoded source string that was parsed, and `RepositoryMetadata` from the scanner/orchestrator. It returns a tuple of immutable `CodeChunk` values.

Each chunk carries its stable ID, repository identifier, normalized commit SHA, repository-relative file path, entity type, qualified name, one-based inclusive start/end lines, and exact source slice. The module chunk uses the parser's module name as its qualified name. Other entity names follow the parser's lexical qualified-name convention. The module chunk is always first; the remaining entities sort by start line, end line, type, and qualified name.

Class chunks intentionally contain their nested definitions, and separate method/function chunks are also emitted. This parent/child overlap preserves both whole-class context and focused retrieval units. Decorated entity ranges begin at the earliest decorator line because the parser includes decorators in the entity span.

## Design choices

- **AST semantic boundaries:** emit one chunk for each parser module, class, function, and method rather than splitting text at a fixed character/token window. The output records structural provenance needed for controlled retrieval comparisons.
- **Stable IDs:** SHA-256 of a canonical identity containing repository ID, commit, path, entity type/name, line range, and the source-slice digest. Repeated generation over identical inputs yields identical records and IDs; source or provenance changes produce different IDs.
- **Exact source preservation:** slice the supplied source by the parser's inclusive lines and retain its line endings. The chunker verifies the module line count to catch a common parse/chunk source mismatch.
- **No persistence or implicit splitting:** chunks exist in memory and the source tree is never opened or modified by the chunker. Fixed-size subdivision, overlap policies, and an index are deferred; unusually large chunks must be measured and handled in a later, separately specified chunking policy.
- **Privacy:** chunk content is source-derived research data. Callers must keep chunk collections local and outside Git, consistent with [ADR-008](../decisions/ADR-008-source-code-privacy.md). This implementation does not clear the corpus privacy-audit gate.

## Relationship with the AST parser

The parser identifies definitions and their exact ranges; the chunker does not re-parse text or infer boundaries independently. It maps each `ClassEntity` and `FunctionEntity` (including methods distinguished by `kind`) to a source slice, while creating one enclosing module chunk. Thus both lexical and future dense retrieval can use the same deterministic chunk records and provenance. Syntax failures remain the parser's explicit responsibility; this chunker does not invent fallback chunks.

See [ADR-011](../decisions/ADR-011-code-chunking.md) for the decision and [ast-parser-design.md](ast-parser-design.md) for entity extraction details.