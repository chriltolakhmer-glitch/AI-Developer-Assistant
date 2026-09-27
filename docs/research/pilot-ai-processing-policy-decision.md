# Phase 8.12 — Pilot AI Processing Policy Decision

**Decision date:** 2026-09-27
**Repository / snapshot:** `python-humanize/humanize` / `392aef707c0e74341ab4a51420984e9ea6b566c5`
**Privacy status:** **NOT APPROVED**
**Named reviewer (user-designated):** Alot, Project Owner / Thesis Researcher

## Decision

**AI-assisted analysis of pilot source code or source-derived research data through AI/hosted services is NOT ALLOWED.** This records the existing default in [ADR-008](../decisions/ADR-008-source-code-privacy.md) and the explicit Phase 8.12 handling constraint; it does not grant a new exception or constitute privacy approval.

No pilot source or source-derived material may be sent to a hosted LLM/chat, embedding API, cloud search/vector system, external annotation service, or other processor. Do not assume that an installed tool is local merely because it is launched from the researcher's computer; deployment, network egress, telemetry, retention, and service-side processing must be verified. This phase used documentation only and did not access pilot source.

## Conditions for any proposed exception

No exception is currently approved. Any future proposal must be prospective and must not start until all of the following are documented and approved:

1. Separate written research protocol/ADR specifying the exact data, purpose, and proposed system.
2. Privacy/data-protection, research-supervisor/institutional, repository-owner, and legal review as applicable.
3. Verified deployment/data-flow boundary, provider/subprocessor, data residency, retention, training use, telemetry, deletion, and incident terms.
4. Risk assessment and safeguards, including minimization, access restriction, encryption, and a deletion/retention plan.
5. Explicit signed approval by the authorized privacy approver before any source transfer.

If source processing is needed before an exception is approved, use a controlled local human review and approved local non-hosted tools only. Local AI processing is not separately approved by this record; verify the tool's isolation and obtain required approval first.

## Approval responsibility and prior handling question

- **Responsible researcher/reviewer:** Alot is user-designated to coordinate the local evidence review. This designation alone does not establish authority to approve an exception.
- **Approval responsibility:** the designated privacy approver/research supervisor or institutional privacy authority must decide and sign any exception; legal or repository-owner review is required where applicable.
- **Phase 8.10 processing:** the prior record states that pilot source was made available to an AI analysis agent. Service-side processing, residency, retention, and deletion remain unknown. This decision is not retroactive approval and does not resolve that event. Alot must assess and document the event under the applicable institutional/research process before privacy clearance.
- **Phase 8.12:** no pilot source was accessed or submitted to AI services during this documentation-only phase.

## Sign-off status

- Decision: **NOT ALLOWED** for hosted AI processing of pilot source/source-derived research data, per the current policy.
- Authorized approver identity/authority confirmed: **No**
- Signed exception approval: **None**
- Retrospective handling assessment for the Phase 8.10 event: **Pending**
- Overall pilot privacy approval: **NOT APPROVED**

This policy decision does not authorize benchmark questions, chunk annotation, indexing, embeddings, retrieval, evaluation, or experiments.
