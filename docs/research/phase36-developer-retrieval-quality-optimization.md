# Phase 36 — Developer Mode Retrieval Quality Optimization

**Status:** Implemented as isolated developer-only post-release work on 2026-09-28. Changes affect personal local retrieval only; no research retrieval or evaluator behavior was changed.

## Baseline and isolation

At Phase 36 start, the checkout was on `main` with the pre-existing Phase 27–35 working-tree changes still present. The `v0.1.1` tag object was `05688504f74ad51230ee1566fad8cda0f1b1ad97`; its peeled commit was `51329285a882c1b7942d0a5b1c571e628d63dfb4`. Protected benchmark, Humanize, research-evaluation, and retrieval paths had no diff against that tagged commit. The Phase 35 focused suite passed: 30 tests, no failures, errors, or skips.

Existing developer capabilities were local trace and diagnose, failure taxonomy, evidence-based confidence diagnostics, stability checks, incremental indexing, ranking explanations, and developer-only evaluate. Phase 33–35 diagnostics motivated exact-symbol ambiguity, missing caller/dependency context, repeated symbol/content chunks, nearby-only expansion noise, and comparison of ranking/explanation changes over time.

The implementation is limited to `src/developer/`, developer CLI routing, synthetic developer fixtures/tests, and workflow documentation. It does not modify benchmark datasets, Humanize artifacts, frozen release files, `src/retrieval/`, research evaluation methodology, research snapshots, or the v0.1.1 tag. Ranking changes are developer-local navigation preferences and make no benchmark-improvement claim.

## Developer-only quality cases

`tests/fixtures/developer_eval/quality_cases.json` contains seven synthetic cases: exact symbol lookup, dependency tracing, configuration discovery, API route tracing, authentication flow, database access, and utility usage. Each declares expected files/symbols/relationships, allowed extra context, required relationships, and failure tolerance. The paired `quality_repository/` provides local Python-only source, including an exact duplicate utility definition to exercise deduplication. No external repository, benchmark query, or Humanize example is used.

## Ranking refinements

The developer navigation preference version is now `developer-navigation-v2`:

- Qualified identifier boundary matches and exact symbol-leaf matches receive explicit symbol factors, so a parent name is not mislabeled as an exact method match.
- A candidate with a query-matched static relationship receives an explained relationship-proximity factor.
- Path terms are separately recorded and contribute a bounded file-relevance factor.
- Prior metadata/test/container/diversity explanations and score contributions remain present.
- Exact repeated symbol/content copies in different files are suppressed and attached to the selected result's `duplicate_suppressed` explanation. Overlapping spans remain suppressed; distinct non-overlapping methods are not hard-capped.
- Query freshness remains fail-closed: stale indexes are rejected before ranking. Selected ranking reasons identify the verified current index state; freshness is not used as a speculative recency score.

All factors and the formula are retained in `ranking_reason`. Ranking explanations are descriptive; no new quality score is created.

## Context assembly and relationship coverage

Index context now records both outgoing and bounded incoming static call/import relationships. This allows a direct utility query to include an observed local caller, and a route query to expose the handler path. Context expansion prefers explicit relation IDs, deduplicates repeated symbol names, caps related context, and no longer includes nearby-only chunks by default. Grouped context files include selected results and the chosen explicit relation evidence; suppressed duplicates and nearby-only omissions remain visible in diagnostics. Older developer indexes derive duplicate fingerprints from their locally stored chunks when loaded, so the diagnostic does not require a research artifact or change the index schema.

`prototype local analyze-context QUERY` shows selected files, expected/missing evidence (when `--cases PATH` and optionally `--case-id ID` are provided), extra/allowed context, duplicate suppression, and ranking explanations. Without a case file, it explicitly notes that expected-evidence completeness cannot be assessed.

## Retrieval comparison

```text
prototype local compare "Where are login tokens generated?" --repository PATH
prototype local compare "Where are login tokens generated?" --repository PATH --json
```

The command compares the current result with the latest matching prior developer-local `query` or `trace` record for that question/repository. It lists added/removed files and results, rank changes, and changes to ranking reasons, evidence explanations, or selected related context. On a first query it reports that no prior retrieval exists. Records and comparison output stay in the developer workspace. This is a descriptive change report, not a score or quality judgment.

## Regression coverage

Tests exercise all seven case definitions, expected evidence coverage on the synthetic repository, exact-symbol preference, relationship expansion, exact duplicate suppression, repeat-query stability, context analysis JSON output, comparison rank/explanation changes, and compatibility with existing trace/diagnose outputs. Phase 35 stability output shape and ranking explanation fields remain covered by their existing regressions.

## Limitations and unsupported cases

- The index remains Python-only. Unsupported files are not parsed or searched.
- Import/call relationships are static and conservative; dynamic dispatch, reflection, generated code, runtime-only links, and ambiguous aliases may be missed or overapproximated.
- Exact duplicate suppression requires identical qualified symbol and source-content hash across files; semantically equivalent code with different text is not considered a duplicate.
- Context completeness depends on the selected top-k, indexed eligible chunks, parser coverage, and declared expected-evidence case. Without a case file, missing expected evidence cannot be inferred.
- Comparison requires a prior matching local query/trace record. It compares stored outputs from the current local workspace and does not reconstruct code or model versions beyond each run's retained provenance.
- No universal retrieval score, correctness probability, research metric, or benchmark result is produced.

## Validation and preservation

```text
python -m unittest tests.test_developer_mode -v
python -m unittest discover -s tests -v
git diff --check
```

The final record includes focused/full test counts, skips and failures; verifies benchmark, Humanize, research evaluation/retrieval and v0.1.1 identity; and checks that no generated developer index/workspace was written into the source checkout.

**Validation result:** Focused developer suite: `Ran 32 tests` / `OK`, zero skips or failures. Full suite: `Ran 176 tests` / `OK`, zero skips or failures. Preservation and source-checkout artifact checks were run after these suites.
