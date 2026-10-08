"""Real Tk confirmation/rejection flows with disposable Phase 65-68 evidence."""
import tkinter as tk
import json
from threading import Event, get_ident
from unittest.mock import patch

from src.ui.app import Application
from tests import test_ui_candidate_widgets as candidate_widgets
from tests import test_ui_decisions as fixtures


class DecisionWidgetFixture(fixtures.DecisionFixture):
    wait = candidate_widgets.CandidateWidgetTests.wait
    close = candidate_widgets.CandidateWidgetTests.close
    plan = candidate_widgets.CandidateWidgetTests.plan

    def setUp(self):
        super().setUp()
        self.window = tk.Tk(); self.window.withdraw()
        self.app = Application(self.window, self.service, self.workspace_path)
        self.addCleanup(self.close)
        self.app.view.repository.set(str(self.repo))
        self.app.view.open_button.invoke(); self.wait(lambda: not self.app.state.loading)

    def draft(self):
        self.plan()
        self.app.view.candidate_validate.invoke(); self.wait(lambda: not self.app.state.loading)
        draft = self.app.state.candidate_result
        self.assertEqual('draft', draft['status'])
        self.app.view.selected_patch.set(draft['run_id'])
        return draft

    def confirmation(self):
        self.app.view.approve_button.invoke()
        self.wait(lambda: not self.app.state.loading)
        self.assertIsNotNone(self.app.view.confirmation)
        return self.app.state.pending_approval


