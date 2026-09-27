# Phase 8.12 — Local Privacy Attestations and Evidence Status

**Approval decision date:** 2026-09-27
**Phase 8.10 evidence review date:** 2026-09-27
**Phase 8.12 documentation update date:** 2026-09-27
**Thesis repository baseline:** `7e801fc8f034df97b24673eadf4bff0eadf09ef9`
**Pilot repository:** `python-humanize/humanize`
**Required snapshot:** `392aef707c0e74341ab4a51420984e9ea6b566c5`
**Reviewer name (user-designated):** Alot
**Reviewer role:** Project Owner / Thesis Researcher
**Approval decision:** **NOT APPROVED — PILOT ANNOTATION REMAINS BLOCKED**

## Decision summary

Phase 8.10 rechecked the pinned snapshot, external artifacts, manifest, tracked notice filenames, and local storage ACLs. All 13 manifest file hashes match the pinned Git blob bytes. The one-commit shallow-history limit is documented. A preliminary AI-assisted screen of the eligible Python scope reported no obvious credential/contact/identity indicators but flagged three formatted-number candidates in one file for human review. The root MIT notice is present; no separate conventionally named notice/attribution file or file-level license marker was found in the checked eligible scope. These are screening results, not completed human review or legal clearance.

Reviewer name and role are recorded above as supplied by the project owner. Source content from the 13 eligible files was provided for AI-assisted screening in Phase 8.10; service-side processing, data residency, and retention are not verified. Phase 8.11 was documentation-only and did not access or submit pilot source to AI services. The prior source processing remains a potential local-only policy deviation for the designated reviewer to assess. The checked storage directories inherit access for the local `BUILTIN\Users` group, including read/execute and create/append rights, so user-restricted access is not established. The remaining approval gates are not supported by attributable evidence. The history-scan provenance, human disposition of candidate data, complete human notice/terms review, suitable handling-controls attestation, and an authorized privacy approver's signed decision remain outstanding.

This is an evidence decision, not a finding that the repository contains personal/confidential data or that it does not. **No approval is granted.** No benchmark questions or other benchmark data were created for this phase.

## Evidence reviewed

| Gate | Evidence currently available | Phase 8.10 outcome |
|---|---|---|
| Snapshot identity and manifest integrity | The read-only checkout is at `392aef707c0e74341ab4a51420984e9ea6b566c5`. All 13 file hashes in the external manifest match the raw Git blob bytes at that commit; the manifest digest remains `a9f35063535978fd5fe099506c2152922dd42bb0bf95bc56df10de8396a32868`. | **Verified for snapshot and manifest integrity only.** Detailed paths/hashes remain external. |
| Saved secret scan artifacts | The external snapshot and history result files are each 3 bytes and parse as empty JSON arrays. Their SHA-256 values match the prior records. Those records name Gitleaks 8.30.1. | **Evidence of zero findings in the saved artifacts only.** The command/configuration and precise scope provenance are still absent. Gitleaks was not available in the current command environment, and no new scan was run. |
| History coverage | `--is-shallow-repository` is true; `git rev-list --count HEAD` returns one. The shallow-boundary file contains the pinned commit, and the parent is not reachable through this checkout. The saved history JSON has no scan command, refs/range, or configuration. Full history was **not** reviewed. | **OPEN — limited scope documented, not accepted.** No full-history result or authorized acceptance of the limitation/residual risk is evidenced. Gitleaks is unavailable in the current command environment; no new history scan was run. |
| Personal/confidential data | On 2026-09-27, an AI analysis agent screened the 13 manifest-listed Python files for obvious credentials/private keys, email/contact and identity/address indicators, and private user/customer data. Its preliminary output reported no obvious indicators in those categories, but flagged three formatted-number candidates in one eligible file. No raw values are included here. | **PRELIMINARY SCREEN ONLY — HUMAN REVIEW OPEN.** Reviewer of record is Alot, as supplied, but no evidence shows Alot performed or attested to this review. A human must adjudicate the candidates and document methods, result, and exclusions. The screen is not exhaustive and does not establish absence of personal/confidential data. |
| Root license | The pinned tree contains root `LICENCE` text identifying MIT; the earlier review confirmed its MIT terms. | **Root-license evidence present only.** It does not establish per-file notice conditions, source-processing authorization, or legal approval. |
| File-level notices and terms | Files checked: the complete tracked-path name inventory (89 paths), root `LICENCE`, and all 13 manifest-listed eligible Python files (their exact paths and hashes remain in the external manifest). The name inventory found only root `LICENCE` among conventional `LICENSE`/`LICENCE`, `NOTICE`, `COPYRIGHT`, `AUTHORS`, `CONTRIBUTORS`, and `ATTRIBUTION` names. The root text identifies the MIT License and its copyright/notice preservation condition. A preliminary screen found no common SPDX/license/copyright header markers in the 13 eligible files. | **PRELIMINARY INVENTORY ONLY — HUMAN/LEGAL REVIEW OPEN.** No separate conventional notice/attribution file or eligible-file header marker was found by these checks. They do not establish absence of nonstandard notices, fulfillment of MIT attribution obligations, or authorization to use source-derived data. |
| Eligible-file manifest | The external manifest is identified by SHA-256 `a9f35063535978fd5fe099506c2152922dd42bb0bf95bc56df10de8396a32868` and names the required snapshot, filter `phase4.5-python-v1`, 13 tracked/eligible Python files, and 2,915 eligible LOC. | **Artifact identity and aggregate counts confirmed previously; privacy approval of the scope is not established.** Detailed paths/hashes remain external. |
| Handling controls | Observed locations are `C:\Apps\Temp\Phase5.4\corpus\humanize`, `C:\Apps\Temp\Phase5.4\reports\privacy`, and `C:\Apps\Temp\Phase8\benchmark\pilot\python-humanize`. ACLs on the checkout and pilot evidence directory inherit access for `BUILTIN\Users` (read/execute plus create/append rights), as well as SYSTEM and Administrators. Source content from the 13 eligible files was provided for AI-assisted screening during this session; service-side processing, data residency, and retention are not verified. | **NOT ATTESTED / CONTROL GAP.** Access is not restricted to the named reviewer by the observed ACLs. No attestation covers source handling by the AI service, backups, retention, or deletion. Do not claim all source processing remained local. |
| Authorized approval | Reviewer name and role are recorded above as supplied by the project owner. No record establishes an authorized privacy approver's signed/attributable decision or residual-risk acceptance. | **NOT GRANTED.** Reviewer metadata does not constitute an approval attestation. |

