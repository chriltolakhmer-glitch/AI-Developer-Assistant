# Phase 6.3.1 — Vector Retrieval Validation

Recorded on 2026-09-27. Validation uses generated Python fixtures and synthetic normalized vectors only; no frozen-corpus index was created and no corpus privacy clearance or retrieval-quality result is claimed.

## Environment gate

A fresh external environment at `C:\Apps\Temp\Phase6.3\smoke-venv` installed the supported Windows wheel for `faiss-cpu==1.15.1`, `numpy==2.5.3`, and `packaging==26.3`, using Python 3.14.7 on Windows Server 2022 (`10.0.20348`). No custom native build or alternative vector store was needed.

The clean-environment smoke check imported FAISS, created a 384-dimensional CPU `IndexFlatIP`, added three orthogonal unit vectors, verified that the matching query ranked its row first with score 1, persisted/reloaded the index, and asserted exact equality of scores and row IDs. **PASS.** This satisfies ADR-007's Windows installation and behavior gate for this declared runtime.

The application suite used the external Phase 6.2 environment plus the same FAISS version. [requirements-retrieval.txt](../../requirements-retrieval.txt) includes all Phase 6.2 dependency pins and adds FAISS. `pip check` reported no broken requirements.

## Test results

Command: `python -m unittest discover -s tests -v`, with `EMBEDDING_MODEL_CACHE` pointing to the previously acquired external pinned MiniLM cache.

- **49 tests passed**, no failures or skips, in 8.526 seconds (informational runtime).
- **15 retrieval tests** exercised real FAISS, including exact cosine order, negative similarities, immutable metadata preservation, one-based ranks, cutoff ties, repeatability, and query normalization.
- Persistence/reload preserved rankings and byte-identical index, sidecar, and manifest artifacts in the tested runtime, including Unicode output paths.
- Snapshot isolation was checked both for absent snapshots and for selecting/remapping one repository from a combined embedding run.
- Validation rejected invalid query shape/norm/finiteness, invalid `k`, empty snapshot outputs, changed/revoked clearance, mismatched embedding contracts, corrupted artifacts, altered provenance, wrong FAISS metrics/index types, unnormalized index vectors, and incompatible runtime versions.
- Corrupted index checksums failed before native deserialization. A socket-blocked test covered construction, save, load, and search. Artifact writes inside the thesis project were rejected.
- The existing 34 tests also passed, including actual offline MiniLM inference and token-boundary checks.

Test-only clearance files identify generated fixtures using frozen repository identities to exercise the public API. They are temporary, never retained as corpus audit records, and do not represent review of upstream source.

## Readiness and limitations

The dense index component is implemented and tested. It accepts compatible numeric query embeddings; natural-language query encoding and relevance evaluation are not implemented in this milestone. Deterministic ranking is validated under the pinned runtime, not promised bitwise across different hardware or libraries.

Phase 6.3.2 can implement BM25 with a declared tokenization policy and the same accepted chunk set, followed by RRF integration using the parameters in [ADR-017](../decisions/ADR-017-hybrid-retrieval.md). The frozen corpus remains blocked pending its secret/privacy disposition. No LLM, UI, autonomous agents, BM25, or RRF execution was added.
