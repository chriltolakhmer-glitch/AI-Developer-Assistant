# Phase 32 - Developer Mode Retrieval Evaluation

**Status:** Implemented as developer-only post-release work on 2026-09-28.
Research evaluation, benchmark datasets, Humanize artifacts, frozen release
artifacts, and v0.1.1 behavior remain unchanged.

## Purpose and baseline

Phase 31 provides symbol-aware context metadata, `local explain`, grouped file
context, ranking explanations, overlap reduction and developer diagnostics. The
remaining unknowns were retrieval usefulness, context completeness, irrelevant
context rate, symbol relationship accuracy and developer task success. Phase 32
adds a small, explicit measurement loop for those unknowns without changing the
retrieval algorithm or importing developer repositories into research data.

## Developer-only command

```text
prototype local evaluate REPOSITORY --cases CASES.json
prototype local evaluate REPOSITORY --cases CASES.json --explain --json
```

The command indexes and queries only the selected local repository through the
developer workspace. Query runs and the aggregate evaluation record are stored
under that workspace, never under the research `RunTracker` or research data
root. `--explain` retains full result rows and ranking reasons in each case;
without it, the aggregate report omits those larger result details while keeping
failure diagnostics.

## Case format

Cases are a developer-owned JSON list. Expected files and symbols are exact
repository-relative/provenance values. Relationships are checked against
related symbols and imported symbol names exposed by Phase 31.

```json
[
  {
    "id": "auth-login",
    "query": "Where is login implemented?",
    "expected": {
      "files": ["src/auth/service.py"],
      "symbols": ["AuthService.login"],
      "relationships": ["TokenManager"]
    }
  }
]
```

The repository fixture at `tests/fixtures/developer_eval/sample_repository`
contains authentication, token, configuration and API-route Python files. The
`unsupported/app.ts` fixture confirms that unsupported language examples remain
outside the Python indexing contract. These are ordinary regression fixtures,
not benchmark questions or research snapshots.

## Metrics

- `file_hits`: cases where every expected file appears in retrieved results.
- `symbol_hits`: cases where every expected symbol appears in selected or
  related context.
- `context_completeness`: mean fraction of expected symbols and relationships
  found per case. A case with no symbol/relationship requirements is complete.
- `noise_rate`: mean proportion of retrieved rows belonging to unexpected files
  or repeated symbols. It is a diagnostic heuristic, not a relevance score.
- `explanation_coverage`: fraction of cases whose results expose context
  expansion reasons, symbol relevance, developer context, and exclusion text.

Each case also reports missing files, symbols and relationships, extra files,
its completeness/noise values, explanation status and, with `--explain`, the
retrieved rows and ranking explanations.

These measurements describe only the supplied cases, parser support and current
developer repository. They do not establish benchmark improvement, model
quality, user success, or general retrieval performance.

## Limitations

The evaluator measures retrieval evidence, not generated answers or completed
developer tasks. It inherits Python-only parsing, conservative static
relationships, fixed chunk/token limits, and Phase 31's context boundaries.
Unsupported languages are reported by developer scan/index behavior and are not
silently treated as failed Python retrieval cases. Small synthetic fixtures can
miss the ambiguity, scale and conventions of real repositories. More cases and
human task studies would be needed to measure task success; that work is outside
this isolated phase.

## Validation and separation

Focused and full validation commands are:

```text
python -m unittest tests.test_developer_mode -v
python -m unittest discover -s tests -v
```

Final checks include `git diff --check`, protected-path comparison against
v0.1.1, and tag identity verification. Benchmark datasets, Humanize files,
research evaluation artifacts/methodology, research snapshots and the frozen
v0.1.1 release are not inputs or outputs of this evaluator.