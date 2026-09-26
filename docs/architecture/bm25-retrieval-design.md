# Phase 6.3.2 — BM25 Lexical Retrieval

## Pipeline and boundaries

`BM25Index.build` accepts a tuple of `CodeChunk` records, an external completed embedding-run directory, a clearance path, and one repository/commit identity. It validates the embedding contract, clearance, checksums, accepted metadata, and chunk identities before tokenizing source. It indexes every accepted ID for that snapshot, in ascending chunk-ID order. Missing accepted chunks, duplicate IDs, altered source, and mixed-snapshot inputs fail. Additional validated chunks not in the accepted embedding inventory are omitted, preserving the same retrieval population as FAISS.

The embedding directory is an inventory and provenance dependency, not an inference step. No model is loaded and no vectors are generated. The shared artifact loader verifies the embedding matrix as part of checking the complete Phase 6.2 artifact set. Privacy clearance must match the embedding run and still pass the review checks on build and reload.

`BM25Index` stores immutable ordered token tuples, metadata, document lengths, average length, term-frequency postings, and document-frequency-derived IDF values. It does not retain raw source text. `BM25Search` accepts query text, applies the same tokenizer, scores matching postings, orders all matches deterministically, and applies the requested cutoff. All work is local and no source, tokens, queries, or scores are sent to an external service.

## Versioned tokenization

`identifier-components-v1` uses Python's Unicode `\w+` extraction (letters, numbers, underscores), discarding underscore-only words. Punctuation and operators delimit words and are not searchable. Whole words are casefolded. Before casefolding, split underscore boundaries, ASCII lowercase/digit-to-uppercase transitions, acronym-to-capitalized-word transitions, and ASCII letter/digit boundaries. Append each distinct component once per original occurrence, excluding a component identical to the full token. Preserve repeated occurrences across the document.

Examples:

| Input | Emitted tokens |
|---|---|
| `load_user_profile` | `load_user_profile`, `load`, `user`, `profile` |
| `parseHTTPResponse` | `parsehttpresponse`, `parse`, `http`, `response` |
| `HTTP2` | `http2`, `http`, `2` |
| `__init__` | `__init__`, `init` |
| `foo_foo` | `foo_foo`, `foo` |

Non-ASCII words and casefold expansions are retained; camel-case transition detection is deliberately ASCII-only. No Unicode normalization beyond casefolding, stemming, stop-word removal, syntax filtering, metadata prepending, or symbol boosts are applied. Source comments, strings, keywords, and numerals participate. Only `chunk.content.strip()` is indexed. The full identifier contributes its own term; matching components does not enforce exact-match priority.

Queries use sorted unique expanded terms. Repeating a query word does not add weight. Sorting fixes floating-point accumulation order independently of query word order or hash randomization.

## Scoring contract

For each unique query term `t` occurring in document `d`:

```text
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
contribution(t,d) = idf(t) * tf(t,d) * (1.2 + 1)
                    / (tf(t,d) + 1.2 * (1 - 0.75 + 0.75 * length(d)/average_length))
score(d) = sum of contributions in sorted query-term order
```

