# Repository Approval Record — humanize

**Record state:** EVIDENCE PARTIALLY CLOSED — repository-specific approval not recorded.

## A. Repository and snapshot identity

| Field | Value |
|---|---|
| Repository name | `python-humanize/humanize` |
| Repository URL | https://github.com/python-humanize/humanize |
| Pinned commit SHA | `392aef707c0e74341ab4a51420984e9ea6b566c5` |
| Snapshot set / protocol version | `corpus-snapshot-v1` / `phase4.5-python-v1` |
| Review record ID | `repository-approval-humanize-corpus-snapshot-v1` |
| Review date (UTC) | `2026-09-27` (committed Phase 8.8 review date) |
| Checkout identity evidence | `PASS for identity only: Phase 8.8 records the detached, clean checkout at the exact SHA; detailed checkout evidence remains external.` |

## B. License, language, and size scope

| Field | Value |
|---|---|
| Root license identifier | `MIT` (screening record; not legal clearance) |
| License file / evidence | `LICENCE`; root MIT evidence confirmed in the committed Phase 8.8 review; detailed evidence remains external |
| Per-file notices / terms review | `IN PROGRESS — root evidence confirmed; attributable file-level review remains pending` |
| GitHub language metadata | `Python, Shell` |
| Approved study language scope | `Python only` |
| File-filter / manifest version | `phase4.5-python-v1` |
| Size category | `Small` |
| Eligible Python files / LOC | `13 / 2,915` (validated screening baseline) |
| Stratum reconciliation | `PASS for documented screening baseline; privacy approval not established` |

## C. Repository-specific privacy and handling review

| Review gate | Status | Reviewer, date, scope and safe evidence reference | Exclusions / residual risk |
|---|---|---|---|
| Secret / credential scan of exact pinned snapshot | `IN PROGRESS` | `Phase 8.8 records Gitleaks 8.30.1 saved snapshot/history reports with 0 reported findings and digest `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`; scan command/configuration and precise scope remain unverified.` | Empty saved reports are not a complete clearance or personal-data review |
| Available Git-history scan and coverage | `BLOCKED` | Existing records describe shallow single-commit coverage; `[PENDING HUMAN CONFIRMATION: reviewer and accepted limitation]` | History coverage unresolved |
| Candidate finding disposition | `BLOCKED` | `[PENDING HUMAN CONFIRMATION: disposition record for every candidate]` | Existing pilot record has no attributable repository-specific disposition |
| Personal / confidential-data review | `NOT STARTED` | `[PENDING HUMAN CONFIRMATION: designated reviewer, scope, method, date, external reference]` | Review required |
| License terms / file-level notices | `IN PROGRESS` | `[PENDING HUMAN CONFIRMATION: reviewer, scope, attribution/retention assessment]` | Applicable notices unresolved |
| Eligible-file manifest and exclusions | `PASS — artifact identity/counts only` | `Phase 8.8 records the external manifest for the exact SHA, filter `phase4.5-python-v1`, 13 eligible files, 2,915 LOC, 0 exclusions, and digest `a9f35063535978fd5fe099506c2152922dd42bb0bf95bc56df10de8396a32868`.` | Detailed manifest remains external; this does not close privacy approval |
| Local handling controls | `IN PROGRESS` | `Committed records identify external local storage, but pilot-specific access, backup, telemetry/offline, retention, and deletion evidence is incomplete.` | Prior ACL concern remains unresolved |
| Historical exposure or other incident review, if applicable | `BLOCKED` | `[PENDING HUMAN CONFIRMATION: retrospective assessment and authorized reviewer]` | Prior records identify an unresolved data-handling history conflict |

### Source handling rules for this snapshot

- [ ] Checkout is local, read-only, outside the thesis Git repository, and pinned to the full SHA above. `[PENDING HUMAN CONFIRMATION]`
- [ ] Only the approved eligible language/files and reviewed manifest will be processed. `[PENDING HUMAN CONFIRMATION]`
- [ ] Source and all source-derived artifacts remain in approved access-controlled local research storage outside Git. `[PENDING HUMAN CONFIRMATION]`
- [ ] No source or source-derived data is sent to hosted AI/LLM, embedding, notebook, search/vector, telemetry, cloud storage, or external labeling services. `[PENDING HUMAN CONFIRMATION]`
- [ ] Optional telemetry, license notices, access, backup, retention, deletion, and stop-trigger controls are confirmed. `[PENDING HUMAN CONFIRMATION]`

## D. Review outcome and approval decision

**Overall review status:** `BLOCKED — required repository-specific human reviews are incomplete`

**Authorized decision:** `[PENDING HUMAN CONFIRMATION: APPROVED / APPROVED WITH CONTROLS / REJECTED]`

**Approved purposes and exact scope:** `[PENDING HUMAN CONFIRMATION: purpose, exact SHA, Python manifest, and exclusions]`

**Explicitly excluded activities:** `Benchmark annotation, indexing, embedding, retrieval, experiments, external transmission, and publication remain unauthorized unless separately and explicitly approved.`

**Conditions, exclusions, and stop triggers:** `[PENDING HUMAN CONFIRMATION: specific non-sensitive terms and stop triggers]`

**Residual risks and accepted limitations:** `Identity, saved scan-result digests, root MIT evidence, and manifest identity/counts are documented. History scope, personal/confidential-data review, file-level notices, handling controls, historical exposure, and attributable approval remain unresolved; no implicit acceptance.`

**Approval evidence reference / digest:** `[PENDING HUMAN CONFIRMATION: controlled external approval record/digest]`

| Decision authority | Name / role | Decision | Date (UTC) | Signature / attestation reference |
|---|---|---|---|---|
| Repository/privacy approver | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` |
| License/terms reviewer | `[PENDING HUMAN CONFIRMATION: name/role or NOT REQUIRED with rationale]` | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` |

### Scope and expiry of approval

- This record applies only to the identity, exact SHA, Python scope, filter version, manifest, and purpose written above.
- It does not extend to another snapshot, file set, processing purpose, external service, or publication.
- **Benchmark annotation authorization:** `NOT AUTHORIZED — pending explicit attributable approval.`
- **Retrieval/indexing/embedding/experiments:** `NOT AUTHORIZED.`

## E. Annotation handoff checklist — only after approval

- [ ] Explicit attributable approval covers manual annotation for this exact snapshot and scope. `BLOCKED`
- [ ] Frozen corpus map, manifest, exclusions, counts, and handling controls match. `BLOCKED`
- [ ] Phase 10 schema, rubric, split, pilot exclusion, and reviewer sample are confirmed. `BLOCKED`
- [ ] Annotators have approved external storage and evidence-record instructions. `BLOCKED`

**Handoff state:** `BLOCKED`

**Handoff reviewer and date:** `[PENDING HUMAN CONFIRMATION]`
