# Phase 27 — Usability Findings

**Date:** 2026-09-28
**Baseline:** released v0.1.1 at `51329285a882c1b7942d0a5b1c571e628d63dfb4`
**Disposition:** One confirmed CLI defect was fixed with a focused regression test. A documentation clarification records the existing scope boundary. The general real-repository workflow remains unavailable through the CLI and was not bypassed.

## Findings

### P27-01 — `validate` crashes when the corpus root exists

**Severity:** High for the documented command path
**Status:** Fixed in the current working tree; v0.1.1 remains immutable.

**Evidence:** In the fresh v0.1.1 environment, `prototype validate --corpus-root <existing-directory> --output-dir <external-directory>` completed the runner and wrote a report, then failed with `UnboundLocalError: cannot access local variable 'logging' where it is not associated with a value`. `logging` was imported only inside the branch for a *missing* corpus root, but used unconditionally after that branch. The missing-root unit test did not cover the existing-root case.

**Change:** Move `logging` to module scope and add `test_validate_with_existing_corpus_root_completes`. The focused test passes; the full post-fix suite passes 143/143 with no skips. On the selected arbitrary repository path, the fixed CLI now exits cleanly and reports 0/9 expected snapshots and readiness `no`; it does not claim to have processed that repository.

**Behavior preserved:** Missing corpus roots remain a non-fetching validation outcome with readiness `no`; no scanner, parser, chunker, or retrieval behavior changed.

### P27-02 — CLI does not offer arbitrary-repository ingest/index/search

**Severity:** High usability limitation
**Status:** Documented; implementation not changed in Phase 27.

**Evidence:** Fresh `prototype --help` lists only `validate`, `evaluate`, `demo`, and `reproduce`. `validate` invokes the configured pinned-snapshot runner and expects the fixed nine-repository set. With the selected local codebase path it reported 0/9 and did not parse that candidate. The embedding and retrieval APIs are library-level; their corpus path requires approved snapshot identities and matching clearance. Their controls reject an uncleared or non-allowlisted repository.

**Change:** Add a scope-boundary section to the CLI documentation explaining that smoke commands use generated fixtures, `validate` is limited to the pinned snapshot set, and the release has no general `ingest`, `index`, or `search` command. This prevents users from treating a smoke pass as a real-codebase retrieval result.

**Not changed:** No general-purpose command, allowlist entry, clearance exception, test-only bypass, or new repository support was added. Expanding that scope would require a separate design and privacy decision, outside Phase 27.

### P27-03 — Successful smoke metrics can be mistaken for practical retrieval quality

**Severity:** Medium
**Status:** Clarified in the Phase 27 record and CLI documentation.

**Evidence:** `demo` and `evaluate` return perfect deterministic metrics on generated fixtures, and neither command reads a repository or runs the model-backed real-query workflow. Those metrics validate smoke/evaluator wiring only.

**Disposition:** Record the boundary explicitly. No new benchmark claim or evaluation data was created.

### P27-04 — Real-corpus usability remains unassessed

**Severity:** Blocking for the requested end-to-end claim
**Status:** Open; intentionally not bypassed.

**Evidence:** The selected local repository is not one of the prototype's frozen approved snapshots, and no repository-specific secret/privacy clearance was available. The project's source-processing policy requires that review before parsing/embedding/indexing; embedding/index artifact APIs also fail closed without an approved identity and clearance. Therefore no chunks, embeddings, lexical/vector index, or retrieval results were generated for it.

**Disposition:** Report “not validated,” not “retrieval failed” or “retrieval helped.” No source was submitted externally, clearance was not fabricated, and no private internal test helper was used to bypass the gate. A separately authorized and cleared real-repository workflow is needed to close this finding.

## Validation matrix

| Area | Result | Evidence |
|---|---|---|
| Fresh install | PASS | Python 3.14.7; full locked dependency install; package install; `pip check` clean. |
| CLI discovery | PARTIAL | Supported commands are listed; no arbitrary-repository ingest/index/search command exists. |
| Configuration | PARTIAL | YAML/environment configuration is documented/tested but does not expand the fixed repository set or end-to-end workflow. |
| Error handling | FIXED | Existing-directory `validate` regression covered; focused test passes. |
| Synthetic smoke workflow | PASS | Demo, JSON evaluation, and replay pass; these use generated fixtures only. |
| Full tests | PASS | Exact v0.1.1: 142 passed, 0 skipped. Post-fix working tree: 143 passed, 0 skipped, including offline model integration. |
| Real repository parse/index/query | NOT RUN | Clearance and supported-workflow prerequisites were not met. |
| Benchmark/Humanize protection | PASS | No benchmark or Humanize paths changed; no dataset growth or Humanize processing occurred. |

## Remaining friction and recommended next step

A developer can install the package and discover the smoke/validation commands, but cannot follow the requested general local-repository workflow from the CLI. Retrieval requires several library APIs and a repository-specific clearance chain not exposed as a simple user workflow. The safe next step is not to relax the current guards: define a separately approved, auditable local-repository workflow and its user-facing command/API documentation before claiming general usability. That is outside this phase's authorized scope.

## Final disposition

- **Software:** Improved (post-release CLI bug fix plus documentation clarification).
- **User workflow:** Issues found; real-repository workflow not validated.
- **Research:** Reproducible for fresh install, smoke commands, run replay, and full tests.
- **Benchmark:** DEFERRED.
- **Humanize:** COMPLETE / FROZEN.
