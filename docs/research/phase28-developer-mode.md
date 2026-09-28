# Phase 28 — Separate Local Developer Mode

**Status:** Implemented in the current source tree. Research workflows and their artifacts remain separate and unchanged; the published v0.1.1 tag is immutable and does not contain this phase's changes.

> **This is a local developer workspace. Results are not benchmark results.**

## Purpose

`prototype local` lets a developer explore an arbitrary existing local Git repository using the current Python parser, semantic chunker, pinned local embedding model, FAISS dense index, BM25 lexical index, and fixed reciprocal-rank fusion. It is a personal utility for testing whether local retrieval helps with a code-navigation question. It creates no research approval, benchmark candidate, question, annotation, evaluation result, or Humanize access.

No source checkout is cloned, fetched, or modified. Developer indexes and run records are local source-derived data; protect and delete them as carefully as the repository source.

## Developer mode versus research mode

| | Research mode | Developer mode |
|---|---|---|
| Commands | `prototype validate`, `prototype evaluate`, `prototype reproduce RUN_ID`, and generated-fixture `prototype demo` | `prototype local scan PATH`, `prototype local index PATH`, `prototype local query QUESTION`, `prototype local demo` |
| Purpose | Existing pinned research preprocessing and controlled smoke/reproduction workflow | Personal local-repository exploration and retrieval usefulness checks |
| Inputs | Fixed research snapshots/fixtures under existing research rules | Any existing local Git working-tree root, subject to local-storage separation |
| Persistent output | `data_root` paths, including research corpus, validation output and research command runs | Only `developer_workspace`, including indexes, model cache and developer runs |
| Governance/evaluation | Research protocols and existing privacy gates continue to apply | No approvals or research governance records are created; no benchmark metrics/claims are produced |
| Humanize | Existing artifacts remain frozen and research-only | Never opened, read, or modified by local commands |

Research and developer modes share existing code components but not workflow entry points, artifact roots, run trackers, candidate lists, clearance manifests, or evaluation records. The local indexer has its own versioned, source-derived artifact format; it does not write the research embedding/vector/BM25 artifact formats.

## Installation