class DecisionWidgetTests(DecisionWidgetFixture):
    def test_windows_public_approval_smoke_canonical_review_cancel_then_confirm_once(self):
        target = self.snapshot()[:4]
        draft = self.draft()
        self.app.view.review_note.set('Reviewed exact diff.')
        self.app.view.review_button.invoke(); self.wait(lambda: not self.app.state.loading)
        review = self.app.state.review_result
        self.assertEqual(draft, review['draft'])
        self.assertEqual(self.text, self.app.view.diff_view.stored_text)
        self.assertIn('Canonical patch review digest', self.app.view.candidate_details.get('1.0', 'end'))
        before = self.snapshot()
        with patch.object(self.service, 'decide', wraps=self.service.decide) as call:
            context = self.confirmation()
            call.assert_not_called()
            self.assertEqual(before, self.snapshot())
            text = self.app.view.confirmation_details.get('1.0', 'end')
            for value in (draft['patch_id'], draft['run_id'], draft['source_plan_run_id'], draft['source_action_id'],
                          draft['current_commit'], review['patch_sha256'], json.dumps(str(self.repo.resolve())), 'local-developer',
                          'Reviewed exact diff.', 'qualified_symbol', 'allowed_symbol_scope', 'candidate_symbol_scope'):
                self.assertIn(value, text)
            for identity in review['bound_tests']: self.assertIn(identity, text)
            self.assertEqual('', self.app.view.confirmation.bind('<Return>'))
            self.assertEqual('', self.window.bind('<Return>'))
            for widget in (self.app.view.candidate_entry, self.app.view.plan_selector, self.app.view.patch_selector,
                           self.app.view.repository_entry, self.app.view.audit_entry):
                self.assertEqual('disabled', str(widget.cget('state')))
            self.app.view.cancel_button.invoke()
            self.assertIsNone(self.app.view.confirmation)
            self.assertIsNone(self.app.state.pending_approval)
            self.assertEqual(before, self.snapshot())
            self.assertEqual(self.text, self.app.view.diff_view.stored_text)
            context = self.confirmation()
            self.app.view.confirm_button.invoke()
            self.app.confirm_approval(context)
            self.wait(lambda: not self.app.state.loading)
            call.assert_called_once()
        result = self.app.state.decision_result
        self.assertEqual('approve', result['decision'])
        self.assertTrue(result['execution_authorized'])
        self.assertEqual('apply_exact_patch', result['allowed_operation'])
        self.assertFalse(result['executed']); self.assertFalse(result['tests_executed'])
        self.assertFalse(result['source_mutation_performed'])
        self.assertEqual(target, self.snapshot()[:4])
        details = self.app.view.decision_details.get('1.0', 'end')
        for key, value in result.items():
            self.assertIn(key + ':', details)
        self.assertIn(result['authorization_id'], details)
        self.assertIn(result['run_id'], details)
        self.assertIn('NOT APPLIED', self.app.view.decision_status.get())
        with patch.object(self.app.view, '_render_decision', side_effect=ValueError('presentation only')):
            self.app.view.render(self.app.state)
        self.assertIs(result, self.app.state.decision_result)
        self.assertIn(result['authorization_id'], self.app.view.decision_details.get('1.0', 'end'))
        self.app.view.render(self.app.state)
        self.assertEqual('disabled', str(self.app.view.approve_button.cget('state')))
        self.assertEqual('disabled', str(self.app.view.reject_button.cget('state')))

    def test_reject_is_direct_preserves_note_diff_and_target_and_blocked_support(self):
        draft = self.draft()
        self.app.view.review_note.set('Rejected with a note.')
        before = self.snapshot()[:4]
        self.app.view.reject_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIsNone(self.app.view.confirmation)
        result = self.app.state.decision_result
        self.assertEqual('reject', result['decision'])
        self.assertEqual('Rejected with a note.', result['note'])
        self.assertFalse(result['execution_authorized']); self.assertEqual('none', result['allowed_operation'])
        self.assertIn('NO EXECUTION AUTHORITY', self.app.view.decision_status.get())
        self.assertEqual(self.text, self.app.view.diff_view.stored_text)
        self.assertEqual(before, self.snapshot()[:4])
        blocked = self.blocked()
        self.app.state.clear_candidate(); self.app.state.candidate_result = blocked
        self.app.view.render(self.app.state); self.app.view.selected_patch.set(blocked['run_id'])
        self.assertEqual('disabled', str(self.app.view.approve_button.cget('state')))
        self.app.view.review_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIn('Unavailable', self.app.view.decision_details.get('1.0', 'end'))
        self.assertIn('Linked plan evidence: Unavailable', self.app.view.decision_details.get('1.0', 'end'))
        self.app.view.reject_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertEqual(blocked['patch_id'], self.app.state.decision_result['source_patch_id'])
        self.assertEqual('reject', self.app.state.decision_result['decision'])
        self.assertIsNone(self.app.view.confirmation)

    def test_missing_corrupt_and_blocked_never_confirm_or_fabricate_decision(self):
        draft = self.draft()
        record = self.workspace_path / 'runs' / draft['run_id'] / 'results.json'
        record.write_bytes(b'{')
        before = self.snapshot()
        self.app.view.approve_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIn('missing or malformed', self.app.view.decision_status.get())
        self.assertIsNone(self.app.view.confirmation)
        self.assertIsNone(self.app.state.review_result)
        self.assertEqual('', self.app.view.diff_view.stored_text)
        self.app.view.reject_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIsNone(self.app.state.decision_result)
        self.assertIn('persistence outcome is unconfirmed', self.app.view.decision_status.get())
        self.assertEqual(before, self.snapshot())
        blocked = self.blocked()
        self.app.state.clear_candidate(); self.app.state.candidate_result = blocked
        self.app.view.render(self.app.state); self.app.view.selected_patch.set(blocked['run_id'])
        self.app.start_operation('review_approval'); self.wait(lambda: not self.app.state.loading)
        self.assertIsNone(self.app.view.confirmation)
        self.assertIn('Blocked PatchDraft', self.app.view.decision_status.get())

    def test_selection_or_audit_change_dismisses_pending_confirmation(self):
        self.draft()
        before = self.snapshot()
        context = self.confirmation()
        self.app.view.audit_label.set('changed label')
        self.assertIsNone(self.app.view.confirmation)
        self.app.confirm_approval(context)
        self.assertIsNone(self.app.state.decision_result)
        context = self.confirmation()
        self.app.view.candidate_path.set(str(self.root / 'another.diff'))
        self.assertIsNone(self.app.view.confirmation)
        self.assertIsNone(self.app.state.review_result)
        self.app.confirm_approval(context)
        self.assertEqual(before, self.snapshot())

    def test_final_backend_reloads_after_confirmation_source_and_patch_tamper_refused(self):
        draft = self.draft()
        context = self.confirmation()
        (self.repo / 'app.py').write_text('def run():\n    return 9\n')
        before = self.snapshot()
        self.app.view.confirm_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIsNone(self.app.state.decision_result)
        self.assertIn('Repository state differs', self.app.view.decision_status.get())
        self.assertEqual(before, self.snapshot())
        (self.repo / 'app.py').write_text('def run():\n    return 1\n')
        self.app.view.review_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.confirmation()
        self.tamper(draft, 'results.json', lambda v: v.update(patch_text=self.text.replace('return 2', 'return 3')))
        before = self.snapshot()
        self.app.view.confirm_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIsNone(self.app.state.decision_result)
        self.assertIn('modified', self.app.view.decision_status.get())
        self.assertEqual(before, self.snapshot())

    def test_same_head_branch_switch_before_review_or_confirm_stops_approval(self):
        self.draft(); self.git('switch', '-qc', 'same-head')
        before = self.snapshot()
        self.app.view.approve_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIsNone(self.app.view.confirmation)
        self.assertIn('branch context changed', self.app.view.decision_status.get())
        self.assertEqual(before, self.snapshot())
        self.git('switch', '-q', 'main')
        self.confirmation(); self.git('switch', '-q', 'same-head')
        before = self.snapshot()
        self.app.view.confirm_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIsNone(self.app.view.confirmation)
        self.assertIsNone(self.app.state.decision_result)
        self.assertIn('branch context changed', self.app.view.decision_status.get())
        self.assertEqual(before, self.snapshot())

    def test_stale_review_main_thread_and_pending_close_remain_responsive(self):
        draft = self.draft()
        review = self.review(draft)
        started, release, tick = Event(), Event(), Event()
        self.addCleanup(release.set)
        def run(*args, **kwargs):
            started.set(); release.wait(5); return review
        main = get_ident(); original_render = self.app.view.render
        def render(state):
            self.assertEqual(main, get_ident()); original_render(state)
        with patch.object(self.service, 'review_patch', side_effect=run) as call, patch.object(self.app.view, 'render', side_effect=render):
            self.app.view.approve_button.invoke(); self.wait(started.is_set)
            self.app.start_operation('review_approval'); call.assert_called_once()
            self.app.view.selected_patch.set('')
            release.set(); self.wait(lambda: not self.app.state.loading)
        self.assertIsNone(self.app.state.review_result)
        self.assertIsNone(self.app.view.confirmation)
        self.app.view.selected_patch.set(draft['run_id'])
        started.clear(); release.clear()
        with patch.object(self.service, 'review_patch', side_effect=run):
            self.app.view.approve_button.invoke(); self.wait(started.is_set)
            self.app.request_close(); self.window.after(5, tick.set); self.wait(tick.is_set)
            self.assertFalse(self.app.closed)
            release.set(); self.wait(lambda: self.app.closed)

    def test_decision_worker_error_duplicate_and_pending_close_no_fake_authority(self):
        self.draft(); self.confirmation()
        started, release, tick = Event(), Event(), Event()
        self.addCleanup(release.set)
        def fail(*args, **kwargs):
            started.set(); release.wait(5); raise ValueError('exact decision failure')
        with patch.object(self.service, 'decide', side_effect=fail) as call:
            context = self.app.state.pending_approval
            self.app.view.confirm_button.invoke(); self.wait(started.is_set)
            self.app.confirm_approval(context); call.assert_called_once()
            self.app.request_close(); self.window.after(5, tick.set); self.wait(tick.is_set)
            self.assertFalse(self.app.closed)
            release.set(); self.wait(lambda: self.app.closed)
        self.assertIsNone(self.app.state.decision_result)
        self.assertIn('exact decision failure', self.app.state.decision_error)
