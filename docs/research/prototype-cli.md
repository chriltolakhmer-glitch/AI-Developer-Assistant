# Prototype CLI

The `prototype` command is the supported entry point for the local research prototype. The following Windows PowerShell setup uses the tested Python 3.14 runtime and the complete pinned dependency set. Python 3.11 or newer is required by the package.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install .
python -m pip check
$env:PROTOTYPE_DATA_ROOT = "$HOME/prototype-data"
prototype --help
```

For a CLI-only install, `python -m pip install .` installs the declared base dependency. The lock file is for the complete retrieval/test environment; model-backed operations also need the pinned model cache. The packaged default YAML is available without a source checkout.

## Commands

### `prototype validate`

Runs the scanner, parser, and chunker over already-present local checkouts. It never clones, fetches, or writes into a source checkout.

```text
prototype validate
prototype validate --corpus-root C:/research/corpus --output-dir C:/research/validation
```

Defaults are external to the repository: `~/prototype-data/corpus` and `~/prototype-data/validation`. The root can be changed with `PROTOTYPE_DATA_ROOT`. Missing or mismatched checkouts are reported in aggregate output rather than treated as permission to recover from the network.

### `prototype evaluate`

Runs a deterministic evaluation smoke check over generated fixtures. It validates the evaluator and metric wiring without reading the frozen Humanize pilot.

```text
prototype evaluate
prototype evaluate --json
```

The JSON form is suitable for shell capture or a lightweight reproducibility check. It is not a new benchmark result.

### `prototype demo`

Shows the parser, chunker, and evaluator flow over generated Python code:

```text
prototype demo
```

The demo is offline, repeatable, and source-independent.

### `prototype reproduce RUN_ID`

Replays a prior tracked `demo`, `evaluate`, or `validate` command and compares the standardized output. Find the ID in `$env:PROTOTYPE_DATA_ROOT\runs` (default: `$HOME\prototype-data\runs`). For example:

```powershell
$run = Get-ChildItem "$env:PROTOTYPE_DATA_ROOT/runs" -Directory | Select-Object -First 1
prototype reproduce $run.Name
```

Use the intended run directory if several runs exist; the example selects the first one only for illustration.

## Troubleshooting

- `prototype` is not recognized: activate `.venv` in the current PowerShell session, or invoke `& .\.venv\Scripts\prototype.exe ...`.
- Validation reports missing checkouts: the command still writes an aggregate report and exits successfully, but preprocessing readiness is `no`. Supply already-acquired, authorized pinned checkouts; it never fetches them.
- Invalid validation paths: check that the corpus root is a directory and the report output is writable and outside the project and source checkouts.
- Model-backed operations fail: configure the documented offline model cache and `HF_HUB_OFFLINE=1`; the CLI smoke commands do not require a model.