# Bounded parent-child retrieval mode

Phase 15 adds the opt-in `ParentChildSearch` API. Existing `BM25Search`,
`VectorIndex`, `HybridSearch`, their persisted artifact contracts, and evaluation
code are unchanged. This implementation is restricted to the pinned Humanize
pilot and exact frozen chunk-map digest. It does not authorize benchmark expansion.

## Build and query

```python
from src.retrieval import ParentChildSearch

search = ParentChildSearch.build(
    canonical_chunks,              # tuple[CodeChunk, ...], unchanged parents
    chunk_map_path=frozen_map_path, # external, read-only frozen chunk map
    sources=canonical_file_text,    # dict[relative_path, full canonical source]
    model_cache=offline_cache_path,
)
results = search.search(query)     # exactly five unique canonical parents
details = search.search_with_details(query)
```

Build checks the map digest, all 44 IDs, repository/commit, source identities,
spans and complete module text before loading the cached model. No questions,
annotations, expected answers or relevance grades are build/search inputs.
The caller supplies canonical LF-normalized text matching the source hashes;
drift fails closed. Caches/maps must reside outside the project. Build performs
local embedding inference; the existing loader fixes the model revision,
offline operation and deterministic CPU settings.

Accepted source parents use one unchanged passage. Longer parents use the
validated 224-token payload / 32-token overlap policy, with exact character
offsets and re-tokenization to enforce 256 tokens including special tokens.
Complete parent characters are covered. Child IDs are representation IDs
containing parent identity, source offsets, content hash and splitter version;
they never replace parent IDs or gold annotations.

The index is in memory. It intentionally does not write children into the legacy
one-vector-per-chunk storage schema or create FAISS/BM25 indexes. Every child
vector is scored with normalized float32 cosine dot products. Per-parent maxima
and deterministic parent-ID ties produce the dense parent ranking. Child-score
ties use child ID. No raw child top-k cutoff can starve distinct parents.

## Bounded direct-call expansion

The first three dense parent results are preserved. Up to two unseen direct
callees of these seeds are appended in dense parent-score order, then remaining
slots are filled from the dense ranking. This is one hop only, and final output
always contains five distinct parents. `k` values other than 5 are rejected;
configuration changes require a separately validated mode/version.

Source-only AST and symbol-table resolution supports top-level functions, local
function names and absolute/relative `from` import aliases within the supplied
parent inventory. Local assignments/parameters, ambiguous module bindings,
nested definition bodies, attribute calls and unresolved names are skipped.
Modules have no outgoing edges. This is a bounded static approximation, not a
general Python call graph: dynamic rebinding, complex scopes and runtime
dispatch are not inferred. The candidate graph contains only frozen parents.

## Evidence and evaluation compatibility

`ParentEvidence` extends the existing `SearchResult`. Its `chunk_id`, metadata
span/hash, and `content` describe the complete original parent. Its tokenizer
count can exceed 256 because that parent is not encoded as one model input.
Do not feed this metadata into legacy accepted-embedding artifact validators.
`winning_child_id`, `dense_rank` and `expansion_from` explain how it was selected.
`score` remains the dense cosine score; after expansion final rank is not
necessarily score-descending. Consumers must use `rank`, not re-sort by score.

`ParentChildResponse` provides all child hits, all dense parents, ordered
expansion candidates and source-located call edges for auditing. All result
records are frozen; vector backing memory is read-only. Query text must be
nonempty and at most 256 tokenizer tokens; silent truncation is forbidden.

The unchanged `RetrievalEvaluator` accepts these results because IDs, snapshot
metadata and contiguous ranks retain the existing interface. Its aggregate
recall is a macro average over questions. The pilot's reported evidence recall
is micro-averaged over 20 occurrences (13 primary / seven supporting). Report
these separately rather than changing evaluator semantics or denominators.

## Validation boundary

Synthetic tests cover splitting/coverage, immutable IDs and contexts, expansion
budget/deduplication/one-hop behavior, aliases and shadowing, ties, invalid
queries/maps and evaluator compatibility. External Phase 15 runs exercise all
12 frozen questions through the public build/query API, reproduce the selected
Phase 14.8 prototype, compare independent builds and preserve original baselines.

Corpus source, child passages, vectors, benchmark questions and experiment
outputs stay in external research storage. This mode is an implementation of a
pilot-selected strategy, not independent validation or a general retrieval
service. Persistence, concurrency, large-corpus performance, answer generation
and expanded evaluation are outside this change.
