# Phase 30 — Developer Mode Retrieval Hardening

**Status:** Implemented and validated on 2026-09-28 as post-release development.
Developer-only diagnostics, index reuse, navigation ranking and workspace UX are
improved. No research benchmark improvement is claimed.

## Baseline and scope

HEAD remains `9512581d382ff1b66ff40d0eb90ccef6d14aabb9`. The starting working tree
already contained Phase 27–29 changes. A file-hash/status inventory was captured
before editing; those changes were preserved. The published release remains:

- `v0.1.1` annotated tag object: `05688504f74ad51230ee1566fad8cda0f1b1ad97`.
- Release commit: `51329285a882c1b7942d0a5b1c571e628d63dfb4`.
- Baseline test count: 153, as validated in Phase 29.
- Baseline developer commands: `local scan`, `local index`, `local query`,
  `local demo`. Phase 30 adds `local inspect` and JSON output for repository
  commands. The generated developer demo remains unchanged.

Phase 29 identified missing chunk coverage, redundant inference during repeat
indexing, noisy navigation results and inherited workspace permissions. This
phase addresses those findings in `src/developer` and the `local` CLI branches.
Shared scanner/parser/chunker, embedding, BM25, vector search, RRF, evaluation
code and research CLI execution are unchanged. Benchmark/Humanize tests and
artifacts were not edited. No release tag, research question or dataset changed.

## Coverage diagnostics

```powershell
prototype local inspect PATH --workspace WORKSPACE
prototype local inspect PATH --workspace WORKSPACE --json
```

Inspection reports:

- Git tracked and nonignored untracked paths scanned, included and excluded;
  per-file inclusion/exclusion reason and hashes for eligible Python files.
- Unsupported file types, generated/vendor/environment exclusions, missing
  files and redirected paths. Ignored untracked files are not enumerated.
- Generated chunks, file/symbol/line provenance, exact token counts when the
  pinned cached model is available, and eligible/empty/over-limit/unknown totals.
- Parser failures, skipped chunks, whether the active v2 index matches current
  source, and which chunks are present in that current index.

Inspection never downloads a model or produces embeddings. It currently loads
the cached model to obtain its tokenizer; without that cache, file/parsing
diagnostics still work but nonempty chunk token eligibility is **unknown**.
Eligibility and actual active-index membership are reported separately. Source
language support remains Python only; no code is silently truncated.

The authorized Phase 29 Python pilot still has 67 listed files, 50 included
Python files, 17 unsupported files, 315 generated chunks, 194 searchable chunks,
10 empty chunks, 111 oversized chunks and no parser failures. Inspection now
explains the missing configuration result: its module, class and initializer
chunks have 672, 636 and 633 tokens, respectively, above the unchanged 256-token
limit. Diagnostics expose this gap; they do not claim to repair it.

## Index reuse and compatibility

The versioned developer format is `developer-local-index-v2`, stored under:

```text
WORKSPACE/indexes/REPOSITORY_ID/v2/WORKING_TREE_SHA256/
    manifest.json
    documents.json
    vectors.npy
    state.json
```

`state.json` caches source chunks, file hashes, parse failures and rejection
details. It is source-bearing private data, not just index metadata. Manifest
checksums cover documents, vectors and state. Runtime/model compatibility and
artifact integrity are checked before reuse.

An unchanged index verifies commit and eligible working-tree file hashes, loads
the validated snapshot and skips parsing, tokenization and model inference. A
changed working tree at the same commit reparses/re-embeds only new or changed
files, reuses unchanged chunks/vectors and removes deleted files. Combined index
artifacts are assembled into a new immutable snapshot; existing snapshots are
not edited. Before publishing a rebuilt index, a second scan rejects source
changes that occurred during the build.

A changed commit triggers a full rebuild because chunk IDs bind commit identity.
There is no cross-commit embedding reuse claim. File reuse counts refer to
eligible Python files; chunk reuse/rebuild counts refer to searchable embedded
chunks. Generated/rejected totals are reported separately. No-op reuse still
reads files, verifies artifacts and reconstructs in-memory search structures.

