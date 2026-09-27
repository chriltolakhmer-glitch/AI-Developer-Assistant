# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

**Current scope:** Humanize is COMPLETE / FROZEN / PILOT-ONLY. All eight non-Humanize candidates are NOT SELECTED FOR THESIS SCOPE. The former eight-blocked queue is archived; missing approvals for unused repositories are not an active thesis backlog.

## Historical document (unchanged)

# Phase 19.1 — Candidate Selection Review

**Date:** 2026-09-27  
**Status:** Selection recommendation only. No repository is approved for processing or annotation.  
**Scope:** Documentary review of the Phase 19.0 proposals and existing approval records; no repository was cloned or source-inspected. No questions were created, annotation was not started, and retrieval code was not changed. Humanize remains frozen.

## Candidate summary

The proposal set is the same nine exact snapshots already recorded in the [Phase 9 frozen corpus selection](corpus-final-selection.md). Eight are possible candidates for a future repository-approval review. Humanize is listed for traceability but remains a completed, frozen pilot and is not considered for new expansion work.

| Candidate | Recorded size/domain | Selection-review recommendation | Current approval state |
|---|---|---|---|
| `theskumar/python-dotenv` — `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` | Small, 2,776 eligible Python LOC; application configuration | **Select for repository approval review** | Blocked for annotation; candidate-specific clearance is not documented. |
| `python-humanize/humanize` — `392aef707c0e74341ab4a51420984e9ea6b566c5` | Small, 2,915 LOC; formatting utilities | **Defer from expansion review**; pilot/reference only | Pilot-only authorization/history; pilot is complete and frozen. No new Humanize work. |
| `python-validators/validators` — `70de324322def13a49a93d222f798ec1ab700885` | Small, 4,353 LOC; validation library | **Select for repository approval review** | Blocked for annotation; candidate-specific clearance is not documented. |
| `pallets/flask` — `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` | Medium, 13,301 LOC; web framework | **Select for repository approval review** | Blocked; six unresolved Gitleaks snapshot candidates and other clearance work remain. |
| `encode/httpx` — `b5addb64f0161ff6bfe94c124ef76f6a1fba5254` | Medium, 13,800 LOC; HTTP client | **Select for repository approval review** | Blocked for annotation; candidate-specific clearance is not documented. |
| `Textualize/rich` — `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | Medium, 45,223 LOC; terminal UI/rendering | **Select for repository approval review** | Blocked for annotation; candidate-specific clearance is not documented. |
| `pytest-dev/pytest` — `8721173580390a9d297e5af06cac3f0b6841f425` | Large, 93,998 LOC; testing framework | **Select for repository approval review** | Blocked; one unresolved Gitleaks snapshot candidate and other clearance work remain. |
| `python/mypy` — `0861bb6450d6d3658e44dbca9cd2ba478faf3c1d` | Large, 144,316 LOC; static type checker | **Select for repository approval review** | Blocked; MIT/PSF-2.0 file qualifications and clearance work remain. |
| `sphinx-doc/sphinx` — `b04a2101295ac3fb725b16111eda0284b6da4cca` | Large, 118,987 LOC; documentation generator | **Select for repository approval review** | Blocked; one unresolved Gitleaks candidate, `.dot` history-scan error, and file-notice review remain. |

“Select for repository approval review” means prioritize a Gate 1 evidence review using the already recorded identity and existing approved evidence processes. It is **not** selection for benchmark inclusion, repository approval, permission to inspect/process source, or annotation authorization.

## Selection criteria evaluation

The Phase 19.0 criteria are applied to documentary information only:

1. **Frozen scope and identity:** all nine proposals match the existing Phase 9 candidate list and carry recorded full SHAs. The review did not verify a local checkout or SHA against source.
2. **Python fit:** Python is recorded as the study language for all candidates. Other language metadata is descriptive and does not expand the language scope.
3. **Size coverage:** screening baselines represent three Small, three Medium, and three Large candidates. Deferring Humanize leaves at most two Small, three Medium, and three Large candidates for expansion; the set would no longer be balanced by size. No revised target is adopted here.
4. **Domain breadth:** the eight non-Humanize candidates cover configuration, validation, web framework, HTTP client, terminal UI, test tooling, static analysis, and documentation tooling. This is a useful metadata-level diversity spread, not verified evidence coverage.
5. **License screening:** root-license identifiers are present, but applicable file notices and permissions for the intended processing/distribution scope are not fully reviewed. This supports a license-review queue, not a clearance pass.
6. **Privacy and sensitive-file readiness:** no candidate has documented expansion clearance. Known findings and incomplete privacy/history/handling records make Gate 1 review necessary; unresolved issues block processing.
7. **Feasibility/exposure:** existing Python file/LOC counts and project descriptions allow preliminary comparison. No candidate is presumed independent/blind; exposure assessment remains future work.
8. **Humanize protection:** the pilot is excluded from new expansion work. Its prior thesis-only pilot scope does not extend to a new dataset or an unseen-repository claim.

## Diversity considerations

Selecting the eight non-Humanize proposals for Gate 1 review would preserve a broad set of stated project domains without adding repositories. The selection queue includes three small candidates in the corpus definition, but only two are non-Humanize; medium and large strata each have three. If the non-Humanize set later passes the required approval and a project-specific scope decision confirms the target, the resulting evaluation must describe this imbalance accurately. The earlier balanced 9-repository design must not be carried forward by silently reusing Humanize.

No numeric score or winner ranking is produced: domain labels and LOC screening are insufficient to quantify question answerability, privacy suitability, or independent evaluation value. Gate 1 results may change the candidate pool; any resulting allocation or claim change must be documented before annotation.

## Risks

- **Approval confused with selection:** moving a candidate to Gate 1 review is only a review queue decision; all non-Humanize candidates remain blocked for annotation in the current repository approval report.
- **Incomplete evidence:** local exact-SHA verification, full-history/secret disposition, personal/confidential-data review, file-notice review, manifest/exclusions, and handling controls are not closed for the candidates.
- **Known scan/history issues:** Flask has six recorded scan candidates, pytest one, and Sphinx one plus a `.dot` history-scan error. These are unresolved candidate findings, not confirmed secrets; disposition must be documented by the appropriate review process.
- **File-level license obligations:** mypy and Sphinx need special notice review. Root-level license labels alone do not permit all intended uses.
- **Humanize exposure and freeze:** reuse, editing, or claiming the pilot as blind could contaminate the independent evaluation. Keep every pilot artifact and digest unchanged.
- **Size imbalance:** excluding Humanize leaves a 2/3/3 Small/Medium/Large composition. Do not claim three per size band or retain a 9/108 allocation without a separately documented scope decision.
- **Selection/confirmation bias:** do not choose candidates based on retrieval results or favorable expected performance. Keep all currently proposed options and reasons visible.

## Blocking issues

1. Repository-specific approval evidence is missing for every expansion candidate. A Gate 1 review must determine exact permitted activities for each exact SHA.
2. The repository approval status report lists all eight non-Humanize snapshots as blocked for annotation. No Phase 19.1 decision changes this status.
3. Existing privacy records identify incomplete history/secret handling, personal/confidential-data review, license/notice review, manifests, and local handling controls; known findings remain open for Flask, pytest, and Sphinx.
4. Exposure and blind-evaluation eligibility are not established. The approval-review queue is not a final evaluation split.
5. Humanize is unavailable for new expansion work while frozen. Its pilot-only authorization/history cannot cure the small-stratum or sample-count change.

## Recommendation

**Select the eight non-Humanize candidate proposals for repository approval review; defer Humanize from expansion selection; reject none on project merit at this stage.** This is a queueing recommendation only, based on frozen metadata and diversity. It does not pass Gate 1 or authorize source handling.

The next review should reconcile existing candidate-specific evidence for identity, language, license/notices, privacy/sensitive-file findings, and approval status under the [simplified workflow](benchmark-research-workflow-final.md). If that review requires new source access or scanning, it must occur only under the applicable already-authorized privacy process; this Phase 19.1 review performed none. Any candidate that fails or lacks evidence remains deferred/blocked. No repositories are to be added as replacements.

**End state:** no repository enters processing, source-derived inventory use, annotation, or evaluation without passing the repository approval gate for the exact commit and activity. Humanize remains frozen. No benchmark expansion execution has started.

## Evidence references

- [Phase 19.0 candidate analysis](candidate-selection-analysis.md) and [selection checklist](candidate-selection-checklist.md)
- [Phase 18.4 simplified research workflow](benchmark-research-workflow-final.md)
- [Phase 9 frozen corpus selection](corpus-final-selection.md) and [repository corpus screening](repository-corpus-final.md)
- [Consolidated repository approval status](repository-approval-status-report.md), [privacy clearance report](privacy-clearance-report.md), and [candidate clearance matrix](benchmark-candidate-clearance-matrix.md)
- [Phase 16 Humanize readiness decision](../../../../Temp/Phase8/benchmark/pilot/python-humanize/benchmark-expansion-readiness.md) and [pilot closure report](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md)
