# Thesis Privacy Review

**Project:** AI Developer Assistant Master's Thesis
**Reviewer:** Alot — Project Owner / Thesis Researcher
**Review date:** 2026-09-27
**Decision:** **APPROVED WITH CONTROLS**

## Scope

This is a concise, thesis-level handling decision based on the reviewer statement supplied on 2026-09-27. The research uses publicly available open-source repositories for source analysis, AST parsing, chunk generation, embeddings, and retrieval evaluation. This review is not legal advice, independent certification, or proof that every repository, file, snapshot, or control has been separately audited.

The associated pilot is `python-humanize/humanize`, snapshot `392aef707c0e74341ab4a51420984e9ea6b566c5`. The review statement does not itself identify that SHA, so the attestation-to-snapshot binding is a limitation.

## Reviewer-reported review

The reviewer reports that repository/license conditions, credentials, API keys, personal information, and unrelated private files were considered; that source repositories and embeddings are kept local; and that sensitive or unnecessary files are to be excluded from indexing and benchmark data. The reviewer also states that source is not uploaded to external AI services and that required license attribution will be maintained.

These statements are recorded as the project owner's attestation. They were not independently re-performed or verified in this documentation update.

## Controls for continued research

1. Use public repositories only and pin each repository to its recorded commit.
2. Keep source checkouts and derived source data outside the thesis Git repository, in local storage with access limited to the project owner.
3. Process source and generate embeddings locally. Do not upload source, chunks, embeddings, benchmark content, or source-derived details to external AI services.
4. Review and exclude sensitive or unnecessary files before indexing or evaluation. Do not include repository contents in thesis publications.
5. Preserve applicable copyright notices and provide license attribution where required.
6. Keep benchmark metadata to the minimum needed and store experiment artifacts separately from source checkouts.

This approval is conditional: if local-only processing or the other controls cannot be maintained, stop pilot data processing until the issue is corrected and documented.

## Known limitations and scope boundary

- Prior records document that 13 eligible pilot source files were made available to an AI analysis agent in Phase 8.10. That conflicts with the supplied statement that previous AI assistance was limited to architecture, documentation, and planning. This review does not resolve or retroactively approve that prior event. Do not submit further repository source to AI services; any retrospective service/data-handling assessment remains outstanding.
- Prior local ACL inspection found `BUILTIN\Users` access on the checkout and pilot-evidence folders. No updated permissions evidence was supplied with this review. The project owner must ensure and verify owner-limited access before further pilot source processing.
- The pilot checkout is shallow and full upstream history review was not established in the prior records.
- The review statement does not provide candidate-by-candidate dispositions, a detailed exclusion list, or an exact commit-bound review artifact. Retain sensitive details locally; this document does not invent those records.

The decision approves the thesis-level privacy rules **with the controls above**; it is not a finding that historical source handling or every pilot-specific prerequisite has been verified. Any pilot processing must satisfy these controls and applicable research gates. External source upload and source redistribution/publication are not approved.
