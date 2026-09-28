# Phase 27 — Real User Workflow Validation

**Date:** 2026-09-28
**Status:** Partial — release installation, CLI smoke paths, and regression behavior were validated; a real-repository indexing and retrieval workflow was not run because the selected repository is outside the approved/cleared corpus and the release CLI does not expose general-purpose ingest/index/search commands.
**Release under test:** v0.1.1, commit `51329285a882c1b7942d0a5b1c571e628d63dfb4`.
**Scope:** No benchmark expansion, question/dataset creation, Humanize changes, repository additions, or retrieval-algorithm changes.

## Executive result

The v0.1.1 package installs in a new Windows/Python 3.14.7 environment, its documented smoke commands run, and the complete test suite passes. A small local Python repository was selected and inventoried without copying or publishing its source. The shipped `validate` command is for the fixed nine-snapshot corpus, not arbitrary repositories; it reported zero of nine snapshots for this candidate. The release version then crashed on that existing-directory path with `UnboundLocalError`. The issue was fixed in the current working tree and covered by a focused regression test. The fixed command now exits cleanly but still does not ingest the candidate.

No real-corpus parse/chunk, embedding, index build, or user query was performed. The selected repository has no repository-specific secret/privacy clearance, and the v0.1.1 embedding/index APIs intentionally fail closed for snapshots outside their approved allowlist. Creating a clearance attestation or bypassing those guards would not be a valid Phase 27 usability test.

## Selected local codebase

| Property | Observation |
|---|---|
| Repository | Existing local developer repository `Codebase-RAG-Assistant` under the workspace's `Explore/projects` tree; no repository was cloned or added for this phase. |
| Type | Small Python application/codebase-assistant project, based on its tracked Python application files and project identity. |
| Snapshot | `03ba3425109f4e3ba99243c5d2469cb221c32003` |
| Working-tree state | Clean before and after the metadata-only scan. |
| Size | 27 tracked files; 95,600 tracked bytes in the local working tree. |
| Language/file mix | 22 Python files, 1 HTML, 1 Markdown, 1 text, 1 `.example`, and 1 `.gitignore`. |
| Python inventory | 22 eligible tracked Python files; 1,127 eligible code lines using the released scanner's nonblank/non-comment count. No files were excluded. |
| Handling conditions | Local checkout only; scanner inventory retained in memory and only aggregate counts recorded here. No source text, manifest, chunks, embeddings, index, or per-file scan report was added to Git or copied into this report. Model inference settings were offline and telemetry disabled for the prototype smoke/tests. |
| Clearance condition | No repository-specific secret/privacy audit or clearance manifest was available. The candidate is not in the prototype's fixed approved corpus. Processing beyond the scanner's metadata-only inventory was therefore stopped. |

## Execution record

The release checkout was the detached v0.1.1 tag target, not the moving `main` branch. A fresh external virtual environment was created at `C:\Apps\Temp\Phase27-user-workflow-20260928\venv`; the exact dependency lock and released project were installed. Python was 3.14.7, `pip check` reported no broken requirements, and the existing pinned model cache at `C:\Apps\Temp\Phase6.2\model-cache` was used offline. Run artifacts and test logs stayed under `C:\Apps\Temp\Phase27-user-workflow-20260928`, outside the repository and candidate checkout.

| Step | Outcome |
|---|---|
| Install `requirements-lock.txt`, install the v0.1.1 package, and run `pip check` | PASS in a new virtual environment. |
| `prototype --help` | PASS; it lists `validate`, `evaluate`, `demo`, and `reproduce`. It does not list arbitrary-repository ingestion, indexing, or search commands. |
| `prototype demo` | PASS; reports three chunks and two queries from generated `demo.py` fixture data. This is not a real-repository retrieval run. |
| `prototype evaluate --json` | PASS; machine-readable generated-fixture smoke report. Its perfect metrics are synthetic and are not retrieval-quality evidence. |
| `prototype validate --corpus-root <candidate> --output-dir <external path>` on unmodified v0.1.1 | The pipeline report recorded 0/9 expected snapshots and `preprocessing_ready: false`, then the CLI raised `UnboundLocalError` and exited 1. The command expects the fixed approved snapshot layout; it did not parse the candidate. |
| Same validation command after the narrow fix in the current working tree | PASS as a CLI invocation (exit 0); correctly reports 0/9 and `Preprocessing ready: no`. It still does not ingest the arbitrary candidate. |
| `prototype reproduce <tracked demo run id>` | PASS; replayed the demo payload. |
| Full test suite on exact v0.1.1 | PASS: 142 tests, 0 skipped, including the pinned model's offline integration tests. |
| Focused test for validate with an existing corpus directory after fix | PASS: 1 test. |
| Full suite on the post-fix working tree | PASS: 143 tests, 0 skipped. |

