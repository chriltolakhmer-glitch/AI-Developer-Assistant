# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

**Current scope:** Humanize is COMPLETE / FROZEN / PILOT-ONLY. All eight non-Humanize candidates are NOT SELECTED FOR THESIS SCOPE. The former eight-blocked queue is archived; missing approvals for unused repositories are not an active thesis backlog.

## Historical document (unchanged)

# Phase 19.0 — Candidate Selection Checklist

**Date:** 2026-09-27  
**Purpose:** Prepare comparison of only the already-frozen Phase 9 candidate repositories.  
**Status:** All candidates remain proposals; no selection or approval for expansion use is made.  
**Boundary:** No repositories were added or cloned, no source was inspected, no questions were created, and Humanize remains frozen.

This checklist records existing metadata and preliminary concerns, not completed repository approval. `[x]` means that the fact or screening note is documented in existing records. It does **not** mean the candidate is approved for processing, annotation, retrieval, or release. A decision box stays blank until a separate, attributable proposal decision is recorded.

## Proposal comparison checklist

| Existing candidate proposal | Identity recorded | Language recorded | License checked* | Size estimated | Privacy concerns identified | Selection rationale written | Selected for review | Deferred | Rejected |
|---|---|---|---|---|---|---|---|---|---|
| `theskumar/python-dotenv` — `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | [x] | [x] | [x] | [x] Small, 2,776 LOC | [x] | [x] | [ ] | [ ] | [ ] |
| `python-humanize/humanize` — `392aef707c0e74341ab4a51420984e9ea6b566c5` | [x] | [x] | [x] | [x] Small, 2,915 LOC | [x] | [x] Pilot rationale retained | [ ] | [ ] | [ ] |
| `python-validators/validators` — `70de324322def13a49a93d222f798ec1ab700885` | [x] | [x] | [x] | [x] Small, 4,353 LOC | [x] | [x] | [ ] | [ ] | [ ] |
| `pallets/flask` — `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | [x] | [x] | [x] | [x] Medium, 13,301 LOC | [x] Six unresolved scan candidates | [x] | [ ] | [ ] | [ ] |
| `encode/httpx` — `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | [x] | [x] | [x] | [x] Medium, 13,800 LOC | [x] | [x] | [ ] | [ ] | [ ] |
| `Textualize/rich` — `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | [x] | [x] | [x] | [x] Medium, 45,223 LOC | [x] | [x] | [ ] | [ ] | [ ] |
| `pytest-dev/pytest` — `8721173580390a9d297e5af06cac3f0b6841f425` | [x] | [x] | [x] | [x] Large, 93,998 LOC | [x] One unresolved scan candidate | [x] | [ ] | [ ] | [ ] |
| `python/mypy` — `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | [x] | [x] | [x] | [x] Large, 144,316 LOC | [x] File-level license/privacy review open | [x] | [ ] | [ ] | [ ] |
| `sphinx-doc/sphinx` — `b04a2101295ac3fb725b16111eda0284b6da4cca` | [x] | [x] | [x] | [x] Large, 118,987 LOC | [x] One unresolved scan candidate; history-scan error | [x] | [ ] | [ ] | [ ] |

\* **License checked** here means root-license screening is recorded in the frozen corpus metadata. It is not complete file-level notice review, legal advice, or permission for annotation/distribution. Candidate-specific privacy/sensitive-file review is not completed merely because the concern is identified. For all eight non-Humanize candidates, the repository approval status remains blocked for annotation. Humanize remains pilot-only.

## Per-candidate record template

Use one copy per existing candidate when a later selection-review record is prepared. Keep all fields as proposals until a decision is documented.

**Repository:** ______________________________  
**Canonical ID:** _____________________________  
**Exact full commit SHA:** _____________________  
**Language metadata / study language:** ________  
**License / notice screening evidence:** _______  
**Size category / eligible Python LOC:** _______  
**Privacy or sensitive-file concerns:** _________  
**Expected diversity contribution:** ___________  
**Selection rationale:** _______________________

- [ ] Identity recorded
- [ ] Language recorded
- [ ] License checked (screening only; permitted use separately verified)
- [ ] Size estimated
- [ ] Privacy concerns identified and disposition path recorded
- [ ] Selection rationale written

**Decision — proposals only until separately recorded:**

- [ ] Selected for review
- [ ] Deferred
- [ ] Rejected

**Decision rationale / evidence reference:** _________________________________  
**Reviewer / date:** __________________________  
**Approval for processing:** **Not granted by this checklist.**

## Selection constraints

- Compare only the nine exact candidates listed above; do not add or substitute repositories.
- Do not clone, fetch, inspect repository source, create/use source-derived inventories, or create questions as part of this selection preparation.
- Do not use Humanize for new expansion cases or characterize it as unseen. Preserve its existing 12-case pilot and all associated artifacts unchanged.
- Treat prior domain/size/license values as screening metadata. A candidate cannot proceed to new work until the simplified workflow's repository approval conditions are met for its exact SHA and intended activity.
- Keep all decision checkboxes blank in this preparation record. A later selection decision must be supported by Gate 1 approval status and written rationale; a proposal is not an approval.

## References

- [Candidate selection analysis](candidate-selection-analysis.md)
- [Simplified research workflow](benchmark-research-workflow-final.md)
- [Phase 9 frozen corpus selection](corpus-final-selection.md) and [repository corpus screening](repository-corpus-final.md)
- [Repository approval status report](repository-approval-status-report.md) and [candidate clearance matrix](benchmark-candidate-clearance-matrix.md)
- [Humanize pilot readiness and history](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md) and [closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md)
