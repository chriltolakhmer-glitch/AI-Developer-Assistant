# Phase 35 — Developer Retrieval Trust & Explainability Hardening

**Status:** Implemented as developer-only post-release work on 2026-09-28. This phase adds local evidence explanations and missing-context diagnosis; it does not alter retrieval ranking or research evaluation.

## Baseline and isolation

At Phase 35 start, the repository was on `main` with pre-existing Phase 27–34 working-tree changes. The `v0.1.1` tag object resolved to `05688504f74ad51230ee1566fad8cda0f1b1ad97`, and its commit resolved to `51329285a882c1b7942d0a5b1c571e628d63dfb4`. Protected benchmark, Humanize, research evaluation, and research retrieval paths had no diff against the tagged baseline at that point. The Phase 34 focused developer suite passed: 28 tests, no failures, errors, or skips.

Phase 34 already provided:

- Developer-local evaluate and failure taxonomy.
- Calibration fixtures and incremental change diagnostics.
- Stability checks and evaluation run-record explanations.
- Ranking reasons and context-expansion explanations.

Remaining trust gaps were why a result ranked highly, why expected context was absent, whether an index was current, whether evidence was strong or weak, and whether a gap reflected unsupported languages or relationships.

This work remains confined to developer-local workflows, their tests/fixtures, and workflow documentation. It does not modify benchmark datasets, Humanize files, frozen release artifacts, research evaluation methodology, release tags, or research snapshots. Developer repositories and cases are not added to research data; no benchmark-improvement claim is made.

## Retrieval evidence trace

Use the developer-only command:

```text
prototype local trace "where is authentication handled" --repository PATH
prototype local trace "where is AuthService.login handled" --repository PATH --json
```

Each selected result reports its repository-relative file and symbol, observed evidence signals, available relationship paths, readable ranking factors, context-expansion reason, and evidence-based confidence diagnostics. Signals may include exact symbol match, metadata-term match, lexical retrieval, semantic retrieval, and statically visible import/call/parent relationships. Existing `ranking_reason` data remains available; explainability is added alongside it and does not change ranking.

Trace output and run records are developer-local. Result order, overlap suppression, ranking weights, and the Phase 34 stability signature are unchanged.

## Confidence explanation

Every selected query result carries an explanation. The query summary has a qualitative `high`, `medium`, or `low` evidence label, the observed signals, and limitations. `high` requires an exact symbol signal plus corroborating retrieval channels or a visible relationship; `medium` requires an exact symbol or visible relationship; otherwise the label is `low`.

These labels describe only the evidence visible to this local retrieval workflow. They are not calibrated correctness probabilities, universal quality scores, benchmark scores, or research metrics. Limitations name gaps such as an unobserved caller/import relationship. An empty result is reported as low evidence with `no_results_returned`, not as a confidence estimate about the correctness of an answer.

## Missing-context diagnosis

Diagnosis uses a developer-owned case ID and case file:

```text
prototype local diagnose trust-missing-symbol --cases tests/fixtures/developer_eval/trust_cases.json --repository PATH
prototype local diagnose trust-stale-index --cases tests/fixtures/developer_eval/trust_cases.json --repository PATH --json
```

The report separates expected evidence, evidence available from the active index, missing evidence, index freshness, and likely causes. It can identify an absent/unindexed symbol, an excluded or unparseable file, an unsupported extension, a stale index, a deleted/renamed source item, or a relationship not observed by conservative static analysis. When the active index is stale, retrieved evidence remains explicitly identified as belonging to the older snapshot; rebuild before relying on it as current.

Case declarations are developer-owned and are not research labels. Use `prototype local inspect PATH --changes` and `prototype local index PATH` to review and refresh index state as appropriate.

## Trust fixtures and regression coverage

`tests/fixtures/developer_eval/trust_cases.json` contains six synthetic local cases:

- Clear authentication retrieval with a static import/call relationship.
- An ambiguous settings query.
- A missing symbol and file.
- An unsupported TypeScript file.
- A stale working-tree index.
- A deleted file still represented by an older index.

Every case states expected behavior and acceptable limitations. Tests also verify per-result explanations, preserved ranking-factor records, relationship paths, freshness/deletion/unsupported-language diagnoses, and compatibility with existing developer evaluation and stability checks. Fixtures are synthetic regression inputs; they are not external repositories, benchmark questions, or Humanize examples.

## Limitations and unsupported cases

- Retrieval remains Python-only. Unsupported language files are identified from local file inventory, not parsed or searched.
- Relationships are conservative static AST evidence; dynamic imports, runtime dispatch, generated code, indirect callers, and behavior requiring execution may not be identified.
- Confidence summarizes observed local signals only. It does not validate an answer or estimate general retrieval quality.
- Diagnosis is bounded by the declared case, active index, current local inventory, parser output, and requested top-k. It cannot prove an absent symbol does not exist outside supported/indexed inputs.
- A stale-index diagnosis may inspect old indexed results to explain the mismatch; those results are not current-source evidence.

## Validation and separation

Run the focused and full developer test suites and check whitespace:

```text
python -m unittest tests.test_developer_mode -v
python -m unittest discover -s tests -v
git diff --check
```

Final validation records the test count, skips, and failures; verifies the tag identities; and checks that benchmark, Humanize, research evaluation, and protected research retrieval paths are unchanged. The only effect is improved transparency in personal developer workflows. Research evaluation and methodology remain unchanged; benchmark work is deferred; Humanize remains frozen; `v0.1.1` is unchanged.

**Validation result:** Focused developer suite: `Ran 30 tests` / `OK`, zero skips or failures. Full suite: `Ran 174 tests` / `OK`, zero skips or failures. `git diff --check` passed; protected benchmark/Humanize/research-evaluation/retrieval paths remained unchanged against v0.1.1; tag object and peeled commit identities matched the Phase 35 baseline. No developer index/workspace artifacts were created in the source checkout.
