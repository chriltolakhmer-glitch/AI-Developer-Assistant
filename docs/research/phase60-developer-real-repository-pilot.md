# Phase 60 — Developer Mode real repository pilot

Status: **incomplete end-to-end real lifecycle**, 2026-10-02. The authorized
Python pilot completed retrieval, diagnosis, evaluation, regression, candidate
validation and a pending review. The candidate failed validation; promotion was
rejected. Configuration, deployment, operation, recovery, assurance, governance
and closure therefore have no successful real-pilot result. Synthetic regression
coverage exercises those layers separately. This report does not waive gates or
claim a benchmark or research improvement.

## Baseline and isolation

The checkout began clean on `main` at
`9fa26cff27e213c422e52c02c5873a01d00993ae`. The release tag object is
`05688504f74ad51230ee1566fad8cda0f1b1ad97`; its peeled commit is
`51329285a882c1b7942d0a5b1c571e628d63dfb4`.
Baseline hashes, source identities, command outputs, pilot findings and test logs
are retained under `C:\Apps\phase60-validation`. Source inspection and retrieval
started while the prerequisite suite was running; they did not wait for its final
result. This sequencing deviation is recorded rather than presented as a satisfied
pre-pilot gate.

Phase 59 provides readiness views, lifecycle verification, read-only audit,
evidence bundles, manual closure and follow-ups. It reuses promotion, configuration,
deployment and deployment audit, operations, recovery/continuity, assurance,
maturity, evolution, strategic governance, decisions/actions/exceptions, candidate
review and maintenance diagnostics. See the
[Phase 59 capability inventory](phase59-developer-retrieval-operational-readiness.md).
Phase 60 adds no governance subsystem or retrieval method.

## Repository selection and environment

Two existing Phase 29 developer repositories were selected under this request's
local pilot authorization. They remain outside this checkout, research datasets,
benchmark snapshots and Humanize artifacts. Applications were not imported or
executed. Processing uses the existing pinned developer model cache offline.
The workspace is `C:\Apps\phase60-validation\pilot-workspace`.

| Identifier | Commit | Selection reason |
| --- | --- | --- |
| `local/codebase-rag-039fd2f87664` | `1bd600638dea12c3103cc95037f413690e2f4583` | Python application: 50 Python files, multiple modules, settings, API handlers and static symbol relationships |
| `local/ai-codebase-assistant-33ca4b7134fc` | `6cd1bee3d28d9fa41b39d0439425b06733370b98` | Existing TypeScript application; unsupported-language scenario, no eligible Python files |

The harness hashes tracked and nonignored files and captures commit/status before
and after processing. Both repositories remained unchanged. Neither source copies
nor generated indexes are included in project deliverables. Detailed source-derived
outputs stay external; this document contains navigation observations only.

## Retrieval and optimization observations

Python scan/index succeeded. Of 315 generated chunks, 194 were searchable and 121
were skipped. All three configuration-file chunks were over the existing token
limit. Repeat indexing succeeded. Six questions each completed query, trace and
context analysis. Repeating the cache question produced identical result records.
Trace includes selected results and ranking explanations; relationship expansion
is static and bounded, not proof of runtime calls or dependencies.

| Scenario | Observed navigation |
| --- | --- |
| Configuration loading | Expected settings file absent from selected results; inspection identifies over-limit chunks |
| API query handler | Relevant handler ranked first |
| Expired cache entries | Relevant cache lookup ranked first; repeated results identical |
| Repository cloning/updating | Loader initialization led results; update/clone navigation requires inspection beyond the leading results |
| Cache callers | Cache path/lookup methods led results; conservative relationship metadata requires manual interpretation |
| Language-to-parser mapping | Parser initialization methods led results |

Three declared developer cases (configuration, API, cache) were evaluated with
repetition and captured as an immutable regression baseline. These observations
are not benchmark labels or quality scores. All repeated regression cases were
stable. Full evidence is external in `pilot-evaluate.json`, `pilot-regression.json`,
`diagnose-*.json`, `python-trace-*.json` and `python-context-*.json`.

Candidate `phase60-config-context` links to the configuration regression event,
proposes bounded `relationship_factor: 1.5`, and retains ownership, lifecycle,
validation and review history. It completed all checks but failed the regression
and duplicate-context gates: API duplicate context increased and the cache case
gained undeclared context. Stability, ranking review, trace compatibility and
diagnose compatibility passed. The descriptive configuration comparison recorded
gained context, which does not establish that the settings miss was fixed.

