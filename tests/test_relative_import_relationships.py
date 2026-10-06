"""Static relationship resolution for package-relative and absolute imports."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from src.developer.local_workflow import parse_local_repository


class RelativeImportRelationshipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self):
        subprocess.run(["git", "-C", str(self.root), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Import Test"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "imports@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "--all"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "--quiet", "-m", "baseline"], check=True)

    def details(self, parsed, path, symbol):
        return next(row for row in parsed.context.values()
                    if row["source_region"].startswith(path + ":") and row["symbol_name"] == symbol)

    def test_same_package_parent_and_module_relative_imports_resolve(self):
        self.write("pkg/__init__.py", '"""Package."""\n')
        self.write("pkg/validation.py", "def require_rate(value):\n    return value\n")
        self.write("pkg/caller.py",
                   "from .validation import require_rate\n\ndef run(value):\n    return require_rate(value)\n")
        self.write("pkg/module_caller.py",
                   "from . import validation\n\ndef run(value):\n    return validation.require_rate(value)\n")
        self.write("pkg/shared.py", "def helper(value):\n    return value\n")
        self.write("pkg/sub/__init__.py", '"""Nested package."""\n')
        self.write("pkg/sub/caller.py",
                   "from ..shared import helper\n\ndef run(value):\n    return helper(value)\n")
        self.write("pkg/absolute_from.py",
                   "from pkg.validation import require_rate\n\ndef run(value):\n    return require_rate(value)\n")
        self.write("pkg/absolute_module.py",
                   "import pkg.validation\n\ndef run(value):\n    return pkg.validation.require_rate(value)\n")
        self.write("pkg/local_call.py",
                   "def helper(value):\n    return value\n\ndef run(value):\n    return helper(value)\n")
        self.commit()

        parsed = parse_local_repository(self.root)
        expected = {
            ("pkg/caller.py", "run"): ("pkg/validation.py", "require_rate", "call_relationship"),
            ("pkg/module_caller.py", "run"): ("pkg/validation.py", "require_rate", "call_relationship"),
            ("pkg/sub/caller.py", "run"): ("pkg/shared.py", "helper", "call_relationship"),
            ("pkg/absolute_from.py", "run"): ("pkg/validation.py", "require_rate", "call_relationship"),
            ("pkg/absolute_module.py", "run"): ("pkg/validation.py", "require_rate", "call_relationship"),
            ("pkg/local_call.py", "run"): ("pkg/local_call.py", "helper", "call_relationship"),
        }
        for (source_path, source_symbol), (target_path, target_symbol, kind) in expected.items():
            source = self.details(parsed, source_path, source_symbol)
            self.assertIn({"file_path": target_path, "symbol": target_symbol, "kind": kind},
                          source["relationship_edges"], source)
            self.assertFalse(source["relationship_diagnostics"], (source_path, source["relationship_diagnostics"]))
        imported = self.details(parsed, "pkg/module_caller.py", "run")
        self.assertIn({"file_path": "pkg/validation.py", "symbol": "pkg.validation",
                       "kind": "import_relationship"}, imported["relationship_edges"])

    def test_invalid_relative_import_and_ambiguous_relative_name_remain_diagnostics(self):
        self.write("pkg/__init__.py", '"""Package."""\n')
        self.write("pkg/invalid.py",
                   "from ...outside import missing\nfrom .absent import helper\n\ndef run():\n    return 1\n")
        self.write("amb/__init__.py", "def helper():\n    return 'package'\n")
        self.write("amb/helper.py", "def helper():\n    return 'module'\n")
        self.write("amb/caller.py", "from . import helper\n\ndef run():\n    return helper()\n")
        self.commit()

        parsed = parse_local_repository(self.root)
        invalid = self.details(parsed, "pkg/invalid.py", "run")
        self.assertTrue(any(row["status"] == "unresolved" and row["kind"] == "import_relationship"
                            and "beyond" in row["reason"] for row in invalid["relationship_diagnostics"]))
        self.assertTrue(any(row["status"] == "unresolved" and row["kind"] == "import_relationship"
                            and "not present" in row["reason"] for row in invalid["relationship_diagnostics"]))
        ambiguous = self.details(parsed, "amb/caller.py", "run")
        self.assertTrue(any(row["status"] == "ambiguous" and row["symbol"] == "helper"
                            for row in ambiguous["relationship_diagnostics"]))

if __name__ == "__main__":
    unittest.main()
