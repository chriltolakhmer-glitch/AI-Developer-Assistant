# Phase 61 — Developer retrieval candidate remediation and re-validation

Status: **implementation, candidate gates, focused/full tests, real-repository pilot, preservation, commit, and push complete**. The successor review is pending human decision. Phase 61 continues from the Phase 60 checkout and its uncommitted remediation work. It does not restart prior implementation, revise research retrieval, or change benchmark, Humanize, version, manifest, or release artifacts.

## Phase 60 failure evidence

Phase 60 used the authorized local Python repository and a TypeScript-only repository. The Python index completed, but configuration chunks exceeded the existing 256-token model input limit. Candidate `phase60-config-context` failed the regression and duplicate-context gates: the API case gained duplicate context and the cache case gained undeclared context. Stability, ranking review, trace compatibility, and diagnose compatibility passed. Review `review-a8cff9352e844928b7905a926e8220f3` remained pending; promotion was rejected. No configuration was activated and no deployment or recovery/closure was performed.

The original candidate, validation, review, and histories are preserved in the external Phase 60 developer workspace at `C:\Apps\phase60-validation\pilot-workspace`. Phase 61 creates a new successor rather than editing those records.

## Technical causes and remediation

### Bounded configuration context

Developer indexing now applies the pinned tokenizer before embedding configuration chunks. Oversized chunks retain a whole-line prefix up to 256 tokens where possible. Excerpts receive provenance-correct chunk IDs and source ranges; retained/original hashes, line ranges, bounded/omitted status, and reason remain in developer-only context metadata. When no whole line fits, the chunk is omitted from embedding but its original context identity and omission diagnostic remain. `inspect` distinguishes searchable bounded excerpts from skipped over-limit source chunks. Query context reports index version and selected, expanded, omitted, oversized, and bounded context diagnostics. No source file is modified.

### Duplicate suppression and relationship integrity

Ranking suppresses duplicate file/symbol and identical-content results across the complete direct-result set and all relationship expansions, irrespective of whether a target was reached as a dependency, caller, callee, or importer. Suppressed targets retain explicit relationship references and omission reasons. The assembled context evidence contains unique direct/expanded identity and digest records for validation.

Inter-file relationships require matching module/import evidence; same-file call edges are accepted only when their target is unambiguous. Name-only matches do not create edges. Ambiguous and unresolved same-name symbols retain bounded candidate diagnostics. Legitimate resolved edges remain available to retrieval expansion. These are static Python source relationships, not runtime execution traces.

The pilot also exposed generic one-term relationship boosts: ordinary terms such as
`api`, `vector`, or `save` could promote loosely related files even after edge
resolution had been constrained. Ranking v6 therefore applies the relationship
multiplier only when a fully qualified component or multiple specific terms match
the question. The explanation gate separately treats active ranking-factor labels
as configuration-dependent while continuing to fail when actual relationship or
match evidence disappears.

### Index and evidence compatibility

The developer index contract is `developer-local-index-v4`, stored under external `indexes/REPOSITORY/v4/`. Phase 60 v2 and interim v3 indexes cannot be loaded as v4; a new index build is required. Index schema is included in developer inspect/query diagnostics. The final ranking contract is `developer-navigation-v6`. Research indexes and shared retrieval storage are unchanged.

Reliability journal replay shares immutable JSON evidence between each loaded event and its materialized view rather than recursively duplicating the evidence tree. Mutation paths retain defensive copies. Canonical evidence bytes and SHA-256 digests are unchanged. This reduces avoidable replay copies; large JSON parsing and the returned state still require memory proportional to the retained data.

## Successor candidate and gates

Successor `phase61-dependency-context-v5` references the intervening Phase 61 v4
candidate, which itself descends from the failed Phase 60 candidate. Each candidate
retains an owner, purpose, affected cases, remediation reason, behavior change,
validation requirements, and timestamp in the external workspace. The final
validation passed regression, context completeness, declared-context, duplicate
context, stability, ranking review, trace compatibility, and diagnose compatibility
for all six cases. The previous Phase 60 and Phase 61 candidate hashes and the
original pending Phase 60 review hash were unchanged. A separate review was created
for the final successor and is **pending**; there is no human approval.

## Real-repository pilot

