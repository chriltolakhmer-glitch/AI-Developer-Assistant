"""Focused tests for deterministic Python AST entity extraction."""

from pathlib import Path
import tempfile
import unittest

from src.parser import ParserError, PythonAstParser


SOURCE = """\
import os as operating_system
from .helpers import run as execute, trace

def standalone():
    import json
    return json

@register("service")
class Service(BaseService):
    @property
    def name(self):
        return "service"

    @classmethod
    async def create(cls):
        return cls()

    def outer(self):
        def nested():
            return True
        return nested

    class Inner:
        def run(self):
            return None
"""


class PythonAstParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = PythonAstParser()

    def test_extracts_classes_with_decorators_bases_and_line_ranges(self) -> None:
        module = self.parser.parse(SOURCE, "pkg/service.py")

        self.assertEqual("pkg.service", module.name)
        self.assertEqual(2, len(module.classes))
        service = next(entity for entity in module.classes if entity.name == "Service")
        self.assertEqual("Service", service.name)
        self.assertEqual("Service", service.qualified_name)
        self.assertEqual(("BaseService",), service.bases)
        self.assertEqual(('register("service")',), service.decorators)
        self.assertEqual((8, 25), (service.start_line, service.end_line))
        inner = next(entity for entity in module.classes if entity.name == "Inner")
        self.assertEqual("Service.Inner", inner.qualified_name)
        self.assertEqual("Service", inner.parent_class)

    def test_extracts_top_level_functions_methods_and_nested_functions(self) -> None:
        module = self.parser.parse(SOURCE, "pkg/service.py")

        functions = {entity.qualified_name: entity for entity in module.functions}
        self.assertEqual("function", functions["standalone"].kind)
        self.assertIsNone(functions["standalone"].parent_class)
        self.assertEqual("method", functions["Service.name"].kind)
        self.assertEqual("Service", functions["Service.name"].parent_class)
        self.assertEqual(('property',), functions["Service.name"].decorators)
        self.assertEqual("method", functions["Service.create"].kind)
        self.assertTrue(functions["Service.create"].is_async)
        self.assertEqual("function", functions["Service.outer.nested"].kind)
        self.assertEqual("Service", functions["Service.outer.nested"].parent_class)
        self.assertEqual("method", functions["Service.Inner.run"].kind)

    def test_extracts_absolute_relative_and_nested_imports(self) -> None:
        module = self.parser.parse(SOURCE, "pkg/service.py")

        imports = [
            (entity.import_kind, entity.module, entity.name, entity.alias, entity.level)
            for entity in module.imports
        ]
        self.assertEqual(
            [
                ("import", None, "os", "operating_system", 0),
                ("from", "helpers", "run", "execute", 1),
                ("from", "helpers", "trace", None, 1),
                ("import", None, "json", None, 0),
            ],
            imports,
        )
        self.assertEqual((1, 1), (module.imports[0].start_line, module.imports[0].end_line))

    def test_parse_output_is_deterministic(self) -> None:
        first = self.parser.parse(SOURCE, "pkg/service.py")
        second = self.parser.parse(SOURCE, "pkg/service.py")

        self.assertEqual(first, second)
        self.assertEqual(
            sorted(module_path.qualified_name for module_path in first.classes),
            [entity.qualified_name for entity in first.classes],
        )
        self.assertEqual(
            sorted(
                first.functions,
                key=lambda entity: (entity.start_line, entity.end_line, entity.qualified_name),
            ),
            list(first.functions),
        )

    def test_parse_file_is_read_only_and_accepts_repository_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "service.py"
            source_path.write_text(SOURCE, encoding="utf-8")
            original_bytes = source_path.read_bytes()

            module = self.parser.parse_file(source_path, "pkg/service.py")

            self.assertEqual("pkg/service.py", module.relative_path)
            self.assertEqual(original_bytes, source_path.read_bytes())

    def test_syntax_errors_are_reported_without_source_text(self) -> None:
        with self.assertRaises(ParserError) as raised:
            self.parser.parse("def broken(:\n    pass\n", "pkg/broken.py")

        self.assertEqual("pkg/broken.py", raised.exception.relative_path)
        self.assertEqual(1, raised.exception.line)
        self.assertNotIn("def broken", str(raised.exception))

    def test_rejects_paths_that_are_not_safe_repository_relative_paths(self) -> None:
        for path in ("", ".", "../outside.py", "/absolute.py", "C:\\private.py", "pkg/"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.parser.parse("value = 1\n", path)


if __name__ == "__main__":
    unittest.main()