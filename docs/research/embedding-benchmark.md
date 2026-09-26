# Phase 6.2 — Local Embedding Benchmark

Recorded on 2026-09-27. This is a synthetic implementation benchmark, not a frozen-corpus experiment or a retrieval-quality evaluation. No corpus privacy clearance is claimed.

## Method

Run `python -m src.embedding.benchmark` using the protocol in [embedding-implementation.md](../architecture/embedding-implementation.md). Generate 128 distinct short Python function chunks through the existing parser/chunker. Load the pinned MiniLM model from the external cache, warm up with eight chunks, then measure three full 128-chunk transformations with batch size 32. Generation timing includes provenance validation, sorting, token counting, inference, normalization, and creation of metadata records. Acquisition time is excluded. Model-load timing includes Python library imports and cached weight loading.

The process blocks socket connections during model loading, generation, and artifact verification. It compares all embedding records across repeats for exact equality and compares the stored float32 matrix with the generated vectors after loading. Outputs stay under `C:\Apps\Temp\Phase6.2\runs\synthetic-001`; the model acquisition integrity record stays in the external model cache.

## Environment

- Windows CPU runtime; Intel Core i7-13700HX host identification, eight exposed logical CPUs.
- Python 3.14.7; PyTorch 2.14.0; SentenceTransformers 6.1.0; Transformers 5.17.0; NumPy 2.5.3; tokenizers 0.23.2; huggingface-hub 1.33.0.
- Model: `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- One PyTorch thread, CPU float32, seed zero, deterministic algorithms, batch size 32, unit L2 output, 384 dimensions.
- Full installed dependency pins: [requirements-embedding.txt](../../requirements-embedding.txt).

## Results

| Measurement | Result |
|---|---:|
| Inputs / accepted / rejected | 128 / 128 / 0 |
| Cached model load including imports | 4.9974 s |
| Generation, repeat 1 | 0.3643 s |
| Generation, repeat 2 | 0.3954 s |
| Generation, repeat 3 | 0.3732 s |
| Median throughput | **342.99 chunks/s** |
| Artifact save plus verified reload | 0.0494 s |
| Repeated vectors and metadata exactly equal | Yes |
| Network connections blocked throughout measured work | Yes |

The complete test suite passed **34/34 tests**, with no skips, including real model loading/inference, exact repeatability, actual 256/257-token boundary behavior, fail-closed clearance, invalid vectors, deterministic metadata, empty outputs, and storage integrity. The final suite ran in 7.876 seconds; this duration is informational and not a stable performance assertion.

## Interpretation and next-phase readiness

The implementation produces validated normalized matrices and deterministic row mappings suitable for a later FAISS consumer. No FAISS index was built. These short synthetic inputs do not represent the corpus length distribution; do not extrapolate this throughput to the 33,415 frozen chunks. Corpus embedding, rejection coverage measurement, and corpus indexing remain blocked until the outstanding secret/privacy review is completed and recorded. Retrieval effectiveness remains unmeasured.