## Phase 8.11 remediation package status

Created the [privacy remediation plan](privacy-remediation-plan.md) and four blank forms: [candidate data disposition](templates/privacy/candidate-data-disposition-template.md), [notice/license review](templates/privacy/notice-license-review-template.md), [handling controls](templates/privacy/handling-controls-template.md), and [AI processing policy decision](templates/privacy/ai-processing-policy-decision-template.md).

These documents assign proposed owners and specify required evidence; **they are templates, not completed reviews or attestations**. No candidate disposition, human notice review, access-control remediation, AI-processing policy disposition, full-history scan evidence, or approval sign-off was supplied in Phase 8.11. The privacy decision therefore remains **NOT APPROVED**.

## Phase 8.12 evidence status

Phase 8.12 was documentation-only. **No pilot source code was accessed or submitted to AI services during this phase.** The available evidence does not permit completion of the requested human attestations:

| Review | Phase 8.12 result | Remaining requirement |
|---|---|---|
| Candidate data disposition | Not completed. The prior aggregate screen records three formatted-number candidates but does not contain approved file/line locations, classifications, reviewer decisions, or justifications. No source was reopened to recover them. | Alot must inspect the candidates locally, fill the [candidate disposition form](templates/privacy/candidate-data-disposition-template.md) in a properly restricted location, record classifications/decisions/justifications, and attest/date it. Keep candidate locations and values out of Git and chat. |
| Notice/license review | Not completed as a human attestation. The Phase 8.10 filename/header inventory and root MIT-license observation remain preliminary. The [notice/license form](templates/privacy/notice-license-review-template.md) remains blank. | Alot must verify applicable LICENSE/LICENCE, NOTICE, COPYRIGHT, attribution and eligible-file conditions locally, record obligations/exclusions, and sign/date the completed form; seek legal/owner review if required. |
| Handling controls | Not attested. Previously observed folders inherit `BUILTIN\Users` read/execute and create/append rights; no access changes or lifecycle attestations were made. The [handling controls form](templates/privacy/handling-controls-template.md) remains blank. | Restrict access through an authorized administrator, then record effective permissions, owner, storage, external-processing decision, encryption/backups, retention, deletion, and sign/date the form. Assess the prior AI-agent source access. |
| AI processing policy | [Phase 8.12 policy decision](pilot-ai-processing-policy-decision.md) records hosted AI processing of pilot source/source-derived data as **NOT ALLOWED** under ADR-008 and the current instruction. | The decision does not resolve the prior Phase 8.10 AI-agent handling event. Alot and the appropriate privacy authority must assess service-side processing, residency, retention, and policy disposition; no exception is approved. |
| History and final approval | The checkout was previously verified shallow with one reachable commit; full history was not reviewed. No new scan, risk acceptance, signed review package, or authorized final decision was provided. | Record scanner provenance and full available history coverage, or obtain authorized written acceptance of the limitation; then submit the complete evidence package for a signed, attributable approval decision. |

