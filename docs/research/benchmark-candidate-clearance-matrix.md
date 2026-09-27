# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

**Current scope:** Humanize is COMPLETE / FROZEN / PILOT-ONLY. All eight non-Humanize candidates are NOT SELECTED FOR THESIS SCOPE. The former eight-blocked queue is archived; missing approvals for unused repositories are not an active thesis backlog.

| Repository | Preserved snapshot | Current thesis scope |
|---|---|---|
| `python-humanize/humanize` | `392aef707c0e74341ab4a51420984e9ea6b566c5` | **COMPLETE / FROZEN / PILOT-ONLY** |
| `theskumar/python-dotenv` | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | **NOT SELECTED FOR THESIS SCOPE** |
| `python-validators/validators` | `70de324322def13a49a93d222f798ec1ab700885` | **NOT SELECTED FOR THESIS SCOPE** |
| `pallets/flask` | `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | **NOT SELECTED FOR THESIS SCOPE** |
| `encode/httpx` | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | **NOT SELECTED FOR THESIS SCOPE** |
| `Textualize/rich` | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | **NOT SELECTED FOR THESIS SCOPE** |
| `pytest-dev/pytest` | `8721173580390a9d297e5af06cac3f0b6841f425` | **NOT SELECTED FOR THESIS SCOPE** |
| `python/mypy` | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | **NOT SELECTED FOR THESIS SCOPE** |
| `sphinx-doc/sphinx` | `b04a2101295ac3fb725b16111eda0284b6da4cca` | **NOT SELECTED FOR THESIS SCOPE** |

## Historical document (unchanged)

# Phase 18.2 — Benchmark Candidate Clearance Matrix

**Date:** 2026-09-27  
**Status:** Evidence/status matrix only. **No candidate is cleared.**  
**Boundary:** This matrix records the existing Phase 9 candidate set only. It authorizes no inspection, processing, annotation, indexing, retrieval, freeze, or release. Humanize stays frozen.

A frozen repository identity and preprocessing result are not repository-specific privacy/use clearance. Status below reflects documented evidence; `Not evidenced` must be treated as pending, not as a pass. G1 must identify the exact commit, activity, accountable reviewers, evidence digests, decision date, outcome, and conditions. Sensitive scan details stay in the controlled internal evidence location rather than this committed summary.

## Phase 19.6 calibration note

The table below is the historical Phase 18.2 evidence view, not a live approval ledger. The [per-candidate approval record](repository-approvals/python-dotenv.md) records python-dotenv's later Phase 19.5 **BLOCKED** disposition; the [progress tracker](repository-evidence-progress.md) is the current queue summary. No candidate approval changes in Phase 19.6, and no other repository was processed. Keep historical rows intact and use dated links to current evidence rather than copying partial findings between matrices.

Use the [calibrated checklist and state crosswalk](gate1-workflow-calibration.md) for future Gate 1 records under the [simplified workflow](benchmark-research-workflow-final.md). The minimum evidence below remains required for the exact activity; historical `APPROVE/REVISE/REJECT` labels are not automatic approval transitions. Evidence-collection completion and Gate 1 approval are separate fields.

## Candidate matrix (Phase 18.2 baseline)

| Candidate ID / pinned commit | Existing evidence | Unresolved clearance items | G1 status | Owner / reviewer fields | Annotation readiness |
|---|---|---|---|---|---|
| `theskumar/python-dotenv` — `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | Phase 9 records BSD-3-Clause root-license evidence and 20 eligible Python files / 2,776 LOC. Phase 5.4.1 validates snapshot identity/counts, but not privacy. | No attributable repo-specific secret/history disposition, personal/confidential-data review, full provenance/snapshot digest package, file/notice confirmation, or handling/storage approval found in reviewed records. | **PENDING — NOT CLEARED** | Data/privacy reviewer: **Unassigned**; license reviewer: **Unassigned**; benchmark approver: **Unassigned** | **Blocked** until G1 then G2. |
| `python-humanize/humanize` — `392aef707c0e74341ab4a51420984e9ea6b566c5` | Phase 16 records 12 accepted pilot cases and a pilot-only freeze. Existing record explicitly says pilot clearance remains open. | History scope, personal/confidential-data review, file-notice review, handling evidence, and attributable clearance/approval remain unresolved. | **PENDING — NOT CLEARED for expansion**; pilot remains frozen | Pilot custodian: **Unassigned**; data/privacy reviewer: **Unassigned**; license reviewer: **Unassigned** | **Excluded from new annotation and blind evaluation.** Do not modify the pilot or count its cases. |
| `python-validators/validators` — `70de324322def13a49a93d222f798ec1ab700885` | Phase 9 records MIT license-file evidence and 64 eligible Python files / 4,353 LOC; preprocessing baseline only. | Candidate-specific secret/history disposition, personal/confidential-data review, notices, provenance, storage/access/retention and handling approval not evidenced. | **PENDING — NOT CLEARED** | Data/privacy reviewer: **Unassigned**; license reviewer: **Unassigned**; benchmark approver: **Unassigned** | **Blocked** until G1 then G2. |
| `pallets/flask` — `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | Phase 9 records BSD-3-Clause root-license evidence and 83 files / 13,301 LOC. | Six unresolved Gitleaks snapshot candidates recorded in Phase 5.4.1; authorized disposition, personal/confidential-data review, provenance and handling approval remain open. | **BLOCKED — unresolved findings; not cleared** | Data/privacy reviewer: **Unassigned**; scan reviewer: **Unassigned**; license reviewer: **Unassigned** | **Blocked** pending findings disposition, G1, then G2. |
| `encode/httpx` — `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | Phase 9 records BSD-3-Clause root-license evidence and 60 files / 13,800 LOC; preprocessing baseline only. | No attributable repo-specific privacy/history review, personal/confidential-data decision, provenance/handling clearance or named approval found. | **PENDING — NOT CLEARED** | Data/privacy reviewer: **Unassigned**; license reviewer: **Unassigned**; benchmark approver: **Unassigned** | **Blocked** until G1 then G2. |
| `Textualize/rich` — `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | Phase 9 records MIT root-license evidence and 213 files / 45,223 LOC; preprocessing baseline only. | Candidate-specific privacy/history, personal/confidential-data, provenance, file-use and handling approvals not evidenced. | **PENDING — NOT CLEARED** | Data/privacy reviewer: **Unassigned**; license reviewer: **Unassigned**; benchmark approver: **Unassigned** | **Blocked** until G1 then G2. |
| `pytest-dev/pytest` — `8721173580390a9d297e5af06cac3f0b6841f425` | Phase 9 records MIT root-license evidence and 245 files / 93,998 LOC. | One unresolved Gitleaks snapshot candidate recorded; authorized disposition, personal/confidential-data review, provenance and handling approval remain open. | **BLOCKED — unresolved finding; not cleared** | Data/privacy reviewer: **Unassigned**; scan reviewer: **Unassigned**; license reviewer: **Unassigned** | **Blocked** pending finding disposition, G1, then G2. |
| `python/mypy` — `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | Phase 9 records MIT for most code with PSF-2.0 file-level qualifications; 444 files / 144,316 LOC. | Qualified file notices need review; candidate-specific privacy/history, personal/confidential-data, provenance and handling approval not evidenced. | **PENDING — NOT CLEARED** | Data/privacy reviewer: **Unassigned**; license/notice reviewer: **Unassigned**; benchmark approver: **Unassigned** | **Blocked** pending notice/privacy clearance at G1, then G2. |
| `sphinx-doc/sphinx` — `b04a2101295ac3fb725b16111eda0284b6da4cca` | Phase 9 records BSD-2-Clause default with possible file-level notices; 774 files / 118,987 LOC. | One unresolved Gitleaks snapshot candidate and a history-scan `.dot` error; authorized disposition/completed or approved alternative scope, personal/confidential-data and file-notice review, provenance and handling approval remain open. | **BLOCKED — unresolved scan/history items; not cleared** | Data/privacy reviewer: **Unassigned**; scan/history reviewer: **Unassigned**; license/notice reviewer: **Unassigned** | **Blocked** pending disposition, G1, then G2. |

