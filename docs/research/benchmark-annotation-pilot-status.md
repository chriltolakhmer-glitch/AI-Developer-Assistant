# Phase 13.1 — Controlled Benchmark Annotation Pilot Status

**Status:** **ANNOTATION DRAFT COMPLETE — HUMAN REVIEW PENDING; PILOT NOT FROZEN**

**Pilot repository selected:** `python-humanize/humanize`

**Pinned commit:** `392aef707c0e74341ab4a51420984e9ea6b566c5`

**Maximum pilot size:** 12 questions

**Questions created:** **12 of 12 maximum**

**Structural validation:** **PASS** against the exact local Humanize chunk map; 3 questions per category.

**Human review / freeze:** **PENDING** in the external `human-review-record.md`; no freeze is claimed.

This status record applies the Phase 13.3 solo-thesis risk acceptance recommendation recorded by `Alot — Project Owner / Thesis Researcher`. It authorizes only a maximum 12-question humanize pilot under local-only controls. The 12 pilot records are stored externally with their chunk map and draft export; no pilot data is committed to this repository.

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
| Pilot validation | `PASS — STRUCTURAL ONLY` | All 12 records validate against the exact local chunk map; human review is still pending. |
| Human review and freeze | `PENDING` | The external review record has not been completed; no freeze is claimed. |
| Expansion to full benchmark | `NOT ALLOWED` | Full benchmark requires separate review, pilot completion, and freeze prerequisites. |

## Decision

The pilot repository is authorized for controlled execution only. The pilot contains **12/12 questions**, authored externally from the exact SHA and approved Python scope. Human review remains pending. Any correction must be revalidated; the pilot must remain excluded from the final benchmark.

**Pilot freeze:** **NOT COMPLETE — pending Alot's traceable human review and acceptance.**

**Full benchmark expansion:** **NOT ALLOWED.** The pilot must be reviewed, frozen, and excluded from the final benchmark if it influences instructions or tuning. Passing implementation tests or structural validation does not authorize expansion.

See [annotation-pilot-plan.md](annotation-pilot-plan.md), [repository-approval-thesis-risk-acceptance.md](repository-approval-thesis-risk-acceptance.md), [repository-approvals/humanize.md](repository-approvals/humanize.md), [repository-approval-status-report.md](repository-approval-status-report.md), and [benchmark-schema.md](benchmark-schema.md).
