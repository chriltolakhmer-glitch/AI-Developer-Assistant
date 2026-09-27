# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 19.3 — Repository Evidence Closure Plan

**Date:** 2026-09-27  
**Status:** Documentary closure plan; no Gate 1 decision is passed by this document.  
**Scope:** The eight non-Humanize candidates in the Phase 19.1 review, using the Phase 18.4 simplified Repository Approval Gate.  
**Boundary:** No repository is processed, cloned, or newly inspected; no source content or external approval packet was accessed in this phase. No questions, annotation, or retrieval changes. Humanize remains frozen.

## Purpose

Define the minimum evidence required to close Gate 1 and the safe method for updating each candidate's record. The current evidence baseline is the [Phase 19.2 repository approval review](repository-approval-review.md), [repository approval status](repository-approval-status.md), individual [repository approval records](repository-approvals/), and the consolidated [repository approval status report](repository-approval-status-report.md).

Phase 19.3 records what is already stated in those committed documents and what remains missing. It does not perform source processing or manufacture evidence. All eight candidates remain blocked; this plan does not approve any repository.

## Evidence required for each exact candidate

Gate 1 evidence must refer to one canonical repository identity, full commit SHA, language/file scope, and stated purpose. Keep detailed or sensitive evidence in the authorized controlled external location; committed status should include only non-sensitive summaries and safe references/digests.

1. **Identity and provenance**
   - Canonical repository ID, source origin, full pinned SHA, snapshot set and filter version.
   - Attributable evidence that any checkout used for a review is at that SHA, detached/read-only, and clean; safe reference or digest to the restricted evidence.
   - Confirmation that the proposed eligible scope is Python-only under the declared filter. Historical counts are screening baselines until exact-snapshot reconciliation is evidenced.
2. **License and notices**
   - Root license file/identifier and applicable terms for the intended thesis activity.
   - Human review of relevant file-level notices, attribution/retention obligations, exceptions and exclusions. Record reviewer, date, scope, evidence reference, and unresolved terms.
   - Root-license screening alone is not approval, legal advice, or blanket authorization to annotate or distribute.
3. **Privacy and sensitive-file review**
   - Scanner/tool version, configuration, exact snapshot/scope, date, output digest/reference, and disposition of every candidate finding. A candidate finding is not a confirmed secret or a presumed false positive until resolved.
   - History coverage (refs/range, shallow/full status, errors) and either adequate evidence or an attributable, authorized acceptance of a precisely documented limitation.
   - Designated human review of personal/confidential-data risks in the intended scope, with reviewer, method/categories, date, result and exclusions.
4. **Manifest and exclusions**
   - Exact-SHA eligible/excluded file scope, filter version, aggregate counts, exclusions/reasons and manifest digest/reconciliation. Keep detailed paths and per-file hashes restricted.
   - Any scope/count/stratum change must be raised as a versioned corpus decision before use; no silent substitutions.
5. **Handling and permitted activity**
   - Approved storage/access, local/offline and telemetry controls/limitations, backup, retention/deletion, and incident/stop procedure for the evidence and source scope.
   - Explicitly state which activity is permitted. Gate 1 approval for a narrowly bounded review/preparation activity does not automatically authorize annotation, inventory use for gold labels, retrieval evaluation, external transfer, or release.
6. **Attributable decision**
   - Named authorized decision-maker, role, date, exact repository/SHA/scope/purpose, evidence references/digests, status (`APPROVED`, `APPROVED WITH CONTROLS`, `REJECTED`, or `BLOCKED`), conditions, residual risks and stop triggers.
   - An author/researcher recommendation, blank approval field, project-owner status without supporting evidence, or thesis-level risk acceptance is not a repository-specific Gate 1 approval.

## Collection method

### Phase 19.3 work performed

- Review only the committed corpus-selection, repository-approval, privacy-status, and Phase 19 selection documents listed below.
- Do not clone/fetch repositories, open repository source, run scanners, generate manifests, inspect raw external reports, or access external evidence packets.
- Treat existing statements and screening metadata as documentary evidence only. Where a record has a placeholder, says `OPEN`, `IN PROGRESS`, `BLOCKED`, or lacks an attributable reviewer/decision, retain that status.

### Future Gate 1 evidence collection

