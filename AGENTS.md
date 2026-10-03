# Local developer testing policy

Use this policy for future development phases in this checkout.

During development, run the directly affected test first, then the affected
component tests. Run `tests.test_developer_mode` when developer workflow behavior
is affected. Use `prototype local test --dry-run --changed` to inspect selection;
use `--test tests.MODULE.CLASS.METHOD` for the smallest reproduction. The default
`prototype local test` is T0, not a substitute for component or final validation.

Full discovery is a final gate only. Complete targeted tests, the developer suite
when applicable, and preservation checks before running once:

```text
python -m unittest discover -s tests -v
```

Never use full discovery as the normal development loop. If it fails, reproduce
the failing test independently, determine whether the change caused it, fix the
underlying issue, rerun that test and the appropriate focused suite, and only then
rerun the final full gate. A timing report supplies reproduction commands; it does
not automatically retry, repair, or suppress failures.

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

See [Phase 62](docs/research/phase62-developer-test-execution-optimization.md)
for tiers, selection limits, measured costs and command examples.
