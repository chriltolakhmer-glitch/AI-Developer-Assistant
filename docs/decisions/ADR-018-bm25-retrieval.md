# ADR-018: BM25 Lexical Retrieval as the Second Retrieval Channel

## Status

Accepted for Phase 6.3.2 on 2026-09-27. Corpus execution remains conditional on the existing privacy clearance gate. No RRF, LLM, UI, or agents are implemented.

## Context

Dense semantic similarity can miss exact identifiers, API names, and uncommon code terms. A lexical channel makes those literal signals available independently and supplies the BM25-only baseline required by the thesis. Neither lexical nor semantic similarity is assumed to establish relevance without evaluation.

ADR-017 requires both channels to use the same accepted chunk inventory. Phase 6.2 rejects empty and oversized embedding inputs; indexing those only in BM25 would confound retrieval comparisons with corpus coverage differences.

## Decision

Add BM25 lexical retrieval as the second retrieval channel alongside local FAISS. Build one index per repository/commit from verified `CodeChunk` contents, selecting exactly the accepted IDs in the approved embedding artifacts. Require every accepted chunk to be supplied; ignore validated additional chunks excluded from that inventory. Reuse the existing clearance and artifact validation without running an embedding model or constructing a FAISS index.

Implement an explicit, standard-library BM25 scorer with `k1=1.2`, `b=0.75`, and positive IDF `ln(1 + (N - df + 0.5)/(df + 0.5))`. The parameter and IDF conventions follow the [Lucene BM25Similarity reference](https://lucene.apache.org/core/9_12_1/core/org/apache/lucene/search/similarities/BM25Similarity.html); this implementation is not a Lucene backend or a claim of identical Lucene scores. Record the complete formula in the design. Do not introduce another scoring dependency or tune parameters on held-out queries.

Freeze tokenizer `identifier-components-v1`: Unicode word extraction, whole-token casefolding, and additional unique snake_case, ASCII camelCase/acronym, and ASCII letter/digit components per occurrence. Preserve whole identifiers, numbers, keywords, comments, and string content. Use no stop-word list, stemming, or metadata-field boosts. The expanded token count defines document length. Use the same tokenizer for source and queries; score each distinct query term once, in sorted order.

Return only positive lexical matches, sorted by descending score then ascending chunk ID, with one-based ranks and default top-k 50. Blank, punctuation-only, and unknown-term queries return no results. Use the shared immutable `SearchResult` model with `strategy="bm25"`; preserve the existing dense result interface and all chunk provenance.

Persist tokenized documents and metadata locally, outside Git, together with a versioned configuration, embedding-run lineage, and integrity manifest. Lexical tokens are source-derived confidential data, even without the original source text. Rebuild when tokenizer, scoring policy, accepted inventory, or recorded Python/Unicode runtime changes.

## Relationship with FAISS and future RRF

FAISS ranks compatible query vectors by cosine similarity. BM25 accepts text and ranks literal term evidence; its numeric score scale is different. Both now return the same result type and accepted chunk IDs, enabling later RRF integration. Future RRF must consume component ranks under ADR-017's fixed parameters, not add raw BM25 and cosine scores. No fusion code is added in this phase, and text-to-vector query encoding remains a separate integration requirement.

## Consequences

- Exact identifier tokens remain searchable alongside their components, but BM25 does not guarantee exact-match precedence over all other evidence.
- Casefolding loses case distinctions; component expansion affects term frequency and length normalization. These are declared baseline choices, not optimality claims.
- IDF and document lengths are computed over the accepted per-snapshot corpus, including any accepted document with zero lexical terms. Such documents never match.
- Corpus privacy findings remain unresolved; synthetic tests do not authorize corpus processing or establish retrieval quality.

## References

- [ADR-017: hybrid retrieval](ADR-017-hybrid-retrieval.md)
- [ADR-014: privacy policy](ADR-014-embedding-privacy-policy.md)
- [BM25 design and validation](../architecture/bm25-retrieval-design.md)
