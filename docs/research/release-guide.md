# Research Prototype Release Guide

**Version:** 0.1.1
**Status:** Released Research Prototype
**Research status:** Reproducible
**Benchmark status:** Future work; no expansion started.

This release packages the existing software workflow only. It does not release or modify Humanize pilot data, benchmark questions, source checkouts, or research results.

The repository-root [source manifest](../../release-manifest.json) records the dependency/test contract and source baseline. The immutable GitHub Release provides a generated `release-manifest.json` asset whose `git_sha` is the exact tagged commit, plus the external-user verification report; a commit cannot contain its own commit SHA without a self-reference.

## Get the tagged source

From the parent directory where the checkout should be created, use the versioned tag rather than `main`:

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

The `git ls-remote` check must list the tag. If it fails or cloning reports `Remote branch v0.1.1 not found`, stop and request publication of the release tag; do not silently use the default branch. The downloaded release manifest asset binds the exact tag commit SHA without creating a self-referential commit hash.

## Installation

Use Python 3.11 or newer. This PowerShell example uses the tested Python 3.14 runtime, creates an isolated environment, installs the full exact-version lock, installs this package, and checks dependency consistency:

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

The install creates the `prototype` command. For a smaller CLI-only install, omit the lock-file step; `python -m pip install .` installs the declared base dependency. The lock composes the pinned retrieval and embedding requirements and is used for the full test suite/model-backed operations. Model-backed tests additionally need the pinned offline model cache.

For development, use `python -m pip install --editable .` instead of the final package-install command. The packaged default configuration is included in built distributions; custom configuration can be supplied with `--config PATH`.

## Quick start

```powershell
prototype --help
prototype demo
prototype evaluate
```

These smoke workflows use generated fixtures and do not read Humanize data or access the network. `demo` demonstrates parsing, chunking, and evaluation; `evaluate` reports deterministic smoke metrics, not benchmark results.

## CLI commands

| Command | Purpose | Data boundary |
|---|---|---|
| `prototype --help` | List supported commands and options. | No research data access. |
| `prototype demo` | Run a generated-fixture walkthrough. | Offline; no repository or benchmark input. |
| `prototype evaluate [--json]` | Run deterministic evaluator smoke checks. | Generated fixtures only; not a benchmark result. |
| `prototype validate [--corpus-root PATH] [--output-dir PATH]` | Validate already-present pinned local checkouts. | Never fetches checkouts; reports go to the configured external output directory. |
| `prototype --config PATH validate` | Run with an explicit YAML configuration. | Keep data, checkouts, caches, and outputs outside the repository. |
| `prototype reproduce RUN_ID` | Replay a tracked command and compare its standardized output. | Reads and writes run records under the configured external data root. |

Every executed command records a run under `PROTOTYPE_DATA_ROOT` (default `~/prototype-data`). Configure it before invocation to keep generated records external. Validation may complete successfully while reporting zero validated snapshots if approved local checkouts are absent; that is not evidence of corpus readiness.

## Experiment tracking

Run records contain normalized configuration, a configuration hash, software/Git identity, runtime metadata, structured results, and logs. Locate a run under `<data-root>/runs/`, inspect its `metadata.json` and `results.json`, then replay it with `prototype reproduce RUN_ID`. Reproduction compares the command payload; it does not compare timestamps or prove scientific validity. See [experiment tracking](prototype-experiment-tracking.md) and [configuration](prototype-configuration.md).

## Reproduction workflow

1. Install the release and record the release version, Git SHA, Python version, and dependency state (`python -m pip freeze`; `python -m pip check`).
2. Set `PROTOTYPE_DATA_ROOT` to a new directory outside the checkout.
3. Run `prototype --help`, `prototype demo`, and `prototype evaluate --json`.
4. Run `prototype validate` only against already-acquired, authorized, pinned checkouts; do not fetch or add data as part of this guide.
5. Find the demo run ID under `$env:PROTOTYPE_DATA_ROOT\runs` by checking each `metadata.json` for `"command": "demo"`; replay that ID with `prototype reproduce RUN_ID`. The [CLI guide](prototype-cli.md) includes a PowerShell example that selects the latest demo run rather than an arbitrary run.
6. Run the test suite from the project root: `python -m unittest discover -s tests -v`.
7. Preserve command output, release manifest, and environment metadata. Do not commit run records, source-derived artifacts, or private data.

## Tests and CI preparation

The project uses the standard-library `unittest` runner:

```powershell
python -m unittest discover -s tests -v
```

Recommended CI checks on Windows and Linux with the minimum supported Python and a current Python release:

1. Install the pinned research dependencies with `python -m pip install -r requirements-retrieval.txt`.
2. Install the project with `python -m pip install .`.
3. Check dependency consistency with `python -m pip check`.
4. Verify `prototype --help`, `prototype demo`, `prototype evaluate --json`, and the full unittest command.
5. For a packaging job, build/install the distribution in a fresh environment and run the CLI smoke commands outside the source checkout.

`requirements-retrieval.txt` pins the retrieval stack and includes the embedding lock. When changing dependencies, update the relevant requirement files deliberately, reinstall from scratch, run `pip check`, and run the full tests. The package metadata currently declares only the base CLI dependency; do not interpret the optional pinned retrieval stack as an implicit base installation requirement.

Model-backed tests may require the separately acquired pinned offline model cache. Keep `HF_HUB_OFFLINE=1` for offline operation; do not download a model or inspect benchmark data as part of CI preparation.

## Known limitations

- This is a released research prototype, not a production service or public benchmark/data release.
- `demo` and `evaluate` are generated-fixture smoke paths; their metrics make no claim about retrieval quality on Humanize or any corpus.
- `validate` requires local pinned checkouts and appropriate authorization; it does not acquire data. A missing corpus is reported as not ready.
- Full model-backed retrieval requires the pinned optional dependency stack and an externally managed model cache.
- Reproduction is payload-based and assumes compatible code, configuration, dependencies, runtime, and inputs; the manifest records the source Git SHA, while a dirty source tree must be disclosed separately.
- Humanize remains unchanged and frozen. Benchmark questions, methodology, and retrieval algorithms are unchanged; benchmark expansion remains deferred and was not started.
