# ADR-008: Source-Code Processing and Privacy Policy

## Status

Accepted as the research prototype's default data-handling policy on 2026-09-26. Applies before any source ingestion, embedding, retrieval, or evaluation. A repository-specific audit remains a prerequisite; this ADR does not assert that any corpus snapshot is free of secrets or personal/confidential data.

## Context

The study indexes third-party source, repository metadata, benchmark questions, and derived embeddings. Public availability and a permissive code license do not make credentials, personal data, customer material, or derived vector representations harmless. Embeddings can reveal information about their input and must be protected as source-derived data. The thesis needs a reproducible retrieval experiment without sending code or queries to third parties.

## Decision

### 1. Source processing policy

- Process only the approved, public, SHA-pinned Python snapshots listed in [corpus-manifest-validation.md](../research/corpus-manifest-validation.md), subject to the pre-index gates recorded there.
- Treat checked-out source as read-only input. Never modify upstream files. Scanner and parser outputs must preserve the upstream commit identity.
- Before indexing each snapshot, run secret/credential scanning and a documented personal/confidential-data review. Exclude offending files from all derived artifacts and the manifest; if safe filtering cannot be assured, exclude the repository and record a replacement or protocol revision before annotation.
- Keep corpus checkouts, file contents, raw chunks, questions that quote source, vectors, FAISS indexes, caches, logs, and per-file audit output in a local research-data area outside this Git repository. Do not commit or publish them. Only non-sensitive protocol documentation and aggregate counts may be committed.
- Preserve applicable license and per-file copyright notices. Corpus selection is not legal advice and is not permission to redistribute repository source.

### 2. Local processing requirement

- Source reading, parsing, chunking, tokenization, embedding generation, vector-index creation, BM25 indexing, query execution, scoring, and logging must execute on the researcher's controlled local machine for the primary study.
- Pin model and software revisions. Download public repositories, model weights, and dependencies only through the explicitly controlled setup step; record their identities and verify integrity where supported. After setup, primary indexing and evaluation must run without a service call or source-data egress.
- Do not use hosted notebooks, remote build agents, hosted vector databases, browser-based source analysis, or any service that receives source, chunks, embeddings, benchmark questions containing source-derived details, results, or audit findings.
- Apply local account access controls and full-disk encryption where available. Keep temporary plaintext copies to the minimum needed; remove them when no longer required. Encrypt backups and restrict them to the researcher. Record retention/deletion of local corpus data in the final research record.

### 3. External-service restrictions

- **Prohibited for primary research data:** hosted LLM/chat, embedding APIs, cloud vector/search databases, telemetry or crash-reporting services receiving study content, external human-labeling services, and any upload of source or source-derived data.
- External use of public Git hosting to fetch the selected pinned snapshots and model/package registries to acquire declared dependencies is permitted only as a controlled acquisition step. It must not upload local corpus data. Disable optional telemetry where supported.
- No online answer generation is part of RQ1. Any future exception or secondary study that transmits source-derived data requires a separate written protocol/ADR, data-protection and license review, provider/retention review, and explicit approval before transmission. It cannot be enabled by configuration drift.

### 4. Embedding and index storage policy

- Treat embeddings, tokenized chunks, BM25 terms, index files, and metadata sidecars as **confidential source-derived research data**, regardless of whether the upstream source is public.
- Store them locally, outside Git, with repository/commit scoping and least-privilege filesystem access. Keep FAISS indexes and their chunk-ID/provenance sidecars together so data can be deleted as one snapshot. Do not place source text in application logs or diagnostic telemetry.
- Do not distribute embeddings or vector indexes. Do not include them in thesis artifacts or backups without access control and encryption. Report only aggregate results; cite upstream repository and commit as required, and include source excerpts only when permitted, necessary, and attributed.
- On repository removal, audit failure, or project retention expiry, delete the checkout and all derived chunks, embeddings, indexes, and temporary copies; retain only the minimum non-sensitive audit/decision record needed for reproducibility.

## Rationale

This approach supports reproducibility while minimizing exposure and respecting the fact that vector embeddings are derived from copyrighted and potentially sensitive source. Local inference reduces disclosure to processors but is not a claim of perfect privacy or immunity from local compromise. Acquisition from a public hosting provider is distinct from uploading source or query data to a hosted inference/database service.

## Consequences and implementation requirements

- A corpus audit and exclusion manifest must precede ingestion; the current Phase 4.5 validation confirms SHA/file/LOC/license-path facts only, not a clean secret/privacy audit.
- The prototype must provide deterministic local storage paths outside the repository, explicit retention/deletion controls, and logs that avoid source contents, credentials, queries with sensitive text, and embedding values.
- The execution environment must support local inference and CPU FAISS. If the implementation cannot meet this policy, pause and seek a new decision rather than silently sending data to a hosted service.
- Any policy exception or research scope change requires a new decision before data transfer or indexing.

## Related records

- [Corpus manifest validation](../research/corpus-manifest-validation.md)
- [Final corpus selection](../research/repository-corpus-final.md)
- [Final technology selection](../research/technology-selection-final.md)
- [ADR-003: system boundary](ADR-003-system-boundary.md)