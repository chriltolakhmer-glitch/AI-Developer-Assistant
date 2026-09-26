# Phase 6.2 — Local Embedding Implementation

## Runtime flow

1. Acquire the declared public model revision into an external cache using the dedicated acquisition command. It accepts no source inputs and records SHA-256 hashes of acquired model files.
2. Pass immutable `CodeChunk` records and a local clearance manifest to `EmbeddingPipeline.run`. Validate frozen repository/commit identities and complete privacy review before model loading or tokenization.
3. Recompute chunk identities using the Phase 5.3 identity algorithm, validate paths and line spans, reject duplicates, and sort by chunk ID. `CodeChunk` has no separate content-hash field; the embedding layer derives it from the original UTF-8 content.
4. Load the pinned SentenceTransformer locally on CPU, in float32 evaluation mode, with seed zero, one thread, and deterministic PyTorch algorithms. Library offline and telemetry settings are set before importing the model runtime. No external inference fallback exists.
5. Apply `source-strip-v1`: strip outer whitespace from source, without adding metadata or prompts. Count tokens without truncation, including special tokens. Reject empty text or more than 256 tokens. The rejection ledger records parent ID, token count, and reason; no new child chunks are produced.
6. Encode accepted inputs in batches of 32 by default. Validate row count, dimension, finite values and nonzero norms; normalize to unit L2 length.
7. Write external artifacts into a new directory. Write the run manifest last. Load verification checks hashes, shape, float32 dtype, norms, unique sorted IDs, and row mapping.

Runtime validation failures abort the run; no completed manifest is emitted. A partial directory from an I/O failure is not a valid run and is not overwritten automatically. Detailed errors and source-derived artifacts stay local. Host filesystem permissions, encryption, retention, and audit truthfulness remain operator responsibilities; a clearance file is an attestation, not an automated privacy audit.

## Input and clearance contract

The public API accepts `tuple[CodeChunk, ...]`, an external clearance JSON path, and an external output path. Only repository/commit pairs in `APPROVED_CORPUS` are eligible. The clearance JSON has this shape (placeholders are not valid authorization):

```json
{
  "schema_version": "1.0",
  "snapshot_id": "corpus-snapshot-v1",
  "repositories": [{
    "repository_id": "<approved repository>",
    "commit_sha": "<frozen full SHA>",
    "secret_review": "passed",
    "privacy_review": "passed",
    "unresolved_findings": 0,
    "reviewer": "<reviewer identity>",
    "reviewed_at": "<review date>",
    "audit_record": "<external local audit reference>"
  }]
}
```

Each input snapshot needs exactly one matching clearance record. Missing files, incomplete reviews, unresolved findings, unknown snapshots, and duplicate matching records fail closed. No clearance has been manufactured for the frozen research corpus. Excluded files must be removed upstream before passing eligible chunks; the current contract requires a passed snapshot review.

```python
from pathlib import Path
from src.embedding import EmbeddingPipeline

pipeline = EmbeddingPipeline(Path(r"C:\Apps\Temp\Phase6.2\model-cache"))
manifest = pipeline.run(
    chunks,
    Path(r"C:\Apps\Temp\Phase6.2\privacy-clearance.json"),
    Path(r"C:\Apps\Temp\Phase6.2\runs\approved-run-001"),
)
```

`generate` returns immutable `Embedding` records and rejection records without saving; `run` saves the artifacts. Each embedding contains `chunk_id`, `vector`, and typed `metadata`. The private `_generate_validated` core is used only after production clearance or by generated synthetic fixtures; it is not a corpus execution entry point.

## Storage format

| Artifact | Contents |
|---|---|
| `vectors.npy` | C-contiguous float32 array `(accepted_count, 384)`, unit L2 vectors, no pickle |
| `metadata.json` | Ordered rows with chunk ID, repository, commit, path, entity type, symbol, inclusive lines, original content SHA-256, token count; no source text |
| `rejections.json` | Ordered empty/oversized input decisions and parent IDs |
| `run.json` | Schema, snapshot, model/revision, representation and tokenizer policy, normalization, dimensions, package/runtime versions, CPU settings, timestamp, counts, clearance digest, and artifact SHA-256 hashes |

Vector/metadata rows are deterministic; run timestamps are intentionally variable. Source-derived manifests are confidential even without raw source. All caches and outputs are rejected if their resolved paths are inside this thesis project. Keep them under the external research-data area, separate from read-only source checkouts. Hashes detect accidental corruption, not malicious replacement of both artifacts and manifests.

## Installation, acquisition, and verification

Run from the repository root in PowerShell. The dependency lock records the tested Windows/Python runtime; install into an external environment.

```powershell
python -m venv C:\Apps\Temp\Phase6.2\venv
$embeddingPython = 'C:\Apps\Temp\Phase6.2\venv\Scripts\python.exe'
& $embeddingPython -m pip install -r requirements-embedding.txt
& $embeddingPython -m src.embedding.acquire --cache C:\Apps\Temp\Phase6.2\model-cache
$env:EMBEDDING_MODEL_CACHE = 'C:\Apps\Temp\Phase6.2\model-cache'
& $embeddingPython -m unittest discover -s tests -v
& $embeddingPython -m src.embedding.benchmark --cache $env:EMBEDDING_MODEL_CACHE --output C:\Apps\Temp\Phase6.2\runs\synthetic-001
```

Acquisition requires network access for public weights only. Inference uses `local_files_only=True`, the pinned revision, and `trust_remote_code=False`, as supported by the [SentenceTransformer API](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html). Run acquisition in a fresh process before offline execution. The benchmark blocks socket connections during loading, generation, and storage; it uses 128 generated short Python functions, an eight-input warm-up, and three timed repeats. It checks identical repeated outputs and exact float32 save/load round trips. Ordinary unit tests use a controlled fake encoder; setting `EMBEDDING_MODEL_CACHE` also enables the real-model offline test.

## Readiness boundary

The [recorded synthetic benchmark](../research/embedding-benchmark.md) measured 342.99 chunks/s with exact repeated outputs; all 34 tests passed, including real offline inference. Performance applies only to the documented fixture and runtime.

The output contract supplies the matrix and row mapping needed for future FAISS indexing. The reject policy can substantially reduce corpus coverage and must be measured after privacy clearance. No corpus embedding run or retrieval-quality claim follows from the synthetic benchmark. The nine-snapshot privacy gate remains open.
