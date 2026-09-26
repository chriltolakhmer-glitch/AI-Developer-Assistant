# Phase 7 — Retrieval Evaluation Framework

## Research experiment

Phase 7 evaluates retrieval quality without answer generation. The controlled comparison uses the same pinned repository snapshots, AST semantic chunks, benchmark questions, privacy-approved artifacts, and top-k cutoffs for both systems. The independent variable is retrieval strategy:

- **Baseline:** FAISS dense retrieval using the pinned local embedding model.
- **Proposed:** FAISS dense retrieval plus BM25 lexical retrieval combined with fixed Reciprocal Rank Fusion.

Every benchmark question is evaluated against both systems as a paired observation. The benchmark loader keeps question identity, repository/commit scope, query text, and manually reviewed graded relevant chunk IDs together. Gold labels remain separate from retriever output in the research-data workflow.

## Baseline system

The baseline calls snapshot-scoped FAISS `IndexFlatIP` over normalized embedding vectors and returns a deterministic ranked list. It uses no lexical channel and no LLM. Its purpose is to measure the retrieval quality supplied by semantic similarity alone.

## Proposed system

The proposed system calls the existing local hybrid search path: the text query is encoded for FAISS, searched lexically by BM25, and fused by RRF. RRF uses constant `60`, equal channel weights, 50 candidates per channel, and a maximum of 50 fused results. These parameters are frozen before held-out evaluation.

## Evaluation workflow

1. Load a versioned local JSON benchmark with unique query IDs and positive graded relevance labels.
2. Verify that every retriever result belongs to the benchmark case's repository and commit.
3. Run the dense baseline and hybrid system with identical benchmark cases and cutoffs.
4. Calculate per-query Recall@K, reciprocal rank, and nDCG.
5. Aggregate macro means by system, then report paired results overall and by question category or repository stratum when those fields are added to the benchmark schema.
6. Preserve configuration, model/index identities, benchmark hash, metric outputs, and run metadata in local research artifacts; commit only aggregate non-sensitive reports.

The evaluator is a pure framework over a retriever callable and does not build indexes, access checkouts, call external services, or run the full corpus.

## Metrics

### Recall@K

For a query with gold relevant set $G$, Recall@K is the fraction of gold evidence items retrieved in the first $K$ positions:

$$
Recall@K = \frac{|G \cap retrieved_{1:K}|}{|G|}
$$

This measures coverage. A one-item gold set becomes a binary hit rate, while multi-evidence questions receive partial credit.

### MRR

Mean Reciprocal Rank uses the rank of the first relevant result:

$$
MRR = \frac{1}{N} \sum_{i=1}^{N} \frac{1}{rank_i}
$$

Queries with no relevant result contribute zero.

### nDCG@K

nDCG uses graded relevance labels, rewarding highly relevant evidence near the top and normalizing by the ideal ranking:

$$
nDCG@K = \frac{DCG@K}{IDCG@K}
$$

The implementation uses gain $2^{relevance}-1$ and logarithmic rank discounting. The primary report uses nDCG@10.

## Determinism and validity controls

- Benchmark query IDs and relevance entries are validated and sorted deterministically.
- Retrieval result ranks must be contiguous, one-based, and unique by chunk ID.
- Cross-snapshot results are rejected rather than silently scored.
- System reports are emitted in sorted system-name order.
- Dense and hybrid runs share the same benchmark, snapshot, chunk, and metric configuration.
- Privacy clearance is a prerequisite for full corpus execution. No full corpus experiment is run by Phase 7 framework tests.

## Scope exclusions

This phase does not implement or evaluate an LLM, UI, agents, answer quality, citation quality, or generation latency. Those are separate future concerns and must not confound the primary retrieval comparison.

## Related records

- [ADR-020: retrieval evaluation](../decisions/ADR-020-retrieval-evaluation.md)
- [Evaluation plan](evaluation-plan.md)
- [Benchmark design](benchmark-design.md)
- [ADR-019: RRF hybrid ranking](../decisions/ADR-019-rrf-hybrid-ranking.md)
