from dataclasses import replace
from pathlib import Path
from threading import Event, get_ident
import time
from unittest.mock import patch

try:
    import tkinter as tk
except ImportError:
    tk = None

from src.config import load_config
from src.ui.service import RepositoryService
from tests.ui_fixture import GitFixture


class UIWidgetTests(GitFixture):
    def setUp(self):
        super().setUp()
        if tk is None:
            self.skipTest("Tkinter is unavailable in this Python installation")
        try:
            self.window = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Cannot initialize Tk: {error}")
        self.window.withdraw()
        self.addCleanup(self.close_window)
        from src.ui.app import Application
        config = replace(load_config(environ={}), developer_workspace=self.workspace_path)
        self.app = Application(self.window, RepositoryService(config), self.workspace_path)

    def close_window(self):
        if not self.app.closed:
            self.app.request_close()
            self.wait_until(lambda: self.app.closed)

    def wait_until(self, predicate, timeout=15):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            if not self.app.closed:
                self.window.update()
            time.sleep(0.005)
        self.assertTrue(predicate(), "Tk operation did not finish")

    def open(self, path=None):
        self.app.view.repository.set(str(path or self.repo))
        self.app.view.workspace.set(str(self.workspace_path))
        self.app.view.open_button.invoke()
        self.wait_until(lambda: not self.app.state.loading)

    def test_four_tabs_and_open_refresh_preserve_repository_and_workspace(self):
        tabs = self.app.view.notebook.tabs()
        self.assertEqual(["Project", "Plan & Review", "Run & Result", "History"],
                         [self.app.view.notebook.tab(tab, "text") for tab in tabs])
        for tab in tabs[2:]:
            children = self.window.nametowidget(tab).winfo_children()
            self.assertEqual(["TLabel"], [child.winfo_class() for child in children])
        before = self.snapshot()
        self.open()
        self.assertEqual("Clean", self.app.view.fields["clean"].get())
        self.assertEqual("main", self.app.view.fields["branch"].get())
        self.assertEqual(self.git("rev-parse", "HEAD").decode().strip(), self.app.view.fields["head"].get())
        self.app.view.refresh_button.invoke()
        self.wait_until(lambda: not self.app.state.loading)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.workspace_path.exists())

    def test_browse_selects_repository_and_workspace_and_displays_facts(self):
        with patch("src.ui.app.filedialog.askdirectory", return_value=str(self.root / "chosen-workspace")):
            self.app.view.browse_workspace_button.invoke()
        self.assertEqual(str(self.root / "chosen-workspace"), self.app.view.workspace.get())
        with patch("src.ui.app.filedialog.askdirectory", return_value=str(self.repo)):
            self.app.view.browse_repo_button.invoke()
        self.wait_until(lambda: not self.app.state.loading)
        self.assertEqual(str(self.repo.resolve()), self.app.state.repository)
        self.assertEqual(str((self.root / "chosen-workspace").resolve()), self.app.state.workspace)
        self.assertEqual("main", self.app.view.fields["branch"].get())
        self.assertFalse((self.root / "chosen-workspace").exists())

    def test_invalid_repository_displays_error_without_crash(self):
        invalid = self.root / "invalid"
        invalid.mkdir()
        self.open(invalid)
        self.assertIsNotNone(self.app.state.error)
        self.assertIn("Git", self.app.view.status.get())
        self.assertIsNone(self.app.state.facts)
        self.assertFalse(self.workspace_path.exists())

    def test_one_non_daemon_worker_busy_controls_and_main_thread_render(self):
        release, started = Event(), Event()
        self.addCleanup(release.set)
        original_read = self.app.service.read_repository
        calls = []
        def read(repository, workspace):
            calls.append(get_ident())
            started.set()
            release.wait(5)
            return original_read(repository, workspace)
        main_thread = get_ident()
        actual_render = self.app.view.render
        def render(state):
            self.assertEqual(main_thread, get_ident())
            actual_render(state)
        with patch.object(self.app.service, "read_repository", side_effect=read), \
                patch.object(self.app.view, "render", side_effect=render):
            self.app.view.repository.set(str(self.repo))
            self.app.view.open_button.invoke()
            self.wait_until(started.is_set)
            self.assertFalse(self.app.worker.daemon)
            self.assertEqual("disabled", str(self.app.view.refresh_button.cget("state")))
            self.app.open_repository()
            self.app.view.refresh_button.invoke()
            self.assertEqual(1, len(calls))
            self.assertNotEqual(main_thread, calls[0])
            release.set()
            self.wait_until(lambda: not self.app.state.loading)
        self.assertIsNotNone(self.app.state.facts)

    def test_pending_close_keeps_loop_responsive_and_processes_result_without_join(self):
        release, started, tick = Event(), Event(), Event()
        self.addCleanup(release.set)
        original_read = self.app.service.read_repository
        def read(repository, workspace):
            started.set()
            release.wait(5)
            return original_read(repository, workspace)
        with patch.object(self.app.service, "read_repository", side_effect=read):
            self.app.view.repository.set(str(self.repo))
            self.app.open_repository()
            self.wait_until(started.is_set)
            with patch.object(self.app.worker, "join", side_effect=AssertionError("blocking join")):
                self.app.request_close()
                self.assertTrue(self.app.state.close_pending)
                self.assertFalse(self.app.closed)
                self.assertIn("Close pending", self.app.view.status.get())
                self.window.after(5, tick.set)
                self.wait_until(tick.is_set)
                self.assertFalse(self.app.closed)
                release.set()
                self.wait_until(lambda: self.app.closed)
        self.assertIsNotNone(self.app.state.facts)
        self.assertTrue(self.app.state.facts["clean"])

    def test_unexpected_worker_failure_is_delivered_before_pending_close(self):
        release, started = Event(), Event()
        self.addCleanup(release.set)
        def failing(repository, workspace):
            started.set()
            release.wait(5)
            raise RuntimeError("worker failure")
        with patch.object(self.app.service, "read_repository", side_effect=failing):
            self.app.view.repository.set(str(self.repo))
            self.app.open_repository()
            self.wait_until(started.is_set)
            self.app.request_close()
            release.set()
            self.wait_until(lambda: self.app.closed)
        self.assertEqual("RuntimeError: worker failure", self.app.state.error)

    def test_window_can_render_visible_and_close_when_idle(self):
        self.window.deiconify()
        self.window.update()
        self.assertTrue(self.window.winfo_viewable())
        self.assertGreater(self.app.view.project.winfo_width(), 0)
        self.app.request_close()
        self.assertTrue(self.app.closed)

    def test_malformed_result_is_displayed_and_pending_close_finishes(self):
        with patch.object(self.app.service, "read_repository", return_value={}):
            self.app.view.repository.set(str(self.repo))
            self.app.open_repository()
            self.app.request_close()
            self.wait_until(lambda: self.app.closed)
        self.assertIsNone(self.app.state.facts)
        self.assertIn("Cannot display repository result", self.app.state.error)