The [Phase 8.12 remediation plan](privacy-remediation-plan.md) tracks the assigned actions and closure evidence. Blank templates and a policy-level `NOT ALLOWED` decision are not evidence that the candidate, notice, handling, or final approval checks have been completed.

## Why approval cannot be recorded

Approval requires evidence about people, applicable terms, data handling, and accepted risk—not only artifact hashes or automated scan output. Phase 8.10 adds useful scoped checks, but in particular:

1. The history scan cannot be characterized as full-history, and the narrower scope has not been justified and accepted by an authorized approver.
2. Three formatted-number candidates from the preliminary screen still need human adjudication; the required personal/confidential-data review has no attributable human completion record.
3. The filename/header inventory is preliminary and does not establish complete human review of applicable notices, MIT attribution obligations, terms, and exclusions.
4. Observed ACLs allow the local `BUILTIN\Users` group access; the directory is not shown to be reviewer-restricted. The 13 source files were made available to an AI analysis agent, but processing location/retention cannot be verified. Backup, retention, deletion, and AI-service handling lack a pilot-specific attestation.
5. Although reviewer name and role are recorded, no authorized privacy approver's date-attributed, signed decision referencing the evidence and limitations is present.

These gates remain unresolved; therefore the status must remain **NOT APPROVED**. Do not infer approval from the user's instruction, project ownership, MIT license, a clean worktree, empty saved scan JSON files, a preliminary AI screen, or a reconciled manifest.

## Required evidence before reconsideration

A designated, authorized human reviewer must provide or perform, on the controlled local system, using the blank forms linked above:

1. A provenance record for secret scans (tool/version, command, configuration, exact snapshot and history refs/range, output digest, and finding dispositions), with full required history scanned or the one-commit limitation explicitly justified and accepted by an authorized approver.
2. Alot or another designated human reviewer must adjudicate the three formatted-number candidates on the controlled local system and complete the personal/confidential-data review for the exact snapshot and eligible scope, documenting identity/role, date, methods/categories, result, and exclusions. The candidate file/line details are not present in the approved aggregate record; retrieve/verify them locally without submitting source to AI services. Assess and document the prior AI-agent source access under the applicable local-only research policy.
3. A human file-level notice and applicable-terms review, with applicable MIT attribution/retention conditions and excluded files; obtain legal/owner review if required.
4. An attestation of manifest digest/filter/scope and handling controls. Restrict the data directories to authorized reviewers, document local/offline and telemetry handling, determine/disclose prior AI-service processing and retention, and attest backups, retention, and deletion.
5. Confirmation that the named reviewer is the authorized privacy approver, plus an explicit `APPROVED` or `REJECTED` decision, date, exact snapshot, evidence references/digests, limits/residual risks, and signature or equivalent attributable attestation. The reviewer name and role alone do not provide this sign-off.

Keep raw scan outputs, detailed findings, source-derived notes, and per-file inventory outside Git. Reassess this decision only after the evidence is supplied; a future approval must be recorded as a new attributable decision rather than inferred from this report.

## Next allowed activity

Only non-annotation privacy evidence collection and documentation may proceed: the designated human reviewer may complete the listed checks locally, after correcting/reviewing access controls and assessing the prior AI-agent source access. Do not submit pilot source to AI or other hosted services while the local-only handling question is unresolved. Until an authorized approval is recorded, do **not** inspect the pilot for benchmark annotation, create or consume a chunk inventory, create questions, query IDs, gold chunk references or relevance labels, or run indexing, embedding, retrieval, metric, or experiment work.

This decision applies only to `python-humanize/humanize` at the specified snapshot. It does not clear other corpus repositories or the full benchmark.

## Related records

- [Phase 8.11 privacy remediation plan](privacy-remediation-plan.md)
- [Phase 8.12 AI processing policy decision](pilot-ai-processing-policy-decision.md)
- [Candidate data disposition template](templates/privacy/candidate-data-disposition-template.md)
- [Notice/license review template](templates/privacy/notice-license-review-template.md)
- [Handling controls template](templates/privacy/handling-controls-template.md)
- [AI processing policy decision template](templates/privacy/ai-processing-policy-decision-template.md)
- [Phase 8.8 final pilot privacy review](pilot-privacy-final-review.md)
- [Phase 8.7 pilot privacy review and approval record](pilot-privacy-approval.md)
- [Phase 8.6 pilot privacy clearance record](pilot-privacy-clearance.md)
- [Phase 8.5 privacy clearance report](privacy-clearance-report.md)
- [Dataset manifest validation](corpus-manifest-validation.md)
- [ADR-008: source-code privacy](../decisions/ADR-008-source-code-privacy.md)
- [ADR-013: dataset snapshot freeze](../decisions/ADR-013-dataset-snapshot-freeze.md)
- [ADR-014: embedding privacy policy](../decisions/ADR-014-embedding-privacy-policy.md)
