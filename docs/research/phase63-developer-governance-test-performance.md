# Phase 63 — Developer governance test performance

## Status and scope

Phase 63 implements a developer-only, operation-scoped validated journal read
context. Work is limited to developer journal/readiness code, developer tests,
opt-in timing diagnostics, and this documentation. Research retrieval/evaluation,
benchmark/Humanize artifacts, `VERSION`, the release manifest and the v0.1.1 tag
are outside the change scope.

The repository began at `main`, HEAD `c08fe30b39ec8dedf6f42ebbe361c14d169f714f`,
clean and aligned with `origin/main`. The peeled v0.1.1 commit was
`51329285a882c1b7942d0a5b1c571e628d63dfb4`.

## Historical Phase 62 baseline

The existing Phase 62 evidence is used; T2 and T4 were not rerun to recreate a
baseline.

| Run | Phase 62 result |
| --- | ---: |
| Developer suite | 215/215 passed in 4489.695 s; no skips, failures or errors |
| Complete-chain closure/history | 1167.423 s in developer suite; 1072.698 s in full discovery |
| Drift/expiry compatibility | 1352.970 s in developer suite; 971.297 s in full discovery |
| CLI/manual outstanding items | 353.810 s in developer suite; 350.675 s in full discovery |
| Missing/orphaned links | 339.863 s in developer suite; 340.279 s in full discovery |
| Incomplete-chain transitions/follow-up | 123.020 s in developer suite; 128.153 s in full discovery |
| Full discovery | 385 tests, 383 passed, 2 environment-dependent skips, 0 failures/errors; 3986.838 s |

## Profiling correction and diagnostic method

An initial whole-test `--profile` / cProfile run for the complete-chain test was
manually interrupted after more than an hour. It stopped in readiness transition
→ audit → governance journal replay → source snapshot digest validation. It
produced no valid report and is not a performance measurement. The interruption
is a useful lead, not standalone proof of the final bottleneck. No orphan Python
worker remained after the interrupted run.

Whole-test cProfile is not used again. Instead,
[phase63_readiness_timing.py](../../tests/phase63_readiness_timing.py) is an
opt-in diagnostic that uses `time.perf_counter()` and aggregate wrappers. It
measures fixture stages, one explicit audit, per-module loads and `_apply`,
`_read` plus JSON decode, digest time/callsite, and nested checks. It writes only
counts, timings and shallow size estimates to a caller-supplied new external
report path; it does not emit journal contents. It is not a benchmark or a
productivity score. Diagnostic reports were stored under `C:\Apps\Temp\phase63`,
outside the checkout.

## Measured baseline and observed cost

On Windows Server 2022 / Python 3.14.7, one lightweight run measured full
`_operational_readiness_setup()` at 153.093 s. The lifecycle was genuinely built;
no mocks replaced the integration setup. The largest measured fixture stages
were governance decision/review work (60.091 s, including its nested decision
steps) and readiness creation (69.806 s, including its real audit). A separate
run measured 158.333 s for setup; an after-change diagnostic run measured
175.029 s. This variation and the fact setup instrumentation differs slightly
from the unittest wall time mean these are diagnostic stage measurements, not a
controlled fixture speed comparison. Since setup remains material, four
drift/gap/CLI/follow-up tests now lazily build one temporary validated lifecycle
seed and copy its workspace into each test's own temporary workspace. The seed
remains untouched; the complete-chain test still constructs its lifecycle from
scratch. The seed and per-test copies are external temporary state, never files
under the checkout. A measured suite-level fixture saving is pending the
required T2 run.

The baseline explicit audit took 53.025 s and reported 32 passed checks, 9
warnings and 0 blockers. Instrumented nested work included:

- 4,363 journal JSON reads / decodes, approximately 915 MB read cumulatively;
- 1,064 `reliability._digest()` calls, 35.885 s cumulative measured digest time;
- 183 deployment `_load()` calls, 124 configuration loads, 106 promotion loads,
  40 reliability loads, 39 continuity loads, 21 operations loads, and 21 assurance
  loads, in addition to the other source journals;
- 968 deployment replay `_apply()` calls and 372 configuration `_apply()` calls;
- governance close check once (15.917 s); strategic review twice (17.785 s total);
  evolution review three times (11.909 s); maturity review four times (8.574 s);
  deployment governance 42 times (3.060 s); reliability check 20 times (3.266 s).

Nested durations overlap and must not be summed. File byte totals include
repeated reads of the same journal and related governance evidence files.

## Implementation

`DeveloperReadContext` is created by each readiness audit and is attached only to
that read-only workspace facade. It has no global cache. Each first journal load
runs the existing loader, validates all event identities/transitions/digest
chains, and materializes state normally. Before reuse, the context rechecks the
journal directory and every event file's name, device/inode, size and timestamps;
changed identity forces a full reload and validation. A change during a replay
fails closed. Returned cached states are deep-copied so consumers cannot mutate
the validated context. Standalone public behavior is unchanged when no context is
present. New readiness audits get new contexts; appends cannot reuse a previous
operation's state.

Context propagation is preserved across read-only workspace facades. The
operation-scoped load decorator covers readiness, promotion, configuration,
deployment, operations, reliability, continuity, assurance, recovery governance,
assurance operations, maturity, evolution, strategic governance, and governance
decisions. Governance snapshot digest reuse is limited to one context: a
canonical-value fingerprint must match before reuse, and the cached digest is
stored only after matching the journal's expected SHA-256. Tampered snapshots
continue to fail validation.

