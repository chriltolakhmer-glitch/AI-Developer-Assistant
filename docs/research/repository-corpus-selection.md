# Repository Corpus Selection

**Status:** Phase 3 shortlist template superseded by the Phase 4 screened and pinned result in [repository-corpus-final.md](repository-corpus-final.md). Retained for criteria and selection rationale; its placeholder table is not the selected corpus.

## Repository Selection Criteria

Restated from [dataset-design.md](dataset-design.md) for direct use during candidate screening:

1. Clear project purpose with substantive, parseable Python source (no tutorial fragments, no generated-only code).
2. Publicly accessible under a research-compatible license; license recorded and complied with.
3. No credentials, personal data, or confidential material present.
4. Varied application domains and code organization across the sample (avoid single-framework bias).
5. Sufficient identifiable functions/classes and cross-file structure to support cross-file evidence questions.
6. Commit SHA pinned; download date, eligible file/LOC counts, parser success/failure and exclusions recorded.
7. The three previously analyzed assistant repositories (`codebase-rag`, `Codebase-RAG-Assistant`, `ai-codebase-assistant`) are excluded from the primary evaluation sample to avoid bias toward already-studied systems; they may be used only for pilot/tooling checks.

## Python-Only Scope

The primary study indexes and evaluates **Python source only**. Non-Python files in a selected repository are recorded for transparency (language mix, total repo size) but excluded from chunking, indexing and the query benchmark. This bounds parser/annotation effort for a solo researcher (see [ADR-003](../decisions/ADR-003-system-boundary.md)).

## Repository Size Categories

Sizing is based on eligible Python LOC after a fixed ignore/filter policy (vendor, generated, test-fixture, and build-output directories excluded; blank/comment-only lines excluded from the LOC count).

| Category | Eligible Python LOC | Target sample |
|---|---:|---:|
| Small | 1,000–10,000 | 3 repositories |
| Medium | >10,000–50,000 | 3 repositories |
| Large | >50,000–150,000 | 3 repositories |

## Candidate Repositories

**Historical Phase 3 placeholder (superseded):** The table below records the shortlist state before the Phase 4 screening. It is not the active corpus; use [repository-corpus-final.md](repository-corpus-final.md) for the selected repositories and their measured evidence.

| Category | Candidate repository (placeholder) | Domain | License to verify | Pinned commit | Status |
|---|---|---|---|---|---|
| Small | *TBD* | *TBD* | *TBD* | *not pinned* | Candidate |
| Small | *TBD* | *TBD* | *TBD* | *not pinned* | Candidate |
| Small | *TBD* | *TBD* | *TBD* | *not pinned* | Candidate |
| Medium | *TBD* | *TBD* | *TBD* | *not pinned* | Candidate |
| Medium | *TBD* | *TBD* | *TBD* | *not pinned* | Candidate |
| Medium | *TBD* | *TBD* | *TBD* | *not pinned* | Candidate |
| Large | *TBD* | *TBD* | *TBD* | *not pinned* | Candidate |
| Large | *TBD* | *TBD* | *TBD* | *not pinned* | Candidate |
| Large | *TBD* | *TBD* | *TBD* | *not pinned* | Candidate |

Before a candidate moves from "Candidate" to "Selected," it must pass all seven selection criteria above and have its commit SHA, LOC count, and license recorded in this table.

## Selection Justification

- **Historical Phase 3 rationale for a placeholder table:** Repository selection required external license and LOC screening, which Phase 3 had not performed. Phase 4 has now completed the documented screening; remaining pre-index checks are listed in [repository-corpus-final.md](repository-corpus-final.md).
- **Why three size strata of three repositories each:** Matches the sample size proposed in [dataset-design.md](dataset-design.md) — large enough to observe size-related retrieval/cost effects, small enough to be annotated (108 questions total) by a single researcher within thesis timelines.
- **Why domain diversity is a hard criterion:** Reduces the risk that observed retrieval effects are specific to one coding style or framework rather than generalizable within the Python-only scope.
- **Why exclude the three previously analyzed assistant repositories from the primary sample:** They were the subject of the prior static analyses that motivated this thesis; using them as the evaluation corpus would bias the benchmark toward systems whose limitations already informed the research design.

**Next action:** Complete the pre-index secret/privacy audit and scanner-manifest verification documented in [repository-corpus-final.md](repository-corpus-final.md) before annotation or indexing.
