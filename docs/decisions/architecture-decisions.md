# Architecture Decisions

## Decision 001

**Title:** Use GitHub as project memory and collaboration source

**Context:** The project uses a ChatGPT + Codex + GitHub workflow.

**Decision:** GitHub stores the official project state.

**Reason:** Allows ChatGPT to review progress and provide future guidance.

## Decision 002

**Title:** Simple GitHub workflow for solo development

**Context:** The project is developed by one person with support from ChatGPT and Codex.

**Decision:** Use a simple main branch workflow with optional feature branches.

**Reason:** Reduce process overhead while maintaining project history and reproducibility.

## Decision 004

**Title:** Initial research methodology uses retrieval evaluation as primary contribution

**Context:** The thesis direction is AST-aware hybrid retrieval for software repository analysis (see [research-question.md](../research/research-question.md)). Answer generation, agentic behavior and IDE integration are excluded from the primary scope by [ADR-003](ADR-003-system-boundary.md).

**Decision:** The primary research contribution is a controlled retrieval-only evaluation (RQ1: Recall@k, MRR@10, nDCG@10 comparing BM25-only, dense-vector-only and AST-aware hybrid retrieval). Answer-generation quality (RQ2) is treated as a secondary, conditional study, not the primary contribution.

**Reason:** Evaluating retrieval independently of generation avoids confounding — LLM fluency cannot mask or compensate for retrieval errors — and keeps the study experimentally tractable for a solo Master's thesis within the bounded system scope already defined.
