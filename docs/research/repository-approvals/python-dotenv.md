# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](../thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

**Current thesis scope: NOT SELECTED FOR THESIS SCOPE.** No active approval/evidence-closure task remains for this unused repository. Its historical BLOCKED disposition is retained below; it is not a current scope status or a new approval. Reconsideration requires only the applicable Phase 1 evidence in the replacement workflow.

## Historical document (unchanged)

# Phase 19.5 - Repository Approval Record: python-dotenv

**Final Gate 1 decision: BLOCKED**
**Review date:** 2026-09-27 (UTC)
**Record ID:** `repository-approval-python-dotenv-corpus-snapshot-v1`
**Evidence collector:** Codex, automated local checks; not a designated human reviewer or approval authority.

This record replaces the open template for this one candidate. The Phase 19.5 user instruction authorizes bounded evidence collection and documentation, not benchmark expansion. Selection uses only the [existing registry](../benchmark-candidate-registry.md) and this candidate's existing approval record. No other candidate was advanced. Humanize remains frozen and pilot-only.

## 1. Selection and repository identity

| Field | Recorded value |
|---|---|
| Repository name | `python-dotenv` |
| Owner/project | `theskumar/python-dotenv` |
| Canonical URL | https://github.com/theskumar/python-dotenv |
| Existing checkout origin | `https://github.com/theskumar/python-dotenv.git` |
| Pinned commit / verified HEAD | `a00cb2eed0704cd6d2071b2004c37e95ccc86ee5` |
| Verified Git tree | `9d1f2ecb741b9644d593b1488c5373a09db151c7` |
| Snapshot / filter | `corpus-snapshot-v1` / `phase4.5-python-v1` |
| Language | Registry metadata: Python, Makefile; proposed study scope: Python only |
| Screening size | Small; 20 eligible Python files / 2,776 LOC (prior screening, not a newly approved manifest) |
| Root license evidence | Registry and prior approval record: BSD-3-Clause, root `LICENSE`; pinned blob checked locally, digest in E1 |
| Selection reason | First queued small candidate; compact configuration-library scope makes one complete Gate 1 trial manageable without adding a repository or changing the frozen corpus. Selection is not a safety or license-compatibility judgment. |

**Proposed purpose:** resolve Gate 1 evidence for this exact snapshot and proposed Python scope. No activity beyond this evidence review is approved. Annotation, benchmark questions, indexing, embeddings, retrieval, evaluation, external source transfer and publication remain unauthorized.

## 2. Evidence packet and method

Packet alias **`phase19.5-python-dotenv`** maps to `C:/Apps/Temp/Phase19.5/python-dotenv`, outside the thesis Git repository. Existing source remains at `C:/Apps/Temp/Phase5.4/corpus/python-dotenv`; existing scan reports remain in `C:/Apps/Temp/Phase5.4/reports/privacy`. These are observed storage locations, not approved handling controls. Detailed file paths/hashes and access identities stay outside Git. Only aggregate results and evidence references are recorded here.

The collection requirement was written into this record before the new content checks: perform local, read-only license/privacy indicator triage; verify existing secret-report provenance first; require a replacement secret scan if provenance cannot be established. No new Gitleaks/history scan, fetch, clone, candidate execution, benchmark pipeline or annotation inventory was run. The indicator review is not a secret scanner or a human review.

| ID | External packet item | SHA-256 |
|---|---|---|
| E1 | `evidence.json`: timestamp, identity, license checks, aggregate content indicators, existing report results | `680a8c1844d6da48fc8a390614a384de87d75b287b5989197c36cb9459d25b3d` |
| E2 | `snapshot-details.json`: exact pinned blob inventory and indicator locations; evidence scope only | `31dacd5b1b09588e042686e76e5f2f1388741a449b1047b98192ad4905186cd7` |
| E3 | `collect-evidence.py`: reproducible local collection method and indicator expressions | `6f60248fba3fe7aa42859890d401a70f52e5511acb55300f3d743d2d49495c31` |
| E4 | `access-details.json`: observed Windows ACLs for checkout and packet | `1ff19ae524a270e30a8ea602157c73632ba438080aed13f6ff35a261d1c23a29` |
| E5 | `access-summary.json`: ACL and read-only attribute aggregates | `eb435e03fda9049db183e4beda2ad4fc1347c0ba101f75b96d2cbf9f660ca265` |
| E6 | `scan-provenance.json`: selected candidate's CSV rows, original CSV digest and limitations | `307f9a0760179feb30a89ae82c57cf709a166155523d466eb564cca314bf48a6` |
| E7 | `tests.log`: full existing application suite | `7ffe24c7a4045899a5c183a79652f95672c8d0db1da0fefcbfc8c0f81d078ac5` |

