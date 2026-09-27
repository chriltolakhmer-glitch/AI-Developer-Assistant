# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 8.5 — Privacy Clearance Report

**Review date:** 2026-09-27

**Repository baseline reviewed:** `a41bfda`

**Status:** **OPEN — PRIVACY CLEARANCE NOT GRANTED**

## Decision and scope

The committed research record does not establish privacy clearance for any of the nine selected snapshots. Do not start annotation source inspection, produce or consume a chunk inventory, index, embed, retrieve, or run experiments until the applicable repository-specific checks below are evidenced and approved. This report records the state documented in Git; it is not a new scan, a review of the external scan files, a legal opinion, or an approval.

The Phase 5.4 preprocessing result is **PASS for the pinned snapshot/file/LOC and deterministic parser/chunker checks only**. It is not a secret, personal-data, confidentiality, or license clearance. The privacy policy in [ADR-008](../decisions/ADR-008-source-code-privacy.md), [ADR-013](../decisions/ADR-013-dataset-snapshot-freeze.md), and [ADR-014](../decisions/ADR-014-embedding-privacy-policy.md) remains binding and conditional.

## Evidence reviewed

- [Repository corpus screening](repository-corpus-final.md) and [manifest validation](corpus-manifest-validation.md): exact revisions, root license-file presence, and file/LOC counts were checked; secret/privacy screening remained a separate prerequisite.
- [Corpus checkout validation](corpus-checkout-validation.md) and [dataset snapshot freeze](dataset-snapshot-freeze.md): preprocessing validated all nine pinned snapshots, while explicitly leaving the privacy gate open.
- [ADR-008](../decisions/ADR-008-source-code-privacy.md), [ADR-013](../decisions/ADR-013-dataset-snapshot-freeze.md), and [ADR-014](../decisions/ADR-014-embedding-privacy-policy.md): processing, local-only handling, exclusions, storage, and authorization policy.
- [Benchmark annotation guide](benchmark-annotation-guide.md), [benchmark finalization](benchmark-finalization.md), and [annotation workflow](benchmark-annotation-workflow.md): no corpus annotation or source-derived inventory before the prerequisite is met.

The detailed/redacted Gitleaks reports and other file-level audit artifacts are external. Their contents and any approval records were not inspected for this documentation update. No scan was run and no external research data was read or changed.

## Current documented status

| Gate | Evidence in the committed record | Status |
|---|---|---|
| Snapshot identity and preprocessing | All nine exact SHAs, file/LOC baselines, and preprocessing results are documented as matching; 1,916 files parsed and 33,415 chunks generated deterministically. | **PASS for preprocessing only** |
| Secret/credential scan | Gitleaks 8.30.1 snapshot scans reported eight candidate findings: six Flask, one pytest, and one Sphinx. | **OPEN** — candidates are not manually dispositioned |
| History scan | The checkouts were shallow, with only the pinned commit available. The Sphinx history scan also reported an unsupported `.dot` file. | **OPEN** — history coverage/error not resolved or justified in the record |
| Personal/confidential-data review | The freeze and checkout reports state that this review has not been completed. | **OPEN** |
| License and notices | Root license files and screening identifiers are recorded. Per-file notices still require attention, especially in mypy and Sphinx. | **PARTIAL** — no complete file-level review/approval is recorded |
| Final scanner manifest and exclusion reconciliation | Manifest documentation requires the exact filter, eligible/excluded file records, hashes, reasons, and count reconciliation before processing. The preprocessing pass does not close the privacy review. | **OPEN / not evidenced as a privacy approval** |
| Privacy approval | No repository-specific clearance decision and attributable approval is present in the reviewed records. | **NOT GRANTED** |

“Candidate finding” is deliberate: the records do not establish that the eight scanner results are confirmed secrets or false positives. They must each receive a documented disposition; do not report them as confirmed exposures without evidence.

## Required checks before any pilot source annotation

The proposed pilot repository is [python-humanize/humanize](https://github.com/python-humanize/humanize), pinned at `392aef707c0e74341ab4a51420984e9ea6b566c5`. Before reading it for annotation or generating/using its chunk inventory:

1. **Confirm the exact snapshot.** Use a read-only checkout at the full SHA. Record the checked-out SHA, acquisition date, and clean-worktree verification.
2. **Complete secret/credential review.** Retain the scanner name/version, configuration, scope, date, output digest, and redacted finding references externally. Manually disposition every candidate affecting this snapshot; document remediation/exclusion and scan the resulting eligible set again where applicable.
3. **Resolve history coverage.** Obtain and scan the required available history or document why a narrower scan is sufficient, how the `.dot` error is resolved/handled, and the residual risk. Record the approved rationale; a failed or incomplete scan is not a pass.
4. **Complete personal/confidential-data review.** Document the reviewed scope, categories/checks, reviewer, date, result, and any file/repository exclusions. If processing permission cannot be established, exclude or replace the repository through a versioned protocol decision.
5. **Verify license and notices.** Confirm the applicable license terms and file-level notices for material in the Python scope, preserve notices, and record any files that cannot be included. This is a research clearance check, not legal advice.
6. **Reconcile the scanner manifest.** Apply the approved shared file filter to the exact SHA; retain the eligible/excluded file inventory, per-file hashes, exclusion reasons, parser status, and count/stratum reconciliation in the controlled external location. Do not silently alter the corpus or strata.
7. **Verify handling controls.** Keep checkouts, inventories, source-derived annotations, raw scan outputs, and review evidence outside Git in the approved access-controlled location. Use local processing only, disable optional telemetry where supported, avoid hosted analysis/labeling, and document access, retention, and deletion controls.
8. **Record an attributable decision.** Identify the privacy reviewer and authorized approver; record date, exact repository/SHA, evidence references/digests, exclusions, residual risks, decision, and any limits. The existing decisions do not name a privacy approver, so one must be designated rather than inferred.

## Approval criteria and scope of a clearance

A **pilot-repository clearance** may be recorded only when all checks above pass for the exact pilot snapshot, every relevant candidate is dispositioned, the personal/confidential-data and license/notice reviews are complete, the final manifest is reconciled, and an authorized reviewer/approver signs the external record. If any check is incomplete, ambiguous, or failed, the status remains **OPEN** or the repository is **EXCLUDED**; do not generate/use pilot chunks or annotations.

A pilot-only approval is **not** clearance for the other eight repositories or for the complete study. **Full-corpus clearance** requires the same documented checks and approval for every repository in the frozen corpus. Any exclusions/replacements require an explicit versioned corpus decision and updated counts before use. No approval is recorded by this report, and no repository is represented as cleared.

## Handling and non-authorizations

- Raw source, raw chunk content, query text quoting source, detailed secret findings, per-file paths/spans, chunk inventories, and audit records stay outside Git. Commit only non-sensitive protocol text and appropriately aggregated status.
- Treat derived chunks, IDs/provenance, and later embeddings/indexes as confidential source-derived research material. Do not upload them to hosted LLMs, embedding APIs, hosted notebooks, external labeling providers, telemetry, or cloud search/vector services.
- A successful scanner run, preprocessing report, unit test, root license file, or blank annotation template does not independently grant clearance.
- This report does not authorize corpus reading for annotation, chunk inventory generation, indexing, embedding, retrieval, or experiments.

See [ADR-008](../decisions/ADR-008-source-code-privacy.md), [ADR-013](../decisions/ADR-013-dataset-snapshot-freeze.md), [ADR-014](../decisions/ADR-014-embedding-privacy-policy.md), and the [Phase 8.5 annotation pilot plan](annotation-pilot-plan.md).