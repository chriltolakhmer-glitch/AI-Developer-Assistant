# Phase 8.6 — Pilot Privacy Clearance Record

**Review date:** 2026-09-27
**Status:** **NOT CLEARED — PILOT ANNOTATION BLOCKED**

## Repository and snapshot identity

| Field | Recorded value |
|---|---|
| Canonical repository | `python-humanize/humanize` |
| Pinned commit | `392aef707c0e74341ab4a51420984e9ea6b566c5` |
| External checkout | `C:\Apps\Temp\Phase5.4\corpus\humanize` |
| Checkout verification | `HEAD` matched the pinned full SHA; detached checkout; clean worktree at review |
| History availability | Shallow clone (`--is-shallow-repository=true`); full upstream history was not available in this checkout |
| Preprocessing baseline | Existing Phase 5.4 report records 13 eligible Python files and 126 deterministic chunks; this is not privacy clearance or authorization to use a chunk inventory |

## Privacy checks and evidence

The existing local Gitleaks 8.30.1 reports were checked in aggregate on 2026-09-27. No new scan was run. Both saved JSON reports contain an empty result array (`[]`), so **zero findings were recorded in these two reports**:

| Scope | Saved report | Report timestamp (UTC) | Finding result | SHA-256 |
|---|---|---|---|---|
| Working-tree snapshot scan | `C:\Apps\Temp\Phase5.4\reports\privacy\humanize-dir.json` | 2026-09-26 17:18:02 | 0 reported | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| Available Git-history scan | `C:\Apps\Temp\Phase5.4\reports\privacy\humanize-git.json` | 2026-09-26 17:18:03 | 0 reported | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |

The report digests and aggregate outcome are recorded here; raw scan reports remain outside Git. The history result covers only the shallow local history, not the full upstream history. The prior corpus report documents a Sphinx `.dot` history-scan error; that is a separate repository finding, not a humanize finding.

**No manual personal/confidential-data review is evidenced.** Automated secret scanning is not a substitute for that review. No attributable pilot-specific privacy approval was found in the reviewed records. No clearance is granted by this report.

## License and notice checks

- The pinned Git tree contains the root `LICENCE` file. The file identifies the MIT License; the corpus screening record also records MIT for this repository.
- This establishes root-license evidence only. It is not legal advice or a completed review of all applicable file-level notices, attribution/retention requirements, or the authorization to include source-derived evidence in this pilot.
- A reviewer must complete and record the applicable notice/terms check for the intended Python scope before source annotation. Preserve required notices and keep any source excerpts out of Git.

## Remaining findings and gates

| Gate | Status | Required resolution |
|---|---|---|
| Secret scan on pinned snapshot | **Evidence available: 0 reported in saved report** | Confirm the scan scope/configuration and that it corresponds to this exact SHA; retain its external provenance record. This result alone does not clear the pilot. |
| Full-history coverage | **OPEN** | The checkout is shallow. Obtain/scan the available history or have an authorized reviewer document an acceptable scope limitation and residual risk. |
| Personal/confidential-data review | **OPEN — NOT EVIDENCED** | Complete a documented review of the exact snapshot and eligible scope, including reviewer, date, result, and exclusions. |
| License and file notices | **PARTIAL** | Root MIT `LICENCE` verified; complete and record the applicable file-level notice/terms review. |
| Final eligible-file manifest and exclusions | **OPEN / NOT EVIDENCED AS A CLEARANCE RECORD** | Reconcile the approved filter, eligible/excluded files and reasons, per-file hashes, parser/count result, and any changes against the pinned SHA. Keep the detailed manifest external. |
| Handling/access/retention controls | **NOT APPROVED IN A PILOT-SPECIFIC RECORD** | Confirm the controlled local research-data location, access restriction, telemetry/offline handling, retention, and deletion procedure. |
| Attributable approval | **NOT GRANTED / NOT EVIDENCED** | Identify the authorized privacy approver and record a signed/date-attributed decision referencing the evidence and limits above. Do not infer approval from project ownership or a zero-finding scan. |

## Decision

**Pilot privacy status: NOT CLEARED.** The two existing Gitleaks reports show zero recorded findings for the scopes they covered, and the exact snapshot/root license identity are verified. However, the clone is shallow, a personal/confidential-data review and complete notice review are not evidenced, the pilot manifest/exclusions are not reconciled as clearance evidence, and no attributable approval is recorded. Therefore the pilot remains blocked: do not inspect the checkout to author questions, create or consume its chunk inventory, or validate gold chunk references until the open gates are resolved and clearance is explicitly recorded.

This is a pilot-only status. It says nothing that clears the remaining eight snapshots or the full corpus. No embedding, index, retrieval, metric run, or full experiment is authorized. The pilot category labels requested for the plan (`function discovery`, `architecture understanding`, `dependency understanding`, `behavior understanding`) also require a documented pilot-only category map; they differ from the final benchmark's frozen taxonomy and must not silently replace it.

See [dataset snapshot freeze](dataset-snapshot-freeze.md), [corpus checkout validation](corpus-checkout-validation.md), [ADR-008](../decisions/ADR-008-source-code-privacy.md), [ADR-013](../decisions/ADR-013-dataset-snapshot-freeze.md), [ADR-014](../decisions/ADR-014-embedding-privacy-policy.md), and the [annotation pilot plan](annotation-pilot-plan.md).