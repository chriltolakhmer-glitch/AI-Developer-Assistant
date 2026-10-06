"""Deterministic path-qualified Python symbol attribution for exact source patches."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.parser.python_ast_parser import ParserError, PythonAstParser
from .local_workflow import LocalWorkflowError

# Not a legal Python identifier, so it cannot collide with a parsed symbol.
MODULE_SYMBOL = "<module>"


def patch_sections(patch: str) -> dict[str, str]:
    """Split sections by parsed hunk counts so dash-prefixed source is never a header."""
    import re
    lines = patch.splitlines()
    result = {}
    i = 0
    while i < len(lines):
        if not (lines[i].startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ ")):
            i += 1
            continue
        start = i
        path = lines[i][4:].removeprefix("a/").split("\t", 1)[0]
        i += 2
        saw_hunk = False
        while i < len(lines) and lines[i].startswith("@@ "):
            match = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)", lines[i])
            if not match:
                raise LocalWorkflowError("Cannot split malformed patch hunk; replan before approval.")
            old_count, new_count = int(match.group(2) or 1), int(match.group(4) or 1)
            old_seen = new_seen = 0
            i += 1
            while (old_seen < old_count or new_seen < new_count) and i < len(lines):
                row = lines[i]
                if row.startswith("\\ No newline"):
                    i += 1
                    continue
                if not row or row[0] not in " +-":
                    raise LocalWorkflowError("Cannot split malformed patch hunk lines; replan before approval.")
                old_seen += row[0] in " -"
                new_seen += row[0] in " +"
                i += 1
            if (old_seen, new_seen) != (old_count, new_count):
                raise LocalWorkflowError("Cannot split incomplete patch hunk; replan before approval.")
            while i < len(lines) and lines[i].startswith("\\ No newline"):
                i += 1
            saw_hunk = True
        if not saw_hunk or path in result:
            raise LocalWorkflowError("Cannot split patch with missing hunk or duplicate path.")
        result[path] = "\n".join(lines[start:i]) + "\n"
    return result


def canonical_scope(rows: Any) -> tuple[tuple[str, str], ...]:
    """Canonical immutable path/symbol pairs."""
    entries = set()
    for row in rows:
        path, symbol = row.get("file_path"), row.get("symbol", row.get("qualified_symbol"))
        if isinstance(path, str) and isinstance(symbol, str) and symbol:
            entries.add((path.replace("\\", "/"), symbol))
    return tuple(sorted(entries))


def proposal_allowed_scope(proposal: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return canonical_scope(proposal.get("evidence_refs", ()))


def derive_patch_symbols(patch: str, preimages: dict[str, str], postimages: dict[str, str]) -> tuple[tuple[str, str], ...]:
    """Map changed old/new hunk lines to the smallest enclosing parsed symbol on each side."""
    lines = patch.splitlines()
    changed_lines: set[tuple[str, str, int]] = set()
    i = 0
    parser = PythonAstParser()
    while i < len(lines):
        if not lines[i].startswith("--- "):
            i += 1
            continue
        path = lines[i][4:].removeprefix("a/").split("\t", 1)[0]
        i += 2
        while i < len(lines) and lines[i].startswith("@@ "):
            import re
            m = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)", lines[i])
            if not m:
                raise LocalWorkflowError("Cannot attribute malformed patch hunk to symbols; replan before approval.")
            old_line, new_line = int(m.group(1)), int(m.group(3))
            old_count, new_count = int(m.group(2) or 1), int(m.group(4) or 1)
            seen_old = seen_new = 0
            i += 1
            while (seen_old < old_count or seen_new < new_count) and i < len(lines):
                line = lines[i]
                if line.startswith("\\ No newline"):
                    i += 1
                    continue
                if not line or line[0] not in " +-":
                    raise LocalWorkflowError("Cannot attribute malformed patch hunk line; replan before approval.")
                if line[0] in " -":
                    if line[0] == "-":
                        changed_lines.add((path, "old", old_line))
                    old_line += 1; seen_old += 1
                if line[0] in " +":
                    if line[0] == "+":
                        changed_lines.add((path, "new", new_line))
                    new_line += 1; seen_new += 1
                i += 1
            if (seen_old, seen_new) != (old_count, new_count):
                raise LocalWorkflowError("Cannot attribute incomplete patch hunk; replan before approval.")
            while i < len(lines) and lines[i].startswith("\\ No newline"):
                i += 1
    symbols: set[tuple[str, str]] = set()
    for path, side, number in changed_lines:
        source = preimages.get(path) if side == "old" else postimages.get(path)
        if source is None:
            raise LocalWorkflowError(f"Cannot attribute {side}-image for {path}; replan before approval.")
        try:
            module = parser.parse(source, path)
        except (ParserError, SyntaxError, ValueError) as error:
            raise LocalWorkflowError(f"Cannot deterministically parse {side}-image {path}; replan before approval.") from error
        source_lines = source.splitlines()
        if 1 <= number <= len(source_lines) and not source_lines[number - 1].strip():
            # Whitespace-only separator edits have no source symbol semantics.
            continue
        entities = [entity for entity in (*module.classes, *module.functions)
                    if entity.start_line <= number <= entity.end_line]
        if entities:
            # Shortest source span is the innermost lexical entity; parser names retain hierarchy.
            selected = min(entities, key=lambda entity: (entity.end_line - entity.start_line,
                                                          -entity.start_line, entity.qualified_name))
            touched_symbol = selected.qualified_name
        else:
            touched_symbol = MODULE_SYMBOL
        symbols.add((path, touched_symbol))
    return tuple(sorted(symbols))


def scope_is_allowed(actual: tuple[tuple[str, str], ...], allowed: tuple[tuple[str, str], ...],
                     preimages: dict[str, str]) -> bool:
    """Exact authorization or parser-proven class ancestry; never use textual prefixes."""
    allowed_pairs = set(allowed)
    for path, symbol in actual:
        if (path, symbol) in allowed_pairs:
            continue
        if symbol == MODULE_SYMBOL or not preimages.get(path):
            return False
        try:
            module = PythonAstParser().parse(preimages[path], path)
        except (ParserError, SyntaxError, ValueError):
            return False
        classes = {entity.qualified_name for entity in module.classes}
        named = {entity.qualified_name for entity in (*module.classes, *module.functions)}
        if symbol not in named:
            return False
        if not any(p == path and parent in classes and symbol.startswith(parent + ".")
                   for p, parent in allowed_pairs):
            return False
    return bool(actual)


def postimages_for_patch(root: Path, patch: str, paths: tuple[str, ...], apply_text) -> tuple[dict[str, str], dict[str, str]]:
    old = {relative: (root / relative).read_bytes().decode("utf-8") for relative in paths}
    new = postimages_from_preimages(patch, paths, old, apply_text)
    return old, new


def postimages_from_preimages(patch: str, paths: tuple[str, ...], preimages: dict[str, str], apply_text) -> dict[str, str]:
    by_path = patch_sections(patch)
    new = {}
    for relative in paths:
        try:
            original = preimages[relative].encode("utf-8")
            updated = apply_text(original, by_path[relative])
            new[relative] = updated.decode("utf-8")
        except (OSError, KeyError, UnicodeError) as error:
            raise LocalWorkflowError(f"Cannot compute exact symbol post-image for {relative}; PATCH NOT APPLIED.") from error
    return new
