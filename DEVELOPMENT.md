# Development Workflow

This workflow is for routine software maintenance only. It does not authorize source processing, corpus expansion, new benchmark questions, retrieval changes, or evaluation-method changes.

## 1. Prepare an isolated environment

From the project root in Windows PowerShell (Python 3.14 is the tested runtime; Python 3.11+ is required):

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install --editable .
python -m pip check
$env:PROTOTYPE_DATA_ROOT = "$HOME/prototype-data"
```

Keep that data root outside the checkout. For model-dependent tests, use an existing pinned cache with `EMBEDDING_MODEL_CACHE` and set `HF_HUB_OFFLINE=1`.

## 2. Run checks

```powershell
python -m unittest discover -s tests -v
prototype --help
prototype demo
prototype evaluate --json
```

`prototype validate` operates only on checkouts already present at the supplied corpus root. A missing corpus is an expected blocked/not-ready outcome; the command must not fetch it. Reproduce a saved demo/evaluation/validation record with `prototype reproduce RUN_ID`.

## 3. Update dependencies safely

The supported set is composed by `requirements-lock.txt`, which includes the exact pins from `requirements-retrieval.txt` and `requirements-embedding.txt`. The project base dependency and build backend are declared in `pyproject.toml`. When a dependency changes, update the relevant exact pin(s), create a fresh environment, install the lock and project, run `pip check`, and execute the full suite. Do not add packages solely for functionality already available in the standard library.

## 4. Review and submit

Run `git diff --check`; inspect the complete diff and status; confirm no run data, source-derived artifacts, Humanize files, or benchmark questions are included. Document any skipped tests and prerequisites. Follow [Contributing](CONTRIBUTING.md) for scope and review safeguards.
