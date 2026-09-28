# Phase 33 - Developer Mode Retrieval Calibration

**Status:** Implemented as developer-only post-release work on 2026-09-28.
Research evaluation, benchmark artifacts, Humanize files, frozen release
artifacts and v0.1.1 behavior remain unchanged.

## Baseline and scope

Phase 32 provides `prototype local evaluate`, JSON query cases, file/symbol/
context metrics, ranking explanations and context diagnostics. Phase 33 uses
those outputs to make retrieval failures visible and compare developer runs.
No research evaluator, shared research ranking method, benchmark question,
Humanize artifact or release tag is an input or output.

Known failure categories include missing symbols, missing related files, excess
context, duplicate chunks, poor ordering, incorrect relationship expansion and
unsupported-language handling. The evaluator reports these as diagnostics, not
as benchmark scores.

## Failure analysis

Each case now includes `failure_type`, expected evidence, retrieved file paths,
and a short explanation. Categories include:

- `wrong_file` and `no_result`
- `missing_symbol` and `correct_file_wrong_symbol`
- `missing_dependency` and `missing_caller_or_callee`
- `too_little_context` and `too_much_context`
- `duplicate_context`
- `ranking_order`
- `explanation_mismatch`

The categories are mechanical signals from the declared case expectations and
Phase 31 result metadata. They do not assert why a developer failed a task or
represent a confidence judgment.

## Calibration cases

Developer-only calibration cases are in:

```text
tests/fixtures/developer_eval/calibration/cases.json
```

They cover authentication, API endpoint discovery, configuration lookup,
database access and utility tracing. The database case intentionally references
evidence absent from the compact fixture so failure reporting is exercised.
Every case includes query text, expected files/symbols/relationships and failure
notes. The fixtures are synthetic and are not research benchmark data.

## Comparison and diagnostics

Run an evaluation and compare it with the previous evaluation record for the
same developer repository:

```text
prototype local evaluate REPOSITORY --cases CASES.json --compare --json
```

The report contains baseline and candidate file/symbol/context/noise/
explanation values and per-case change reasons. The baseline is read only from
the selected developer workspace; no research evaluation record is created.

Explain a named case with its expected and retrieved evidence:

```text
prototype local explain auth-login --cases CASES.json --repository REPOSITORY
```

Use `--explain` on `local evaluate` to retain complete result rows and ranking
factors for every case. These commands are debugging tools for local retrieval,
not repository scoring or research performance evaluation.

## Calibration boundary

Phase 33 does not tune weights from a quality claim or change shared retrieval
methodology. The evidence-backed calibration change is bounded import-to-symbol
expansion: imported names are matched to same-repository indexed symbols and
added as related context. It does not infer dynamic dispatch or traverse beyond
the repository-local import evidence. Comparison reports make any case-level
change explicit. Future metadata weighting or duplicate-policy changes must be
justified by these developer diagnostics and validated with the same isolated
cases.

Unsupported languages remain outside the Python index contract. A TypeScript
fixture is retained to verify that unsupported input is reported rather than
silently evaluated as missing Python evidence.

## Validation

```text
python -m unittest tests.test_developer_mode -v
python -m unittest discover -s tests -v
git diff --check
```

The final validation also verifies the v0.1.1 commit and tag identities and
checks that benchmark, Humanize, research evaluation and research retrieval
paths are unchanged. No benchmark improvement or release change is claimed.