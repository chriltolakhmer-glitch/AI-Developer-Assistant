"""Tests for deterministic AST-based semantic code chunking."""

import unittest

from src.chunker import CodeChunker
from src.models import RepositoryMetadata
from src.parser import PythonAstParser


SOURCE = """\
import os
@decorator
class Demo:
    value = 1
    def method(self):
        return "method"

def helper():
    return "helper"
"""


class CodeChunkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = RepositoryMetadata(
            repository_id="example/repository",
            commit_sha="a" * 40,
            repository_url="https://example.invalid/repository",
        )
        self.module = PythonAstParser().parse(SOURCE, "pkg/demo.py")
        self.chunker = CodeChunker()

    def test_chunk_generation_is_deterministic(self) -> None:
        first = self.chunker.chunk_module(self.module, SOURCE, self.repository)
        second = self.chunker.chunk_module(self.module, SOURCE, self.repository)

        self.assertEqual(first, second)
        self.assertEqual(
            [chunk.chunk_id for chunk in first],
            [chunk.chunk_id for chunk in second],
        )

    def test_preserves_repository_and_file_provenance_on_every_chunk(self) -> None:
        chunks = self.chunker.chunk_module(self.module, SOURCE, self.repository)

        self.assertTrue(chunks)
        for chunk in chunks:
            self.assertEqual("example/repository", chunk.repository_id)
            self.assertEqual("a" * 40, chunk.commit_sha)
            self.assertEqual("pkg/demo.py", chunk.file_path)
            self.assertEqual(64, len(chunk.chunk_id))

    def test_emits_module_class_function_and_method_chunks(self) -> None:
        chunks = self.chunker.chunk_module(self.module, SOURCE, self.repository)

        self.assertEqual(
            ["module", "class", "method", "function"],
            [chunk.entity_type for chunk in chunks],
        )
        self.assertEqual("pkg.demo", chunks[0].qualified_name)
        self.assertEqual("Demo", chunks[1].qualified_name)
        self.assertEqual("Demo.method", chunks[2].qualified_name)
        self.assertEqual("helper", chunks[3].qualified_name)
        self.assertEqual(SOURCE, chunks[0].content)
        self.assertIn("class Demo:", chunks[1].content)
        self.assertIn('return "method"', chunks[2].content)
        self.assertIn('return "helper"', chunks[3].content)

    def test_tracks_exact_inclusive_source_ranges_and_decorator_lines(self) -> None:
        chunks = self.chunker.chunk_module(self.module, SOURCE, self.repository)
        by_entity = {chunk.qualified_name: chunk for chunk in chunks}

        self.assertEqual((1, 9), (by_entity["pkg.demo"].start_line, by_entity["pkg.demo"].end_line))
        self.assertEqual((2, 6), (by_entity["Demo"].start_line, by_entity["Demo"].end_line))
        self.assertEqual((5, 6), (by_entity["Demo.method"].start_line, by_entity["Demo.method"].end_line))
        self.assertTrue(by_entity["Demo"].content.startswith("@decorator\n"))
        self.assertTrue(by_entity["Demo.method"].content.startswith("    def method(self):\n"))

    def test_rejects_source_that_does_not_match_the_parsed_module_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "same source"):
            self.chunker.chunk_module(self.module, "different\nline count\n", self.repository)


if __name__ == "__main__":
    unittest.main()