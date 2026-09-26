# ADR-016: Local Embedding Implementation Before Retrieval Indexing

## Status

Accepted for Phase 6.2 on 2026-09-27. Corpus execution remains conditional on the privacy review in ADR-014.

## Decision

Implement local embedding generation before retrieval indexing.

Use `sentence-transformers/all-MiniLM-L6-v2` at the immutable revision selected in ADR-015, on CPU with one PyTorch thread, seed zero, deterministic algorithms, float32 inference, and L2-normalized 384-dimensional output. Acquire public weights separately; normal loading uses only local files, with telemetry and network access disabled through library settings. Tests additionally prohibit socket connections.

The representation `source-strip-v1` is the exact chunk content with outer whitespace stripped, without path, symbol, or retrieval instructions prepended. Content identity is still calculated from the original unmodified source. Count tokenizer special tokens within the 256-token ceiling. Reject oversized and empty inputs with explicit chunk lineage; do not split or silently truncate. This deliberately reduces coverage for long entities and must be reported in future corpus results.

Accept only frozen corpus identities with complete local privacy clearance. Synthetic fixtures exercise the private transformation core without claiming corpus clearance. Do not introduce a production bypass flag.

Persist an ordered NumPy float32 matrix, source-free JSON metadata, a rejection ledger, and a versioned run manifest with artifact hashes outside Git. A run manifest is written last and denotes a completed artifact set. Output directories must be new, preventing accidental replacement of prior runs.

## Consequences

- Model acquisition and inference are separate steps; no hosted inference or source upload is used.
- Repeated runs with the same software, batch size, CPU settings, and inputs have stable metadata and vector ordering. Timestamps identify runs separately; cross-hardware bitwise equality is not promised.
- The artifact format can supply normalized vectors and row mappings to future FAISS indexing. No FAISS, BM25, RRF, LLM, query embedding, or UI is implemented.
- The Phase 5.4.1 corpus privacy findings remain open. Synthetic performance does not establish corpus throughput, retrieval quality, or indexing authorization.

## References

- [Privacy policy](ADR-014-embedding-privacy-policy.md)
- [Model selection](ADR-015-embedding-model-selection.md)
- [Implementation and runtime protocol](../architecture/embedding-implementation.md)
