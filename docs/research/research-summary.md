# Research Summary (Input to Phase 1 Blueprint)

**Source material:** Static analyses of three prior repositories (`codebase-rag`, `Codebase-RAG-Assistant`, `ai-codebase-assistant`) and synthesis documents maintained outside this repository under `Explore/thesis/` and `Explore/reports/` (kept unmodified as prior research artifacts). This file summarizes the findings relevant to this project's blueprint; it does not duplicate or replace the source documents.

## Common AI assistant architecture (extracted)

A two-path system recurs across all three analyzed projects:

- **Indexing path:** repository snapshot → scan/filter → document read/normalize → parse (AST where supported, else text) → chunk → embed → store in a vector/lexical index with source metadata.
- **Question path:** developer question → optional query analysis/classification → retrieval (dense, and optionally lexical/symbol) → context assembly (provenance, dedup, token budget) → LLM generation or retrieval-only response → answer/evidence returned to the UI.

Implementation choices (UI type, parser presence, storage engine, model hosting) vary; the two-path shape and metadata-carrying chunk model are the shared pattern.

## Research gaps (extracted)

1. **Code understanding accuracy** — hash-based or text-window chunking loses semantic/structural fidelity compared with AST-aware chunking.
2. **Large repository handling** — no analyzed project reports indexing/query performance at scale.
3. **Retrieval quality** — no project has a labeled benchmark (Recall@k / MRR / nDCG) comparing dense, lexical and hybrid retrieval.
4. **Source code relationship understanding** — cross-file/call-graph relationships are regex-approximated, not compiler/symbol-resolved.
5. **Context limitation and construction** — no consistent token-budget policy; duplication and omission are possible.
6. **Answer verification and trust** — citations are prompted for, not mechanically verified against retrieved spans.
7. **Incremental updates and index consistency** — no project demonstrates a transactional, commit-aware update/delete lifecycle.
8. **Developer workflow integration** — no IDE/editor integration or usability evaluation observed.

## Possible thesis contribution (extracted)

Three directions were identified; **Option B — AST-Aware Hybrid Retrieval System** was recommended as the most defensible, bounded Master's-thesis scope:

- Research question: does AST-aware chunking plus hybrid (dense + lexical/symbol) retrieval improve relevant-evidence retrieval for identifier, dependency and cross-file questions over dense-only or text-window baselines, under a fixed context/token budget?
- Evaluation: Recall@k, MRR, nDCG, source-span accuracy, context token cost, measured against a manually annotated query-to-evidence benchmark for a bounded (initially Python-only) language scope.
- An LLM answer-generation layer is a secondary, optional evaluation, not the primary contribution; retrieval-only mode is required for the primary study.

This summary feeds directly into [system-requirements.md](../requirements/system-requirements.md) and [system-architecture-v1.md](../architecture/system-architecture-v1.md).
