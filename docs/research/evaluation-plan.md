# Phase 19.8 - Software prototype scope notice

**HISTORICAL PLAN - existing evaluation utilities remain active**

Current project scope: [Research software prototype validation](software-prototype-scope.md).

Maintain evaluation code, fixed metrics, existing pilot results and validation/reproducibility checks. Additional experiment designs, comparisons, parameter searches and scaling studies described below are paused. This plan does not expand the Humanize-only dataset or add benchmark questions.

## Preserved earlier document

# Evaluation Plan

**Status:** Phase 2 blueprint — no implementation exists yet. Operationalizes [research-question.md](research-question.md).

## Baseline System

**Baseline 1 — Keyword/BM25 retrieval:** Lexical search over the same indexed chunk units using a documented tokenization scheme. Reproducible BM25 implementation; no dense or structural signal used.

**Baseline 2 — Dense-vector retrieval:** Cosine (or index-native metric) similarity search using a single fixed, recorded embedding model over the same chunk units. No BM25 or graph/structural expansion.

Both baselines use identical chunk units (same chunking method as the proposed system, unless a separate chunking ablation is run) so that the retrieval *method* — not the chunk representation — is the controlled variable.

## Proposed System

**AST-aware hybrid retrieval:** AST-derived chunks (symbol, node kind, exact source spans) combined with dense retrieval and BM25/identifier evidence via a predeclared, fixed fusion strategy (e.g., Reciprocal Rank Fusion with fixed parameters). Fusion parameters and any query routing / bounded structural-neighbor expansion must be fixed *before* evaluation and reported as a separate factor — no tuning on held-out questions.

## Comparison Methodology

1. **Fixed shared conditions:** same pinned repository snapshots, same exclusions, same query set, same top-k, same hardware. For RQ2 only: same LLM, prompt, temperature and token budget across context strategies.
2. **Paired evaluation:** every query is run against all three retrieval strategies, enabling paired (not independent-sample) statistical comparison.
3. **Retrieval-only for RQ1:** no LLM call is made when measuring retrieval quality, so generation cannot mask or compensate for retrieval errors.
4. **Frozen configuration:** all baseline and proposed-system configurations are frozen before the held-out evaluation run; any deviation must be recorded.
5. **Ablation (if feasible):** text-window vs. AST chunks under dense-only and/or hybrid retrieval, to separate the effect of chunking from the effect of lexical-dense fusion.
6. **Aggregation:** report macro averages plus breakdowns by question category and repository-size stratum; use bootstrap confidence intervals (resampling unit stated) given the exploratory sample size.

## Evaluation Metrics

### Recall@k

**Definition:** Fraction of queries for which at least one gold-labeled relevant evidence item appears in the top-k retrieved results (also report evidence-level recall when multiple spans are required).

**Why suitable:** Recall@k directly measures whether the system surfaces *any* usable evidence at all within a bounded result list — the minimum condition for a developer or downstream LLM to find the right code. It is simple to interpret, comparable across retrieval strategies at a fixed k, and does not depend on rank position beyond the cutoff, making it robust to minor ranking noise while still testing coverage.

### MRR (Mean Reciprocal Rank, @10)

**Definition:** Average of the reciprocal rank of the first relevant result across all queries.

**Why suitable:** Many developer questions only need one correct piece of evidence to be useful (e.g., "where is X implemented"). MRR rewards placing that first relevant result as early as possible, which models realistic usage where a developer reads results top-down and often stops at the first correct one — a dimension Recall@k alone does not capture.

### nDCG (Normalized Discounted Cumulative Gain, @10)

**Definition:** Rank-sensitive gain metric using predeclared graded relevance labels (e.g., primary evidence vs. supporting/context evidence), normalized against the ideal ranking.

**Why suitable:** Not all relevant evidence is equally important — a primary implementation span is more valuable than a loosely related supporting file. nDCG accounts for both graded relevance and rank position, making it the most information-rich of the three metrics for judging whether the *best* evidence is ranked highest, not merely present.

Together, Recall@k (coverage), MRR (first-hit rank), and nDCG (graded rank quality) provide complementary views: a system could score well on one and poorly on another (e.g., high recall but poor ranking), so all three are reported rather than a single composite score.

### Secondary metrics (RQ2 only, if run)

- **Answer correctness:** human-rubric score against repository snapshot and gold evidence (factual correctness/completeness, unsupported claims, appropriate abstention).
- **Citation/span validity:** mechanical check that a cited path/line range exists in the pinned snapshot and overlaps the associated claim; report citation precision (supported cited claims / cited claims).
- **Cost:** query latency (p50/p95), indexing throughput, token counts, and generation latency — reported but not treated as primary research outcomes.

See [dataset-design.md](dataset-design.md) for the annotated benchmark this evaluation runs against, and [experiment-design.md](experiment-design.md) for the full experimental design.
