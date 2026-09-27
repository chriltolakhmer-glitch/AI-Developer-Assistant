# Phase 11 — Repository Approval Record Template

**Purpose:** One review record per exact repository snapshot. This is a blank template, not an approval, privacy clearance, legal opinion, or authorization to inspect source or annotate the benchmark. Do not fill it with invented, assumed, or copied approval evidence.

**Handling:** Keep completed records, scan outputs, detailed findings, file-level manifests, source-derived evidence, and signatures in the approved, access-controlled local research-data area outside the thesis Git repository. The committed copy remains blank and non-sensitive. Record only safe evidence references or digests here; never commit credentials, raw findings, source excerpts, sensitive paths, or private reviewer material.

---

## A. Repository and snapshot identity

| Field | Value |
|---|---|
| Repository name | `[canonical owner/repository]` |
| Repository URL | `[canonical HTTPS URL]` |
| Pinned commit SHA | `[full 40-character commit SHA; no branch/tag]` |
| Snapshot set / protocol version | `[for example, corpus-snapshot-v1; record any approved revision]` |
| Review record ID | `[unique, non-sensitive ID]` |
| Review date (UTC) | `[YYYY-MM-DD]` |
| Checkout identity evidence | `[external evidence reference/digest; exact SHA and clean/read-only state]` |

## B. License, language, and size scope

| Field | Value |
|---|---|
| Root license identifier | `[identifier as evidenced; do not infer from repository metadata]` |
| License file / evidence | `[file name and external review reference; retain applicable notices]` |
| Per-file notices / terms review | `[NOT STARTED / IN PROGRESS / PASS / BLOCKED; reviewer and evidence reference]` |
| GitHub language metadata | `[languages as recorded; informational only]` |
| Approved study language scope | `[Python only, or explicitly approved scope]` |
| File-filter / manifest version | `[for example, phase4.5-python-v1]` |
| Size category | `[Small / Medium / Large under the approved eligible-Python-LOC thresholds]` |
| Eligible Python files / LOC | `[verified aggregate count and evidence reference; never include the detailed file manifest here]` |
| Stratum reconciliation | `[PASS / CHANGE REQUIRED / NOT REVIEWED; summarize non-sensitive outcome]` |

Root license evidence is a screening input, not blanket permission or legal advice. Record any attribution, retention, file exclusion, or additional review conditions. Changes to repository membership, SHA, scope, filter, counts, or stratum require an explicit versioned corpus decision before use.

## C. Repository-specific privacy and handling review

For each review, record the state, reviewer/role, review date, method/scope, safe evidence reference or digest, exclusions, and unresolved risk. Keep detailed findings outside Git.

| Review gate | Status (`NOT STARTED` / `IN PROGRESS` / `PASS` / `BLOCKED`) | Reviewer, date, scope and safe evidence reference | Exclusions / residual risk |
|---|---|---|---|
| Secret / credential scan of exact pinned snapshot | `[status]` | `[tool/version, configuration, exact SHA, date, external report reference/digest, disposition status]` | `[non-sensitive summary; keep finding details external]` |
| Available Git-history scan and coverage | `[status]` | `[refs/range, shallow/full-history limitation, command/config reference, date, external report reference/digest]` | `[uncovered history, scan errors, accepted limitation or remediation]` |
| Candidate finding disposition | `[status]` | `[all candidates accounted for? safe external record reference]` | `[unresolved count/status; do not disclose values]` |
| Personal / confidential-data review | `[status]` | `[designated human reviewer, reviewed scope/categories, method, date, external record reference]` | `[exclusions and residual risk; do not infer absence from secret scan]` |
| License terms / file-level notices | `[status]` | `[reviewer, scope, attribution/retention assessment, date, external record reference]` | `[excluded files or unresolved terms]` |
| Eligible-file manifest and exclusions | `[status]` | `[manifest schema/filter, exact SHA, aggregate reconciliation, digest and external location]` | `[count deltas or exclusions needing decision]` |
| Local handling controls | `[status]` | `[approved storage location alias, access verification, local/offline and telemetry controls, backup/retention/deletion evidence]` | `[open controls / limitations]` |
| Historical exposure or other incident review, if applicable | `[status / NOT APPLICABLE with rationale]` | `[external assessment reference; do not reproduce source or service details here]` | `[open follow-up / residual risk]` |

### Source handling rules for this snapshot

Confirm each rule or record an approved, explicit exception in the external decision record. An exception does not override the requirement for attributable authorization.

