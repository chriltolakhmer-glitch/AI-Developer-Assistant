# Repository Approval Record — mypy

**Record state:** OPEN — repository-specific approval not recorded.

## A. Repository and snapshot identity

| Field | Value |
|---|---|
| Repository name | `python/mypy` |
| Repository URL | https://github.com/python/mypy |
| Pinned commit SHA | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` |
| Snapshot set / protocol version | `corpus-snapshot-v1` / `phase4.5-python-v1` |
| Review record ID | `repository-approval-mypy-corpus-snapshot-v1` |
| Review date (UTC) | `[PENDING HUMAN CONFIRMATION: repository-specific review date]` |
| Checkout identity evidence | `[PENDING HUMAN CONFIRMATION: local read-only checkout evidence/digest]` |

## B. License, language, and size scope

| Field | Value |
|---|---|
| Root license identifier | `MIT for most code; PSF-2.0 applies to specified files` (screening record; not legal clearance) |
| License file / evidence | `LICENSE`; detailed file-level evidence remains external and requires human review |
| Per-file notices / terms review | `IN PROGRESS — qualifications require human review` |
| GitHub language metadata | `Python, C, C++, XSLT, Go Template, Shell, CSS, Batchfile, Emacs Lisp, Makefile, Dockerfile` |
| Approved study language scope | `Python only` |
| File-filter / manifest version | `phase4.5-python-v1` |
| Size category | `Large` |
| Eligible Python files / LOC | `444 / 144,316` (validated screening baseline) |
| Stratum reconciliation | `PASS for documented screening baseline; privacy approval not established` |

## C. Repository-specific privacy and handling review

| Review gate | Status | Reviewer, date, scope and safe evidence reference | Exclusions / residual risk |
|---|---|---|---|
| Secret / credential scan of exact pinned snapshot | `IN PROGRESS` | `[PENDING HUMAN CONFIRMATION: scanner/version, exact SHA, date, external report reference/digest]` | Candidate disposition pending |
| Available Git-history scan and coverage | `BLOCKED` | Existing records describe shallow single-commit coverage; `[PENDING HUMAN CONFIRMATION: reviewer and accepted limitation]` | History coverage unresolved |
| Candidate finding disposition | `BLOCKED` | `[PENDING HUMAN CONFIRMATION: disposition record for every candidate]` | No attributable disposition committed |
| Personal / confidential-data review | `NOT STARTED` | `[PENDING HUMAN CONFIRMATION: designated reviewer, scope, method, date, external reference]` | Review required |
| License terms / file-level notices | `BLOCKED` | `[PENDING HUMAN CONFIRMATION: reviewer and file-level attribution/retention assessment]` | MIT/PSF-2.0 qualifications unresolved |
| Eligible-file manifest and exclusions | `IN PROGRESS` | Screening counts are recorded; `[PENDING HUMAN CONFIRMATION: exact-SHA manifest digest and reconciliation]` | Detailed manifest remains external |
| Local handling controls | `NOT STARTED` | `[PENDING HUMAN CONFIRMATION: approved storage, access, telemetry, backup, retention, deletion evidence]` | Handling authorization unresolved |
| Historical exposure or other incident review, if applicable | `NOT STARTED` | `[PENDING HUMAN CONFIRMATION: assessment or NOT APPLICABLE rationale]` | Historical review unresolved |

### Source handling rules for this snapshot

- [ ] Local read-only checkout outside this thesis repository matches the full SHA. `[PENDING HUMAN CONFIRMATION]`
- [ ] Approved Python manifest, file-level notice exclusions, source storage, local-only processing, telemetry, retention, deletion, and stop triggers are confirmed. `[PENDING HUMAN CONFIRMATION]`

## D. Review outcome and approval decision

**Overall review status:** `BLOCKED — license qualifications and required repository-specific human reviews are incomplete`

**Authorized decision:** `[PENDING HUMAN CONFIRMATION: APPROVED / APPROVED WITH CONTROLS / REJECTED]`

**Approved purposes and exact scope:** `[PENDING HUMAN CONFIRMATION: purpose, exact SHA, Python manifest, and exclusions]`

**Explicitly excluded activities:** `Benchmark annotation, indexing, embedding, retrieval, experiments, external transmission, and publication remain unauthorized unless separately approved.`

**Conditions, exclusions, and stop triggers:** `[PENDING HUMAN CONFIRMATION]`

**Residual risks and accepted limitations:** `File-level MIT/PSF-2.0 terms and all privacy, history, manifest, and handling gates remain unresolved.`

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
