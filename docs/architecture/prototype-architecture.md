# Prototype Architecture

**Status:** Phase 3 blueprint, incrementally implemented through Phase 6.3.1. Scanner, AST parser, chunker, preprocessing validation, local chunk embeddings, and FAISS vector-query retrieval are implemented. BM25, fusion, text-query encoding, and metric evaluation remain planned. See [embedding-implementation.md](embedding-implementation.md), [vector-retrieval-design.md](vector-retrieval-design.md), and [pipeline-validation.md](../research/pipeline-validation.md). Corpus execution remains subject to privacy clearance. Refines [system-architecture-v1.md](system-architecture-v1.md) into components scoped for [experiment-design.md](../research/experiment-design.md).

## Scope of This Prototype

This architecture covers only what is needed to run the **RQ1 retrieval-only evaluation**: ingest pinned Python repositories, build three comparable retrieval strategies (BM25, dense, AST-aware hybrid), and score them against the benchmark. Answer generation (RQ2) and any UI beyond a minimal evaluation runner are excluded from this first prototype (see [ADR-003](../decisions/ADR-003-system-boundary.md)).

## Components

### Repository Scanner

- **Responsibility:** Resolve a pinned commit for a given repository (local checkout or clone), enumerate eligible Python files via a configurable allow/ignore policy, record repository identity, commit SHA, and per-file content hashes.
- **Output:** A manifest of eligible files with path, language, hash, and byte size; excluded-file log with exclusion reason.
- **Constraint:** Read-only — never writes into the scanned repository.

### Python AST Parser

- **Responsibility:** Parse each eligible Python file using Python's built-in `ast` module (see [ADR-005](../decisions/ADR-005-technology-selection.md) and [ADR-010](../decisions/ADR-010-ast-parser.md)), extracting module identity, classes, functions, methods, imports, decorators and exact source line spans.
- **Output:** Per-file structured module record with qualified names and source ranges; syntax failures are surfaced with file and location, not silently skipped.
- **Failure handling:** Syntax failures are counted and reported by pipeline validation. The current implementation does not emit fallback chunks; any fallback policy is deferred and must be explicit.

### Code Chunker

- **Responsibility:** Convert each parsed module, class, function, and method into a semantic source chunk carrying repository ID, commit, file path, qualified name/type, exact line span, and source text.
- **Output:** An in-memory, deterministic chunk inventory intended to be shared by future embedding and lexical retrieval pipelines.
- **Constraint:** Same repository, commit, AST, and source produce the same stable chunk IDs. Parent/child chunks overlap intentionally; fixed-size splitting and persistence are not implemented in this milestone.

### Pipeline Validation

- **Responsibility:** Run the scanner → AST parser → chunker over each approved local, SHA-pinned repository checkout before implementing retrieval. Verify expected file/LOC counts, parser success/failure accounting, repeated parse/chunk equality, and source-tree read-only behavior.
- **Output:** Aggregate per-repository JSON and Markdown reports written outside this Git repository and all corpus checkouts. Reports contain counts and chunk-size distributions, not source text or per-file paths.
- **Constraint:** Local-only; no clone/fetch, embeddings, vector database, LLM, UI, or chatbot. The required secret/privacy audit is separate and remains a gate before indexing.

### Embedding Generator

- **Responsibility:** Generate a fixed-model embedding vector for every chunk and for every incoming query, using a single recorded model/version (see [ADR-005](../decisions/ADR-005-technology-selection.md)).
- **Output:** Chunk-ID → vector mapping; failures logged, not silently dropped.
- **Constraint:** A model change invalidates the existing vector index and requires an explicit, logged re-embedding pass.

### Vector Index

- **Responsibility:** Persist normalized chunk vectors in a per-repository+commit FAISS `IndexFlatIP`, resolve results through the deterministic chunk-ID/provenance sidecar, and return exact cosine-ranked candidates (see [ADR-007](../decisions/ADR-007-vector-index-selection.md)).
- **Output:** Ranked candidate chunk IDs with similarity/distance scores for the dense-only baseline and as one input to the hybrid retriever.

### BM25 Index

- **Responsibility:** Tokenize and index the same chunk text for lexical/keyword retrieval, using a documented tokenization scheme.
- **Output:** Ranked candidate chunk IDs with BM25 scores for the keyword-only baseline and as the second input to the hybrid retriever.

### Hybrid Retriever

- **Responsibility:** Implement all three retrieval strategies behind one interface so the evaluation module can request BM25-only, dense-only, or AST-aware hybrid results for the same query:
  - **BM25-only:** pass through BM25 Index results.
  - **Dense-only:** pass through Vector Index results.
  - **Hybrid:** fuse Vector Index and BM25 Index candidates using a fixed, predeclared fusion method (e.g., Reciprocal Rank Fusion with fixed parameters), frozen before evaluation per [evaluation-plan.md](../research/evaluation-plan.md).
- **Output:** Ranked chunk IDs with rank, score, and strategy label for every query/strategy combination.

### Evaluation Module

- **Responsibility:** Load the benchmark (from [benchmark-design.md](../research/benchmark-design.md)), run every question against every retrieval strategy, compare ranked chunk IDs to gold evidence spans, and compute Recall@k, MRR@10 and nDCG@10.
- **Output:** Per-query results, per-category/per-size-stratum aggregates, and raw ranked outputs retained for failure analysis, per [experiment-design.md](../research/experiment-design.md).
- **Constraint:** No LLM call in this module — retrieval-only, so generation cannot mask retrieval errors.

## Component Interaction (indexing → evaluation)

```text
Repository Scanner -> Python AST Parser -> Code Chunker
                                              -> Pipeline Validation -> aggregate preprocessing report
                                              |-> Embedding Generator -> Vector Index
                                              |-> BM25 Index
Code Chunker (chunk store) + Vector Index + BM25 Index -> Hybrid Retriever
Benchmark (repository-corpus-selection.md + benchmark-design.md) + Hybrid Retriever -> Evaluation Module -> Recall@k / MRR@10 / nDCG@10 results
```

## Explicitly Excluded From This Prototype

- LLM answer generation and citation validation (RQ2) — deferred to a later phase if time allows.
- Any user-facing UI beyond a minimal script/CLI needed to run the evaluation and inspect results.
- Multi-language parsing, incremental/streaming indexing, and any write-back to source repositories.