Older Phase 28/29 v1 snapshots are untouched. Current developer queries require
one v2 build, with a separate v2 active pointer. Corrupt or incompatible snapshots
fail closed; they are not silently overwritten. See the CLI guide for a manual
workspace-scoped reset. Published v0.1.1 and research behavior remain unchanged;
these developer format and ranking changes are explicitly post-release.

## Developer ranking and explanations

`developer-navigation-v1` applies transparent navigation preferences after the
unchanged dense/BM25 candidate retrieval and shared RRF function. Each query run
records question text, retrieved paths/spans, raw channel scores and ranks, base
RRF score, final score, lexical/vector/hybrid source and ranking explanation.

The documented preferences are:

1. Match query terms against paths and qualified symbols, with a small fixed
   normalization map for configuration/authentication/routes/connections.
   The metadata factor is `1 + 0.20 * min(matched terms, 3)`.
2. Multiply test-path results by `0.70` unless tests are explicitly requested.
3. Multiply module/class containers by `0.85` to favor concrete definitions.
4. Select results greedily, suppress overlapping ranges within a file, and use
   `1 / (1 + 0.1 * already selected results from that file)` as a soft diversity
   factor. Distinct methods from the same file have no hard numerical cap.

Every factor and the multiplication formula are available in `query --json`
and private run JSON. Text output shows the source, matches and factors. A hard
two-results-per-file experiment was rejected during development because it hid
distinct useful methods. The final implementation uses the soft preference above.
No benchmark labels or scores were used to choose these rules.

This is a navigation heuristic, not an answer generator or a confidence score.
It cannot recover chunks excluded by the embedding contract, and it can still
return weak matches. The candidate window remains 50 per retrieval channel.
Shared research scoring constants, functions and evaluation methodology remain
unchanged.

## Developer fixtures and real-repository observations

Synthetic developer tests cover configuration, API routes, authentication and
database connections, with a test-file distractor. They assert that expected
files appear among the first three results and that explanations/component scores
are present. Further cases check overlap removal and explicit requests for tests.
These are ordinary software regression fixtures using deterministic fake vectors;
they are not a benchmark dataset or a measurement of embedding quality.

Real offline usability checks reused the previously authorized
`local/codebase-rag-039fd2f87664` checkout at
`1bd600638dea12c3103cc95037f413690e2f4583`. Its source hashes and clean Git state
were unchanged. The eight Phase 29 navigation questions were rerun without
introducing benchmark scoring. Examples from the final output:

| Navigation task | Phase 29 observation | Phase 30 observation |
|---|---|---|
| Configuration loading | Missing | Still missing; oversized chunks now explained |
| API query handler | Rank 10 | Rank 1 |
| Completion request creation | Rank 6 | Rank 2 |
| Cache expiry | Rank 1 | Rank 1 |
| Vector persistence | Concrete save/load at 6/7 | Concrete save/load at 4/6; wrappers still near the top |
| Repository update | Update method at 10 | Update method at 9; clone implementation still absent |
| Parser setup | Constructor/parse/setup led results | Setup at 1, constructor at 3, parse at 7; a generic source-reference class at 2 remains noise |
| Intent and filters | Intent at 2, filters at 9 | Intent at 1, filters at 3; parse wrapper at 7 |

These small, disclosed observations establish practical behavior, not general
retrieval quality or a research comparison. The configuration miss and unrelated
results remain limitations. No additional real repository was approved or added
to a research corpus.

## Indexing timings

Wall-clock process timings include CLI startup. These are single-machine local
observations, not controlled performance benchmarks. Windows/Python 3.14.7 and
the same pinned CPU model/cache were used. Some synthetic checks overlapped
validation processes, so timings should not be interpreted as precise speed ratios.

