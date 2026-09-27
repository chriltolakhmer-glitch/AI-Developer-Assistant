"""Synthetic tests only: no frozen questions or third-party source in the repository."""

from dataclasses import replace
import hashlib
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import numpy as np

from src.evaluation.benchmark import Benchmark, BenchmarkCase
from src.evaluation.retrieval import RetrievalEvaluator
from src.models.chunk import CodeChunk
from src.retrieval.direct_calls import DirectCall, direct_calls
from src.retrieval.parent_child_passages import split_parent
from src.retrieval.parent_child_search import ParentChildSearch, _validate_inventory


def chunk(cid, content="def f():\n    return 1\n", file="src/pkg/main.py", name="f", kind="function"):
    return CodeChunk(cid, "fixture/repo", "a" * 40, file, kind, name, 1, len(content.splitlines()), content)


class CharacterTokenizer:
    def __call__(self, text, add_special_tokens=True, **kwargs):
        out = {"input_ids": [1] * (len(text) + (2 if add_special_tokens else 0))}
        if kwargs.get("return_offsets_mapping"):
            out["offset_mapping"] = [(i, i + 1) for i in range(len(text))]
        return out


class ParentChildTests(unittest.TestCase):
    def test_long_line_full_coverage_stable_identity_and_budget(self):
        parent = chunk("parent", "  " + "x" * 900 + "\n")
        children = split_parent(parent, CharacterTokenizer())
        self.assertEqual(children, split_parent(parent, CharacterTokenizer()))
        self.assertGreater(len(children), 1)
        covered = set()
        for child in children:
            self.assertEqual("parent", child.parent_chunk_id)
            self.assertLessEqual(child.token_count, 256)
            self.assertEqual(parent.content[child.char_start:child.char_end], child.content)
            self.assertEqual(hashlib.sha256(child.content.encode()).hexdigest(), child.content_sha256)
            covered.update(range(child.char_start, child.char_end))
        self.assertEqual(set(range(len(parent.content))), covered)
        self.assertEqual(len(children), len({c.child_id for c in children}))

    def test_accepted_parent_keeps_exact_source(self):
        parent = chunk("parent")
        child, = split_parent(parent, CharacterTokenizer())
        self.assertEqual(parent.content, child.content)
        self.assertNotEqual(parent.chunk_id, child.child_id)
        with self.assertRaises(ValueError):
            split_parent(replace(parent, content="\n  "), CharacterTokenizer())

    def make_search(self, edges=True, ties=False):
        parents = tuple(chunk(cid, f"def {cid}():\n    return 1\n", name=cid) for cid in "abcdefgh")
        children = tuple(c for p in parents for c in split_parent(p, CharacterTokenizer()))
        vectors = np.zeros((8, 384), dtype=np.float32)
        vectors[:, 0] = 1 if ties else np.arange(8, 0, -1) / 10
        vectors[:, 1] = np.sqrt(1 - vectors[:, 0] ** 2)
        graph = (DirectCall("a", "g", "src/pkg/main.py", 1, "g"),
                 DirectCall("a", "h", "src/pkg/main.py", 1, "h"),
                 DirectCall("b", "g", "src/pkg/main.py", 1, "g"),
                 DirectCall("g", "f", "src/pkg/main.py", 1, "f")) if edges else ()
        model = Mock()
        model.tokenizer = CharacterTokenizer()
        model.encode.return_value = np.array([[1.] + [0.] * 383], dtype=np.float32)
        return ParentChildSearch._assemble(parents, children, vectors, graph,
                                           {p.chunk_id: len(p.content)+2 for p in parents}, model)

    def test_bounded_expansion_provenance_and_evaluator_compatibility(self):
        search = self.make_search()
        response = search.search_with_details("question")
        self.assertEqual(["a", "b", "c", "g", "h"], [r.chunk_id for r in response.results])
        self.assertEqual(("a", "b"), response.results[3].expansion_from)
        self.assertEqual(7, response.results[3].dense_rank)
        self.assertEqual("def g():\n    return 1\n", response.results[3].content)
        self.assertEqual(response, search.search_with_details("question"))
        # The edge g -> f must not trigger a second hop; returned IDs stay parents.
        self.assertNotIn("f", [r.chunk_id for r in response.results])
        case = BenchmarkCase("q", "fixture/repo", "a"*40, "question", (("g", 1), ("a", 2)))
        report = RetrievalEvaluator().evaluate(Benchmark("1.0", (case,)), "parent_child",
                                               lambda c: search.search(c.query), ks=(5,))
        self.assertEqual(((5, 1.0),), report.recall)

    def test_no_edges_fill_and_parent_ties_are_deterministic(self):
        search = self.make_search(edges=False, ties=True)
        self.assertEqual(list("abcde"), [r.chunk_id for r in search.search("q")])
        self.assertTrue(all(not r.expansion_from for r in search.search("q")))
        with self.assertRaises(ValueError):
            search._vectors.setflags(write=True)

    def test_multiple_children_do_not_consume_parent_slots(self):
        search = self.make_search(edges=False)
        children = search.children + (replace(search.children[0], child_id="extra"),)
        vectors = np.concatenate((search._vectors, search._vectors[:1]), axis=0)
        duplicate = ParentChildSearch._assemble(search.parents, children, vectors, (), search._counts, search._model)
        self.assertEqual(list("abcde"), [r.chunk_id for r in duplicate.search("q")])

    def test_invalid_query_and_cutoff_rejected_before_encoding(self):
        search = self.make_search()
        for query in (None, " ", "x"*255):
            with self.assertRaises(ValueError):
                search.search(query)
        for k in (True, 0, 4, 6):
            with self.assertRaises(ValueError):
                search.search("q", k)
        search._model.encode.assert_not_called()

    def test_wrong_frozen_inventory_fails_before_model_load(self):
        with self.assertRaises(ValueError):
            _validate_inventory((), b"different frozen map", {})
        with patch("src.retrieval.parent_child_search.external_path") as path, patch("src.retrieval.parent_child_search.load_model") as load:
            path.return_value.read_bytes.return_value = b"wrong"
            with self.assertRaises(ValueError):
                ParentChildSearch.build((), chunk_map_path=Path("map"), sources={}, model_cache=Path("cache"))
            load.assert_not_called()


