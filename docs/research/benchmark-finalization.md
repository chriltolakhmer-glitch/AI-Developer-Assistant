# Phase 8.2 — Benchmark Finalization Protocol

## Final benchmark structure

The final evaluation target is 108 repository-question cases, stored as a versioned local JSON benchmark using `schema_version: "1.0"`. Each case has a unique `<repository-slug>-NNN` query ID, repository identity, full pinned commit SHA, concise natural-language query, and a non-empty map of exact gold chunk IDs to integer relevance grades. The current retrieval case schema omits category; the freeze utility requires an accompanying query-ID-to-category map and incorporates it into the canonical benchmark hash.

The annotation ledger remains separate from retriever outputs and records category, expected files/symbols, exact inclusive source spans, rationale, ambiguity notes, and review disposition. It is source-derived research material and must remain outside Git in the controlled local research-data area. The committed freeze report contains aggregate metadata only, never questions, paths, symbols, chunk IDs, source text, or sensitive audit findings.

## Query categories

Each repository contributes three queries per category:

| Category | Target per repository | Total target | Annotation focus |
|---|---:|---:|---|
| `architecture_understanding` | 3 | 27 | Static component/workflow relationships and evidence-bearing definitions |
| `code_navigation` | 3 | 27 | Locating the implementation or a specific code behavior |
| `dependency_understanding` | 3 | 27 | Caller/callee or cross-file dependency hops; annotate each required hop |
| `bug_investigation` | 3 | 27 | Source-grounded failure possibility, guards, and relevant conditions—not an unverified runtime defect claim |
| **Total** | **12** | **108** | |

Across the set, balance conceptual and identifier-heavy wording, single-file and cross-file evidence, and include a deliberately challenging question in each category/repository allocation where feasible. Questions must be answerable from static evidence in the pinned revision; identifier disclosure is permitted only for an identifier-lookup question. Fix the held-out unit and split before tuning and record it in the ledger; pilot questions that influenced annotation instructions or system tuning are excluded.

## Planned repository coverage

Coverage is the nine-repository, Python-only sample already pinned by the corpus-selection decision. The entries below are planned allocation, not proof of completed annotation.

| Size stratum | Repository | Planned queries |
|---|---|---:|
| Small | `theskumar/python-dotenv` | 12 |
| Small | `python-humanize/humanize` | 12 |
| Small | `python-validators/validators` | 12 |
| Medium | `pallets/flask` | 12 |
| Medium | `encode/httpx` | 12 |
| Medium | `Textualize/rich` | 12 |
| Large | `pytest-dev/pytest` | 12 |
| Large | `python/mypy` | 12 |
| Large | `sphinx-doc/sphinx` | 12 |
| **Total** | **9 pinned snapshots** | **108** |

Use the full commit SHAs in [dataset-snapshot-freeze.md](dataset-snapshot-freeze.md); never resolve a branch or moving tag during annotation. Only eligible Python chunks from the exact validated snapshot inventory are in scope.

## Annotation process

1. **Clear prerequisites first.** Close and document secret/credential and personal/confidential-data review for every proposed snapshot; disposition scanner findings, and confirm applicable license/file notices. Until then, do not inspect corpus source for annotation or create/consume source-derived chunk inventories. The current snapshot-freeze record explicitly says these reviews remain open.
2. **Fix protocol and split.** Confirm category definitions, 12-per-repository allocation, held-out unit, pilot exclusions, and reviewer sample before annotating any final case. Preserve any deviations as a versioned protocol change.
3. **Author from the pinned source manually.** Write natural-language questions from static evidence. Do not use retriever rankings or unreviewed model-generated labels to choose questions or evidence.
4. **Record exact evidence.** For each case, record repository/commit, category, expected file and symbol, inclusive line span, corresponding deterministic chunk ID(s), grade, rationale, and ambiguity. Multi-hop questions include every necessary evidence chunk. Verify paths, symbols, and spans directly against the pinned snapshot.
5. **Review independently.** Predeclare an independent-review sample of at least 20% where a second reviewer is available; compare labels, adjudicate differences, and retain the review record locally. If unavailable, document the single-annotator limitation without claiming inter-rater agreement.
6. **Validate and reconcile.** Build/verify the exact chunk inventory using the already approved upstream pipeline, create the v1.0 benchmark JSON and category map, and run `BenchmarkValidator`. Resolve every issue; no unknown or missing chunk IDs or cross-snapshot evidence may remain.
7. **Freeze once.** Compute the canonical benchmark, snapshot-map, annotation-ledger, and review-record SHA-256 digests with `BenchmarkFreezeUtility`. Record metadata outside the repository and copy only aggregate, non-sensitive counts and digests to the freeze report. Do not overwrite an existing metadata file; corrections create a new benchmark version and preserve the old digest.

## Relevance labeling rules

| Human label | Stored grade | Rule |
|---|---:|---|
| Primary | 2 | Directly answers the question or provides the central implementation evidence. |
| Supporting | 1 | Necessary context or a required dependency hop, but not the main answer by itself. |

No other grade is valid. Each query requires at least one relevant chunk. Label at the chunk level; references must exist in the same repository and commit as the query. Do not label merely related code as supporting unless it is necessary to answer or understand the question. State ambiguity rather than silently selecting one of several plausible implementations. These integer grades are the frozen mapping used by nDCG; changing the mapping requires a new protocol version before evaluation.

## Freeze eligibility

The utility reports `frozen` only when automated validation passes, the benchmark has exactly 108 cases over nine repositories with exactly 12 queries and three of each category per repository, and a review-record SHA-256 digest is supplied. That digest is a caller attestation to a controlled review record; the utility cannot independently judge annotation correctness, clearance truthfulness, or the contents of that record. A structurally valid but incomplete or unreviewed pilot fixture is reported as pending, never represented as the final frozen benchmark.

See [benchmark-validation.md](benchmark-validation.md), [ADR-021](../decisions/ADR-021-benchmark-freeze.md), and [dataset-snapshot-freeze.md](dataset-snapshot-freeze.md).