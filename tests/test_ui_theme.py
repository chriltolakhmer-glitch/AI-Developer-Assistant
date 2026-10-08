from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from threading import Event
import time
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from src.config import load_config
from src.ui.app import Application
from src.ui.diff_view import DiffView
from src.ui.preferences import AppearancePreferences
from src.ui.service import RepositoryService
from src.ui.theme import ThemeController, SystemAppearance, ThemedScrolledText, contrast, detect_windows_appearance
from tests.ui_fixture import GitFixture
from tests.test_ui_decision_widgets import DecisionWidgetFixture


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.window = tk.Tk()
        self.window.withdraw()
        self.system = SystemAppearance('Light')
        self.theme = ThemeController(self.window, detector=lambda: self.system)
        self.addCleanup(self.close)

    def close(self):
        self.theme.close()
        self.window.destroy()

    def test_all_modes_runtime_detection_fallback_and_high_contrast_priority(self):
        for mode in ('Light', 'Dark', 'System'):
            self.theme.set_mode(mode)
            self.assertEqual('Dark' if mode == 'Dark' else 'Light', self.theme.resolved)
        self.system = SystemAppearance('Dark')
        self.theme.refresh()
        self.assertEqual('Dark', self.theme.resolved)
        self.system = SystemAppearance()
        self.theme.refresh()
        self.assertEqual(('System', 'Light'), (self.theme.mode, self.theme.resolved))
        self.assertIn('unavailable', self.theme.message)
        self.system = SystemAppearance('Dark', True, tuple(dict(main='#000000', text='#FFFFFF',
             selected='#FFFF00', selection_text='#000000', focus='#FFFF00').items()))
        self.theme.set_mode('Light')
        self.assertEqual('#000000', self.theme.colors['main'])
        self.assertIn('high contrast', self.theme.message)

    def test_detector_reads_windows_without_changing_settings_and_nonwindows_fallback(self):
        result = detect_windows_appearance()
        self.assertIn(result.mode, (None, 'Light', 'Dark'))
        with patch('src.ui.theme.sys.platform', 'other'):
            self.assertEqual(SystemAppearance(), detect_windows_appearance())
        with patch.object(self.theme, 'detector', side_effect=OSError('unavailable')):
            self.theme.set_mode('System')
        self.assertIn('unavailable', self.theme.message)

    def test_rendered_contrast_widget_states_diff_and_popup_colors(self):
        text = tk.Text(self.window)
        listing = tk.Listbox(self.window)
        button = ttk.Button(self.window, text='Action')
        entry = ttk.Entry(self.window)
        combo = ttk.Combobox(self.window, state='readonly', values=('Light', 'Dark'))
        tree = ttk.Treeview(self.window)
        view = DiffView(self.window)
        view.show('--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-old\n+new\n')
        for mode in ('Light', 'Dark'):
            self.theme.set_mode(mode)
            for widget in (text, listing, view.text):
                self.assertGreaterEqual(contrast(widget.cget('foreground'), widget.cget('background')), 4.5)
                self.assertGreaterEqual(contrast(widget.cget('selectforeground'), widget.cget('selectbackground')), 4.5)
                self.assertGreaterEqual(contrast(widget.cget('highlightcolor'), widget.cget('background')), 3)
            self.assertGreaterEqual(contrast(listing.cget('disabledforeground'), listing.cget('background')), 4.5)
            for tag in ('addition', 'deletion', 'heading', 'hunk'):
                self.assertGreaterEqual(contrast(view.text.tag_cget(tag, 'foreground'),
                                                view.text.tag_cget(tag, 'background')), 4.5)
            style = self.theme.style
            for state in ((), ('active',), ('disabled',), ('focus',)):
                self.assertGreaterEqual(contrast(style.lookup('TButton', 'foreground', state),
                                                style.lookup('TButton', 'background', state)), 4.5)
            for name in ('TEntry', 'TCombobox'):
                for state in ((), ('disabled',), ('readonly',)):
                    self.assertGreaterEqual(contrast(style.lookup(name, 'foreground', state),
                                                    style.lookup(name, 'fieldbackground', state)), 4.5)
            for tag in ('Warning.TLabel', 'Error.TLabel'):
                self.assertGreaterEqual(contrast(style.lookup(tag, 'foreground'), style.lookup(tag, 'background')), 4.5)
            self.assertGreaterEqual(contrast(style.lookup('TButton', 'bordercolor', ('focus',)),
                                            style.lookup('TButton', 'background', ('focus',))), 3)
            pop = combo.tk.call('ttk::combobox::PopdownWindow', combo)
            self.assertEqual(self.theme.colors['main'], combo.tk.call(f'{pop}.f.l', 'cget', '-background'))
            self.assertEqual(self.theme.colors['main'], style.lookup('Treeview', 'fieldbackground'))
        button.state(['disabled'])
        self.theme.set_mode('Light')
        self.assertTrue(button.instate(['disabled']))

    def test_new_dialogs_focus_selection_scroll_and_raw_diff_remain_intact(self):
        self.window.deiconify()
        view = DiffView(self.window)
        view.pack(fill='both', expand=True)
        raw = '--- a/a.py\r\n+++ b/a.py\r\n@@ -1 +1 @@\r\n-old\r\n+€' + 'x' * 4000
        view.show(raw)
        self.window.update()
        view.text.xview_moveto(.3)
        view.text.tag_add('sel', '2.0', '3.0')
        view.text.focus_force()
        self.window.update()
        before = (view.text.xview(), view.text.yview(), view.text.tag_ranges('sel'), self.window.focus_get())
        self.theme.set_mode('Dark')
        self.assertEqual(before, (view.text.xview(), view.text.yview(), view.text.tag_ranges('sel'), self.window.focus_get()))
        self.assertEqual(raw, view.text.get('1.0', 'end-1c'))
        self.assertEqual(raw, view.stored_text)
        dialog = tk.Toplevel(self.window)
        detail = ThemedScrolledText(dialog)
        detail.pack()
        detail.insert('1.0', 'literal log €\r\n<script>')
        detail.configure(state='disabled')
        self.window.update()
        self.assertEqual(self.theme.colors['main'], detail.cget('background'))
        self.assertEqual('disabled', detail.cget('state'))
        self.assertEqual('TScrollbar', detail.vbar.winfo_class())
        dialog.destroy()

    def test_keyboard_traversal_and_focus_under_practical_tk_scaling(self):
        self.window.deiconify()
        first = ttk.Entry(self.window)
        second = ttk.Button(self.window, text='Safe action')
        first.pack(); second.pack()
        for scaling in (1.333333, 2.0, 2.666667):
            self.window.tk.call('tk', 'scaling', scaling)
            for mode in ('Light', 'Dark'):
                self.theme.set_mode(mode)
                first.focus_force()
                self.window.update()
                self.assertEqual(second, first.tk_focusNext())
                first.event_generate('<Tab>')
                self.window.update()
                self.assertEqual(second, self.window.focus_get())
                self.assertGreaterEqual(contrast(self.theme.style.lookup('TButton', 'focuscolor'),
                                                self.theme.style.lookup('TButton', 'background')), 3)


