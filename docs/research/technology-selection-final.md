# Technology Selection — Phase 4

**Status:** Accepted for the initial RQ1 research prototype, subject to the explicit pre-implementation smoke checks below. No source implementation or retrieval-quality claim is made here.

## Frozen primary choices

| Concern | Selection | Fixed configuration / rationale |
|---|---|---|
| Parser | Python standard-library `ast` | Python-only scope; no external grammar. Record Python interpreter version, syntax errors, and labeled fallback use. This confirms the Phase 3 working default. |
| Vector index | CPU FAISS `IndexFlatIP` (exact flat inner-product search) | L2-normalize each embedding and query, so inner product is cosine similarity. Use one index per repository+commit; keep deterministic chunk-ID-to-vector-position mapping and full provenance in a versioned sidecar. This avoids needing vector-store metadata filtering, makes repository isolation explicit, and removes approximate-neighbor parameters from the dense baseline. |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2`, local inference | Pin model revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; 384-dimensional vectors; Apache-2.0 model-card license. Use identical model revision, preprocessing, normalization, and inference settings for chunks and queries. Keep source and queries local. |
| Embedding input ceiling | At most 256 model word pieces | The model card says longer inputs are truncated at 256 word pieces. Make truncation explicit and logged; do not silently treat a longer AST chunk as fully embedded. The chunking stage must either bound the embedded text or deterministically split it while retaining provenance. |
| Hybrid fusion | Equal-weight, two-list Reciprocal Rank Fusion | Fuse dense and BM25 lists with one-based ranks: `score(d) = 1/(60 + rank_dense(d)) + 1/(60 + rank_bm25(d))`; absent documents contribute zero. Use rank constant 60, input window 50 per retriever, stable chunk-ID tie-break, and retain the fused scores/ranks. No learned weights or query-specific routing. |
| RRF evaluation output | Top 50 fused candidates retained; report Recall@5 and Recall@10, MRR@10, and nDCG@10 | Retrieve up to 50 per component; de-duplicate by stable chunk ID; rank the union by RRF, breaking ties by chunk ID. Retain up to 50 raw/fused results. Freeze these cutoffs before final runs. |

## Vector index decision: FAISS rather than Chroma

Both libraries can store/search vectors and Chroma offers convenient metadata filters. For this bounded experiment, however, each search is already scoped to one repository and immutable commit. Separate per-snapshot FAISS indexes provide that isolation without metadata predicates; a sidecar holds chunk text and source coordinates. `IndexFlatIP` gives exact search after normalization and avoids approximate-index settings or training as a confound in the dense-only baseline. The indexed corpus is bounded by the screened nine-repository sample, so the project does not need Chroma's database and metadata-management features to answer RQ1.

FAISS's documented CPU packages include Windows x86-64 support through Conda; the current `faiss-cpu` PyPI package also lists Windows classifiers. Because the working environment is Windows and native packages can vary by Python/platform version, a clean-environment install/import, save/load, normalized-search, and repeatability smoke check is a **gate before implementation dependencies are frozen**. If the declared target environment cannot install a supported FAISS build without a custom native build, stop and record a superseding ADR before switching to Chroma; do not quietly change the index underneath evaluation.

Chroma was not rejected as unsuitable in general: it is a reasonable alternative for a persistent metadata-rich application. Here its extra persistence/configuration surface does not compensate for using an exact, single-purpose per-snapshot index with an explicit metadata sidecar.

## Embedding choice and limitations

The local MiniLM model avoids service access, per-request fees, network/version drift, and transmission of repository source to an embedding provider. Its fixed 384-dimensional output and modest model size suit a reproducible solo-researcher baseline. The model is a general sentence-embedding model, not a code-specialized model; the result must therefore be described as a fixed baseline choice, not as the best code-search model. Its 256-wordpiece limit makes explicit truncation/AST-chunk length handling necessary. Report model ID, immutable revision, license, SentenceTransformers/Transformers/PyTorch versions, Python version, device, inference options, and any truncation/failure counts with every run. Do not tune or swap the model after looking at held-out query outcomes.

## RRF rationale and freeze boundary

RRF avoids directly mixing BM25 scores with cosine similarities, whose numeric scales are not comparable. The rank constant 60 is the widely documented conventional RRF constant; window 50 preserves a useful candidate union while keeping the experiment bounded. Equal retriever weight is fixed. These are **predeclared starting parameters**, not empirically optimized settings or a claim of optimality. Any tuning must use only a separately identified pilot not represented in the final benchmark; record and freeze settings before the held-out evaluation. For RQ1, run BM25-only, dense-only, and hybrid on identical pinned chunks and queries, with no LLM calls.

## Reproducibility and implementation gate

Before adding `src/` code or freezing environment dependencies:

1. Test supported FAISS installation and exact inner-product semantics in a clean environment on the intended OS/Python version; record the resolved FAISS/NumPy versions and smoke-test outcome.
2. Verify the model revision is fetchable offline after one controlled download, its license is recorded, output dimension is 384, and input-length behavior is explicitly tested at and above 256 word pieces.
3. Specify deterministic chunk-ID creation, sidecar schema, normalization, tie-breaking, chunk truncation/splitting, and RRF rank-window/cutoff configuration in versioned run metadata.
4. Freeze versions, hardware/device, source filter, chunking, tokenizer/preprocessing, retrieval windows, and evaluation cutoffs before held-out runs. Re-index whenever the model or chunk representation changes.
5. Keep retrieval evaluation retrieval-only; report Recall@k, MRR@10, nDCG@10 and failure logs as specified in [evaluation-plan.md](evaluation-plan.md).

## Sources

- [FAISS documentation](https://github.com/facebookresearch/faiss) and [installation guide](https://github.com/facebookresearch/faiss/blob/main/INSTALL.md): exact/flat search, normalized-vector cosine via inner product, and supported installation options.
- [FAISS CPU package on PyPI](https://pypi.org/project/faiss-cpu/): package metadata and platform classifiers checked on 2026-09-26.
- [Chroma metadata filtering](https://docs.trychroma.com/docs/querying-collections/metadata-filtering): metadata filtering capability considered in the comparison.
- [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2): intended use, 384 dimensions, 256-wordpiece truncation, and Apache-2.0 license; immutable revision recorded above.
- [Reciprocal Rank Fusion documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html): rank-fusion formula, rank constant, and per-retriever result windows. The fixed settings here are this thesis protocol, not copied service configuration.

This Phase 4 selection supersedes the technology deferral in [ADR-005](../decisions/ADR-005-technology-selection.md). The vector-store decision is recorded in [ADR-007](../decisions/ADR-007-vector-index-selection.md); corpus identity and screening are recorded in [repository-corpus-final.md](repository-corpus-final.md).