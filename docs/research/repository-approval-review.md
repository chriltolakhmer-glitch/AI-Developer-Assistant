# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 19.2 — Repository Approval Review

**Date:** 2026-09-27  
**Review scope:** Documentary review of the eight non-Humanize candidates queued in Phase 19.1 against Gate 1 of the [simplified research workflow](benchmark-research-workflow-final.md).  
**Status:** **No candidate is approved for processing.** Humanize remains frozen.  
**Method boundary:** Existing approval, privacy, corpus, and Phase 19 selection records only. No repository was cloned; no repository source, new scan, or external approval evidence was inspected or generated.

## Candidate repository list and Gate 1 result

The review covers exactly the eight non-Humanize repositories already in `corpus-snapshot-v1`; no repository was added or substituted. The commit SHAs below are the canonical identities recorded in Phase 9. Their presence in the corpus documents is not local checkout verification: each individual approval record still marks exact checkout evidence as pending.

| Candidate repository ID | Required exact snapshot SHA | License screening | Privacy / sensitive-file review | Gate 1 recommendation |
|---|---|---|---|---|
| `theskumar/python-dotenv` | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | BSD-3-Clause `LICENSE` recorded; file-level/terms review in progress. | Secret scan provenance/disposition and history coverage pending; personal/confidential-data review not started; handling and manifest evidence incomplete. | **BLOCKED — pending evidence; do not process.** |
| `python-validators/validators` | `70de324322def13a49a93d222f798ec1ab700885` | MIT `LICENSE.txt` recorded; file-level/terms review in progress. | Scan disposition and history coverage pending; personal/confidential-data review not started; handling and manifest evidence incomplete. | **BLOCKED — pending evidence; do not process.** |
| `pallets/flask` | `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | BSD-3-Clause `LICENSE.txt` recorded; file-level/terms review in progress. | Six snapshot scanner candidates are unresolved; history coverage is shallow; personal/confidential-data review not started; handling and manifest evidence incomplete. | **BLOCKED — unresolved findings and missing approvals.** |
| `encode/httpx` | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | BSD-3-Clause `LICENSE.md` recorded; file-level/terms review in progress. | Scan provenance/disposition and history coverage pending; personal/confidential-data review not started; handling and manifest evidence incomplete. | **BLOCKED — pending evidence; do not process.** |
| `Textualize/rich` | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | MIT `LICENSE` recorded; file-level/terms review in progress. | Scan provenance/disposition and history coverage pending; personal/confidential-data review not started; handling and manifest evidence incomplete. | **BLOCKED — pending evidence; do not process.** |
| `pytest-dev/pytest` | `8721173580390a9d297e5af06cac3f0b6841f425` | MIT `LICENSE` recorded; file-level/terms review in progress. | One snapshot scanner candidate is unresolved; history coverage is shallow; personal/confidential-data review not started; handling and manifest evidence incomplete. | **BLOCKED — unresolved finding and missing approvals.** |
| `python/mypy` | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | MIT for most code; PSF-2.0 applies to specified files. Applicable file-level terms/notices are blocked pending human review. | Scan provenance/disposition and history coverage pending; personal/confidential-data review not started; handling and manifest evidence incomplete. | **BLOCKED — notice and privacy evidence unresolved.** |
| `sphinx-doc/sphinx` | `b04a2101295ac3fb725b16111eda0284b6da4cca` | BSD-2-Clause default; file-level notices require review and remain blocked. | One snapshot scanner candidate is unresolved; shallow history scan has an unsupported `.dot` error; personal/confidential-data review not started; handling and manifest evidence incomplete. | **BLOCKED — unresolved scan/history/notices and missing approvals.** |

“License screening” means the root-license file and identifier are recorded. It is not a complete terms review, legal opinion, or authorization for annotation or release. “Privacy review” distinguishes identified concerns from a completed human review; no absent finding or empty report is treated as clearance.

## Exact snapshot requirement

Gate 1 is specific to the canonical repository ID, full 40-character SHA, eligible language/file scope, and intended activity. The SHAs listed above agree with the frozen corpus records. However, every reviewed per-repository approval form still contains a pending placeholder for checkout identity evidence (exact SHA, detached/read-only state, and clean-tree evidence). Therefore:

- treat the full SHA as the required identity, not proof of a verified current checkout;
- do not use mutable branches, tags, another revision, or an unapproved file scope;
- any later SHA, filter, exclusion, or purpose change requires review against that changed identity/scope before use.

## Privacy and handling status

The [repository approval status report](repository-approval-status-report.md), [privacy clearance report](privacy-clearance-report.md), and individual [repository approval records](repository-approvals/) indicate the following corpus-wide gaps for the eight queued candidates:

- saved scan evidence and candidate disposition are incomplete; Flask (six), pytest (one), and Sphinx (one) have specifically recorded unresolved candidates;
- recorded checkouts/history coverage is shallow; candidate records do not show a completed history-coverage disposition;
- no complete personal/confidential-data review is recorded;
- exact-SHA eligible/excluded manifest digests and reconciliation are pending in the individual records;
- local handling evidence—approved storage/access, telemetry/offline settings, backup, retention, and deletion—is incomplete;
- no attributable repository-specific approval decision is recorded.

The prior thesis-level risk acceptance permits only its described limited local experimentation and explicitly does not constitute repository-specific clearance or authorize benchmark annotation. The earlier selection, corpus freeze, preprocessing results, and root-license records do not supersede these gaps.

## Known blockers

1. **All eight repositories:** exact checkout/read-only evidence and an attributable decision for the intended activity are missing.
2. **All eight repositories:** privacy review, personal/confidential-data review, history coverage/disposition, final manifest/exclusion reconciliation, and local handling controls are incomplete in the approval records.
3. **Flask:** six scanner candidates remain undispositioned.
4. **pytest:** one scanner candidate remains undispositioned.
5. **Sphinx:** one scanner candidate, a shallow-history limitation, and an unsupported `.dot` history-scan error remain unresolved; file-level notices also need review.
6. **mypy:** MIT/PSF-2.0 applicability and required file-level attribution/retention terms are unresolved.
7. **License terms generally:** root license screening exists, but per-file notice review is not complete for the intended Python scope.

A scanner candidate is an unresolved review item, not a confirmed secret. Its status must not be silently treated as false positive or exposure.

## Approval recommendation

**Recommendation: BLOCK all eight candidates from processing pending evidence.** The eight remain in the Gate 1 review queue from Phase 19.1, but none passes the simplified repository approval gate today. Status for every candidate is **Blocked** (with supporting evidence pending/in progress); none is `Approved for processing` or `Rejected` on project merit.

Required next actions are to reconcile the existing candidate-specific approval packets for exact SHA, license/notices, privacy/sensitive-file review, history and scan dispositions, manifest/exclusions, handling controls, and attributable approval. This review did not perform those checks or authorize their performance outside already permitted procedures. Until a candidate has a recorded Gate 1 pass for the exact activity, do not clone, inspect/process source, generate/use a source-derived inventory, annotate, or evaluate it.

**Humanize:** excluded from this eight-candidate review. Its completed pilot and its limited pilot-only history remain frozen; that does not provide expansion clearance or permit new Humanize questions.

## End state

No repository enters benchmark processing without passing the repository approval gate for its exact snapshot and intended activity. No questions were created, no annotation began, no retrieval code changed, and no benchmark expansion execution is authorized.

## Evidence references

- [Phase 18.4 simplified research workflow](benchmark-research-workflow-final.md)
- [Phase 19.1 selection review](candidate-selection-review.md) and [candidate status](candidate-review-status.md)
- [Phase 9 corpus selection](corpus-final-selection.md), [repository corpus screening](repository-corpus-final.md), and [snapshot freeze](dataset-snapshot-freeze.md)
- [Consolidated repository approval status](repository-approval-status-report.md), [privacy clearance report](privacy-clearance-report.md), and [repository approval workflow](repository-approval-workflow.md)
- [Repository approval template](repository-approval-template.md) and individual approval records: [python-dotenv](repository-approvals/python-dotenv.md), [validators](repository-approvals/validators.md), [Flask](repository-approvals/flask.md), [httpx](repository-approvals/httpx.md), [Rich](repository-approvals/rich.md), [pytest](repository-approvals/pytest.md), [mypy](repository-approvals/mypy.md), and [Sphinx](repository-approvals/sphinx.md)
- [Humanize pilot status](benchmark-annotation-pilot-status.md) and [Phase 16 closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md)
