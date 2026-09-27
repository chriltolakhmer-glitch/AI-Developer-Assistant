# Phase 8.8 — Final Pilot Privacy Review

**Review date:** 2026-09-27
**Thesis repository baseline:** `397d24ed54455258fac742d3337f8a7c8942d070`
**Pilot repository:** `python-humanize/humanize`
**Required snapshot:** `392aef707c0e74341ab4a51420984e9ea6b566c5`
**Decision:** **NOT APPROVED — PILOT ANNOTATION REMAINS BLOCKED**

## Scope and boundary

This review reconciles the committed Phase 8.5–8.7 privacy records with the referenced external scan reports, manifest metadata, and read-only Git metadata for the pilot checkout. The pilot checkout is detached at the required SHA, has no reported worktree changes, and is shallow. This is a documentation/evidence review, not an attributable human privacy assessment, legal opinion, or approval.

No new Gitleaks scan was run. The pilot's source files were not reviewed here to make personal/confidential-data or per-file notice determinations. No scanner, parser, chunker, embedding, FAISS, BM25, RRF, retrieval, or evaluation-metric work was run. No benchmark questions were created.

## Evidence reconciliation

| Review area | Evidence confirmed | Finding / status |
|---|---|---|
| Snapshot identity | The external checkout's `HEAD` is `392aef707c0e74341ab4a51420984e9ea6b566c5`; it is detached and `git status` reports no worktree changes. | **PASS for identity only.** This does not grant processing permission. |
| Snapshot secret scan | The external `humanize-dir.json` exists, is 3 bytes, parses as an empty JSON result array, and has SHA-256 `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`, matching the digest recorded in the prior privacy records. Those records identify Gitleaks 8.30.1. | **0 findings in the saved artifact; not a privacy clearance.** The command, configuration, and precise scan scope/provenance are not established by the artifact or committed records. No scan was repeated. |
| History scan scope | The external `humanize-git.json` exists, is 3 bytes, parses as an empty JSON result array, and has the same SHA-256 as recorded previously. The associated checkout reports `--is-shallow-repository=true`; `git rev-list --count HEAD` returns `1`. The commit object records a parent, and that parent object exists, but the shallow boundary hides it from `HEAD^` traversal. | **OPEN.** The evidence supports at most an empty saved result associated with the shallow checkout's scan scope. The scan command, refs/range, configuration, and exact coverage are not documented, and full upstream-history coverage is not established. Do not call this a full-history pass. |
| Personal/confidential data | Phase 8.6 and 8.7 records explicitly report no attributable manual review. No reviewer, date, method/category checklist, result, or exclusions are supplied. | **NOT REVIEWED / OPEN.** Secret scanning does not substitute for this review. This record does not claim that personal or confidential data is absent. |
| Root license | At the pinned Git tree, the tracked root `LICENCE` contains the MIT permission and warranty text; prior corpus-screening and privacy records also identify MIT. | **Root MIT evidence confirmed.** This confirms the root license only; it is not legal advice, permission from an authorized reviewer, or a complete terms review. |
| File-level notices and terms | A name-only query of the pinned tree found the root `LICENCE` as the conventionally named license/notice file. No attributable review of notices or license headers in each eligible file is documented. | **OPEN / PARTIAL.** The name-only check cannot establish that eligible files have no additional notices or conditions. Applicable per-file notices, attribution and retention conditions, and exclusions still require review. |
| Eligible-file manifest | The external `eligible-file-manifest.json` exists and its SHA-256 is `a9f35063535978fd5fe099506c2152922dd42bb0bf95bc56df10de8396a32868`, matching Phase 8.7. Its metadata identifies `python-humanize/humanize`, the required commit, schema version `1.0`, filter `phase4.5-python-v1`, 13 tracked Python files, 13 eligible Python files, and 2,915 eligible LOC. The prior record reports zero excluded files. | **PASS for artifact identity and aggregate reconciliation only.** The detailed manifest remains external; the check does not constitute privacy review or approval of the filter/exclusions. No file paths or per-file hashes are copied into this repository. |
| Handling, access, retention, deletion | Prior records place the checkout and manifest outside the thesis Git repository. They do not contain a complete pilot-specific attestation for access restriction, backups, telemetry/offline handling, retention, and deletion. | **PARTIAL / OPEN.** Location alone does not prove the required controls. |
| Attributable approval | No authorized approver, signed/date-attributed decision, or documented acceptance of residual risk is present in the reviewed records. | **NOT GRANTED.** Approval cannot be inferred from a clean worktree, empty scan artifacts, root license, manifest, project ownership, or this review. |

