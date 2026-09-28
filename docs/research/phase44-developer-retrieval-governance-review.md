# Phase 44 — Developer Retrieval Governance Review Workflow

## Purpose and isolation

Phase 44 adds an explicit developer-only review queue, append-only review decisions,
and read-only optimization policy checks. It makes pending reviews, reviewer identity,
validation evidence, lifecycle history and decision reasons visible together. It does
not change the research retrieval methodology or apply an optimization.

Research evaluation, benchmark datasets or artifacts, Humanize artifacts, frozen
release artifacts, v0.1.1 behavior and source retrieval code are outside this phase.
No benchmark-improvement claim, research-quality metric, developer ranking or
productivity measure is produced. Developer repositories are not added to research
snapshots. The v0.1.1 tag is not changed.

All review records are stored under the external developer workspace at
`optimization/reviews/REVIEW_ID/events/`. No review, queue, approval or policy record
is generated inside the source checkout.

## Phase 44 baseline

The active branch was `main`. The worktree was already dirty from prior phases at
baseline; Phase 44 preserves those changes rather than treating the checkout as a
clean release tree. Pre-existing tracked changes included README/configuration files,
the shared CLI documentation, CLI/configuration source and tests. Prior-phase developer
source, fixtures and Phase 27–43 documentation were already untracked. No protected
research-evaluation/retrieval, benchmark, Humanize, `VERSION` or release-manifest path
was modified at baseline.

The `v0.1.1` tag object was
`05688504f74ad51230ee1566fad8cda0f1b1ad97`, pointing to commit
`51329285a882c1b7942d0a5b1c571e628d63dfb4`. Baseline protected-file SHA-256 values:

| Path | SHA-256 |
| --- | --- |
| `src/evaluation/benchmark.py` | `1F7D49297724B62A6519792FC8053A785B0C7B0797C0FC5F7FE4947CDC71051E` |
| `src/retrieval/hybrid_search.py` | `34ECD82C9E9B45355CD0860CD7F4B69A60118F38967164F644DB560EC9D70167` |
| `src/retrieval/vector_index.py` | `2846CF4C01A0B21D72B872DD66F7007B03F407A7FA7D14F1C0AD23A16614D8E8` |
| `src/retrieval/bm25_search.py` | `F6020DF554FA0BDC5186D73E7862A46FE0F4513E93BB483C4747EAC904F2DEA6` |
| `VERSION` | `F21DCC10F28EA1EDE5510B510904990584F28BD9744914FA4CB7A4811FD458F8` |
| `release-manifest.json` | `B8D430F89E9AA3EEB0C9BBB40F73FA12FD76DC1D95FE8A3DF2E903400D83C273` |

The Phase 43 focused baseline command, `python -m unittest tests.test_developer_mode
-v`, passed: 67 tests, zero failures/errors and zero skips. Baseline `git diff --check`
passed; the source checkout contained no candidate lifecycle or governance checkpoint
records.

### Existing governance carried forward

Before Phase 44, developer mode already supported:

- Candidate lifecycle states `proposed`, `experimenting`, `validated`, `accepted`,
  `rejected`, `rolled_back` and `archived`, with append-only lifecycle history and
  explicit owner/purpose metadata.
- Governance audit, lifecycle/history summaries, health reports, maintenance findings,
  ownership tracking, rollback records and archive workflow.
- Append-only governance checkpoints and conflict diagnostics.

The review gap was that the existing “pending review” summary inferred review needs
from candidate status but did not provide a dedicated review queue, reviewer identity,
review-specific state transitions, a joined decision view, or a policy gate before
recording a review approval.

## Review queue and states

`prototype local optimize-review-create CANDIDATE_ID --reason TEXT` opens a pending
review. `--owner` defaults to `developer`; repeat `--case CASE_ID` to narrow the
recorded affected cases. `--conflict-note TEXT` can document a known conflict for
human consideration, but does not resolve it. At most one pending review is allowed
per candidate. The candidate must already exist.

Each review snapshot records a generated `review_id`, candidate ID, status, owner,
creation time, reviewer and reason, affected cases, validation summary, governance
health status, related candidate-attempt history and review history. Review events are
written as new files using exclusive creation. Each event retains a complete history
snapshot; existing event files are not rewritten or deleted.

| Current state | Allowed next state |
| --- | --- |
| `pending` | `approved`, `rejected`, `deferred`, `withdrawn` |
| `deferred` | `pending`, `withdrawn` |
| `approved` | none (terminal) |
| `rejected` | none (terminal) |
| `withdrawn` | none (terminal) |

Every transition requires a reviewer and nonempty reason. Invalid transitions fail
without adding an event. Approval is never automatic. `optimize-approve` changes only
the review status; it does not accept the optimization candidate, advance its
lifecycle, change ranking, apply code or change retrieval settings.