Review `review-a8cff9352e844928b7905a926e8220f3` remains pending. Promotion was
attempted without approval and correctly rejected. No candidate was accepted,
approved or activated. Recommended disposition is manual rejection or further
investigation; no automated decision is recorded.

## Confirmed defects and permanent regression

`diagnose` described the present settings file as deleted merely because its name
appeared in the previous index's file hashes and it was missing from retrieval.
The current index and unchanged source disproved that diagnosis. Removing that
fallback preserves explicit deletion checks and reports an existing omitted file
as not selected. The post-fix real query confirms the correction in
`diagnose-configuration-fixed.json`. Parser, chunker and research retrieval remain
unchanged; this fix does not make an over-limit symbol searchable.

`test_pilot_diagnosis_distinguishes_unselected_existing_file_from_deletion` uses
a sanitized temporary Git repository and a controlled empty result set. It checks
current/unselected versus stale/deleted diagnosis, unchanged index bytes, and
research isolation. The existing unsupported/stale/deleted regression also passed
alongside the digest regression (3 targeted tests, exit 0). No permanent test
depends on a real pilot checkout.

An auxiliary synthetic failure drill raised `MemoryError` while hashing valid,
large governance evidence during readiness replay. The developer reliability
digest helper previously allocated a complete formatted JSON string and byte
buffer solely for hashing. It now hashes that same representation incrementally.
The canonical formatting, final newline and SHA-256 values remain unchanged, so
existing journals and evidence references retain their digest contract. This
does not change lifecycle policy, approvals, source histories or runtime settings.

`test_pilot_evidence_digest_preserves_legacy_bytes_with_bounded_memory` compares
the digest with the legacy representation for nested Unicode evidence and measures
the allocation ceiling. It passed in the three-test targeted run. Large retained snapshots still
require memory for parsing and replay;
this correction does not promise unbounded lifecycle capacity or faster reports.
The initial 201-test developer baseline also encountered the same allocation
error in the complete readiness-chain case; its terminal result was 200 passing
tests and one error, with no assertion failures or skips.

## Failure drills and readiness

The real workspace records failed candidate validation, rejected promotion,
unsupported-language indexing/query, and incomplete readiness. Readiness reports
the mixed candidate outcome and missing deployment/decision links. It does not
create a deployment or close a lifecycle. CLI `readiness` and `readiness-audit`
returned exit 0 with findings; report success is distinct from lifecycle readiness.
`readiness-evidence`, `readiness-followup` and `readiness-close` returned exit 2
because no eligible readiness record exists. No closure was forced.
An independent before/after SHA-256 inventory also verified that the real
workspace's `readiness` and `readiness-audit` CLI reports changed no file;
the command results are retained in `readiness-readonly.json`. A separate
18-command CLI replay completed every expected exit status, including explicit
exit-2 rejections for promotion and the unsupported TypeScript repository.
The second validation again failed regression and duplicate-context gates;
review remained pending. CLI records and expected codes are external in
`cli-pilot-result.json` and `cli-*.json`.

The required full suite provides controlled synthetic drills without touching real
source. The external `failure-drills.json` maps each scenario to its completed
test evidence, expected detection, actual result, manual action and final state.

| Synthetic scenario | Regression evidence |
| --- | --- |
| Changed source, stale index, deleted symbols/files | Missing-context diagnosis and stale-query rejection |
| Invalid configuration and missing validation | Configuration transitions and deployment prerequisites |
| Deployment inconsistency | Live deployment governance and corrupt-link rejection |
| Expired assurance/readiness evidence | Operational readiness drift/expiry compatibility |
| Unresolved action and accepted/expired exception | Governance actions, deferrals and exception expiry |
| Conflicting governance records | Readiness missing/orphaned links and explicit decision selection |
| Incomplete recovery | Reliability plan validation and incomplete readiness |
| Stale readiness and attempted closure | Readiness review/evidence drift rejection |
| Complete chain, ownership, bundle, follow-up and closure history | Six existing Phase 59 operational readiness tests |

