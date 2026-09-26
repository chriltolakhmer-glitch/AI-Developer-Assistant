# ADR-006: Select and Pin the Primary Python Repository Corpus

## Status

Accepted for the Phase 4 research corpus on 2026-09-26, subject to pre-index secret/privacy audit and manifest verification.

## Context

The Phase 3 corpus shortlist was explicitly a placeholder. The controlled RQ1 comparison requires real, diverse Python repositories with licenses, immutable revisions, and reproducible size strata. The previous three analyzed AI-assistant repositories must not enter the primary benchmark.

## Decision

Select the nine repositories, exact commit SHAs, root-license findings, language metadata, eligible Python file counts, nonblank/non-comment eligible LOC estimates, tracked checkout sizes, and maturity signals recorded in [repository-corpus-final.md](../research/repository-corpus-final.md). The three small, three medium, and three large repositories meet the predeclared eligible-LOC thresholds. The selected set spans configuration, formatting, validation, web, HTTP, terminal UI, testing, static analysis, and documentation domains.

The pinned SHA—not a mutable branch or release tag—is the corpus identity. Retain the prescribed LOC filter, file manifest, hashes, exclusions, screening date, license notices, and later parser results. Complete the documented secret/credential and personal/confidential-data audit before indexing; selection does not assert that this audit has passed.

## Rationale

This sample meets the feasible nine-repository / three-stratum design while varying domain and project organization. Exact source revisions and one shared LOC rule allow the corpus to be reconstructed and checked. MIT and BSD-licensed repositories, plus mypy's and Sphinx's file-level notices, are explicitly identified rather than inferred from potentially incomplete GitHub SPDX fields.

## Consequences

- Use only these revisions for the planned primary sample unless an eligibility failure is found before annotation; record any substitution and rationale before evaluation.
- Re-run eligibility counts with the eventual scanner and record all deltas; do not change LOC rules or strata after seeing retrieval outcomes.
- Complete the secret/privacy audit and honor all license notices before indexing or redistribution.
- Exclude `codebase-rag`, `Codebase-RAG-Assistant`, and `ai-codebase-assistant` from primary evaluation; any pilot use must be separate and disclosed.
- Benchmark annotation, query freeze, and evaluation are future tasks; this ADR does not claim their completion.

## Related decisions and sources

- Supersedes the placeholder candidate table in [repository-corpus-selection.md](../research/repository-corpus-selection.md).
- Follows [ADR-003](ADR-003-system-boundary.md) and [Decision 004 in architecture-decisions.md](architecture-decisions.md) on the retrieval-evaluation scope.
- Repository URLs, SHA pins, license-file paths, counts, and screening method are detailed in [repository-corpus-final.md](../research/repository-corpus-final.md).