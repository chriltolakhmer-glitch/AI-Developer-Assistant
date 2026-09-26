# Benchmark Design

**Status:** Phase 3 blueprint — no implementation exists yet. Concretizes the benchmark format described in [dataset-design.md](dataset-design.md).

## Question Format

Each benchmark question is authored as natural developer language — it must not directly reveal the target file/function name unless the question's category specifically tests identifier lookup. Each question must be answerable from static repository evidence at the pinned commit (no external runtime behavior unless represented in source/config).

```yaml
id: <repository-slug>-<3-digit-sequence>
repository: <repository URL or identity>
commit: <pinned commit SHA>
category: architecture_understanding | code_navigation | dependency_understanding | bug_investigation
question: "Where is authentication implemented?"
```

## Ground Truth Format

Each question carries one or more gold evidence entries, kept in a separate file/table from any retriever output:

```yaml
id: <repository-slug>-<3-digit-sequence>
expected_files:
  - auth.py
expected_functions:
  - authenticate()
expected_spans:
  - file: auth.py
    symbol: authenticate
    lines: [42, 58]
relevance_grade: primary | supporting
annotation_rationale: "Direct implementation of the credential-check flow referenced by the login route."
ambiguity_notes: "None." # or explanation if the question could plausibly map to more than one file
```

### Worked example

```yaml
question:
  id: sample-repo-001
  repository: <repository URL>
  commit: <pinned commit SHA>
  category: code_navigation
  question: "Where is authentication implemented?"

ground_truth:
  expected_files:
    - auth.py
  expected_functions:
    - authenticate()
  expected_spans:
    - file: auth.py
      symbol: authenticate
      lines: [42, 58]
  relevance_grade: primary
  annotation_rationale: "authenticate() in auth.py performs the credential check called by the login route."
  ambiguity_notes: "None."
```

## Evidence Annotation Rules

1. **Manual annotation only:** gold labels are created by reading the pinned source directly; unreviewed LLM output is never used as ground truth.
2. **Exact spans required:** every gold entry records file path and line range at the pinned commit, so it can be mechanically re-verified against that exact snapshot.
3. **Graded relevance:** each evidence item is labeled `primary` (directly answers the question) or `supporting` (necessary context but not the core answer), to support nDCG scoring.
4. **Multi-hop questions:** for dependency-understanding questions requiring multiple files/functions, every necessary hop is annotated individually rather than collapsed into one entry.
5. **Ambiguity disclosure:** if a question could plausibly map to more than one valid implementation, this is recorded in `ambiguity_notes` rather than silently picking one answer.
6. **Separation from retriever output:** ground-truth files/tables are stored independently of any system output to prevent contamination of the evaluation.
7. **Second-reviewer spot check:** a predeclared ≥20% sample of questions is independently reviewed where a second reviewer is available; disagreements are adjudicated and recorded. If unavailable, this is documented as a single-annotator limitation.
8. **Pilot exclusion:** any question used during pilot annotation-instruction refinement, or that informed system/fusion tuning, is excluded from the final reported benchmark.

## 108-Question Benchmark Structure

Following [dataset-design.md](dataset-design.md): **12 questions per repository × 9 repositories = 108 questions**, with 3 questions per category per repository.

| Category | Questions per repository | Total across 9 repositories |
|---|---:|---:|
| Architecture understanding | 3 | 27 |
| Code navigation | 3 | 27 |
| Dependency understanding | 3 | 27 |
| Bug investigation | 3 | 27 |
| **Total** | **12** | **108** |

Within each repository's 12 questions, authors should mix:
- Identifier-heavy wording vs. conceptual wording.
- Single-file evidence vs. cross-file evidence.
- At least one deliberately harder question per category (e.g., ambiguous naming, indirect call chains).

A held-out subset (by repository or by question, decided during annotation) is kept separate from any tuning of the retrieval fusion strategy, to prevent leakage that would inflate the proposed system's apparent advantage.

See [repository-corpus-selection.md](repository-corpus-selection.md) for the repositories this benchmark will be built against, and [experiment-design.md](experiment-design.md) for how it is used in the controlled comparison.