The six authorized Python scenarios are configuration discovery, authentication flow, dependency tracing, API route tracing, utility tracing, and database access. The same Phase 60 Python repository is used, without modifying its source. Expected files, symbols and relationships are checked alongside undeclared files, duplicate identities/content, bounded configuration diagnostics, ranking, and completeness. The TypeScript-only repository remains explicitly unsupported by the Python-only indexer; a rejection is not described as retrieval success.

Pilot baseline and successor evidence, generated indexes, candidate/review records, and run records remain outside the source checkout. No generated developer records are committed.

## Validation and preservation results

* The quality utility failure was reproduced in isolation and passed there, but failed in the prior full runs. It was **not** test-order state leakage: the fixture contains both `src/legacy/formatting.py` and the legitimate imported `src/utils/formatting.py`, whose function bodies are exact content duplicates. When the valid target fell outside the direct top-50 retrieval window, the unrelated legacy copy could rank first and digest deduplication then hid the declared relationship target during context expansion.
* Ranking now chooses an exact-content representative that is an explicit static relationship target of a query-relevant result, even when that target is available through sidecar relationship metadata beyond the direct candidate window. The unrelated duplicate remains suppressed and the suppression remains explained on a returned source result. A focused synthetic regression places the legitimate target beyond top-50; the original quality workflow test and that regression both pass, as does the smallest neighboring sequence.
* Complete `tests.test_developer_mode` suite: 215 tests passed, zero skips, failures, or errors (3919 seconds; 65m 19s).
* Final full unittest discovery: 359 tests passed, 2 skipped, zero failures/errors (3965.040 seconds; 66m 5s). The skipped tests were `test_real_embedding_to_persisted_indexes_to_text_query_offline` and `test_real_model_offline_repeatability`; both require `EMBEDDING_MODEL_CACHE`, which was not configured. The sole final full-suite run completed successfully; do not repeat it.
* Real-repository pilot: all six authorized Python query scenarios re-ran against the current v4 external index with ranking v6. Configuration selected `config/settings.py` / `Settings.__init__`; dependency tracing selected `CacheManager.get` and `_get_cache_path`; API route tracing selected `backend/api/main.py` / `query_code`; utility tracing selected `backend/parsing/code_parser.py` / `CodeParser.parse`; vector-store persistence selected `backend/retrieval/vector_store.py` / `FAISSVectorStore.save`. Authentication remained a negative case: no authentication implementation surfaced in the repository results. No duplicate context was emitted in any scenario. TypeScript index/query remained explicitly unsupported.
* Successor `phase61-dependency-context-v5`: fresh validation `fab222ccadd645b2a9b9246f735957d9` passed all eight gates against the final implementation. The existing human review `review-f4e5c85be5e94488be360bfed737f6b4` remains pending; the read-only policy check passed with no blockers. No approval, activation, deployment, rollback, recovery, or readiness closure occurred.
* Phase 60 failed candidate and pending review: hash-preserved across successor creation and validation.
* Review `review-f4e5c85be5e94488be360bfed737f6b4` is pending with no human approval. Policy eligibility passed with no policy blockers/warnings. The review's governance-health `warnings` reflects that no accept/reject decision exists yet; it is an expected human-disposition warning, not a validation failure. Pre-existing extra files remain visible in each context report; none were introduced relative to each new immutable baseline, and the cache case explicitly allows its two observed static caller files.
* Preservation: `git diff --check` passed; the Phase 60 baseline reported 58 protected paths matched; Phase 60’s 166 original external evidence hashes and failed candidate/review hashes were preserved; both pilot repositories remain unchanged; remote/local v0.1.1 tag object and peeled commit match. No generated indexes/candidates/reviews/evidence are in the checkout. The Phase 61 commit was pushed to `origin/main`; local and remote HEADs were verified aligned and the working tree clean.

No quality scores or benchmark-improvement claims are made. Phase 61 does not activate a configuration, deploy, execute rollback or recovery, or close readiness. Human approval remains required.

## Limitations

The retrieval parser remains Python-only. Relationship extraction is static and conservative; unresolved or ambiguous edges can omit useful context, which is preferable to fabricating links. Bounded configuration excerpts preserve source text and disclose omissions, but cannot make omitted lines available to retrieval. Evidence replay still parses retained JSON histories into memory. Offline pilot execution requires the previously authorized pinned local model cache. The results are developer navigation evidence only and do not establish research or benchmark performance.
