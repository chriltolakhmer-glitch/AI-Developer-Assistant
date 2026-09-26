# ADR-007: Select FAISS for the Research Vector Index

## Status

Accepted for the initial prototype on 2026-09-26, contingent on the documented clean-environment installation and behavior smoke check before implementation dependencies are frozen.

The declared Windows/Python 3.14.7 environment passed that gate on 2026-09-27 with FAISS 1.15.1 and NumPy 2.5.3. See [Phase 6.3.1 validation](../research/vector-retrieval-validation.md). Corpus privacy clearance remains a separate open gate.

## Context

[ADR-005](ADR-005-technology-selection.md) left FAISS versus Chroma open pending a pilot. The prototype compares BM25-only, dense-only, and hybrid retrieval over identical, immutable repository snapshots. Each query is scoped to one repository+commit. The study needs reproducible vector ranks and provenance; it does not need a general metadata-rich vector database.

## Decision

Use CPU FAISS `IndexFlatIP` with L2-normalized vectors for exact cosine ranking. Build one index per repository+commit snapshot. Persist the index together with a versioned sidecar that maps vector positions to deterministic chunk IDs and maps those IDs to source metadata (repository, commit, path, symbol, line span, and content hash). Do not use approximate indexes, GPU indexes, or index training in the primary comparison. Fix stable chunk-ID ordering for ties and retain library/index configuration in each run manifest.

Keep embeddings local using `sentence-transformers/all-MiniLM-L6-v2` at immutable revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, as specified in [technology-selection-final.md](../research/technology-selection-final.md). Fix equal-weight RRF to rank constant 60 and a 50-result input window for each of BM25 and dense retrieval; retain up to 50 fused candidates and evaluate declared cutoffs consistently. These settings are frozen before held-out runs and are not described as tuned or optimal.

## Rationale

Normalized inner product implements cosine similarity and `IndexFlatIP` returns exact results for the stored vectors, avoiding ANN approximation settings as an experimental confound. Per-snapshot indexes provide repository/commit isolation directly, while the sidecar preserves full metadata without FAISS-native filtering. The bounded sample does not justify Chroma's persistence and metadata conveniences as a reason to add a database layer. FAISS is a mature vector-search library and its current CPU distribution documents Windows support, but the actual study environment must pass an installation/import and save/load smoke test first.

## Consequences

- The retrieval prototype must implement and validate index/sidecar consistency, deterministic ordering, normalization, save/load equivalence, and snapshot scoping.
- Record exact FAISS, NumPy, model, SentenceTransformers, Python, OS, and device versions. Rebuild the index after a model or chunk change.
- The MiniLM model is general-purpose and truncates inputs after 256 word pieces; the chunking/input-length policy must be explicit and truncation logged.
- If supported FAISS installation fails in the declared environment, pause and create a superseding ADR before choosing another library. Do not substitute Chroma silently.
- This decision makes no claim that FAISS or the chosen embedding model improves retrieval relevance; that is measured by RQ1.

## Alternatives considered

### Chroma

Chroma provides persistent collections and query-time metadata predicates, but each evaluation query already selects a single repository+commit index. A sidecar handles metadata while avoiding an additional database/persistence layer and gives the dense baseline explicit exact-search behavior.

### Other FAISS index types

Approximate or trained index types could reduce query cost at larger scale, but introduce more settings and possible approximation error. They are not needed for this corpus and are excluded from the primary experiment.

## References

- [FAISS repository and documentation](https://github.com/facebookresearch/faiss) and [installation guide](https://github.com/facebookresearch/faiss/blob/main/INSTALL.md).
- [FAISS CPU package metadata](https://pypi.org/project/faiss-cpu/), checked 2026-09-26.
- [Chroma metadata-filter documentation](https://docs.trychroma.com/docs/querying-collections/metadata-filtering).
- [Phase 4 technology selection](../research/technology-selection-final.md).
