# Prototype Experiment Tracking

Phase 25 maintains lightweight run tracking around the public `prototype` commands. It records execution identity and aggregate outputs without copying source text, benchmark questions, annotations, or Humanize artifacts.

## Experiment Lifecycle

1. Load and validate the central configuration.
2. Create a run directory before executing the command.
3. Snapshot normalized configuration and compute its SHA-256 hash.
4. Execute the existing validation, evaluation, or demo flow with stage logs.
5. Persist metadata and a standardized result payload.
6. Reproduce a prior run when an output comparison is needed.

## Run Storage

Runs are stored under the configured external data root:

```text
runs/YYYYMMDD-HHMMSS-run-id/
  config.yaml
  metadata.json
  results.json
  logs.txt
```

`metadata.json` contains the UTC timestamp, command arguments, Git commit SHA when run from a source checkout (otherwise `unknown`), configuration hash, software version, Python/platform runtime, and duration. `config.yaml` is the normalized configuration snapshot. `results.json` contains the run ID, configuration hash, software version, command, and aggregate command payload. `logs.txt` contains timestamped INFO messages and failure tracebacks.

Run IDs are timestamped and include a deterministic 12-character digest derived from the command and configuration. A suffix is added only when the same-second directory already exists.

## Commands

```powershell
python -m pip install -r requirements-lock.txt
python -m pip install .
$env:PROTOTYPE_DATA_ROOT = "$HOME/prototype-data"
prototype demo
prototype evaluate --json
prototype validate --corpus-root C:/research/corpus --output-dir C:/research/validation
prototype reproduce 20260928-123456-abcdef123456
```

The demo and evaluation commands use generated fixtures. Validation remains local and never fetches missing checkouts. Reproduction loads the saved `config.yaml`, verifies the configuration through the normal loader, reruns the original command, and compares the saved aggregate payload. A mismatch exits with an actionable error and is logged in the reproduction run.

## Reproducibility Workflow

1. Locate the run ID under the configured external `runs` directory.
2. Inspect `metadata.json` for the Git commit, runtime, command, and configuration hash.
3. Inspect `logs.txt` for stage timing and errors.
4. Run `prototype reproduce RUN_ID` from the same project revision and compatible environment.
5. Treat a mismatch as a failed reproduction; do not overwrite the original run.

Reproduction compares aggregate payloads, not timestamps, run IDs, or duration. This keeps the comparison focused on command output while retaining full execution provenance.

## Troubleshooting

- **Run not found:** use the same `PROTOTYPE_DATA_ROOT` or `--config` that produced the run.
- **Run incomplete or corrupt:** the error identifies the invalid/missing record file; confirm the run contains `config.yaml`, `metadata.json`, `results.json`, and `logs.txt`. Do not edit the original run directory.
- **Configuration mismatch:** use the saved `config.yaml`; frozen CPU, model revision, dimensions, and token limits are validated before execution.
- **Reproduction mismatch:** compare software commit, dependency/runtime metadata, input checkout state, and logs. The original result remains unchanged.
- **Missing optional corpus:** validation logs a warning and writes an aggregate blocked report; it does not fetch or create a repository.