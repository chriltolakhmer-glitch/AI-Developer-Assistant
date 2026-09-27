# Phase 8.11 — Pilot Privacy Remediation Plan

**Plan date:** 2026-09-27
**Phase 8.14 evidence review date:** 2026-09-27
**Repository:** `python-humanize/humanize`
**Pinned snapshot:** `392aef707c0e74341ab4a51420984e9ea6b566c5`
**Thesis baseline:** `d2184d5e02528d7ed50ba076f60e7983f5f777a8`
**Privacy status:** **NOT APPROVED — annotation remains blocked**
**Designated reviewer (user-provided):** Alot, Project Owner / Thesis Researcher

## Scope and safety boundary

This plan closes evidence gaps only. Phases 8.11–8.14 have not reopened or transmitted pilot source code, created benchmark questions, annotated chunks, generated a chunk inventory, or run retrieval/evaluation experiments. Phases 8.12–8.14 did not use pilot source with AI services. Completed review forms must be kept in an approved controlled local research-data area; commit only blank templates, policy-level records, and non-sensitive aggregate status. Do not place source excerpts, candidate values, line-level personal data, or per-file inventory in this Git repository.

Under [ADR-008](../decisions/ADR-008-source-code-privacy.md), hosted LLM/chat and other services that receive source or source-derived research data are **not allowed** for the primary study. Phase 8.10 recorded that source content was made available to an AI analysis agent, while service-side handling and data residency are unknown. Treat this as a potential policy deviation requiring assessment; do not send additional pilot source to AI or hosted services.

## Current blockers and remediation register

| ID | Blocker / verified state | Remediation action | Responsible person | Required closure evidence | Status |
|---|---|---|---|---|---|
| H-1 | The pilot checkout is shallow; one commit is reachable. The saved history scan has no recorded command, configuration, refs/range, or complete-history coverage. | In the controlled local environment, obtain and scan the available history with an approved secret scanner and record exact refs/range and configuration. If full history cannot be obtained/scanned, document the coverage boundary and residual risk and obtain explicit acceptance from the authorized privacy approver. | Alot; authorized privacy approver for any scope limitation | Scanner/version, command/configuration, snapshot/ref scope, output digest, candidate dispositions, and either full-history evidence or signed acceptance of the limitation | **OPEN** |
| P-1 | The prior preliminary AI screen flagged three formatted-number candidates in one eligible file. The 2026-09-27 reviewer narrative reports candidate review complete with exclusions, but supplies no candidate count/details, per-item classifications/dispositions, exact snapshot/manifest binding, or controlled evidence reference. | Alot reconciles each prior candidate locally against the attested disposition, records the result in the restricted form, and confirms exclusions against the approved manifest. Do not put candidate values or locations in Git/chat. | Alot | Completed, attributable [candidate data disposition form](templates/privacy/candidate-data-disposition-template.md) bound to the exact SHA and manifest, with reviewer/date, per-item decisions/justifications and controlled evidence reference; no unresolved candidate | **OPEN — attested in narrative, supporting detail unverified** |
| N-1 | The reviewer narrative reports checking “LICENSE”, NOTICE, COPYRIGHT, and attribution, but does not name the exact snapshot, applicable license, findings, attribution conditions, or evidence reference. Prior tree evidence identifies root `LICENCE` (MIT), so the filename should be reconciled. | Alot confirms the actual pinned-tree `LICENCE` and all applicable notice/attribution files were reviewed, records terms and conditions, and resolves any discrepancy between the narrative's `LICENSE` label and actual file. Obtain legal or repository-owner review if required. | Alot; legal/repository owner reviewer if required | Attributable [notice/license review form](templates/privacy/notice-license-review-template.md) bound to exact SHA/scope, checked items/results, MIT notice-preservation obligations, exclusions, reviewer/date, and controlled evidence reference | **OPEN — review completion reported, scope/results unverified** |
| C-1 | The reviewer narrative attests local storage and owner-only access. Prior measured ACLs on the checkout/evidence folders allow `BUILTIN\Users` read/execute and create/append; the narrative supplies no updated ACL evidence. Backup, retention, deletion, and encryption remain undocumented. | Alot and an authorized workstation administrator reconcile the owner-only assertion with effective ACLs; move/restrict data as needed. Document the storage identity, access, egress, encryption, backups, retention/deletion, and source-derived data handling. | Alot; authorized workstation administrator for ACL changes | Attributable [handling controls form](templates/privacy/handling-controls-template.md), effective before/after ACL evidence, storage/owner, lifecycle controls and signed/date attestation | **OPEN — attested claim conflicts with measured ACLs** |
| A-1 | The reviewer narrative says earlier AI activity was limited to architecture/design/planning. This conflicts with the Phase 8.10 record that eligible source was provided to an AI analysis agent. Provider/service, data flow, residency, retention, deletion, and institutional disposition remain unknown. | Do not further submit pilot source/source-derived details to AI/hosted services. Alot and the institutional privacy authority/research supervisor reconcile the Phase 8.10 source-processing record with the new narrative, identify service records if available, and document the event's disposition. Any future exception must be prospective and separately approved. | Alot; institutional privacy authority/research supervisor for policy disposition | Completed [AI processing policy decision](pilot-ai-processing-policy-decision.md) or attributable addendum addressing the specific prior event, provider/data flow and unknowns, retention/deletion, policy/incident disposition, reviewer/date, and approver | **OPEN — narrative conflicts with recorded event** |
| D-1 | Reviewer name/role are recorded, but no completed review package or attributable authorized approval is present. | After H-1, P-1, N-1, C-1, and A-1 are resolved, the authorized privacy approver reviews the complete evidence and issues a dated, explicit decision for this exact snapshot. | Alot as designated reviewer; authorized privacy approver (identity/authority to be confirmed) | Signed/attributable decision naming reviewer/approver, role, date, snapshot, evidence references/digests, exclusions, residual risks, and `APPROVED` or `REJECTED` outcome | **OPEN — final gate** |

