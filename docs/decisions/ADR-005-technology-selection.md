# ADR-005: Technology Selection for the Retrieval Evaluation Prototype

## Status

**Status:** Superseded for final Phase 4 choices by [ADR-007](ADR-007-vector-index-selection.md) and [technology-selection-final.md](../research/technology-selection-final.md). The Python `ast` and local embedding defaults are confirmed; the earlier FAISS/Chroma deferral is closed by ADR-007.

## Context

[prototype-architecture.md](../architecture/prototype-architecture.md) defines the components needed for the RQ1 retrieval evaluation (Repository Scanner, Parser, Chunker, Embedding Generator, Vector Index, BM25 Index, Hybrid Retriever, Evaluation Module). Three technology choices most directly affect reproducibility and the validity of the retrieval comparison: the parser, the vector index, and the embedding model.

## Decision Candidates

### Parser: Python AST (standard library `ast`)

- **Considered alternative:** Tree-sitter Python grammar (used by two of the three previously analyzed projects).
- **Trade-offs:**
  - Python's built-in `ast` module requires no external grammar dependency, is guaranteed version-matched to the Python interpreter running the study, and is sufficient for the declared scope (functions, methods, classes, line spans).
  - Tree-sitter offers a uniform parsing interface that would generalize more easily to future multi-language extension (explicitly out of scope per [ADR-003](ADR-003-system-boundary.md)) and provides a full concrete syntax tree (comments, whitespace-sensitive nodes) that `ast` discards.
  - Since this thesis is Python-only by scope decision, the multi-language generalization benefit of Tree-sitter is not currently needed, and avoiding an extra dependency reduces reproducibility risk (fewer pinned versions to track).
- **Leaning:** Python `ast` for the initial prototype; revisit only if multi-language scope is added in future work.

### Vector Index: FAISS vs. Chroma (Phase 3 comparison; superseded)

- **Trade-offs:**
  - **FAISS (`IndexFlatL2` or similar):** minimal dependency footprint, well-understood exact/approximate search, no built-in metadata filtering — chunk metadata must be tracked in a separate sidecar structure (as observed in the analyzed `codebase-rag` project).
  - **Chroma:** persistent collection with built-in metadata storage and cosine-similarity search, simplifying repository/commit-scoped filtering, at the cost of an additional service/library dependency and less direct control over index internals.
  - For a controlled, single-machine research evaluation with modest corpus size (nine repositories, small/medium/large strata), both are computationally adequate; the deciding factor is metadata-handling convenience and reproducibility of persisted state across evaluation runs, not raw performance at this scale.
- **Phase 3 leaning:** Decide during the pilot step by testing metadata-filtering needs (e.g., isolating candidates per repository/commit) against both libraries with a small sample repository. This deferral is now resolved: see [ADR-007](ADR-007-vector-index-selection.md) for the accepted FAISS decision.

### Embedding: Local model vs. API model

- **Considered candidates:** local SentenceTransformer (e.g., `all-MiniLM-L6-v2`, used by `Codebase-RAG-Assistant`) vs. a hosted embedding API (e.g., OpenAI embeddings).
- **Trade-offs:**
  - **Local model:** fully reproducible (fixed weights, no network dependency, no per-call cost), but requires local compute and may have lower embedding quality than large hosted models; keeps source code off third-party services, satisfying the "no source sent to hosted LLMs unless explicitly permitted" constraint from [dataset-design.md](../research/dataset-design.md).
  - **API model:** potentially higher embedding quality, but introduces network latency, per-call cost, provider version drift over time, and a data-handling question (sending source code to a third party) that must be explicitly justified per repository license/terms.
  - Reproducibility and data-handling simplicity favor a local model as the default for the primary evaluation; an API model could be run as a documented secondary comparison only if licensing and privacy terms are separately verified per repository.
- **Leaning:** Local SentenceTransformer model as the default/primary embedding for reproducibility; API-based embedding treated as an optional, separately justified comparison, not the primary evaluation path.

## Decision

The Phase 3 decision was to record candidates, adopt Python `ast` and local SentenceTransformers as working defaults, and defer the vector index pending a pilot. Phase 4 closes that deferral: Python `ast` and the pinned local embedding selection are adopted, and FAISS is selected under [ADR-007](ADR-007-vector-index-selection.md), subject to its pre-implementation environment smoke check.

## Reason

The original Phase 3 rationale for Python `ast` and local embeddings remains valid: they reduce dependencies and keep source local. The vector-index trade-off has since been resolved for the bounded evaluation; see [ADR-007](ADR-007-vector-index-selection.md) and [technology-selection-final.md](../research/technology-selection-final.md) for the FAISS rationale and constraints.

## Consequences

- Any implementation in `src/` must record the exact `ast` behavior (Python version), pinned embedding model/revision, and vector-index/library version and configuration.
- The final vector-index choice and its installation gate are recorded in [ADR-007](ADR-007-vector-index-selection.md); the complete configuration is in [technology-selection-final.md](../research/technology-selection-final.md).
- If multi-language support is ever added (a scope change requiring its own ADR), the parser decision must be revisited, since `ast` is Python-specific.
