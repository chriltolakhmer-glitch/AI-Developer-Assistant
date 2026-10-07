# AI Developer Assistant

## Project Purpose

This Master's thesis project builds and validates a working benchmark/retrieval research prototype. The current dataset is the frozen Humanize pilot: 12 validated questions with evidence mappings, answers and recorded retrieval results.

## Development Philosophy

- **Research first** — Investigate the problem space and existing work before writing code.
- **Analyze existing solutions** — Study comparable tools and architectures to identify gaps and opportunities.
- **Design before implementation** — Define architecture and decisions before building features.
- **Document every decision** — Record the reasoning behind significant choices as they are made.
- **Validate through experiments** — Use structured experiments and evaluation to confirm design assumptions.

## Current Phase

**Post-roadmap product direction (2026-10-08): UI first.** The developer roadmap through Phase 72 is complete; future product work is tracked separately in the [post-roadmap product development plan](docs/post-roadmap-product-plan.md). UI v1 will expose existing trusted capabilities before feature-specific test planning, implementation/test drafting, and supervised orchestration. This is planning only; no Phase 73 is created. The Phase 65 summary below records the earlier main-branch integration baseline.

**Main development through Phase 65 — evidence-grounded implementation planning.** The immutable v0.1.1 tag remains the research-prototype release baseline. The moving `main` branch separately integrates developer-mode work through Phase 65; none of that work changes or becomes part of v0.1.1.

| Area | Status |
|---|---|
| Humanize pilot | COMPLETE / FROZEN |
| Software | RESEARCH PROTOTYPE + SEPARATE DEVELOPER MODE |
| Research | REPRODUCIBLE / UNCHANGED |
| Benchmark expansion | FUTURE WORK |

The research workflow remains pinned, reproducible and governed separately. `prototype local` is for a developer's own local Python repository and writes rebuildable indexes, model cache, and personal run records only under a separate developer workspace. **This is a local developer workspace. Results are not benchmark results.** Local inputs do not become benchmark candidates, Humanize data is not read, and local runs are not research/evaluation records. The local parser currently supports Python `.py` files in existing Git working-tree roots; other file types are reported and ignored.

Quick local flow: `prototype local scan PATH`, `prototype local index PATH`, then `prototype local query "question" --repository PATH`. Use `prototype local change-impact PATH` to inspect an existing change, or `prototype local plan-change PATH --goal "..."` to turn current Git, symbol, relationship, retrieval, and affected-test evidence into a read-only implementation plan. Planning never edits source, runs tests, reindexes, or generates a patch. Run `prototype local --help` for options or `prototype local demo` for a generated fixture. Dense indexing/query requires a local copy of the pinned model; model acquisition instructions and privacy/storage limits are in the [Phase 28 guide](docs/research/phase28-developer-mode.md).