Use Python 3.11 or newer. From a source checkout, Windows PowerShell setup with the complete pinned retrieval environment:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install .
python -m pip check
prototype --help
prototype local --help
```

The workflow implementation is in the current source tree; published v0.1.1 binaries/tags remain unchanged. Local dense indexing and text queries use the pinned MiniLM model on CPU. If it is not already cached in the developer workspace, acquire only the declared public model weights explicitly (network is used only for this download):

```powershell
$env:PROTOTYPE_DEVELOPER_WORKSPACE = "$HOME/.prototype/developer-workspace"
python -m src.embedding.acquire --cache "$env:PROTOTYPE_DEVELOPER_WORKSPACE/model-cache"
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:DO_NOT_TRACK = '1'
```

Acquisition accepts no repository source. Indexing and query inference run locally with cached model files. `prototype local demo` uses generated in-memory code and does not need the model cache.

## Example workflow

Run commands from the project environment. Quote Windows paths containing spaces.

```powershell
$repo = 'C:\work\my-application'
prototype local scan "$repo"
prototype local index "$repo"
prototype local query "Where is the session token loaded?" --repository "$repo" --top-k 10
prototype local demo
```

`scan` reports the existing commit, a working-tree content identity, eligible Python file/code-line counts, and unsupported file extensions. It reads files and Git metadata but does not write to the repository. `index` reparses the current working-tree contents, chunks supported Python files, produces local embeddings, and builds dense/lexical retrieval artifacts. `query` checks that the repository still matches the indexed working-tree identity, searches both channels, fuses ranks, and prints ranked file/symbol/line provenance. When more than one repository has an index, pass `--repository PATH` to select it. Use `prototype local query --help` for all options.

The local indexer excludes scanner-designated generated/vendor paths and reports unsupported extensions; Python is the only parser supported here. Parse/read failures are reported per file in the local run record, and valid files can still be indexed. Chunks rejected for empty or greater-than-256-token input are counted; source is not silently truncated. No result or metric is evidence of benchmark performance or research usefulness.

## Storage locations and isolation

Research and developer roots have distinct defaults:

- Research: `~/prototype-data` (`data_root`), with `corpus/`, `validation/`, `runs/`, and the research `model-cache/` as configured.
- Developer: `~/.prototype/developer-workspace`, overridable by YAML `developer_workspace`, `PROTOTYPE_DEVELOPER_WORKSPACE`, or `--workspace PATH` on any local subcommand. It contains:
  - `indexes/<repo-name-and-local-id>/<working-tree-sha256>/`: local dense vectors, lexical tokens, provenance, integrity manifest.
  - `indexes/<repo-name-and-local-id>/active.json`: selected developer index for convenient queries.
  - `model-cache/`: locally acquired pinned model weights for developer operations.
  - `runs/<run-id>/`: local JSON results and run metadata, including query text for query commands.
  - `tmp/`: workspace-scoped temporary directory (normally empty after commands complete).

Config validation rejects overlapping developer and research storage roots. Local commands also reject a workspace inside the source repository, a source path overlapping research storage, and any write target that overlaps either. Research `RunTracker` and research commands do not write into the developer workspace; developer commands do not create research runs or write to `data_root`. Do not point both modes at a common parent/shared output path. Keep source-derived developer artifacts private, access-controlled, backed up only under your own data policy, and delete the workspace when no longer needed.

## Privacy expectations

- Use this mode only for code you are authorized to inspect. The developer is responsible for repository licenses, secrets, personal/confidential material, and local storage access.
- Do not point developer commands at the frozen research corpus, benchmark/evaluation directories, Humanize checkout or Humanize pilot artifacts. Humanize and research artifacts remain read-only and outside this personal workflow.
- No repository source, chunks, queries, embeddings, or indexes are uploaded by the local workflow or sent to a hosted model/vector service. Do not enable external services around the CLI that collect command output or workspace contents.
- Model acquisition downloads pinned public model files; it is separate from indexing and accepts no source input. After acquisition, set the documented offline environment for indexing/query if strict offline operation is desired.
- The source tree is opened read-only. Local indexes, tokens, vectors and query-bearing run records are derived source data and remain on the developer's machine.
- Research privacy/approval records do not authorize developer processing, and developer use does not authorize research corpus processing.

## Reproducibility notes and limitations

- A local repository must be an existing Git working-tree root with a valid `HEAD`. Local mode never clones/fetches. It hashes eligible on-disk Python contents plus the commit to identify a working-tree snapshot, so uncommitted edits are included; running `index` again after source changes builds/selects the matching snapshot, and a stale index is rejected at query time.
- Repository IDs include a normalized local path-derived suffix to avoid collisions between different local repositories with the same directory name. Moving a checkout creates a different developer identity.
- Repeated scans, index builds and queries for the same repository path, bytes, model/runtime contract and query produce stable IDs/rankings. Index files are checksummed and existing snapshots/run records are not overwritten. Python, NumPy, FAISS, tokenizer/scoring contract and model revision are recorded/validated; different runtimes can require a rebuild.
- The parser currently supports Python `.py` only. Other file types are counted and ignored. Generated/vendor and common environment directories are excluded. This is a local developer convenience, not a general multi-language indexer.
- The release supports retrieval-only outputs. It does not generate answers, analyze runtime behavior, evaluate against labels, compute benchmark metrics, or make claims about usefulness beyond the developer's manual inspection.
- Dense chunks over the fixed model token limit are rejected rather than silently truncated. If useful definitions are rejected, the command reports counts/reasons; chunking policy changes are outside this phase.
- `prototype local demo` uses a synthetic in-memory fixture to demonstrate the interface; its result is not from a repository and is not a benchmark.

## Regression and scope validation

Focused tests cover local repository path handling, read-only scans, unsupported-only repositories, workspace separation, local index/query reuse with a fake encoder, deterministic result/run identities, CLI discovery/error output, and local demo behavior. The full existing research test suite remains the regression gate. Humanize and benchmark files, candidate registries, scoring methodology, evaluation outputs and research run records are not modified or consumed by developer commands.

Phase 28 validation on Windows/Python 3.14.7 used a fresh locked environment and a generated, temporary Python Git repository. Research `validate`/`evaluate`/`demo`/`reproduce` and developer `scan`/`index`/`query`/`demo` all completed; model inference ran offline with the pinned local cache. The candidate checkout remained clean. Research records were under the temporary research root; the dense+lexical index, model-cache copy, and developer run records were under a different temporary developer root. The final full suite passed 153 tests, 0 skipped. Detailed process logs and temporary data remain outside Git under `C:\Apps\Temp\Phase28-fresh-validation-20260928`.

This validation exercises a generated local codebase to establish the user path, not Humanize, a benchmark corpus, or a relevance-quality claim. The released v0.1.1 tag SHA remains `51329285a882c1b7942d0a5b1c571e628d63dfb4`; Phase 28 work exists only in the current working tree. No benchmark/Humanize/evaluation/retrieval-methodology paths changed against that baseline.
