# Support

This is a solo-research software prototype, not a production service. Support is limited to installation, the documented CLI, local run tracking, and reproducing behavior covered by the test suite. There is no service-level agreement or guarantee of compatibility with every operating system or dependency set.

## Before reporting a problem

1. Check the [release guide](docs/research/release-guide.md), [CLI guide](docs/research/prototype-cli.md), and [configuration guide](docs/research/prototype-configuration.md).
2. Record the release/tag, Git revision, Python and OS versions, command used, and `python -m pip check` output.
3. Include a minimal error message and relevant test result. Redact usernames, local paths, credentials, source text, query text, and any source-derived data.
4. Report whether the command used the pinned offline model cache. Do not attach a model cache, corpus checkout, run directory, index, or raw benchmark material.

## Known boundaries

- `prototype demo` and `prototype evaluate` are generated-fixture smoke paths, not retrieval-quality claims.
- `prototype validate` requires already-acquired, authorized, pinned local checkouts; missing inputs are reported as not ready and are never fetched.
- Model-backed behavior requires the pinned optional dependency set and an externally managed model cache.
- Humanize remains frozen; benchmark expansion is deferred. No benchmark questions, retrieval algorithms, or evaluation methodology may be changed as part of a support report.

Security or privacy concerns should not be reported with raw secrets, source files, annotations, or logs. Share only redacted diagnostics through an appropriate private channel.
