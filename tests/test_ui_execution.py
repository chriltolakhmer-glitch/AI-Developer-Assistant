"""Exact Slice 6 call boundaries and display-state chaining."""

import unittest
from unittest.mock import patch

from src.ui.service import RepositoryService
from src.ui.state import ViewState


class ServiceBoundaryTests(unittest.TestCase):
    def test_public_contracts_receive_exact_runs_without_chaining(self):
        service = RepositoryService.__new__(RepositoryService)
        workspace = object()
        service._workspace = lambda path: workspace
        calls = (
            ('src.developer.patch_application.apply_approved_patch', lambda: service.apply('repo', 'work', 'auth-run'), ('auth-run',)),
            ('src.developer.test_execution.execute_applied_patch_tests', lambda: service.test('repo', 'work', 'execution-run'), ('execution-run',)),
            ('src.developer.execution_verification.verify_execution', lambda: service.verify('repo', 'work', 'execution-run', 'observation-run'), ('execution-run', 'observation-run')),
            ('src.developer.recovery_evaluation.evaluate_recovery', lambda: service.evaluate('repo', 'work', 'verification-run'), ('verification-run',)),
        )
        for target, invoke, run_ids in calls:
            with self.subTest(target=target), patch(target, return_value={'run_id': 'returned'}) as backend:
                self.assertEqual({'run_id': 'returned'}, invoke())
                arguments = backend.call_args.args
                self.assertIs(workspace, arguments[0])
                self.assertEqual('repo', str(arguments[1]))
                self.assertEqual(run_ids, arguments[2:])
                if 'test_execution' in target:
                    self.assertEqual((), backend.call_args.kwargs['tests'])


class ExecutionStateTests(unittest.TestCase):
    def setUp(self):
        self.state = ViewState(repository='repo', workspace='work', facts={'branch': 'main'})
        self.state.decision_result = {'run_id': 'auth-run', 'decision': 'approve',
            'execution_authorized': True, 'allowed_operation': 'apply_exact_patch', 'executed': False}

    def test_each_phase_needs_exact_selection_and_separate_action(self):
        state = self.state
        self.assertIsNone(state.begin_operation('apply', 'repo', 'work'))
        state.select_execution_input('authorization', 'auth-run')
        self.assertIsNone(state.begin_operation('apply', 'repo', 'work'))
        state.pending_apply = (state.generation, 'repo', 'work', 'auth-run')
        request = state.begin_operation('apply', 'repo', 'work')
        self.assertEqual('auth-run', request.authorization_run_id)
        self.assertIsNone(state.begin_operation('test', 'repo', 'work'))
        state.complete(request, {'run_id': 'exec-run', 'status': 'applied'}, None)
        self.assertEqual('auth-run', state.applied_authorization_run_id)
        self.assertEqual('', state.selected_execution_run_id)
        state.select_execution_input('execution', 'exec-run')
        request = state.begin_operation('test', 'repo', 'work')
        self.assertEqual('exec-run', request.execution_run_id)
        state.complete(request, {'run_id': 'obs-run', 'status': 'failed'}, None)
        state.select_execution_input('observation', 'obs-run')
        request = state.begin_operation('verify', 'repo', 'work')
        self.assertEqual(('exec-run', 'obs-run'), (request.execution_run_id, request.observation_run_id))
        state.complete(request, {'run_id': 'verify-run', 'status': 'not_verified'}, None)
        state.select_execution_input('verification', 'verify-run')
        request = state.begin_operation('evaluate', 'repo', 'work')
        self.assertEqual('verify-run', request.verification_run_id)
        state.complete(request, {'run_id': 'recovery-run', 'classification': 'failed_tests'}, None)
        self.assertEqual('failed_tests', state.evaluation_result['classification'])

    def test_deselecting_applied_result_does_not_encourage_replay(self):
        state = self.state
        state.select_execution_input('authorization', 'auth-run')
        state.pending_apply = (state.generation, 'repo', 'work', 'auth-run')
        request = state.begin_operation('apply', 'repo', 'work')
        state.complete(request, {'run_id': 'exec-run', 'status': 'applied'}, None)
        state.select_execution_input('authorization', '')
        state.select_execution_input('authorization', 'auth-run')
        state.pending_apply = (state.generation, 'repo', 'work', 'auth-run')
        self.assertIsNone(state.begin_operation('apply', 'repo', 'work'))

    def test_change_invalidates_and_stale_completion_cannot_restore_chain(self):
        state = self.state
        state.select_execution_input('authorization', 'auth-run')
        state.pending_apply = (state.generation, 'repo', 'work', 'auth-run')
        request = state.begin_operation('apply', 'repo', 'work')
        state.select('other', 'work')
        self.assertFalse(state.complete(request, {'run_id': 'stale', 'status': 'applied'}, None))
        self.assertIsNone(state.application_result)


if __name__ == '__main__':
    unittest.main()
