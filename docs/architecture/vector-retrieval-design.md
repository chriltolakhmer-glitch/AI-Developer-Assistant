# Phase 6.3.1 — Local FAISS Vector Retrieval

## Scope and runtime flow

`src/retrieval/` consumes the completed Phase 6.2 embedding artifacts. It implements exact dense vector search, without reading source checkouts or calling network services. Natural-language query encoding is not part of this vector-index boundary; callers provide a query vector from the same pinned MiniLM model, `source-strip-v1` representation, and runtime contract.

1. `VectorIndex.build` validates the embedding run's model, immutable revision, representation, normalization, dimension, input policy, and frozen snapshot identifier.
2. Validate the requested repository/commit against the local privacy clearance and approved corpus. Require the clearance file's SHA-256 to match the embedding run. A changed or revoked clearance fails closed and requires regenerated approved artifacts.
3. Use the Phase 6.2 artifact loader to verify input checksums, vectors, metadata rows, and counts. Select only the requested repository/commit from a potentially combined embedding run. Reject snapshots without accepted vectors.
4. Recompute each chunk ID from its provenance and original content hash. Validate relative paths, entity types, line spans, and token counts; preserve the metadata in immutable records. Remap selected rows to contiguous local positions in ascending chunk-ID order.
5. Add the normalized float32 matrix to CPU `IndexFlatIP(384)`, with one FAISS thread. Stored vectors are validated rather than silently renormalized or re-embedded.
6. Search using one finite, nonzero 384-dimensional query vector. Normalize the query to unit L2 length. Score all index rows with FAISS, sort by descending score and ascending chunk ID, then return up to `k` results (default 50).

With normalized vectors, inner-product search yields cosine similarity, following the [FAISS metric documentation](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances). Negative similarities remain valid results. Scores are raw float32 inner products and can differ slightly from mathematical cosine due to rounding; no rounding or score threshold is applied.

## Determinism and results

FAISS's top-k heap can select an arbitrary subset of equal-score rows at the cutoff. Requesting every row before applying the project's total order ensures ties are resolved consistently even when `k=1`. This exact baseline uses O(N) candidate storage and O(N log N) sorting per query. It is intentionally simple for the bounded per-repository corpus; future optimization must preserve the same tie contract.

`search(query_vector, k=50)` returns an immutable tuple of `SearchResult` records:

| Field | Meaning |
|---|---|
| `chunk_id` | Stable Phase 5.3 identity |
| `rank` | One-based rank after deterministic ordering |
| `score` | Cosine similarity via normalized inner product |
| `strategy` | `dense` |
| `metadata` | Repository, commit, path, entity type, qualified name, inclusive source lines, original content SHA-256, tokenizer count |

`k` must be a positive integer; values larger than the index return all available rows. Wrong dimensions, empty/zero vectors, NaN, infinity, invalid provenance, or incompatible manifests fail. The library cannot infer the originating model from an arbitrary numeric query vector; matching the query encoder is the caller's responsibility. Text-query encoding and benchmark evaluation require later integration.

## Persistence and local-data boundary

`save` writes a new external directory and never overwrites an existing run:

| File | Contents |
|---|---|
| `index.faiss` | FAISS binary exact inner-product index |
| `metadata.json` | Ordered row-to-chunk mapping and full source-free provenance |
| `manifest.json` | Schema `1.0`, snapshot, index type, metric, dimension/count, tie policy, runtime, embedding-run manifest and original manifest hash, artifact hashes |

The manifest is written last; failed partial writes do not constitute a valid index. Binary serialization goes through Python byte I/O to support Unicode Windows paths. All model/preprocessing/runtime provenance from the embedding manifest is retained. The source embedding-run hash links the index to the original external run; it is lineage evidence rather than a signature.

`load` requires current local clearance, validates the index contract and matching FAISS/NumPy versions, verifies both artifact hashes before native deserialization, and checks the decoded index type, metric, dimensions, count, normalized vectors, and metadata identities. Rebuild after model, representation, chunk, or library changes. Repeated build/save/load under the tested runtime preserves ranking and artifact bytes; cross-hardware floating-point equality is not promised.

Only load trusted local artifacts. As the [FAISS I/O documentation](https://github.com/facebookresearch/faiss/wiki/Index-IO,-cloning-and-hyper-parameter-tuning) notes, native deserialization does not establish file safety. Checksums detect accidental corruption but cannot authenticate an index if an attacker can replace its manifest too.

Index artifacts, clearance files, and embedding inputs must resolve outside the thesis Git project. Keep them in the controlled research-data area, outside source checkouts, with access controls and retention rules from ADR-014. No source text or raw query/vector logging is introduced. Clearance is checked on build/load; dispose of an already-loaded index when clearance is revoked.

## Usage and validation

Install the pinned retrieval requirements into the external Phase 6 environment:

```powershell
$retrievalPython = 'C:\Apps\Temp\Phase6.2\venv\Scripts\python.exe'
& $retrievalPython -m pip install -r requirements-retrieval.txt
$env:EMBEDDING_MODEL_CACHE = 'C:\Apps\Temp\Phase6.2\model-cache'
& $retrievalPython -m unittest discover -s tests -v
```

After corpus privacy clearance and an approved embedding run:

```python
from pathlib import Path
from src.retrieval import VectorIndex

index = VectorIndex.build(
    Path(r"C:\Apps\Temp\Phase6.2\runs\approved-run-001"),
    Path(r"C:\Apps\Temp\Phase6.2\privacy-clearance.json"),
    repository_id=repository_id,
    commit_sha=commit_sha,
)
index.save(Path(r"C:\Apps\Temp\Phase6.3\indexes\snapshot-001"))
results = index.search(query_vector, k=10)
```

These are API examples, not a claim that an approved corpus run exists. Tests generate source fixtures and synthetic vectors locally; test-only clearance records do not authorize research corpus processing. The validation record is [vector-retrieval-validation.md](../research/vector-retrieval-validation.md).

The next phase is BM25 lexical retrieval, with a frozen tokenization policy and the same eligible chunk IDs, followed by RRF integration under [ADR-017](../decisions/ADR-017-hybrid-retrieval.md). No BM25, RRF, LLM, UI, or autonomous-agent implementation is included here.
