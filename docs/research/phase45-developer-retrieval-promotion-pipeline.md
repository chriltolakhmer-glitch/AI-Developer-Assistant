# Phase 45 ? Developer Retrieval Promotion Pipeline

## Scope and baseline

Phase 45 adds explicit promotion of approved, validated developer retrieval settings.
All runtime records remain in the external developer workspace. Research evaluation,
research retrieval, benchmark datasets and artifacts, Humanize and frozen release
artifacts are unchanged. There is no benchmark improvement claim or research metric.
Developer repositories are never added to research snapshots.

The initial branch was `main`, at `9512581d382ff1b66ff40d0eb90ccef6d14aabb9`.
Origin was `https://github.com/chriltolakhmer-glitch/AI-Developer-Assistant.git`.
The checkout contained uncommitted Phases 27?44 prerequisites. With explicit user
approval these were committed separately as `9e21343` before Phase 45 edits.
The Phase 44 focused baseline passed all 71 tests, with no failures or skips.
No protected path was dirty. SHA-256 hashes of every initially tracked file were
captured outside the checkout for the final preservation comparison.

The existing workflow provided evidence-backed optimization candidates, lifecycle
states, validation gates, review approvals/rejections, governance policy/audits and
manual source-change rollback records. It lacked executable configuration proposals,
active configuration tracking, promotion history and exact configuration rollback.

The local and remote `v0.1.1` tag object remains
`05688504f74ad51230ee1566fad8cda0f1b1ad97`, pointing to
`51329285a882c1b7942d0a5b1c571e628d63dfb4`.

## Executable developer settings and evidence

Candidate creation accepts `--retrieval-settings` as a JSON object. The first
supported setting is `relationship_factor`, a finite number from 1 to 2 inclusive;
its default is 1.25. It controls the existing developer ranking multiplier for a
query-matched static relationship. Unsupported keys, booleans and invalid values
are rejected. Free-text proposals are never interpreted as code or settings.

For example, add `--retrieval-settings '{"relationship_factor": 1.5}'` to the
existing `prototype local optimize create` command, together with candidate ID,
problem, affected cases, evidence IDs, proposed change and validation method.
Shell quoting must preserve the JSON quotes.

The existing `optimize validate` command evaluates the candidate settings in an
isolated execution context across regression, trace and diagnosis. The override is
removed even when validation fails. It does not activate a promotion. Validation
records preserve the exact settings and base active configuration. Review approval
snapshots include both. Ranking explanations show the effective multiplier.

An existing prose-only candidate remains usable in the earlier review workflow,
but cannot be promoted. Create a new candidate with explicit settings, validate it,
and obtain review approval. Old approval snapshots without configuration evidence
require a new validation and review; they are not silently upgraded.

## Promotion commands

All commands accept `--workspace EXTERNAL_WORKSPACE` and `--json`:

```text
prototype local optimize-promote CANDIDATE_ID --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-promotion-status --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-promotion-check --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-retire PROMOTION_OR_CANDIDATE_ID --workspace EXTERNAL_WORKSPACE --json
prototype local optimize-promote-rollback PROMOTION_OR_CANDIDATE_ID --workspace EXTERNAL_WORKSPACE --json
```

Promotion requires an existing, non-rejected candidate, latest approved review,
passing live policy checks, a valid `validated` candidate lifecycle, latest passing
validation matching the review and proposed settings, an existing rollback baseline,
and an unchanged base active configuration. Existing conflict-note warnings remain
visible and do not resolve conflicts. At most one live promotion per candidate and
one active settings promotion per repository are allowed.

Only the explicit promote command activates settings. It records pending, validated
and promoted transitions separately. Approval alone never activates settings.
Queries, traces, diagnosis and developer regression/evaluation consume settings only
for the promoted repository. Research commands have no promotion integration.

## Lifecycle and configuration records

| State | Allowed next states |
| --- | --- |
| pending | validated, retired |
| validated | promoted, retired |
| promoted | paused, rolled_back, retired |
| paused | promoted, rolled_back, retired |
| rolled_back | retired |
| retired | none |

The Python API exposes `create_promotion` and `transition_promotion`, including
pause/resume. There are no automatic transitions or background repair jobs. Invalid
transitions fail before writing. If a multi-step promote command is interrupted,
status shows the pending/validated record. Inspect and retire that record before
retrying the CLI; API callers may explicitly resume a valid transition.