## Initial before/after audit diagnostics

The post-change lightweight audit was measured at 43.671 s in the digest-cache
instrumentation run (a preceding scoped-state-only diagnostic was 50.235 s).
Compared with the 53.025 s baseline, the first run is about 17.6% lower, but this
is a single diagnostic sample on a variable Windows workload, not a stable
benchmark claim. Both audits returned 32 passed, 9 warnings and 0 blockers.

The scoped context reported 449 cache hits across the journal loaders, with one
validated replay per journal (including the readiness history); the direct
source journal requests were 106 promotion, 124 configuration, 163 deployment,
21 operations, 40 reliability, 39 continuity, 21 assurance, 18 recovery
governance, 9 assurance operations, 4 maturity, 6 evolution, 4 strategic
governance and 1 decisions. The first validated replay counts were 3 promotion,
3 configuration, 4 deployment, 2 operations, 2 reliability, 3 continuity, 3
assurance, 3 recovery governance, 2 assurance operations, 7 maturity, 2 evolution,
3 strategic governance, 4 decisions and 1 readiness event. In the baseline these
loads replayed 183 deployment and 124 configuration journal copies (968 and 372
`_apply()` calls respectively).

The digest instrumentation run observed 290 digest calls versus 1,064 in the
uncached audit. Cumulative timed digest work was 24.153 s versus 35.885 s. A
single governance snapshot digest was reused after canonical value fingerprint
comparison; the large savings principally accompany avoiding repeated journal
replay. Nested live checks (for example governance close checks and reviews)
remain expensive.

The exact complete-chain test passed unprofiled in 1089.875 s, compared with the
Phase 62 developer-run baseline of 1167.423 s (77.548 s / 6.65% lower). It is
not lower than the historical full-discovery run of 1072.698 s, so no comparable
T4 claim is made. The drift/expiry test passed in 771.917 s versus 1352.970 s in
the Phase 62 developer run (581.053 s / 42.9% lower). Its lightweight test-body
diagnostic measured 652.583 s (fixture setup is excluded in that mode) and
recorded 13 real audit invocations totaling 554.671 s (36.302–49.822 s each);
some calls execute under deliberate dependency-failure patches in the test.
This confirms that the test repeatedly executes live audits rather than reusing
one audit result. Do not compare this 13-audit sum directly with the single-audit
microdiagnostic: their scope and wrappers differ.

Prepared-seed test timings after the fixture change were 270.335 s for the CLI /
manual-items test (Phase 62: 353.810 s; reduction 83.475 s / 23.6%) and
118.864 s for missing/orphaned-links/read-only isolation (Phase 62: 339.863 s;
reduction 220.999 s / 65.0%). Focused cache integrity, atomic append/corruption
and incomplete-chain tests passed in 0.276 s, 0.425 s and 91.443 s respectively.
These test-level timings include each test's own actions and audits; fixture
construction was shared once within that worker, then its temporary workspace
was copied into a private per-test workspace. The prepared source remained
unchanged.

These are focused same-host, same-interpreter runs, but fixture preparation and
timing wrapper scope differ from historical aggregate suite measurements.
Treat them as targeted evidence, not a claim about the entire developer suite.
Full T2 and T4 gates passed:

- T2 developer component: 216/216 passed, 0 skipped/failures/errors, 3182.077 s.
- T4 full discovery: 386 run, 384 passed, 2 environment-dependent skips,
  0 failures/errors, 3336.060 s. The two existing skips require the unavailable
  `EMBEDDING_MODEL_CACHE`; no skip was added by Phase 63.

## Integrity and test architecture

The complete-chain test retains its real construction and now compares the
legacy uncached audit result with the scoped-context result (excluding only the
report generation timestamp). A focused test verifies detached cached values,
append invalidation, modified digest and sequence rejection, missing middle-event
rejection, recovery after restoring the journal, and governance source snapshot
tamper rejection. Existing atomic-write, history-preservation, ownership,
stale-evidence, drift/expiry, orphan, external-workspace-isolation and journal
corruption assertions remain in place. No test was removed, weakened or skipped.

The first measured drift diagnostic failed because its wrapper replaced the
public audit entry point instead of the private implementation. An independent
targeted invocation also exposed that the prepared-fixture setup was rebuilding
lifecycle state; both seams were corrected before the final passing diagnostic
and the 771.917 s runner test above. Failed diagnostic attempts are not counted
as passing evidence.

The CLI/manual readiness test already performs one real audit and patches that
immutable report only for its later parser/dispatch/manual-decision checks; the
drift/expiry tests retain real audits. No generated or prepared runtime state is
stored in the checkout.

## Limits and remaining work

The context only helps within one synchronous logical audit. It does not persist
between separate CLI commands, readiness mutations, or audit calls; fresh audits
remain necessary to detect source drift, expiry, corruption and ownership changes.
It uses filesystem identity metadata as a reuse guard; writers that alter content
while defeating all identity metadata are outside the supported local filesystem
assumptions. Promotion candidate/review inventories and the optimization health
scan have different storage shapes and remain independently inspected. Digest
and nested review work not associated with repeated journal replay remains a
cost center. No append serialization/deepcopy/fsync optimization is made.

Testing uses the Phase 62 tier policy: focused targeted tests first; T2 developer
suite only when the changed-file planner requires it and after affected tests are
green; T4 full discovery once at the final gate. Whole-test cProfile is expressly
not used.
