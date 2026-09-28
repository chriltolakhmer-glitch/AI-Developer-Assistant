# Phase 43 — Developer Retrieval Governance Automation & Self-Check

## Purpose and isolation

Phase 43 adds repeatable developer-only governance checks, lifecycle summaries,
append-only health checkpoints and actionable maintenance findings. It preserves
human review and decision control: health and maintenance commands are diagnostic;
the checkpoint command writes only its own new snapshot. None of these commands
accepts, rejects, archives, rolls back, repairs or deletes candidates.

Research evaluation, benchmark datasets/artifacts, Humanize artifacts, frozen release
artifacts, v0.1.1 behavior and retrieval methodology are out of scope and unchanged.
No benchmark improvement or research-quality metric is claimed. Developer
repositories are not added to research snapshots. Checkpoint data is stored under the
external developer workspace, never the source checkout.

## Baseline

The checkout was on branch `main` and already contained uncommitted work from earlier
phases (including modified CLI/configuration files and untracked Phase 27–42 developer
files). Phase 43 retained those existing changes. Baseline `git diff --check` passed.
The Phase 42 focused suite ran before Phase 43 edits: 64 passed, zero failures,
zero skips.

The v0.1.1 tag object remains
`05688504f74ad51230ee1566fad8cda0f1b1ad97`, pointing to commit
`51329285a882c1b7942d0a5b1c571e628d63dfb4`. The baseline protected-file SHA-256
values were captured for the benchmark entry point, selected research retrieval
modules, `VERSION` and `release-manifest.json`; the final comparison is recorded
below.

Capabilities present at baseline included lifecycle state management, read-only
`optimize-audit` and `optimize-history`, maintenance diagnostics, rollback records,
conflict detection, ownership tracking, archive workflow and append-only lifecycle
events. Remaining workflow friction was repeated manual audit/maintenance execution,
no unified health result, no concise status summary, weak maintenance prioritization,
and no persistent time-stamped snapshot for recurring checks.

## Governance health self-check

Run:

`prototype local optimize-health --workspace EXTERNAL_WORKSPACE --json`

Health combines the Phase 42 lifecycle integrity audit, metadata and validation
completeness checks, maintenance scan, conflict detection and archived-reference
consistency checks. `health_status` is one of:

- `clean`: no lifecycle, metadata or maintenance warnings were detected.
- `warnings`: diagnostic findings need human review, but no lifecycle/metadata audit
  failure was found.
- `issues_found`: invalid transitions, inconsistent/orphaned records or required
  metadata/validation evidence failed checks.

The `checks` object has `lifecycle`, `metadata`, `maintenance`, `conflicts` and
`archive_consistency` sections, each with a status and relevant findings. The report
includes structured issue detail and `automatic_changes: false`. A candidate awaiting
a decision or other maintenance concern can produce a warning without failing the
integrity checks. Health does not alter workspace records.

## Governance summary

Run:

`prototype local optimize-summary --workspace EXTERNAL_WORKSPACE --json`

The `summary` includes counts for each of the seven lifecycle states, total candidate
records, and a separate count/list for optimization candidates not registered in the
optional lifecycle layer. It also includes the latest lifecycle events (newest first;
`--recent-limit` accepts 1–1000 and defaults to 20), pending reviews, stale active or
accepted items, archived candidates and unresolved conflicts. It is descriptive only:
there are no scores, rankings or productivity measurements. State counts cover
registered lifecycle records; unregistered candidate records are not misrepresented
as `proposed` and are listed separately.

## Repeatable checkpoints

Run:

`prototype local optimize-checkpoint --workspace EXTERNAL_WORKSPACE --json`

Each invocation runs health and summary and appends one JSON snapshot at:

`DEVELOPER_WORKSPACE/optimization/governance-checkpoints/UUID.json`

The record schema is `developer-governance-checkpoint-v1`, mode
`developer-local-governance-checkpoint`, and contains an ID, UTC timestamp, governance
health status, detected findings, lifecycle state counts and untracked candidate
count. Exclusive file creation prevents overwrites. Repeated checks create separate
records; the command does not alter candidate, lifecycle, validation, decision,
rollback or earlier checkpoint records.

This CLI command supports manual repeatability and can be called by a developer's
external scheduler. It does not install or configure a scheduler and does not run in
the background. Workspace path containment remains enforced. Runtime/test checkpoint
records are created only in external temporary developer workspaces; no generated
checkpoint directory or data is committed inside this source checkout.

## Prioritized maintenance guidance