An independent controlled drill using a sanitized full-chain fixture also
completed with exit 0. Its `synthetic-drills/*.json` outputs retain the direct
diagnostics for expired assurance, unresolved action and stale readiness, expired
exception, incomplete recovery, deployment inconsistency, invalid bounded settings,
changed source/stale query and deleted symbol. Each audit asserted the copied test
workspace remained byte-for-byte unchanged. The only injected changes were made
to external fixture copies; no real pilot source or journal was repaired.

Synthetic tests explicitly exercise approval, activation and closure in temporary
workspaces. Their passing result is not a manual real-pilot approval, a recovery
execution, or a successful real-repository closure. The real pilot remains blocked.

## Findings and follow-ups

The developer-only findings record is external at
`C:\Apps\phase60-validation\pilot-findings.json`; each entry includes category,
behavior, expectation, reproduction, stage, severity, evidence and manual follow-up.
Historical follow-ups are retained in `pilot-findings-environment.json`,
`pilot-findings-digest-fix.json` and `pilot-findings-replay-cost.json`. The original
resource finding was subsequently confirmed as a digest allocation defect; its
original investigation status is preserved alongside the correction evidence.
Automatic approval review rejected recursive removal of disposable drill copies
with the reason "blocked by policy". Those copies remain external; the retry
uses hard links for unchanged synthetic records and detaches links before
corrupting evidence. No source or real pilot evidence is deleted.

| Finding | Classification | Follow-up |
| --- | --- | --- |
| Existing file falsely described as deleted | Confirmed diagnostic implementation defect; corrected | Retain sanitized regression and verify other selection misses |
| Full JSON allocation merely to hash evidence | Confirmed replay allocation defect; corrected | Retain legacy digest compatibility and bounded-memory regression |
| Configuration chunks exceed token limit | Observed indexing/context limitation | Inspect bounded context and consider a separately authorized developer-only enhancement |
| Candidate introduces API duplicates/cache context | Observed optimization/ranking limitation | Review or reject candidate; preserve baseline and validation |
| TypeScript-only repository cannot index/query | Unsupported repository structure | Use supported Python input; language expansion is future work |
| Real downstream chain lacks an eligible promoted candidate | Workflow limitation in this pilot | Obtain a valid candidate and human decisions in a subsequent cycle |
| Offline inference requires an existing pinned cache | Environment prerequisite | Supply the approved developer cache; do not infer research clearance |
| Concurrent broad validation exhausted memory | Environment limitation; initial runs retained | Run required suites sequentially and inspect final terminal results |
| Large nested evidence graphs have substantial replay/storage cost | Observed usability limitation; future enhancement | Investigate footprint separately; preserve histories and digest compatibility |

There is no evidence-backed reason to implement a new governance layer, change
frozen chunking contracts, relax validation, or automatically remediate findings.

## Validation and preservation

The targeted regression run completed 3 tests with `OK`, exit 0. The focused
`tests.test_developer_mode` run completed 203 tests with `OK`, exit 0, no skips,
failures or errors. The sequential full unittest discovery completed 347 tests
with `OK (skipped=2)`, exit 0: 345 passed, two environment cache skips, zero
failures and zero errors. The two skips require an unavailable optional
`EMBEDDING_MODEL_CACHE` and are unrelated to the pinned offline developer cache
used for this pilot. Terminal logs, exit codes and timings are external in
`targeted.log`, `focused-final.log`, `full-final.log` and the corresponding
`*-result.json` files. The pre-fix baseline finished with 201 tests, one
`MemoryError`, 200 passed and zero skips. Earlier overlapping focused/full
attempts and a later interrupted full run lacked terminal results and are not
counted as passes. The completed runs were sequential.

Phase changes are limited to the developer diagnostic and reliability digest,
their sanitized regressions,
this report and the CLI documentation. `final-preservation.json` verified all 294 pre-existing
tracked files outside the allowlist, both release tag identities, original pilot
file hashes, repository status and commits, `git diff --check`, and checkout
isolation. `failure-drills.json` links 12 synthetic scenarios to terminal test
results and direct diagnostics. `pilot-evidence-manifest.json` hashes 166 external
real-workspace JSON records; its candidate review is pending and real lifecycle
closure is false. Benchmark, Humanize, research
evaluation/retrieval, VERSION and release manifest must remain unchanged.

Completion requires a subsequent eligible real lifecycle with explicit human
approval, promotion, configuration/deployment decisions and readiness closure.
The present validation and check-in preserve an incomplete pilot honestly.
