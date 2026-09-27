# Pilot Privacy Review Decision

**Project:** AI Developer Assistant Master's Thesis
**Reviewer:** Alot — Project Owner / Thesis Researcher
**Decision date:** 2026-09-27
**Repository:** `python-humanize/humanize`
**Snapshot under discussion:** `392aef707c0e74341ab4a51420984e9ea6b566c5`
**Decision:** **APPROVED WITH CONTROLS**

## Decision scope

This decision adopts the thesis-level privacy rules in [privacy-review.md](privacy-review.md), based on Alot's supplied reviewer statement. It approves continued thesis work **subject to the controls below**. It is not legal advice, independent certification, or verification that every pilot-specific control or historical data-handling event is resolved.

The supplied review statement does not identify the pilot SHA. The SHA above is the previously selected pilot snapshot, not a claim that the reviewer document independently binds its findings to that exact commit.

## Controls

- Use public, commit-pinned repositories only.
- Keep source repositories and source-derived research data outside the thesis Git repository, in local storage restricted to the project owner.
- Perform source processing and embedding locally; do not upload source, chunks, embeddings, benchmark content, or source-derived details to external AI services.
- Exclude sensitive or unnecessary files before indexing or evaluation; do not publish repository contents.
- Preserve applicable license notices and maintain required attribution.
- Keep benchmark metadata to the minimum needed and store experiment artifacts separately from source repositories.

If a control cannot be met, pause pilot data processing until it is corrected and documented.

## Evidence and limitations

Alot's supplied review reports completion of license/usage and sensitive-data checks and attests to local-only handling, restricted access, exclusions, and attribution. This is recorded as the project owner's attestation; this documentation update did not access pilot source or independently re-perform those checks.

Prior project records state that 13 eligible pilot source files were made available to an AI analysis agent in Phase 8.10. That conflicts with the supplied statement that earlier AI use was limited to architecture discussion, documentation, and planning. The present decision does **not** retroactively approve or resolve that prior event. No further pilot source may be submitted to AI or hosted services; retrospective service/data-handling assessment remains outstanding.

Prior local ACL inspection also found `BUILTIN\Users` access on the checkout and evidence folders; no updated permissions evidence was supplied. Owner-only access must be established and verified before pilot source processing. Full upstream history review was not established because the checkout was shallow. The supplied statement does not include candidate-level disposition details or bind the review to the stated SHA.

Accordingly, **APPROVED WITH CONTROLS is the thesis-level policy decision, not a claim that prior external processing, ACLs, full-history coverage, or every pilot-specific review detail has been independently verified.**

## Next activity

Continue thesis work only under the stated controls. Before processing this pilot snapshot, verify owner-restricted local storage, apply sensitive-file exclusions, preserve the applicable MIT notice/attribution, and document the disposition of the prior AI-assisted source review and the history-scope limitation. No external AI/source upload is allowed. This approval does not authorize source redistribution or publication.

See [thesis privacy review](privacy-review.md) and [ADR-008](../decisions/ADR-008-source-code-privacy.md).
