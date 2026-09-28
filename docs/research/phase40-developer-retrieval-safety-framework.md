# Phase 40 — Developer Retrieval Optimization Safety Framework

This phase adds accountability, rollback visibility and conflict diagnostics around
the Phase 39 developer optimization loop. Retrieval code, research evaluation and
methodology, benchmark datasets, Humanize artifacts and frozen release artifacts
remain unchanged. No quality score or benchmark improvement is claimed. Developer
repositories are never added to research snapshots. Nothing in this phase edits
source files, retrieval settings, or applies/reverts patches automatically.

## Baseline and inputs

The checkout retains existing Phase 27–39 work. The `v0.1.1` tag object is
`05688504f74ad51230ee1566fad8cda0f1b1ad97`, pointing to commit
`51329285a882c1b7942d0a5b1c571e628d63dfb4`; both are unchanged. The starting Phase 39
focused suite passed 50 tests with zero skips, failures or errors.

Existing capabilities carried into this phase: evidence-linked optimization
candidates, six-gate validation, before/after version comparison, and immutable
accept/reject decisions (Phase 39). Safety gaps identified before this phase:

- Decision records referenced a validation ID but did not restate the evidence,
  gate summary, or how to restore a prior version, so accountability required
  cross-referencing multiple files.
- There was no way to link a rejected experiment to the retry that replaced it, so
  "how many times was this tried" was not visible.
- There was no rollback-facing command; developers had to reconstruct the
  restoration path (which baseline to return to) from validation records manually.
- There was no automated way to notice that two independent candidates targeted the
  same case, proposed the same change, or disagreed about whether a change was an
  improvement or a regression.

## Optimization lifecycle

Unchanged from Phase 39: `candidate` → `validate` (zero or more validations, latest
one governs) → `accept` or `reject` (final, immutable; a new candidate ID is required
to retry). This phase adds an optional lineage: `optimize create --supersedes
PRIOR_ID` links a new candidate to a previously **rejected** one in the same
repository. `--supersedes` is refused if the prior candidate belongs to a different
repository or has not been rejected (accepted candidates are not retried; a genuinely
new problem should get an unlinked candidate).

`optimize`/`optimize show` report, per candidate, a `history` list ordered from the
first attempt to the current one (`attempt`, `candidate_id`, `status`, `reason`, where
`reason` is the recorded decision note for a rejected/accepted attempt and `null`
otherwise), for example:

```text
Candidate: dependency-expansion-gap (attempt 2)
History:
  Attempt 1 (dependency-gap): rejected — "Too much unrelated context"
  Attempt 2 (dependency-expansion-gap): candidate — pending
```

The top-level payload also includes `unresolved_candidates`: candidate IDs with no
decision yet (`candidate` or `validated` status), independent of lineage.

## Decision records

`optimize accept`/`optimize reject` still require a nonempty `--note` and, for
acceptance, a latest validation that passed every gate. The stored decision record
now additionally carries:

- `evidence`: the candidate's source event IDs.
- `reason`: the same text as `note` (kept for backward compatibility), always present.
- `validation`: `{"regressions": N, "improvements": N, "stability_passed": bool,
  "passed": bool}` summarizing the latest validation, or `null` if the candidate was
  rejected before any validation existed.
- `rollback`: `{"restore_to": BASELINE_OR_NULL, "instructions": TEXT}` naming the
  `before` version from the latest validation, or `null` if none exists.
- `scope`: the existing statement that the decision applies only to the recorded
  experiment.

Example (rejected, matching the schema requested for this phase):

```json
{
  "candidate_id": "dependency-context-gap",
  "status": "rejected",
  "reason": "introduced unrelated context",
  "validation": {"regressions": 2, "improvements": 0, "stability_passed": true, "passed": false}
}
```

Every accepted decision therefore carries evidence, a validation result and (via the
stored `comparison` on the referenced validation) a comparison result. Every rejected
decision carries a nonempty rejection reason. Decisions remain immutable; a rewritten
decision is refused exactly as in Phase 39.

## Rollback workflow

`prototype local rollback --id ID --workspace EXTERNAL_WORKSPACE --json` (default
action `show`) reports, per matching candidate:

- `current_state`: the decision status, or the undecided candidate/validated status.
- `previous_states`: every baseline/history version referenced by the candidate's
  validations (`before` as `baseline`, `after` as `history`), de-duplicated.
- `affected_behavior`: the latest validation's per-case comparisons (regressions,
  improvements, classification), or `[]` if unvalidated.
- `rollback_available`: `true` only when the candidate was accepted.
- `rollback_records`: previously recorded rollback attempts for this candidate.

