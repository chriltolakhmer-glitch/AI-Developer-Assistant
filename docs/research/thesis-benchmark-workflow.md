# Phase 19.8 - Software prototype scope notice

**SUPERSEDED - archived as future expansion work**

Current project scope: [Research software prototype validation](software-prototype-scope.md).

The active project is research software prototype validation. The four-phase workflow below is retained for possible later expansion, not active selection, annotation, experimentation or freeze work. Humanize is COMPLETE / FROZEN; software is ACTIVE DEVELOPMENT; expansion is DEFERRED; benchmark growth is NOT STARTED.

## Preserved earlier document

# Lightweight Thesis Benchmark Workflow

**Effective:** Phase 19.8, 2026-09-27.

This is the active benchmark workflow for the solo thesis. It replaces the administrative G0-G6 chain, the later repository-approval queue and their mandatory forms, reviewer assignments and attestations. The researcher maintains a short dated research record with evidence references; no board, multiple approvers or signatures are required. The [migration record](thesis-benchmark-governance-migration.md) lists superseded documents and retained evidence.

This phase changes documentation and scope only. It creates no questions, annotations, evaluation runs or new freeze artifacts, and processes no source repositories.

## Current thesis scope

| Material | Current scope |
|---|---|
| Humanize, `python-humanize/humanize`, `392aef707c0e74341ab4a51420984e9ea6b566c5` | **COMPLETE / FROZEN / PILOT-ONLY**. Preserve existing questions, annotations, results and hashes. Describe results as a bounded, exposed pilot, not unseen-repository or corpus-wide validation. |
| python-dotenv, validators, Flask, HTTPX, Rich, pytest, mypy, Sphinx | **NOT SELECTED FOR THESIS SCOPE**. No active evidence-closure queue or requirement to finish their historical approval packets. |
| New benchmark expansion | Outside current scope; not run or selected by this workflow change. No active repository has been selected for new annotation/evaluation. |

The former nine-repository/108-case target and proposed eight-repository/96-case allocation are historical plans, not current deliverables. This scope change does not alter the old corpus snapshot map or any pilot results. Reconsidering a repository is a new dated selection decision under Phase 1, not an automatic restart of the old approval chain.

## Decision states

| State | Meaning |
|---|---|
| SELECTED | Included in a stated thesis activity, with the Phase 1 evidence recorded. It does not authorize every future use or public distribution. |
| NOT SELECTED | Outside the current research scope. Display unused candidates as **NOT SELECTED FOR THESIS SCOPE**; do not track them as blocked work. |
| BLOCKED | A selected or actively considered activity lacks required evidence needed to perform it or substantiate its result. State the exact missing evidence and next action. Administrative forms, unassigned approvers and unused repositories are not blockers. |

Humanize's COMPLETE / FROZEN / PILOT-ONLY labels describe the preserved pilot lifecycle, not selection for new work. Old BLOCKED/APPROVED decisions remain historical facts; supersession is not a retrospective safety finding or approval of earlier handling.

## Phase 1 - Repository Selection

Record one short entry for a repository actually being considered:

- **Repository URL** and **exact full commit SHA**, with evidence that the source used matches that snapshot.
- **License check:** root license and relevant file notices, applicable attribution and any restriction on the intended thesis use. Public availability alone is not sufficient.
- **Basic data safety check:** inspect the intended file scope for credentials, sensitive personal/confidential material and unnecessary generated or external data. Record the method, relevant known findings and exclusions. A zero scanner count is not proof of absence; use an existing trustworthy scan or a targeted check when it answers a real question. Full-history scanning and retrospective exposure dossiers are not default tasks.
- **Research suitability decision:** why this repository and scope answer the research question, exposure/selection limitations, and SELECTED, NOT SELECTED or BLOCKED with a concise reason and evidence reference.

Keep source and derived research data local and outside the thesis Git repository, restrict access appropriately, exclude sensitive material, and preserve required notices. Do not upload source-derived content to hosted AI services or redistribute it by implication. A concise handling note is sufficient; ACL exports, backup attestations, designated security reviewers and a separate form suite are not routine prerequisites. An actual inability to meet the stated handling or use conditions still needs correction before the affected work.

