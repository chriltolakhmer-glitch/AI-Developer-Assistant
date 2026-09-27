# Phase 19.8 - Supersession notice

**SUPERSEDED — replaced by lightweight thesis workflow**

Effective 2026-09-27. Use the [lightweight thesis workflow](thesis-benchmark-workflow.md) as the current operational reference. The original document below is preserved as historical evidence, including its prior decisions, unresolved findings and phase-specific statuses. Its approval chains, mandatory forms/signatures/reviewer assignments, expansion quotas and unused-candidate closure tasks are no longer active requirements. Supersession does not assert that historical safety issues were resolved or authorize source processing, new annotation, evaluation or release.

## Historical document (unchanged)

# Phase 18.2 — Benchmark Freeze and Release Gate

> **Superseded as the active release workflow by Phase 18.4.** This document is retained as historical design evidence. Use [Gate 4 in the simplified workflow](benchmark-research-workflow-final.md) for the current proportional dataset freeze/release decision. This does not waive repository/privacy approval, permit external distribution, or authorize execution. Humanize remains frozen.

**Date:** 2026-09-27  
**Status:** Proposed release-control procedure; **no freeze, evaluation, or release is authorized**.  
**Boundary:** Documentation only. No benchmark package is created. Humanize remains frozen; no repository or question is added and retrieval code is not modified.

## Purpose and authorities

This document separates benchmark freeze from retrieval-evaluation authorization and from public/internal release. It supplements the [Phase 17 protocol](benchmark-expansion-protocol.md) G4–G6 rules and [Phase 17 checklist](benchmark-expansion-checklist.md), and uses the [Phase 18 quality gates](benchmark-quality-gates.md), [Phase 18.1 gate review](benchmark-expansion-gate-review.md), and [Phase 18.2 finalization proposal](benchmark-expansion-protocol-finalization.md). It does not close any gate or substitute for the [G0 authorization record](benchmark-expansion-g0-authorization.md).

## Gate map

| Gate | Decision | Required accountable parties | Effect of approval |
|---|---|---|---|
| G0 | Accept versioned protocol/scope and authorize one bounded next activity | Benchmark owner; required independent reviewers | Only the named activity. No candidate clearance unless explicitly within approved scope; no annotation/evaluation/release implied. |
| G1 | Clear exact candidate snapshot and activity | Data/privacy steward, license reviewer, benchmark owner | Only approved local snapshot/inventory preparation for that candidate; no annotation. |
| G2 | Accept annotation readiness and access controls | Annotation lead, evaluation custodian | Manual annotation in isolated staging for exact approved allocation only. |
| G3 | Accept completed review and validation | Independent review lead, validation owner | Preparation of a freeze package; not freeze or evaluation permission. |
| G4 | Freeze a separately versioned benchmark before evaluation | Benchmark owner with independent review sign-off | Immutable benchmark freeze only; no retrieval run or distribution permission. |
| G5 | Approve a sealed retrieval evaluation plan | Evaluation custodian, experiment owner | Only predeclared runs on the approved frozen identity. |
| G6 | Approve artifact distribution/release and audience | Benchmark owner, data steward | Release of only the named artifacts to the named audience. |

## G4 — pre-evaluation freeze requirements

G4 can be considered only after G0–G3 pass for the same version and exact scope. The freeze package must be separate from the pilot and preserve:

- canonical benchmark payload and category-map digests, plus private-ledger digest for metadata not carried by schema 1.0;
- exact repository/commit map, snapshot and inventory manifests/digests, eligible/excluded-file contract, and any approved limitations;
- annotation ledger, independent initial reviews, correction/adjudication history, agreement report, exposure/split manifest and access-control record;
- protocol, schema, rubric, validator/freeze-tool versions, inputs/outputs, any exact supplemental validation allowance, and G0–G3 decision references;
- freeze timestamp, accountable owner, immutable retained bytes and verification results, and prior-version reference.

**G4 pass:** all required approved slots are complete; independent review is 100% complete and final; thresholds pass; evidence is source-resolved; zero unresolved validation, clearance, provenance, exposure, or disagreement issue remains; expected digests verify; prior benchmark and Humanize pilot hashes remain unchanged; benchmark owner and independent review lead record an attributable freeze decision.