class ThemeApplicationTests(GitFixture):
    def setUp(self):
        super().setUp()
        self.window = tk.Tk(); self.window.withdraw()
        config = replace(load_config(environ={}), developer_workspace=self.workspace_path)
        self.service = RepositoryService(config)
        self.preferences = AppearancePreferences((self.repo,), path=self.root / 'settings' / 'preferences.json')
        self.app = Application(self.window, self.service, self.workspace_path, preferences=self.preferences,
                               appearance_detector=lambda: SystemAppearance())
        self.addCleanup(self.close)

    def close(self):
        if not self.app.closed:
            self.app.request_close()
            self.wait(lambda: self.app.closed)

    def wait(self, predicate):
        deadline = time.monotonic() + 15
        while not predicate() and time.monotonic() < deadline:
            self.window.update()
            time.sleep(.005)
        self.assertTrue(predicate())

    def switch(self, mode):
        self.app.view.appearance.set(mode)
        self.app.view.appearance_selector.event_generate('<<ComboboxSelected>>')

    def test_change_preserves_inputs_evidence_ids_safety_latches_without_backend_calls(self):
        view, state = self.app.view, self.app.state
        view.goal.insert('1.0', 'unsent € goal')
        view.review_note.set('exact note')
        state.application_result = {'run_id': 'exact-execution', 'status': 'applied'}
        state.selected_execution_run_id = 'exact-execution'
        state.branch_context_invalidated = True
        state.test_request_state = 'outcome_unknown'
        view.log_text.configure(state='normal'); view.log_text.insert('1.0', 'log €\r\n')
        view.log_text.configure(state='disabled')
        baseline = deepcopy(state)
        before = self.snapshot()
        with patch.object(self.app, 'start_operation', side_effect=AssertionError('theme dispatched backend')):
            for mode in ('Dark', 'Light', 'System'):
                self.switch(mode)
                self.assertEqual(baseline, state)
                self.assertEqual('unsent € goal', view.goal.get('1.0', 'end-1c'))
                self.assertEqual('exact note', view.review_note.get())
                self.assertEqual('log €\r\n', view.log_text.get('1.0', 'end-1c'))
        self.assertEqual(before, self.snapshot())
        self.assertEqual(4, len(view.notebook.tabs()))

    def test_switch_during_worker_preserves_request_and_pending_close_and_save_failure(self):
        started, release = Event(), Event()
        def read(*args):
            started.set()
            release.wait(10)
            return {'repository_path': str(self.repo), 'workspace_path': str(self.workspace_path)}
        self.app.view.repository.set(str(self.repo))
        with patch.object(self.service, 'read_repository', side_effect=read) as call:
            self.app.view.open_button.invoke()
            self.wait(started.is_set)
            request, worker = self.app.state._active, self.app.worker
            with patch.object(self.preferences, 'save', return_value='Appearance preference not saved: denied'):
                self.switch('Dark')
            self.assertIn('denied', self.app.view.appearance_status.get())
            self.assertIs(request, self.app.state._active)
            self.assertIs(worker, self.app.worker)
            self.assertTrue(worker.is_alive())
            self.assertTrue(self.app.state.loading)
            call.assert_called_once()
            self.app.request_close()
            self.assertTrue(self.app.state.close_pending)
            self.switch('Light')
            self.assertTrue(self.app.state.close_pending)
            release.set()
            self.wait(lambda: self.app.closed)


