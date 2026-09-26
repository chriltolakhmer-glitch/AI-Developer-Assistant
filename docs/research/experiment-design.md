# Experiment Design

**Status:** Phase 2 blueprint — no implementation exists yet. Operationalizes [research-question.md](research-question.md) using the dataset defined in [dataset-design.md](dataset-design.md) and the metrics defined in [evaluation-plan.md](evaluation-plan.md).

## Experiment

**Baseline:** Traditional vector-based RAG — dense-vector retrieval only (single fixed embedding model, cosine/index-native similarity), no lexical or structural signal. A keyword/BM25-only baseline is run alongside it (see [evaluation-plan.md](evaluation-plan.md)) so the proposed system is compared against two distinct baselines, not one.

**Proposed:** AST-aware hybrid retrieval — AST-derived chunks with symbol/node-kind/source-span metadata, combining dense retrieval and BM25/identifier evidence through a fixed, predeclared fusion strategy.

Both conditions run against the same pinned repositories and the same annotated query benchmark, in retrieval-only mode (no LLM call) for the primary comparison.

## Variables

### Independent Variables

- **Retrieval strategy** (primary manipulated variable): BM25-only / dense-vector-only / AST-aware hybrid.
- **Question category:** architecture understanding / code navigation / dependency understanding / bug investigation.
- **Repository size stratum:** small / medium / large.
- *(Ablation, if run)* **Chunking method:** text-window vs. AST-aware chunks, crossed with dense-only and/or hybrid retrieval, to isolate chunking effects from fusion effects.
- *(RQ2 only, conditional)* **Context strategy:** flat top-ranked chunk context vs. structurally selected (AST-aware hybrid) context, at a fixed token budget.

### Dependent Variables

- **Recall@k**, **MRR@10**, **nDCG@10** (primary, per query, aggregated by category/stratum).
- Evidence-level recall (when multiple gold spans are required).
- *(RQ2 only)* Answer-correctness rubric score, citation/span validity, citation precision.
- *(Secondary, reported not central)* Query latency (p50/p95), indexing time/throughput, memory, index size, token counts.

## Expected Results

Per the hypotheses in [research-question.md](research-question.md):

- AST-aware hybrid retrieval is expected to outperform both single-signal baselines on Recall@k, MRR@10 and nDCG@10, with the largest advantage on **identifier-heavy** and **cross-file dependency** questions, where lexical/symbol matching and dense semantic similarity individually miss evidence the other captures.
- Advantage is expected to be smaller or absent for purely conceptual/architecture questions where dense retrieval alone may already perform well.
- Repository size is expected to affect indexing/query cost but is not expected to reverse the relative ranking of retrieval strategies (tested only if RQ3 is in scope).
- These are stated expectations to be tested, not guaranteed outcomes; a null result (H1₀, no distinguishable difference) is a valid and reportable finding given the exploratory sample size.

## Threats to Validity

- **Construct validity:** "Relevant code" and answer correctness depend on the annotation rubric; file-level relevance may overstate span-level precision. Mitigated by predefining the annotation unit (span/symbol) and rubric before annotation begins.
- **Internal validity:** Retrieval variants could differ in chunking, embedding model, or token budget rather than purely in fusion method. Mitigated by freezing shared configuration and running the chunking ablation where feasible.
- **External validity:** Nine Python repositories cannot represent all languages, domains, sizes, or developer question styles; conclusions must be scoped to the studied sample and language.
- **Annotation bias:** A single primary annotator may introduce subjective judgment. Mitigated by a predeclared ≥20% second-reviewer spot check where available; documented as a limitation otherwise.
- **Model/tooling variability:** Embedding model versions, library updates, or nondeterministic library behavior could shift results between runs. Mitigated by pinning and recording all model/library versions and re-running key comparisons where feasible.
- **Fusion-tuning leakage:** Tuning the hybrid fusion parameters on the held-out benchmark would inflate its apparent advantage. Mitigated by freezing fusion parameters before evaluation and using a pilot/held-out split.
- **Generation confound (RQ2 only):** If answer generation is evaluated, LLM fluency could be mistaken for correctness. Mitigated by keeping RQ1 retrieval-only and using a human rubric plus mechanical citation-span validation for RQ2, rather than LLM-as-judge alone.

## Reporting

Report macro averages, per-category and per-size-stratum breakdowns, bootstrap confidence intervals (resampling unit stated), and qualitative failure analysis (parser failures, symbol ambiguity, lexical misses, embedding misses, stale/incorrect spans, context-budget truncation). Report negative/null results and any protocol deviations explicitly.
