# Phase 20 - Prototype Validation Report

**Date:** 2026-09-28  
**Scope:** Software reliability, reproducibility, and usability for the existing research prototype.  
**Dataset boundary:** Frozen Humanize pilot only; no new repositories, questions, annotations, or benchmark scope.

## Final Status

| Area | Status |
|---|---|
| Humanize | **COMPLETE / FROZEN** |
| Software | **Prototype validation complete for the tested local contracts** |
| Expansion | **DEFERRED** |
| Future | Additional repositories can be added after prototype maturity. |

This report describes software validation. It does not claim production readiness, corpus-wide retrieval quality, or new research results.

## Architecture Summary

```text
Pinned local Git checkout
  -> RepositoryScanner (commit and tracked-file provenance)
  -> PythonAstParser (AST entities and source locations)
  -> CodeChunker (module/class/function/method chunks and stable IDs)
  -> EmbeddingPipeline (validated normalized embeddings)
  -> VectorIndex and BM25Index (persisted, integrity-checked indexes)
  -> Hybrid / parent-child retrieval (snapshot-scoped ranked results)
  -> RetrievalEvaluator (recall, MRR, nDCG reports)

BenchmarkValidator and PipelineValidationRunner provide independent schema,
provenance, integrity, read-only, and repeatability checks.
```

The ingestion boundary is intentionally local and read-only. The scanner verifies the exact full commit SHA and reads tracked Git blobs rather than relying on mutable working-tree state. The parser and chunker preserve repository, commit, path, symbol, and source-range provenance. Indexes are built from validated embedding artifacts and reject mixed snapshots, changed clearances, corrupted files, unsupported runtimes, and invalid vectors.

## Current Capabilities

- Deterministic Python AST parsing with explicit syntax errors and safe repository-relative paths.
- Deterministic module, class, function, and method chunks with stable SHA-256 identities.
- Exact snapshot verification, tracked-file filtering, aggregate pipeline reports, and source read-only checks.
- Offline embedding generation and artifact integrity validation.
- Deterministic exact-cosine vector retrieval, identifier-aware BM25 retrieval, hybrid reciprocal-rank fusion, and bounded parent-child expansion.
- Snapshot-scoped evaluation with recall@k, reciprocal rank, and nDCG, plus deterministic system ordering.
- Benchmark schema/provenance validation and freeze metadata utilities.
- Persisted index round trips with integrity checks and reproducible output bytes in the validated runtime.

## Stabilization Change

`PipelineValidationRunner` accepted a caller-provided repository tuple but reported the canonical nine-repository count and used that canonical count in reconciliation. This was a misleading interface for synthetic fixtures and focused validation runs. The runner now reports and reconciles against the tuple actually supplied by the caller. A regression test covers the custom-scope contract.

## Known Limitations

- The prototype is Python-focused and local/offline; it is not a hosted service or production ingestion platform.
- Humanize source-derived pilot files, annotations, answers, chunk maps, and retrieval records remain external to this repository. Reproduction on another machine requires equivalent approved local artifacts and the pinned offline model cache.
- The full pinned corpus validation requires local checkouts outside Git; this phase does not authorize or perform repository expansion.
- Persisted index compatibility is runtime- and package-sensitive. The manifests intentionally require matching Python/package/runtime contracts and a rebuilt index after incompatible changes.
- Evaluation validates metric computation and provenance contracts. It does not establish unseen-repository generalization or statistical conclusions from the frozen pilot.
- Reports intentionally omit source text, per-file paths, and checkout paths; this improves handling safety but limits standalone forensic detail.
- No UI, answer-generation service, cloud deployment, or production operational controls are part of this prototype.

## Test Results

The existing offline suite was run from the project root with the documented Python environment and model cache:

```powershell
$env:EMBEDDING_MODEL_CACHE = 'C:/Apps/Temp/Phase6.2/model-cache'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
& C:/Apps/Temp/Phase6.2/venv/Scripts/python.exe -m unittest discover -s tests -v
```

- Baseline before the stabilization change: **124 tests passed; 0 failures, errors, or skips**.
- Focused regression after the change: **4 tests passed** in `test_pipeline_validation`.
- Final full suite after the stabilization change and report preparation: **124 tests passed in 10.433 seconds; 0 failures, errors, or skips**.

The tests use synthetic/offline fixtures and existing cached-model coverage. They do not alter the Humanize pilot.

## Reproducibility Results

| Check | Result | Evidence |
|---|---|---|
| Same parsed input produces the same chunks and IDs | **PASS** | Parser and chunker deterministic-output tests; source-range and provenance tests. |
| Same index produces the same retrieval output | **PASS** | FAISS tie-policy, repeated-build, persistence-reload, BM25 round-trip, and hybrid-fusion tests. |
| Evaluation metrics can be regenerated | **PASS** | Repeated benchmark loading and evaluator runs produce equal reports with stable system/query ordering. |
| Pipeline validation can be regenerated | **PASS** | Repeated reports and serialized JSON are byte-equal; source checkout remains unchanged. |
| Humanize artifacts remain unchanged | **PASS for this phase** | No Humanize files were edited; the existing external preservation baseline and frozen pilot records remain the controlling evidence. |
| Benchmark expansion occurred | **NO** | No repositories, questions, annotations, or benchmark cases were added or modified. |

Reproducibility is bounded to the documented runtime, package versions, pinned snapshot identities, and external artifact locations. It is not a claim that every platform or dependency version will produce identical persisted bytes.

## Validation Statement

**Humanize:** COMPLETE / FROZEN  
**Software:** Prototype validation complete for the current tested contracts.  
**Expansion:** DEFERRED  
**Future:** Additional repositories can be added after prototype maturity.  
**Validation:** Full test suite, Humanize artifact preservation, and absence of benchmark expansion are required completion checks for this phase.
