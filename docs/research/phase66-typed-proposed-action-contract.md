# Phase 66 — Typed Proposed Action Contract

## Outcome

Phase 66 formalizes the read-only implementation planner as a reviewable proposal object rather than an ad hoc dictionary. The planner still does not edit source, execute tests, or mutate the repository. It records a `proposed_action` object inside the stable `developer-local-implementation-plan` payload so a human reviewer can inspect the evidence, target scope, and approval boundary before any implementation work begins.

```python
{
  "proposed_action": {
    "action_id": "proposal-<hash>",
    "action_type": "implementation_plan",
    "source_mode": "developer-local-implementation-plan",
    "schema_version": "1.0",
    "goal": "Add validation to run",
    "repository_path": "C:/.../repository",
    "target_paths": ["src/app.py"],
    "target_symbols": ["run"],
    "evidence_refs": [
      {
        "file_path": "src/app.py",
        "symbol": "run",
        "role": "primary_target",
        "evidence_types": ["retrieval_evidence", "changed_code"],
        "current_index_evidence": true,
        "reason": "..."
      }
    ],
    "authority_required": "human_approval_required",
    "required_mutations": [],
    "status": "proposed",
    "execution_allowed": false
  }
}
```

## Contract purpose

The `proposed_action` object is a bounded, reviewable representation of the planned change. It makes the intent explicit and separates the planning evidence from any later execution authority.

The contract is intentionally conservative:

- It describes the goal, repository, and candidate targets.
- It records direct evidence references used in the plan.
- It remains read-only and human-approval gated.
- It never declares mutation intent or execution permission.
- It remains JSON-ready for inspection, logs, and future review tools.

## Required fields

The Phase 66 contract includes the following fields:

- `action_id`: stable proposal identifier derived from repository path and goal.
- `action_type`: fixed value `implementation_plan`.
- `source_mode`: fixed value `developer-local-implementation-plan`.
- `schema_version`: fixed version `1.0`.
- `goal`: the original developer goal text.
- `repository_path`: repository root the proposal was generated from.
- `target_paths`: sorted list of relevant implementation file paths.
- `target_symbols`: relevant qualified symbols from the implementation targets.
- `evidence_refs`: evidence-backed file/symbol references with role and basis.
- `authority_required`: fixed value `human_approval_required`.
- `required_mutations`: empty array for the planning-only phase.
- `status`: fixed value `proposed`.
- `execution_allowed`: fixed value `false`.

## Boundary behavior

This contract does not grant execution authority. It is not a patch, not an approval, and not a deferred action to be auto-executed. The planner may recommend validation order, but it does not run tests or mutate the repository.

This matches the Phase 65 behavioral boundary: planning remains read-only, local-source evidence remains the only source of truth, and dynamic behavior still needs human confirmation.

## Evidence handling

The contract binds the proposal to the same evidence set used by the implementation plan:

- changed-code evidence
- static relationship evidence
- retrieval evidence from a current local index
- related context and unresolved diagnostics

If the plan has no direct implementation targets, the contract falls back to current retrieval evidence for reviewability. If no evidence is available, the proposal still records the repository and the goal while leaving `target_paths` and `target_symbols` empty.

## Validation status

Focused coverage confirms the proposal contract is created and remains reviewable without creating any mutation instructions or execution authority. The Phase 66 unit test verifies:

- the contract is present under `proposed_action`
- the action type, authority, source mode, and schema are stable
- the proposal identifier is generated deterministically
- the goal and target paths are captured
- evidence references are populated
- no mutations are required at plan time

## Completion boundary

Phase 66 is complete when the reviewable proposal contract is part of the plan payload and validated by the affected tests. It remains intentionally separate from any later phase that may support controlled patch drafting or execution.
