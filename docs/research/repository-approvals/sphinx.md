# Repository Approval Record — sphinx

**Record state:** OPEN — repository-specific approval not recorded.

## A. Repository and snapshot identity

| Field | Value |
|---|---|
| Repository name | `sphinx-doc/sphinx` |
| Repository URL | https://github.com/sphinx-doc/sphinx |
| Pinned commit SHA | `b04a2101295ac3fb725b16111eda0284b6da4cca` |
| Snapshot set / protocol version | `corpus-snapshot-v1` / `phase4.5-python-v1` |
| Review record ID | `repository-approval-sphinx-corpus-snapshot-v1` |
| Review date (UTC) | `[PENDING HUMAN CONFIRMATION: repository-specific review date]` |
| Checkout identity evidence | `[PENDING HUMAN CONFIRMATION: local read-only checkout evidence/digest]` |

## B. License, language, and size scope

| Field | Value |
|---|---|
| Root license identifier | `BSD-2-Clause default; inspect file-level notices` (screening record; not legal clearance) |
| License file / evidence | `LICENSE.rst`; detailed file-level evidence remains external and requires human review |
| Per-file notices / terms review | `BLOCKED — file-level notices require human review` |
| GitHub language metadata | `Python, JavaScript, TeX, Jinja, HTML, Common Lisp, Makefile, CSS, BitBake, Cython, C, Assembly, NASL, Pascal` |
| Approved study language scope | `Python only` |
| File-filter / manifest version | `phase4.5-python-v1` |
| Size category | `Large` |
| Eligible Python files / LOC | `774 / 118,987` (validated screening baseline) |
| Stratum reconciliation | `PASS for documented screening baseline; privacy approval not established` |

## C. Repository-specific privacy and handling review

| Review gate | Status | Reviewer, date, scope and safe evidence reference | Exclusions / residual risk |
|---|---|---|---|
| Secret / credential scan of exact pinned snapshot | `IN PROGRESS` | Existing aggregate record reports one unresolved candidate finding for Sphinx; `[PENDING HUMAN CONFIRMATION: scanner report/digest and scope]` | Candidate disposition pending |
| Available Git-history scan and coverage | `BLOCKED` | Existing records report shallow coverage and an unsupported `.dot` history-scan error; `[PENDING HUMAN CONFIRMATION: resolution or accepted limitation]` | History scan limitation/error unresolved |
| Candidate finding disposition | `BLOCKED` | `[PENDING HUMAN CONFIRMATION: disposition record for the candidate]` | No attributable disposition committed |
| Personal / confidential-data review | `NOT STARTED` | `[PENDING HUMAN CONFIRMATION: designated reviewer, scope, method, date, external reference]` | Review required |
| License terms / file-level notices | `BLOCKED` | `[PENDING HUMAN CONFIRMATION: reviewer, scope, applicable notices, attribution/retention assessment]` | File-level terms unresolved |
| Eligible-file manifest and exclusions | `IN PROGRESS` | Screening counts are recorded; `[PENDING HUMAN CONFIRMATION: exact-SHA manifest digest and reconciliation]` | Detailed manifest remains external |
| Local handling controls | `NOT STARTED` | `[PENDING HUMAN CONFIRMATION: approved storage, access, telemetry, backup, retention, deletion evidence]` | Handling authorization unresolved |
| Historical exposure or other incident review, if applicable | `NOT STARTED` | `[PENDING HUMAN CONFIRMATION: assessment or NOT APPLICABLE rationale]` | Historical review unresolved |

### Source handling rules for this snapshot

- [ ] Local read-only checkout outside this thesis repository matches the full SHA. `[PENDING HUMAN CONFIRMATION]`
- [ ] Approved Python manifest, file-level notice exclusions, source storage, local-only processing, telemetry, retention, deletion, and stop triggers are confirmed. `[PENDING HUMAN CONFIRMATION]`

## D. Review outcome and approval decision

**Overall review status:** `BLOCKED — unresolved candidate, history-scan error, notice review, and required human reviews`

**Authorized decision:** `[PENDING HUMAN CONFIRMATION: APPROVED / APPROVED WITH CONTROLS / REJECTED]`

**Approved purposes and exact scope:** `[PENDING HUMAN CONFIRMATION: purpose, exact SHA, Python manifest, and exclusions]`

**Explicitly excluded activities:** `Benchmark annotation, indexing, embedding, retrieval, experiments, external transmission, and publication remain unauthorized unless separately approved.`

**Conditions, exclusions, and stop triggers:** `[PENDING HUMAN CONFIRMATION]`

**Residual risks and accepted limitations:** `One unresolved aggregate scan candidate, history-scan error/coverage limitation, file-level notices, and open privacy, manifest, and handling gates.`

**Approval evidence reference / digest:** `[PENDING HUMAN CONFIRMATION: controlled external approval record/digest]`

| Decision authority | Name / role | Decision | Date (UTC) | Signature / attestation reference |
|---|---|---|---|---|
| Repository/privacy approver | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` |
| License/terms reviewer | `[PENDING HUMAN CONFIRMATION: name/role]` | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` | `[PENDING HUMAN CONFIRMATION]` |

### Scope and expiry of approval

- This record is limited to the identity, exact SHA, Python scope, filter, manifest, and purpose above.
- **Benchmark annotation authorization:** `NOT AUTHORIZED — pending explicit attributable approval.`
- **Retrieval/indexing/embedding/experiments:** `NOT AUTHORIZED.`

## E. Annotation handoff checklist — only after approval

- [ ] Approval, snapshot, manifest, notices, counts, handling controls, schema, review sample, and external annotation location confirmed. `BLOCKED`

**Handoff state:** `BLOCKED`

**Handoff reviewer and date:** `[PENDING HUMAN CONFIRMATION]`