For a known relevant finding, record its resolution or exclusion and why the remaining scope is suitable. Do not label an unresolved secret/rights question safe because its old approval form was retired. If needed evidence is unavailable, mark the affected activity BLOCKED or choose NOT SELECTED with the scope rationale; do not manufacture a clean finding.

## Phase 2 - Annotation

For each question in a future selected scope, retain:

| Required field | Minimum content |
|---|---|
| Question | Clear, answerable wording tied to the selected snapshot. |
| Evidence chunk ID | Exact identifier(s) resolving to the matching deterministic inventory; include all necessary supporting evidence. |
| Source location | File and source span, plus symbol when useful, at the recorded SHA. |
| Answer | Source-grounded expected answer, separate from retriever output. |
| Validation notes | How the researcher checked the answer and evidence, ambiguities/corrections, limitations and date. |

Retain a stable question ID and repository/SHA linkage, directly or through the dataset header. Keep any relevance grades and technical fields needed by the existing schema/loader; the five-field minimum is a research record, not a replacement serialization format. Do not change code or frozen data to make them fit this summary.

The researcher manually checks every included question, answer and evidence span against the pinned source before evaluation. Independent review can improve confidence but is not a mandatory staffing or signature gate for this solo scope. Disclose self-review and do not claim inter-rater agreement or independent validation without evidence. The former 100% second-reviewer coverage and 80% agreement gate are no longer prerequisites; historical pilot review results remain intact. Do not use generated labels or retriever rankings as ground truth.

Resolve ambiguity before using a case, keep corrections traceable, and record a digest of the evaluation input so later results refer to a fixed question/evidence set. Never edit the frozen Humanize pilot for this purpose.

## Phase 3 - Evaluation

Record the **retrieval evaluation**, **accuracy/error analysis** and **experiment records** for the exact annotated input and system version:

- Identify the repository/SHA, dataset/inventory hashes, code revision, model/configuration, dependencies and reproducible command. Include seeds and hardware where relevant; keep detailed outputs locally.
- State the retrieval task, candidate universe, metric definitions and denominators before interpreting results. Compare systems on the same cases and evidence scope; retain failed cases and report exclusions rather than dropping difficult questions.
- Report retrieval success and misses, including primary/supporting evidence and relevant error examples. Distinguish retrieval metrics from answer accuracy; do not claim answer accuracy if no answer evaluation was performed. Use metrics compatible with the implementation, with limitations explicit.
- Separate development exposure from any claimed unseen evaluation. Do not tune against evaluation answers or present the Humanize pilot as blind evidence. A small solo-reviewed pilot supports limited claims, not broad generalization.
- Check repeatability with the same inputs/configuration and record the result or unresolved variability. Preserve run outputs and interpretation, including negative results. A low score is a result, not a reason to revise ground truth.

No evaluation run is authorized or performed by Phase 19.8; these are requirements for future work brought into scope.

## Phase 4 - Freeze

Retain a **version identifier**, **artifact hash** (SHA-256) and **change log** for the exact dataset and associated experiment records. A short manifest can list the files and hashes plus their repository/SHA, annotation and run references. Verify hashes against retained bytes and keep the previous version.

Corrections create a new version with a reason and affected results; do not overwrite a frozen version. The final package references the unchanged evaluation-input digest from Phase 2 and the runs from Phase 3. A freeze is an immutable research record, not a release approval. Public distribution requires applicable rights and data safety for the actual material; it is outside current scope.

## Remaining real blockers and limitations

**There is no active expansion evidence backlog in the current pilot-only scope.** Missing enterprise signatures, reviewer assignments or full-history scans for unused candidates are not thesis blockers. All eight unused candidates are NOT SELECTED, not approved and not rejected for safety.

The existing [privacy review](privacy-review.md) records unresolved historical handling/exposure and access-control limitations. Those facts are retained and must not be described as resolved, but they do not reopen the frozen pilot or require completing an enterprise dossier merely to report its existing results. Any future pilot source processing must address the actual applicable handling conditions first. No such processing or external release is part of this phase.

For future selected work, genuine missing evidence includes an unverified snapshot, unresolved relevant license/sensitive-data issue, an untraceable answer/evidence location, an incompatible metric, or a missing reproducible run/hash. Record only the affected task and concrete missing evidence. A documented limitation narrows a claim; it does not justify inventing evidence or concealing a result.
