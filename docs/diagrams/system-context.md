# System Context Diagram

**Status:** Phase 1 blueprint — no implementation exists yet.

```mermaid
flowchart TD
    RESEARCHER[Developer / Researcher] -->|Repository selection, questions| UI[Frontend / Research UI]
    OPERATOR[Research Operator] -->|Pin commits, configure experiments| UI
    UI -->|HTTP requests| API[Backend API / Experiment Orchestrator]
    API -->|Read-only clone/checkout| REPO[(Git Repository / Local Checkout)]
    API -->|Embedding / generation requests| LLM[LLM Provider - local or hosted]
    API -->|Read/write vectors and metadata| VDB[(Vector Database)]
    API -->|Read/write tokenized index| LEX[(Lexical / BM25 Index)]
    API -->|Write run metadata and metrics| LOG[(Evaluation / Logging Store)]
    API -->|Ranked evidence, optional answer| UI
```

## Notes

- The system never writes into the indexed source repository.
- The LLM Provider is only invoked when answer-generation mode is explicitly requested; retrieval-only mode does not call it.
- The Research Operator and Developer/Researcher may be the same person for a solo thesis project, but the roles are distinguished by responsibility (experiment configuration vs. question asking).
