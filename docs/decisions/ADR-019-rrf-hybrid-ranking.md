# ADR-019: Reciprocal Rank Fusion Hybrid Ranking

## Status

Accepted for Phase 6.3.3 on 2026-09-27. This is a fixed retrieval baseline; it is not tuned against evaluation results.

## Context

The assistant has two snapshot-scoped retrieval channels: dense FAISS search and lexical BM25 search. Their scores are not directly comparable: dense results use normalized inner-product similarity, while BM25 results use a positive lexical relevance score whose scale depends on term frequency and document statistics. The hybrid baseline needs a deterministic way to combine evidence without introducing score calibration as an experimental confound.

## Decision

Use Reciprocal Rank Fusion to combine the dense and lexical rankings. The implementation accepts the validated result lists, preserves their provenance and channel contributions, and returns one deterministic hybrid ranking.

## Parameters

| Parameter | Decision |
|---|---:|
| RRF constant | 60 |
| Channel weights | Equal |
| Candidates per channel | 50 |
| Maximum fused results | 50 |
| Tie breaking | Fused score descending, then stable chunk ID ascending |

For a chunk `d`, the baseline score is the equal-weight sum:

`score(d) = sum(1 / (60 + rank_channel(d)))`

Only ranks contribute to the fused score. A missing channel contributes zero. Duplicate chunk IDs within one channel are invalid; the same chunk across channels is combined once, provided its provenance agrees.

## Rationale

RRF is appropriate because it combines ordinal evidence while avoiding assumptions about the relationship between FAISS and BM25 score scales. Equal weights keep the first hybrid comparison transparent and avoid empirical weighting before evaluation is authorized. Fixed candidate and output windows bound the experiment and match the previously declared retrieval protocol.

The compatibility gate requires identical repository/commit scope, chunk IDs, metadata, and embedding run identity across channels. This protects provenance and prevents accidental cross-snapshot fusion.

## Consequences

- The query path must execute dense and lexical searches with a candidate limit of 50 before fusion.
- The fused result is capped at 50 and ranks are reassigned deterministically from one.
- Consumers can inspect both fused scores and per-channel `RankContribution` evidence.
- Raw score calibration, learned weights, ANN tuning, LLM generation, UI behavior, agents, and evaluation experiments remain outside this decision.
- A future weighted or score-calibrated method requires a separate decision and a controlled comparison against this baseline.

## References

- [Hybrid retrieval design](../architecture/hybrid-retrieval-design.md)
- [ADR-007: vector index selection](ADR-007-vector-index-selection.md)
- [ADR-015: embedding model selection](ADR-015-embedding-model-selection.md)
