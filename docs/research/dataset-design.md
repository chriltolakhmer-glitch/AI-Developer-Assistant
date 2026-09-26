# Dataset Design

**Status:** Phase 2 blueprint — no implementation exists yet. Supports [research-question.md](research-question.md) and [evaluation-plan.md](evaluation-plan.md).

## Repository Selection Criteria

Candidate repositories must satisfy all of the following before inclusion:

1. Clear project purpose with substantive, parseable Python source (exclude tutorial fragments and generated-only code).
2. Publicly accessible under a license compatible with research use; license recorded and complied with.
3. No credentials, personal data, or confidential material present (verified before indexing); source is not sent to hosted LLMs unless the study protocol explicitly permits it.
4. Varied application domains and code organization across the sample, to limit selection bias (avoid choosing every repository from the same framework/domain).
5. Sufficient identifiable functions/classes and cross-file structure to support evidence-grounded, cross-file questions.
6. Commit SHA pinned; download date, eligible file/LOC counts, parser success/failure and exclusions recorded for every repository.
7. The three previously analyzed assistant repositories (`codebase-rag`, `Codebase-RAG-Assistant`, `ai-codebase-assistant`) are not used as the primary evaluation sample — using them would bias the benchmark toward systems already studied. They may be used only for pilot/tooling checks if license/scope permits, and pilot use must be reported separately from held-out evaluation.

## Programming Language Scope

**Python only**, for the primary study. This bounds parser and annotation effort for a solo researcher and avoids language coverage becoming a confound in the primary retrieval comparison. Other languages present in a selected repository are recorded (for transparency) but not indexed or evaluated in the primary experiment. Multi-language extension is explicitly out of scope for this thesis (see [ADR-003](../decisions/ADR-003-system-boundary.md)) and may be noted as future work only.

## Repository Size Categories

Sizing is based on eligible Python LOC after the same ignore/filter policy is applied to every repository. The exact LOC-counting rule (e.g., whether blank/comment-only lines count) must be fixed and documented before sampling.

| Category | Eligible Python LOC | Planned sample |
|---|---:|---:|
| Small | 1,000–10,000 | 3 repositories |
| Medium | >10,000–50,000 | 3 repositories |
| Large | >50,000–150,000 | 3 repositories |

This nine-repository target is a **proposed, feasible sample**, not a claim of coverage across all software projects. If a size category proves infeasible given available repositories or compute, the protocol must be revised and documented *before* final evaluation, not silently adjusted afterward.

## Query Benchmark Format

Each benchmark item is a repository-question pair recording:

- Repository URL/identity and immutable commit SHA.
- Question text and question category (see below).
- Gold relevant file(s).
- Gold supporting function/class or exact line span(s).
- Relevance grade (for nDCG — e.g., primary evidence vs. supporting/context evidence).
- Annotation rationale and ambiguity notes.

Gold labels are stored separately from any retriever output to prevent contamination.

### Question categories

| Category | Example | Ground truth to annotate |
|---|---|---|
| Architecture understanding | "What is the authentication workflow?" | Relevant route/controller/service files and ordered supporting functions where statically traceable |
| Code navigation | "Where is user registration implemented?" | Primary implementation file and exact function/class span(s) |
| Dependency understanding | "How does payment processing work?" | Relevant callers/callees, definitions and cross-file evidence; each necessary hop annotated |
| Bug investigation | "Why could this function fail when the input is empty?" | Function plus source conditions/guards, phrased as a source-based possibility (not a claimed runtime defect) |

**Proposed target:** 12 questions per repository (3 per category) × 9 repositories = **108 questions total**. Questions must mix identifier-heavy vs. conceptual wording and single-file vs. cross-file evidence across the size strata. A held-out subset (by repository or by question) is kept separate from any tuning to reduce leakage.

## Ground Truth Creation Method

1. **Pilot first:** annotate one separate (non-benchmark) repository or a small subset to refine question-writing and labeling instructions; exclude pilot queries that informed system tuning from final results.
2. **Single primary annotator** (the thesis author) creates gold labels by manually reading the pinned source, not by using unreviewed LLM-generated labels.
3. **Second-reviewer spot check:** a predeclared sample (target ≥ 20% of questions) is independently reviewed, with disagreements adjudicated. If no second reviewer is available, this is documented as a single-annotator limitation and no inter-rater agreement figure is reported (avoiding a false claim of validation).
4. **Traceability:** every gold label references exact file path and line span at the pinned commit so it can be mechanically re-verified.
5. **Freeze before evaluation:** the finalized benchmark (minus any deliberately held-out portion) is frozen before running the retrieval strategies under comparison.

See [experiment-design.md](experiment-design.md) for how this dataset is used in the controlled experiment.
