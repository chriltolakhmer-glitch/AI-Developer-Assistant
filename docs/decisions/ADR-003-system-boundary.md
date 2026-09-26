# ADR-003: Define the Initial System Boundary of AI Developer Assistant

## Status

Accepted (Phase 1 blueprint)

## Context

Prior research identified three possible thesis directions (a full codebase-understanding assistant, an AST-aware hybrid retrieval system, and an autonomous software-engineering agent). Without an explicit boundary, implementation risks growing into an unscoped "do everything" system, which would confound evaluation and exceed a solo Master's-thesis budget.

## Decision

The initial system boundary is set as follows:

**In scope:**
- Repository ingestion of a pinned, immutable commit snapshot (read-only; never modifies the source tree).
- AST-aware chunking for an initially Python-only language scope, with a labeled text fallback.
- Three comparable retrieval strategies: BM25 (lexical), dense-vector, and AST-aware hybrid.
- Token-budgeted, provenance-preserving context construction.
- A retrieval-only evaluation mode as the primary research instrument (Recall@k, MRR, nDCG, source-span accuracy).
- An optional, secondary LLM answer-generation capability with mechanical citation/span validation.
- A reproducible evaluation protocol (pinned commits, annotated query/evidence dataset, versioned configuration).

**Out of scope:**
- Any autonomous code modification, pull-request creation, deployment, or unrestricted agent tool execution.
- Multi-language, production-grade, or multi-tenant support.
- IDE/editor plugin integration (deferred as potential future work).
- Claims of retrieval superiority prior to measurement.
- Distributed/large-scale infrastructure or commercial availability guarantees.

## Reason

This boundary aligns with the recommended thesis direction (AST-aware hybrid retrieval, Option B) identified during research analysis: it is experimentally tractable for a solo developer, directly targets the documented research gaps (chunking fidelity, retrieval benchmarking, context budgeting, citation verification), and defers higher-risk/higher-scope work (full agent behavior, IDE integration) to explicit future work rather than silently expanding project scope.

## Consequences

- `docs/requirements/system-requirements.md` and `docs/architecture/system-architecture-v1.md` must stay within this boundary; any expansion requires a new ADR.
- Implementation (`src/`) must not begin until this boundary and the requirements/architecture blueprint are reviewed.
- Future ADRs should reference this boundary when evaluating scope-expanding proposals (e.g., adding a new language, enabling write actions, or adding IDE integration).