| Operation | Seconds | Reused files / rebuilt files | Reused chunks / rebuilt chunks |
|---|---:|---:|---:|
| Phase 29 real initial index | 14.503 | No reuse | 0 / 194 |
| Phase 29 real repeat | 14.077 | Reparsed/re-embedded all | Re-embedded 194 |
| Phase 30 real initial v2 index | 14.482 | 0 / 50 | 0 / 194 |
| Phase 30 real unchanged repeat | 0.620 | 50 / 0 | 194 / 0 |
| Three-file synthetic initial index | 7.252 | 0 / 3 | 0 / 6 |
| Synthetic unchanged repeat | 0.542 | 3 / 0 | 6 / 0 |
| Synthetic one-file edit | 7.948 | 2 / 1 | 4 / 2 |
| Synthetic one-file deletion | 0.755 | 2 / 0 | 4 / 0 |

The one-file edit still pays model startup cost; reduced embedded work does not
guarantee a shorter cold process on tiny repositories. Query processes still load
the model per invocation. No persistent model service was introduced.

## Workspace UX and privacy

Repository commands display the resolved workspace and distinguish existing
storage from creation after separation checks. Creation requests private mode;
existing ACLs are not rewritten. A temporary-file probe catches write denial.
Errors explain invalid directory paths, permission/free-space problems, source
or research overlap, and artifact paths redirected outside the workspace.
Unsupported-only queries now explain the Python limitation instead of directing
the developer into an impossible index/query loop.

The new pilot area is `C:\Apps\Temp\Phase30-developer-workspace-20260928`.
Its ACL was restricted to Administrators and SYSTEM before source-derived work.
Real indexes, cache and runs are here; the generated synthetic repository and its
separate sibling workspace are also inside this area. Test-only research and
developer roots are siblings here, separate from existing research storage.
The cached model was copied from the prior developer cache. Offline and
telemetry-disabled environment settings were used; no model download was needed.

The CLI guide documents JSON diagnostics, v2 compatibility, checking effective
permissions, and manual reset/retention steps. No destructive reset command was
added. Before resetting, stop local commands, verify the resolved developer path,
and move only the affected v2 index directory to a retired location inside that
workspace. Source checkouts and research storage must never be cleanup targets.

Source-bearing state, tokens, vectors and query records all require source-level
privacy. This phase does not grant repository permission, audit repository
licenses/secrets or imply approval for research use. Filesystem checks are not a
security boundary against another process actively changing symlinks or artifacts
during an operation; use a private workspace and avoid concurrent writers.

## Validation and protected-state checks

- `git diff --check` passes.
- Focused developer suite: **21 passed**, up from 9.
- Full suite with the offline model cache: **165 passed, 0 skipped**, up from 153.
- Regression checks include no model/parse call on unchanged reuse; changed,
  removed and committed files; identical cold/incremental artifacts under the
  deterministic fixture encoder; checksum failure; mid-build edits; stale
  queries; parser/coverage diagnostics; JSON output; ranking explanations;
  write denial; redirected paths; and research/source workspace separation.
- A Windows temporary Git-directory cleanup race also produced error 145
  (directory not empty). The existing bounded cleanup retry now handles that
  code as well as sharing violation 32; persistent/unrelated errors still fail.
- Project baseline hashes limit changed existing files to developer workflow,
  local CLI integration, developer tests and CLI documentation. New files are
  developer ranking code and this report. Protected benchmark, Humanize,
  evaluation, embedding and retrieval files remain unchanged.
- All 8,892 previously inventoried external research-area files retain their
  size/mtime metadata. This checks existing files, not cryptographic content or
  newly created files across the whole machine. Test/pilot outputs stayed in
  the dedicated Phase 30 area. Prior developer index hashes also match.
- Both tag object and peeled `v0.1.1` commit remain unchanged. No commit, tag,
  release, research run or benchmark expansion was created by pilot commands.
  Full tests exercised their existing synthetic research paths only inside
  isolated test storage.

Commands, outputs, durations, baseline hashes and audits are retained privately
under `WORKSPACE/evidence`. Research remains unchanged; benchmark expansion is
deferred; Humanize remains frozen. Remaining developer work includes coverage
policy for large definitions, tokenizer-only inspection, query startup cost and
broader usability testing independent of these development fixtures.
