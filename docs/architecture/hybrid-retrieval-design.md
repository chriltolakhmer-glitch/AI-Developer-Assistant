# Phase 6.3.3 — Hybrid Retrieval Design

## Status

Implemented design for snapshot-scoped dense and lexical retrieval with Reciprocal Rank Fusion. The design does not add an LLM, UI, agents, or evaluation experiments.

## Architecture

```text
                         Query
                           |
                +----------+----------+
                |                     |
                v                     v
             FAISS                  BM25
                |                     |
                +----------+----------+
                           |
                           v
                          RRF
                           |
                           v
                    Hybrid Results
```

A text query is normalized once, encoded locally with the pinned embedding model, and sent to the dense FAISS channel. The same query text is sent to the local BM25 channel. Each channel returns at most 50 ranked `SearchResult` values for the same repository and commit. RRF combines ranks and returns at most 50 `FusionResult` values.

## Channel responsibilities

### Dense retrieval

FAISS provides semantic matching over normalized embedding vectors. It is useful when query wording differs from source identifiers or when conceptual similarity is more informative than exact term overlap. The index is exact `IndexFlatIP` with deterministic score-descending and chunk-ID tie ordering.

### Lexical retrieval

BM25 provides identifier-aware lexical matching over the same accepted chunk inventory. It preserves exact words and identifier components, making it useful for function names, class names, symbols, and distinctive terms that dense representations may soften.

### Reciprocal Rank Fusion

RRF combines channel rank evidence rather than raw scores:

`RRF(d) = sum(1 / (60 + rank_channel(d)))`

A chunk appearing in both channels receives contributions from both ranks. A chunk appearing in only one channel retains that channel's contribution. Channel weights are equal, so neither retriever is privileged in the baseline.

Raw-score fusion is avoided because FAISS cosine scores and BM25 scores have different scales, distributions, and meanings. Normalizing or calibrating them would introduce additional choices and potential tuning confounds. Rank fusion requires only the declared rank positions and is therefore easier to reproduce across the two channels.

## Provenance preservation

Every result retains the immutable `EmbeddingMetadata` associated with its chunk: repository ID, commit SHA, file path, entity type, qualified name, source line range, content hash, and tokenizer count. `FusionResult` additionally records each channel's rank and original score in `RankContribution` values. The fused output therefore preserves both the source location and the evidence used to produce its rank.

The hybrid constructor rejects channels with different snapshots, chunk inventories, provenance metadata, embedding runs, or runtime contracts. This prevents a result set from silently combining incompatible artifacts.

## Fixed parameters

| Parameter | Baseline |
|---|---|
| RRF constant | 60 |
| Channel weights | Equal |
| Candidates per channel | 50 |
| Maximum fused results | 50 |
| Tie breaking | Fused score descending, then chunk ID ascending |

## Scope and limitations

The implementation is local and privacy-gated. It does not execute full-corpus indexing, invoke an LLM, generate answers, provide a UI, or run evaluation experiments. Corpus execution remains blocked until privacy clearance is resolved.

## Related records

- [ADR-019: RRF hybrid ranking](../decisions/ADR-019-rrf-hybrid-ranking.md)
- [ADR-007: vector index selection](../decisions/ADR-007-vector-index-selection.md)
- [ADR-014: embedding privacy policy](../decisions/ADR-014-embedding-privacy-policy.md)
