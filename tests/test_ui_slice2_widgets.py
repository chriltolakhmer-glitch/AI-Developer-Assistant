"""Real Tk Slice 2 actions, result labels, serialization and responsive close."""
from dataclasses import replace
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
from tests.test_implementation_planning import _Model


class UISlice2WidgetTests(GitFixture):
    def setUp(self):
        super().setUp()
        (self.repo/'tests').mkdir()
        (self.repo/'tests'/'test_app.py').write_text('import unittest\nfrom app import run\nclass RunTests(unittest.TestCase):\n    def test_run(self):\n        self.assertEqual(1, run())\n', encoding='utf-8')
        self.git('add', '--all'); self.git('commit', '-qm', 'regression fixture')
        if tk is None: self.skipTest('Tkinter unavailable')
        try: self.window = tk.Tk()
        except tk.TclError as error: self.skipTest(f'Cannot initialize Tk: {error}')
        from src.ui.app import Application
        self.app = Application(self.window, RepositoryService(replace(load_config(environ={}), developer_workspace=self.workspace_path)), self.workspace_path)
        self.window.withdraw()
        self.addCleanup(self.close)
        self.identity = 'tests.test_app.RunTests.test_run'

    def wait(self, predicate):
        deadline = time.monotonic()+15
        while not predicate() and time.monotonic()<deadline:
            if not self.app.closed: self.window.update()
            time.sleep(.005)
        self.assertTrue(predicate(), 'Tk operation did not finish')

    def close(self):
        if not self.app.closed:
            self.app.request_close(); self.wait(lambda: self.app.closed)

    def open(self):
        self.app.view.repository.set(str(self.repo))
        self.app.view.open_button.invoke()
        self.wait(lambda: not self.app.state.loading)
        self.assertIsNone(self.app.state.error)

    def goal(self, text='improve run'):
        self.app.view.goal.delete('1.0', 'end')
        self.app.view.goal.insert('1.0', text)
        self.window.update()

    def plan_payload(self, status='completed'):
        return dict(status=status, run_id='exact-plan-run', goal='goal',
                    repository={'repository_id': 'exact-repository'},
                    proposed_action={'action_id': 'exact-action', 'status': 'proposed',
                                     'action_type': 'implementation_plan', 'repository_id': 'exact-repository',
                                     'target_paths': ['app.py'], 'target_symbols': ['run'],
                                     'unresolved_evidence': [{'type': 'human_check'}],
                                     'execution_allowed': False, 'authority_required': 'human_approval_required'},
                    implementation_targets=[{'role': 'primary_target', 'file_path': 'app.py',
                                              'qualified_symbol': 'run', 'reasons': ['goal evidence']},
                                             {'role': 'configuration_target', 'file_path': 'config.py',
                                              'qualified_symbol': 'load', 'reasons': ['configuration evidence']},
                                             {'role': 'related_context', 'file_path': 'helper.py',
                                              'qualified_symbol': 'help', 'reasons': ['related evidence']}],
                    tests={'selected_tests': [self.identity], 'expected_test_selection': {
                        'status': 'known', 'confidence': 'developer_selected',
                        'evidence': [{'test': self.identity, 'source': 'explicit_developer_selection'}],
                        'uncertainty': ['Runtime coverage requires human review.']}},
                    preserved_behavior=[{'kind': 'static_dependency', 'statement': 'keep the public return value'}],
                    implementation_steps=[{'order': 1, 'action': 'inspect target', 'target_refs': ['app.py::run']}],
                    recommended_validation=[{'order': 1, 'selector': self.identity, 'scope': 'focused',
                                             'reason': 'bound regression'}],
                    limitations=['Dynamic behavior requires human validation.'],
                    unresolved_evidence=[{'type': 'human_check', 'reason': 'inspect runtime behavior'}],
                    warnings=[{'type': 'visible_warning', 'classification': 'non_blocking',
                        'evidence': {'file_path': 'tests/test_app.py', 'qualified_name': 'RunTests',
                                     'reason': 'over_limit', 'token_count': 300},
                        'basis': {'kind': 'exact_retained_leaf_evidence',
                            'container': {'file_path': 'tests/test_app.py', 'qualified_symbol': 'RunTests'},
                            'proofs': [{'kind': 'exact_retained_test_leaf', 'chunk_id': 'exact-chunk',
                                'file_path': 'tests/test_app.py', 'qualified_symbol': 'RunTests.test_run',
                                'target_role': 'test_target', 'content_sha256': 'exact-content-hash',
                                'test_identity': self.identity,
                                'expected_test_binding_source': 'explicit_developer_selection'}]},
                        'action': 'backend retained exact leaf'}],
                    change_impact={'repository': {'repository_id': 'exact-repository',
                                                   'current_commit': 'exact-commit',
                                                   'working_tree_sha256': 'exact-snapshot'},
                                   'index_freshness': {'status': 'current'}})

    def scan_payload(self):
        facts = self.app.state.facts
        repo = dict(repository_id=facts['repository_id'], commit_sha=facts['head'], working_tree_sha256=facts['working_tree_sha256'], tracked_file_count=2, eligible_python_file_count=2)
        return dict(status='completed', run_id='exact-scan-run', scan=repo)

    def index_payload(self):
        return dict(status='completed', run_id='exact-index-run', repository=self.scan_payload()['scan'], index_status='indexed', index_path='external/index', indexed_chunk_count=3)

    def test_open_refresh_scan_index_and_plan_are_separate_explicit_real_actions(self):
        before = self.snapshot()[:4]
        with patch.object(self.app.service, 'scan', wraps=self.app.service.scan) as scan, \
                patch.object(self.app.service, 'index', wraps=self.app.service.index) as index, \
                patch.object(self.app.service, 'plan', wraps=self.app.service.plan) as plan, \
                patch('src.developer.local_workflow.load_model', return_value=_Model()):
            self.open()
            self.app.view.refresh_button.invoke(); self.wait(lambda: not self.app.state.loading)
            self.assertFalse(self.workspace_path.exists())
            scan.assert_not_called(); index.assert_not_called(); plan.assert_not_called()
            self.app.view.scan_button.invoke(); self.wait(lambda: not self.app.state.loading)
            scan.assert_called_once(); index.assert_not_called(); plan.assert_not_called()
            self.assertIn(self.app.state.scan_result['run_id'], self.app.view.details.get('1.0', 'end'))
            self.assertEqual(before, self.snapshot()[:4])
            self.app.view.index_button.invoke(); self.wait(lambda: not self.app.state.loading)
            index.assert_called_once(); plan.assert_not_called()
            self.assertIn(self.app.state.index_result['index_status'], self.app.view.details.get('1.0', 'end'))
            self.goal('improve run')
            self.app.view.plan_button.invoke(); self.wait(lambda: not self.app.state.loading)
            plan.assert_called_once_with(str(self.repo.resolve()), str(self.workspace_path.resolve()), goal='improve run', top_k=10, expected_tests=())
            result = self.app.state.plan_result
            self.assertIsNotNone(result)
            self.assertIn(result['run_id'], self.app.view.plan_header.get())
            evidence_snapshot = self.snapshot()
            run_records = sorted(str(path.relative_to(self.workspace_path))
                                 for path in self.workspace_path.rglob('metadata.json'))
            self.app.view.render(self.app.state)
            self.app.view.render(self.app.state)
            self.assertEqual(evidence_snapshot, self.snapshot())
            self.assertEqual(run_records, sorted(str(path.relative_to(self.workspace_path))
                                                 for path in self.workspace_path.rglob('metadata.json')))
        self.assertEqual(before, self.snapshot()[:4])
        self.assertEqual(['Run & Result','History'], [self.app.view.notebook.tab(tab,'text') for tab in self.app.view.notebook.tabs()[2:]])
        self.window.deiconify(); self.window.update()
        self.assertTrue(self.window.winfo_viewable())

    def test_catalog_selection_passes_exact_existing_ids_and_invalidates_plan(self):
        self.open(); before=self.snapshot()
        self.app.view.notebook.select(self.app.view.plan)
        self.window.deiconify(); self.window.update()
        self.app.view.catalog_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertEqual((self.identity,), self.app.view.catalog_ids)
        self.assertEqual(before, self.snapshot())
        self.app.view.tests.selection_set(0)
        self.app.view.tests.event_generate('<<ListboxSelect>>'); self.window.update()
        self.goal()
        with patch.object(self.app.service, 'plan', return_value=self.plan_payload()) as plan:
            self.app.view.plan_button.invoke(); self.wait(lambda: not self.app.state.loading)
            self.assertEqual((self.identity,), plan.call_args.kwargs['expected_tests'])
        self.app.view.tests.selection_clear(0)
        self.app.view.tests.event_generate('<<ListboxSelect>>'); self.window.update()
        self.assertIsNone(self.app.state.plan_result)
        self.assertEqual((), self.app.state.selected_tests)
        self.assertFalse(hasattr(self.app.view, 'test_command'))
        self.app.view.tests.selection_set(0)
        self.app.view.tests.event_generate('<<ListboxSelect>>'); self.window.update()
        self.app.view.workspace.set(str(self.root/'new-workspace'))
        self.assertEqual((), self.app.state.selected_tests)
        self.assertIsNone(self.app.state.test_catalog)

    def test_literal_statuses_ids_blockers_and_warnings_are_preserved(self):
        self.open(); self.goal()
        for status in ('completed', 'limited', 'manual_review_required'):
            payload=self.plan_payload(status)
            with patch.object(self.app.service, 'plan', return_value=payload) as plan:
                self.app.view.plan_button.invoke(); self.wait(lambda: not self.app.state.loading)
                plan.assert_called_once()
            self.assertIs(payload, self.app.state.plan_result)
            text=self.app.view.plan_summary.get('1.0','end')
            self.assertIn('Primary target (primary_target): 1', text)
            self.assertIn('Configuration target (configuration_target): 1', text)
            self.assertIn('Blocking / unresolved evidence', text)
            self.assertIn('Warnings / informational evidence', text)
            self.assertIn('Proposed Action', text)
            self.assertIn('Proposed scope', text)
            self.assertIn('execution_allowed: false', text)
            self.assertNotIn('Approved scope', text)
            self.assertIn('tests.test_app.RunTests.test_run', text)
            self.assertIn('exact_retained_test_leaf', text)
            self.assertIn('exact-content-hash', text)
            self.assertIn('Proposed implementation steps - no source changes have been made.', text)
            self.assertIn('Recommended validation (advisory; not executed)', text)
            self.assertIn('Limitations', text)
            self.assertNotIn('Primary targets: 2', text)
            self.assertIn(f'Plan status: {status}', self.app.view.plan_header.get())
            for exact in ('exact-action',self.identity,'visible_warning','human_check'):
                self.assertIn(exact,text)
            target_ids = self.app.view.target_tree.get_children()
            self.assertEqual(3, len(target_ids))
            self.app.view.target_tree.selection_set(target_ids[1])
            self.app.view.target_tree.event_generate('<<TreeviewSelect>>')
            self.window.update()
            detail = self.app.view.target_detail.get('1.0', 'end')
            self.assertIn('configuration_target', detail)
            self.assertIn('configuration evidence', detail)
            self.assertEqual('Phase 65 run ID: exact-plan-run', self.app.view.plan_header.get().splitlines()[2])
            self.assertIsNone(self.app.state.error)

    def test_slice3_has_no_candidate_or_approval_controls_and_large_evidence_scrolls(self):
        self.open(); self.goal()
        payload = self.plan_payload()
        payload['limitations'] = [f'limitation-{index}-' + ('evidence ' * 40) for index in range(80)]
        with patch.object(self.app.service, 'plan', return_value=payload):
            self.app.view.plan_button.invoke(); self.wait(lambda: not self.app.state.loading)
        text = self.app.view.plan_summary.get('1.0', 'end')
        self.assertIn('limitation-79-', text)
        self.assertEqual('disabled', str(self.app.view.plan_summary.cget('state')))
        names = [child.cget('text') for child in self.app.view.plan.winfo_children()
                 if child.winfo_class() == 'TButton']
        combined = ' '.join(names).casefold()
        for forbidden in ('candidate', 'approve', 'validate patch', 'draft patch', 'execute'):
            self.assertNotIn(forbidden, combined)
        before = self.snapshot()
        self.app.view.raw_detail_button.invoke()
        raw_window = self.app.view.raw_detail_window
        raw_text = next(child for child in raw_window.winfo_children() if isinstance(child, tk.Text))
        self.assertEqual('disabled', str(raw_text.cget('state')))
        self.assertIn('exact_retained_test_leaf', raw_text.get('1.0', 'end'))
        self.assertEqual(before, self.snapshot())
        self.goal('a different plan input')
        self.assertIsNone(self.app.state.plan_result)
        self.assertFalse(raw_window.winfo_exists())

    def test_blank_goal_and_backend_scan_index_plan_errors_are_visible_without_chaining(self):
        self.open()
        with patch.object(self.app.service,'plan') as plan:
            self.app.view.plan_button.invoke(); plan.assert_not_called()
            self.assertIn('nonempty',self.app.view.plan_status.get())
        self.goal()
        for operation in ('scan','index','plan'):
            with patch.object(self.app.service,operation,side_effect=ValueError('exact backend reason')) as action:
                self.app.start_operation(operation); self.wait(lambda:not self.app.state.loading)
                action.assert_called_once()
                self.assertIn('exact backend reason',self.app.view.status.get())
                self.assertIsNone(self.app.state.plan_result)
        self.assertFalse(self.workspace_path.exists())

    def test_goal_repository_and_workspace_edits_invalidate_displayed_plan(self):
        self.open(); self.goal()
        self.app.state.plan_result=self.plan_payload(); self.app.view.render(self.app.state)
        self.goal('changed goal'); self.assertIsNone(self.app.state.plan_result)
        self.app.state.plan_result=self.plan_payload()
        self.app.view.workspace.set(str(self.root/'other-workspace'))
        self.assertIsNone(self.app.state.plan_result)
        self.assertIsNone(self.app.state.facts)
        self.app.state.plan_result=self.plan_payload()
        self.app.view.repository.set(str(self.root/'other-repo'))
        self.assertIsNone(self.app.state.plan_result)
        self.assertFalse((self.root/'other-workspace').exists())

    def busy_close(self, operation):
        self.open(); self.goal()
        payload={'scan':self.scan_payload(),'index':self.index_payload(),'plan':self.plan_payload()}[operation]
        started,release,tick=Event(),Event(),Event()
        self.addCleanup(release.set)
        def run(*args,**kwargs):
            started.set(); release.wait(5); return payload
        actual_render=self.app.view.render; main=get_ident()
        def render(state):
            self.assertEqual(main,get_ident()); actual_render(state)
        with patch.object(self.app.service,operation,side_effect=run) as action, patch.object(self.app.view,'render',side_effect=render):
            self.app.start_operation(operation); self.wait(started.is_set)
            self.assertFalse(self.app.worker.daemon)
            self.app.start_operation(operation)
            action.assert_called_once()
            with patch.object(self.app.worker,'join',side_effect=AssertionError('join')):
                self.app.request_close()
                self.window.after(5,tick.set); self.wait(tick.is_set)
                self.assertFalse(self.app.closed)
                self.assertEqual('disabled',str(self.app.view.plan_button.cget('state')))
                release.set(); self.wait(lambda:self.app.closed)
        self.assertIs(payload,getattr(self.app.state,operation+'_result'))
        action.assert_called_once()

    def test_scan_busy_and_pending_close_remain_responsive(self): self.busy_close('scan')
    def test_index_busy_and_pending_close_remain_responsive(self): self.busy_close('index')
    def test_plan_busy_and_pending_close_remain_responsive(self): self.busy_close('plan')

    def test_stale_worker_cannot_overwrite_changed_session(self):
        self.open(); self.goal()
        started,release=Event(),Event(); self.addCleanup(release.set)
        def run(*args,**kwargs): started.set(); release.wait(5); return self.plan_payload()
        with patch.object(self.app.service,'plan',side_effect=run):
            self.app.start_operation('plan'); self.wait(started.is_set)
            self.app.state.select('other-repository',str(self.workspace_path))
            release.set(); self.wait(lambda:not self.app.state.loading)
        self.assertEqual('other-repository',self.app.state.repository)
        self.assertIsNone(self.app.state.plan_result)
