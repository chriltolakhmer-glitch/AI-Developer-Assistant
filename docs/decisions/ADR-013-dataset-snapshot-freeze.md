# ADR-013: Freeze the Phase 5.4.1 Dataset Snapshots

## Status

Accepted on 2026-09-27. Preprocessing validation passed for all nine approved snapshots. Privacy clearance for indexing remains open.

## Context

The nine repositories selected by [ADR-006](ADR-006-corpus-selection.md) were not present locally when Phase 5.4 was implemented. The offline validation runner therefore could not yet verify the approved SHAs against scanner, parser, and chunker results. The research design requires immutable revisions, reproducible preprocessing, and source checkouts outside the thesis Git project. The corpus is public upstream source, but SHA/count validation alone does not establish that it is free of credentials, personal data, or confidential material.

## Decision

1. Freeze the nine repository revisions, root-license evidence, Python file/LOC baselines, and validation date recorded in [dataset-snapshot-freeze.md](../research/dataset-snapshot-freeze.md). The full commit SHA—not a branch or tag—is the identity of each snapshot.
2. Keep all checkouts under `C:\Apps\Temp\Phase5.4\corpus`, outside the thesis project. Keep pipeline reports and scanner/audit artifacts outside both the project and source checkouts. Do not commit upstream source, chunks, per-file manifests, or detailed scan findings.
3. Treat the preprocessing implementation as the Phase 5.4 baseline at commit `2c3e5ec`: manifest schema `1.0`, filter `phase4.5-python-v1`, pipeline report schema `1.0`, standard-library AST parser, semantic chunker, Python `3.14.7` for the recorded run. Any future filter, parser, chunking, or runtime change must be versioned and revalidated against all nine frozen SHAs.
4. Accept the Phase 5.4.1 preprocessing result documented in [corpus-checkout-validation.md](../research/corpus-checkout-validation.md): all nine SHAs matched; file and LOC counts matched; 1,916 files parsed successfully with no parse failures; 33,415 deterministic chunks were generated with no chunk failures. The preprocessing gate is passed for this version.
5. Keep indexing and model work blocked until the secret/privacy findings are manually dispositioned and the personal/confidential-data review is completed. This ADR does not authorize embeddings, FAISS, another vector database, or LLM processing. The user's explicit “do not implement embeddings yet” scope remains in force.

## Rationale

A documented snapshot freeze separates corpus identity from mutable upstream branches, provides a reproducible baseline for future phases, and closes the Phase 5.4 local-checkout blocker. The external data location respects the source-retention boundary. Recording preprocessing versions and exact counts makes later differences visible instead of silently changing the sample. Privacy is an independent gate, not an inference from successful parsing.

## Consequences

- The nine snapshots are frozen for the validated preprocessing baseline; any substitution or SHA change requires a new decision and count reconciliation before annotation or evaluation.
- The validation run used shallow checkouts with only the pinned commit available. It establishes snapshot correctness, not full-history secret scanning.
- Gitleaks `8.30.1` identified eight candidate snapshot findings (six Flask, one pytest, one Sphinx); they remain undispositioned. The Sphinx history scan reported an unsupported `.dot` file. The scan reports are local-only and outside Git.
- No personal/confidential-data audit pass is claimed. Do not start embeddings or indexes until that gate is documented and explicitly authorized.
- Preprocessing validation does not establish embedding, FAISS, retrieval, benchmark, or LLM readiness.

## References

- [ADR-006: primary corpus selection](ADR-006-corpus-selection.md)
- [ADR-008: source-code privacy](ADR-008-source-code-privacy.md)
- [ADR-009: repository scanner](ADR-009-scanner-design.md)
- [ADR-010: Python AST parser](ADR-010-ast-parser.md)
- [ADR-011: semantic code chunks](ADR-011-code-chunking.md)
- [ADR-012: pipeline validation](ADR-012-pipeline-validation.md)
- [Dataset snapshot freeze](../research/dataset-snapshot-freeze.md)
- [Corpus checkout validation report](../research/corpus-checkout-validation.md)
