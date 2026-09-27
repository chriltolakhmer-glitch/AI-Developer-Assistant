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

**Phase 26.1 — Reproducible Research Prototype 0.1.1.**

| Area | Status |
|---|---|
| Humanize pilot | COMPLETE / FROZEN |
| Software | RELEASED RESEARCH PROTOTYPE |
| Research | REPRODUCIBLE |
| Benchmark expansion | FUTURE WORK |

The release packages the existing ingestion, Python parsing/chunking, indexing, retrieval, evaluation and validation utilities. The research workflow is reproducible; additional repositories, questions, annotation rounds, retrieval tuning/strategies, new experiments and scaling studies remain outside scope.

See the [release guide](docs/research/release-guide.md) for clean installation, commands, tests and reproduction. The [Phase 26 external-user validation report](docs/research/phase26-external-user-validation.md) records the earlier v0.1.0 blocker, and the [Phase 26.1 verification report](docs/research/phase26.1-release-verification.md) records the verified v0.1.1 public release. The [v0.1.1 release page](https://github.com/chriltolakhmer-glitch/AI-Developer-Assistant/releases/tag/v0.1.1) hosts the exact-tag manifest asset. The [software prototype scope](docs/research/software-prototype-scope.md) documents component boundaries. Humanize remains frozen; benchmark expansion is deferred. This is not a production release.

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
```

`prototype demo` parses and chunks a tiny generated Python fixture (three chunks), evaluates two synthetic queries, and prints MRR and nDCG. Its fixture is constructed to exercise the plumbing; perfect scores are not research results. `prototype evaluate --json` prints the per-query smoke report. Neither command accesses the network or Humanize artifacts. `prototype validate` checks only pinned local checkouts and never fetches them; without a corpus, `0/9` snapshots and `Preprocessing ready: no` are the expected result, not a successful corpus validation. Its defaults use `~/prototype-data/corpus` for input and `~/prototype-data/validation` for reports; override them with `--corpus-root` and `--output-dir`, or set `PROTOTYPE_DATA_ROOT` before starting the command. Reports and run records are written outside this project and the source checkouts.

Configuration defaults and environment overrides are documented in [prototype configuration](docs/research/prototype-configuration.md). Use `prototype --config PATH validate` for a complete external YAML configuration.

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