E1 records collection at `2026-09-27T16:04:11.217158+00:00`. E3 uses Git `2.55.0.windows.5`, reads pinned Git blobs locally, emits no source excerpts, and compares the worktree after CRLF normalization. E4/E5 were collected on the same UTC date with PowerShell `Get-Acl` and file attributes. Human review and signed approval are absent; neither the collector identity nor a digest substitutes for them.

## 3. Evidence checklist and findings

| Category | Completed evidence | Gate disposition / missing evidence |
|---|---|---|
| Identity | Origin and exact SHA match; detached HEAD; clean tracked/untracked status; tree digest; all 47 pinned files readable; `git fsck --full --no-reflogs` exit 0; zero worktree mismatches after CRLF normalization (E1-E3) | Objective identity verified. Enforced read-only handling not established; full identity/handling gate remains open. |
| License/notices | Root license blob fingerprint and all four BSD clause markers checked; notice indicator triage across 47 tracked files (E1-E3) | Human file-level terms, attribution, applicability and exclusions unresolved. |
| Privacy/data | All 47 tracked files checked for declared text indicators; aggregate outcomes below (E1-E3) | Preliminary triage only; designated human review and dispositions missing. |
| History | Shallow state, available refs and one reachable commit verified (E1) | Earlier/deleted content unavailable; history coverage or authorized limitation acceptance missing. |
| Security/secrets | Two saved JSON reports parsed and hashed; selected CSV rows reconciled (E1, E6) | Contradictory finding counts and missing original scan provenance; BLOCKED. |
| Manifest/exclusions | 47 tracked files, including 20 Python files, inventoried for evidence (E2) | Python count agrees with screening; filter eligibility, LOC, exclusions and final approved manifest not reconciled. |
| Handling | Source/packet locations and current ACL/file attributes recorded (E4-E5) | Approved access, read-only, telemetry, backup, retention/deletion and incident controls not evidenced. |
| Approval | Exact purpose, blockers, responsibilities and explicit BLOCKED disposition recorded here | Named authorized human reviewers and signed decision absent; no approval inferred. |

### Identity and checkout reproducibility

The existing detached checkout resolves to the registered SHA and tree; all 47 tracked blobs can be read from the local object database, and their worktree contents agree after CRLF normalization. Recheck with `git remote get-url origin`, `git rev-parse HEAD`, `git rev-parse HEAD^{tree}`, `git symbolic-ref -q HEAD` (exit 1 means detached), `git status --porcelain --untracked-files=all`, and the E3 script against the existing checkout. Clean status and local object availability establish local snapshot reproducibility, not a fresh network-clone test or proof of upstream authenticity. No network fetch was performed. E5 finds zero of 47 files marked read-only; read-only command use does not prove an enforced filesystem restriction.

### License and notice review

The pinned root `LICENSE` SHA-256 is `80619b7049f08c81683ad0e01f08f257a840652dd71ee83146d36658c7d2c2b9`. E1/E3 confirm source-notice retention, binary-notice reproduction, non-endorsement and warranty-disclaimer text markers, consistent with the existing BSD-3-Clause screening record. This is objective text evidence, not legal compatibility clearance.

Notice-related markers occur in six non-Python tracked files; no Python file matched the declared notice expression. That does not establish that every file is covered by the root license. The designated terms reviewer must inspect all applicable notices, assess any incorporated material, record source/binary notice obligations for the intended use, and specify retained notices and exclusions. Until then, notice requirements and distribution compatibility are unresolved. No source distribution is authorized by this record.

### Privacy and data review

Local triage used the exact 47-file pinned tree, not live upstream content (E1-E3). Results are file counts, not numbers of people, secrets or incidents:

