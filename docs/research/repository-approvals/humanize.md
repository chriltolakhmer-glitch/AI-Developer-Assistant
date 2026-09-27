# Repository Approval Record — humanize

**Record state:** **APPROVED WITH THESIS SCOPE LIMITATIONS — 12-QUESTION PILOT ONLY**

**Reviewer / researcher:** `Alot — Project Owner / Thesis Researcher`

**Decision boundary:** This is a solo-thesis risk acceptance for one controlled pilot. It is not perfect privacy clearance, a security audit, legal approval, or production approval.

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

**Overall review status:** `APPROVED WITH CONTROLS — limited 12-question pilot only; unresolved repository limitations remain`

**Authorized decision:** `APPROVED WITH CONTROLS — manual annotation for a maximum of 12 pilot questions at this exact SHA only`

**Approved purposes and exact scope:** `Manual authoring and review of at most 12 pilot questions for python-humanize/humanize at commit 392aef707c0e74341ab4a51420984e9ea6b566c5, limited to the approved Python scope and reviewed exclusions.`

**Explicitly excluded activities:** `The full 108-question benchmark, benchmark freeze, expansion to the other eight repositories, retrieval/indexing/embedding experiments, external transmission, publication, redistribution, and production use remain unauthorized.`

**Conditions, exclusions, and stop triggers:** `Local-only work; public pinned snapshot; Python-only approved scope; exclude sensitive or unassessable files; keep source-derived records outside Git; preserve MIT attribution; stop on new findings, scope mismatch, failed handling controls, or unresolved evidence that affects the pilot.`

**Residual risks and accepted limitations:** `Identity, saved scan-result digests, root MIT evidence, and manifest identity/counts are documented. Shallow history, incomplete personal/confidential-data review, incomplete file-level notice review, handling gaps, and historical exposure concerns remain accepted only within this limited pilot decision; this is not perfect privacy clearance.`

**Approval evidence reference / digest:** `Phase 13.3 solo-thesis risk acceptance recommendation; reviewer Alot; based on the committed evidence references above and the documented limitations.`

| Decision authority | Name / role | Decision | Date (UTC) | Signature / attestation reference |
|---|---|---|---|---|
| Repository/privacy approver | `Alot — Project Owner / Thesis Researcher` | `APPROVED WITH CONTROLS — pilot only` | `2026-09-27` | `Committed Phase 13.3 risk-acceptance recommendation; not an independent privacy or legal attestation` |
| License/terms reviewer | `[PENDING HUMAN CONFIRMATION: name/role or NOT REQUIRED with rationale]` | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` |

### Scope and expiry of approval

- This record applies only to the identity, exact SHA, Python scope, filter version, manifest, and purpose written above.
- It does not extend to another snapshot, file set, processing purpose, external service, or publication.
- **Benchmark annotation authorization:** `AUTHORIZED WITHIN THE SCOPE ABOVE — maximum 12 humanize pilot questions only.`
- **Retrieval/indexing/embedding/experiments:** `NOT AUTHORIZED.`

## E. Annotation handoff checklist — only after approval

- [ ] Explicit attributable approval covers manual annotation for this exact snapshot and scope. `BLOCKED`
- [ ] Frozen corpus map, manifest, exclusions, counts, and handling controls match. `BLOCKED`
- [ ] Phase 10 schema, rubric, split, pilot exclusion, and reviewer sample are confirmed. `BLOCKED`
- [ ] Annotators have approved external storage and evidence-record instructions. `BLOCKED`

**Handoff state:** `READY FOR MANUAL ANNOTATION — LIMITED PILOT ONLY`

**Handoff reviewer and date:** `Alot — Project Owner / Thesis Researcher, 2026-09-27; pilot-only risk acceptance, not full benchmark authorization.`
