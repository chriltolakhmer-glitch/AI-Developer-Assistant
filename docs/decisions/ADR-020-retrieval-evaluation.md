# ADR-020: Retrieval Metrics as the Primary Evaluation Method

## Status

Accepted for Phase 7 on 2026-09-27. Full corpus experiments remain blocked until privacy clearance is resolved.

## Context

The thesis compares a FAISS dense baseline with a FAISS + BM25 + RRF hybrid retrieval system. The research question concerns whether the hybrid method surfaces relevant code evidence more effectively. Measuring answer generation at this stage would introduce an LLM, prompt, and judge confound and would not directly establish retrieval quality.

The project already defines a frozen corpus, AST semantic chunks, a deterministic dense index, lexical index, and fixed RRF parameters. Evaluation therefore needs a retrieval-only framework that accepts manually annotated gold evidence and produces reproducible per-query and aggregate metrics.

## Decision

Use retrieval metrics as the primary thesis evaluation method. Evaluate both systems on the same versioned benchmark and snapshot-scoped results, using paired queries and macro aggregation.

The primary metrics are:

1. Recall@K for evidence coverage, with `K` reported at declared cutoffs such as 1, 5, and 10.
2. MRR for the rank of the first relevant chunk.
3. nDCG@10 for rank-sensitive graded relevance.

Use a local JSON benchmark loader with unique query IDs, repository/commit identity, query text, and positive integer relevance grades keyed by chunk ID. Reject results from a different snapshot. Keep benchmark source-derived artifacts outside Git under the privacy policy.

## Rationale

Recall measures whether the needed evidence is surfaced, MRR measures how quickly the first useful evidence appears, and nDCG distinguishes primary evidence from supporting context. Together they cover complementary aspects of retrieval quality without collapsing the experiment into one opaque score.

Retrieval-only evaluation isolates the independent variable, retrieval strategy. It avoids LLM generation quality masking retrieval errors and is directly reproducible from ranked result lists. Paired evaluation controls for question difficulty because each system sees the same benchmark case.

## Consequences

- The evaluator must validate rank order, snapshot identity, gold labels, and deterministic report ordering.
- The dense baseline and hybrid system must use identical chunks, snapshots, benchmark questions, and metric cutoffs.
- Primary results are macro averages with per-query records preserved for paired analysis and failure inspection.
- Full corpus execution, benchmark annotation, and any held-out run require privacy clearance first.
- LLM, UI, agents, answer scoring, and generation experiments remain outside this decision.
- Any change to metric definitions, relevance grades, benchmark split, or RRF configuration requires a new decision or an explicit protocol revision before held-out evaluation.

## References

- [Evaluation framework](../research/evaluation-framework.md)
- [Evaluation plan](../research/evaluation-plan.md)
- [Benchmark design](../research/benchmark-design.md)
- [ADR-014: embedding privacy policy](ADR-014-embedding-privacy-policy.md)
- [ADR-019: RRF hybrid ranking](ADR-019-rrf-hybrid-ranking.md)
