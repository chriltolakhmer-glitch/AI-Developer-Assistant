# System Architecture v1

**Status:** Initial blueprint (Phase 1), incrementally implemented through Phase 5.4. Scanner, Python AST parser, semantic chunker, and preprocessing validator now exist; retrieval/evaluation infrastructure remains planned.

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
| AST Parser | Parse the initial Python-only scope via the standard-library `ast` module; extract modules, classes, functions/methods, imports, decorators and exact source spans. Syntax failures are surfaced for a later labeled fallback decision. |
| Chunking Engine | Produce AST-aware chunks with stable source spans; handle oversized nodes deterministically; version chunking config. |
| Pipeline Validation | Before retrieval implementation, verify pinned scanner/parser/chunker outputs, corpus count reconciliation, parse coverage, determinism, and read-only behavior; write aggregate reports outside the source tree. |
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

The following Phase 1 candidates have since been narrowed by Phase 4: Python standard-library `ast` is selected for parsing; local `sentence-transformers/all-MiniLM-L6-v2` is selected at the immutable revision documented in [technology-selection-final.md](../research/technology-selection-final.md); and CPU FAISS `IndexFlatIP` is selected under [ADR-007](../decisions/ADR-007-vector-index-selection.md), subject to the pre-implementation environment smoke check.

- **Lexical index:** BM25 (e.g., `rank-bm25` or an existing search library).
- **Backend:** Python (FastAPI) to align with the parsing/embedding ecosystem.
- **LLM (secondary path):** A single fixed, declared model/provider (local or hosted) — chosen once the retrieval study is stable.
- **Evaluation storage:** Flat files or SQLite for experiment run metadata and metrics (kept simple for a solo researcher).

## Data Flow

```text
Pinned repository snapshot
  -> Scan & filter
  -> Document read & normalize (+ metadata)
  -> AST parse (syntax failures reported; fallback policy deferred)
  -> AST-aware chunking
  -> Pipeline validation (pinned revisions, counts, parse coverage, repeatability)
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
