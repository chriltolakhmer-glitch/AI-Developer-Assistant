# ADR-009: Deterministic Read-Only Repository Scanner

## Status

Accepted and implemented for Phase 5.1 on 2026-09-26.

## Context

Phase 4 selected nine immutable Python repository snapshots and recorded reproducible file and LOC screening rules. Before AST parsing or indexing, the prototype needs to independently verify each requested revision and generate auditable file metadata. The scanner must not make the source tree mutable, introduce network behavior, or emit machine-dependent manifests. The existing secret/privacy audit remains open and blocks indexing; scanner output alone does not establish corpus clearance.

## Decision

Use a small Python standard-library scanner that operates only on a local Git repository. The caller must provide a full expected commit SHA; the scanner verifies `HEAD` and fails closed on a mismatch. It enumerates the committed Git tree, considers tracked `.py` files, applies the shared Phase 4.5 ignore and generated-file rules, and records both eligible files and excluded Python candidates with reasons. Eligible records include SHA-256, byte size, and nonblank/non-comment physical LOC.

Read file bytes from local Git blob objects for platform-independent results. Do not clone, fetch, checkout, edit, or call external APIs/services. Manifest JSON is stable, has no timestamp or checkout-root path, and may only be written outside the scanned repository. Use the Python standard library and `unittest`; do not add runtime dependencies for this phase.

The scanner is only the corpus-inventory component. Secret/privacy screening, AST parsing, chunking, indexing, UI/chatbot, and LLM integration are not part of this decision.

## Rationale

Verifying the immutable revision before measurement makes corpus identity explicit. Reading canonical committed blobs avoids line-ending conversion differences across machines. Recording eligible and excluded Python paths, content hashes, sizes, and LOC makes the screening counts auditable while sorted, timestamp-free serialization supports repeatable comparisons. A local-only standard-library implementation keeps the first research prototype easy to inspect and test.

## Consequences

- Scan only an existing Git checkout at the approved SHA; acquisition remains a distinct controlled step.
- Reconcile scanner counts against [repository-corpus-final.md](../research/repository-corpus-final.md) before annotation or indexing; document differences rather than silently changing corpus strata.
- Keep generated per-file manifests and corpus checkouts outside this Git repository in accordance with [ADR-008](ADR-008-source-code-privacy.md).
- Run and disposition the required secret/credential and personal/confidential-data audit before indexing; this implementation does not perform that audit.
- Treat the scanner's filter version and LOC semantics as part of the manifest protocol. Any change requires explicit versioning and count reconciliation.

## References

- [Phase 4 corpus selection](../research/repository-corpus-final.md)
- [Phase 4.5 manifest validation](../research/corpus-manifest-validation.md)
- [Phase 5 readiness check](../research/phase5-readiness-check.md)
- [ADR-008: source-code privacy](ADR-008-source-code-privacy.md)
- [Scanner architecture](../architecture/scanner-design.md)