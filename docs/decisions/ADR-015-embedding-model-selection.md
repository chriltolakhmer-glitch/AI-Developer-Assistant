# ADR-015: Select the Baseline Embedding Model

## Status

Accepted for the Phase 6.1 baseline on 2026-09-27. The choice is a research baseline, not a claim that it is optimal for source-code retrieval. Embedding execution remains subject to [ADR-014](ADR-014-embedding-privacy-policy.md) and the corpus clearance gate in [ADR-013](ADR-013-dataset-snapshot-freeze.md).

## Context

The project needs one reproducible embedding model for a first dense-retrieval baseline over AST semantic chunks. The model must run locally, avoid source-data egress, be practical on the declared Windows CPU environment, and have a stable public identity that can be recorded in experiment manifests. Model selection must be frozen before retrieval evaluation so that the experiment does not tune the encoder against held-out results.

## Candidates

| Model | Strengths | Limitations for this baseline |
|---|---|---|
| `sentence-transformers/all-MiniLM-L6-v2` | Small, fast, widely used sentence-transformer; simple local CPU inference; 384-dimensional output; Apache-2.0 model-card license; straightforward normalization | General-purpose rather than code-specialized; finite input limit requires explicit handling |
| `microsoft/codebert-base` | Pretrained on natural-language/code pairs; relevant code representation research lineage; local weights available | Base encoder is not a ready-made sentence-embedding model; pooling and fine-tuning choices add experimental variables; larger and less direct for a first baseline |
| `BAAI/bge-small-en-v1.5` | Compact local encoder with strong general semantic-search orientation; 384-dimensional output | Primarily general English retrieval; query/instruction conventions must be fixed; less continuity with the project’s existing vector-index decision |
| `intfloat/e5-small-v2` | Compact retrieval-oriented model with documented query/passage conventions; local execution | Requires strict `query:`/`passage:` formatting; that protocol adds another representation variable for code chunks and queries |
| Code-specific models such as GraphCodeBERT | Stronger code-pretraining rationale and useful future comparison candidate | Larger inputs/compute and task-specific pooling or fine-tuning choices increase scope; not needed before the reproducible baseline is established |

## Decision

Select `sentence-transformers/all-MiniLM-L6-v2` as the Phase 6.1 baseline, pinned to immutable revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

The implementation configuration is:

1. Execute locally with SentenceTransformers in inference mode on the declared CPU baseline unless a separately recorded device configuration is approved.
2. Produce 384-dimensional vectors and L2-normalize them before persistence.
3. Use identical model revision, text representation, tokenizer settings, and normalization for corpus chunks and queries.
4. Enforce the model input ceiling explicitly. Do not silently truncate; apply and record a deterministic split-or-reject policy.
5. Record model revision, library versions, Python version, operating system, device, dimensions, normalization, and input policy in every run manifest.

## Rationale

### Reproducibility

The model is a compact, established sentence-transformer with a direct encode-and-normalize workflow. The immutable revision and fixed 384-dimensional output provide a clear artifact identity. Avoiding custom pooling or task-specific fine-tuning reduces degrees of freedom in the first experiment.

### Local execution

The model is small enough for controlled CPU execution and can be acquired once, then used offline. This fits [ADR-014](ADR-014-embedding-privacy-policy.md), which prohibits sending source-derived data to hosted embedding services or LLMs.

### Research suitability

The project needs a transparent general-purpose baseline before comparing retrieval strategies. MiniLM is not selected as code-semantic ground truth; its general semantic behavior makes the dense component interpretable as a baseline. CodeBERT and other code-specialized encoders remain suitable future comparison conditions, but introducing them now would mix model comparison with the first retrieval implementation and add pooling/protocol decisions.

The selection is consistent with [ADR-007](ADR-007-vector-index-selection.md) and the existing Phase 4 technology decision. Replacing it after embedding or retrieval evaluation begins requires a new ADR and a revalidated experiment plan.

## Consequences

- The first embedding implementation must depend on a local SentenceTransformers-compatible runtime and must pass the privacy gate before corpus processing.
- The 256-word-piece input boundary and explicit handling policy are part of the experiment contract; truncation must be measurable and logged without source contents.
- Model quality on code retrieval is an empirical question. The thesis must not describe this baseline as code-specialized or optimal.
- A future model comparison should use the same frozen corpus, chunk representation, query set, evaluation protocol, and artifact handling, with model identity as the controlled independent variable.
- FAISS is not implemented or selected by this ADR; its previously documented design remains a later retrieval milestone.

## References

- [ADR-007: vector index selection](ADR-007-vector-index-selection.md)
- [ADR-014: embedding privacy policy](ADR-014-embedding-privacy-policy.md)
- [ADR-013: dataset snapshot freeze](ADR-013-dataset-snapshot-freeze.md)
- [Sentence Transformers model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [CodeBERT model card](https://huggingface.co/microsoft/codebert-base)
- [BGE small model card](https://huggingface.co/BAAI/bge-small-en-v1.5)
- [E5 small model card](https://huggingface.co/intfloat/e5-small-v2)
