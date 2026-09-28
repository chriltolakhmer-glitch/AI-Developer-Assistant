# Phase 42 — Developer Retrieval Governance Validation

## Purpose and isolation

Phase 42 validates and strengthens the Phase 41 lifecycle governance workflow. The
work is limited to developer-local optimization lifecycle records, diagnostic CLI
commands, regression tests and this documentation. It does not alter research
retrieval methodology, research evaluation, benchmark datasets or artifacts,
Humanize artifacts, frozen release artifacts, the v0.1.1 tag, or v0.1.1 behavior.
No benchmark improvement or research-quality metric is claimed.

Governance records remain under the external developer workspace at
`optimization/candidates/ID/`. No governance records are generated in the source
checkout. The CLI does not add developer repositories to research snapshots.

## Baseline and Phase 41 capabilities

The working branch was `main`. At baseline the checkout contained pre-existing
uncommitted Phase 27–41 work, including changes to the shared CLI documentation and
untracked developer-mode source/tests; Phase 42 preserved that work. The v0.1.1 tag
object was `05688504f74ad51230ee1566fad8cda0f1b1ad97`, pointing to commit
`51329285a882c1b7942d0a5b1c571e628d63dfb4`. The tag and release identity remain
unchanged.

Phase 41 already provided:

- The `proposed → experimenting → validated → accepted/rejected → rolled_back`
  lifecycle, with `archived` as a terminal state and invalid transition rejection.
- Owner, purpose and affected-case metadata at registration.
- Candidate and lifecycle history as append-only workspace records.
- Explicit archive workflow, maintenance/status reports, rollback compatibility and
  conflict detection reused from Phase 40.

Baseline focused validation ran
`python -m unittest tests.test_developer_mode -v`: 59 tests passed, zero failures,
zero skips. The initial repository was not clean, so protected-path comparisons for
this phase are against the captured Phase 42 starting state as well as the immutable
v0.1.1 tag identity, not an assumption that all worktree content matched the tag.

### Risks addressed and remaining

Phase 41 did not have a consolidated audit, broad detection of malformed or orphaned
lifecycle records, a unified cross-record event timeline, or checks for incomplete
validation and stale accepted work. It also had no ownership-change event or
maintainer-facing recommendations. Phase 42 adds diagnostics for those conditions.

The audit detects structural and workflow inconsistencies but is not a cryptographic
tamper-evidence system. Workspace files can still be manually changed outside the
CLI. Repair and deletion are intentionally out of scope. Archived lifecycle states
are terminal; restoration is not supported, so a new candidate is needed to resume
work. Maintenance thresholds are descriptive, fixed at 30 days, and do not trigger
automatic state changes. The governance state is an opt-in layer and does not rewrite
Phase 39 candidate status or execute source changes.

## Lifecycle validation

Supported states remain `proposed`, `experimenting`, `validated`, `accepted`,
`rejected`, `rolled_back` and `archived`. Supported transitions are:

| Current state | Allowed next state(s) |
| --- | --- |
| proposed | experimenting, archived |
| experimenting | validated, rejected, archived |
| validated | accepted, rejected, archived |
| accepted | rolled_back, archived |
| rejected | archived |
| rolled_back | archived |
| archived | none (terminal) |

Each transition is stored as a new, exclusive-created lifecycle event. Sequence,
previous-state linkage, ownership metadata and timestamps remain visible in the
history. Transition timestamps are strictly increasing relative to the previous
lifecycle record. A `validated` transition requires an ISO-8601
`--last-validation-at` value. `--owner NAME` on a transition can record an explicit
ownership change; the event stores the previous owner as well as the new owner.

Regression coverage exercises invalid state jumps, transition ordering, accepted
candidate rollback compatibility, rejection followed by archival, archived candidate
inspection, ownership changes, timestamp ordering, and immutability through read-only
inspection. An accepted lifecycle event is checked against the optimization decision;
a `rolled_back` event is checked against a rollback record. The records still describe
manual actions and do not perform rollback or accept/reject operations themselves.

