"""Slice 2 contract routing, presentation invalidation, and real backend boundaries."""
from dataclasses import replace, fields
from pathlib import Path
import json
from unittest.mock import patch, Mock

from src.config import load_config
from src.developer.local_workflow import DeveloperWorkspace, LocalWorkflowError
from src.ui.service import RepositoryService
from src.ui.state import ViewState
from tests.ui_fixture import GitFixture
from tests.test_implementation_planning import _Model


class UIWorkflowTests(GitFixture):
    def run_commands(self):
        return [json.loads(path.read_text())['command'] for path in self.workspace_path.rglob('metadata.json')
                if path.parent.parent.name == 'runs']
    def setUp(self):
        super().setUp()
        (self.repo / 'tests').mkdir()
        (self.repo / 'tests' / 'test_app.py').write_text(
            'import unittest\nfrom app import run\nclass RunTests(unittest.TestCase):\n'
            '    def test_run(self):\n        open("test-executed", "w").write("executed")\n        self.assertEqual(1, run())\n', encoding='utf-8')
        self.git('add', '--all')
        self.git('commit', '-qm', 'existing test fixture')
        self.service = RepositoryService(replace(load_config(environ={}), developer_workspace=self.workspace_path))
        self.args = (str(self.repo), str(self.workspace_path))
        self.identity = 'tests.test_app.RunTests.test_run'

    def test_exact_public_contract_routing_and_no_later_api(self):
        with patch.object(DeveloperWorkspace, 'scan', return_value={'scan': 'result'}) as scan, \
                patch.object(DeveloperWorkspace, 'index', return_value={'index': 'result'}) as index, \
                patch('src.developer.implementation_planning.plan_change', return_value={'status': 'limited'}) as plan:
            self.assertEqual({'scan': 'result'}, self.service.scan(*self.args))
            self.assertEqual({'index': 'result'}, self.service.index(*self.args))
            goal = '  exact\n goal  '
            self.assertEqual({'status': 'limited'}, self.service.plan(*self.args, goal=goal, expected_tests=(self.identity,)))
            scan.assert_called_once_with(self.repo)
            index.assert_called_once_with(self.repo)
            developer, repo = plan.call_args.args
            self.assertEqual(self.workspace_path.resolve(), developer.root)
            self.assertEqual(self.repo, repo)
            self.assertEqual(dict(goal=goal, top_k=10, expected_tests=(self.identity,)), plan.call_args.kwargs)
        self.assertEqual({'read_repository', 'scan', 'index', 'catalog_tests', 'plan'},
                         {name for name, value in RepositoryService.__dict__.items() if not name.startswith('_') and callable(value)})

    def test_catalog_is_exact_read_only_and_imports_no_target_tests(self):
        before = self.snapshot()
        with patch.object(DeveloperWorkspace, '_prepare', side_effect=AssertionError('prepare')):
            self.assertEqual({'tests.test_app': [self.identity]}, self.service.catalog_tests(*self.args))
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.workspace_path.exists())
        self.assertFalse((self.repo / 'test-executed').exists())

    def test_real_scan_writes_only_external_run_after_explicit_call(self):
        before = self.snapshot()
        self.service.read_repository(*self.args)
        self.service.read_repository(*self.args)
        self.assertEqual(before, self.snapshot())
        with patch.object(DeveloperWorkspace, 'index', side_effect=AssertionError('automatic index')), \
                patch('src.developer.implementation_planning.plan_change', side_effect=AssertionError('automatic plan')):
            result = self.service.scan(*self.args)
        self.assertEqual('completed', result['status'])
        self.assertTrue(result['run_id'])
        self.assertEqual(before[:4], self.snapshot()[:4])
        self.assertEqual(['scan'], self.run_commands())
        self.assertTrue((self.workspace_path / 'runs' / result['run_id'] / 'results.json').is_file())
        self.assertFalse(list(self.workspace_path.rglob('active.json')))

    def test_real_index_and_plan_preserve_target_and_create_exact_external_evidence(self):
        before = self.snapshot()[:4]
        with patch('src.developer.local_workflow.load_model', return_value=_Model()) as model:
            indexed = self.service.index(*self.args)
            self.assertEqual('completed', indexed['status'])
            self.assertTrue(indexed['run_id'])
            self.assertTrue(list(self.workspace_path.rglob('active.json')))
            self.assertEqual(before, self.snapshot()[:4])
            result = self.service.plan(*self.args, goal='  improve\n run  ', expected_tests=(self.identity,))
            self.assertIn(result['status'], ('completed', 'limited', 'manual_review_required'))
            self.assertEqual('improve run', result['goal'])
            self.assertEqual([self.identity], result['tests']['selected_tests'])
            self.assertTrue(result['proposed_action']['action_id'])
            self.assertTrue(result['run_id'])
            self.assertFalse(result['tests_executed'])
            self.assertFalse(result['source_changes_made'])
            self.assertEqual('current', result['change_impact']['index_freshness']['status'])
        self.assertEqual(before, self.snapshot()[:4])
        self.assertFalse((self.repo / 'test-executed').exists())
        self.assertIn('plan-change', self.run_commands())
        self.assertTrue((self.workspace_path / 'runs' / result['run_id'] / 'results.json').is_file())
        self.assertEqual({'index', 'query', 'inspect', 'change-impact', 'plan-change'}, set(self.run_commands()))

    def test_missing_model_preserves_actionable_backend_error_no_fake_index(self):
        before = self.snapshot()[:4]
        with patch('src.developer.local_workflow.load_model', side_effect=ValueError('pinned cache unavailable')):
            with self.assertRaisesRegex(LocalWorkflowError, 'Could not index with the pinned local model: pinned cache unavailable'):
                self.service.index(*self.args)
        self.assertEqual(before, self.snapshot()[:4])
        self.assertFalse(list(self.workspace_path.rglob('active.json')))
        self.assertEqual('missing', self.service.read_repository(*self.args)['index_freshness']['status'])

    def test_real_plan_without_scan_or_index_retains_status_and_unknown_test_refusal(self):
        before = self.snapshot()[:4]
        with patch('src.developer.local_workflow.load_model', return_value=_Model()):
            result = self.service.plan(*self.args, goal='improve run')
        self.assertIn(result['status'], ('limited', 'manual_review_required'))
        self.assertEqual('missing', result['change_impact']['index_freshness']['status'])
        self.assertNotIn('scan', self.run_commands())
        self.assertFalse(list(self.workspace_path.rglob('active.json')))
        with patch('src.developer.local_workflow.load_model', return_value=_Model()), \
                self.assertRaisesRegex(LocalWorkflowError, 'exact existing unittest'):
            self.service.plan(*self.args, goal='run', expected_tests=('invented.command',))
        self.assertEqual(before, self.snapshot()[:4])

    def test_blank_goal_backend_refuses_without_writing(self):
        with self.assertRaisesRegex(LocalWorkflowError, 'nonempty'):
            self.service.plan(*self.args, goal=' \n ')
        self.assertFalse(self.workspace_path.exists())

    def test_presentation_invalidates_plan_on_all_input_changes_and_has_no_authority(self):
        state = ViewState(repository=self.args[0], workspace=self.args[1], facts={'display': 'loaded'})
        state.planning_inputs('goal', (self.identity,))
        for operation in ('scan', 'index', 'catalog_tests', 'plan'):
            request = state.begin_operation(operation, *self.args)
            self.assertEqual(operation, request.operation)
            self.assertIsNone(state.begin_operation(operation, *self.args))
            state.complete(request, {'status': 'limited'}, None)
        for change in ('goal', 'tests', 'repository', 'workspace'):
            state.plan_result = {'run_id': 'old'}
            if change == 'goal': state.planning_inputs('new goal', state.selected_tests)
            elif change == 'tests': state.planning_inputs(state.goal, ())
            elif change == 'repository': state.select('other', state.workspace)
            else: state.select(state.repository, 'other-workspace')
            self.assertIsNone(state.plan_result)
        self.assertFalse({'approved', 'authorized', 'applied', 'tests_passed', 'verified', 'plan_ready'} & {f.name for f in fields(state)})

    def test_stale_operation_completion_never_overwrites_new_session(self):
        for operation in ('scan', 'index', 'catalog_tests', 'plan'):
            state = ViewState(repository=self.args[0], workspace=self.args[1], facts={'loaded': True}, goal='goal')
            request = state.begin_operation(operation, *self.args)
            state.select('new-repository', self.args[1])
            self.assertFalse(state.complete(request, {'run_id': 'old'}, None))
            self.assertFalse(state.loading)
            self.assertIsNone(state.plan_result)
            self.assertIsNone(state.scan_result)
            self.assertIsNone(state.index_result)
            self.assertIsNone(state.test_catalog)

    def test_blank_goal_ui_state_refuses_backend_request(self):
        state = ViewState(repository=self.args[0], workspace=self.args[1], facts={'loaded': True})
        self.assertIsNone(state.begin_operation('plan', *self.args))
        self.assertIn('nonempty', state.error)
