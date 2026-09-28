# Phase 41 — Developer Mode Retrieval Governance & Lifecycle Management

This phase adds explicit lifecycle states, ownership metadata, and long-term
maintenance diagnostics on top of the Phase 39 optimization loop and Phase 40 safety
framework. Retrieval code, research evaluation and methodology, benchmark datasets,
Humanize artifacts and frozen release artifacts remain unchanged. No quality score,
benchmark improvement claim, developer ranking, or productivity metric is produced.
Nothing in this phase deletes a candidate, archives automatically, or edits source
files or retrieval settings.

## Baseline and inputs

The checkout retains existing Phase 27–40 work. The `v0.1.1` tag object is
`05688504f74ad51230ee1566fad8cda0f1b1ad97`, pointing to commit
`51329285a882c1b7942d0a5b1c571e628d63dfb4`; both are unchanged. Protected research,
benchmark and Humanize paths are unchanged. The starting Phase 40 focused suite
passed before this phase's changes were added.

Existing capabilities carried into this phase: evidence-linked optimization
candidates, six-gate validation, before/after version comparison, immutable
accept/reject decisions with rollback and evidence summaries (Phase 39/40), rollback
visibility (`rollback`/`rollback record`), and conflict diagnostics
(`optimize-check`). Lifecycle gaps identified before this phase:

- A candidate's coarse `status` (`candidate`/`validated`/`accepted`/`rejected`) did
  not distinguish "proposed but not yet started" from "actively being experimented
  on", and had no `rolled_back` or `archived` end state.
- There was no owner or purpose recorded against a candidate, so accountability for
  an in-flight experiment required reading the original `optimize create --problem`
  text.
- There was no single command summarizing which candidates were active, decided, or
  obsolete across a workspace.
- There was no way to retire an obsolete candidate (abandoned proposal, superseded
  duplicate) without leaving it listed as unresolved forever, and no way to do so
  without deleting its history.
- There was no diagnostic for stale pending candidates, repeated failed experiment
  chains, or duplicate proposals beyond the ad-hoc conflict report.

## Lifecycle state model

New, additive lifecycle records live under each candidate's existing
`optimization/candidates/ID/lifecycle/` directory (one immutable JSON file per
transition; schema `developer-governance-v1`, mode `developer-local-governance`).
They do not replace or rewrite the Phase 39 `candidate.json`, `validations/`,
`decision.json` or Phase 40 `rollback/` records; they add an explicit, ownership-aware
state machine referencing the same candidate ID.

Supported states: `proposed`, `experimenting`, `validated`, `accepted`, `rejected`,
`rolled_back`, `archived`. Allowed transitions:

| From | To |
| --- | --- |
| `proposed` | `experimenting`, `archived` |
| `experimenting` | `validated`, `rejected`, `archived` |
| `validated` | `accepted`, `rejected`, `archived` |
| `accepted` | `rolled_back`, `archived` |
| `rejected` | `archived` |
| `rolled_back` | `archived` |
| `archived` | *(none — terminal)* |

Any other request (including re-registering an already-registered candidate, or
transitioning an unregistered one) raises `LocalWorkflowError` and writes nothing.
Every transition is a new, exclusively-created file (append-only); no existing
transition file is ever modified or deleted, so `history` is always a complete,
immutable audit trail:

```json
{
  "candidate_id": "dependency-context-improvement",
  "state": "validated",
  "owner": "developer",
  "purpose": "reduce missing dependency context",
  "affected_cases": ["auth-flow"],
  "created_at": "2026-09-29T00:00:00+00:00",
  "updated_at": "2026-09-29T01:00:00+00:00",
  "last_validation_at": "2026-09-29T01:00:00+00:00",
  "history": [
    {"sequence": 1, "state": "proposed", "previous_state": null, "note": "Candidate registered for lifecycle tracking."},
    {"sequence": 2, "state": "experimenting", "previous_state": "proposed", "note": "started experimenting"},
    {"sequence": 3, "state": "validated", "previous_state": "experimenting", "note": "gates passed"}
  ]
}
```

## Ownership model

`optimize register --id ID --owner NAME --purpose TEXT --case CASE_ID` (repeat
`--case` as needed) starts lifecycle tracking for an existing candidate. `owner` and
`purpose` must be nonempty; `affected_cases` must be a nonempty subset of the
candidate's own recorded cases. Ownership and purpose are set once at registration and
copied forward on every later transition — they describe *who is accountable and
why*, not a score. This phase intentionally does **not** add: user scoring,
productivity metrics, or a ranking of developers. `optimize transition` only accepts
a target `--state` and a nonempty `--note`; it does not accept ownership changes,
keeping accountability attached to the original registration.

## Lifecycle inspection commands

`prototype local optimize-status --workspace EXTERNAL_WORKSPACE --json` buckets every
registered candidate by current state:

```json
{"active": [], "validated": [], "accepted": [], "rejected": [], "rolled_back": [], "archived": [], "stale": []}
```

`active` covers `proposed`/`experimenting` candidates; `stale` is the subset of
`active` with no lifecycle update in 30+ days. This command only reads lifecycle
records; it never changes state.

`prototype local optimize-archive ID --note TEXT --workspace EXTERNAL_WORKSPACE
--json` archives an obsolete experiment from any non-archived state (a transition to
`archived`). It requires the candidate to already be registered and does not delete
any candidate, validation, decision or rollback record — it only appends one more
immutable lifecycle event. Archiving is a developer-workspace-only, manual action;
nothing archives automatically.

## Maintenance diagnostics

`prototype local optimize-maintenance --workspace EXTERNAL_WORKSPACE --json` reports,
without modifying anything:

```json
{"stale_candidates": [], "duplicates": [], "maintenance_notes": []}
```

- `stale_candidates`: registered candidates stuck in `proposed`/`experimenting` for
  30+ days (`candidate_id`, `state`, `owner`, `updated_at`, `days_since_update`).
- `duplicates`: candidates proposing the same change in the same repository,
  reusing the existing Phase 40 `optimize-check` `duplicate_attempt` conflict type.
- `maintenance_notes`: free-text observations — repeatedly rejected attempt chains
  (reusing `optimize-check`'s `repeated_failed_experiments` warning) and accepted
  candidates whose rollback path has never been exercised.

This command never archives, deletes, or otherwise modifies a candidate; it is
purely descriptive, matching the existing Phase 39/40 convention that decisions and
code changes remain manual.

## Limitations and scope

- Lifecycle tracking is optional per candidate: an existing Phase 39/40 candidate
  that is never `optimize register`ed simply does not appear in `optimize-status` or
  the maintenance report's stale/duplicate buckets.
- Registration and transitions are pure bookkeeping; they do not trigger validation,
  acceptance, rejection, or rollback — those remain the existing `optimize
  validate`/`accept`/`reject` and `rollback record` commands.
- The 30-day staleness window is a fixed, descriptive threshold, not a policy; no
  automatic action follows from it.
- All lifecycle, status, archive and maintenance data lives under the developer
  workspace's `optimization/candidates/*/lifecycle/` directory only. Nothing is
  written to the source checkout, research data root, benchmark artifacts, Humanize
  pilot outputs, or release manifests.
- This phase does not change the meaning of the existing `candidate.json` `status`
  field (`candidate`/`validated`/`accepted`/`rejected`); the new lifecycle `state`
  field is an independent, more granular, opt-in model layered on top of it.
