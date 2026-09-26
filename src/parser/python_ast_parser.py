"""Deterministic Python AST extraction for modules and code entities."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
import tokenize

from src.models.code_entity import ClassEntity, FunctionEntity, ImportEntity, Module


class ParserError(ValueError):
    """A syntax error with stable source-location metadata and no source text."""

    def __init__(
        self,
        relative_path: str,
        line: int | None,
        column: int | None,
        message: str,
    ) -> None:
        self.relative_path = relative_path
        self.line = line
        self.column = column
        self.message = message
        location = f"{relative_path}:{line or 0}:{column or 0}"
        super().__init__(f"{location}: {message}")


@dataclass(frozen=True, slots=True)
class _Scope:
    name: str
    qualified_name: str
    kind: str


class _DefinitionVisitor(ast.NodeVisitor):
    def __init__(self, source: str) -> None:
        self.source = source
        self.scopes: list[_Scope] = []
        self.classes: list[ClassEntity] = []
        self.functions: list[FunctionEntity] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualified_name = self._qualified_name(node.name)
        self.classes.append(
            ClassEntity(
                name=node.name,
                qualified_name=qualified_name,
                parent_class=self._parent_class(),
                bases=tuple(self._source_expression(base) for base in node.bases),
                decorators=self._decorators(node),
                start_line=self._start_line(node),
                end_line=self._end_line(node),
            )
        )
        self.scopes.append(_Scope(node.name, qualified_name, "class"))
        for statement in node.body:
            self.visit(statement)
        self.scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node, is_async=True)

    def _visit_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        is_async: bool,
    ) -> None:
        qualified_name = self._qualified_name(node.name)
        kind = "method" if self.scopes and self.scopes[-1].kind == "class" else "function"
        self.functions.append(
            FunctionEntity(
                name=node.name,
                qualified_name=qualified_name,
                kind=kind,
                parent_class=self._parent_class(),
                is_async=is_async,
                decorators=self._decorators(node),
                start_line=self._start_line(node),
                end_line=self._end_line(node),
            )
        )
        self.scopes.append(_Scope(node.name, qualified_name, "function"))
        for statement in node.body:
            self.visit(statement)
        self.scopes.pop()

    def _qualified_name(self, name: str) -> str:
        return ".".join([scope.name for scope in self.scopes] + [name])

    def _parent_class(self) -> str | None:
        for scope in reversed(self.scopes):
            if scope.kind == "class":
                return scope.qualified_name
        return None

    def _decorators(self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...]:
        return tuple(self._source_expression(decorator) for decorator in node.decorator_list)

    def _source_expression(self, node: ast.expr) -> str:
        segment = ast.get_source_segment(self.source, node)
        return segment if segment is not None else ast.unparse(node)

    @staticmethod
    def _start_line(node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        definition_line = node.lineno
        decorator_lines = [decorator.lineno for decorator in node.decorator_list]
        return min([definition_line, *decorator_lines])

    @staticmethod
    def _end_line(node: ast.AST) -> int:
        return getattr(node, "end_lineno", None) or getattr(node, "lineno", 1)


class _ImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[ImportEntity] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                ImportEntity(
                    import_kind="import",
                    module=None,
                    name=alias.name,
                    alias=alias.asname,
                    level=0,
                    start_line=node.lineno,
                    end_line=self._end_line(node),
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.imports.append(
                ImportEntity(
                    import_kind="from",
                    module=node.module,
                    name=alias.name,
                    alias=alias.asname,
                    level=node.level,
                    start_line=node.lineno,
                    end_line=self._end_line(node),
                )
            )
        self.generic_visit(node)

    @staticmethod
    def _end_line(node: ast.AST) -> int:
        return getattr(node, "end_lineno", None) or getattr(node, "lineno", 1)


class PythonAstParser:
    """Parse Python files without changing them or invoking external services."""

    def parse(self, source: str, relative_path: str = "<memory>") -> Module:
        """Parse source text into sorted, source-located module entities."""
        normalized_path = self._normalize_relative_path(relative_path)
        try:
            tree = ast.parse(source, filename=normalized_path, type_comments=True)
        except SyntaxError as error:
            raise ParserError(
                relative_path=normalized_path,
                line=error.lineno,
                column=error.offset,
                message=error.msg,
            ) from error

        definitions = _DefinitionVisitor(source)
        definitions.visit(tree)
        imports = _ImportVisitor()
        imports.visit(tree)

        classes = tuple(
            sorted(
                definitions.classes,
                key=lambda entity: (entity.start_line, entity.end_line, entity.qualified_name),
            )
        )
        functions = tuple(
            sorted(
                definitions.functions,
                key=lambda entity: (entity.start_line, entity.end_line, entity.qualified_name),
            )
        )
        module_name = self._module_name(normalized_path)
        return Module(
            name=module_name,
            relative_path=normalized_path,
            start_line=1,
            end_line=len(source.splitlines()),
            classes=classes,
            functions=functions,
            imports=tuple(imports.imports),
        )

    def parse_file(
        self,
        file_path: str | Path,
        relative_path: str | None = None,
    ) -> Module:
        """Read and parse one file, honoring its declared Python source encoding."""
        path = Path(file_path)
        module_path = relative_path if relative_path is not None else path.name
        with tokenize.open(path) as source_file:
            source = source_file.read()
        return self.parse(source, module_path)

    @staticmethod
    def _normalize_relative_path(path: str) -> str:
        normalized = path.replace("\\", "/")
        pure_path = PurePosixPath(normalized)
        windows_path = PureWindowsPath(path)
        if (
            not normalized
            or normalized.endswith("/")
            or not pure_path.parts
            or pure_path.is_absolute()
            or windows_path.is_absolute()
            or windows_path.drive
            or ".." in pure_path.parts
        ):
            raise ValueError("relative_path must be a non-empty repository-relative path")
        return pure_path.as_posix()

    @staticmethod
    def _module_name(relative_path: str) -> str:
        path = PurePosixPath(relative_path)
        parts = list(path.parts)
        if path.name == "__init__.py" and len(parts) > 1:
            return ".".join(parts[:-1])
        parts[-1] = path.stem
        return ".".join(parts)