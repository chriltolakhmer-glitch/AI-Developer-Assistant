# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 12.3 — Repository Approval Evidence Closure

**Status:** WORKFLOW DEFINED — no repository approval is newly recorded.

**Review baseline:** [Consolidated repository approval status](repository-approval-status-report.md), commit `63b30a8`.

**Current result:** All nine repositories remain **BLOCKED**. No new external scan, checkout, license review, personal-data review, or approval evidence was inspected or created for this phase.

This is a lightweight closure workflow for a solo thesis. It defines how existing external evidence may be assembled and verified without placing sensitive findings, source-derived data, credentials, raw reports, or signatures in the thesis Git repository. It does not authorize source inspection, benchmark annotation, indexing, embedding, retrieval, experiments, or external transmission.

## 1. Fail-closed closure states

Use one state per repository and per gate:

| State | Meaning | Permitted transition |
|---|---|---|
| `NOT STARTED` | No evidence packet has been assembled. | `IN PROGRESS` when work begins. |
| `IN PROGRESS` | Evidence is being collected or checked; no conclusion may be inferred. | `PASS`, `BLOCKED`, or back to `IN PROGRESS`. |
| `PASS` | Required evidence is present, scoped to the exact SHA, attributable, dated, and independently checkable. | Remains `PASS` only while scope and controls remain unchanged. |
| `BLOCKED` | Evidence is missing, contradictory, failed, out of scope, or not attributable. | `IN PROGRESS` after remediation; never directly to approval. |
| `READY FOR DECISION` | All applicable gates are `PASS` or have an explicitly documented, authorized exception, and the packet is internally reconciled. | `APPROVED`, `APPROVED WITH CONTROLS`, or `REJECTED` by the authorized decision-maker. |
| `APPROVED` / `APPROVED WITH CONTROLS` | Explicit decision recorded for the exact snapshot, scope, purpose, and conditions. | Suspended or re-reviewed if any scope, finding, or control changes. |

A blank field, a project-owner statement without evidence, a public URL, a root license identifier, a preprocessing result, a passing test, or a clean partial scan is not a `PASS` and cannot advance a repository to `READY FOR DECISION`.

## 2. Minimal external evidence packet

Create one access-controlled packet outside the thesis Git repository for each exact repository/SHA. Use a non-sensitive packet ID and retain raw reports, detailed paths, source-derived material, and signatures only in the approved local research-data area.

| Packet item | Minimum evidence to retain externally | Closure test |
|---|---|---|
| Identity | Full SHA, local checkout alias, detached/read-only and clean-worktree result, date, digest/reference | `HEAD` equals the frozen SHA and the checkout was not modified. |
| Secret scan | Tool/version, configuration, exact scope/SHA, date, report digest, redacted candidate references, disposition of every candidate | Every candidate is dispositioned; exclusions/remediation are recorded and any required rescan is complete. |
| History | Refs/range, shallow/full status, tool/configuration, date, report digest, errors and accepted limitations | Coverage is resolved or an authorized decision explicitly accepts a documented limitation and residual risk. |
| Personal/confidential review | Reviewer, date, scope/categories, method, result, exclusions, evidence reference | A designated human review covers the approved file scope; no absence is inferred from secret scanning. |
| License/notices | Exact root license, applicable file-level notices, reviewer, attribution/retention conditions, exclusions, date | The eligible scope has a documented terms outcome and required notices/conditions are preserved. |
| Manifest | Filter version, exact SHA, eligible/excluded inventory, hashes/counts, parser status, reconciliation digest | Counts and exclusions reconcile to the frozen corpus decision; changes trigger a versioned corpus decision. |
| Handling controls | Storage alias, access check, local/offline and telemetry settings/limitations, backup encryption/access, retention and deletion record | Controls are evidenced for the actual packet and source scope, not merely promised by policy. |
| Historical exposure | Retrospective assessment where applicable, reviewer, date, evidence reference, unresolved risk | Conflicts or prior exposure are assessed; they are not silently reinterpreted as approval. |
| Decision | Authorized approver, role, exact SHA/scope/purpose, decision/date, conditions, attestation reference | Decision is explicit, attributable, dated, and bound to the packet. |