**G4 fail/hold:** any missing decision/evidence, changed digest, incomplete target, open dispute, unresolved clearance issue, validator invariant failure, pilot modification, or exposed blind material blocks freeze. Return to the earliest failed gate in isolated staging. Never freeze a partial batch as final, alter a frozen artifact in place, or bypass existing 108/9 tooling invariants to freeze a changed target. The proposed 8/96 scope in the [independence plan](benchmark-independence-plan.md) is not active unless versioned, approved, and supported by separately approved/tested tooling.

## G5 — evaluation authorization boundary

G4 does not authorize retrieval evaluation. Before G5, custodian and experiment owner must approve and pin the exact frozen identity; repository-level split/access; code/configuration/model/runtime/seeds/hardware; task and common candidate universe; eligibility denominators; metric formulas/cutoffs/tie rules; failures/uncertainty; handling/compute; trace tolerance; and two fresh-process repeatability procedure. Evaluation is blocked if blind labels have leaked, primary complete-inventory eligibility is below 100%, metrics are incompatible, or system/configuration identity is incomplete. Any run requires its own attributable G5 decision. This Phase 18.2 document authorizes no run.

## G6 — release authorization requirements

G6 is a separate distribution decision and may be considered only for the exact G4 version and, where evaluation is in scope, accepted G5 evidence. Required evidence:

1. validation/evaluation reports with fixed denominators, failures, repository/category/difficulty/partition/task strata, limits, and no unsupported generalization claims;
2. data/privacy and license/notice approvals for each artifact and audience, including separate decisions for derived records, external reviewers, and raw benchmark/source distribution;
3. release manifest with artifact identities/digests, version, audience, allowed use, responsible owner, and access route;
4. verified retained digests and intact prior versions/pilot;
5. named incident/rollback owner, withdrawal contact, prior approved release reference, and tested withdrawal/restore readiness;
6. signed G6 decision from the benchmark owner and data steward, recording date, evidence location/digests, conditions, and exact artifact set/audience authorized.

Default committed output is limited to approved aggregate metadata and digests. Raw questions, gold labels, paths/spans, inventories, source text, detailed scan results, or reviewer records remain in controlled storage unless individually authorized for distribution. A benchmark freeze, public upstream license, successful retrieval metric, or prior risk acceptance is not by itself distribution permission.

## Rollback, withdrawal, and correction

Stop and withhold release on any clearance incident, integrity/provenance mismatch, changed scope, leakage, unresolved gold/review issue, threshold failure, nonreproducibility, incomplete rights, or rollback failure. Before release, quarantine the candidate version and return to the earliest failed gate. After release, withdraw the affected release, invalidate dependent results, retain only permitted audit evidence, and restore a previous reference only if its digest and clearance remain valid. Corrections require a new version and renewed affected review/validation/freeze/evaluation approvals. Never overwrite or “repair” the Humanize pilot.

Low retrieval scores alone are not a release-gate failure for a valid benchmark; they are reported as results. They do not justify removing hard cases or revising gold labels.

## Current disposition

- **G4 freeze:** not started, not approved.
- **G5 retrieval evaluation:** not started, not approved.
- **G6 release:** not started, not approved.
- **Phase 19:** not authorized.
- **Humanize:** frozen, pilot-only.

All future approval fields require named human decision-makers and attributable evidence. This document is not a gate decision.

## Existing references

- [Phase 17 protocol](benchmark-expansion-protocol.md) and [checklist](benchmark-expansion-checklist.md)
- [Phase 18 quality gates](benchmark-quality-gates.md), [expansion plan](benchmark-expansion-plan.md), and [candidate registry](benchmark-candidate-registry.md)
- [Phase 18.1 review](benchmark-expansion-gate-review.md) and [readiness checklist](expansion-readiness-checklist.md)
- [Phase 18.2 protocol finalization](benchmark-expansion-protocol-finalization.md), [G0 authorization record](benchmark-expansion-g0-authorization.md), and [independence plan](benchmark-independence-plan.md)
- [Phase 9 benchmark finalization contract](benchmark-finalization.md) and [Phase 16 Humanize closure](../../../../Temp/Phase8/benchmark/pilot/python-humanize/humanize-pilot-closure-report.md)