class ThemeConfirmationTests(DecisionWidgetFixture):
    def test_approval_dialog_context_and_exact_evidence_survive_appearance_change(self):
        self.draft()
        context = self.confirmation()
        dialog = self.app.view.confirmation
        before = self.app.view.confirmation_details.get('1.0', 'end-1c')
        state = deepcopy(self.app.state)
        for mode in ('Dark', 'Light', 'System'):
            self.app.theme.set_mode(mode)
            self.assertIs(dialog, self.app.view.confirmation)
            self.assertEqual(context, self.app.state.pending_approval)
            self.assertEqual(state, self.app.state)
            self.assertEqual(before, self.app.view.confirmation_details.get('1.0', 'end-1c'))
            self.assertEqual('disabled', self.app.view.confirmation_details.cget('state'))
            self.assertEqual('', dialog.bind('<Return>'))

    def test_apply_confirmation_context_and_log_evidence_survive_system_change(self):
        self.draft(); self.confirmation(); self.app.view.confirm_button.invoke()
        self.wait(lambda: not self.app.state.loading)
        decision = self.app.state.decision_result
        self.app.view.selected_authorization.set(decision['run_id']); self.app.inputs_changed()
        self.app.view.apply_button.invoke()
        context, dialog = self.app.state.pending_apply, self.app.view.apply_confirmation
        before = deepcopy(self.app.state)
        for mode in ('Dark', 'Light'):
            self.app.theme.set_mode(mode)
            self.assertIs(dialog, self.app.view.apply_confirmation)
            self.assertEqual(context, self.app.state.pending_apply)
            self.assertEqual(before, self.app.state)
            self.assertIsNone(self.app.state.application_result)
            self.assertEqual('', dialog.bind('<Return>'))
