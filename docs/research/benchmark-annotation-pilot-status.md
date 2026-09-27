# Phase 13.1 — Controlled Benchmark Annotation Pilot Status

**Status:** **AUTHORIZED WITH CONTROLS — LIMITED PILOT ONLY**

**Pilot repository selected:** `python-humanize/humanize`

**Pinned commit:** `392aef707c0e74341ab4a51420984e9ea6b566c5`

**Maximum pilot size:** 12 questions

**Questions created:** **0 of 12 maximum**

This status record applies the Phase 13.3 solo-thesis risk acceptance recommendation recorded by `Alot — Project Owner / Thesis Researcher`. It authorizes only a maximum 12-question humanize pilot under local-only controls. No question has been created, no source has been inspected for authoring, no chunk inventory has been consumed, and no benchmark data has been created.

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
| Humanize repository-specific approval | `APPROVED WITH THESIS SCOPE LIMITATIONS` | Limited to this 12-question pilot; full repository clearance is not claimed. |
| Annotation purpose authorization | `AUTHORIZED — PILOT ONLY` | Explicit Phase 13.3 risk acceptance by Alot; maximum 12 questions. |
| Source inspection for authoring | `AUTHORIZED — PILOT ONLY` | Local-only, Python-only, sensitive-file exclusions, and stop conditions apply. |
| Chunk inventory use for gold evidence | `AUTHORIZED — PILOT ONLY` | Only after the approved exact-SHA inventory is available and kept outside Git. |
| Pilot validation | `NOT RUN` | There are no pilot questions or evidence records to validate. |
| Expansion to full benchmark | `NOT ALLOWED` | Full benchmark requires separate review, pilot completion, and freeze prerequisites. |

## Decision

The pilot repository is authorized for controlled execution only. The pilot contains **0/12 questions**, with no fabricated placeholders. Any authoring must remain local, use the exact SHA and approved Python scope, exclude sensitive or unassessable files, preserve attribution, and stop on a new finding or control failure. Record each authorized question with the required ID, category, difficulty, evidence chunks, grades, and validation notes outside Git.

**Full benchmark expansion:** **NOT ALLOWED.** The pilot must be independently reviewed and validated, and remains excluded from the final benchmark if it influences instructions or tuning. Passing implementation tests does not authorize expansion.

See [annotation-pilot-plan.md](annotation-pilot-plan.md), [repository-approval-thesis-risk-acceptance.md](repository-approval-thesis-risk-acceptance.md), [repository-approvals/humanize.md](repository-approvals/humanize.md), [repository-approval-status-report.md](repository-approval-status-report.md), and [benchmark-schema.md](benchmark-schema.md).