Evidence references in committed records should be limited to safe packet aliases or digests. Do not commit raw scanner output, source excerpts, candidate secrets, detailed file paths, private reviewer material, or signatures.

## 3. Solo-thesis closure sequence

Process one repository at a time, starting with the repository selected by the already documented protocol. Do not process source for annotation while closing evidence; the evidence task is an authorization review, not benchmark authoring.

1. **Freeze identity.** Copy the canonical repository ID, URL, exact full SHA, snapshot set, language scope, filter version, and screening counts from the frozen corpus record. Resolve any mismatch before continuing.
2. **Assemble the packet.** Gather only existing local evidence or conduct the explicitly permitted local checks under the privacy policy. Record tool versions, dates, scope, digests, and reviewer role. Keep detailed artifacts outside Git.
3. **Close objective gates.** Evaluate identity, scan/disposition, history, personal/confidential data, license/notices, manifest, handling, and historical-exposure gates independently. Mark missing or contradictory evidence `BLOCKED`.
4. **Reconcile.** Confirm that every `PASS` refers to the same repository, exact SHA, Python scope, filter, exclusions, and packet. Re-run or supersede stale evidence when identity or scope differs.
5. **Perform a solo quality check.** The researcher may collect and review evidence, but must record the single-reviewer limitation. Do not claim independent review or inter-rater agreement. Where a separate legal, privacy, or repository authority is required, obtain that attributable decision externally rather than inferring it.
6. **Prepare the decision request.** Only when all mandatory gates are `PASS`, or an authorized exception is explicitly documented, set the record to `READY FOR DECISION`. List conditions, exclusions, stop triggers, residual risks, and the exact permitted purpose.
7. **Record the decision.** The authorized approver records `APPROVED`, `APPROVED WITH CONTROLS`, or `REJECTED`, with name/role, date, exact scope, and attestation reference. A researcher recommendation is not the decision.
8. **Update the committed record.** Commit only non-sensitive status, safe evidence aliases/digests, aggregate outcomes, and the explicit decision. Leave the repository `BLOCKED` when any mandatory evidence or authorization is absent.
9. **Recheck before handoff.** Confirm the approval has not expired or been invalidated, then separately verify benchmark schema, annotation storage, review sample, and handoff controls. Approval for annotation does not authorize retrieval or experiments.

## 4. Current closure status

The Phase 12.2 report documents the following unresolved items:

- All nine records lack attributable checkout evidence and an explicit repository-specific approval decision.
- Eight scan candidates remain undispositioned: six for Flask, one for pytest, and one for Sphinx.
- History coverage is shallow across the recorded checkouts; Sphinx additionally has an unsupported `.dot` scan error.
- No complete personal/confidential-data review is recorded.
- File-level license/notice review is incomplete, with specific qualifications for mypy and Sphinx.
- Exact-SHA manifest/exclusion evidence and local handling-control evidence remain pending.
- Humanize additionally has an unresolved historical data-handling conflict and remains not approved for pilot annotation.

**Repositories approved in Phase 12.3:** None.

**Phase 13 benchmark annotation:** **LOCKED — NOT UNLOCKED.** No questions, labels, chunk IDs, source spans, or benchmark artifacts may be created until the applicable record reaches `READY FOR MANUAL ANNOTATION` after explicit approval.

**Retrieval/indexing/embedding/experiments:** **NOT AUTHORIZED.**

## 5. Closure record update rule

When evidence genuinely closes a gate, update only the affected repository record and this consolidated report after checking the packet digest, exact SHA, scope, reviewer, date, and decision authority. If evidence conflicts, expires, changes the eligible scope, or reveals a new finding, revert the gate to `BLOCKED`, stop downstream work, and document a versioned corpus decision where required.

Do not use this workflow to fill placeholders from assumptions, convert screening metadata into clearance, or mark a repository approved merely because all tests pass.

See [repository-approval-status-report.md](repository-approval-status-report.md), [repository-approval-workflow.md](repository-approval-workflow.md), [repository-approval-template.md](repository-approval-template.md), [privacy-clearance-report.md](privacy-clearance-report.md), and [privacy-remediation-plan.md](privacy-remediation-plan.md).
