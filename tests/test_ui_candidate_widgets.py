import tkinter as tk
import time
from threading import Event, get_ident
from unittest.mock import patch
from src.ui.app import Application
from tests.ui_fixture import GitFixture
from tests import test_ui_candidates as fixtures
from tests.test_implementation_planning import _Model


class CandidateWidgetTests(fixtures.CandidateFixture):
    def setUp(self):
        super().setUp()
        self.window = tk.Tk(); self.window.withdraw()
        self.app = Application(self.window, self.service, self.workspace_path)
        self.addCleanup(self.close)
        self.app.view.repository.set(str(self.repo))
        self.app.view.open_button.invoke(); self.wait(lambda: not self.app.state.loading)

    def wait(self, predicate):
        until = time.monotonic() + 20
        while not predicate() and time.monotonic() < until:
            if not self.app.closed: self.window.update()
            time.sleep(.005)
        self.assertTrue(predicate())

    def close(self):
        if not self.app.closed:
            self.app.request_close(); self.wait(lambda: self.app.closed)

    def plan(self):
        with patch('src.developer.local_workflow.load_model', return_value=_Model()):
            self.app.view.index_button.invoke(); self.wait(lambda: not self.app.state.loading)
            self.app.view.goal.insert('1.0', 'improve run'); self.window.update()
            self.app.view.plan_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertEqual('completed', self.app.state.plan_result['status'])
        self.app.view.selected_plan.set(self.app.state.plan_result['run_id'])
        self.app.view.candidate_path.set(str(self.candidate))

    def test_windows_public_phase67_smoke_and_backend_body_remains_authoritative(self):
        before = self.snapshot()[:4]
        self.plan()
        self.app.view.candidate_validate.invoke(); self.wait(lambda: not self.app.state.loading)
        result = self.app.state.candidate_result
        self.assertEqual('draft', result['status'])
        self.assertIn(result['patch_id'], self.app.view.candidate_details.get('1.0', 'end'))
        self.assertIn(result['run_id'], self.app.view.candidate_details.get('1.0', 'end'))
        self.assertEqual(result['patch_text'], self.app.view.diff_view.text.get('1.0', 'end-1c'))
        details = self.app.view.candidate_details.get('1.0', 'end')
        self.assertIn('Allowed by Phase 66 / Phase 67 evidence', details)
        self.assertIn('Actually present in validated candidate', details)
        self.assertIn('qualified_symbol', details)
        self.assertIn('Display-only patch SHA-256', details)
        self.assertFalse(result['tests_executed'])
        after = self.snapshot()
        self.candidate.write_text('changed external input')
        self.app.view.render(self.app.state)
        self.assertEqual(self.text, self.app.view.diff_view.stored_text)
        self.assertEqual(after, self.snapshot())
        self.assertEqual(before, self.snapshot()[:4])
        self.assertTrue(self.app.view.raw_detail_button.winfo_exists())
        self.app.view.notebook.select(self.app.view.plan)
        self.app.view.review_tabs.select(self.app.view.candidate_frame)
        self.window.deiconify(); self.window.update(); self.assertTrue(self.window.winfo_viewable())
        self.assertGreater(self.app.view.diff_view.text.winfo_height(), 30)

    def test_chooser_no_validation_and_candidate_change_invalidates(self):
        self.plan()
        with patch('src.ui.views.filedialog.askopenfilename', return_value=str(self.candidate)), patch.object(self.service, 'import_candidate') as call:
            self.app.view.candidate_browse.invoke()
            call.assert_not_called()
        self.app.state.candidate_result = {'status': 'draft', 'patch_text': self.text}
        self.app.view.candidate_path.set(str(self.root / 'other.diff'))
        self.assertIsNone(self.app.state.candidate_result)
        self.assertEqual('', self.app.view.diff_view.stored_text)

    def test_blocked_and_exception_clear_accepted_diff_without_fake_ids(self):
        self.plan()
        for response in ({'status': 'draft', 'patch_text': self.text, 'patch_id': 'patch-real', 'run_id': 'run-real'},
                         {'status': 'blocked', 'patch_text': '', 'patch_id': 'patch-blocked', 'run_id': 'run-blocked', 'unresolved_evidence': [{'type': 'manual_review'}]}):
            with patch.object(self.service, 'import_candidate', return_value=response):
                self.app.view.candidate_validate.invoke(); self.wait(lambda: not self.app.state.loading)
            self.assertEqual(response['patch_text'], self.app.view.diff_view.stored_text)
            with patch.object(self.app.view, '_render_candidate', side_effect=ValueError('render failure')):
                self.app.view.render(self.app.state)
            self.assertIs(response, self.app.state.candidate_result)
            self.assertEqual(response['patch_text'], self.app.view.diff_view.stored_text)
            self.app.view.render(self.app.state)
        self.assertIn('blocked', self.app.view.candidate_status.get())
        self.assertNotIn('patch-real', self.app.view.candidate_details.get('1.0', 'end'))
        with patch.object(self.service, 'import_candidate', side_effect=ValueError('exact refusal')):
            self.app.view.candidate_validate.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIn('exact refusal', self.app.view.candidate_status.get())
        self.assertIsNone(self.app.state.candidate_result)
        self.assertEqual('', self.app.view.candidate_details.get('1.0', 'end-1c'))

    def test_one_worker_pending_close_and_no_application_controls(self):
        self.plan(); started, release, tick = Event(), Event(), Event()
        def buttons(widget):
            return ([str(widget.cget('text'))] if widget.winfo_class() == 'TButton' else []) + [label for child in widget.winfo_children() for label in buttons(child)]
        labels = ' '.join(buttons(self.app.view.notebook)).lower()
        self.assertIn('approve', labels)
        self.assertIn('reject', labels)
        for forbidden in ('apply', 'verify', 'evaluate', 'rollback'):
            self.assertNotIn(forbidden, labels)
        self.addCleanup(release.set)
        original_render, main_thread = self.app.view.render, get_ident()
        def render(state):
            self.assertEqual(main_thread, get_ident())
            original_render(state)
        def run(*args, **kwargs):
            started.set(); release.wait(5); return {'status': 'blocked', 'patch_text': ''}
        with patch.object(self.service, 'import_candidate', side_effect=run) as call, patch.object(self.app.view, 'render', side_effect=render):
            self.app.view.candidate_validate.invoke(); self.wait(started.is_set)
            self.app.start_operation('import_candidate'); call.assert_called_once()
            self.app.request_close(); self.window.after(5, tick.set); self.wait(tick.is_set)
            self.assertFalse(self.app.closed)
            self.assertEqual('disabled', str(self.app.view.candidate_validate.cget('state')))
            release.set(); self.wait(lambda: self.app.closed)

    def test_stale_worker_result_cannot_replace_changed_candidate(self):
        self.plan(); started, release = Event(), Event()
        self.addCleanup(release.set)
        def run(*args, **kwargs):
            started.set(); release.wait(5)
            return {'status': 'draft', 'patch_text': self.text, 'patch_id': 'old-patch'}
        with patch.object(self.service, 'import_candidate', side_effect=run):
            self.app.view.candidate_validate.invoke(); self.wait(started.is_set)
            self.app.view.candidate_path.set(str(self.root / 'new.diff'))
            release.set(); self.wait(lambda: not self.app.state.loading)
        self.assertIsNone(self.app.state.candidate_result)
        self.assertEqual('', self.app.view.diff_view.stored_text)

    def test_goal_tests_plan_and_session_changes_invalidate(self):
        self.plan()
        plan = self.app.state.plan_result
        for change in ('goal', 'tests', 'plan', 'repository', 'workspace'):
            self.app.state.plan_result = plan
            self.app.state.selected_plan_run_id = plan['run_id']
            self.app.state.goal = 'improve run'
            self.app.state.selected_tests = ()
            self.app.state.candidate_result = {'status': 'draft'}
            if change == 'goal': self.app.state.planning_inputs('other', ())
            elif change == 'tests': self.app.state.planning_inputs('other', ('different-test',))
            elif change == 'plan': self.app.state.candidate_inputs(str(self.candidate), '')
            elif change == 'repository': self.app.state.select('other', self.app.state.workspace)
            else: self.app.state.select(self.app.state.repository, 'other-workspace')
            self.assertIsNone(self.app.state.candidate_result)