`rollback record --id ID --note TEXT` requires a previously **accepted** candidate and
a nonempty note. It writes an exclusive, immutable record under
`optimization/candidates/ID/rollback/UUID.json` naming the `target_version` (the
validation's `before` baseline) and restoration instructions. It does not revert any
file, reindex, or touch retrieval settings — restoration remains a manual step, as in
Phase 39's stated limitations. Rollback storage uses the same workspace containment
checks (`_contained`) as candidates, validations and decisions, so it cannot be
redirected outside the developer workspace, and it never reads or writes research,
benchmark, Humanize or release paths.

## Conflict detection

`prototype local optimize-check --workspace EXTERNAL_WORKSPACE --json` returns:

```json
{"conflicts": [], "affected_cases": [], "warnings": []}
```

Each conflict has a `type`, the `candidates` involved, the affected `cases`, and a
plain-language `detail`. Detected types:

- `repeated_case_target`: more than one independently-created candidate (not linked
  by `--supersedes`) lists the same affected case.
- `duplicate_attempt`: more than one independent candidate in the same repository has
  an identical (case-insensitive, trimmed) `proposed_change` text.
- `mixed_outcome`: a single candidate's latest validation classifies some cases as
  `improved` and others as `regression` at the same time.
- `conflicting_ranking_adjustment`: two independent candidates' latest validations
  disagree (`improved` vs. `regression`) about the same case.

`warnings` currently include `repeated_failed_experiments` (an attempt chain rejected
more than once) and `unresolved_candidate` (no decision recorded yet). Conflicts and
warnings are diagnostics only; nothing is auto-resolved, merged, or reverted by this
command.

## Storage

New records live entirely under the existing `optimization/candidates/ID/` namespace,
alongside Phase 39's `candidate.json`, `validations/UUID.json` and `decision.json`:

```text
DEVELOPER_WORKSPACE/optimization/candidates/ID/rollback/UUID.json
```

Rollback records use `schema_version: developer-rollback-v1`, mode
`developer-local-rollback`, and the same exclusive-write, never-overwritten
convention as every other developer-optimization record. `candidate.json` gains one
additional field, `supersedes` (a prior candidate ID or `null`); existing Phase 39
candidate files without this field are read as `supersedes: null`.

## Limitations

Lineage (`--supersedes`) is an explicit, developer-asserted link, not an automatically
inferred relationship; unrelated candidates that happen to touch the same case are
still reported as conflicts even when a developer considers them intentional variants.
Conflict detection only reasons over the local optimization records; it does not
inspect the actual retrieval code. Rollback is descriptive: it never edits source
files, reindexes, or reverts retrieval settings, matching Phase 39's stated absence of
automatic tuning, patching or rollback of code. Decision, validation and rollback
records are not cryptographically signed; a filesystem owner can still edit them
outside the workflow.

## Developer-only scope

Nothing in this phase reads or writes `config.data_root`, `config.corpus_root`,
`config.validation_output`, `config.embedding_model_cache`, benchmark datasets,
Humanize artifacts, `VERSION`, or `release-manifest.json`. All new commands operate
only inside the external developer workspace and the `research_roots` passed to
`DeveloperWorkspace` remain excluded by the same isolation checks Phase 28 introduced.

## Validation and preservation

Validation uses `C:/Apps/.venv/Scripts/python.exe` with `HF_HUB_OFFLINE=1` and the
existing external Phase 37 model cache; no new model downloads are needed. Required
commands:

```text
python -m unittest tests.test_developer_mode -v
python -m unittest discover -s tests -v
git diff --check
```

Results:

- Phase 39 baseline: 50 tests passed; zero skips, failures or errors.
- Phase 40 focused suite: 55 tests passed; zero skips, failures or errors.
- Full suite: 199 tests passed; 2 skipped; zero failures or errors.
- `git diff --check`: passed (no whitespace errors).
- No generated optimization, decision or rollback state exists inside the source
  checkout; all runtime records are written under external temporary/developer
  workspaces used by tests and manual smoke checks.

Five new tests cover: decision-record accountability and rollback show/record
(including the nonempty-note and accepted-only guards), rejected-candidate reason
handling and the rollback-availability guard, `--supersedes` lineage/history and the
`unresolved_candidates` list (including the previously-rejected-only guard), conflict
detection for repeated case targets and duplicate attempts without auto-resolution,
and the `optimize-check`/`rollback` CLI commands end to end. Existing Phase 37–39
regression, trace/diagnose compatibility and comparison tests are unchanged and still
pass, confirming compatibility with this phase's additions.

Research: unchanged. Benchmark: unchanged/deferred. Humanize: unchanged/frozen.
Release: `v0.1.1` unchanged.
