# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 11 — Repository Approval Record Template

**Purpose:** One review record per exact repository snapshot. This is a blank template, not an approval, privacy clearance, legal opinion, or authorization to inspect source or annotate the benchmark. Do not fill it with invented, assumed, or copied approval evidence.

**Handling:** Keep detailed completed evidence, scan outputs, file-level manifests, source-derived evidence, and signatures in the approved, access-controlled local research-data area outside the thesis Git repository. This reusable template remains blank. A per-candidate record may contain non-sensitive status, aggregate findings and safe evidence references/digests; never commit credentials, raw findings, source excerpts, sensitive paths, or private reviewer material.

**Phase 19.6 calibration:** Use the [calibrated checklist and status rules](gate1-workflow-calibration.md) under the [simplified four-gate workflow](benchmark-research-workflow-final.md). These fields improve evidence recording; they grant no review or processing permission.

## Review setup and evidence index

Complete setup before any newly authorized collection. Existing session authorization may be referenced; do not ask for the same authorization again. Missing required handling evidence remains a blocker, not permission inferred from a folder path.

| Field | Value |
|---|---|
| Selection rationale / registry reference | `[existing candidate only; why selected]` |
| Collection authority / permitted checks | `[dated instruction or decision reference; local scope, boundaries and stop conditions]` |
| Proposed next activity / exclusions | `[distinguish evidence review, inventory preparation, annotation, retrieval and distribution]` |
| Evidence collector / method / date | `[human or automated; identity, UTC date, method version]` |
| Designated reviewers / authority | `[privacy, terms and decision roles; named person and authority evidence, or UNASSIGNED]` |
| Data owner / incident contact | `[named responsibility and restricted contact reference, or UNASSIGNED]` |
| Packet alias / version / collection scope | `[safe reference; exact SHA; all tracked files vs proposed eligible files; excluded/ignored scope]` |
| Collection progress / Gate 1 state | `[NOT STARTED / IN PROGRESS / RECORDED] / [BLOCKED / READY FOR REVIEW / APPROVED WITH CONTROLS / APPROVED; rejection only by explicit authority]` |
| Single-reviewer limitation | `[roles shared, independence limitations; no automated collector represented as a human reviewer]` |

| Evidence ID | Safe reference / digest | Exact SHA and scope | Method / tool / configuration reference | Collector / collection UTC | Review result / reviewer / review UTC |
|---|---|---|---|---|---|
| `[E1]` | `[external alias; SHA-256]` | `[scope]` | `[method]` | `[collector/date]` | `[observation vs accepted disposition]` |

Use separate collection, original-run and human-review dates. File modification time is not a scan timestamp. Preserve contradictory and superseded evidence with a reason; a newer report does not silently erase an earlier finding.

| Blocker ID | Primary class | Evidence / contradiction | Required closure evidence | Responsible person | Next action / target or UNASSIGNED | Disposition / authority reference |
|---|---|---|---|---|---|---|
| `[B1]` | `[mandatory approval / evidence collection / workflow-documentation]` | `[safe summary]` | `[objective closure test]` | `[name or UNASSIGNED]` | `[action/date or unassigned]` | `[OPEN; no implicit waiver]` |

The primary class routes the work; evidence and documentation problems can still block a mandatory approval requirement. Record one blocker once and reference its ID from the gates below.

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
| Observed checkout state | `[origin, HEAD/tree, detached state, clean/untracked result, local object availability, normalization and reproducibility limits]` |
| Read-only handling evidence | `[actual mechanism/effective access, verification date and control owner; separate from clean status or file attributes]` |

## B. License, language, and size scope

| Field | Value |
|---|---|
| Root license identifier | `[identifier as evidenced; do not infer from repository metadata]` |
| License file / evidence | `[file name and external review reference; retain applicable notices]` |
| Per-file notices / terms review | `[NOT STARTED / IN PROGRESS / PASS / BLOCKED; reviewer and evidence reference]` |
| GitHub language metadata | `[languages as recorded; informational only]` |
| Proposed study language scope / approval reference | `[Python only unless separately approved; do not label proposed scope approved]` |
| File-filter / manifest version | `[for example, phase4.5-python-v1]` |
| Size category | `[Small / Medium / Large under the approved eligible-Python-LOC thresholds]` |
| Eligible Python files / LOC | `[verified aggregate count and evidence reference; never include the detailed file manifest here]` |
| Stratum reconciliation | `[PASS / CHANGE REQUIRED / NOT REVIEWED; summarize non-sensitive outcome]` |

Root license evidence is a screening input, not blanket permission or legal advice. Record any attribution, retention, file exclusion, or additional review conditions. Changes to repository membership, SHA, scope, filter, counts, or stratum require an explicit versioned corpus decision before use.

## C. Repository-specific privacy and handling review

For each review, record the state, reviewer/role, review date, method/scope, safe evidence reference or digest, exclusions, and unresolved risk. Keep detailed findings outside Git.

For scans, retain the original command, executable/version and configuration digests, ignore rules, exact files/refs/range, timestamp, exit code and output digest externally. Compare report counts with summaries and disposition records; any unexplained conflict stays BLOCKED. Record the need and permitted scope before a new scan. For personal/confidential-data review, explicitly cover generated artifacts, fixtures/external datasets and prior exposure, with method limitations; zero keyword hits do not prove absence. For history, record available vs scanned refs/commits, shallow state/errors, uncovered scope and any separately authorized limitation acceptance.

For handling, distinguish observed from approved controls. Record actual authorized readers/effective access and read-only mechanism, telemetry/network limits, backup destinations/copies/encryption/access, retention trigger or period, deletion coverage/verifier and incident responsibility. Each item needs a dated evidence reference; intended policy alone does not establish implementation.

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

**Overall Gate 1 status:** `[BLOCKED / READY FOR REVIEW / APPROVED WITH CONTROLS / APPROVED; REJECTED only with an explicit authorized rejection]`

**Authorized decision:** `[NOT RECORDED / APPROVED / APPROVED WITH CONTROLS / REJECTED; give authority/date/reference; a collector's BLOCKED disposition is not an approval]`

`READY FOR REVIEW` means all mandatory evidence is complete, consistent, dated and attributable, all relevant findings resolved and required exception decisions recorded; only the final authorized decision remains. It permits no processing. `APPROVED WITH CONTROLS` requires evidenced controls and explicit accepted residual risk, not promises to collect missing mandatory evidence. Unresolved requirements remain `BLOCKED`. Historical readiness labels are interpreted using the calibration crosswalk, not automatically upgraded.

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
