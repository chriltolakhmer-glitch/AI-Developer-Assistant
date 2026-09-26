# Phase 5.1 — Deterministic Repository Scanner

**Status:** Initial implementation design, implemented with the Phase 5.1 scanner. This component produces a corpus inventory only; it does not parse ASTs, build indexes, answer questions, or invoke a model.

## Component responsibility

The scanner loads an already-present local Git working-tree root and verifies that its `HEAD` equals the caller-supplied, full 40-character corpus SHA. It reads the committed tree and blob objects from Git's local object database, discovers tracked `.py` files, applies the Phase 4.5 filters, calculates byte sizes, SHA-256 hashes, and eligible LOC, then returns a corpus manifest.

The scanner is deliberately offline and read-only with respect to the source checkout. It does not clone, fetch, switch commits, modify source files, or make API/service calls. A requested JSON manifest can only be written outside the scanned checkout. Running the scanner does not clear a repository's outstanding secret/privacy-audit gate.

## Input and output

### Input

- Local path to the repository's Git working-tree root.
- Required expected full commit SHA.
- Optional stable repository ID and repository URL. Neither is resolved over the network.

### Output

- `RepositoryMetadata`: repository ID, verified commit SHA, and optional supplied URL.
- One `FileMetadata` record for each tracked `.py` path, with normalized relative path, language, inclusion state, and exclusion reason when excluded. Eligible records additionally contain SHA-256, exact blob byte size, and eligible LOC.
- `CorpusManifest`: schema/filter versions, sorted records, eligible Python file count, and eligible Python LOC. Its JSON contains no checkout absolute path, source text, timestamps, or nondeterministic values.

Use `RepositoryScanner.scan(...)` to create a manifest in memory. `scan_to_file(...)` writes its deterministic JSON to a caller-selected path outside the source repository.

## Data flow

```text
Local repository root + required expected SHA
  -> verify Git root and HEAD (no fetch/checkout)
  -> enumerate committed tree with git ls-tree
  -> select tracked .py files and assign exclusions
  -> read eligible blobs in one local git cat-file batch
  -> compute SHA-256, byte size, and nonblank/noncomment LOC
  -> sort file records by repository-relative path
  -> CorpusManifest -> stable JSON (optional; outside checkout only)
```

## Filtering and LOC rule

The implementation follows the Phase 4.5 screening policy: only Git-tracked `.py` paths are considered; path components exactly named `.git`, `.venv`, `venv`, `__pycache__`, `site-packages`, `build`, `dist`, `vendor`, `vendors`, `third_party`, `generated`, `fixtures`, and `testdata` are excluded; generated `*_pb2.py` files are excluded. Directory-name comparisons are case-sensitive to match the recorded path rule. Ordinary Python test files remain eligible. Symbolic links and non-regular tree entries are recorded as excluded rather than followed.

Eligible LOC counts each physical line whose trimmed bytes are non-empty and do not begin with `#`. Blank and comment-only lines are excluded; inline comments do not affect the count. Hash and size are computed over canonical committed blob bytes, not platform-converted working-tree bytes.

Every tracked `.py` candidate appears in the manifest. Excluded entries include their reason; content-derived fields are intentionally absent for excluded entries. Non-Python paths are outside this scanner's manifest scope.

## Design decisions and limits

- **Commit objects, not working-tree bytes:** requiring exact `HEAD` establishes snapshot identity; reading canonical Git blobs stabilizes hashes and LOC across checkout line-ending settings.
- **Local Git only:** network acquisition is a separate, controlled setup operation; this scanner never fetches or clones.
- **Deterministic serialization:** stable versions, paths, order, SHA-256, byte counts, and LOC are emitted; no timestamp or machine-specific root path is embedded.
- **Manifest output outside checkout:** avoids accidental source-repository mutation and follows the privacy policy for per-file audit artifacts.
- **No scope expansion:** no source text, AST parse results, secret scanning, indexing, embeddings, UI, chatbot, or LLM integration. Secret/privacy clearance remains a prerequisite before indexing.

See [ADR-009](../decisions/ADR-009-scanner-design.md) for the governing decision.