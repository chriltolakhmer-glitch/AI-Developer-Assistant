# Phase 5.2 — Python AST Parser Design

**Status:** Implemented as the first structural extraction stage. The parser is a local, read-only component and does not perform indexing, retrieval, or answer generation.

## Component responsibility

`PythonAstParser` converts one Python source file into immutable structured metadata. It uses only the Python standard-library `ast` module and returns module identity, classes, functions/methods, imports, decorators, and inclusive source line ranges. Syntax errors are surfaced as `ParserError` with file and location metadata; malformed files are not silently omitted.

The parser does not alter source files, make network/API calls, resolve symbols dynamically, execute code, or extract source text as entity payload. It records source expressions for class bases and decorators to support later AST-aware retrieval research.

## Input and output

### Input

- `parse(source, relative_path)`: source text and a repository-relative Python path.
- `parse_file(file_path, relative_path)`: a local file path and optional stable repository-relative path. The file is opened read-only with Python's encoding-cookie-aware `tokenize.open`.

The relative path is normalized to POSIX separators and rejected if absolute or if it traverses above the repository root. The module name is derived from that path (`package/__init__.py` maps to `package`).

### Output

- `Module`: module name/path, file line range, and sorted tuples of classes and functions plus source-order imports.
- `ClassEntity`: name, qualified name, parent class when nested, base expressions, decorators, and inclusive line range.
- `FunctionEntity`: name, qualified name, kind (`function` or `method`), parent class when applicable, async flag, decorators, and inclusive line range.
- `ImportEntity`: one imported name per alias with import kind, module, alias, relative-import level, and statement line range.

All line numbers are one-based and inclusive. A class/function's range starts at the earliest decorator line when decorated and ends at the AST node's `end_lineno`. Nested definitions are returned as flat, source-sorted entities with qualified names. A function directly declared in a class body is a method; a nested local function remains a function. Imports anywhere in the module—including inside function or class bodies—are retained in source traversal order.

## AST processing flow

```text
Python source + repository-relative path
  -> validate and normalize path
  -> ast.parse(..., type_comments=True)
  -> definition visitor: classes, functions, methods, decorators, bases, spans
  -> import visitor: each alias, relative level, statement span
  -> deterministic ordering and module-name derivation
  -> immutable Module result
       or ParserError(relative path, line, column, syntax message)
```

## Reproducibility and limits

- Extraction uses the selected standard-library parser and is deterministic for the same source, relative path, and Python interpreter version.
- Entity collections use stable source-location/qualified-name ordering; imports follow AST source order and preserve alias order within a statement.
- Decorator/base expressions use their source segment, preserving meaningful spelling and formatting without retaining the full source file.
- Python AST is not a concrete syntax tree: comments and whitespace are not represented, and dynamic imports, runtime behavior, and semantic name resolution are out of scope.
- Parser behavior can vary across Python grammar versions; the interpreter version must be recorded with later corpus runs. Syntax failures remain explicit for a future fallback/chunking decision.

See [ADR-010](../decisions/ADR-010-ast-parser.md) for the governing decision and [scanner-design.md](scanner-design.md) for the preceding pinned-repository stage.