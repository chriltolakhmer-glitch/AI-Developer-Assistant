# Phase 13.1 — Controlled Benchmark Annotation Pilot Status

**Status:** **BLOCKED — pilot authorization prerequisites are not satisfied.**

**Pilot repository selected:** `python-humanize/humanize`

**Pinned commit:** `392aef707c0e74341ab4a51420984e9ea6b566c5`

**Maximum pilot size:** 12 questions

**Questions created:** **0**

This status record applies the approved Phase 12.5 thesis scope. That scope permits local thesis experimentation but explicitly excludes benchmark question creation, source-derived annotation, chunk-inventory use for gold labels, and benchmark freeze. No source was inspected for authoring, no chunk inventory was consumed, and no benchmark data was created.

## Required pilot record shape

Each future question, if separately authorized, must record all of the following in the controlled external annotation workspace, not in this Git repository:

| Field | Requirement | Current status |
|---|---|---|
| Question ID | Unique pilot-local identifier, separate from final benchmark IDs | Not created |
| Category | One declared pilot category mapped to the approved protocol | Not created |
| Difficulty | `easy`, `medium`, or `hard`, assigned before retrieval results | Not created |
| Evidence chunks | Exact chunk IDs from the matching repository/SHA inventory | Not created; inventory use is not authorized |
| Relevance grades | Integer `2` primary or `1` supporting | Not created |
| Validation notes | Snapshot, schema, evidence, ambiguity, review, and pilot-exclusion checks | Not created |

Question text, source paths/spans, chunk IDs, labels, rationale, and review material remain source-derived research data and must stay outside Git.

## Gate status

| Gate | Status | Reason |
|---|---|---|
| Phase 12.5 thesis scope | `APPROVED WITH THESIS SCOPE LIMITATIONS` | Local thesis experimentation is allowed within the recorded controls. |
| Humanize repository-specific approval | `BLOCKED` | History, personal/confidential-data review, file-level notices, handling controls, historical exposure, and attributable approval remain unresolved. |
| Annotation purpose authorization | `NOT AUTHORIZED` | Phase 12.5 explicitly excludes benchmark question creation and source-derived annotation. |
| Source inspection for authoring | `BLOCKED` | Annotation prerequisites are not satisfied. |
| Chunk inventory use for gold evidence | `BLOCKED` | No approved annotation handoff exists for this exact snapshot. |
| Pilot validation | `NOT RUN` | There are no pilot questions or evidence records to validate. |
| Expansion to full benchmark | `NOT ALLOWED` | Pilot approval, review, and freeze prerequisites are absent. |

## Decision

The pilot repository is selected for planning only. The pilot contains **0/12 questions**, with no fabricated placeholders. Do not create questions, inspect source for annotation, consume a chunk inventory, or record evidence chunks until the humanize approval record has an explicit attributable decision covering manual annotation for this exact SHA and a `READY FOR MANUAL ANNOTATION` handoff state.

**Full benchmark expansion:** **NOT ALLOWED.** A future pilot must be independently authored, reviewed, validated, and excluded from the final benchmark if it influences instructions or tuning. Passing implementation tests does not unlock annotation.

See [annotation-pilot-plan.md](annotation-pilot-plan.md), [repository-approval-thesis-risk-acceptance.md](repository-approval-thesis-risk-acceptance.md), [repository-approvals/humanize.md](repository-approvals/humanize.md), [repository-approval-status-report.md](repository-approval-status-report.md), and [benchmark-schema.md](benchmark-schema.md).