## Phase 8.12 documentation check-in

This is a status update, not closure evidence or a human attestation:

- **Candidate dispositions:** no candidate-level form was completed. The prior aggregate record identifies three formatted-number candidates but does not include approved file/line coordinates or human decisions. Alot must locate and adjudicate them on the controlled local system; no candidate values or locations belong in Git or this chat.
- **Notice/license review:** the reusable form remains blank. The available Phase 8.10 filename/header inventory is preliminary; Alot still needs to verify the applicable notices, attribution, retention obligations, and any exclusions and attest to the result.
- **Handling controls:** the reusable form remains blank. Existing observations show `BUILTIN\Users` access on the identified folders; no permissions were changed and no custody, encryption, backup, retention, deletion, or egress attestation was received.
- **AI policy:** [the Phase 8.12 policy decision](pilot-ai-processing-policy-decision.md) records hosted AI processing of pilot source/source-derived data as **NOT ALLOWED**, following ADR-008 and the current instruction. It does not resolve the prior Phase 8.10 AI-agent handling event, whose service-side processing remains unknown.
- **Final approval:** no human-signed review package or authorized approval was provided. Overall status remains **NOT APPROVED**.

## Phase 8.14 evidence receipt

On 2026-09-27, Alot provided a narrative stating candidate review, license/notice review, handling controls, and prior-AI assessment were complete, and requesting “APPROVED WITH CONTROLS.” This is recorded as a reviewer attestation in the conversation, but not as the completed per-review forms or linked controlled evidence. Its candidate dispositions lack per-item details and snapshot/manifest binding; the notice statement names `LICENSE` while prior evidence found root `LICENCE`; its owner-only access claim conflicts with measured broad ACLs; and its description of prior AI activity conflicts with the Phase 8.10 source-analysis record. The narrative does not establish history scan scope or authorized acceptance of the shallow-history limit.

A filename/metadata-only listing of the previously identified Phase 8 pilot folder still found no completed review forms. File contents and pilot source were not opened for this Phase 8.14 review, and no repository data was sent to AI services. Treat the supplied completion statements as **reported, not reconciled/verified**. No remediation gate is closed solely on this narrative; Alot must provide or attest to the scoped details in the controlled local evidence package and resolve the specific discrepancies above.

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
