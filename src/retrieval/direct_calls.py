"""Conservative direct-call resolution within an explicitly supplied source inventory."""

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePosixPath
import symtable

from src.models.chunk import CodeChunk


@dataclass(frozen=True, slots=True, order=True)
class DirectCall:
    caller_id: str
    callee_id: str
    file_path: str
    line: int
    call_name: str


class _Calls(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append(node)
        self.generic_visit(node)

    # Bodies/defaults of nested definitions are a different scope.
    def visit_FunctionDef(self, node):
        pass

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef


def direct_calls(parents: tuple[CodeChunk, ...], sources: dict[str, str]) -> tuple[DirectCall, ...]:
    symbols = {(p.file_path, p.qualified_name): p.chunk_id for p in parents
               if p.entity_type == "function"}
    edges = set()
    for file, source in sorted(sources.items()):
        tree = ast.parse(source, filename=file)
        scope = symtable.symtable(source, file, "exec")
        bindings = defaultdict(list)
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    directory = PurePosixPath(file).parent
                    for _ in range(node.level - 1):
                        directory = directory.parent
                    target = str(directory / ((node.module or "").replace(".", "/") + ".py"))
                else:
                    target = "src/" + (node.module or "").replace(".", "/") + ".py"
                for alias in node.names:
                    bindings[alias.asname or alias.name].append((target, alias.name))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                bindings[node.name].append((file, node.name))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    bindings[alias.asname or alias.name.split(".")[0]].append(None)
            else:
                # Reject module-level rebinding/conditional definitions conservatively.
                for item in ast.walk(node):
                    if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store):
                        bindings[item.id].append(None)
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            caller = symbols.get((file, node.name))
            local = next((s for s in scope.get_children()
                          if s.get_name() == node.name and s.get_lineno() == node.lineno), None)
            if caller is None or local is None:
                continue
            visitor = _Calls()
            for statement in node.body:
                visitor.visit(statement)
            for call in visitor.calls:
                name = call.func.id
                try:
                    symbol = local.lookup(name)
                except KeyError:
                    continue
                choices = bindings.get(name, ())
                if not symbol.is_global() or symbol.is_assigned() or len(choices) != 1 or choices[0] is None:
                    continue
                callee = symbols.get(choices[0])
                if callee and callee != caller:
                    edges.add(DirectCall(caller, callee, file, call.lineno, name))
    return tuple(sorted(edges))
