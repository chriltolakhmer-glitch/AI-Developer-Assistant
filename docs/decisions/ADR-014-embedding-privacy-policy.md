# ADR-014: Embedding Privacy and Data-Handling Policy

## Status

Accepted as the Phase 6.1 embedding policy on 2026-09-27. Operational embedding authorization remains conditional on the unresolved corpus secret/privacy audit described by [ADR-008](ADR-008-source-code-privacy.md) and [ADR-013](ADR-013-dataset-snapshot-freeze.md).

## Context

Phase 5 produces AST-derived semantic chunks from fixed public repository snapshots. Phase 6 will transform those chunks into vector representations for a retrieval experiment. A vector is derived from source code and may preserve information about that source; public upstream availability does not make source, chunks, vectors, indexes, or metadata unrestricted research data.

The study requires a reproducible baseline without sending source-derived data to an embedding provider, hosted notebook, hosted vector database, telemetry service, or LLM. The policy must also distinguish a documented processing rule from authorization to process the currently frozen corpus.

## Decision

### 1. Source code processing policy

- Process only the nine SHA-pinned snapshots approved by [ADR-006](ADR-006-corpus-selection.md) and frozen by [ADR-013](ADR-013-dataset-snapshot-freeze.md).
- Treat checkouts and parser/chunker outputs as read-only, source-derived research data. Do not modify upstream files or place source, raw chunks, or source excerpts in Git.
- Before embedding a snapshot, complete and record the secret/credential disposition and personal/confidential-data review required by [ADR-008](ADR-008-source-code-privacy.md). A successful parse or chunk count is not privacy clearance.
- Exclude a file, repository, or derived artifact when the audit cannot establish that processing is permitted. Record exclusions and count changes in a local, access-controlled audit record.
- Preserve repository, commit, path, symbol, line-span, and content-hash provenance for every eligible chunk without copying source text into routine logs.

### 2. Embedding generation policy

- Generate embeddings only on the researcher's controlled local machine using the pinned model configuration in [ADR-015](ADR-015-embedding-model-selection.md).
- Use the same model revision, text representation, tokenizer behavior, input-length policy, normalization, and software versions for corpus chunks and later queries.
- Enforce the model input limit explicitly. Do not silently truncate a semantic chunk; record a deterministic split/rejection decision and the resulting chunk lineage before embedding.
- L2-normalize output vectors for the planned cosine-similarity baseline. Store model identity, dimensions, preprocessing policy, runtime, device, and generation timestamp in a versioned run manifest.
- Embedding generation is a batch transformation over approved chunks. It does not authorize retrieval, FAISS construction, query processing, or LLM use; those require their own implementation and validation steps.

### 3. External service restrictions

- Do not send source code, chunks, queries containing source-derived details, embeddings, metadata, audit findings, or experiment results to hosted embedding APIs, hosted LLMs, hosted notebooks, cloud vector/search databases, external labeling services, telemetry, or crash-reporting systems.
- Network access is permitted only for a controlled acquisition of declared public repositories, model weights, and package dependencies. Record versions and integrity identifiers, then run the primary experiment offline.
- Do not enable an external provider as a fallback when local inference fails. A change to this boundary requires a superseding privacy decision, provider retention/security review, and explicit approval before transmission.

### 4. Experiment artifact handling

- Store checkouts, chunks, vectors, indexes, tokenizer/model caches, manifests containing sensitive provenance, logs, and per-file audit results outside this Git repository, under the local research-data area defined by [ADR-013](ADR-013-dataset-snapshot-freeze.md).
- Treat vectors and all vector-to-chunk metadata as confidential source-derived data. Keep them access-controlled, do not distribute them, and do not include them in thesis artifacts or backups without encryption and access control.
- Commit only non-sensitive protocol documents, schemas, aggregate counts, and reproducibility instructions. Logs must omit source text, credentials, raw embeddings, and sensitive query content.
- On repository removal, audit failure, or retention expiry, delete the checkout and all derived chunks, vectors, caches, and temporary copies. Retain only the minimum non-sensitive decision and aggregate audit record needed to explain the study.

## Rationale

Local inference minimizes data disclosure and removes provider behavior, availability, and pricing from the primary experiment. Explicit input handling and artifact lineage make privacy and reproducibility properties observable rather than assumed. The conditional authorization is deliberate: this ADR resolves the processing policy, but it does not convert the outstanding corpus audit into a pass.

## Consequences and implementation requirements

- The embedding implementation must fail closed when the privacy-clearance manifest is absent, incomplete, or records an unresolved finding.
- The implementation must write a run manifest and artifact manifest without source contents or raw vector values in logs.
- A controlled model download must be completed before offline execution; later runs must not require source-data egress.
- FAISS, retrieval, and LLM work remain out of scope for this ADR and must not be introduced as incidental embedding dependencies.

## References

- [ADR-008: source-code privacy](ADR-008-source-code-privacy.md)
- [ADR-013: dataset snapshot freeze](ADR-013-dataset-snapshot-freeze.md)
- [ADR-015: embedding model selection](ADR-015-embedding-model-selection.md)
- [Phase 5.3 chunker design](../architecture/chunker-design.md)
