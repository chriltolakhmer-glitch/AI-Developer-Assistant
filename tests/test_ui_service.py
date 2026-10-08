from contextlib import redirect_stderr
from dataclasses import replace
from io import StringIO
import unittest
from unittest.mock import patch

from src.config import load_config
from src.developer.local_workflow import LocalWorkflowError
from src.ui.__main__ import main
from src.ui.service import RepositoryService
from tests.ui_fixture import GitFixture


class UIServiceTests(GitFixture):
    def config(self):
        return replace(load_config(environ={}), developer_workspace=self.workspace_path,
                       data_root=self.root / "research", corpus_root=self.root / "corpus",
                       validation_output=self.root / "validation", embedding_model_cache=self.root / "model")

    def test_exact_inputs_protected_roots_and_backend_result_preserved(self):
        config = self.config()
        service = RepositoryService(config)
        result = {"display": "facts"}
        with patch("src.developer.ui_read.read_repository", return_value=result) as reader:
            self.assertIs(result, service.read_repository(str(self.repo), str(self.workspace_path)))
        developer, repository = reader.call_args.args
        self.assertEqual(self.repo, repository)
        self.assertEqual(self.workspace_path.resolve(), developer.root)
        self.assertEqual(tuple(path.resolve() for path in (config.data_root, config.corpus_root,
                                                         config.validation_output, config.embedding_model_cache)),
                         developer.research_roots)
        self.assertFalse(self.workspace_path.exists())

    def test_errors_propagate_and_only_supported_operations_exist(self):
        service = RepositoryService(self.config())
        with patch("src.developer.ui_read.read_repository", side_effect=LocalWorkflowError("exact reason")):
            with self.assertRaisesRegex(LocalWorkflowError, "exact reason"):
                service.read_repository(str(self.repo), str(self.workspace_path))
        self.assertEqual(["read_repository", "scan", "index", "catalog_tests", "plan", "import_candidate", "review_patch", "decide", "apply", "test", "verify", "evaluate", "read_log"], [name for name, value in RepositoryService.__dict__.items()
                                              if not name.startswith("_") and callable(value)])

    def test_service_open_and_refresh_do_not_write(self):
        service = RepositoryService(self.config())
        before = self.snapshot()
        for _ in range(2):
            facts = service.read_repository(str(self.repo), str(self.workspace_path))
            self.assertTrue(facts["clean"])
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.workspace_path.exists())


class UIEntrypointTests(unittest.TestCase):
    def test_missing_tk_import_is_actionable_without_install_or_fallback(self):
        import builtins
        actual_import = builtins.__import__
        def import_without_tk(name, *args, **kwargs):
            if name == "tkinter":
                raise ImportError("Tcl/Tk unavailable")
            return actual_import(name, *args, **kwargs)
        output = StringIO()
        with patch("builtins.__import__", side_effect=import_without_tk), redirect_stderr(output):
            self.assertEqual(2, main())
        self.assertIn("requires Python with Tkinter/Tcl/Tk", output.getvalue())

    def test_missing_display_runtime_is_actionable(self):
        import tkinter
        output = StringIO()
        with patch("tkinter.Tk", side_effect=tkinter.TclError("no desktop")), redirect_stderr(output):
            self.assertEqual(2, main())
        self.assertIn("cannot initialize Tcl/Tk", output.getvalue())

    def test_launch_loads_config_shell_and_does_no_repository_work(self):
        from unittest.mock import Mock
        root = Mock()
        config = load_config(environ={})
        with patch("tkinter.Tk", return_value=root), patch("src.config.load_config", return_value=config), \
                patch("src.ui.app.Application") as shell, \
                patch.object(RepositoryService, "read_repository", side_effect=AssertionError("startup read")):
            self.assertEqual(0, main())
            self.assertEqual(config.developer_workspace, shell.call_args.args[2])
            root.mainloop.assert_called_once()

    def test_package_import_does_no_ui_or_backend_work(self):
        import importlib
        import src.ui
        with patch("tkinter.Tk", side_effect=AssertionError("root")), \
                patch.object(RepositoryService, "read_repository", side_effect=AssertionError("read")):
            importlib.reload(src.ui)
