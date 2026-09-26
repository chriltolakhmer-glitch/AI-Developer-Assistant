# Phase 6.1 — Embedding Pipeline Design

## Status

Design baseline for local embedding generation. No embedding implementation, FAISS index, retrieval component, or LLM is introduced by this document.

## Purpose

The embedding pipeline converts validated AST semantic chunks into deterministic vector representations that can later support dense retrieval experiments. It is a bounded transformation between the Phase 5 preprocessing boundary and a future vector-index boundary.

```text
Validated AST semantic chunks
  -> privacy-clearance gate
  -> canonical embedding text and provenance validation
  -> pinned local embedding model
  -> explicit input-length handling
  -> vector validation and L2 normalization
  -> versioned local vector artifacts and manifests
```

## Input

The input is the immutable tuple of `CodeChunk` records produced by the Phase 5.3 semantic chunker. Each record supplies a stable chunk ID, repository and commit identity, relative path, entity type, qualified name, inclusive line span, content hash, and source text. The source text is read from the approved local snapshot and is not modified by this pipeline.

Input preconditions:

- The repository and commit are present in the approved snapshot manifest.
- The privacy-clearance manifest authorizes processing of the snapshot; unresolved findings fail closed.
- Chunk IDs and content hashes are valid and deterministically ordered.
- The embedding text representation is versioned and identical for corpus chunks and future queries.

The Phase 6.1 design does not alter scanner, parser, or chunker behavior. Any required handling for oversized chunks must be expressed as a versioned embedding input policy with parent/child lineage, not as an implicit change to Phase 5.

## Processing

### 1. Gate and canonicalize

Load the approved snapshot and chunk manifests, validate repository/commit scope, and select chunks in stable chunk-ID order. Build the model input from the declared chunk representation. Do not put source text, credentials, or raw vectors in ordinary logs.

### 2. Run the embedding model

Use the local, pinned model selected by [ADR-015](../decisions/ADR-015-embedding-model-selection.md). The same tokenizer, model revision, inference mode, and software versions must be used for every corpus and query embedding. Network access is not part of a normal run after the controlled model acquisition step.

The selected baseline has a finite input limit. The pipeline must measure the tokenized input before inference and apply the declared deterministic split-or-reject policy. Silent truncation is prohibited because it would make semantic coverage and experiment results irreproducible.

### 3. Validate and normalize

Validate that every input produces exactly one finite vector of the expected dimension. Reject or quarantine non-finite, missing, duplicated, or dimension-mismatched outputs. L2-normalize vectors so the planned dense baseline can use cosine similarity through normalized inner product.

### 4. Record provenance

Write a local run manifest containing the corpus snapshot identity, chunk schema and representation versions, model and revision, tokenizer behavior, input-length policy, vector dimension, normalization rule, package/runtime versions, operating system, device, and artifact hashes. Keep vector files and chunk metadata outside Git under the research-data boundary in [ADR-014](../decisions/ADR-014-embedding-privacy-policy.md).

## Output

The output is a versioned local vector artifact and a companion metadata manifest:

- one normalized vector per accepted embedding input;
- deterministic vector-position-to-chunk-ID mapping;
- repository, commit, content hash, and source-location provenance;
- model, preprocessing, normalization, runtime, and artifact identity metadata;
- aggregate counts for accepted, split, rejected, and failed inputs.

This output is not yet a searchable index. FAISS construction, persistence, query-time embedding, and retrieval evaluation are later milestones and must consume the validated artifacts without changing their meaning.

## Reproducibility and privacy constraints

- Pin the model revision and all material runtime/library versions.
- Use deterministic ordering and record the device and execution configuration.
- Keep all source-derived artifacts local, access-controlled, and outside Git.
- Make the pipeline fail closed when privacy clearance is missing or when input/output validation fails.
- Report aggregate statistics in committed research documentation; retain detailed manifests and audit results locally.

## Validation plan

Before implementation is accepted, validate model availability in a controlled download, output dimension, finite values, normalization, deterministic ordering, save/load artifact integrity, and explicit behavior at the model input boundary. Run a small non-sensitive fixture first, then process the approved corpus only after the privacy gate is closed.

## Related records

- [ADR-014: embedding privacy policy](../decisions/ADR-014-embedding-privacy-policy.md)
- [ADR-015: embedding model selection](../decisions/ADR-015-embedding-model-selection.md)
- [Phase 5.3 chunker design](chunker-design.md)
- [ADR-007: vector index selection](../decisions/ADR-007-vector-index-selection.md)
