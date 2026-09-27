# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

**Current scope:** Humanize is COMPLETE / FROZEN / PILOT-ONLY. All eight non-Humanize candidates are NOT SELECTED FOR THESIS SCOPE. The former eight-blocked queue is archived; missing approvals for unused repositories are not an active thesis backlog.

## Historical document (unchanged)

# Phase 19.2 — Repository Approval Status

**Date:** 2026-09-27  
**Scope:** The eight non-Humanize candidates selected for Gate 1 review in Phase 19.1.  
**Status:** **0 approved for processing; all eight blocked.** Humanize remains frozen and is not in this candidate list.

Status is based on existing committed approval evidence only. Root-license screening, frozen corpus identity, and preprocessing validation are not clearance. `Blocked` means at least one mandatory Gate 1 item is missing or unresolved; it is not a finding that a repository is unsuitable on project merit.

## Candidate status matrix

| Repository ID | Commit SHA | License status | Privacy status | Approval status | Required actions |
|---|---|---|---|---|---|
| `theskumar/python-dotenv` | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | BSD-3-Clause `LICENSE` root screening recorded; file-level review in progress. | Scan scope/disposition and history coverage pending; personal/confidential-data review not started; manifest and handling evidence incomplete. | **Blocked** | Supply exact-SHA read-only checkout evidence; complete/disposition scan and history evidence; complete human privacy and terms/notice reviews; reconcile manifest/exclusions; evidence handling controls; obtain attributable decision for exact purpose. |
| `python-validators/validators` | `70de324322def13a49a93d222f798ec1ab700885` | MIT `LICENSE.txt` root screening recorded; file-level review in progress. | Scan disposition/history pending; personal/confidential-data review not started; manifest and handling evidence incomplete. | **Blocked** | Verify exact checkout identity; complete scan/history and privacy reviews; review applicable notices; reconcile eligible-file manifest and handling controls; record attributable approval for exact purpose. |
| `pallets/flask` | `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | BSD-3-Clause `LICENSE.txt` root screening recorded; file-level review in progress. | Six Gitleaks snapshot candidates unresolved; history is shallow; personal/confidential-data review not started; manifest/handling evidence incomplete. | **Blocked** | Disposition all six candidates under approved review; resolve history coverage/limitation; complete privacy, notice, manifest, handling, identity, and attributable-approval evidence. |
| `encode/httpx` | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | BSD-3-Clause `LICENSE.md` root screening recorded; file-level review in progress. | Scan scope/disposition and history coverage pending; personal/confidential-data review not started; manifest and handling evidence incomplete. | **Blocked** | Verify exact checkout identity; complete scan/history and privacy reviews; review notices; reconcile manifest/exclusions and handling controls; record attributable approval for exact purpose. |
| `Textualize/rich` | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | MIT `LICENSE` root screening recorded; file-level review in progress. | Scan scope/disposition and history coverage pending; personal/confidential-data review not started; manifest and handling evidence incomplete. | **Blocked** | Verify exact checkout identity; complete scan/history and privacy reviews; review notices; reconcile manifest/exclusions and handling controls; record attributable approval for exact purpose. |
| `pytest-dev/pytest` | `8721173580390a9d297e5af06cac3f0b6841f425` | MIT `LICENSE` root screening recorded; file-level review in progress. | One Gitleaks snapshot candidate unresolved; history is shallow; personal/confidential-data review not started; manifest/handling evidence incomplete. | **Blocked** | Disposition the candidate under approved review; resolve history coverage/limitation; complete privacy, notice, identity, manifest, handling, and attributable-approval evidence. |
| `python/mypy` | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | MIT for most code; PSF-2.0 for specified files. File-level notice review blocked/pending. | Scan scope/disposition and history coverage pending; personal/confidential-data review not started; manifest and handling evidence incomplete. | **Blocked** | Complete file-level MIT/PSF-2.0 applicability and notice review; complete exact-SHA privacy/history, manifest, handling, and identity evidence; obtain attributable approval for exact purpose. |
| `sphinx-doc/sphinx` | `b04a2101295ac3fb725b16111eda0284b6da4cca` | BSD-2-Clause default; file-level notices remain blocked pending review. | One Gitleaks snapshot candidate unresolved; shallow history and `.dot` scan error unresolved; personal/confidential-data review not started; manifest/handling evidence incomplete. | **Blocked** | Disposition the candidate; resolve or obtain an attributable acceptance of the history-scan limitation; review file notices; complete privacy, identity, manifest, handling, and approval evidence. |

## Status interpretation

- **Approved for processing:** none. No reviewed record grants the eight candidates benchmark-processing permission.
- **Pending evidence:** multiple individual evidence items are pending or in progress within each blocked record.
- **Blocked:** all eight, because each individual record states open mandatory Gate 1 items and no attributable approval.
- **Rejected:** none. The documentary review found no project-merit basis to reject a candidate; unresolved evidence is a block, not a rejection.

The approval records contain pending placeholders for exact local checkout evidence, reviewers, dates, report references/digests, human review outcomes, handling attestations, and authorized decisions. These placeholders must not be populated from assumption.

## Humanize boundary

`python-humanize/humanize` (`392aef707c0e74341ab4a51420984e9ea6b566c5`) is excluded from this eight-candidate status table because its 12-question pilot is complete and frozen. Its prior authorization is pilot-only and does not clear Humanize for new expansion questions or provide clearance for any other candidate. Preserve its questions, annotations, answers, chunk map, and freeze digests unchanged.

## Processing rule

No candidate may enter benchmark processing—source inspection for authoring, source-derived inventory use, annotation, indexing/retrieval evaluation, or dataset freeze—until Gate 1 is explicitly passed for its exact repository ID, SHA, file/language scope, and intended activity. Approval for one purpose does not imply permission for another. A failed, incomplete, or contradictory item remains `Blocked` until resolved under the applicable permitted review process.

**End state:** No repository enters benchmark processing without passing the approval gate. No question, annotation, retrieval run, or benchmark expansion execution was performed by this review.

## Evidence references

- [Phase 19.2 approval review](repository-approval-review.md)
- [Phase 19.1 selection review](candidate-selection-review.md) and [candidate review status](candidate-review-status.md)
- [Phase 18.4 simplified workflow](benchmark-research-workflow-final.md)
- [Repository approval status report](repository-approval-status-report.md), [privacy clearance report](privacy-clearance-report.md), and [repository approval workflow](repository-approval-workflow.md)
- [Candidate clearance matrix](benchmark-candidate-clearance-matrix.md)
- Individual records: [python-dotenv](repository-approvals/python-dotenv.md), [validators](repository-approvals/validators.md), [Flask](repository-approvals/flask.md), [httpx](repository-approvals/httpx.md), [Rich](repository-approvals/rich.md), [pytest](repository-approvals/pytest.md), [mypy](repository-approvals/mypy.md), and [Sphinx](repository-approvals/sphinx.md)
- [Phase 9 corpus selection](corpus-final-selection.md) and [snapshot freeze](dataset-snapshot-freeze.md)
- [Humanize pilot status](benchmark-annotation-pilot-status.md) and [Phase 16 closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md)
