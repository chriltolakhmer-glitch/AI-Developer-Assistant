# System Architecture v1

**Status:** Initial blueprint (Phase 1). No implementation exists yet; this document precedes and governs `src/`.

## Architecture Overview

The system follows a two-path architecture derived from the common pattern identified across prior analyzed projects, refined with this project's research requirements (provenance, token budgeting, hybrid retrieval, citation checking):

1. **Indexing path** — converts a pinned repository snapshot into AST-aware, metadata-carrying chunks stored in both a vector index and a lexical (BM25) index.
2. **Question path** — takes a developer question, retrieves evidence via a selectable strategy (BM25 / dense / AST-aware hybrid), builds a token-budgeted context, and either returns retrieval-only evidence or an optional LLM-generated answer with citation checks.

The orchestrator never modifies the indexed source tree and treats retrieval quality as independently measurable from generation quality.

## Component Responsibilities

| Component | Responsibility |
|---|---|
| Repository Analyzer / Scanner | Resolve a pinned commit, enumerate eligible files via allow/ignore rules, record identity and content hashes. |
| Document Processor | Read files, normalize text, attach language/path/hash metadata. |
| AST Parser | Parse supported languages (initially Python) via Tree-sitter; extract functions/classes/methods; provide labeled text fallback. |
| Chunking Engine | Produce AST-aware chunks with stable source spans; handle oversized nodes deterministically; version chunking config. |
| Embedding Service | Generate fixed-model embeddings for chunks and queries; log failures; enforce re-index on model change. |
| Vector Database | Persist chunk vectors and metadata; return nearest candidates. |
| Lexical/BM25 Index | Persist tokenized chunk text for keyword/symbol retrieval. |
| Query Analyzer | Normalize/classify the developer question (optional routing input). |
| Hybrid Retriever | Combine dense and lexical/symbol candidates per selected strategy (BM25-only, dense-only, hybrid); return ranked results with scores/strategy metadata. |
| Context Builder | Assemble retrieved evidence under a token budget; preserve repository/commit/path/line provenance; deduplicate. |
| LLM Service (secondary) | Optional fixed-prompt generation over the assembled context; retrieval-only mode always available. |
| Response Layer | Return ranked evidence, optional answer, and source references; flag citations failing span validation. |
| Evaluation/Logging Store | Persist experiment settings, retrieval metrics (Recall@k, MRR, nDCG) and answer-evaluation inputs. |
| Backend API / Experiment Orchestrator | Coordinates indexing and question-answering requests; does not write to source repositories. |
| Frontend / Research UI | Accepts repository selection and questions; displays ranked evidence, retrieval mode comparison, and optional answers. |

## Technology Candidates

These are candidates to evaluate during Phase 2, not final decisions:

- **Parsing:** Tree-sitter (Python grammar).
- **Embeddings:** Local SentenceTransformer model (e.g., `all-MiniLM-L6-v2`) for reproducibility; optionally a hosted embedding API for comparison.
- **Vector index:** FAISS or Chroma (decide based on filtering/metadata needs).
- **Lexical index:** BM25 (e.g., `rank-bm25` or an existing search library).
- **Backend:** Python (FastAPI) to align with the parsing/embedding ecosystem.
- **LLM (secondary path):** A single fixed, declared model/provider (local or hosted) — chosen once the retrieval study is stable.
- **Evaluation storage:** Flat files or SQLite for experiment run metadata and metrics (kept simple for a solo researcher).

## Data Flow

```text
Pinned repository snapshot
  -> Scan & filter
  -> Document read & normalize (+ metadata)
  -> AST parse (fallback: text)
  -> AST-aware chunking
  -> Embedding generation
  -> Vector index + Lexical index (source metadata retained)
```

```text
Developer question
  -> Query analysis (optional)
  -> Retrieval (BM25 | dense | hybrid, per selected strategy)
  -> Context construction (token budget, provenance, dedup)
  -> Retrieval-only response
       OR
     LLM generation -> citation/span validation -> Response
  -> Evaluation/logging (metrics recorded per run)
```

## Communication Flow

- UI ↔ Backend API: HTTP requests for repository indexing and question submission; responses include ranked evidence, strategy metadata, and optional answers.
- Backend API ↔ Analyzer/Chunking/Embedding: in-process or internal calls during the indexing job; no external network dependency required for local models.
- Backend API ↔ Vector/Lexical indexes: read/write calls scoped by repository+commit identity.
- Backend API ↔ LLM Service: outbound call only when answer-generation mode is explicitly requested; retrieval-only mode bypasses this entirely.
- Backend API ↔ Evaluation Store: write experiment run metadata and metrics after each indexing or query operation.

See companion diagrams: [system-context.md](../diagrams/system-context.md), [component-architecture.md](../diagrams/component-architecture.md), [data-flow.md](../diagrams/data-flow.md).
