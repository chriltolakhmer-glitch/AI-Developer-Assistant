# Phase 8.9 — Final Pilot Privacy Approval Decision

**Decision date:** 2026-09-27
**Thesis repository baseline:** `85e343563d3402f021bb9b306f171eeefa5bedbe`
**Pilot repository:** `python-humanize/humanize`
**Required snapshot:** `392aef707c0e74341ab4a51420984e9ea6b566c5`
**Reviewer:** GitHub Copilot (AI-assisted evidence reconciliation; not an authorized human privacy approver)
**Approval decision:** **NOT APPROVED — PILOT ANNOTATION REMAINS BLOCKED**

## Decision summary

The Phase 8.8 final review and prior Phase 8.5–8.7 records were rechecked against the available local evidence. The pinned snapshot identity, saved empty scan artifacts, root MIT license text, and external eligible-file manifest identity and aggregate counts are documented. The remaining approval gates are not supported by attributable evidence. The chat instruction “Approve all” does not supply the missing history-scan provenance, a completed personal/confidential-data assessment, per-file notice review, handling-controls attestation, or an identified authorized approver's signed decision; it cannot substitute for those records.

This is an evidence decision, not a finding that the repository contains personal/confidential data or that it does not. **No approval is granted.** No benchmark questions or other benchmark data were created for this phase.

## Evidence reviewed

| Gate | Evidence currently available | Phase 8.9 outcome |
|---|---|---|
| Snapshot identity | The existing read-only checkout is detached at `392aef707c0e74341ab4a51420984e9ea6b566c5`; its worktree was clean when previously checked. | **Verified for identity only.** |
| Saved secret scan artifacts | The external snapshot and history result files are each 3 bytes and parse as empty JSON arrays. Their SHA-256 values match the prior records. Those records name Gitleaks 8.30.1. | **Evidence of zero findings in the saved artifacts only.** The command/configuration and precise scope provenance are still absent. Gitleaks was not available in the current command environment, and no new scan was run. |
| History coverage | The checkout is shallow; `git rev-list --count HEAD` reports one reachable commit. The shallow boundary hides the recorded parent from normal history traversal. The existing history JSON contains no scan command, refs/range, or configuration. | **OPEN.** Full history coverage is not established, and there is no documented authorized acceptance of a narrower scope and its residual risk. |
| Personal/confidential data | Prior records say that no attributable manual review was performed or found. There is no human reviewer, method/category checklist, result, or exclusions record for this snapshot and eligible scope. | **NOT EVIDENCED / OPEN.** No absence claim is made. An automated secret scan is not this assessment. |
| Root license | The pinned tree contains root `LICENCE` text identifying MIT; the earlier review confirmed its MIT terms. | **Root-license evidence present only.** It does not establish per-file notice conditions, source-processing authorization, or legal approval. |
| File-level notices and terms | The previous final review found only the root `LICENCE` by conventional license/notice filename and documented no attributable review of notices or license headers across eligible files. No subsequent review record was found. | **OPEN / PARTIAL.** A complete eligible-file notice/terms assessment, attribution/retention conditions, and exclusions are not evidenced. |
| Eligible-file manifest | The external manifest is identified by SHA-256 `a9f35063535978fd5fe099506c2152922dd42bb0bf95bc56df10de8396a32868` and names the required snapshot, filter `phase4.5-python-v1`, 13 tracked/eligible Python files, and 2,915 eligible LOC. | **Artifact identity and aggregate counts confirmed previously; privacy approval of the scope is not established.** Detailed paths/hashes remain external. |
| Handling controls | Prior records identify an external local checkout/manifest location, but no pilot-specific attestation establishes who can access it, backups, offline/telemetry handling, retention period, or deletion procedure. | **OPEN.** A path outside Git is not proof of the required controls. |
| Authorized approval | No named/identified authorized human approver, role, explicit evidence-based decision, signature/attestation, or residual-risk acceptance is present in the records reviewed. | **NOT GRANTED.** This AI-authored record is not approval or a human attestation. |

## Why approval cannot be recorded

Approval requires evidence about people, applicable terms, data handling, and accepted risk—not only artifact hashes or automated scan output. In particular:

1. The history scan cannot be characterized as full-history, and the narrower scope has not been justified and accepted by an authorized approver.
2. The required personal/confidential-data review has no attributable human completion record.
3. The eligible Python files do not have a documented complete notice/terms and attribution review.
4. Required access, backup, offline/telemetry, retention, and deletion controls lack a pilot-specific attestation.
5. No authorized privacy approver is identified with a date-attributed, signed decision referencing the evidence and limitations.

These gates remain unresolved; therefore the status must remain **NOT APPROVED**, notwithstanding the request to approve all. Do not infer approval from the user's instruction, project ownership, MIT license, a clean worktree, the empty saved scan JSON files, or the manifest.

## Required evidence before reconsideration

A designated, authorized human reviewer must provide or perform, on the controlled local system:

1. A provenance record for secret scans (tool/version, command, configuration, exact snapshot and history refs/range, output digest, and finding dispositions), with full required history scanned or an explicitly justified and accepted scope limitation/residual risk.
2. A personal/confidential-data review of the exact snapshot and approved eligible scope, including reviewer identity/role, date, methods/categories, result, and exclusions.
3. A file-level notice and applicable-terms review, with applicable attribution/retention conditions and excluded files; obtain legal/owner review if required.
4. An attestation of manifest digest/filter/scope and handling controls: authorized access, controlled location, local/offline and telemetry handling, backups, retention, and deletion.
5. The authorized approver's name and role, explicit `APPROVED` or `REJECTED` decision, date, exact snapshot, evidence references/digests, limits/residual risks, and signature or equivalent attributable attestation.

Keep raw scan outputs, detailed findings, source-derived notes, and per-file inventory outside Git. Reassess this decision only after the evidence is supplied; a future approval must be recorded as a new attributable decision rather than inferred from this report.

## Next allowed activity

Only non-annotation privacy evidence collection and documentation may proceed: the designated human reviewer may complete the listed checks and attestations. Until an authorized approval is recorded, do **not** inspect the pilot for benchmark annotation, create or consume a chunk inventory, create questions, query IDs, gold chunk references or relevance labels, or run indexing, embedding, retrieval, metric, or experiment work.

This decision applies only to `python-humanize/humanize` at the specified snapshot. It does not clear other corpus repositories or the full benchmark.

## Related records

- [Phase 8.8 final pilot privacy review](pilot-privacy-final-review.md)
- [Phase 8.7 pilot privacy review and approval record](pilot-privacy-approval.md)
- [Phase 8.6 pilot privacy clearance record](pilot-privacy-clearance.md)
- [Phase 8.5 privacy clearance report](privacy-clearance-report.md)
- [Dataset manifest validation](corpus-manifest-validation.md)
- [ADR-008: source-code privacy](../decisions/ADR-008-source-code-privacy.md)
- [ADR-013: dataset snapshot freeze](../decisions/ADR-013-dataset-snapshot-freeze.md)
- [ADR-014: embedding privacy policy](../decisions/ADR-014-embedding-privacy-policy.md)