| Category | Observed result | Limit / required disposition |
|---|---|---|
| Personal data indicators | Email-shaped text in 3 non-Python files | Human reviewer must classify public attribution/contact vs other personal data and decide minimization; identifiers not reproduced here. Names, phone numbers and other personal data are not comprehensively detected. |
| Confidential-data indicators | 0 files matched the declared confidential/proprietary/internal-only/private-key expression | No absence claim; semantic confidential-data review remains required. |
| Credential-related text | 5 files matched password/secret/token/API-key expressions, including 2 Python files | Could include examples or ordinary code; no finding is declared a live secret or false positive. Human disposition required. |
| Generated artifacts | 0 files matched generated-file markers; 0 files contained NUL bytes | Heuristic only; does not rule out generated text, binaries without NULs, ignored artifacts or untracked ignored files. |
| External datasets | 0 files matched dataset/download expressions; observed tracked extensions listed in E1 | Does not establish absence of external data, fixtures, embedded data or runtime downloads. A human must review references and data provenance. |
| Unresolved privacy concerns | Human personal/confidential review, indicator dispositions and historical exposure assessment absent | BLOCKED; no privacy clearance, no accepted exclusions. |

No raw source, matching personal identifiers or candidate secret values were printed into this record. The review is automated preliminary evidence, not independent human review. It does not examine remote services, earlier commits, ignored files, external datasets or dependencies.

### History review

`git rev-parse --is-shallow-repository` returned `true`; `git rev-list --count --all` returned `1`. Local `main`, `origin/main` and `origin/HEAD` point to the pinned commit (E1). Earlier commits, deleted secrets/data, other branches/tags, unreachable upstream history and prior exposure cannot be assessed from this checkout. An authorized reviewer must either require acquisition and scanning of a defined broader range or sign an explicit bounded-history limitation with residual risks. Neither has occurred. No historical exposure or incident is asserted absent.

### Security/secret review and required next scan

The prior [approval status report](../repository-approval-status-report.md) leaves candidate scan disposition open. Existing `python-dotenv-dir.json` and `python-dotenv-git.json` each parse as an empty JSON list (0 findings, 3 bytes), each with SHA-256 `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` (E1). However, the corresponding original `scan-summary.csv` rows each say `ExitCode=0, Findings=1` (E6). **The reports conflict.** This record does not silently correct the CSV or infer a counting bug or a clean scan.

The inherited approval context identifies Gitleaks 8.30.1, but these empty reports cannot establish the original executable/configuration, command, ignore rules, exact scanned SHA/files/refs or run timestamp. E1 records file modification times only; they are not authenticated scan dates. No saved candidate details exist in these two JSON lists to disposition, while the CSV's two reported findings remain unexplained. New credential-text indicators above are separate from these historical scanner counts.

**Requirement documented before any replacement scan:** first recover original logs/configuration and reconcile the count discrepancy. If unavailable, a designated reviewer must arrange a replacement local scan of the pinned scope, retaining tool/version/executable and configuration digests, exact SHA/files/refs, ignores, timestamp, exit code, redacted reports and dispositions. History needs its own coverage decision. No replacement secret/history scan was run in Phase 19.5; new scan results could not close the missing human or handling gates by themselves.

## 4. Handling controls and responsibilities

| Control | Observed evidence | Required closure / responsible role |
|---|---|---|
| Storage | Existing checkout and packet locations above, both outside Git | Research data owner must approve these actual locations and the evidence scope. |
| Access restrictions | Both locations inherit ACLs, each with six allow entries; detailed identities/rights retained in E4. None of 47 source files has a read-only attribute (E5). | Data owner must identify authorized principals, assess effective access and establish documented restricted/read-only handling. No claim of owner-only access. No ACLs changed. |
| Local processing / telemetry | Collection script reads locally; no source excerpts printed; no candidate code executed or network clone/fetch used | Owner must attest applicable telemetry/network controls and prior exposure limits; local commands alone do not prove system-wide offline operation. |
| Backup handling | No backup inventory, encryption/access evidence or cloud-sync assessment in the candidate approval record | Owner must identify copies, backup destinations, encryption and access; do not assume no backups exist or include this packet in new unreviewed backups. |
| Retention/deletion | No approved period, trigger, copy inventory or deletion attestation | Owner must set retention for source/reports/packet, deletion trigger and accountable verifier, including backups. No retention date invented and no evidence deleted. |
| Incident / stop procedure | This BLOCKED record prevents downstream use | Reviewer must assign contact and containment procedure. Changed SHA/scope, live-secret suspicion, unreviewed transfer or failed controls require stop and re-review; do not expose raw findings in Git. |
| Reviewer responsibility | Automated collector identified; no named designated human in prior approval record | Researcher assembles packet; privacy reviewer dispositions data/secret/history concerns; terms reviewer resolves notices; authorized approver records final scope and controls. Roles may coincide only with an explicit solo-review limitation. |

