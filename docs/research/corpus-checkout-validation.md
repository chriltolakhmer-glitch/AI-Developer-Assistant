# Corpus Checkout Validation — Phase 5.4.1

**Validation date:** 2026-09-27
**Result:** **Preprocessing validation PASS — 9/9 repositories.**
**Preprocessing implementation:** commit `2c3e5ec`; manifest schema `1.0`; filter `phase4.5-python-v1`; pipeline report schema `1.0`; Python `3.14.7`.

This run resolves the local-checkout blocker recorded in [Phase 5.4 pipeline validation](pipeline-validation.md). Exact pinned snapshots were acquired into `C:\Apps\Temp\Phase5.4\corpus`, outside the thesis project. No corpus source was added to Git.

## Method

- Acquired one shallow, detached checkout per approved repository at its full 40-character SHA. The checkout roots are the short repository slugs used by the Phase 5.4 runner.
- Verified each checkout's `HEAD` against the approved SHA and required a clean tracked worktree. The scanner reads committed Git blobs, applies the shared tracked-Python filter, and computes eligible file/LOC counts.
- Ran the Phase 5.4 pipeline validator: scanner → Python AST parser → semantic chunker. Successful parse and chunk outputs are repeated and compared for determinism. The runner writes aggregate JSON and Markdown reports outside both the project and all checkouts.
- External reports: `C:\Apps\Temp\Phase5.4\reports\corpus-checkout-validation\pipeline-validation.json` and `.md`.
- The nine clone histories are shallow (one pinned commit each). This run is a snapshot validation, not a complete-history audit.

## Per-repository results

| Repository | Expected and verified SHA | Python files | Eligible LOC | Parse success / failure | Classes | Functions | Methods | Chunks | Chunk failures | Deterministic |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| theskumar/python-dotenv | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | 20 / 20 | 2,776 / 2,776 | 20 / 0 | 12 | 125 | 46 | 203 | 0 | Yes |
| python-humanize/humanize | `392aef707c0e74341ab4a51420984e9ea6b566c5` | 13 / 13 | 2,915 / 2,915 | 13 / 0 | 3 | 103 | 7 | 126 | 0 | Yes |
| python-validators/validators | `70de324322def13a49a93d222f798ec1ab700885` | 64 / 64 | 4,353 / 4,353 | 64 / 0 | 5 | 218 | 13 | 300 | 0 | Yes |
| pallets/flask | `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | 83 / 83 | 13,301 / 13,301 | 83 / 0 | 160 | 1,060 | 402 | 1,705 | 0 | Yes |
| encode/httpx | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | 60 / 60 | 13,800 / 13,800 | 60 / 0 | 107 | 712 | 422 | 1,301 | 0 | Yes |
| Textualize/rich | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | 213 / 213 | 45,223 / 45,223 | 213 / 0 | 272 | 959 | 865 | 2,309 | 0 | Yes |
| pytest-dev/pytest | `8721173580390a9d297e5af06cac3f0b6841f425` | 245 / 245 | 93,998 / 93,998 | 245 / 0 | 789 | 2,321 | 4,125 | 7,480 | 0 | Yes |
| python/mypy | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | 444 / 444 | 144,316 / 144,316 | 444 / 0 | 835 | 2,408 | 6,979 | 10,666 | 0 | Yes |
| sphinx-doc/sphinx | `b04a2101295ac3fb725b16111eda0284b6da4cca` | 774 / 774 | 118,987 / 118,987 | 774 / 0 | 1,198 | 2,782 | 4,571 | 9,325 | 0 | Yes |

For each row, the first file/LOC number is actual and the second is the Phase 4.5 baseline.

## Aggregate result

| Measure | Result |
|---|---:|
| Approved repositories | 9 / 9 |
| Pinned SHA matches | 9 / 9 |
| Eligible Python files | 1,916 / 1,916 baseline |
| Eligible Python LOC | 439,669 / 439,669 baseline |
| Parsed files | 1,916 success; 0 failures |
| Modules | 1,916 |
| Classes | 3,381 |
| Functions (methods excluded) | 10,688 |
| Methods | 17,430 |
| Semantic chunks generated | 33,415 |
| Chunk-generation failures | 0 |
| Repeated parse/chunk comparison | Deterministic for all nine |
| Pipeline `preprocessing_ready` | `true` |
| Pipeline `embedding_readiness` | `blocked_pending_privacy_audit` |

The report contains no source text, per-file paths, or checkout paths. Chunk-size statistics are present only in the external aggregate report.

## Separate privacy gate

Gitleaks `8.30.1` snapshot scans completed for all nine repositories. Eight candidate findings were reported: six in Flask, one in pytest, and one in Sphinx. These findings have not been manually dispositioned. The Sphinx Git scan logged an unsupported `.dot` file error, and only the single available shallow commit was in each clone. Detailed redacted scan reports are retained outside Git. Personal/confidential-data review is also still outstanding. Therefore the corpus is **not cleared for indexing or embeddings**, despite the 9/9 preprocessing pass.

No embeddings, FAISS index, vector database, or LLM were created or invoked. The full Python test suite also passed: 22 tests, 0 failures.

## References

- [Dataset snapshot freeze](dataset-snapshot-freeze.md)
- [Phase 5.4 pipeline validation methodology and initial blocked run](pipeline-validation.md)
- [ADR-013: dataset snapshot freeze](../decisions/ADR-013-dataset-snapshot-freeze.md)
- [ADR-008: source-code privacy](../decisions/ADR-008-source-code-privacy.md)