See the [release guide](docs/research/release-guide.md) for clean installation, commands, tests and reproduction. The [Phase 26 external-user validation report](docs/research/phase26-external-user-validation.md) records the earlier v0.1.0 blocker, and the [Phase 26.1 verification report](docs/research/phase26.1-release-verification.md) records the verified v0.1.1 public release. The [v0.1.1 release page](https://github.com/chriltolakhmer-glitch/AI-Developer-Assistant/releases/tag/v0.1.1) hosts the exact-tag manifest asset. The [software prototype scope](docs/research/software-prototype-scope.md) documents component boundaries. Humanize remains frozen; benchmark expansion is deferred. This is not a production release.

Use the [Phase 28 developer-mode guide](docs/research/phase28-developer-mode.md) for the personal workflow and storage/privacy boundary, the [Phase 64 change-aware workflow](docs/research/phase64-change-aware-developer-assistance.md) for integrated change analysis, and the [Phase 65 planning workflow](docs/research/phase65-evidence-grounded-implementation-planning.md) for deterministic evidence-grounded implementation plans. Main-branch developer changes do not rewrite the published v0.1.1 tag.

## Get the Release

Start from the published release tag, not the moving `main` branch. The release tag must be visible on the remote before a new user can clone it. In Windows PowerShell, run these commands from the directory where you want the checkout:

```powershell
$repoUrl = 'https://github.com/chriltolakhmer-glitch/AI-Developer-Assistant.git'
git ls-remote --exit-code --tags $repoUrl refs/tags/v0.1.1
git clone --depth 1 --branch v0.1.1 $repoUrl AI-Developer-Assistant
Set-Location AI-Developer-Assistant
$head = (git rev-parse HEAD).Trim()
$sourceManifest = Get-Content .\release-manifest.json -Raw | ConvertFrom-Json
$tagManifest = Invoke-RestMethod 'https://github.com/chriltolakhmer-glitch/AI-Developer-Assistant/releases/download/v0.1.1/release-manifest.json'
if ($sourceManifest.version -ne '0.1.1' -or $sourceManifest.git_tag -ne 'v0.1.1' -or $tagManifest.git_sha -ne $head) {
	throw 'Release manifest asset does not identify this tag checkout.'
}
```

If the tag check or clone reports that `v0.1.1` is missing, stop: the release tag has not been published. Do not substitute `main` for a release-tag validation. The in-tree manifest records the source baseline; the downloadable release manifest asset is generated after tagging so its `git_sha` can equal the immutable tag target. The release page also hosts the post-clone verification report.

## Quick Start

From the project root in Windows PowerShell, set up Python 3.14 (3.11 or newer is required), install the pinned environment, and install the package:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install .
python -m pip check
$env:PROTOTYPE_DATA_ROOT = "$HOME/prototype-data"
```

If PowerShell blocks `Activate.ps1`, allow it for the current session only, then activate the environment:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

The lock installs the complete retrieval/test environment. For only the generated-fixture CLI smoke paths (`demo`, `evaluate`, and `reproduce`), the smaller install is `python -m pip install .`; model-backed tests and retrieval need the pinned lock and offline model cache.

After activating that environment, the public commands are:

```text
prototype --help
prototype validate
prototype evaluate
prototype demo
prototype reproduce RUN_ID
prototype local --help
```

`prototype demo` parses and chunks a tiny generated Python fixture (three chunks), evaluates two synthetic queries, and prints MRR and nDCG. Its fixture is constructed to exercise the plumbing; perfect scores are not research results. `prototype evaluate --json` prints the per-query smoke report. Neither command accesses the network or Humanize artifacts. `prototype validate` checks only pinned local checkouts and never fetches them; without a corpus, `0/9` snapshots and `Preprocessing ready: no` are the expected result, not a successful corpus validation. Its defaults use `~/prototype-data/corpus` for input and `~/prototype-data/validation` for reports; override them with `--corpus-root` and `--output-dir`, or set `PROTOTYPE_DATA_ROOT` before starting the command. Reports and run records are written outside this project and the source checkouts.

Configuration defaults and environment overrides are documented in [prototype configuration](docs/research/prototype-configuration.md). Use `prototype --config PATH validate` for a complete external YAML configuration.

For local code exploration, use `prototype local scan PATH`, `prototype local index PATH`, and `prototype local query "question"`. These commands use the separate `~/.prototype/developer-workspace`; they do not write to `PROTOTYPE_DATA_ROOT`, benchmark/evaluation directories, or Humanize storage. Indexing requires the separately downloaded pinned model cache in that developer workspace. See the Phase 28 guide before indexing personal or sensitive code.

Every command creates an external run record under `$env:PROTOTYPE_DATA_ROOT\runs` containing configuration, metadata, standardized results, and logs. After running the demo, find its run ID and reproduce that specific run with:

```powershell
$run = Get-ChildItem "$env:PROTOTYPE_DATA_ROOT/runs" -Directory |
	ForEach-Object {
		$metadata = Get-Content (Join-Path $_.FullName 'metadata.json') -Raw | ConvertFrom-Json
		if ($metadata.command -eq 'demo') {
			[pscustomobject]@{ Id = $_.Name; Created = $_.LastWriteTime }
		}
	} |
	Sort-Object Created -Descending |
	Select-Object -First 1
if (-not $run) { throw 'Run prototype demo before looking up its run ID.' }
prototype reproduce $run.Id
```

Reproduction reruns the saved command/configuration and compares its standardized payload; it is a smoke-result check, not a reproduction of corpus retrieval results. See [experiment tracking](docs/research/prototype-experiment-tracking.md) for record contents and limits.

Run the full test suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

## Maintenance

See [Contributing](CONTRIBUTING.md), [Support](SUPPORT.md), and the [development workflow](DEVELOPMENT.md) for scope boundaries, environment setup, and validation steps.