## Minimum G1 evidence package

For each candidate and exact activity, the responsible reviewers must provide:

1. Canonical repository ID, source origin, full 40-character SHA, snapshot digest, approved file/filter scope, and reproducible provenance record.
2. Secret/history scan coverage and finding dispositions; personal/confidential-data review; justified disposition of incomplete history scans. Keep sensitive findings in restricted evidence storage.
3. Applicable license version, attribution/notice obligations, file-level exceptions, and separate decisions for internal processing, derived artifacts, external review/transmission, and distribution.
4. Approved storage, authorized reader list/access controls, processing boundaries, retention/deletion, backup, incident contact, and transmission policy.
5. Named data/privacy and license reviewers plus benchmark-owner decision; date, evidence digests, outcome (`APPROVE`, `REVISE`, `REJECT`), conditions, and exact activity allowed.

Clearance for snapshot/inventory preparation does not authorize use of inventory for gold annotation. That requires G2. Any changed SHA, filter, file exclusion, finding status, activity, or handling control reopens the affected decision.

## Current decision

**Zero of nine candidates has documented G1 approval in the reviewed Phase 17/18 artifacts.** The Phase 8 thesis-level risk acceptance is explicitly not repository-specific clearance, and Phase 9/ADR-013 freezes corpus identity while privacy clearance remains open. The matrix must not be changed to “approved” without attributable evidence. No candidate processing is authorized by this document.

## Existing references

- [Phase 9 frozen corpus selection](corpus-final-selection.md), [dataset snapshot freeze](dataset-snapshot-freeze.md), and [Phase 5.4.1 checkout validation](corpus-checkout-validation.md)
- [ADR-013 dataset snapshot freeze](../decisions/ADR-013-dataset-snapshot-freeze.md)
- [Phase 8 thesis scope risk acceptance](repository-approval-thesis-risk-acceptance.md) and [repository approval status report](repository-approval-status-report.md)
- [Phase 17 protocol](benchmark-expansion-protocol.md), [Phase 18 registry](benchmark-candidate-registry.md), and [Phase 18.1 gate review](benchmark-expansion-gate-review.md)
- [Phase 16 Humanize readiness decision](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md)
