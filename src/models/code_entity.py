"""Structured, source-located entities extracted from a Python module."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ImportEntity:
    """One imported name, including its alias and relative-import depth."""

    import_kind: Literal["import", "from"]
    module: str | None
    name: str
    alias: str | None
    level: int
    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class FunctionEntity:
    """A function, async function, or class method with lexical provenance."""

    name: str
    qualified_name: str
    kind: Literal["function", "method"]
    parent_class: str | None
    is_async: bool
    decorators: tuple[str, ...]
    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class ClassEntity:
    """A Python class definition and its source-level bases/decorators."""

    name: str
    qualified_name: str
    parent_class: str | None
    bases: tuple[str, ...]
    decorators: tuple[str, ...]
    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class Module:
    """The complete deterministic extraction result for one Python source file."""

    name: str
    relative_path: str
    start_line: int
    end_line: int
    classes: tuple[ClassEntity, ...]
    functions: tuple[FunctionEntity, ...]
    imports: tuple[ImportEntity, ...]