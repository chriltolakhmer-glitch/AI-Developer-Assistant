# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

**Current scope:** Humanize is COMPLETE / FROZEN / PILOT-ONLY. All eight non-Humanize candidates are NOT SELECTED FOR THESIS SCOPE. The former eight-blocked queue is archived; missing approvals for unused repositories are not an active thesis backlog.

## Historical document (unchanged)

# Phase 19.0 — Candidate Repository Selection Analysis

**Date:** 2026-09-27  
**Status:** Selection preparation only. Every listed candidate remains a **proposal**; no repository is selected or approved for expansion use.  
**Scope:** Compare only the nine repositories and exact SHAs already in the frozen Phase 9 corpus. No repository was added, cloned, or inspected for this analysis. No questions were created. Humanize remains frozen.

## Purpose and relation to the simplified workflow

This analysis prepares candidate comparison for the [Phase 18.4 simplified research workflow](benchmark-research-workflow-final.md), especially Gate 1 (Repository approval). It uses only previously recorded repository identity, GitHub language metadata, root-license screening, eligible Python LOC, stated project purpose, and approval-status records. It does not establish source suitability or repository clearance.

**Proposal is not approval.** All eight non-Humanize candidates remain blocked for annotation in the [repository approval status report](repository-approval-status-report.md). The Humanize snapshot is retained only as the frozen, completed pilot/reference; it is not proposed for new questions or expansion work. A later selection decision must still satisfy Gate 1 for the exact snapshot and intended activity.

## Selection criteria

Apply these criteria in order, using the existing frozen corpus only:

1. **Scope and identity:** exact canonical `owner/repository` and full pinned commit SHA must match the Phase 9 corpus selection. No branches, moving tags, repository additions, or substitutions.
2. **Language fit:** Python is the evaluation language. Other GitHub language metadata is recorded for transparency only and does not broaden processing scope.
3. **Size and sample balance:** use the already-recorded eligible-Python-LOC screening strata: Small 1,000–10,000; Medium >10,000–50,000; Large >50,000–150,000. Counts are screening baselines, not a fresh measurement.
4. **Domain and structural diversity:** compare stated project purpose and domain to avoid selecting only one project type. Treat potential single-file/cross-file or dependency coverage as a hypothesis until verified under permitted source access.
5. **License suitability:** retain the root license text/identifier and flag file-level qualifications. Root-license screening is not legal advice or a decision authorizing use, annotation, or distribution.
6. **Privacy and handling:** require a candidate-specific review of sensitive-file/privacy concerns, known scan/history findings, exclusions, and the applicable use/handling scope. Missing, unresolved, or contradictory evidence means defer/block; do not infer safety from public availability or preprocessing success.
7. **Feasibility and independence:** consider only the recorded Python file/LOC baseline and published project purpose at this preparation stage. Do not rank by unverified source quality or retrieval performance. Exposure and any held-out claim must be assessed separately before evaluation.
8. **Humanize protection:** retain Humanize's history and results as pilot evidence only. Do not edit its 12 cases, count them in a new allocation, or use it as an unseen repository.

## Candidate comparison method

Use a simple two-step, non-numeric comparison to avoid false precision from metadata alone:

- **Step A — record each candidate:** identity/SHA, language metadata, root-license screening, size stratum, intended diversity contribution, known approval/privacy blockers, and exposure/frozen status. The [candidate selection checklist](candidate-selection-checklist.md) provides the per-candidate record.
- **Step B — compare proposal fit:** compare diversity contribution within and across the three size strata, then apply Gate 1 as a hard prerequisite to any actual repository use. No weighted score or final ranking is assigned because repository-specific clearances are open and no authorized source-suitability review was performed.

Selection order for a future round should prioritize a defensible mix of project domains and sizes among candidates that first pass repository approval. If a stratum or candidate cannot pass, document a deferral and the resulting limitation; do not replace it with an unlisted repository or silently change the scope.

## Candidate proposals and expected diversity contribution

The table summarizes the frozen selection record. Contributions are expected from each repository's stated purpose, not verified claims about code internals. “Proposal only” means no current selection or approval decision.

