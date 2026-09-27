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

**Phase 25 — Research Prototype 0.1.0.**

| Area | Status |
|---|---|
| Humanize pilot | COMPLETE / FROZEN |
| Software | RELEASED RESEARCH PROTOTYPE |
| Research | REPRODUCIBLE |
| Benchmark expansion | FUTURE WORK |

The release packages the existing ingestion, Python parsing/chunking, indexing, retrieval, evaluation and validation utilities. The research workflow is reproducible; additional repositories, questions, annotation rounds, retrieval tuning/strategies, new experiments and scaling studies remain outside scope.

See the [release guide](docs/research/release-guide.md) for clean installation, commands, tests and reproduction. The [software prototype scope](docs/research/software-prototype-scope.md) documents component boundaries. Humanize remains frozen; benchmark expansion is deferred. This is not a production release.

## Quick Start

From the project root in Windows PowerShell, set up Python 3.14 (3.11 or newer is required), install the pinned environment, and install the package:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install .
python -m pip check
```

After activating that environment, the public command is:

```text
prototype --help
prototype validate
prototype evaluate
prototype demo
prototype reproduce RUN_ID
```

`prototype demo` and `prototype evaluate` use generated, non-sensitive fixtures and do not access the network or Humanize artifacts. `prototype validate` checks pinned local checkouts without fetching them. Its defaults use `~/prototype-data/corpus` for input and `~/prototype-data/validation` for reports; override them with `--corpus-root` and `--output-dir`, or set `PROTOTYPE_DATA_ROOT` before starting the command. Reports are always written outside this project and the source checkouts.

Configuration defaults and environment overrides are documented in [prototype configuration](docs/research/prototype-configuration.md). Use `prototype --config PATH validate` for a complete external YAML configuration.

Every command creates an external run record under `runs/` containing configuration, metadata, standardized results, and logs. See [experiment tracking](docs/research/prototype-experiment-tracking.md) and use `prototype reproduce RUN_ID` to rerun and compare a saved execution.

Run the full test suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

## Maintenance

See [Contributing](CONTRIBUTING.md), [Support](SUPPORT.md), and the [development workflow](DEVELOPMENT.md) for scope boundaries, environment setup, and validation steps.
