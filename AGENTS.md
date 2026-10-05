# Local developer testing policy

Use this policy for future development phases in this checkout. Validation has
three distinct purposes: repeated development feedback, one phase-completion
gate, and optional or risk-required exhaustive acceptance.

During development, run the directly affected method first, then the affected
component tests. Use `prototype local test --test tests.MODULE.CLASS.METHOD` for
the smallest reproduction and `prototype local test --changed --dry-run` to
inspect static changed-file selection. The default `prototype local test` is T0
feedback; it is not phase-completion evidence.

For normal phase completion, run exactly one changed-file phase gate:

```text
prototype local test --gate phase
```

It selects affected test modules and adds the fast safety modules. It may complete
without full discovery when mapping is known and the selection is smaller than the
complete inventory. Do not mechanically run the full developer module and then
full discovery. If the phase gate itself escalates to exhaustive discovery, that
single execution is the completion and exhaustive gate.

Exhaustive acceptance is available as `prototype local test --gate exhaustive`
or the direct command `python -m unittest discover -s tests -v`. It is mandatory
for release/milestone acceptance, test runner or dependency mapping changes,
package initializers, governance/readiness core, journal/storage and shared
configuration/serialization changes, dynamic loading, unknown or unsupported
mapping, a change touching three or more distinct `src` package roots, or an
explicit exhaustive request. Unknown selection always escalates; it never reduces
coverage. Static AST mapping follows
relative and function-local imports but cannot prove dynamic imports, plugin
loading, external services or arbitrary non-Python dependencies. Review those
limits and use the stronger gate when relevant.

T2 remains useful for debugging, failure localization, a focused developer
workflow change, or when developer integration coverage is the affected gate and
exhaustive discovery is not required. It adds no coverage when immediately
followed by exhaustive discovery because `tests.test_developer_mode` is included
in full discovery. A timing report supplies reproduction commands; it does not
automatically retry, repair, or suppress failures.

If a gate fails, reproduce the failing test independently, determine whether the
change caused it, fix the underlying issue, and rerun the target plus the
appropriate affected validation. Rerun exhaustive acceptance only if it was
required by policy or the fix changes its risk/coverage basis; do not rerun a
complete suite as ritual duplication.

For replay-heavy operational-readiness/governance integration tests, do not wrap
an entire slow test or suite in `--profile`/cProfile. Use unprofiled targeted
timing and, where internal attribution is needed, opt-in `perf_counter()` stage
diagnostics with outputs outside the checkout. Profile only a narrowly bounded
function after lightweight measurements establish it as the bottleneck.

Do not delete tests, weaken assertions, change expected results to get a pass,
convert tests to skips, or permanently disable expensive tests. Missing runtime
dependencies are errors. Existing environment-dependent skips must be reported
separately. Record duration, counts, exit status and environment limitations, and
retain the terminal unittest `Ran` and `OK`/failure evidence. An interrupted run
is incomplete, never a pass.

Generated logs, reports, timing records, model caches and bytecode caches belong
outside this checkout. Use `PYTHONDONTWRITEBYTECODE=1` (or Python `-B`) for test
runs and an external new path for `--report`. Do not change research evaluation,
research retrieval methodology, benchmark datasets, Humanize/frozen artifacts,
`VERSION`, `release-manifest.json`, or the `v0.1.1` tag as part of developer test
optimization. Verify `git diff --check`, intended paths and protected identities
before the final gate and check-in. Existing dirty changes remain separately
attributed; do not include unrelated changes in the phase commit.

See [the test-gating architecture redesign](docs/research/test-gating-architecture-redesign.md)
for gate semantics, selection limits, risk rules and the evidence behind this policy.