Each promotion includes a generated promotion ID, source candidate and repository,
status, creation time, approved-by identity, review ID, validation summary, policy
report, settings, promotion timestamp, rollback reference, previous configuration
and append-only transition history. The identity is the recorded human reviewer;
it is not independently authenticated.

Immutable numbered snapshots live at `optimization/promotions/NNNNNNNN.json` in the
external workspace. A snapshot contains all promotion records and the active
configuration, including active candidate IDs, per-repository settings, promotion
metadata, validation evidence, rollback references and an update timestamp. The
previous snapshots preserve every earlier configuration. There is no separate
mutable active file that can drift from promotion history.

Publication writes and flushes a temporary file, then atomically creates the final
snapshot using an exclusive hard link. A competing writer fails rather than
replacing a snapshot. Readers see a complete prior or new snapshot. Temporary files
are removed on handled failures; an abrupt process termination can leave an unused
`.tmp` file outside the source checkout. The filesystem must support hard links.

## Retirement, rollback and validation

Retirement removes an active candidate from subsequent retrieval, preserves all
records, and adds a retirement event. Other active candidates remain in use.
Rollback restores the exact pre-promotion configuration, including its timestamp,
and adds a `rolled_back` event. It changes developer configuration only: it does
not edit source, revert Git commits or invoke the older manual source rollback.

Rollback and pause require the expected activation configuration. Later active
changes must first be rolled back in reverse order. This prevents restoration from
silently discarding another repository's settings or resurrecting retired entries.
If intervening retirement means exact rollback is unavailable, retire the remaining
promotion and validate a new configuration. Pausing removes settings, and explicit
resume rechecks approval, evidence and the base configuration.

`optimize-promotion-check` returns `passed`, `warnings`, `blocked` and
`automatic_changes: false`. It checks the journal chain, metadata, allowed
transitions, immutable history, configuration consistency, historical rollback
references, and current review/lifecycle/policy/validation/baseline evidence for
live records. Terminal records retain historical evidence. It does not initialize
an absent workspace, repair directories, rewrite records or activate settings.
Status reports all promotions, active/pending/retired groups and rollback history.

## Limitations

This is a local developer configuration workflow, not a source-code deployment
system. The single supported setting is intentionally bounded. Configuration
validation is descriptive developer evidence, not proof of causal improvement.
Candidate lifecycle and review records remain separate from promotion states, so
existing review and governance consumers retain their earlier semantics. Live
policy failures are reported by the check command; there is no automatic retirement.

Journal digests detect chain inconsistency, not malicious administrator edits or
truncation of the journal tail. Protect the external workspace with filesystem ACLs.
There is no remote identity service. Snapshot history grows with each transition;
no pruning or compaction is performed. Default developer retrieval remains unchanged
when there are no promotions. The tagged v0.1.1 release remains untouched.

## Verification and preservation

Validation used Python 3.14.7. The focused command
`python -m unittest tests.test_developer_mode -v` passed all 80 tests, with zero
failures/errors/skips. Nine new promotion regression tests cover creation,
approval/policy requirements, stale evidence, missing rollback baselines, transitions,
active retrieval behavior, repository isolation, status, retirement, exact rollback,
rollback ordering, pause/resume, read-only checks, corruption, publication failures
and review/governance compatibility.

The first full run discovered an existing environment problem: 224 tests ran with
19 errors and 2 skips, and all 19 errors were missing `sentence-transformers`
package metadata in BM25 setup. Installing the repository-pinned
`sentence-transformers==6.1.0` with `--no-deps` resolved the isolated failing test;
`python -m pip check` then reported no broken requirements. No requirements or
research code was changed to work around the failure.

The full rerun of `python -m unittest discover -s tests -v` completed successfully:
224 tests run, 222 passed, 2 skipped, zero failures or errors. Both skips require
`EMBEDDING_MODEL_CACHE` for real offline model inference/integration; that cache was
not configured. The final Phase 45 commit is separate from the approved prerequisite
commit and uses the requested message, `Phase 45: add developer retrieval promotion
pipeline`. Push and remote-ref verification are reported at task completion.

All 23 initially tracked protected research/retrieval/evaluation, artifact and
release paths matched their captured SHA-256 hashes. Across all initially tracked
files, only the intended shared CLI source and CLI documentation changed during
Phase 45; developer files added by the prerequisite commit were reviewed separately.
No generated promotion records, active configuration files or rollback state exist
inside the checkout. Runtime regression records were created in temporary external
workspaces. `git diff --check` passed.
