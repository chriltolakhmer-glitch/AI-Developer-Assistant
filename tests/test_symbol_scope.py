"""Focused deterministic, path-qualified source symbol authorization tests."""
import difflib
import unittest

from src.developer.local_workflow import LocalWorkflowError
from src.developer.symbol_scope import (MODULE_SYMBOL, derive_patch_symbols,
                                        scope_is_allowed)


def patch(path, before, after):
    return "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                         fromfile="a/" + path, tofile="b/" + path))


class SymbolScopeTests(unittest.TestCase):
    def test_function_body_is_path_qualified_and_strict_subset_is_allowed(self):
        before = "def run():\n    return 1\n\ndef reset_state():\n    return 0\n"
        after = before.replace("return 1", "return 2")
        symbols = derive_patch_symbols(patch("src/app.py", before, after),
                                       {"src/app.py": before}, {"src/app.py": after})
        self.assertEqual((("src/app.py", "run"),), symbols)
        self.assertTrue(scope_is_allowed(symbols, (("src/app.py", "run"),), {"src/app.py": before}))

    def test_sibling_expansion_and_different_sibling_are_rejected(self):
        before = "def run():\n    return 1\n\ndef reset_state():\n    return 0\n"
        after = before.replace("return 1", "return 2").replace("return 0", "return 3")
        symbols = derive_patch_symbols(patch("src/app.py", before, after),
                                       {"src/app.py": before}, {"src/app.py": after})
        self.assertEqual({("src/app.py", "run"), ("src/app.py", "reset_state")}, set(symbols))
        self.assertFalse(scope_is_allowed(symbols, (("src/app.py", "run"),), {"src/app.py": before}))
        reset = before.replace("return 0", "return 3")
        symbols = derive_patch_symbols(patch("src/app.py", before, reset),
                                       {"src/app.py": before}, {"src/app.py": reset})
        self.assertFalse(scope_is_allowed(symbols, (("src/app.py", "run"),), {"src/app.py": before}))

    def test_same_name_in_another_file_is_not_authorized(self):
        source = "def run():\n    return 1\n"
        changed = source.replace("1", "2")
        symbols = derive_patch_symbols(patch("src/b.py", source, changed),
                                       {"src/b.py": source}, {"src/b.py": changed})
        self.assertFalse(scope_is_allowed(symbols, (("src/a.py", "run"),), {"src/b.py": source}))

    def test_class_ancestor_requires_parser_proven_member_and_sibling_is_denied(self):
        before = "class User:\n    def validate(self):\n        return True\n    def delete(self):\n        return False\n"
        validate_changed = before.replace("return True", "return False")
        symbols = derive_patch_symbols(patch("src/app.py", before, validate_changed),
                                       {"src/app.py": before}, {"src/app.py": validate_changed})
        self.assertEqual((("src/app.py", "User.validate"),), symbols)
        self.assertTrue(scope_is_allowed(symbols, (("src/app.py", "User"),), {"src/app.py": before}))
        delete_changed = before.replace("return False", "return True")
        symbols = derive_patch_symbols(patch("src/app.py", before, delete_changed),
                                       {"src/app.py": before}, {"src/app.py": delete_changed})
        self.assertFalse(scope_is_allowed(symbols, (("src/app.py", "User.validate"),), {"src/app.py": before}))

    def test_module_changes_are_explicit_and_old_deleted_symbol_is_attributed(self):
        before = "import os\n\ndef run():\n    return os.getcwd()\n"
        module_change = before.replace("import os", "import sys")
        symbols = derive_patch_symbols(patch("src/app.py", before, module_change),
                                       {"src/app.py": before}, {"src/app.py": module_change})
        self.assertIn(("src/app.py", MODULE_SYMBOL), symbols)
        self.assertFalse(scope_is_allowed(symbols, (("src/app.py", "run"),), {"src/app.py": before}))
        deleted = "import os\n"
        symbols = derive_patch_symbols(patch("src/app.py", before, deleted),
                                       {"src/app.py": before}, {"src/app.py": deleted})
        self.assertIn(("src/app.py", "run"), symbols)

    def test_new_symbol_is_visible_and_unparseable_postimage_fails_closed(self):
        before = "def run():\n    return 1\n"
        after = before + "\ndef reset_state():\n    return 0\n"
        symbols = derive_patch_symbols(patch("src/app.py", before, after),
                                       {"src/app.py": before}, {"src/app.py": after})
        self.assertEqual((("src/app.py", "reset_state"),), symbols)
        malformed = before + "\ndef broken(:\n"
        with self.assertRaises(LocalWorkflowError):
            derive_patch_symbols(patch("src/app.py", before, malformed),
                                 {"src/app.py": before}, {"src/app.py": malformed})


if __name__ == "__main__":
    unittest.main()