`N` is the accepted snapshot document count; `df` counts documents containing the term; `tf` counts occurrences in the expanded lexical representation. Document length includes full tokens and added components. No query-frequency multiplier is used. This is `bm25-positive-idf-v1`, computed with Python floating-point arithmetic. The parameter and positive-IDF choices are grounded in the [Lucene BM25 reference](https://lucene.apache.org/core/9_12_1/core/org/apache/lucene/search/similarities/BM25Similarity.html), while the declared tokenizer and length policy are project-specific.

Only matching documents receive a score; all contributions are positive. Do not pad results with zero-score documents. If all documents have zero lexical tokens, postings are empty and every query returns an empty tuple without division by zero. Reject a snapshot with no accepted documents entirely.

Sort matches by descending score, then ascending chunk ID, before taking `k` (default 50). Ranks are one-based. `k` must be a positive integer; oversized `k` returns all positive matches. Blank/unknown/punctuation-only queries return `()`. Non-string queries and invalid `k` fail.

## Shared result model and FAISS compatibility

Both channels use `src/models/retrieval_result.py::SearchResult` (`RetrievalResult` is an alias). The original fields `chunk_id`, `rank`, `score`, `metadata`, and `strategy` remain unchanged. Read-only convenience properties expose `repository_id`, `commit_sha`, `file_path`, `entity_type`, `qualified_name`, `start_line`, `end_line`, and inclusive `line_range` directly. Existing imports from `src.retrieval` and `src.retrieval.vector_index` remain supported.

Metadata preserves the content SHA-256 and original embedding tokenizer count. `metadata.token_count` is **not** the BM25 document length. The standard dataclass serialization retains the existing nested metadata shape; convenience properties do not duplicate serialized data.

Both channels operate on the same accepted per-snapshot IDs and return the same provenance. The common embedding contract/clearance/metadata checks now live in `embedding_artifacts.py`; FAISS behavior is unchanged. Lexical scores and cosine scores are not directly comparable. Future RRF can combine their one-based ranks; no rank fusion or text-query embedding for FAISS is implemented here.

## Persistence and reproducibility

`save` creates a new external directory containing:

- `documents.json`: deterministic rows with chunk IDs, provenance, and ordered lexical tokens.
- `manifest.json`: schema `1.0`, scoring/tokenizer versions, parameters, query-term and tie policies, count, snapshot, Python/Unicode versions, embedding-run manifest/hash, and documents checksum. Written last.

`load` checks configuration/runtime compatibility, current clearance, checksum, row count/order, chunk identities/provenance, and token structure. It rebuilds postings and statistics from the stored tokens. Identical inputs and runtime produce identical saved bytes and repeated rankings. Python and Unicode versions are recorded and checked; cross-platform floating-point identity is not promised.

Tokens are sensitive source-derived content. Store them outside Git and outside source checkouts under the controlled research-data area. No pickle or source/query logging is used. Checksums detect accidental corruption, not malicious replacement of both files. Load only trusted local artifacts. Partial writes lack a valid manifest; existing directories are never overwritten. Discard loaded indexes if privacy clearance is revoked.

## Usage

Use the existing pinned `requirements-retrieval.txt` environment; this phase adds no dependencies.

```python
from pathlib import Path
from src.retrieval import BM25Index, BM25Search

index = BM25Index.build(
    chunks,
    Path(r"C:\Apps\Temp\Phase6.2\runs\approved-run-001"),
    Path(r"C:\Apps\Temp\Phase6.2\privacy-clearance.json"),
    repository_id=repository_id,
    commit_sha=commit_sha,
)
results = BM25Search(index).search("load_user_profile", k=10)
index.save(Path(r"C:\Apps\Temp\Phase6.3\lexical\snapshot-001"))
```

The example requires a genuinely approved embedding run; none is claimed for the frozen corpus. The benchmark comparison must keep the accepted inventory identical across BM25 and FAISS and report embedding exclusions.

## Validation and readiness

On 2026-09-27, `python -m unittest discover -s tests -v` passed **68/68 tests with no skips**, including **19 BM25 tests**, the existing FAISS tests, and real offline embedding inference. Runtime: Windows Server 2022, Python 3.14.7, with the existing pinned retrieval environment and `EMBEDDING_MODEL_CACHE` set. The suite completed in 8.885 seconds (informational). `pip check` reported no broken requirements; this phase adds no packages.

Tests use generated code fixtures and synthetic embedding artifacts, with temporary test-only clearance attestations. Coverage includes identifier/keyword matches, hand-computed scores, length normalization, repeated-query policy, deterministic ties, accepted-inventory equality with FAISS, provenance, malformed inputs, privacy gates, persistence, Unicode casefolding, zero-token documents, and socket-blocked local execution. These tests establish implementation behavior, not retrieval relevance.

RRF implementation can now consume the two channels' shared results under ADR-017. Natural-language query encoding for the dense branch and corpus privacy clearance remain separate prerequisites for a full text-query corpus experiment.