The release test log and post-fix test log are preserved outside Git at `C:\Apps\Temp\Phase27-user-workflow-20260928\full-suite.log` and `C:\Apps\Temp\Phase27-user-workflow-20260928\working-tree-full-suite.log`. The actual tracked demo run record is also external under that run's `data/runs/` directory.

## Real-workflow attempt and query record

The selected-repository attempt stopped after the metadata-only inventory and the `validate` CLI probe. The CLI's fixed nine-snapshot configuration does not accept a repository identity, expected SHA, or per-repository file/LOC baseline. The supported embedding and index APIs additionally require an approved snapshot and a matching completed clearance record. No clearance was invented and no private test helper was used to bypass those requirements.

The following are representative developer questions for the selected project's category, **not executed queries**:

| Task/query example | Retrieved result | Expected answer location | Did retrieval help? |
|---|---|---|---|
| Locate the request path from a user's question to the retrieval call. | None — no index was built. | Not established; source was not parsed or manually inspected. | Not assessable. |
| Find where the local index is created or loaded. | None — no index was built. | Not established; source was not parsed or manually inspected. | Not assessable. |

No query-specific relevance judgment, ranking, or answer-location claim is made. Existing unit/integration tests exercise synthetic fixtures only and do not substitute for this real-codebase check.

## Usability checks

| Check | Result | Evidence/qualification |
|---|---|---|
| Is installation understandable? | PASS | Release guide commands succeeded unchanged in a clean isolated environment; lock install, package install, and dependency check all passed. |
| Are CLI commands discoverable? | PARTIAL | `--help` clearly lists the four commands, but there is no general user command for ingest, index, or search. The v0.1.1 command surface cannot express the requested workflow. |
| Are errors actionable? | FAIL observed; fixed in working tree | Existing-directory validation crashed with an internal `UnboundLocalError`; it did not tell the user what to change. A focused regression test now covers the path. The fixed command produces the aggregate missing-snapshot/readiness result. |
| Is configuration easy to adjust? | PARTIAL | YAML and environment overrides are documented and covered by tests. They adjust prototype paths/settings, but do not add an arbitrary repository to the fixed approved snapshot set or create a retrieval workflow. |
| Are generated outputs understandable? | PASS for smoke / NOT AVAILABLE for real retrieval | Demo/evaluate summaries and aggregate validation report are legible. No ranked code results or provenance could be reviewed because the candidate was not indexed. |
| Can a developer reproduce the workflow? | PARTIAL | Clean installation, smoke runs, tracked demo replay, and both suites are reproducible. A real-repository end-to-end workflow is not currently reproducible through the supported CLI. |

## Scope and artifact verification

- No repository was added; the selected repository was already present locally.
- No benchmark questions, dataset rows, or evaluation claims were created.
- Benchmark and Humanize paths have no changes relative to the v0.1.1 tag; the Phase 27 edits are limited to CLI code, a focused regression test, and research documentation.
- The prototype did not create embeddings or indexes for the selected repository. Generated/synthetic test fixtures were temporary test inputs only.
- No retrieval-algorithm or benchmark change was made.

## Final status

- **Software:** Improved after the v0.1.1 validation run (one narrow CLI fix and a documentation clarification; the v0.1.1 tag itself remains unchanged).
- **User workflow:** Issues found; installation and smoke/reproduction flows validated, real-repository end-to-end workflow blocked/not validated.
- **Research:** Reproducible for the documented release/test/smoke runs; real-repository retrieval is not claimed.
- **Benchmark:** DEFERRED.
- **Humanize:** COMPLETE / FROZEN.

## Related records

- [Phase 27 usability findings](phase27-usability-findings.md)
- [Prototype CLI and scope boundary](prototype-cli.md)
- [Release guide](release-guide.md)
- [ADR-008 source-code privacy policy](../decisions/ADR-008-source-code-privacy.md)
- [ADR-014 embedding privacy policy](../decisions/ADR-014-embedding-privacy-policy.md)