`prototype local optimize-maintenance --workspace EXTERNAL_WORKSPACE --json` retains
Phase 42's `stale_candidates`, `duplicates`, `maintenance_notes`, audit findings and
recommendations. It now also exposes a deterministically ordered `findings` list. A
finding includes:

- `issue`/`type`: a stable issue category, such as `stale_candidate`,
  `duplicate_attempt`, `incomplete_validation`, or `archived_active_reference`.
- `severity`: `error` for integrity/required-evidence problems and `warning` for
  stale, conflicting, unresolved-review or lineage concerns.
- `affected_candidate_ids` and an optional singular `candidate_id`.
- `detail` and a `recommendation` for manual review.
- `related_lifecycle_events`: candidate/event IDs, sequence, state and timestamp when
  such lifecycle records exist.

Findings include lifecycle audit failures, candidates lacking lifecycle ownership
registration, missing ownership/metadata, incomplete or stale validation, stale
active/accepted candidates, archive references, conflict reports and unresolved
decisions. These recommendations explain where a human should
inspect history or evidence. No automatic changes are made (`automatic_changes` is
false); take a separate supported workflow action only after review.

## Limits

- Governance remains opt-in. Unregistered optimization candidates are counted
  separately and do not have lifecycle states.
- Diagnostics check persisted local records and workflow consistency, not whether the
  underlying source-code change is correct or active.
- A checkpoint is an unsigned point-in-time snapshot, not cryptographic tamper
  evidence, a guarantee of future state, or a substitute for the audit/history
  commands. A filesystem owner can edit records outside the CLI.
- No repair, reconciliation, retention or checkpoint deletion command is introduced.
- `optimize-checkpoint` adds one checkpoint record to the external developer
  workspace; other candidates and records remain read-only.
- The 30-day stale threshold remains descriptive. Human decisions and candidate
  lifecycle actions remain explicit.

## Regression coverage and validation

Phase 43 tests cover clean/warning health output, summary state and recent activity,
checkpoint creation and append-only behavior, severity/manual action/lifecycle event
references, audit/history compatibility, rollback, conflict detection and existing
optimization workflows.

Validation used the configured Python 3.14.7 environment:

- Focused: `python -m unittest tests.test_developer_mode -v` — 67 passed, zero
  failures/errors and zero skips.
- Full: `python -m unittest discover -s tests -v` — 211 passed, zero failures/errors,
  2 skipped. The skips are offline real-model integration tests requiring
  `EMBEDDING_MODEL_CACHE`, which was not configured in this environment.
- No environment issue blocked either suite. A pre-existing Transformers
  `cache_dir` deprecation warning appeared during a developer inspection test; it did
  not affect results.

## Preservation

Final checks compare the v0.1.1 tag object and peeled commit, protected-file hashes
against the Phase 43 baseline, `git diff --check`, and the source checkout for
checkpoint artifacts. Benchmark and research retrieval/evaluation paths, Humanize
artifacts, release artifacts and v0.1.1 are not modified by this phase. The shared
`docs/research/prototype-cli.md` is updated only to document developer-local commands.

The following protected-file SHA-256 values match both the Phase 43 baseline and the
final checkout:

| Path | SHA-256 | Result |
| --- | --- | --- |
| `src/evaluation/benchmark.py` | `1F7D49297724B62A6519792FC8053A785B0C7B0797C0FC5F7FE4947CDC71051E` | unchanged |
| `src/retrieval/hybrid_search.py` | `34ECD82C9E9B45355CD0860CD7F4B69A60118F38967164F644DB560EC9D70167` | unchanged |
| `src/retrieval/vector_index.py` | `2846CF4C01A0B21D72B872DD66F7007B03F407A7FA7D14F1C0AD23A16614D8E8` | unchanged |
| `src/retrieval/bm25_search.py` | `F6020DF554FA0BDC5186D73E7862A46FE0F4513E93BB483C4747EAC904F2DEA6` | unchanged |
| `VERSION` | `F21DCC10F28EA1EDE5510B510904990584F28BD9744914FA4CB7A4811FD458F8` | unchanged |
| `release-manifest.json` | `B8D430F89E9AA3EEB0C9BBB40F73FA12FD76DC1D95FE8A3DF2E903400D83C273` | unchanged |

The v0.1.1 tag object/peeled commit still match the baseline values above.
`git diff --check` passed, no protected tracked paths appear in `git status`, and
no `optimization/governance-checkpoints/` or lifecycle directory exists in the
source checkout. Runtime records generated by tests were isolated in temporary
developer workspaces.
