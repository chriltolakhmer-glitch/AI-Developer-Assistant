# Phase 29 — Developer Mode Real Repository Pilot

**Status:** Completed with usability limitations, 2026-09-28. One real Python
repository completed scan/index/query; a real TypeScript repository exercised the
unsupported-language path. These are developer usability observations, not
research benchmark results. No release or retrieval-methodology change was made.

## Scope

Only `prototype local scan`, `local index`, `local query`, and `local demo` were
used for pilot operations. Local Git/status checks, filesystem audits and the
required test suites were validation operations. No pilot application was run,
no checkout was cloned or fetched, and no source was copied into a research
corpus. Source excerpts are not included in this report.

The two repositories were already local under `C:\Apps\Explore\projects`.
They remain excluded from primary evaluation as required by ADR-006. Their use
here does not change any research approval or candidate registry.

## Baseline and protected scope

- Initial and final HEAD: `9512581` (Phase 26.1 release verification).
- Package release version: `0.1.1`.
- Annotated `v0.1.1` tag object: `05688504f74ad51230ee1566fad8cda0f1b1ad97`.
- Peeled release commit: `51329285a882c1b7942d0a5b1c571e628d63dfb4`.
  Both tag identities and HEAD were checked before and after the pilot.
- The checkout was initially dirty with Phase 27/28 work: README, configuration,
  CLI, configuration/CLI tests, developer workflow code/tests and Phase 27/28
  documentation. This existing work was preserved, not reset or committed.
- SHA-256 inventories of tracked and nonignored project files distinguish this
  phase's edits from those pre-existing changes. Benchmark, Humanize, evaluation,
  parser, chunker, embedding and retrieval files were unchanged. Protected
  tracked paths also have no changes against `v0.1.1`.
- A before/after inventory of 8,892 existing external files under `C:\Apps\Temp`
  and the default research root showed no size/mtime/addition/deletion changes.
  It excludes Git internals, environments, bytecode, model caches, prior developer
  workspace directories and the new Phase 29 workspace. This is a filesystem
  metadata check, not a cryptographic revalidation of external research data.
  No frozen Humanize source was used as pilot input.

## Repository pilot metadata

Sizes below cover tracked/nonignored working-tree files, excluding `.git` and
ignored files; language mix is inferred from extensions, not a language detector.
Both working trees were clean before and after processing, and their file hashes
and commit identities matched.

| Repository identifier | Commit SHA | Language mix and approximate size | Developer approval |
|---|---|---|---|
| `local/codebase-rag-039fd2f87664` | `1bd600638dea12c3103cc95037f413690e2f4583` | 50 Python files, 3 shell files plus YAML/docs/config; 67 files, 230,000 bytes | User explicitly authorized local scan/index/query in this session. README declares MIT; referenced LICENSE file is absent. No redistribution or research permission is inferred. |
| `local/ai-codebase-assistant-33ca4b7134fc` | `6cd1bee3d28d9fa41b39d0439425b06733370b98` | 35 TypeScript files plus HTML/CSS/JSON/docs; 47 files, 953,755 bytes | Selected under the user's pilot authorization; local root LICENSE contains GPLv3. Local inspection only. |

The third nearby repository was not selected. Two repositories were sufficient
to exercise a supported workflow and a realistic unsupported-language case.

## Environment

- Windows, PowerShell, Python 3.14.7, CPU inference.
- Existing Phase 28 locked environment:
  `C:\Apps\Temp\Phase28-fresh-validation-20260928\venv`.
- `prototype.exe` from that environment, with `PYTHONPATH` pointing to the
  current `C:\Apps\Explore\AI-Developer-Assistant` source checkout.
- NumPy 2.5.3, FAISS CPU 1.15.1, Torch 2.14.0,
  sentence-transformers 6.1.0, transformers 5.17.0.
- Pinned MiniLM revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- Dedicated workspace: `C:\Apps\Temp\Phase29-developer-workspace-20260928`.
  Evidence, indexes, model cache, developer runs and temporary files stay here.
  The report and CLI/test edits are the requested project deliverables.
- Model files were copied from the previous **developer** workspace cache.
  No acquisition command or network download was needed. `HF_HUB_OFFLINE`,
  `TRANSFORMERS_OFFLINE`, `HF_HUB_DISABLE_TELEMETRY`, and `DO_NOT_TRACK` were set
  to `1`; bytecode writes were disabled in CLI/test subprocesses.
- Research defaults remained separate at `~/prototype-data`. Tests used
  sibling `test-research` and `test-developer` directories inside the Phase 29
  workspace, with temporary fixtures also confined there. These synthetic test
  records are distinct from pilot runs and existing research records.

## Commands executed

The exact argument arrays, exit codes, wall-clock timings and stdout/stderr are
retained in `WORKSPACE/evidence/*.json`; no source checkout is bundled there.
Using the environment above, the pilot command forms were:

