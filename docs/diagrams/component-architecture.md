# Component Architecture Diagram

**Status:** Phase 1 blueprint — no implementation exists yet.

```mermaid
flowchart TD
    UI[Frontend / Research UI] --> API[Backend API / Experiment Orchestrator]

    API --> ANALYZER[Repository Analyzer / Scanner]
    ANALYZER --> DOC[Document Processor]
    DOC --> AST[AST Parser]
    AST --> CHUNK[Chunking Engine]
    CHUNK --> EMB[Embedding Service]
    EMB --> VDB[(Vector Database)]
    CHUNK --> LEX[(Lexical / BM25 Index)]

    API --> QAN[Query Analyzer]
    QAN --> HYBRID[Hybrid Retriever]
    VDB -->|Dense candidates| HYBRID
    LEX -->|Lexical / symbol candidates| HYBRID

    HYBRID --> CTX[Context Builder]
    CTX --> RESP[Response Layer]
    CTX -->|Optional| LLM[LLM Service - secondary]
    LLM --> RESP
    RESP --> API

    API --> LOG[(Evaluation / Logging Store)]
    HYBRID -->|Retrieval metrics| LOG
    RESP -->|Answer / citation metrics| LOG
```

## Notes

- Each component behind the Backend API is intended to be independently testable and swappable (per the maintainability non-functional requirement).
- The Hybrid Retriever supports three selectable strategies: BM25-only, dense-only, and combined hybrid — all three must be comparable for the primary research evaluation.
- The LLM Service is explicitly marked secondary/optional to keep the primary retrieval study decoupled from generation quality.
