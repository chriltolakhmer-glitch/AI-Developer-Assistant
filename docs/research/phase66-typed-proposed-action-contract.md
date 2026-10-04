# Phase 66 — Typed Proposed Action Contract

## Outcome

Phase 66 introduces a typed, review-only proposal contract for the developer implementation planner. The planner still does not edit source, write patches, execute tests, or perform repository mutations. It emits a `proposed_action` object inside the `developer-local-implementation-plan` payload so a reviewer can inspect the target scope, repository identity, evidence basis, and approval boundary before any implementation work begins.

```python
{
  "proposed_action": {
    "action_id": "proposal-<stable-hash>",
    "action_type": "implementation_plan",
    "source_mode": "developer-local-implementation-plan",
    "schema_version": "1.0",
    "goal": "Add validation to run",
    "repository_path": "C:/.../repository",
    "repository_id": "<repository-id>",
    "base_reference": "HEAD",
    "base_commit": "<sha>",
    "current_commit": "<sha>",
    "working_tree_sha256": "<sha256>",
    "target_paths": ["src/app.py"],
    "target_symbols": ["run"],
    "evidence_refs": [{
      "file_path": "src/app.py",
      "symbol": "run",
      "role": "primary_target",
      "evidence_types": ["retrieval_evidence", "changed_code"],
      "current_index_evidence": true,
      "reason": "..."
    }],
    "unresolved_evidence": [{
      "type": "index_not_current",
      "action": "manual_review_required",
      "evidence": "..."
    }],
    "authority_required": "human_approval_required",
    "required_mutations": [],
    "status": "proposed",
    "execution_allowed": false
  }
}
```

## Contract purpose

The `proposed_action` object is the canonical planning contract. It is narrow, explicit, serializable, and testable. It separates the plan from the later execution layer and captures the repository and evidence state that justified the recommendation.

The contract is intentionally conservative:

- it records the goal, repository identity, and base state
- it preserves the current target paths and symbols
- it stores evidence references and unresolved evidence for review
- it keeps the review object non-mutating and execution-blocked
- it remains serializable to JSON for logs, audits, or future review tooling

## Required fields

The Phase 66 contract includes the following fields:

- `action_id`: stable identifier derived from the proposal state, prefixed with `proposal-`
- `action_type`: fixed value `implementation_plan`
- `source_mode`: fixed value `developer-local-implementation-plan`
- `schema_version`: fixed value `1.0`
- `goal`: normalized developer goal text
- `repository_path`: repository root associated with the proposal
- `repository_id`: stable repository identity used to bind the proposal to the underlying repo state
- `base_reference`: repository reference used as the baseline, defaulting to `HEAD`
- `base_commit`: commit at the baseline reference when available
- `current_commit`: current repository commit when available
- `working_tree_sha256`: working-tree fingerprint used to detect state changes
- `target_paths`: sorted repository-relative paths for the planned implementation scope
- `target_symbols`: relevant qualified symbols from the implementation targets
- `evidence_refs`: direct evidence references used to justify the proposal
- `unresolved_evidence`: unresolved or ambiguous evidence, preserved explicitly instead of hidden
- `authority_required`: fixed value `human_approval_required`
- `required_mutations`: always empty for Phase 66
- `status`: fixed value `proposed`
- `execution_allowed`: fixed value `false`

## Validation and serialization rules

The proposal must validate at construction-time and at serialization boundaries where necessary:

- `status` must remain `proposed`
- `execution_allowed` must remain `false`
- `required_mutations` must remain empty
- `authority_required` must remain `human_approval_required`
- `action_type` must be limited to `implementation_plan`
- `repository_id` and `repository_path` are required
- target paths must remain repository-relative and may not escape the repository root
- `action_id` must start with `proposal-`
- evidence references must be mapping objects with a list-valued `evidence_types`

The deterministic identity is derived from repository state and proposal scope rather than timestamps or randomness. If the repository state, base commit, working-tree hash, goal, or target set changes, the proposal identity changes as well.

## Boundary behavior

This contract does not grant execution authority and is not a patch or approval record. The planner may identify recommended validation steps, but it does not execute them and it does not mutate the repository. The proposal exists to make the review boundary explicit and to preserve unresolved evidence without pretending it is a certainty.

This remains consistent with the read-only Phase 65 planning boundary: repository evidence is the source of truth, human approval is required before any later execution work, and the plan remains separate from any future implementation execution layer.

## Evidence handling

The proposal binds to the same evidence set used by the implementation plan and preserves uncertainty instead of flattening it away:

- changed-code evidence
- static relationship evidence
- retrieval evidence from the current local index
- unresolved diagnostics and ambiguous relationships

When no direct targets are available, the proposal still keeps goal, repository, and base-state metadata. When there is no evidence, the proposal remains valid but keeps `target_paths`, `target_symbols`, and `evidence_refs` empty while preserving `unresolved_evidence` for review.

## Completion gate

Phase 66 is complete when the reviewable proposal contract is part of the plan payload, the deterministic identity and repository/base metadata are present, unresolved evidence is preserved, and the affected validation tests pass. The contract remains intentionally separate from future execution phases and should not be promoted into an execution or mutation object.
