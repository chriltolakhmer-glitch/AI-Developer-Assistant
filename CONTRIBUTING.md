# Contributing

Thanks for helping maintain this research prototype. Contributions should improve reliability, reproducibility, documentation, or packaging without broadening the research scope.

## Scope and safeguards

- Preserve the frozen Humanize pilot and all benchmark questions exactly.
- Do not add repositories, begin benchmark expansion, modify retrieval algorithms, or change evaluation methodology without an explicitly approved separate scope change.
- Do not commit corpus checkouts, source-derived files, run records, model caches, embeddings, indexes, private logs, or secrets.
- Keep external inputs read-only and all generated research data outside this repository.

## Development setup

Use Python 3.14 on Windows for the validated environment (the package requires Python 3.11 or newer). From the repository root in PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install --editable .
python -m pip check
$env:PROTOTYPE_DATA_ROOT = "$HOME/prototype-data"
```

For offline model-backed tests, point `EMBEDDING_MODEL_CACHE` at the already acquired pinned model cache and set `HF_HUB_OFFLINE=1`. Do not acquire model weights or corpus data as part of an ordinary test run.

## Validation before submitting

```powershell
python -m unittest discover -s tests -v
prototype --help
prototype demo
prototype evaluate --json
```

If changing validation messages or configuration handling, also exercise `prototype validate` with a missing corpus and invalid paths. A missing corpus should produce an explicit not-ready report, not trigger acquisition. Check packaging in a fresh virtual environment when modifying `pyproject.toml` or requirement files.

## Change review

- Keep changes focused and explain their motivation and observable effect.
- Add or adjust tests for changed behavior; do not change retrieval/evaluation semantics as incidental cleanup.
- Update the applicable guide and dependency lock when behavior or dependencies change.
- Review `git diff --check`, `python -m pip check`, and the full test output before committing.
- Never include Humanize or benchmark-question changes in a software maintenance change.
