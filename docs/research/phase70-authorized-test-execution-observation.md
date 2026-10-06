# Phase 70 — Authorized Test Execution and Observation

## Post-roadmap pilot-readiness integration

For drafts linked to a validated Phase 65 plan, Phase 70 uses that plan's exact expected-test identities. Omitting `--test` runs the bound set; specifying `--test` is accepted only when the complete explicit set equals the bound set. Missing or changed identities stop before the worker starts. The approved allowed paths may exceed the patch paths, while Phase 69 observed paths must equal the actual patch paths. Older direct test fixtures without a linked plan retain their legacy selection behavior.

## Purpose

Phase 70 executes a bounded Python `unittest` selection after one exact Phase 69 patch application and records what the process reported. It does not decide whether the change is correct. The AIDA development gate validates this feature; a target repository observation is separate evidence about the applied target source.

## Architecture boundary

The flow is Phase 65 plan → Phase 66 `ProposedAction` → Phase 67 `PatchDraft` → Phase 68 human approval → Phase 69 exact application → explicit Phase 70 invocation → immutable observation and external logs → stop. Test outcomes do not trigger repair, retry, rollback, lifecycle closure, or Phase 71 verification.

## Explicit human authorization

Phase 68 grants only `apply_exact_patch`. The developer explicitly authorizes one bounded test plan by invoking `prototype local test-applied-patch`. Phase 70 requires the exact Phase 69 run ID; it never chooses the latest run. The invocation authorizes only the exact selected identities in the recorded deterministic plan.

## Phase 69 binding

Before launch, Phase 70 verifies the canonical Phase 69 run record and its content-derived identity, successful status, Phase 68 approval, Phase 67 draft, action/patch/authorization/repository bindings, patch hash, target paths, HEAD, index-independent source inventory and the exact Phase 69 working-tree diff. The current Git status paths must still be exactly the Phase 69 target paths. A stale or mismatched state returns an error containing `TEST NOT EXECUTED`.

## Test selection

The default uses Phase 62 `developer_testing.plan(..., changed=True)` for Phase 69 actual changed paths and the existing static dependency mapping. Exact user selectors may be repeated with `--test`; they must match the existing test catalog as full unittest method identities. Unknown, partial, malformed and executable-like inputs are rejected. Selection and scope are rechecked before starting the worker.

## Supported runner

The only runner is `python -m unittest`, invoked through a fixed internal worker with the current Python interpreter, `-B`, and a validated identity list. The worker loads only those exact identities and verifies unittest did not expand or alter the set. No shell, command string, executable path, pytest fallback, dependency installation, network access, or model call is used.

## TestExecutionPlan

The immutable plan records the deterministic plan ID, source execution, repository ID/path/state, Phase 69 target paths, runner, exact identities, selection source, changed test files, and selection tier. Its identity is stable for the same source execution, repository state, runner, and test identities.

## TestExecutionObservation

The immutable observation records unique observation ID, source Phase 69/68/67/66 identities, repository identity and before/after source state, runner and exact tests, timestamps and duration, exit code, run/pass/failure/error/skip counts, fact-only status (`passed`, `failed`, or `error`), external stdout/stderr paths and SHA-256 values, and unexpected repository-change details. A passing test observation is not Phase 71 verification.

## stdout/stderr evidence

Test stdout and stderr plus unittest runner output are stored under the external DeveloperWorkspace `evidence/<observation-id>/`. The run record stores paths and hashes, not unbounded log contents. No test logs are written into the target repository by Phase 70.

## Repository-state protection

The worker runs in the target repository using `PYTHONDONTWRITEBYTECODE=1`. Phase 70 snapshots HEAD, semantic Git index entries (`git ls-files --stage -z`), refs, Git status including untracked and ignored entries, and the AIDA Python-source inventory immediately before and after execution. It reports path/state changes, source changes, ignored-file changes, and Git changes. Git's refreshable physical index stat cache does not count as staging. Phase 69 and Phase 70 share the semantic index helper; staged object/mode/stage/path changes do count. Phase 70 never stages, commits, resets, cleans, or restores the target repository.

## Test side-effect detection

New or modified tracked, untracked, ignored, Python-source, index, ref, or HEAD state is reported in `unexpected_repository_changes` and `unexpected_changed_paths`. The artifact is left in place for human review. These observations do not claim full operating-system sandboxing: a unittest has the same local-user privileges as the invoking developer.

## Failure semantics

Assertion failures are `failed`; unittest loading/runtime errors and invalid worker protocol are `error`; skips remain separately counted and do not convert a zero-exit run into a failure. A failing result leaves the Phase 69 patch intact. Phase 70 neither retries nor repairs code, changes tests, rolls back the patch, makes a commit, nor performs a lifecycle transition.

## CLI

```text
prototype local test-applied-patch REPOSITORY --execution-run-id RUN [--test tests.module.Class.test_method] [--workspace PATH] [--json]
```

With no `--test`, deterministic changed-test selection is used. Supply one or more exact, catalogued unittest method IDs to select explicitly. The command returns a stable machine-readable `developer-local-test-observation` payload in JSON mode.

## External storage

Plans and observations use the existing external DeveloperWorkspace run records. Log files live in the workspace evidence directory. The workspace isolation checks reject overlap with the AIDA checkout, target repository, and configured protected research roots.

## Validation

The focused module exercises successful Phase 69 prerequisites, passing/failing/error/skipped outcomes, exact selectors, rejected unknown identities and executable-like strings, stale state, another repository, tampering, repeat observations, log containment, side-effect detection, and no commit/staging/rollback. Direct Phase 69 patch-application and authorization regressions are run separately. AIDA’s Phase completion gate validates Phase 70 implementation behavior; target observations do not replace that gate.

## Pilots

The full passing and stale-state pilots used separate disposable Git repositories and external DeveloperWorkspaces under `C:\Apps\phase70-validation\phase65-70-pilot-20261005-235225`. Both completed a current Phase 65 plan, Phase 66 proposal, Phase 67 validated draft, Phase 68 approval, and Phase 69 application. A deterministic local fake embedder populated only each disposable pilot's external index; Phase 65 retrieval was stubbed because the pinned model cache was unavailable. The real Phase 65 source/change/test planning, Phase 67 checks, Phase 68 binding, Phase 69 application, and Phase 70 worker were exercised. No model was downloaded. The passing target test ran once, and its structured observation and stdout/stderr were external; the patch, HEAD, and semantic index remained unchanged. In the stale pilot, target source was changed after Phase 69; Phase 70 returned `TEST NOT EXECUTED`, and a marker confirmed the target test never started. Focused tests also cover a failing target test with no repair, retry, rollback, or commit, and an unexpected file left visible. No Phase 71 verdict was produced.

## Limitations

Only Python `unittest` is supported. The worker uses the local Python interpreter and installed environment without installing dependencies. Test processes are bounded by exact identities but are not OS-sandboxed. Git status and source-state inspection may not reveal every non-Python generated artifact that a test writes outside Git’s reportable repository scope.

## Deferred work

Phase 70 does not interpret correctness, issue a verification verdict, approve or close a lifecycle, plan repairs, decide rollback, commit, or deploy. A passing test observation is not yet Phase 71 verification.

## Source symbol evidence

Phase 70 carries the Phase 69 actual and observed symbol records through its validated execution binding. No runtime symbol instrumentation is added: these records describe static source-patch scope only.