### Evidence provenance and limits

The two saved scan artifacts are present outside the thesis repository and their bytes/digests and empty result arrays were checked for this review. The manifest is also present externally; its digest, snapshot identity, filter identifier, and aggregate summary were checked without copying its file-level inventory into Git. These checks verify the referenced artifacts, not how they were produced. The prior Phase 8.7 record is more specific than Phase 8.6 about the manifest; this review confirms the cited external manifest and records the reconciliation, without treating it as privacy clearance.

## Remaining blockers

Before any pilot annotation, chunk inventory use, or benchmark-question work, all of the following must be resolved in an attributable, controlled review record:

1. **History scope:** provide the scan command/configuration and exact refs/range, scan the required available history, or have an authorized approver explicitly justify and accept a documented scope limitation and residual risk. Do not describe shallow coverage as full history.
2. **Personal/confidential-data review:** a designated human reviewer must review the exact approved snapshot and eligible scope, recording identity/role, date, methods/categories considered, results, and exclusions. An empty secret scan is not a substitute.
3. **File notices and applicable terms:** review eligible-file notices/headers and relevant terms, record attribution/retention requirements and exclusions, and obtain legal/owner review if required. Root MIT text alone does not close this gate.
4. **Manifest approval:** have the reviewer confirm the external manifest digest and the approved filter, eligible/excluded scope, and count reconciliation. If it changes, record the replacement digest and reconcile the change. Keep detailed paths and hashes external.
5. **Handling controls:** document the approved controlled location, authorized access, local/offline and telemetry handling, backup/retention period, and deletion procedure.
6. **Authorized decision:** record the approver's name/role, explicit `APPROVED` or `REJECTED` decision, date, snapshot, evidence references/digests, limits/residual risks, and signature/attestation. A blank field or this report is not approval.

## Final decision

**Pilot privacy status: NOT APPROVED. Pilot annotation remains blocked.** Evidence confirms the pinned snapshot identity, two empty saved scan result artifacts with matching recorded digests, root MIT license text, and the exact external manifest identity and aggregate counts. It does not establish the history scan's full scope, a completed personal/confidential-data review, complete per-file notice/terms review, approved handling controls, or an attributable authorized approval.

Until those blockers are resolved and an authorized approval is recorded, do not inspect the pilot for annotation, create or consume a chunk inventory, write benchmark questions, or validate gold chunk references. No benchmark questions were created in Phase 8.8. This decision applies only to the stated pilot snapshot; it does not clear other repositories or the full corpus, and it authorizes no embedding, indexing, retrieval, metric run, or experiment.

## Related records

- [Phase 8.7 pilot privacy review and approval record](pilot-privacy-approval.md)
- [Phase 8.6 pilot privacy clearance record](pilot-privacy-clearance.md)
- [Phase 8.5 privacy clearance report](privacy-clearance-report.md)
- [Dataset manifest validation](corpus-manifest-validation.md)
- [Dataset snapshot freeze](dataset-snapshot-freeze.md)
- [ADR-008: source-code privacy](../decisions/ADR-008-source-code-privacy.md)
- [ADR-013: dataset snapshot freeze](../decisions/ADR-013-dataset-snapshot-freeze.md)
- [ADR-014: embedding privacy policy](../decisions/ADR-014-embedding-privacy-policy.md)
