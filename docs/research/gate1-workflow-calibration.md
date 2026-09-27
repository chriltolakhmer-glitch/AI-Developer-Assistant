# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 19.6 - Gate 1 Workflow Calibration

**Date:** 2026-09-27 (UTC)

**Outcome:** Workflow calibration documented and template/checklist clarifications applied. **python-dotenv remains BLOCKED.** Eight queued candidates remain blocked; zero ready for approval and zero approved. Humanize remains frozen, pilot-only and outside the queue. This is a documentary review, not a human privacy/terms approval or permission to begin another candidate.

## Review basis and limits

The first end-to-decision trial is [python-dotenv's Phase 19.5 record](repository-approvals/python-dotenv.md), for `theskumar/python-dotenv` at `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5`. Its sections 2-5 identify evidence E1-E7, findings, missing evidence and responsibilities. This calibration relies on that recorded evidence; it does not reopen its checkout or raw reports, rescan, resolve findings or change its decision.

Reviewed documents:

| Document | Calibration finding |
|---|---|
| [Repository approval template](repository-approval-template.md) | Broad gates existed, but collection authority, evidence index, contradiction tracking, action ownership and separate collection/decision states needed explicit fields. |
| [Evidence progress tracker](repository-evidence-progress.md) | Correctly kept eight candidates blocked, but needed a distinct workflow status and lessons section so completed collection is not mistaken for clearance. |
| [Candidate clearance matrix](benchmark-candidate-clearance-matrix.md) | Historical python-dotenv row still said PENDING and described earlier evidence gaps; it must be identified as the Phase 18.2 baseline and link to the later decision, not act as a competing live ledger. |
| [Gate 1 quality requirements](benchmark-quality-gates.md#1-repository-approval-gate--g1) | Retain evidence thresholds, but interpret them through the simplified workflow; historical gate numbering and outcome labels cause avoidable ambiguity. |
| [Evidence closure plan](repository-evidence-closure-plan.md), [approval workflow](repository-approval-workflow.md), [evidence closure workflow](repository-approval-evidence-closure.md) | Supply objective requirements, readiness rules, solo-review limits and authorized exception handling. Historical status paragraphs are not current decisions. |
| [Simplified workflow](benchmark-research-workflow-final.md) and [expansion checklist](benchmark-expansion-checklist.md) | The four-gate workflow supersedes the operational G0-G6 chain while retaining evidence and quality requirements. Do not restore removed boards or import annotation/evaluation checks into this calibration task. |

No elapsed-time or effort breakdown was recorded for the trial. “Delays” below means evidenced impediments and likely rework, not measured delay durations or a claim that any person caused them.

## Blocker classification

Classify the immediate problem, then link it to the approval requirement it affects. Categories overlap: repairing documentation cannot waive required evidence, and an evidence-collection problem can keep approval blocked.

| ID / trial issue | Primary class | Requirement affected / closure needed | Responsible role and next action |
|---|---|---|---|
| B1: No designated human privacy review or indicator dispositions | Mandatory approval | Trial section 3 reports email-shaped text in 3 files and credential-related text in 5; neither is a confirmed exposure or a false positive. Human review must cover personal/confidential data, generated artifacts, external data and prior exposure, with scope, date, disposition and exclusions. | Researcher assigns privacy reviewer; reviewer records findings and limitations. |
| B2: Root-license markers but no applicable file-level terms decision | Mandatory approval | Six files have notice indicators; root screening does not settle applicability, attribution, retention or intended-use rights (trial section 3). | Terms reviewer assesses applicable notices and conditions; separate authority only where required. |
| B3: Actual handling controls not approved/evidenced | Mandatory approval | Trial section 4 lacks effective restricted access/read-only evidence, telemetry limits, backup, retention/deletion and incident responsibility. | Data owner verifies actual controls, copies and lifecycle; approver assesses conditions. |
| B4: No named authorized approver or activity-specific decision | Mandatory approval | Trial section 5 has unassigned reviewer/authority fields. A collector's BLOCKED disposition cannot approve use. | Researcher identifies responsible authority; final decision only after evidence closure. |
| B5: JSON reports say zero findings, CSV rows say one each | Evidence collection | Trial E1/E6 conflict; original command/configuration, exact scan scope and timestamp are not established. Zero findings cannot be accepted. | Scan reviewer recovers provenance and explains discrepancy, or documents a replacement-scan requirement before any authorized rerun; retain the conflict history. |
| B6: One available shallow commit | Evidence collection; also mandatory scope decision | Trial E1 establishes available history, not adequate historical exposure coverage. Need defined coverage or an attributable, justified acceptance of the exact limitation. | Privacy/scan reviewer proposes coverage; authorized reviewer accepts or requires additional evidence. Full-history fetch is not automatic. |
| B7: 47-file evidence inventory / 20 Python files, no final filter/LOC/exclusion reconciliation | Evidence collection | Trial E2 is not an approved eligible manifest. Prior 2,776 LOC remains screening evidence. | Researcher reconciles scope under the permitted activity; changed corpus scope/counts require a versioned decision before use. |
| B8: Keyword/NUL checks provide incomplete data review | Evidence collection | Trial section 3 explicitly cannot exclude personal/confidential data, generated content, external datasets, ignored files or binaries. | Human reviewer documents coverage and exclusions; do not make the heuristic more authoritative by renaming it. |
| B9: Detached/clean checkout confused with protected handling | Workflow/documentation; B3 evidence still required | Trial E1 verifies identity, while E4/E5 do not establish an effective restriction. File attributes or ACL-entry counts alone do not prove effective access. | Separate identity facts from control implementation; data owner records mechanism and verification. |
| B10: Unassigned ownership, inconsistent state names and stale parallel summaries | Workflow/documentation | Template lacked a remediation ledger; matrix, tracker and historical workflows use different labels. | Add owner/action/closure fields, state crosswalk and links to one current record; do not invent people or signatures. |
| B11: “Collected”, “reconciled” and “complete” can imply more than observed | Workflow/documentation | Trial checklist calls CSV rows “reconciled” but its detailed section says the conflict is unresolved. An end-to-decision record is complete as a record, not as approval evidence. | Future records say “compared; discrepancy unresolved” and separately record collection progress, gate status and decision authority. Historical trial is preserved. |

B1-B8 remain open. B9-B11 have documentary mitigations in this phase; the underlying candidate evidence and approval requirements remain open. A classification is not a disposition of a finding.

## What worked

- One registered candidate and exact SHA kept the trial bounded; no substitution or benchmark expansion followed the blocked result.
- Identity, tree, local reproducibility and shallow-history observations were recorded with method limits. Evidence IDs/digests separated safe summaries from detailed external material.
- Comparing the saved scan outputs and CSV exposed an inconsistency that the earlier screening summaries did not resolve.
- Automated indicators were explicitly distinguished from confirmed findings and human review. Missing handling evidence was recorded rather than assumed from public availability or a local folder.
- The final record covered every category, named missing evidence and explicitly stayed BLOCKED. Tests and preservation checks were reported as software/scope validation, not privacy approval.

## What caused delays or rework

Existing scan files did not carry enough provenance to establish their original scope, and the conflicting counts prevent reuse as clearance evidence (B5). Shallow history and a screening inventory needed separate coverage and eligibility decisions (B6-B7). Collecting additional automated indicators could not replace the absent human reviewers or control attestations (B1-B4, B8).

The reusable template bundled multiple facts into broad placeholders. That made a verified identity appear tied to an unresolved read-only control and left no simple owner/action ledger (B9-B10). Parallel status documents could drift; the matrix's older PENDING row and the trial's BLOCKED decision illustrate the problem. The trial also had to supply its own evidence index and precise method limitations.

Future work should check collection authority, responsible people, packet handling and existing provenance first. This reduces avoidable collection but does not retroactively void the separately authorized Phase 19.5 checks or request their authorization again.

## Missing or underspecified template fields and applied fixes

| Gap in the previous template | Phase 19.6 improvement |
|---|---|
| No explicit collection authority, selected-candidate rationale or proposed next activity | Added setup fields distinguishing evidence collection from downstream use. |
| Broad reviewer placeholders without remediation ownership | Added collector vs designated reviewer/authority, data owner/incident contact, single-reviewer limitation and blocker owner/action/closure table. Unknown assignments stay explicit. |
| Evidence references scattered across gates | Added evidence index with exact SHA/scope, method, digest, collector/time and human review result/time. |
| No report-conflict or supersession discipline | Added original-run provenance, count comparison, discrepancy handling and retention of superseded evidence. File mtime is not a scan date. |
| Checkout identity and read-only handling bundled | Added separate observed identity/local reproducibility and actual read-only/effective-access fields. |
| Personal-data category did not prompt generated/external-data review | Added explicit categories and limitations, including fixtures and historical exposure. |
| Handling controls compressed into one cell | Added explicit backup copies/destinations, retention trigger, deletion coverage/verifier and incident ownership prompts. |
| “Approved study language” could prematurely imply approval | Renamed to proposed scope plus approval reference. |
| Overall status omitted APPROVED and readiness, while mixing review progress and outcome | Separated collection state, Gate 1 state and authorized decision; defined readiness and controlled approval prerequisites. |
| Template said completed records remain external, yet workflow uses committed candidate summaries | Clarified blank reusable template vs permitted non-sensitive per-candidate summaries; raw/private evidence remains external. |

The template additions do not fill any candidate's missing fields and do not create extra approval boards.

## Duplicate checks and reuse rules

| Repetition | Keep one evidence source; preserve necessary rechecks |
|---|---|
| Root license/notice information in template B and C | B identifies applicable scope/root evidence; C references the same evidence ID for human terms disposition. Do not conduct two identical reviews. |
| Secret-scan gate, finding disposition gate and privacy review | Reuse one scan/disposition ledger. Keep human personal/confidential review distinct: it addresses questions the scanner cannot answer. |
| Checkout identity, manifest and annotation handoff | Reuse identity evidence for the same SHA/scope. Manifest reconciliation is a separate eligibility check; revalidate at handoff or after relevant changes. |
| Handling table and source-handling checklist | One dated control record; checklist verifies applicability and unresolved exceptions rather than duplicating attestations. |
| Candidate record, tracker, clearance matrix and historical status reports | Candidate record is authoritative for detailed current evidence/decision; tracker summarizes and links it. Matrix is labeled historical with a current link. Do not copy raw findings or rewrite earlier phases as current reviews. |
| Unit tests in multiple phases | Run once for the requested phase; reference the actual result. Repeat only after relevant changes/failures. Tests are not a Gate 1 safety check. |

Reuse requires matching SHA, activity, filter, exclusions and handling scope, with evidence currency assessed. A new date on an unchanged summary does not renew approval. Shared storage policy can be referenced across future candidates, but each record must establish that actual controls apply to its source/packet.

## Ambiguous approval rules and calibrated interpretation

The Phase 18.4 four-gate workflow governs operational sequence; older G0-G6 documents remain historical evidence and quality checklists. This calibration clarifies recordkeeping, not approval authority or evidence thresholds.

| Label or ambiguity | Interpretation for future Gate 1 records |
|---|---|
| BLOCKED; older HOLD / REVISE / PENDING | No permission. Preserve the historical label/date; current record states the actual unresolved requirements. REJECTED remains a separate explicit authorized rejection. |
| READY FOR REVIEW; older Ready for approval / READY FOR DECISION | Same readiness intent only when all mandatory evidence is complete, consistent, dated, attributable and resolved, including required exception decisions; only final authorization remains. It grants no permission. Do not automatically relabel historical rows. |
| APPROVED / APPROVED WITH CONTROLS; older PASS / APPROVE | Require actual named, dated, activity-specific authorization and all required evidence. Historical shorthand alone cannot prove it. Controls must be evidenced and accepted; missing mandatory evidence is not a condition that can be deferred into approval. |
| Completed evidence category vs PASS | A recorded observation or completed triage is not a passed gate. Track collection progress independently. |
| Inventory required before permission to prepare inventory | Declare the exact requested activity. Existing quality requirements allow a documented inventory-preparation boundary, but that needs its own applicable evidence and explicit decision. Annotation use still needs the reconciled approved manifest. Do not re-scope python-dotenv to bypass its blocker. |
| Full history vs shallow history | Coverage must be justified; either obtain adequate evidence under authorized scope or record an explicit authorized limitation decision. This is not automatic acceptance of shallow history. |
| Human review vs independent review | Gate 1 requires attributable responsible human assessment; existing solo-thesis rules allow combined roles with disclosed limitations where authority permits. Do not impose a new board. Independent annotation review remains a later requirement and cannot be performed by a second model session. |
| Approval to collect evidence vs approval to use source | Record the existing instruction/decision for bounded collection and applicable handling conditions. It neither approves the candidate nor authorizes annotation, retrieval, transmission or distribution. |

## Recommended workflow and calibrated checklist

This is a future-use checklist; none of its boxes grants permission or records a new candidate pass.

1. [ ] Select exactly one existing candidate and link its record/SHA; identify current instruction, permitted collection, proposed next activity and exclusions.
2. [ ] Assign responsible reviewers/data owner and establish applicable packet/source handling before new collection; record unassigned roles and stop conditions explicitly.
3. [ ] Index existing evidence first. Verify SHA/scope, method/configuration, digests, original dates and provenance; compare counts across raw reports, summaries and dispositions. Record conflicts without overwriting them.
4. [ ] Document required missing checks before running them under authorized scope. Verify identity/local reproducibility separately from access/read-only controls. Do not acquire additional history or run scanners by implication.
5. [ ] Record human privacy/terms findings, defined history coverage, generated/external-data concerns and eligible-manifest reconciliation appropriate to the activity. Link one evidence record from repeated checks.
6. [ ] Resolve every blocker with dated evidence and attributable disposition; document authorized limitations precisely. Unknowns remain BLOCKED, including unavailable evidence.
7. [ ] Separate collection completion from readiness and final decision. Only all-required-evidence completion permits READY FOR REVIEW; only the authorized decision permits the named next activity.
8. [ ] Update the current candidate record and tracker with safe summaries and links; retain prior decisions and evidence. Verify no protected pilot, benchmark or code artifacts changed; record tests separately.
9. [ ] Review this one-candidate outcome before starting another. Reuse the calibrated process only within separately authorized scope; changed SHA/activity/filter/controls reopen affected checks.

**Priorities:** First assign accountability and actual handling evidence; next reconcile python-dotenv's scan provenance/counts and history scope; then complete human reviews and manifest reconciliation. These are recommended next actions, not actions executed in Phase 19.6. Do not spend effort duplicating scans merely to produce another report with the same provenance gap.

## Remaining candidates and workflow status

**Workflow status: CALIBRATED DOCUMENTATION; candidate clearance unresolved.** This phase completes the requested documentary review of the first trial. It does not supply the human privacy/terms review or authorized decision missing from that trial, and it does not start a second repository.

The seven remaining non-Humanize candidates need the same minimum evidence categories and state rules, with checks scaled to their recorded risks, scope and existing usable evidence. They do not need identical commands, repeated boards or a fresh scan when current matching evidence is sufficient. No inference is made about their actual contents. Their existing records and approval states remain unchanged. Humanize is not a candidate for this rollout.

## Validation

Changed documentation only: this report, the approval template, evidence progress tracker, clearance-matrix clarification and Gate 1 quality clarification. The Phase 19.5 python-dotenv record and all other approval records remain unchanged. No source checkout or raw candidate report was inspected, no new repository was processed, and no questions, annotations, retrieval or benchmark code were changed in Phase 19.6.

Existing suite command: `C:/Apps/Temp/Phase6.2/venv/Scripts/python.exe -m unittest discover -s tests -v`, with `EMBEDDING_MODEL_CACHE=C:/Apps/Temp/Phase6.2/model-cache`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `PYTHONDONTWRITEBYTECODE=1`.

**Exact result:** `Ran 124 tests in 9.574s` / `OK`, exit 0, no failures, errors or skips. Log: `C:/Apps/Temp/Phase19.6/tests.log`; SHA-256 `965566a7e14ee608268a589654cfc461a8d6c01de909c3e59261ba0e0d3be184`.

Workspace and 34-file Humanize pilot before/after hashes, documentation checks and allowed-change validation are retained at `C:/Apps/Temp/Phase19.6/validation.json`. Pre-existing retrieval work is preserved. Tests demonstrate application regression status only; expansion remains blocked.