## 5. Final Gate 1 decision and remaining gaps

**Decision state: BLOCKED.** This is the evidence-workflow disposition on 2026-09-27, not an authorized human approval or a rejection of the repository. Neither `READY FOR REVIEW` nor `APPROVED WITH CONTROLS` is warranted because mandatory evidence remains incomplete. Existing approval and downstream handoff remain unauthorized.

| Missing item | Closure evidence required |
|---|---|
| Scan count/provenance reconciliation | Explain saved JSON/CSV conflict with original evidence or documented replacement scan and all finding dispositions. |
| Human privacy and historical exposure review | Named/date/scope/method; resolve personal, confidential and credential indicators, generated/external data concerns and exclusions. |
| History scope decision | Adequate scan coverage or attributable acceptance of the exact shallow one-commit limitation. |
| License and notices | Human file-level applicability/attribution/retention assessment for the exact intended activity. |
| Approved manifest | Exact filter, exclusions and file/LOC reconciliation; current evidence inventory is not an annotation manifest. |
| Handling controls | Actual access/read-only, telemetry, backups, retention/deletion and incident responsibility. |
| Attributable decision | Named authorized reviewer/role/date, evidence references, exact SHA/scope/purpose and conditions. |

| Reviewer field | Value |
|---|---|
| Evidence collector / date | Codex automated checks / 2026-09-27 UTC |
| Designated privacy reviewer / date / attestation | UNASSIGNED / NOT RECORDED / NOT RECORDED |
| Designated license reviewer / date / attestation | UNASSIGNED / NOT RECORDED / NOT RECORDED |
| Storage/data owner / control attestation | NOT RECORDED / NOT RECORDED |
| Authorized decision-maker / role / date / signature reference | NOT RECORDED / NOT RECORDED / NOT RECORDED / NOT RECORDED |
| Approved purpose / accepted residual risk | NONE / NONE RECORDED |
| Next action | Responsible researcher assigns the reviewers and resolves this candidate's scan discrepancy and handling evidence; keep all other candidates on hold until this workflow is reviewed. |

**Workflow problems identified:** existing empty scan reports lack self-contained provenance and disagree with the summary; shallow history was not an accepted coverage decision; a clean detached checkout was not demonstrably protected read-only; template placeholders did not assign named responsibility; evidence storage lacked verified lifecycle controls; screening counts did not constitute an approved manifest. These are concrete barriers to closure, not reasons to substitute another candidate.

## 6. Validation and completion boundary

The existing application suite ran with `C:/Apps/Temp/Phase6.2/venv/Scripts/python.exe -m unittest discover -s tests -v`, `EMBEDDING_MODEL_CACHE=C:/Apps/Temp/Phase6.2/model-cache`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and `PYTHONDONTWRITEBYTECODE=1`.

**Exact result:** `Ran 124 tests in 29.816s` / `OK`; exit code 0; no failures, errors or skips (E7). This validates the current application workspace, including pre-existing retrieval work; it does not validate candidate safety or grant approval.

Before/after workspace hashes and the separate 34-file Humanize pilot hash comparison are retained in the external packet. Final scope validation is recorded in `validation.json`: only this approval record and the evidence progress document change for this task; pre-existing retrieval edits remain untouched. No benchmark questions, annotations, retrieval changes or pipeline changes were made by Phase 19.5. Humanize pilot files and project Humanize records remain unchanged. The candidate checkout remains clean at the pinned SHA.

One candidate now has an end-to-decision record covering every Gate 1 category, explicit gaps, risks, reviewer fields and workflow defects. Evidence collection has reached a documented BLOCKED decision; approval closure and human review remain outstanding. No benchmark expansion has started. Do not begin a second candidate before review of this workflow.