For a later, separately authorized Gate 1 review, gather the minimum evidence from existing approved records and the controlled local evidence packet. If required evidence is not already available, the responsible reviewer must use the applicable approved process and handling controls before any new access/check. This plan itself does not authorize source review, scanning, cloning, or processing to obtain missing evidence. If the necessary review cannot be performed under current permissions, keep the candidate blocked and seek a proper decision or versioned exclusion; do not infer a pass.

Create/update one concise record per repository/SHA. Cross-check the record against the frozen corpus map, note evidence references and dates, and retain restricted details outside Git. Do not copy secrets, source excerpts, sensitive paths, raw scanner output, or private signatures into committed documentation.

## Review checklist

For each candidate, the responsible reviewer should confirm:

- [ ] Canonical repository ID and full SHA match the frozen corpus scope.
- [ ] Exact checkout/provenance evidence is attributable and matches the SHA, or the candidate remains blocked.
- [ ] Python/file scope and filter are stated; eligible/excluded manifest and aggregate counts reconcile.
- [ ] Root license and applicable file-level terms/notices are reviewed for the intended activity.
- [ ] Secret/credential scan provenance and every candidate finding are dispositioned.
- [ ] History coverage/errors are resolved or an authorized, attributable limitation is accepted.
- [ ] Human personal/confidential-data review is completed for the approved scope, with result and exclusions documented.
- [ ] Local handling, access, telemetry/offline, backup, retention/deletion and stop controls are evidenced.
- [ ] A named authorized approver records an explicit decision for this exact SHA and purpose.
- [ ] Conditions/exclusions are reflected in the permitted activity; no downstream permission is inferred.

## Pass/fail criteria

### Pass — Ready for approval

A candidate may be marked **Ready for approval** only when all required evidence above is complete, internally consistent, exact-SHA scoped, dated, attributable, and linked to a restricted evidence reference/digest; there are no unresolved findings that affect the proposed activity; and the remaining step is an explicit authorized decision. `Ready for approval` is not approval and does not authorize processing.

### Pass — Approved for a bounded activity

A candidate may be recorded **Approved for processing** only after the authorized approver signs an explicit, attributable decision for the exact snapshot, file/language scope and stated activity, with all mandatory Gate 1 evidence present and conditions/stop triggers recorded. This phase has no such decisions.

### Fail / hold / reject

- **Pending evidence:** one or more evidence items are absent or still being assembled; no decision can be inferred.
- **Blocked:** a mandatory check is incomplete, contradictory, failed, or has an unresolved finding/permission issue; no processing.
- **Rejected:** an authorized decision-maker explicitly rejects the exact snapshot/activity. Do not use `Rejected` merely because evidence is incomplete.
- Any changed SHA, filter, exclusions, finding status, purpose, or handling scope reopens the affected review.

## Current progress and remaining blockers

The [repository approval status](repository-approval-status.md) records zero approvals for the eight candidates. Individual records remain `OPEN` with pending placeholders; Phase 9 confirms root-license screening, language, size, and frozen SHAs, but not privacy or permission. Known findings: six Flask, one pytest, one Sphinx, plus the Sphinx `.dot` history-scan error. All eight lack completed personal/confidential-data review, exact checkout evidence in their records, final notice/terms review, handling evidence, and attributable Gate 1 approval.

No candidate is Ready for approval because the mandatory evidence is incomplete. All eight remain **Blocked**; several sub-items are also `IN PROGRESS` or pending. Humanize is outside this queue, frozen for pilot use only, and not cleared for new expansion work.

## Existing references

- [Phase 18.4 simplified research workflow](benchmark-research-workflow-final.md)
- [Phase 19.1 selection review](candidate-selection-review.md) and [candidate review status](candidate-review-status.md)
- [Phase 19.2 approval review](repository-approval-review.md) and [status matrix](repository-approval-status.md)
- [Phase 9 corpus selection](corpus-final-selection.md) and [repository corpus screening](repository-corpus-final.md)
- [Repository approval workflow](repository-approval-workflow.md), [approval template](repository-approval-template.md), [evidence closure workflow](repository-approval-evidence-closure.md), and [privacy clearance report](privacy-clearance-report.md)
- [Repository approval status report](repository-approval-status-report.md), [thesis scope risk acceptance](repository-approval-thesis-risk-acceptance.md), and [individual approval records](repository-approvals/)
- [Humanize pilot status](benchmark-annotation-pilot-status.md) and [Phase 16 closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md)