| Candidate proposal | Size stratum / eligible Python LOC | Recorded domain | Expected contribution to diversity | Current constraint |
|---|---:|---|---|---|
| `theskumar/python-dotenv` — `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | Small / 2,776 | Application configuration from `.env` files | Compact configuration-library perspective in the small stratum. | Candidate-specific privacy/handling/license-notice closure and attributable approval not evidenced. |
| `python-humanize/humanize` — `392aef707c0e74341ab4a51420984e9ea6b566c5` | Small / 2,915 | Number, date, and file-size formatting | Historical utility-library pilot evidence; useful for development context only. | **Frozen pilot only.** Exclude from new selection, annotation, final slots, and unseen-repository claims. No new Humanize work. |
| `python-validators/validators` — `70de324322def13a49a93d222f798ec1ab700885` | Small / 4,353 | Reusable value and format validators | Multi-module validation-library perspective and cross-file potential to verify later. | Candidate-specific privacy/handling/notice closure and approval not evidenced. |
| `pallets/flask` — `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | Medium / 13,301 | Python web framework | Framework/application organization distinct from utility libraries. | Six unresolved Gitleaks snapshot candidates plus other open privacy/handling gates; not cleared. |
| `encode/httpx` — `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | Medium / 13,800 | Synchronous/asynchronous HTTP client | Network-client domain and sync/async design perspective. | Candidate-specific privacy/history/handling and approval evidence not recorded. |
| `Textualize/rich` — `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | Medium / 45,223 | Terminal formatting, rendering, and UI utilities | Broad terminal/UI utility domain within the medium stratum. | Candidate-specific privacy/history/handling and approval evidence not recorded. |
| `pytest-dev/pytest` — `8721173580390a9d297e5af06cac3f0b6841f425` | Large / 93,998 | Python testing framework | Test-tooling domain and large-repository organization. | One unresolved Gitleaks snapshot candidate plus other open privacy/handling gates; not cleared. |
| `python/mypy` — `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | Large / 144,316 | Static type checker | Static-analysis/type-checking perspective, distinct from application frameworks. | MIT/PSF-2.0 file qualifications and candidate-specific privacy/handling review remain open. |
| `sphinx-doc/sphinx` — `b04a2101295ac3fb725b16111eda0284b6da4cca` | Large / 118,987 | Documentation generator | Documentation-tooling domain and large component ecosystem. | One unresolved Gitleaks candidate, unsupported `.dot` history-scan error, file notices, and other privacy/handling gates remain open. |

The eight non-Humanize proposals span at most two Small, three Medium, and three Large repositories. This would not preserve the original balanced three-per-stratum allocation. No target count or independence claim is adopted here; any future change to the existing corpus/benchmark contract needs an explicit documented decision and compatible validation/finalization support.

## Risks

- **Screening mistaken for clearance:** exact SHAs, root licenses, LOC counts, and prior preprocessing do not close sensitive-data, privacy, file-notice, handling, or annotation permissions.
- **Known scan/history gaps:** Flask, pytest, and Sphinx have recorded unresolved scan candidates; Sphinx also has an unsupported `.dot` history-scan error. Candidate findings are not confirmed exposures, but remain unresolved until dispositioned.
- **Incomplete review for every candidate:** the repository approval status report says the eight non-Humanize candidates are blocked for annotation; other candidates also lack complete privacy and handling approvals.
- **Pilot leakage:** Humanize is the repeatedly studied and retrieval-tuned pilot. Reuse or relabeling would invalidate an unseen-repository claim and violate its freeze.
- **Diversity claims overstated:** purpose metadata suggests domain variety but does not establish answerable evidence coverage, repository quality, or retrieval suitability.
- **Size balance changes:** excluding Humanize leaves two small versus three medium and three large candidates. Report the actual sample and avoid claiming a balanced three-stratum sample.
- **Exposure overlap:** prior source familiarity, related projects/forks, or viewed outputs may reduce the independent pool; no candidate is presumed blind.
- **License qualifications:** mypy and Sphinx have explicit file-level notice considerations; license screening alone cannot authorize copying or distribution.
- **Selection bias from results:** candidate ordering/deferral must be decided from predeclared metadata and approval, never from favorable retrieval performance.

## Exclusion, deferral, and selection rationale

No final candidate selection, rejection, or revised corpus is made in Phase 19.0. For the next controlled review:

- **Humanize:** exclude from new expansion candidates because its 12-question pilot is complete, exposed, and frozen. Preserve all pilot history/results; do not create additional Humanize cases.
- **Previously studied assistant repositories** (`codebase-rag`, `Codebase-RAG-Assistant`, and `ai-codebase-assistant`): remain outside the existing primary corpus under the Phase 9 selection rationale to avoid prior-study selection bias. This phase does not nominate them.
- **Flask, pytest, Sphinx:** defer any use until the recorded scan/history issues and remaining repository-specific reviews are dispositioned. Their project domains do not override those blockers.
- **mypy and Sphinx:** defer use of affected files/snapshots until applicable file-level licensing/notices are reviewed and the permitted scope is explicit.
- **Other non-Humanize candidates:** remain proposals; defer processing and annotation until exact-SHA, license, privacy/sensitive-file, handling, and approval checks are complete.

These are gate-based deferrals/exclusions, not quality judgments about upstream projects. All candidate decisions remain proposals pending the simplified workflow's repository-approval review.

## Current disposition

**Candidate set recorded:** yes, limited to the existing nine frozen Phase 9 snapshots.  
**Candidates selected for expansion:** none.  
**Candidates approved for processing/annotation:** none documented for expansion.  
**Humanize:** completed pilot; frozen, pilot-only.  
**Repositories added/cloned:** none.  
**Questions or retrieval work:** none created or run.

This document prepares a comparison round only. A future selection decision must reference the updated checklist, keep repository approval as a hard gate, and preserve all existing benchmark and Humanize records.

## Evidence references

- [Phase 18.4 simplified workflow](benchmark-research-workflow-final.md)
- [Phase 18.4 expansion checklist](benchmark-expansion-readiness-checklist.md)
- [Phase 9 frozen corpus selection](corpus-final-selection.md) and [repository corpus screening](repository-corpus-final.md)
- [Repository approval status report](repository-approval-status-report.md), [privacy clearance report](privacy-clearance-report.md), and [thesis scope risk acceptance](repository-approval-thesis-risk-acceptance.md)
- [Phase 18 candidate registry](benchmark-candidate-registry.md) and [clearance matrix](benchmark-candidate-clearance-matrix.md)
- [Phase 16 Humanize readiness](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md), [closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md), and [pilot analysis](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-analysis.md)
