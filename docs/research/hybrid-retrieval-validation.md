# Phase 6.3.3 — Hybrid Retrieval Validation

## Scope

This report records validation of the local RRF hybrid retrieval pipeline. It covers synthetic fixtures and unit tests only. Full corpus indexing and retrieval execution were not run.

## Test results

The existing `tests/test_rrf.py` covers reciprocal-rank behavior, RRF constant 60, rank-only fusion, deterministic tie breaking, 50-result channel/output windows, malformed rankings, mixed snapshots, conflicting metadata, and the local text-query path. The new `tests/test_hybrid_search.py` covers dense/BM25 query fan-out, fixed candidate limits, response parameters, compatibility failure, and provenance preservation.

Validation command:

```text
python -m unittest discover -s tests -v
```

Result: passed. `89` tests completed in `16.882` seconds; `2` model-cache-dependent tests were skipped. The initial attempt failed because the active environment lacked declared dependencies; validation was rerun successfully in the configured `C:\Apps\.venv` environment. No corpus indexing was performed.

## Retrieval flow validation

The validated design is:

```text
Query -> local MiniLM encoder -> FAISS dense search --+
                                                     +-> RRF -> hybrid results
Query ---------------------------------> BM25 search -+
```

The implementation uses 50 candidates per channel, RRF constant 60, equal channel weighting, and a maximum of 50 fused results. It preserves repository, commit, path, symbol, line range, content hash, and per-channel rank/score evidence.

## Known limitations and blockers

- Corpus execution remains blocked until the privacy clearance and unresolved secret findings are resolved.
- Tests use synthetic fixtures and do not establish retrieval quality on the frozen corpus.
- The active environment initially lacked the declared retrieval dependencies, so the full command must be rerun after dependency setup.
- No LLM, UI, agents, answer generation, or evaluation experiments are implemented.
- RRF weights are fixed equal weights and have not been empirically optimized.

## Next milestone

After privacy clearance and successful dependency validation, the next implementation milestone is a controlled retrieval smoke run over approved local artifacts, followed by separately designed evaluation work. Do not begin LLM or UI implementation as part of this phase.

## References

- [Hybrid retrieval design](../architecture/hybrid-retrieval-design.md)
- [ADR-019: RRF hybrid ranking](../decisions/ADR-019-rrf-hybrid-ranking.md)
- [ADR-014: embedding privacy policy](../decisions/ADR-014-embedding-privacy-policy.md)
