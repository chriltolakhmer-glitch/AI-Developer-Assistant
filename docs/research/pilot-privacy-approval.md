# Phase 8.7 — Pilot Privacy Review and Approval Record

**Review date:** 2026-09-27

**Repository baseline:** `974e55b`

**Decision status:** **NOT APPROVED — PILOT ANNOTATION REMAINS BLOCKED**

## Scope and identity

| Item | Evidence |
|---|---|
| Repository | `python-humanize/humanize` |
| Required snapshot | `392aef707c0e74341ab4a51420984e9ea6b566c5` |
| Local read-only checkout | `C:\Apps\Temp\Phase5.4\corpus\humanize` |
| Snapshot check | The checkout `HEAD` matched the full required SHA; it was detached and had no worktree changes before/after the manifest scan. |
| Processing boundary | Only the existing offline scanner was run to produce file metadata. No parser, chunker, embedding, index, retrieval, metric, or experiment was run for this review. |

This is an evidence inventory and pending decision record, **not a privacy approval**. It must not be interpreted as permission to inspect source for benchmark annotation or to create/consume a chunk inventory.

## Review and evidence by gate

| Gate | Evidence reviewed / performed | Status and limitation |
|---|---|---|
| Snapshot identity | Exact checkout `HEAD` verified against the pinned SHA. | **PASS for identity only.** |
| Secret scan — snapshot | Existing Gitleaks `8.30.1` report `humanize-dir.json` is an empty JSON result array, SHA-256 `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`. No new Gitleaks scan was run during this phase. | **0 findings recorded in the saved report; scope/configuration provenance still needs confirmation.** A scanner result is not a personal-data review or an approval. |
| Secret scan — history | Existing `humanize-git.json` is also an empty result array with the same digest. The local checkout is shallow. The exact Git-history range, scan command/configuration, and full-history coverage are not evidenced. | **OPEN.** Do not characterize this as a full-history pass. Obtain/scan the required history or have the authorized reviewer approve a documented scope limitation and residual risk. |
| Personal/confidential data | No attributable manual review record was found. No source content was inspected for annotation in this phase. | **NOT REVIEWED / OPEN.** A designated human reviewer must complete and record the review on the controlled local system; do not infer absence of personal/confidential data from zero secret findings. |
| Root license | The pinned Git tree contains `LICENCE`, which identifies the MIT License; the Phase 4.5 corpus-screening record independently records MIT. | **Root-license evidence present.** This is not legal advice or legal approval. |
| File-level notices / license terms | No complete per-file notice inventory or attributable terms review was found. | **OPEN / PARTIAL.** Review applicable notices for the intended Python scope, document attribution/exclusions, and obtain any required legal/owner review. Do not infer that root MIT text resolves every notice. |
| Eligible-file manifest | Generated with the existing read-only `RepositoryScanner` at the exact SHA and written outside the checkout and Git repository to `C:\Apps\Temp\Phase8\benchmark\pilot\python-humanize\eligible-file-manifest.json`. The manifest has 13 tracked Python records, 13 eligible, 0 excluded, and 2,915 eligible LOC using `phase4.5-python-v1`; SHA-256: `a9f35063535978fd5fe099506c2152922dd42bb0bf95bc56df10de8396a32868`. | **PASS for deterministic manifest generation/count reconciliation.** The file-path/hash manifest remains external. Scanner output is not a privacy clearance, and no chunk inventory was generated or consumed. |
| Local handling and retention | The pilot workspace and manifest are under `C:\Apps\Temp\Phase8\benchmark\pilot\python-humanize\`, outside the thesis Git repository. | **PARTIAL.** A pilot-specific access-control, retention, backup, and deletion attestation is not recorded. |
| Attributable approval | No designated reviewer/approver, signed decision, date-attributed clearance, or residual-risk acceptance was supplied or found. | **NOT APPROVED.** This document intentionally contains no approval attestation. |

Raw Gitleaks reports and the per-file manifest remain external. The report digests and aggregate counts above do not disclose individual paths or findings.

## Approval decision

**Pilot clearance: NOT GRANTED.** The available evidence establishes the pinned snapshot identity, zero findings in two saved Gitleaks result files (with incomplete history-scope provenance), the root MIT license, and a deterministic 13-file eligible manifest. It does not establish a completed personal/confidential-data review, adequate full-history review or accepted limitation, complete file-notice/license review, pilot data-handling attestation, or an attributable authorized approval.

Until an authorized reviewer records approval after resolving or explicitly accepting these limits, do not inspect repository source for annotation, create or consume a chunk inventory, write benchmark cases, or validate gold chunk references. The conditional Phase 8.7 benchmark-creation task is therefore **not performed**. The external pilot draft remains at **0/12 cases**; no questions, query IDs, chunk IDs, relevance labels, or evidence notes have been fabricated.

This pilot decision does not clear the other eight repositories or the full corpus. No final benchmark freeze or experiment is authorized. The pilot-specific categories (`function discovery`, `architecture understanding`, `dependency understanding`, `behavior understanding`) also need a documented pilot schema/category mapping before any projection through the final benchmark tools; they are not the final benchmark's frozen categories.

## Required completion and sign-off

The designated reviewer/approver must add an attributable external review record containing all of the following before the status can change:

1. The secret-scan command/configuration and exact snapshot/history scope, with finding dispositions; full history coverage or an explicitly justified and accepted limitation.
2. A completed personal/confidential-data review for this exact snapshot and eligible scope, including reviewer, date, methods/categories considered, result, and exclusions.
3. A file-level notice/license review, with the applicable terms, attribution/retention conditions, and any files excluded; legal review where required.
4. Confirmation of the eligible-file manifest digest above (or a superseding manifest digest and reconciled counts), plus the approved handling, access, retention, and deletion controls.
5. The authorized approver's name/role, explicit `APPROVED` or `REJECTED` decision, date, evidence references, limits/residual risks, and signature/attestation. A blank field, this report, owner intent, or an automated scan is not approval.

If approved, record that decision separately with its evidence and only then resume pilot annotation in the external workspace. Keep the pilot out of the final benchmark and do not run retrieval experiments.

## Related records

- [Phase 8.6 pilot privacy clearance record](pilot-privacy-clearance.md)
- [Phase 8.5 general privacy clearance report](privacy-clearance-report.md)
- [Dataset manifest validation](corpus-manifest-validation.md)
- [Dataset snapshot freeze](dataset-snapshot-freeze.md)
- [ADR-008: source-code privacy](../decisions/ADR-008-source-code-privacy.md)
- [ADR-013: dataset snapshot freeze](../decisions/ADR-013-dataset-snapshot-freeze.md)
- [ADR-014: embedding privacy policy](../decisions/ADR-014-embedding-privacy-policy.md)