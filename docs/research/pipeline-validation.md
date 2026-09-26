# Phase 5.4 — Scanner, Parser, and Chunker Pipeline Validation

**Review date:** 2026-09-26  
**Status:** Runner and integration tests implemented; approved corpus validation is **blocked** because the nine pinned checkouts are not available locally. No repository was cloned or fetched.

## Purpose and scope

Validate the deterministic preprocessing path before retrieval work:

```text
Approved local checkout at pinned SHA
  -> RepositoryScanner (commit, tracked Python files, LOC)
  -> PythonAstParser (per-file parse result and code entities)
  -> CodeChunker (provenance-aware module/entity chunks)
  -> aggregate JSON and Markdown report outside Git
```

The runner processes only the approved nine repositories in [repository-corpus-final.md](repository-corpus-final.md). It performs no clone/fetch, external API/service call, embedding, vector database, LLM, UI, or chatbot operation. It does not run the required secret/privacy audit.

## Validation methodology

1. Place already-acquired local checkouts under a caller-selected corpus root, one checkout per repository slug (for example, `<corpus-root>/python-dotenv`). Keep checkouts outside this Git repository and follow [ADR-008](../decisions/ADR-008-source-code-privacy.md).
2. For each expected repository, require the full approved SHA and scan the Git commit tree with the Phase 5.1 filter. The runner stops processing a missing checkout, a SHA mismatch, a scanner error, or a tracked dirty worktree; it does not attempt network recovery.
3. Read each eligible Python source file locally using Python's encoding-cookie-aware text reader. Parse each source twice and chunk each successful parse twice; compare immutable results for determinism. Each parser failure is counted once per file and not silently suppressed.
4. Aggregate Python-file/eligible-LOC counts, parse success/failure, module/class/function/method counts, chunk count, and per-chunk character and UTF-8 byte sizes. Size summaries use min, nearest-rank p50/p95, arithmetic mean, and max.
5. Recheck tracked source changes and write stable JSON/Markdown reports only to a caller-selected directory outside the thesis Git repository and each existing corpus checkout. Reports omit source text, per-file paths, local checkout paths, and timestamps.

Invocation is through `python -m src.evaluation.pipeline_validation` with required `--corpus-root` and `--output-dir` arguments. The runner writes `pipeline-validation.json` and `pipeline-validation.md`; it returns aggregate status even when corpus inputs are unavailable so the missing prerequisites remain reviewable.

## Metrics collected

For each repository, the report records repository ID; expected and verified commit SHA; run status/issues; actual and baseline tracked eligible Python file count and LOC; source-read failures; parse successes/failures; modules, classes, functions, methods, chunks, and chunk-generation failures; deterministic comparison result; and character/UTF-8-byte chunk-size summaries.

Function count excludes methods; methods are reported separately. Module count equals successfully parsed files. Chunk count includes the module chunk and all class/function/method chunks for parse-success files. Chunk-size statistics describe normalized decoded source text, not model tokens.

## Success criteria

**Preprocessing pass** requires all nine snapshots to be present at their approved SHAs with clean tracked trees; exact Python-file and eligible-LOC counts to match the Phase 4.5 baselines; every eligible file to be accounted for by source-read or parse success/failure; repeated parser/chunker outputs to match; and no unexpected read, parse, or chunk-generation failures. Any count delta or parse failure must be investigated and documented before the pipeline is considered ready for retrieval experiments.

**Embedding readiness is a separate gate.** A successful pipeline report cannot clear the outstanding credential/secret and personal/confidential-data audit in [corpus-manifest-validation.md](corpus-manifest-validation.md) and [ADR-008](../decisions/ADR-008-source-code-privacy.md). It also does not validate an embedding model or vector index.

## Approved repositories and execution result

The runner includes the full approved set and Phase 4.5 Python counts/LOC. On 2026-09-26, the designated local corpus root was checked without network access; no matching checkout was present anywhere under `C:\Apps`. Therefore **0 of 9 repositories were scanned or parsed**. The generated report records `missing_checkout` for all nine, with counts unavailable; this is a blocked validation attempt, not a successful corpus validation.

| Repository | Approved SHA | Expected Python files | Expected eligible LOC | Local result |
|---|---|---:|---:|---|
| theskumar/python-dotenv | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | 20 | 2,776 | Missing checkout; not scanned |
| python-humanize/humanize | `392aef707c0e74341ab4a51420984e9ea6b566c5` | 13 | 2,915 | Missing checkout; not scanned |
| python-validators/validators | `70de324322def13a49a93d222f798ec1ab700885` | 64 | 4,353 | Missing checkout; not scanned |
| pallets/flask | `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | 83 | 13,301 | Missing checkout; not scanned |
| encode/httpx | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | 60 | 13,800 | Missing checkout; not scanned |
| Textualize/rich | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | 213 | 45,223 | Missing checkout; not scanned |
| pytest-dev/pytest | `8721173580390a9d297e5af06cac3f0b6841f425` | 245 | 93,998 | Missing checkout; not scanned |
| python/mypy | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | 444 | 144,316 | Missing checkout; not scanned |
| sphinx-doc/sphinx | `b04a2101295ac3fb725b16111eda0284b6da4cca` | 774 | 118,987 | Missing checkout; not scanned |

The test suite validates pipeline integration, deterministic reports, parse-failure accounting, and read-only behavior using temporary local Git repositories. It does not substitute for corpus-wide results. The actual aggregate reports were generated outside Git under the local Phase 5.4 temporary reports directory.

## Issues and readiness

- **Blocking:** all nine local corpus checkouts are unavailable, so SHA verification, baseline reconciliation, parser coverage, and chunk statistics for the approved sample remain unverified.
- **Still open:** the required secret/privacy review is not performed by this runner and continues to block embedding/indexing.
- **Decision:** preprocessing implementation is test-validated, but the nine-repository pipeline validation exit criteria have not passed. Do not start embedding based on this run.