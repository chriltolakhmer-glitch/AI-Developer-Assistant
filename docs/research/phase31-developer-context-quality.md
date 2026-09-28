# Phase 31 - Developer Mode Context Quality

**Status:** Implemented as developer-only post-release work on 2026-09-28.
Research workflows, benchmark data, Humanize artifacts, evaluation methodology,
and the v0.1.1 release baseline are unchanged.

## Motivation

Phase 30 made local retrieval inspectable and repeatable, but its results still
had weak context boundaries. Oversized definitions remain excluded by the fixed
embedding contract, a result did not explain its source structure, and related
symbols were not visible without opening several files manually. Phase 31 adds
context metadata and explanations without increasing chunk size or changing
shared research retrieval behavior.

## Implemented improvements

The developer index now stores a separate `state.json` context sidecar. Shared
`CodeChunk`, embedding, BM25, vector, and research schemas are unchanged. Each
developer chunk records:

- repository-relative file path, Python module name, symbol name and parent symbol
- exact source region and a short extraction reason
- imports and uppercase configuration keys visible in the module
- nearby chunk IDs and same-file related symbol IDs

The existing Python AST parser supplies classes, functions, methods and imports.
The sidecar also identifies simple call-name relationships and configuration
assignments. It does not infer dynamic dispatch, runtime routes, aliases beyond
the parser's import records, or a complete call graph.

Query results now retain source provenance and include lexical/vector RRF
contributions, metadata and symbol relevance, context expansion reasons, related
and nearby context IDs, grouped files and symbols, and an explicit note when
overlapping ranges or duplicate file ranges are omitted. Use:

```text
prototype local explain "Where is the session token loaded?" --repository PATH
prototype local explain "Where is the session token loaded?" --repository PATH --json
```

`local query` remains the compact navigation form. Neither command generates an
answer or records a research run.

## Example shape

```text
File: src/auth/service.py
Symbol: AuthService.login
Related context: configuration loading, token validation, middleware usage
Reasons: lexical/vector contribution, symbol match, nearby source expansion
```

The actual CLI emits stable file paths, symbol names, line ranges, chunk IDs and
machine-readable reason fields rather than unsupported confidence scores.

## Tests and isolation

Developer fixtures cover function, class, configuration, API-route, import and
dependency-style lookups. They verify symbol metadata, related context,
explanations, duplicate/overlap reduction, `local explain`, incremental index
reuse and developer workspace separation. These are regression fixtures, not
benchmark questions or quality measurements.

Run focused and full validation with:

```text
python -m unittest tests.test_developer_mode -v
python -m unittest discover -s tests -v
```

## Limitations and future work

Only Python is supported. Large definitions can still be reported as over-limit
and excluded; this phase does not silently truncate or blindly enlarge chunks.
Static call relationships are intentionally conservative. Route-to-handler
resolution, configuration usage tracing and cross-module dependency tracing are
partial and should not be read as complete program analysis. Query startup still
loads the local model per process. Future developer work could add bounded
language-specific extractors, tokenizer-only context inspection, stronger
cross-file symbol resolution and an interactive context viewer.

No benchmark improvement, research evaluation result, Humanize change, or
research snapshot expansion is claimed.