```powershell
$workspace = 'C:\Apps\Temp\Phase29-developer-workspace-20260928'
$repo = 'C:\Apps\Explore\projects\codebase-rag'
prototype local scan $repo --workspace $workspace
prototype local index $repo --workspace $workspace
prototype local index $repo --workspace $workspace
prototype local query QUESTION --repository $repo --workspace $workspace

$repo = 'C:\Apps\Explore\projects\ai-codebase-assistant'
prototype local scan $repo --workspace $workspace
prototype local index $repo --workspace $workspace
prototype local query QUESTION --repository $repo --workspace $workspace
prototype local demo --workspace $workspace
```

Eight Python questions and five TypeScript questions were prepared and executed;
the cache-expiry question and the demo were each repeated. Queries used the
default ten results. Two additional `local scan` calls deliberately selected a
workspace inside the Python checkout and inside the research root. Both returned
exit 2 before creating either target directory; safeguards were not bypassed.

## Scan and index observations

| Observation | Python pilot | TypeScript pilot |
|---|---|---|
| Scan | Exit 0, 0.477 s | Exit 0, 0.422 s |
| Supported files / estimated code volume | 50 Python / 4,789 nonblank, non-comment lines | 0 Python / 0 supported-code lines; TypeScript LOC not estimated |
| Excluded Python files | 0 | 0 |
| Unsupported types | `.ini`: 1, `.md`: 5, `.sh`: 3, `.txt`: 1, `.yml`: 3, no extension: 4 | `.css`: 1, `.example`: 1, `.html`: 1, `.json`: 2, `.map`: 1, `.md`: 1, `.ts`: 35, `.yml`: 1, no extension: 4 |
| Initial index | Exit 0, 14.503 s | Exit 2, 0.427 s; no Python chunks |
| Parser outcome | 50 parsed files, 0 failures | No supported files; not a parser failure |
| Chunks | 315 produced; 194 indexed; 121 rejected for empty/over-limit input | No searchable index |
| Repeated index | Exit 0, 14.077 s, `already indexed` | Not applicable after unsupported-only failure |

No scan errors occurred. Unsupported-file notices were visible; the TypeScript
scan explicitly warned that indexing was unavailable. Included/excluded counts
are available in developer run JSON; scan stdout does not list each file or show
all metadata. No source files were added to research datasets.

The Python working-tree identity is
`aa7a36bc0f32a245fa533cd87ca4b9aa942fbc1497a02f4ef04bf8926ff65664`.
Its index is under `WORKSPACE/indexes/local-codebase-rag-039fd2f87664/` followed
by that identity. The manifest records the repository commit, runtime/model
contract, counts and artifact checksums. Documents, vectors, manifest and active
pointer were byte-identical after repeated indexing. This validates reuse in this
environment, not independent rebuilds across machines. First-build and reuse run
IDs differ because their status differs; this is expected.

## Queries and source traceability

These are qualitative navigation observations, not gold labels, benchmark
questions, accuracy scores or retrieval-methodology changes. Full query/result
records remain in the private developer workspace. All 80 returned references
from the eight Python questions matched indexed chunk metadata and valid source
line bounds. Relevant locations were also inspected in the unchanged checkout.
The CLI generates no answer text; answer synthesis therefore was not evaluated.

| Python question | Manual observation |
|---|---|
| Where is configuration loaded from environment variables? | Miss: the settings file had no indexed chunks, and results did not locate configuration loading. Successful indexing did not imply coverage of this file. |
| Which module saves and loads the FAISS vector index? | Useful: index wrappers appeared near the top; concrete save/load methods appeared at ranks 6 and 7. |
| Where are API query requests handled? | Handler found at rank 10; frontend health helpers and test scripts ranked above it. Requires reviewing the result list. |
| How are expired cache entries detected? | Directly useful: cache lookup/expiry implementation ranked first. |
| Where are GitHub repositories cloned and updated? | Partial: loader initialization ranked first and update implementation at rank 10; clone implementation was absent from returned results. |
| How are source languages mapped to parsers? | Directly useful: parser constructor, parsing and initialization methods led the results. |
| Where are OpenAI completion requests created? | Useful request-creation method at rank 6; embedding-related helpers ranked higher. No API requests were executed. |
| Where are search intent and query filters extracted? | Useful: query parsing and intent detection ranked first/second; filter logic appeared at rank 9. |

Python query processes took 5.971–7.178 seconds each. The repeated cache question
returned identical ranked output and the same developer run ID
`aef03525c77f87449ec4`; it took 6.199 seconds.

The TypeScript questions asked where configuration is loaded, which module owns
database access, where API routes are registered, how files are scanned for
ingestion, and where LLM requests are created. All five returned exit 2, with no
index available. Retrieval relevance could not be assessed. The query error
suggested indexing, which is an unhelpful recovery loop for an unsupported-only
repository. No language support was added or implied.

