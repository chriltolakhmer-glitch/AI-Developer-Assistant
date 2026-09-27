# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 8.4 — Benchmark Annotation Workflow

## Purpose and gate

This workflow prepares the manual annotations for the planned 108-query benchmark. It does not inspect or index corpus source, create real questions, verify source spans, run retrieval, validate/freeze the final benchmark, or authorize experiments.

**The corpus privacy gate is currently open.** Do not inspect the pinned repositories or produce/consume source-derived chunk inventories until the secret/credential and personal/confidential-data reviews are complete, candidate findings are dispositioned, and clearance is documented. See [dataset-snapshot-freeze.md](dataset-snapshot-freeze.md) and [benchmark-finalization.md](benchmark-finalization.md). The external annotation template contains empty slots, not benchmark data.

All annotation templates, ledgers, chunk inventories, drafts, review records, and other source-derived artifacts must remain in `C:\Apps\Temp\Phase8\benchmark` or another approved, access-controlled location outside Git. Do not use retrieval output or unreviewed model-generated questions or labels as ground truth.

## Annotator steps

1. **Confirm authorization.** Verify documented privacy clearance and applicable license/file-notice review for all nine exact snapshots before source inspection. Confirm the frozen full commit SHAs; never substitute a branch or moving tag.
2. **Predeclare the protocol.** Record the held-out unit and split, pilot exclusions, question mix, and independent-review sample before authoring final cases. Target independent review of at least 20% when a second reviewer is available. If unavailable, document the single-annotator limitation without claiming inter-rater agreement.
3. **Load the blank template.** Work from the external `annotation-template.json`. Its 108 slots already carry planned repository, snapshot, ID, and category metadata. Never create fabricated cases to fill slots.
4. **Author one question manually.** Use static evidence at the exact pinned commit. Write concise, natural developer language; do not disclose the answer except where identifier lookup is the intended task. Balance the declared categories and exclude pilot/tuning-influenced questions from the final set.
5. **Select and record evidence.** Follow the evidence-selection process below. Record the exact chunk IDs and source evidence in the external annotation entry/ledger.
6. **Complete independent review.** Have the predeclared sample labeled independently before comparing. Adjudicate disagreements and retain the redacted review record externally.
7. **Run quality checks.** Review entry-level structure and chunk existence/provenance. Once all real annotations are complete, run the final validator against the matching frozen inventory and snapshot map. Resolve every issue before requesting a freeze.
8. **Export a draft only.** Use `benchmark_annotation.py` to export a deterministic draft after saving entries. The tool marks it as not validated/frozen and intentionally emits a draft schema that `BenchmarkLoader` will reject. It is not a final benchmark artifact.

The module API is `load_annotation_template()`, `add_annotation_entry()`, `validate_annotation_entry()`, `save_annotation_template()`, and `export_benchmark_draft()`. Supply an inventory to `validate_annotation_entry()` or `export_benchmark_draft()` to check chunk IDs; field-shape checks alone do not establish snapshot provenance.

## Evidence selection process

1. Formulate the answer from source evidence first, without looking at retriever rankings.
2. Identify the smallest set of eligible chunks that fully supports the answer. Include each required caller/callee or other dependency hop; do not include merely related code.
3. For every evidence item, record its exact deterministic chunk ID from the inventory generated for the same repository and commit. Never alter upstream chunk boundaries or IDs to fit an annotation.
4. Record repository-relative POSIX file path, symbol, and one-based inclusive source line range in `expected_files` and `expected_spans`. Verify each path and span against the pinned checkout after privacy clearance.
5. Assign relevance `2` to primary evidence that directly answers the question and `1` to necessary supporting context. Each case must have at least one chunk; no other grades are allowed. Include all required hops for multi-file questions.
6. State unresolved ambiguity or explicitly record that none remains. For source-level bug investigation, describe a possible condition rather than asserting an untested runtime defect.

## Chunk ID recording

- Copy IDs exactly from the validated inventory; do not derive, shorten, or hand-edit them.
- Use a unique key per chunk in the `relevance` mapping and record each grade as an integer, not a boolean.
- Match each ID against the inventory keyed by the case's exact repository and full commit SHA. An ID that exists only in another snapshot is invalid.
- When exporting with an inventory map, the preparation utility rejects missing IDs. Without an inventory map, it can check only that at least one nonempty ID and valid grade were supplied; this is not chunk validation.
- Keep chunk inventories and all path/span evidence external to the repository.

## Quality checks

Before considering an annotation entry complete, confirm:

- the query ID, repository ID, full commit SHA, and category match the assigned template slot;
- the query is trimmed, single-line, clear, and answerable from static evidence;
- the relevance map is nonempty and contains only grades 1 or 2;
- every chunk ID exists in the exact snapshot inventory and covers necessary evidence;
- every expected path/span is present, uses repository-relative POSIX paths, and has valid one-based inclusive bounds;
- the rationale explains why the selected evidence answers the question, and ambiguity notes record a disposition;
- independent-review, adjudication, pilot-exclusion, and held-out split records are complete as predeclared.

The utility validates annotation field shapes and can check IDs against an explicitly supplied inventory. It cannot establish that source evidence is correct, that spans match a checkout, that privacy clearance is true, or that human review occurred. The benchmark remains **unfrozen** until 108 real questions are complete, all references are validated, privacy clearance and review are approved/documented, and the freeze utility generates the canonical hash. No experiments are authorized before those gates close.

See [benchmark-annotation-guide.md](benchmark-annotation-guide.md), [benchmark-validation.md](benchmark-validation.md), and [benchmark-finalization.md](benchmark-finalization.md).