# Phase 65 — Evidence-Grounded Implementation Planning

## Post-roadmap pilot-readiness integration

For a clean Git checkout, the plan now binds existing exact `unittest` method identities from static import paths between planned Python targets and the test catalog. `tests.expected_test_selection` records the identities, source paths, selection source, confidence, and uncertainty. A developer can instead bind one or more existing exact methods with repeatable `--expected-test tests.module.Class.test_method` arguments. Unknown methods are rejected. If no relevant exact tests can be identified, the plan records `expected_tests_unknown`, requires a human test decision, and cannot become an approvable patch draft. Static import evidence does not establish runtime coverage. The selected identities are preserved for Phase 70 and compared again in Phase 71.

The developer index and pinned real model are required for current goal-retrieval evidence. A narrow `--top-k` can reduce duplicate retrieved context in a small project, but omitted required context remains visible and blocks patch drafting; it is not silently discarded.

## Outcome

Phase 65 adds a developer-only, read-only command that converts existing repository evidence into a deterministic implementation plan:

```powershell
prototype local plan-change REPOSITORY --goal "Add validation to the login token flow"
prototype local plan-change REPOSITORY --workspace C:/work/developer-workspace --base HEAD~1 --goal "Improve stale-index errors" --top-k 10 --json
```

The command does not modify source, draft patches, run tests, rebuild an index, use a network LLM, change governance state, or deploy anything. It may write its run record beneath the separate developer workspace. Phase 64 change-impact orchestration remains the source of Git, symbol, relationship, freshness, retrieval, and Phase 62 affected-test evidence.

## Evidence model

The stable `developer-local-implementation-plan` payload keeps these sources distinct:

- `developer_goal`: the supplied goal, used as the Phase 64 retrieval question.
- `changed_code`: parsed symbols in changed Python files.
- `static_relationship`: resolved parsed-source calls, imports, callers, members, and configuration references. These do not prove runtime execution.
- `retrieval_evidence`: direct results from a current developer index only.
- `additional_related_context`: current relationship-expanded retrieval context.
- `test_selection`: the unchanged Phase 62 affected-test plan.
- unresolved evidence: ambiguous relationships, unsupported files, parser failures, token exclusions, omitted context, missing or stale indexes, and runtime limits.

Every implementation target carries its file/symbol location, descriptive role, evidence types, reasons, relationship references, change status, current-index marker, and unresolved notes. A changed symbol must intersect the goal evidence; merely sharing a file or container with a change does not make it a target. Resolved relationships expand the target set by one goal-relevant hop and ambiguous edges never become dependencies. Roles are `primary_target`, `supporting_target`, `test_target`, `configuration_target`, `related_context`, or `manual_review`; no risk, productivity, quality, or confidence score is calculated.

## Planning behavior

A clean repository with a current index can identify proposed targets from goal retrieval and related context while reporting `current changes: none`. Existing changes remain separately classified as `already_changed`; unchanged relationship or retrieval targets are `unchanged_but_related`, tests are `test_coverage`, and configuration-sensitive symbols are `configuration_dependency` in their supporting evidence.

`preserved_behavior` is conservative. It reports only parsed source relationships, configuration references, and existing related test evidence. `implementation_steps` order inspection, the narrowest evidenced change boundary, contract review, focused regression review, and validation. `tests_to_update_or_review` distinguishes tests to run from tests to inspect and possible new regression cases; selection never implies that a test must be edited.

Validation is planned, never executed: exact changed/added tests first, then directly affected modules, T2 only when required, T3 only for an affected expensive subsystem, and T4 as the final gate.

## Freshness and fail-closed behavior

Goal retrieval and relationship-expanded retrieval are planning evidence only when the active index is current. A stale or missing index yields an explicit limited or manual-review plan, retains valid Git/static/test evidence, and recommends `prototype local index REPOSITORY`; it never reindexes or downloads a model.

Unsupported-language goals, ambiguous relationships, and goals with no meaningful repository evidence do not invent Python targets. They surface individually in `unresolved_evidence` and degrade to `limited` or `manual_review_required`. Dynamic imports, generated code, dispatch, and actual runtime behavior always require human validation.

## Stable output and external records

JSON contains `mode`, `status`, `goal`, `repository`, `change_impact`, `implementation_targets`, `preserved_behavior`, `implementation_steps`, `tests`, `tests_to_update_or_review`, `recommended_validation`, `unresolved_evidence`, `limitations`, and `run_id`. It embeds references and evidence, not full source files. Human output presents the same information as terminal sections rather than dumping JSON structures.

The planner and its composed Phase 64 analysis write only immutable run records under `WORKSPACE/runs`. The source checkout remains read-only during planning. Developer records remain separate from research data, benchmarks, Humanize, and release artifacts.

## Validation coverage

Focused tests exercise clean goal retrieval, modified symbols, validation/error handling, imported helpers, configuration-controlled behavior, ambiguous relationships, stale and missing indexes, unsupported TypeScript, no-evidence goals, JSON and human output, provenance, test-plan reuse, ordered validation, external storage, and source preservation.

The real-project pilot uses the bounded goal “Improve the error message when change-impact retrieval is blocked by a stale index.” Its run record and any index stay in an external developer workspace. The pilot plans only; it does not implement the goal.

## Boundaries

The immutable `v0.1.1` research release baseline is unchanged. Research retrieval/evaluation, benchmark artifacts, Humanize, `VERSION`, and `release-manifest.json` remain outside Phase 65. The pending `phase61-dependency-context-v5` review is not approved, rejected, activated, deployed, or otherwise changed by planning evidence.

Phase 65 does not modify code. A later phase may investigate controlled patch drafting only after this implementation-planning workflow is validated.

## Symbol-scope contract

Phase 65 target evidence binds allowed symbols as canonical path-qualified `(file_path, qualified_symbol)` pairs. Flat `target_symbols` remain descriptive only. The reserved `<module>` sentinel represents module-level changes and cannot collide with a Python identifier; it is authorized only by an explicit Phase 65 evidence reference.
