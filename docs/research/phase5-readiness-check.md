# Phase 5 Readiness Check — Pre-Implementation Validation

**Review date:** 2026-09-26  
**Baseline:** Phase 4.5 documentation review at commit `6fc95fe`  
**Result:** **Conditionally ready for a bounded first implementation milestone; not ready for corpus indexing or the full evaluation run.** No `src/` implementation has been added by this review.

## Completed prerequisites

| Area | Review outcome | Evidence |
|---|---|---|
| Research scope | RQ1 is a Python-only, retrieval-only paired comparison of BM25, dense, and AST-aware hybrid retrieval. Answer generation is secondary and conditional. | [research-question.md](research-question.md), [evaluation-plan.md](evaluation-plan.md), [experiment-design.md](experiment-design.md), [ADR-003](../decisions/ADR-003-system-boundary.md) |
| Architecture | Read-only pinned-snapshot ingestion, Python AST parsing, deterministic provenance-bearing chunks, shared chunk units, lexical and vector indexes, three retrieval modes, and an evaluation module are specified. | [system-architecture-v1.md](../architecture/system-architecture-v1.md), [prototype-architecture.md](../architecture/prototype-architecture.md) |
| Corpus selection | Nine repositories have exact SHAs, root-license evidence, Python file/LOC counts, size strata, and basic maturity checks. Exact SHA fetches and the published counting rule were repeated for all nine; counts match. Secret/privacy review and final scanner manifest remain open. | [repository-corpus-final.md](repository-corpus-final.md), [corpus-manifest-validation.md](corpus-manifest-validation.md), [ADR-006](../decisions/ADR-006-corpus-selection.md) |
| Technology choices | Python `ast`; local `all-MiniLM-L6-v2` at a pinned model revision; CPU FAISS `IndexFlatIP`; equal-weight RRF (rank constant 60, component window 50); and principal cutoffs Recall@5/10, MRR@10, nDCG@10 are recorded. | [technology-selection-final.md](technology-selection-final.md), [ADR-007](../decisions/ADR-007-vector-index-selection.md), updated [prototype-architecture.md](../architecture/prototype-architecture.md) |
| Benchmark design | 108 proposed queries, four categories, gold spans/graded relevance, manual annotation, held-out protection, and second-reviewer spot check when available are specified. | [dataset-design.md](dataset-design.md), [benchmark-design.md](benchmark-design.md) |
| Data handling | A local-only source and source-derived-data policy now prohibits hosted inference/search/storage for the primary study and specifies audit, storage, and deletion gates. | [ADR-008](../decisions/ADR-008-source-code-privacy.md) |
| Implementation boundary | `src/` and tests contain only placeholders; the initial system and code have not been implemented. Documentation and design therefore remain the basis for the first code increment. | Repository state checked at the baseline commit. |

## Remaining risks and gates

### Must pass before source ingestion/indexing

1. **Secret/privacy audit — open, blocking.** Run a maintained scanner on each exact snapshot and review personal/confidential-data findings. The current local validation did not perform or claim this scan. Record tool/version, configuration, findings, exclusions, and disposition. If a repository cannot be cleared, replace it before annotation and recalculate strata.
2. **Scanner manifest — open, blocking.** Implement the exact shared filter and emit the eligible-file list, hashes, exclusion reasons, parser version/results, and LOC count. Reconcile counts against the screening estimate before benchmark annotation; never silently cross strata.
3. **Windows FAISS smoke test — open, blocking to dependency freeze.** In a clean target Python environment, verify CPU FAISS install/import, normalized inner-product ranking, persistence/reload equality, and repeatability. Record OS/Python/NumPy/FAISS versions. A failure requires pausing for a superseding ADR.
4. **Embedding smoke test — open, blocking to embedding/index work.** Fetch the exact model revision once, record model/library versions and device, verify 384 dimensions, offline inference, deterministic settings, and behavior at/above 256 word pieces. Implement and log an explicit split/truncation policy; do not silently lose chunk content.

### Must freeze before held-out evaluation

5. **Chunking details — incomplete.** Specify node inclusion/nesting, module-level code fallback, oversized symbols, deterministic split boundaries/overlap, stable chunk IDs, and how chunk spans map back to lines. Ensure BM25 and dense baselines consume the same chunk records.
6. **BM25/tokenizer configuration — incomplete.** Fix normalization, identifier/camel-case/snake-case tokenization, stop-word/stemming policy (including whether none), implementation/version, and candidate depth. Do not tune these on the held-out set.
7. **Benchmark split and query freeze — incomplete.** Select the pilot repository/questions separately from the final corpus or held-out questions; finalize the held-out unit before tuning. Freeze all question text and gold labels before final runs. The 108-question target is planned, not yet annotated.
8. **Evaluation/statistics details — incomplete.** Confirm the exact complete metric/cutoff list, graded nDCG mapping and evidence-match rule, bootstrap resampling unit/seed, and paired comparison/reporting plan before collecting results. Use identical retrieval conditions and report null findings/deviations.
9. **Runtime reproducibility — incomplete.** Pin a supported Python version, package lock/constraints, hardware/device, index/chunker/tokenizer/model configuration, and run-manifest schema. Capture checksums or immutable revisions for fetched model and packages.

## First implementation milestone: read-only corpus scanner

After completing the privacy audit and clean-environment decisions for Python and FAISS, the first implementation milestone should be a **scanner-only, reproducible corpus manifest**—not embeddings or a user-facing assistant.

1. Create a pinned Python environment and record its exact version/dependency lock.
2. Resolve each repository only to the approved full SHA; refuse moving branches or mismatched commits.
3. Apply the common Python allow/ignore and LOC policy without modifying source; record every included/excluded file and reason.
4. Produce a deterministic local manifest with repository/commit identity, relative path, byte size, content hash, language, exclusion result, and eligible Python LOC. Keep source paths/content and sensitive audit findings out of Git.
5. Add focused tests for SHA mismatch rejection, filter consistency, deterministic manifest output, read-only behavior, and LOC edge cases; compare its counts to the Phase 4.5 table.

**Exit gate:** all nine manifests match approved revisions; exclusions are auditable; secret/privacy findings are dispositioned; and LOC strata remain valid. Only then proceed to the AST parser/chunker milestone. The FAISS and embedding smoke tests are separate gates before vector-index/model implementation.

## Readiness decision

The architecture and research design are sufficiently defined to start a narrow scanner milestone once the **pre-index privacy audit** and supported Python environment are established. Full prototype implementation and evaluation are **not unconditionally ready**: corpus clearance, FAISS/model smoke tests, chunking and BM25 details, benchmark holdout, and statistical settings remain explicit gates. No gate is satisfied by this readiness review alone.