## Governance audit

Run:

`prototype local optimize-audit --workspace EXTERNAL_WORKSPACE --json`

This command is diagnostic-only. Its JSON includes `audit_status`, a combined `issues`
array, and the following categories:

- `invalid_transitions`: a recorded state jump is not permitted or the chain does not
  begin at `proposed`.
- `missing_metadata`: required fields, owner/purpose values, or valid timestamps are
  missing.
- `duplicate_history_entries`: event IDs, sequence numbers or event contents repeat.
- `orphaned_records`: lifecycle/validation/rollback records lack their candidate or
  disagree with their candidate directory.
- `inconsistent_states`: schema, sequence, previous-state chain, timestamp ordering,
  validation, decision or rollback evidence is inconsistent.

A clean workspace returns `"audit_status": "clean"` and `"issues": []`. Otherwise
`audit_status` is `issues_found`. The audit does not repair, remove or rewrite records.
It reports issues for a developer to inspect.

## Maintenance diagnostics

`prototype local optimize-maintenance --workspace EXTERNAL_WORKSPACE --json` retains
its prior `stale_candidates`, `duplicates` and `maintenance_notes` fields, and now
reports:

- `abandoned_experiments`: experiments left in `experimenting` for more than 30 days.
- `incomplete_validation_records`: validated/accepted lifecycle claims without
  corresponding or complete validation evidence.
- `missing_ownership_fields`: lifecycle metadata findings for absent owner/purpose.
- `stale_accepted_candidates`: accepted candidates whose validation is older than 30
  days or lacks a usable validation timestamp.
- `archived_active_references`: archived candidates still referenced by unresolved
  (`candidate`/`validated`) superseding candidates.
- `metadata_issues` and `recommendations`: details and suggested manual review.
- `automatic_changes: false`: explicit indication that no candidate was modified.

The report does not automatically archive, delete, accept or reject candidates. It
also does not decide whether a recommendation is appropriate for a particular
repository; a developer must review the records and take any separate manual action.

## History inspection

Run:

`prototype local optimize-history ID --workspace EXTERNAL_WORKSPACE --json`

The output combines immutable candidate creation, lifecycle, ownership-change,
validation, decision and rollback events, including archival, ordered by
`recorded_at`. Each item is marked `immutable: true` to describe the append-only CLI
record contract; the audit is not a cryptographic verification of the filesystem.
Ownership changes are explicit timeline entries and retain their original lifecycle
record. The command is restricted to the selected candidate in the developer
workspace.

## Regression and compatibility

The Phase 42 tests cover lifecycle transitions and invalid jumps, audit output and
read-only behavior, history chronology and ownership, metadata and maintenance
findings, rejection/archive inspection, accepted rollback compatibility, conflict
detection compatibility, and the existing optimization workflow. Phase 39/40
optimization, rollback and conflict logic remains the source for those established
behaviors; governance augments it rather than changing retrieval behavior.

Validation executed in the configured Python 3.14.7 environment:

- Focused: `python -m unittest tests.test_developer_mode -v` — 64 tests passed,
  zero failures/errors, zero skips.
- Full: `python -m unittest discover -s tests -v` — 208 tests passed, zero
  failures/errors, 2 skipped. Both skips are offline real-model integration tests
  requiring `EMBEDDING_MODEL_CACHE`; this environment did not provide that cache.
- No Phase 42 environment issue blocked the focused or full suite. A deprecation
  warning from Transformers' `cache_dir` argument appeared in a pre-existing
  developer inspection test; it did not fail tests.

## Preservation

The final verification checks `git diff --check`, v0.1.1 tag object and peeled commit,
and Phase 42 starting-state hashes for protected files. Benchmark, Humanize,
research-evaluation and research retrieval paths are not edited by this phase. The
only research-doc path intentionally updated is `docs/research/prototype-cli.md`,
which now documents the developer-local CLI workflow. No v0.1.1 tag operation is
performed.
