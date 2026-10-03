# Phase 64 — Change-aware developer assistance

Status: implementation, validation, and preservation checks complete. The
retained evidence below records the final affected-suite and full-gate results.
This is a developer-only integration workflow, not a new governance, retrieval,
or test-selection subsystem.

## Scope and boundaries

`prototype local change-impact REPOSITORY` combines rename-aware Git change
detection (including staged, unstaged, deleted, and untracked paths), existing
inspection/change diagnostics, Python parser/context metadata, index freshness,
optional retrieval, and Phase 62 test selection. It reuses
`developer_testing.plan(...)` rather than duplicating test-selection rules. It
may write developer run evidence only under the external developer workspace;
it never edits, stages, commits, or executes application source, automatically
reindexes, or runs tests. It never approves, activates, deploys, recovers, rolls
back, or closes governance state.

The immutable v0.1.1 research release, research retrieval/evaluation,
benchmarks, frozen Humanize artifacts, `VERSION`, and `release-manifest.json`
remain out of scope. The external review for successor
`phase61-dependency-context-v5` remains pending human decision. Phase 64 results
do not approve or reject it.

## Command contract

```powershell
prototype local change-impact C:\work\repository
prototype local change-impact C:\work\repository --base HEAD~1
prototype local change-impact C:\work\repository --question "What code handles login?" --top-k 10
prototype local change-impact C:\work\repository --workspace C:\DeveloperWorkspace --json
prototype local change-impact C:\work\repository --workspace C:\DeveloperWorkspace --base HEAD~1 --question "What code handles login?" --top-k 10 --json
```

The CLI accepts `--workspace PATH`, `--base COMMIT`, `--question TEXT`,
`--top-k N` (default 10, range 1–50), and `--json`. `--top-k` controls optional
retrieval requested with `--question`; it does not change test planning.

The default comparison is the current working tree against `HEAD`. `--base`
compares against the verified commit reference and also retains current staged,
unstaged, deleted, renamed, and untracked changes. Dirty/clean status describes
the current working tree even when a base comparison contains committed changes.

The human report groups repository/freshness, changes, affected symbols,
potential static impact, unresolved relationships, optional retrieval, affected
tests, uncertainty, and next actions. The stable JSON top level contains:

```text
mode, repository, changes, symbols, relationships,
unresolved_relationships, index_freshness, retrieval, tests,
recommended_actions, limitations, evidence_sections, run_id
```

No full source bodies are copied into the report. Symbol rows keep file, qualified
name, entity type, source range, change type, imports, parsed calls, and
configuration references. Relationships use exact file identity and existing
Phase 61 parser evidence. Ambiguous same-name targets stay unresolved; no missing
edge is invented. Relationship wording is explicitly static and does not claim
runtime execution.

## Freshness and retrieval

Freshness is one of `current`, `stale`, `missing`, or `unsupported`. Stale reports
name the differing Python sources. Optional `--question` retrieval runs only
against a current matching index and preserves ranking/context reasons. Stale or
missing retrieval is blocked and recommends an explicit `prototype local index`
command. The workflow does not reindex or download a model automatically.

Evidence remains separated as:

1. changed code;
2. conservative static relationships;
3. retrieved query results;
4. additional relationship-expanded context.

## Affected-test planning

The command calls `src/developer_testing.py::plan` with the same repository,
changed-worktree mode, and optional base. It returns selected test identities and
modules, tier, intentionally unselected tests, diagnostics, uncertainty, and
required follow-up. The payload always records `executed: false`. Syntax or
mapping uncertainty is visible and falls back to manual review and the T4 final
gate; it never causes implicit execution.

## Validation record

Focused coverage is in `tests.test_change_impact` and exercises clean, staged,
unstaged, untracked, deleted, and base-relative changes; symbol and conservative
relationship expansion; ambiguity; unsupported/configuration files; current and
stale indexes; retrieval evidence separation; affected-test planning; no test
execution; JSON/human output; external workspace isolation; and source
preservation.

Real-repository validation uses an authorized temporary Python Git repository
outside the source checkout. It covers clean, modified function, added/deleted
Python files, import/dependency change, configuration change, unsupported
TypeScript, and stale-index scenarios. Generated indexes, run records, logs, and
temporary repositories remain external.

Validation followed `AGENTS.md`: exact Phase 64 tests, affected CLI and developer
component tests, one selected T2 run, preservation checks, then one T4 discovery
run. The final retained counts, status, skips, durations, and pilot evidence are
recorded below; validation is not governance approval.

### Recorded implementation validation

- Exact Phase 64 module: 5 tests passed in 7.196 seconds after the final
  inspection-integration adjustment; 0 skips, failures, or errors.
- Focused Phase 64, CLI, and Phase 62 planner set: 39 tests passed in 16.029
  seconds; 0 skips, failures, or errors.
- Changed-file planner: T2, 260 selected tests and 131 intentionally unselected
  tests; no selection uncertainty; T4 remained required.
- Single T2 execution: exit 0; terminal `Ran 260 tests in 3190.784s` and `OK`;
  260 passed, 0 skipped, 0 failures, and 0 errors. The unprofiled JSON evidence
  is external at `C:\Apps\phase64-validation\t2-report.json`.
- Final T4 discovery: 391 run, 389 passed, 2 skipped, 0 failures, and 0 errors
  in 3500.948 seconds; terminal summary was `OK (skipped=2)`. The skips were
  `tests.test_embedding.EmbeddingTests.test_real_model_offline_repeatability`
  and
  `tests.test_rrf.HybridSearchTests.test_real_embedding_to_persisted_indexes_to_text_query_offline`;
  both require `EMBEDDING_MODEL_CACHE`, and no Phase 64 test was skipped. The
  retained log is external at `C:\Apps\phase64-validation\t4-unittest.log`.
- The T4 run emitted the existing Transformer `cache_dir` deprecation warning
  in an inspection/index path. It did not fail the suite and was not changed as
  unrelated model-loading behavior.
- Real project-checkout pilot: completed read-only with 7 changed paths, 43
  affected symbols, explicit static/unresolved evidence, missing-index handling,
  and the same 260-test T2 plan; no tests executed and no source worktree state
  changed. Run records are under the external Phase 64 pilot workspace.
- Scenario repository tests cover the required clean, modified, added, deleted,
  import/dependency, configuration, unsupported-TypeScript, and stale-index
  states. Stale retrieval was blocked and source bytes were preserved.
- Preservation before T4: no protected path changed; the v0.1.1 tag object was
  `05688504f74ad51230ee1566fad8cda0f1b1ad97` and its peeled commit was
  `51329285a882c1b7942d0a5b1c571e628d63dfb4`; the Phase 61 successor review
  remained `pending`.

## Limitations

- Repository parsing and symbol-level impact are Python-focused. Unsupported
  languages and file types remain visible as unsupported evidence; no retrieval
  success is claimed for them.
- Static imports, calls, callers, and configuration references are conservative
  parsed-source relationships, not runtime execution proof.
- Missing, stale, ambiguous, or omitted evidence remains explicit; retrieval is
  presented as current only when the active index matches the current source.
- There are no automatic source edits, test executions, or reindex operations,
  and no risk or confidence score is produced.
- The external `phase61-dependency-context-v5` review remains pending human
  review; Phase 64 validation does not change that governance state.