class DirectCallTests(unittest.TestCase):
    def test_relative_absolute_aliases_and_local_functions(self):
        text = "from .helpers import helper as h\nfrom pkg.helpers import helper as other\ndef caller():\n    h()\n    other()\n    local()\ndef local():\n    return 0\n"
        parents = (chunk("caller", text, name="caller"), chunk("local", name="local"),
                   chunk("helper", file="src/pkg/helpers.py", name="helper"))
        edges = direct_calls(parents, {"src/pkg/main.py": text})
        self.assertEqual({("caller", "helper", "h"), ("caller", "helper", "other"), ("caller", "local", "local")},
                         {(e.caller_id, e.callee_id, e.call_name) for e in edges})

    def test_shadowing_nested_scope_ambiguity_and_unknown_calls(self):
        text = ("from .helpers import helper as h\nfrom .helpers import helper as ambiguous\n"
                "ambiguous = None\ndef caller(h):\n    h()\n    ambiguous()\n    missing()\n"
                "    obj.helper()\n    def nested():\n        helper()\n    return 0\n")
        parents = (chunk("caller", name="caller"), chunk("helper", name="helper", file="src/pkg/helpers.py"))
        self.assertEqual((), direct_calls(parents, {"src/pkg/main.py": text}))

    def test_local_assignment_blocks_apparent_global_call(self):
        text = "from .helpers import helper as h\ndef caller():\n    h = lambda: 1\n    return h()\n"
        parents = (chunk("caller", name="caller"), chunk("helper", name="helper", file="src/pkg/helpers.py"))
        self.assertEqual((), direct_calls(parents, {"src/pkg/main.py": text}))


if __name__ == "__main__":
    unittest.main()