## Developer review workflow

```text
prototype local optimize-review-create CANDIDATE_ID --reason "Ready for review" --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-review REVIEW_ID --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-policy-check --id CANDIDATE_ID --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-approve REVIEW_ID --reviewer NAME --reason "Evidence reviewed" --workspace EXTERNAL_WORKSPACE --json
```

`optimize-review` accepts a review ID or an unambiguous candidate ID. With no ID it
lists the queue. A single-review result includes the current candidate details,
immutable lifecycle timeline, persisted validations, related maintenance findings,
previous optimization decisions, and candidate supersession/attempt history. It
refreshes the visible joined context from developer-workspace records; approval events
also snapshot the validation and lifecycle context current at decision time.

`prototype local optimize-reject REVIEW_ID --reviewer NAME --reason TEXT` records a
rejection reason without requiring a passing validation. `optimize-review-defer` and
`optimize-review-withdraw` record those states; `optimize-review-reopen` moves a
`deferred` review back to `pending`. Each command requires a reason and preserves all
prior event files.

## Policy checks and approval gate

`prototype local optimize-policy-check --workspace EXTERNAL_WORKSPACE --json` checks
all candidates; `--id CANDIDATE_ID` scopes the read-only report to one. The report
contains `passed`, `warnings`, `blocked`, `candidate_results` and
`automatic_changes: false`.

Checks include:

- Required candidate metadata and an existing lifecycle owner.
- A structurally valid lifecycle chain in the `validated` state before approval.
- Persisted latest validation evidence with every gate passing.
- A rollback target and manual instructions for already accepted or rolled-back
  candidates; otherwise rollback information is marked not required at this stage.
- Conflicts affecting the candidate. An unresolved conflict blocks approval unless a
  review contains an explicit conflict note. Documentation is a warning, not proof of
  resolution; the conflict remains visible for human assessment.

Approval is denied while any policy blocker remains. Warnings do not silently change a
candidate or make a decision. `optimize-policy-check` does not repair metadata, create
validations, resolve conflicts, change lifecycle state or write a review record. It
may report governance warnings independently from blockers.

The Phase 39 optimization `accept`/`reject` decision remains a separate operation.
A review approval means only that a developer recorded approval of that review item;
it is not an optimization acceptance and does not assert that a source change was
applied or that retrieval improved.

## Audit, safety and limitations

Review events are additive to the existing candidate lifecycle, validations, decision,
rollback and governance-checkpoint records. Review actions do not rewrite those
records. Policy reports reuse existing candidate validation, lifecycle audit and
conflict information. Review files are immutable by CLI convention and exclusive
creation, not cryptographically signed; administrators can change workspace files
outside the CLI. There is no multi-user locking or external identity verification.

The review workflow does not rank reviewers, measure productivity, assess source-code
correctness, prove an optimization is active, or automatically promote, accept, reject,
archive, roll back, repair, or delete candidates. Deferred/withdrawn/approved/rejected
review statuses describe governance records only. Keep the developer workspace
separate from research storage and protect it using local filesystem ACLs.

## Regression validation

Phase 44 tests cover review creation, queue display, append-only history, allowed and
invalid state transitions, validation-gated approval, reviewer/reason capture,
rejection, policy blockers, documented-conflict warnings, read-only policy behavior,
and compatibility with lifecycle history, rollback records, audit and checkpoints.

Validation used the configured Python 3.14.7 environment:

- Phase 43 baseline before edits: `python -m unittest tests.test_developer_mode -v`
  — 67 passed, zero failures/errors, zero skips.
- Focused after Phase 44: `python -m unittest tests.test_developer_mode -v` — 71
  passed, zero failures/errors, zero skips.
- Full suite: `python -m unittest discover -s tests -v` — 215 run, zero failures or
  errors, 2 skipped. Both skips require `EMBEDDING_MODEL_CACHE` for real offline model
  repeatability; the cache was not configured. A pre-existing Transformers
  `cache_dir` deprecation warning appeared in a developer inspection test.
- `git diff --check` passed.

## Final preservation

The final `v0.1.1` tag object and peeled commit remain
`05688504f74ad51230ee1566fad8cda0f1b1ad97` and
`51329285a882c1b7942d0a5b1c571e628d63dfb4`. All six protected SHA-256 values in the
baseline table match the final checkout. No protected tracked paths appear in
`git status`; benchmark, Humanize, research evaluation/retrieval and frozen release
artifacts remain unchanged. `git diff --check` passes, and no generated review,
candidate-lifecycle or governance-checkpoint records exist inside the source checkout.
All runtime test records were confined to temporary developer workspaces. The
pre-existing dirty Phase 27–43 worktree was preserved.
