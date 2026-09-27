# Phase 19.8 - Software prototype scope notice

**HISTORICAL BLUEPRINT - current scope narrowed**

Current project scope: [Research software prototype validation](../research/software-prototype-scope.md).

The requirements below retain the original design rationale. Current work maintains and validates implemented ingestion, chunking, indexing, retrieval, evaluation and validation utilities on the Humanize pilot. Unimplemented blueprint features, optional LLM/UI capabilities, new retrieval strategies, new comparisons and scaling studies are not active requirements.

## Preserved earlier document

# System Requirements

**Status:** Draft blueprint for Phase 1. No source code has been implemented against this document yet.

## Project Objective

Build a research prototype that indexes pinned repository snapshots (initial scope: Python) and retrieves relevant, source-located evidence for developer questions, using AST-aware chunking and hybrid (dense + lexical/symbol) retrieval. The prototype exists to answer a bounded research question through controlled comparison against keyword-only and dense-vector baselines. An LLM answer-generation layer is a secondary, optional capability.

## Problem Statement

Existing AI codebase-assistant implementations (reviewed in prior research) combine repository ingestion, some form of vectorized retrieval, and LLM-based response generation, but none demonstrate: semantically meaningful chunking consistently, a labeled retrieval benchmark, compiler/symbol-resolved cross-file relationships, a token-budgeted context policy, or mechanically verified answer citations. This project addresses the gap between "a working RAG demo" and "measured, evidence-grounded retrieval for code."

## Target Users

- **Primary:** Software engineering researchers and thesis evaluators assessing code retrieval and source-grounding quality.
- **Secondary:** Developers, students and maintainers exploring an unfamiliar repository.
- **Research operator:** The thesis author, who selects pinned repositories, prepares query/evidence annotations, runs baselines and records results.

## Actors

- **Developer/Researcher** — submits repository selections and questions, inspects ranked evidence and (optionally) generated answers.
- **Research Operator** — configures experiments, pins repository commits, manages the evaluation dataset.
- **System (Backend/Orchestrator)** — coordinates ingestion, indexing, retrieval and evaluation; does not modify source repositories.
- **LLM Provider** — external/local model used only for the secondary answer-generation capability.

## Functional Requirements

- **FR1 — Repository ingestion:** Accept a local checkout or repository URL resolved to an immutable commit; enumerate eligible files via configurable allow/ignore lists; record repository identity, commit and content hashes; never write into the indexed source tree.
- **FR2 — Source code analysis:** Detect supported language/extension per file, preserve relative paths and source coordinates, and record parse/read errors explicitly.
- **FR3 — AST parsing:** Parse Python files with a declared Tree-sitter grammar/version, extract functions/methods/classes, record parse coverage, and provide a clearly labeled text fallback for unsupported/failed files.
- **FR4 — Code chunk generation:** Produce AST-aware chunks with stable source spans and metadata; define a deterministic strategy for oversized nodes; avoid duplicate/stale chunks on re-index; record chunking configuration for reproducibility.
- **FR5 — Embedding generation:** Generate embeddings for chunks and queries using a fixed, recorded model/version; log batch settings and failures; require re-indexing (or a separate index) on model change.
- **FR6 — Hybrid retrieval:** Support three comparable modes — keyword/BM25, dense-vector, and AST-aware hybrid — with a specified fusion/ranking method; return scores, rank and strategy metadata.
- **FR7 — Context construction:** Assemble retrieved evidence (with optional bounded structural neighbors) under a configurable token budget, preserving repository/commit/path/line provenance and avoiding duplication.
- **FR8 — LLM response generation (secondary):** Optionally pass a fixed question, selected context and prompt to a declared LLM; support retrieval-only mode; record model/generation settings; distinguish provider errors from successful answers. No autonomous code edits are in scope.
- **FR9 — Source reference display:** Display repository revision, path and line span for every retrieved item; flag references that fail mechanical span validation when answer generation is enabled.

## Non-Functional Requirements

- **Performance:** Measure cold indexing time, query latency (p50/p95), embedding throughput, memory and index size on a documented machine; thresholds set after a pilot.
- **Accuracy:** Evaluate retrieval with Recall@k, MRR@10, nDCG@10 against an annotated query-to-evidence set; use a rubric (not LLM fluency) for optional-answer correctness, citation validity and abstention.
- **Scalability:** Operate within predeclared small/medium/large repository strata; record file count, eligible LOC, chunk count, parse failures and resource use; generalization beyond tested sizes must be qualified.
- **Maintainability:** Separate ingestion, parsing/chunking, embedding, each retrieval baseline, context assembly and answer generation behind clear interfaces; configure rather than hard-code experimental settings.
- **Reproducibility:** Pin repository commits, dependencies, grammar and embedding model versions; version chunk/fusion/prompt settings; store query-set version and seeds where supported; exclude credentials/private source from the research dataset.

## System Scope

- Ingestion, AST-aware chunking, embedding, and three comparable retrieval modes (BM25, dense, AST-aware hybrid) for a bounded language set (initially Python).
- Token-budgeted, provenance-preserving context construction.
- A retrieval-only evaluation mode as the primary research instrument, plus an optional secondary LLM answer-generation/citation-check capability.
- A reproducible evaluation protocol (pinned commits, annotated query/evidence set, defined metrics).

## Out of Scope

- Automatic code modification, pull-request creation, deployment, or unrestricted agent tool execution.
- Production multi-tenant hosting, authentication/security certification, or any claim that local inference guarantees privacy.
- Comprehensive support for every programming language or framework.
- Any claim that AST-aware hybrid retrieval outperforms baselines prior to measurement.
- Large-scale distributed indexing or commercial service-level availability.
- IDE/editor plugin integration (may be considered as future work, not part of this thesis scope).
