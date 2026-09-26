# Data Flow Diagram

**Status:** Phase 1 blueprint — no implementation exists yet.

```mermaid
flowchart TD
    subgraph Indexing Path
        A[Pinned repository snapshot] --> B[Scan and file filtering]
        B --> C[Document read, normalize, metadata]
        C --> D[AST parse - fallback: text]
        D --> E[AST-aware chunking]
        E --> F[Embedding generation]
        F --> G[(Vector index)]
        E --> H[(Lexical / BM25 index)]
    end

    subgraph Question Path
        Q[Developer question] --> R[Query analysis - optional]
        R --> S[Retrieval: BM25 / dense / hybrid]
        G -->|Dense candidates| S
        H -->|Lexical candidates| S
        S --> T[Context construction - token budget, provenance]
        T --> U{Answer generation requested?}
        U -->|No| V[Retrieval-only response]
        U -->|Yes| W[LLM generation]
        W --> X[Citation / span validation]
        X --> Y[Response with evidence and answer]
    end

    V --> Z[(Evaluation / logging store)]
    Y --> Z
    S -->|Retrieval metrics| Z
```

## Notes

- The indexing path and question path are independent; the question path only depends on the indexes produced by indexing, not on a live indexing run.
- Every response (retrieval-only or generated) is logged with metrics inputs to support the Recall@k / MRR / nDCG and citation-validity evaluation defined in the requirements.
