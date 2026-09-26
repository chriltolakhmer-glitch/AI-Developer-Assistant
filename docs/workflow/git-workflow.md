# Solo Developer Git Workflow

## Branch Strategy

**Main branch:** `main`

Purpose: Stable thesis project version.

**Feature branches:** `feature/<name>`

**Experiment branches:** `experiment/<name>`

Examples:
- `feature/repository-parser`
- `feature/rag-engine`
- `experiment/ast-retrieval`

## Commit Rules

Format:

```text
type: description
```

Examples:
- `docs: update architecture diagram`
- `research: add literature review`
- `feat: implement repository scanner`
- `fix: resolve parser issue`

## Release Milestones

- `v0.1-research` — Research phase completed
- `v0.2-architecture` — System design completed
- `v0.3-prototype` — Working prototype
- `v1.0` — Final thesis system
