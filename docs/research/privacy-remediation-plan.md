# Phase 8.11 — Pilot Privacy Remediation Plan

**Plan date:** 2026-09-27
**Repository:** `python-humanize/humanize`
**Pinned snapshot:** `392aef707c0e74341ab4a51420984e9ea6b566c5`
**Thesis baseline:** `6d9bc34c88b227194730e0c0d6f34ad9b7164e3d`
**Privacy status:** **NOT APPROVED — annotation remains blocked**
**Designated reviewer (user-provided):** Alot, Project Owner / Thesis Researcher

## Scope and safety boundary

This plan closes evidence gaps only. Phase 8.11 has not reopened or transmitted pilot source code, created benchmark questions, annotated chunks, generated a chunk inventory, or run retrieval/evaluation experiments. Completed review forms must be kept in the approved controlled local research-data area; commit only this blank template, protocol-level plan, and non-sensitive aggregate status. Do not place source excerpts, candidate values, line-level personal data, or per-file inventory in this Git repository.

Under [ADR-008](../decisions/ADR-008-source-code-privacy.md), hosted LLM/chat and other services that receive source or source-derived research data are **not allowed** for the primary study. Phase 8.10 recorded that source content was made available to an AI analysis agent, while service-side handling and data residency are unknown. Treat this as a potential policy deviation requiring assessment; do not send additional pilot source to AI or hosted services.

## Current blockers and remediation register

| ID | Blocker / verified state | Remediation action | Responsible person | Required closure evidence | Status |
|---|---|---|---|---|---|
| H-1 | The pilot checkout is shallow; one commit is reachable. The saved history scan has no recorded command, configuration, refs/range, or complete-history coverage. | In the controlled local environment, obtain and scan the available history with an approved secret scanner and record exact refs/range and configuration. If full history cannot be obtained/scanned, document the coverage boundary and residual risk and obtain explicit acceptance from the authorized privacy approver. | Alot; authorized privacy approver for any scope limitation | Scanner/version, command/configuration, snapshot/ref scope, output digest, candidate dispositions, and either full-history evidence or signed acceptance of the limitation | **OPEN** |
| P-1 | The prior preliminary AI screen flagged three formatted-number candidates in one eligible file. They have not been adjudicated by the named human reviewer. | Alot reviews each candidate locally against its surrounding context, records the file and line/location in the restricted form, selects a decision, and gives a concise justification. Keep the completed form outside Git. | Alot | Completed [candidate data disposition form](templates/privacy/candidate-data-disposition-template.md) with date, reviewer, decisions, justifications, and evidence reference; no unresolved candidate | **OPEN** |
| N-1 | Preliminary filename/header inventory found root `LICENCE` (MIT) and no conventional separate notice/attribution filename or common license header marker in the eligible Python scope. This is not a complete human/legal terms review. | Alot checks `LICENSE`/`LICENCE`, `NOTICE`, `COPYRIGHT`, and any authors/contributors/attribution material, then reviews applicable notices for the eligible scope. Record obligations, exclusions, attribution, and retention conditions. Obtain legal or repository-owner review if required. | Alot; legal/repository owner reviewer if required | Completed [notice/license review form](templates/privacy/notice-license-review-template.md), evidence references, and resolution of every applicable condition | **OPEN** |
| C-1 | The checked checkout and pilot-evidence directories inherit `BUILTIN\Users` read/execute and create/append rights; reviewer-only access is not established. Backup, retention, deletion, and encryption controls are not attested. | Move or retain pilot materials only in the institution-approved local research-data location. Restrict access to named authorized reviewers, verify effective ACLs, document encryption and backups, define retention/deletion, and record whether source or derivatives leave the local boundary. Do not change machine-wide permissions without an authorized administrator. | Alot; authorized workstation administrator for ACL changes | Completed [handling controls form](templates/privacy/handling-controls-template.md), before/after access evidence, approved storage location, retention/deletion procedure, and responsible person's attestation | **OPEN** |
| A-1 | Phase 8.10 used an AI analysis agent on eligible source despite the local-only research policy. Service-side processing, residency, retention, and deletion are not verified. | Do not further submit pilot source or source-derived details to AI/hosted services. Alot and the institutional privacy authority/research supervisor assess this event, determine what service/provider records are available, and document the policy disposition. Any exception must be prospective and separately approved before any transfer. | Alot; institutional privacy authority/research supervisor for policy disposition | Completed [AI processing policy decision form](templates/privacy/ai-processing-policy-decision-template.md), applicable provider/data-handling evidence, and documented incident/exception disposition | **OPEN** |
| D-1 | Reviewer name/role are recorded, but no completed review package or attributable authorized approval is present. | After H-1, P-1, N-1, C-1, and A-1 are resolved, the authorized privacy approver reviews the complete evidence and issues a dated, explicit decision for this exact snapshot. | Alot as designated reviewer; authorized privacy approver (identity/authority to be confirmed) | Signed/attributable decision naming reviewer/approver, role, date, snapshot, evidence references/digests, exclusions, residual risks, and `APPROVED` or `REJECTED` outcome | **OPEN — final gate** |

## Required evidence package

Keep completed and detailed records in the controlled local research-data area, not in Git:

1. History scan provenance and candidate finding dispositions, or documented history limitation with authorized risk acceptance.
2. Human candidate-data review and disposition for every flagged item.
3. Human notice/license/attribution review for the approved scope.
4. Handling controls, effective access restrictions, external-processing determination, backup/retention/deletion plan, and AI-service policy disposition.
5. Manifest identity and scope confirmation. The currently recorded external manifest SHA-256 is `a9f35063535978fd5fe099506c2152922dd42bb0bf95bc56df10de8396a32868`; if it changes, retain the superseding digest and reconciliation externally.
6. Authorized, date-attributed final decision. Reviewer identity alone, empty automated scan output, or this remediation plan is not approval.

Commit only blank forms and aggregate, non-sensitive closure state. Do not add the completed candidate file/line table, raw scan output, source material, or per-file manifest to Git.

## Exit criteria and next allowed activity

Privacy approval remains **NOT APPROVED** until every applicable blocker is closed with evidence and an authorized approver records an explicit decision. If any result is ambiguous, adverse, or unavailable, keep the pilot blocked and document exclusion or protocol change through the authorized research process.

Until then, only local privacy remediation and documentation are allowed. Do not create benchmark questions, annotate chunks, create or consume chunk inventories, run indexing/embedding/retrieval/evaluation experiments, or use source code with AI services.

## Related records and forms

- [Final pilot privacy approval record](pilot-privacy-approval-final.md)
- [ADR-008: source-code processing and privacy policy](../decisions/ADR-008-source-code-privacy.md)
- [Candidate data disposition form](templates/privacy/candidate-data-disposition-template.md)
- [Notice/license review form](templates/privacy/notice-license-review-template.md)
- [Handling controls form](templates/privacy/handling-controls-template.md)
- [AI processing policy decision form](templates/privacy/ai-processing-policy-decision-template.md)