- [ ] Checkout is local, read-only, outside the thesis Git repository, and pinned to the full SHA above.
- [ ] Process only the approved eligible language/files and reviewed manifest; do not silently expand scope.
- [ ] Keep source, chunks, inventories, source-derived questions/labels, spans, detailed audit output, vectors, indexes, and working records in the approved access-controlled local research-data area outside Git.
- [ ] Do not send source or source-derived data to hosted AI/LLM, embedding, notebook, search/vector, telemetry, cloud storage, or external labeling services.
- [ ] Disable optional telemetry where supported; record limitations rather than claiming unverified controls.
- [ ] Preserve applicable license/copyright notices and comply with approved attribution, retention, and exclusion conditions.
- [ ] Apply the approved access, encrypted backup, retention, and deletion rules; limit plaintext copies.
- [ ] Stop processing and notify the designated reviewer if new sensitive material, an unresolved finding, a snapshot mismatch, or a handling-control failure is discovered.

## D. Review outcome and approval decision

**Overall review status:** `[NOT STARTED / IN REVIEW / BLOCKED / APPROVED WITH CONTROLS / REJECTED]`

**Authorized decision:** `[APPROVED / APPROVED WITH CONTROLS / REJECTED — select one; blank is not approval]`

**Approved purposes and exact scope:** `[for example: manual benchmark question/evidence annotation for this exact SHA and approved Python manifest only]`

**Explicitly excluded activities:** `[list, or refer to governing policy; do not treat this record as approval for indexing, embedding, retrieval, publication, or experiments unless separately approved]`

**Conditions, exclusions, and stop triggers:** `[specific non-sensitive terms; attach detailed restricted evidence externally]`

**Residual risks and accepted limitations:** `[include history-scan scope limitations and any rejected/unresolved condition; no implicit acceptance]`

**Approval evidence reference / digest:** `[controlled external record identifier/digest; no raw finding content]`

| Decision authority | Name / role | Decision | Date (UTC) | Signature / attestation reference |
|---|---|---|---|---|
| Repository/privacy approver | `[name and authorized role]` | `[APPROVED / APPROVED WITH CONTROLS / REJECTED]` | `[YYYY-MM-DD]` | `[external attestation reference]` |
| License/terms reviewer (if separate/required) | `[name and role or NOT REQUIRED with rationale]` | `[decision]` | `[YYYY-MM-DD]` | `[external attestation reference]` |

### Scope and expiry of approval

- Approval applies only to the repository identity, exact commit SHA, language/file scope, manifest/filter version, and purposes written above.
- Approval does not automatically extend to another commit, repository, file set, processing purpose, external service, or publication/distribution.
- Any changed finding, source scope, handling control, or risk invalidates or suspends the relevant permission until reviewed and re-approved.
- **Benchmark annotation authorization:** `[NOT AUTHORIZED / AUTHORIZED WITHIN THE SCOPE ABOVE]`. Mark authorized only after every blocking gate is resolved and the approver explicitly grants that purpose.
- **Retrieval/indexing/embedding/experiments:** `[NOT AUTHORIZED unless a separate explicit decision records otherwise]`.

## E. Annotation handoff checklist — only after approval

This section records readiness to hand the exact cleared snapshot to benchmark annotation. It does not create any benchmark case.

- [ ] Approval is attributable, dated, explicit, and covers manual annotation for this exact snapshot and scope.
- [ ] The frozen corpus map and required full SHA match this record.
- [ ] Approved file manifest, filter version, exclusions, and counts are reconciled; detailed artifacts remain external.
- [ ] The Phase 10 benchmark schema, categories, difficulty rubric, relevance grades, split/held-out policy, pilot exclusions, and reviewer sample are predeclared.
- [ ] Annotation location and access/retention controls are confirmed outside Git.
- [ ] Annotators are instructed to create questions manually from approved static evidence, use exact inventory chunk IDs, record all required evidence, and keep labels separate from retriever output.

**Handoff state:** `[BLOCKED / READY FOR MANUAL ANNOTATION / NOT APPLICABLE]`

**Handoff reviewer and date:** `[name/role, YYYY-MM-DD, external attestation reference]`

See [repository-approval-workflow.md](repository-approval-workflow.md), [corpus-final-selection.md](corpus-final-selection.md), [privacy-clearance-report.md](privacy-clearance-report.md), [benchmark-schema.md](benchmark-schema.md), and [benchmark-generation-workflow.md](benchmark-generation-workflow.md).
