# Phase 12.2 — Consolidated Repository Approval Status

**Status:** **APPROVED WITH THESIS SCOPE LIMITATIONS** — thesis-level residual-risk acceptance recorded; no repository-specific approval has been granted.

**Review baseline:** Commit `ec21993` / nine records created in [repository-approvals](repository-approvals/).

**Snapshot set:** `corpus-snapshot-v1`

**Study scope:** Python source files only, using `phase4.5-python-v1`.

This report consolidates the committed approval records and the Phase 12.5 [thesis scope risk acceptance](repository-approval-thesis-risk-acceptance.md). The changed state authorizes only controlled local thesis experimentation within that decision's limits. It does not create repository-specific clearance, replace external evidence, or authorize benchmark annotation, external processing, production use, or publication.

**Thesis experimentation state:** **AUTHORIZED WITH THESIS SCOPE LIMITATIONS**.

**Repository-specific approval state:** **Full clearance is blocked**; humanize has a limited thesis-only pilot authorization and the other eight snapshots remain blocked.

## Approval matrix

| Repository | Pinned commit | Stratum | Screening baseline | Overall status | Annotation authorization |
|---|---|---|---:|---|---|
| `theskumar/python-dotenv` | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | Small | 20 files / 2,776 LOC | **BLOCKED** | **NOT AUTHORIZED** |
| `python-humanize/humanize` | `392aef707c0e74341ab4a51420984e9ea6b566c5` | Small | 13 files / 2,915 LOC | **APPROVED WITH THESIS SCOPE LIMITATIONS — PILOT ONLY** | **AUTHORIZED — MAX 12 PILOT QUESTIONS** |
| `python-validators/validators` | `70de324322def13a49a93d222f798ec1ab700885` | Small | 64 files / 4,353 LOC | **BLOCKED** | **NOT AUTHORIZED** |
| `pallets/flask` | `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | Medium | 83 files / 13,301 LOC | **BLOCKED** | **NOT AUTHORIZED** |
| `encode/httpx` | `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | Medium | 60 files / 13,800 LOC | **BLOCKED** | **NOT AUTHORIZED** |
| `Textualize/rich` | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | Medium | 213 files / 45,223 LOC | **BLOCKED** | **NOT AUTHORIZED** |
| `pytest-dev/pytest` | `8721173580390a9d297e5af06cac3f0b6841f425` | Large | 245 files / 93,998 LOC | **BLOCKED** | **NOT AUTHORIZED** |
| `python/mypy` | `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | Large | 444 files / 144,316 LOC | **BLOCKED** | **NOT AUTHORIZED** |
| `sphinx-doc/sphinx` | `b04a2101295ac3fb725b16111eda0284b6da4cca` | Large | 774 files / 118,987 LOC | **BLOCKED** | **NOT AUTHORIZED** |

**Aggregate screening baseline:** 1,916 eligible Python files / 439,669 eligible Python LOC. This is preprocessing and selection evidence only, not privacy clearance or annotation approval.

## Consolidated gate status

| Gate | Status across corpus | Evidence state |
|---|---|---|
| Exact checkout identity and read-only verification | **OPEN / PARTIAL** | Humanize has committed evidence of exact detached, clean SHA identity; the other eight records remain pending, and identity evidence alone does not authorize processing. |
| Secret / credential scan and candidate disposition | **OPEN / BLOCKED** | Humanize has saved zero-result reports with recorded digests, but scan scope/configuration and candidate disposition are not fully evidenced. The corpus baseline still reports eight unresolved candidates: six Flask, one pytest, and one Sphinx. |
| Git-history coverage | **BLOCKED** | Records document shallow single-commit coverage. Sphinx also has an unsupported `.dot` history-scan error. No accepted limitation or remediation is recorded. |
| Personal / confidential-data review | **NOT STARTED** | No designated reviewer, reviewed scope, method, date, result, or external evidence reference is recorded. |
| License and file-level notices | **IN PROGRESS / BLOCKED** | Root license screening is recorded, but file-level review remains incomplete. Mypy has MIT/PSF-2.0 qualifications; Sphinx requires file-level notice review. |
| Eligible-file manifest and exclusions | **IN PROGRESS / PARTIAL** | Humanize has exact-SHA manifest identity/count reconciliation and an external digest; detailed manifest and privacy approval remain outside Git. Other repositories remain pending. |
| Local handling controls | **NOT STARTED / PARTIAL** | Humanize has documented external local storage, but access, offline/telemetry, backup, retention, and deletion evidence remains incomplete. |
| Historical exposure or incident review | **OPEN** | Humanize has a documented unresolved historical data-handling conflict; other records still require a determination or explicit not-applicable rationale. |
| Attributable full repository approval decision | **NOT RECORDED** | Humanize has a named, dated thesis-scope pilot recommendation by Alot; no full repository approval or independent privacy/legal attestation is recorded. |

## Repository-specific blockers

- **python-dotenv, validators, httpx, and Rich:** required scan disposition, history, personal/confidential-data, notice, manifest, handling, and attributable approval evidence remain pending.
- **humanize:** exact identity, saved scan-result digests, root MIT evidence, and manifest identity/counts are documented. History, personal/confidential-data, file-level notices, handling, and historical exposure remain limitations accepted only for the maximum 12-question pilot; full repository clearance remains blocked.
- **Flask:** six aggregate scan candidates remain undispositioned, in addition to the shared open gates.
- **pytest:** one aggregate scan candidate remains undispositioned, in addition to the shared open gates.
- **mypy:** file-level MIT/PSF-2.0 applicability and attribution/retention review is blocked, in addition to the shared open gates.
- **Sphinx:** one aggregate scan candidate, an unsupported `.dot` history-scan error, and file-level notice review remain unresolved, in addition to the shared open gates.

## Decision and annotation lock

No repository is marked fully `APPROVED` or fully `APPROVED WITH CONTROLS`. Humanize has a limited `APPROVED WITH CONTROLS` thesis-scope decision for a maximum 12-question pilot only. Automated preprocessing results, tests, public availability, root license screening, and this consolidated report do not establish perfect privacy clearance or production approval.

The Phase 12.5 decision accepts residual risk only for local, public-corpus, thesis-only experimentation with sensitive-file exclusions, local/offline handling, and the documented limitations. It does not convert blocked repository rows into approvals.

**Phase 13.3 humanize pilot annotation:** **AUTHORIZED — MAXIMUM 12 QUESTIONS ONLY.**

Only the humanize pilot may proceed under its explicit controls, exact SHA, Python scope, sensitive-file exclusions, local-only handling, and stop conditions. Do not expand to the full benchmark, other repositories, benchmark freeze, production use, or external processing.

**Local thesis experimentation:** **AUTHORIZED WITH THESIS SCOPE LIMITATIONS** under [repository-approval-thesis-risk-acceptance.md](repository-approval-thesis-risk-acceptance.md).

**External processing, production use, and publication:** **NOT AUTHORIZED.**

See [repository-approval-workflow.md](repository-approval-workflow.md), [repository-approval-template.md](repository-approval-template.md), [corpus-final-selection.md](corpus-final-selection.md), and the individual [approval records](repository-approvals/).
