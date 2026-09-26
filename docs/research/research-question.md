# Research Question

**Status:** Phase 2 blueprint — no implementation exists yet. This document builds directly on [research-summary.md](research-summary.md) and [ADR-003 system boundary](../decisions/ADR-003-system-boundary.md).

## Main Research Question

**RQ1 (primary):** How does AST-aware hybrid retrieval affect the relevance of retrieved source evidence for developer questions about Python repositories, compared with keyword-only (BM25) and dense-vector-only retrieval?

## Sub Research Questions

- **RQ2 (secondary, conditional on time):** At a fixed prompt-token budget, does structurally selected context improve answer correctness and source-reference (citation) validity compared with a flat top-ranked chunk context?
- **RQ3 (optional, not required):** How does repository size influence the indexing and query-time cost (latency, memory, storage) of the three retrieval strategies?

RQ1 is the required primary contribution. RQ2 is run only if RQ1 and dataset annotation finish on schedule. RQ3 is optional and may be dropped entirely without weakening the thesis.

## Expected Contribution

- A controlled, reproducible comparison of three retrieval strategies (BM25, dense-vector, AST-aware hybrid) over the same pinned Python repositories and the same manually annotated query-to-evidence benchmark.
- Metrics broken down by question category (architecture understanding, code navigation, dependency understanding, bug investigation) and by repository-size stratum.
- A documented failure analysis (parser failures, symbol ambiguity, lexical misses, embedding misses, stale/incorrect spans, context-budget truncation).
- If RQ2 is run: a secondary, human-graded study of answer correctness and citation validity under a fixed context-token budget.

The contribution is the **measured comparison and protocol**, not a claim that AST-aware hybrid retrieval is inherently superior — that is the hypothesis to be tested.

## Hypothesis

- **H1 (primary):** AST-aware hybrid retrieval achieves higher Recall@k, MRR@10 and nDCG@10 than both BM25-only and dense-vector-only retrieval, particularly for identifier-heavy and cross-file dependency questions, at a fixed top-k and equal chunking basis.
- **H2 (secondary, conditional):** Under a fixed context-token budget, structurally selected context (AST-aware hybrid evidence) produces higher answer-correctness and citation-validity scores than a flat top-ranked chunk context, using the same model and prompt.
- **Null hypotheses:** No statistically distinguishable difference between AST-aware hybrid retrieval and the baselines on the primary metrics (H1₀); no distinguishable difference in answer correctness/citation validity between context strategies (H2₀). Both must be reported if observed — a null result is a valid thesis outcome given the exploratory sample size.

See [evaluation-plan.md](evaluation-plan.md), [dataset-design.md](dataset-design.md), and [experiment-design.md](experiment-design.md) for how this question is operationalized.
