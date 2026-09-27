# Phase 8.11 — Pilot Privacy Remediation Plan

**Plan date:** 2026-09-27
**Phase 8.13 evidence check date:** 2026-09-27
**Repository:** `python-humanize/humanize`
**Pinned snapshot:** `392aef707c0e74341ab4a51420984e9ea6b566c5`
**Thesis baseline:** `fec3fbfdc92fc4f11bc21aa41e5b0c5c32bcbbb6`
**Privacy status:** **NOT APPROVED — annotation remains blocked**
**Designated reviewer (user-provided):** Alot, Project Owner / Thesis Researcher

## Scope and safety boundary

This plan closes evidence gaps only. Phases 8.11–8.13 have not reopened or transmitted pilot source code, created benchmark questions, annotated chunks, generated a chunk inventory, or run retrieval/evaluation experiments. Phases 8.12 and 8.13 did not use pilot source with AI services. Completed review forms must be kept in an approved controlled local research-data area; commit only blank templates, policy-level records, and non-sensitive aggregate status. Do not place source excerpts, candidate values, line-level personal data, or per-file inventory in this Git repository.

Under [ADR-008](../decisions/ADR-008-source-code-privacy.md), hosted LLM/chat and other services that receive source or source-derived research data are **not allowed** for the primary study. Phase 8.10 recorded that source content was made available to an AI analysis agent, while service-side handling and data residency are unknown. Treat this as a potential policy deviation requiring assessment; do not send additional pilot source to AI or hosted services.

## Current blockers and remediation register

| ID | Blocker / verified state | Remediation action | Responsible person | Required closure evidence | Status |
|---|---|---|---|---|---|
| H-1 | The pilot checkout is shallow; one commit is reachable. The saved history scan has no recorded command, configuration, refs/range, or complete-history coverage. | In the controlled local environment, obtain and scan the available history with an approved secret scanner and record exact refs/range and configuration. If full history cannot be obtained/scanned, document the coverage boundary and residual risk and obtain explicit acceptance from the authorized privacy approver. | Alot; authorized privacy approver for any scope limitation | Scanner/version, command/configuration, snapshot/ref scope, output digest, candidate dispositions, and either full-history evidence or signed acceptance of the limitation | **OPEN** |
| P-1 | The prior preliminary AI screen flagged three formatted-number candidates in one eligible file. They have not been adjudicated by the named human reviewer. | Alot reviews each candidate locally against its surrounding context, records the file and line/location in the restricted form, selects a decision, and gives a concise justification. Keep the completed form outside Git. | Alot | Completed [candidate data disposition form](templates/privacy/candidate-data-disposition-template.md) with date, reviewer, decisions, justifications, and evidence reference; no unresolved candidate | **OPEN** |
| N-1 | Preliminary filename/header inventory found root `LICENCE` (MIT) and no conventional separate notice/attribution filename or common license header marker in the eligible Python scope. This is not a complete human/legal terms review. | Alot checks `LICENSE`/`LICENCE`, `NOTICE`, `COPYRIGHT`, and any authors/contributors/attribution material, then reviews applicable notices for the eligible scope. Record obligations, exclusions, attribution, and retention conditions. Obtain legal or repository-owner review if required. | Alot; legal/repository owner reviewer if required | Completed [notice/license review form](templates/privacy/notice-license-review-template.md), evidence references, and resolution of every applicable condition | **OPEN** |
| C-1 | The checked checkout and pilot-evidence directories inherit `BUILTIN\Users` read/execute and create/append rights; reviewer-only access is not established. Backup, retention, deletion, and encryption controls are not attested. | Move or retain pilot materials only in the institution-approved local research-data location. Restrict access to named authorized reviewers, verify effective ACLs, document encryption and backups, define retention/deletion, and record whether source or derivatives leave the local boundary. Do not change machine-wide permissions without an authorized administrator. | Alot; authorized workstation administrator for ACL changes | Completed [handling controls form](templates/privacy/handling-controls-template.md), before/after access evidence, approved storage location, retention/deletion procedure, and responsible person's attestation | **OPEN** |
| A-1 | Phase 8.10 used an AI analysis agent on eligible source despite the local-only research policy. Service-side processing, residency, retention, and deletion are not verified. Phase 8.12 records hosted AI source analysis as not allowed, but does not resolve this prior event. | Do not further submit pilot source or source-derived details to AI/hosted services. Alot and the institutional privacy authority/research supervisor assess the prior event, determine what service/provider records are available, and document its policy disposition. Any future exception must be prospective and separately approved before transfer. | Alot; institutional privacy authority/research supervisor for policy disposition | [Phase 8.12 AI policy decision](pilot-ai-processing-policy-decision.md), applicable provider/data-handling evidence if available, and documented retrospective event/incident disposition | **OPEN — prior event assessment** |
| D-1 | Reviewer name/role are recorded, but no completed review package or attributable authorized approval is present. | After H-1, P-1, N-1, C-1, and A-1 are resolved, the authorized privacy approver reviews the complete evidence and issues a dated, explicit decision for this exact snapshot. | Alot as designated reviewer; authorized privacy approver (identity/authority to be confirmed) | Signed/attributable decision naming reviewer/approver, role, date, snapshot, evidence references/digests, exclusions, residual risks, and `APPROVED` or `REJECTED` outcome | **OPEN — final gate** |

## Phase 8.12 documentation check-in

This is a status update, not closure evidence or a human attestation:

- **Candidate dispositions:** no candidate-level form was completed. The prior aggregate record identifies three formatted-number candidates but does not include approved file/line coordinates or human decisions. Alot must locate and adjudicate them on the controlled local system; no candidate values or locations belong in Git or this chat.
- **Notice/license review:** the reusable form remains blank. The available Phase 8.10 filename/header inventory is preliminary; Alot still needs to verify the applicable notices, attribution, retention obligations, and any exclusions and attest to the result.
- **Handling controls:** the reusable form remains blank. Existing observations show `BUILTIN\Users` access on the identified folders; no permissions were changed and no custody, encryption, backup, retention, deletion, or egress attestation was received.
- **AI policy:** [the Phase 8.12 policy decision](pilot-ai-processing-policy-decision.md) records hosted AI processing of pilot source/source-derived data as **NOT ALLOWED**, following ADR-008 and the current instruction. It does not resolve the prior Phase 8.10 AI-agent handling event, whose service-side processing remains unknown.
- **Final approval:** no human-signed review package or authorized approval was provided. Overall status remains **NOT APPROVED**.

## Phase 8.13 evidence receipt

The project owner stated on 2026-09-27 that the human reviews were completed locally and identified the previously used Phase 8 pilot evidence folder. A filename/metadata-only listing of that folder found no completed candidate disposition, notice/license, handling-controls, or prior-AI-processing assessment form; no file contents or pilot source were opened. The folder ACL still inherits access for `BUILTIN\Users` with read/execute and create/append rights. Consequently, the stated completion is recorded as **reported but not evidenced here**; no remediation row is closed. Alot must provide the completed attestations from an appropriately restricted location, without sending source or candidate details through chat.

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
- [Phase 8.12 AI processing policy decision](pilot-ai-processing-policy-decision.md)
- [ADR-008: source-code processing and privacy policy](../decisions/ADR-008-source-code-privacy.md)
- [Candidate data disposition form](templates/privacy/candidate-data-disposition-template.md)
- [Notice/license review form](templates/privacy/notice-license-review-template.md)
- [Handling controls form](templates/privacy/handling-controls-template.md)
- [AI processing policy decision form](templates/privacy/ai-processing-policy-decision-template.md)