## Successful workflows and demo

The authorized Python checkout completed scan, real offline dense/BM25 indexing,
queries and repeat operations without changing source files. Isolation checks
rejected source/research overlap, and pilot run metadata uses developer mode.
No research run was created by a pilot command.

`local demo` completed in 0.312 seconds with three generated in-memory chunks;
the repeat took 0.320 seconds. The fixture and non-benchmark notice are explicit.
A workspace before/after check found only the harness's captured demo log changed:
the demo itself wrote no artifact or run record. It neither opens a repository
nor proves that a chosen workspace/model cache is usable. Its simple output is
understandable in a walkthrough, but no independent new-developer study was run.

## Failure cases, friction and missing capabilities

- Python-only support prevents use on the TypeScript application. The query
  recovery message does not distinguish unsupported source from an unbuilt index.
- Empty/oversized rejection removes useful coverage. The CLI shows totals but
  not rejected file/symbol details; the settings miss is consequential. The frozen
  token/chunking contract was not changed.
- Repeated indexing still reparses and embeds before noticing the stored index;
  observed reuse time was nearly the same as the initial build.
- Each query process loads the model again. Several seconds of startup are
  noticeable for interactive navigation.
- Results can emphasize tests, generic helpers or related subsystems. Source
  navigation is useful but requires manual judgment and opening the editor.
- No generated answers, source previews, machine-readable stdout option,
  complete per-file scan report or incremental indexing are available here.
- Developer approval is an operator responsibility, not a CLI approval record.
  The Python repository's incomplete license packaging needed explicit user
  clarification before processing.
- The focused suite initially failed twice during temporary repository cleanup
  with Windows sharing violation 32, after the workflow assertions passed. A
  bounded retry for that specific cleanup error resolved validation. The cause
  of the brief external directory lock was not independently identified.

## Security and privacy observations

Only locally authorized inputs were selected. Neither public availability nor a
research approval was treated as developer clearance. No target application was
imported or executed, no hosted inference was used, and repository Git histories
were not modified. Offline model settings and local workflow code support this
local-only conclusion; packet capture was not performed.

The new workspace initially inherited `BUILTIN\Users` read/append/create access.
After discovery, inheritance was removed and access restricted to Administrators
and SYSTEM; descendant index permissions were checked. This hardening occurred
after the first index had been produced, so there was an initial interval with
the inherited access policy. The CLI itself does not enforce restrictive ACLs.
No unauthorized access was observed or audited. Future pilots should check ACLs
before any source-derived write.

Query text, lexical tokens, vectors and provenance are sensitive derived data
and remain inside the dedicated workspace. No raw secrets are recorded in this
report. This pilot is not a comprehensive secret scan or license audit, and
approval is limited to local developer use. Benchmark expansion remains deferred;
Humanize remains unchanged and frozen.

## Regression coverage and validation

`tests/test_developer_mode.py` now retries temporary-directory cleanup only for
Windows sharing violation 32, up to one second. Persistent locks and unrelated
errors still fail. No workflow implementation, benchmark/Humanize tests or
evaluation methodology changed. Existing developer tests already cover read-only
scans, unsupported repositories, repeatability, isolation and CLI routing, so no
redundant new test cases were added.

Validation commands:

```text
git diff --check
python -m unittest discover -s tests -p test_developer_mode.py -v
python -m unittest discover -s tests -v
```

Focused result: **9 passed**. The first complete suite passed with two offline
integration tests skipped because their cache environment variable was unset.
After pointing `EMBEDDING_MODEL_CACHE` to the existing workspace model cache,
the complete suite passed **153 tests, 0 skipped**. Test-generated synthetic
research records were confined to workspace test directories. No existing
research run, benchmark expansion, Humanize artifact or evaluation snapshot was
changed. `git diff --check` passed.

Phase 29 deliverables are this report, the scoped developer-test cleanup change
and developer CLI documentation clarifications. All other pre-existing working
changes remain as they were. `v0.1.1` is unchanged; this work is not a new release.

## Recommended Phase 30 improvements

1. Report rejected file/symbol coverage and distinguish unsupported-language
   errors from missing-index errors. Make retrieval-only output and partial
   coverage prominent in onboarding.
2. Add workspace-permission guidance/checks before source-derived writes, and
   make local approval expectations easy to record without creating research
   clearance records.
3. Avoid redundant inference when a verified matching snapshot already exists;
   retain integrity, runtime, source-identity and separation checks.
4. Consider an optional persistent local query session and structured output,
   with source navigation conveniences and no change to ranking methodology.
5. Document that the generated demo is an interface example, then conduct a
   separate novice walkthrough of scan/index/query with an approved repository.
   Treat additional languages or chunking changes as separately scoped future
   work; do not alter the frozen research comparison to address pilot findings.
