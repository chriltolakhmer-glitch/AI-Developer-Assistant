# ADR-017: Hybrid Retrieval with FAISS, BM25, and Reciprocal Rank Fusion

## Status

Accepted for Phase 6.3 on 2026-09-27. Phase 6.3.1 implements the dense vector component only. Frozen-corpus execution remains conditional on the outstanding privacy review.

Phase 6.3.2 adds the lexical component under [ADR-018](ADR-018-bm25-retrieval.md). RRF execution remains unimplemented; the Phase 6.3.1 scope described below is historical.

## Context

The thesis compares dense-only, lexical-only, and AST-aware hybrid retrieval over identical pinned chunks and queries. Dense similarity and lexical identifier matching provide complementary signals, but their raw score scales are not directly comparable. The Phase 4 choices in ADR-007 and the technology selection record already specify exact FAISS search and fixed RRF parameters; this decision makes the hybrid implementation sequence explicit.

## Decision

Use hybrid retrieval combining:

1. Dense semantic retrieval using local CPU FAISS `IndexFlatIP` and normalized 384-dimensional MiniLM vectors.
2. Lexical retrieval using BM25 over the same eligible chunk inventory.
3. Equal-weight Reciprocal Rank Fusion (RRF), using one-based component ranks.

The frozen formula is `score(d) = 1/(60 + rank_dense(d)) + 1/(60 + rank_bm25(d))`; a missing component contributes zero. Each component supplies up to 50 candidates. Deduplicate by chunk ID, order by descending fused score then ascending chunk ID, and retain up to 50 results. Do not tune these settings on held-out evaluation queries. They are baseline parameters, not an optimality claim.

Build one dense index per repository and immutable commit. Insert vectors in ascending chunk-ID order, preserve all provenance in a source-free sidecar, and rank by descending cosine score then ascending chunk ID. Resolve exact score ties before applying the requested cutoff, including ties that cross the cutoff. No approximation, training, GPU search, or hosted storage is introduced.

Phase 6.3.1 implements vector-index construction, persistence, vector-query similarity search, and metadata mapping. BM25, RRF execution, natural-language query encoding, retrieval evaluation, LLMs, UI, and autonomous agents are outside this implementation step. A vector-query caller must supply an embedding from the same pinned model and representation contract.

## Consequences

- Exact search avoids approximate-neighbor settings as an experimental variable. Complete-row scoring and deterministic sorting add per-query ordering cost, acceptable for the bounded per-snapshot baseline.
- Index build and reload require the local clearance manifest associated with the embedding run. No corpus privacy approval is inferred from this implementation or its synthetic tests.
- Persist the index, metadata, source embedding-run identity, model/preprocessing contract, checksums, and runtime versions outside Git. Load only trusted local artifacts; checksums are corruption checks, not authenticity guarantees.
- Keep the future BM25 and dense baselines on the same accepted chunk set. The Phase 6.2 reject policy excludes empty/oversized chunks; coverage must be measured before evaluation.
- Next implement BM25 with an explicit identifier-tokenization policy, then RRF and evaluation. No retrieval-quality improvement is claimed before measurement.

## References

- [ADR-007: FAISS selection and fixed fusion parameters](ADR-007-vector-index-selection.md)
- [ADR-014: privacy policy](ADR-014-embedding-privacy-policy.md)
- [ADR-016: embedding implementation](ADR-016-embedding-implementation.md)
- [Technology selection](../research/technology-selection-final.md)
- [Vector retrieval implementation design](../architecture/vector-retrieval-design.md)
