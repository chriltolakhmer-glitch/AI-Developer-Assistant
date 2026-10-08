"""Real Tk controls require four distinct user requests."""

from unittest.mock import patch
import hashlib

from src.developer.local_workflow import LocalWorkflowError
from tests.test_implementation_planning import _Model

from tests.test_ui_decision_widgets import DecisionWidgetFixture


class ExecutionWidgetTests(DecisionWidgetFixture):
    def test_log_integrity_error_is_visible_without_content(self):
        self.app.state.observation_result = {'run_id': 'selected-observation', 'status': 'passed'}
        self.app.state.selected_observation_run_id = 'selected-observation'
        self.app.view.render(self.app.state)
        with patch.object(self.service, 'read_log', side_effect=LocalWorkflowError('Phase 70 log SHA-256 mismatch')):
            self.app.view.stdout_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIn('SHA-256 mismatch', self.app.view.log_status.get())
        self.assertEqual('', self.app.view.log_text.get('1.0', 'end-1c'))
        self.assertEqual('disabled', str(self.app.view.log_text.cget('state')))

    def test_large_read_only_log_viewer_pages_without_running_tests(self):
        self.app.state.observation_result = {'run_id': 'selected-observation', 'status': 'passed'}
        self.app.state.selected_observation_run_id = 'selected-observation'
        self.app.view.render(self.app.state)
        def chunk(_repo, _workspace, run_id, stream, offset):
            self.assertEqual('selected-observation', run_id)
            self.assertEqual('stdout', stream)
            self.assertIn(offset, (0, 65536))
            end = min(offset + 65536, 70000)
            return {'observation_run_id': run_id, 'observation_id': 'observation-' + 'a' * 20,
                    'stream': stream, 'reference': 'canonical external reference', 'sha256': 'b' * 64,
                    'integrity': 'verified', 'offset': offset, 'end': end, 'total_bytes': 70000,
                    'has_more': end < 70000, 'content': 'X' * (end - offset)}
        with patch.object(self.service, 'read_log', side_effect=chunk) as read, \
             patch.object(self.service, 'test', side_effect=AssertionError('viewer ran tests')):
            self.app.view.stdout_button.invoke(); self.wait(lambda: not self.app.state.loading)
            self.assertIn('More content exists', self.app.view.log_status.get())
            self.assertEqual('disabled', str(self.app.view.log_text.cget('state')))
            self.assertEqual(65536, len(self.app.view.log_text.get('1.0', 'end-1c')))
            self.app.view.next_log_button.invoke(); self.wait(lambda: not self.app.state.loading)
            self.assertEqual(4464, len(self.app.view.log_text.get('1.0', 'end-1c')))
            self.assertEqual('disabled', str(self.app.view.next_log_button.cget('state')))
            self.app.view.previous_log_button.invoke(); self.wait(lambda: not self.app.state.loading)
            self.assertEqual(65536, len(self.app.view.log_text.get('1.0', 'end-1c')))
            self.assertEqual([0, 65536, 0], [call.args[-1] for call in read.call_args_list])

    def test_windows_public_backend_passing_chain_uses_exact_evidence(self):
        target_test = self.repo / 'tests' / 'test_app.py'
        target_test.write_text('import unittest\nfrom app import run\nclass RunTests(unittest.TestCase):\n'
                               '    def test_run(self):\n        self.assertEqual(2, run())\n', encoding='utf-8')
        self.git('add', 'tests/test_app.py')
        self.git('commit', '-qm', 'bound regression for desired behavior')
        self.app.view.refresh_button.invoke(); self.wait(lambda: not self.app.state.loading)
        before_bytes = (self.repo / 'app.py').read_bytes()
        head_before = self.git('rev-parse', 'HEAD')
        refs_before = self.git('show-ref')
        index_before = self.git('ls-files', '--stage', '-z')
        with patch('src.developer.local_workflow.load_model', return_value=_Model()):
            self.app.view.index_button.invoke(); self.wait(lambda: not self.app.state.loading)
            self.app.view.goal.insert('1.0', 'Update run to return 2 while preserving its existing regression')
            self.window.update()
            self.app.view.plan_button.invoke(); self.wait(lambda: not self.app.state.loading)
        plan = self.app.state.plan_result
        self.assertEqual('completed', plan['status'])
        self.assertTrue(plan['proposed_action']['action_id'])
        self.app.view.selected_plan.set(plan['run_id'])
        self.app.view.candidate_path.set(str(self.candidate))
        self.app.view.candidate_validate.invoke(); self.wait(lambda: not self.app.state.loading)
        draft = self.app.state.candidate_result
        self.assertEqual('draft', draft['status'])
        self.app.view.selected_patch.set(draft['run_id'])
        self.app.view.review_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertEqual(self.text, self.app.view.diff_view.stored_text)
        bound = self.app.state.review_result['bound_tests']
        self.assertEqual(['tests.test_app.RunTests.test_run'], bound)
        self.app.view.approve_button.invoke(); self.wait(lambda: not self.app.state.loading)
        self.assertIsNotNone(self.app.view.confirmation)
        self.app.view.confirm_button.invoke(); self.wait(lambda: not self.app.state.loading)
        approval = self.app.state.decision_result
        self.assertEqual('approve', approval['decision'])
        self.app.view.notebook.select(self.app.view.run_tab)
        with patch.object(self.service, 'apply', wraps=self.service.apply) as apply, \
             patch.object(self.service, 'test', wraps=self.service.test) as test, \
             patch.object(self.service, 'verify', wraps=self.service.verify) as verify, \
             patch.object(self.service, 'evaluate', wraps=self.service.evaluate) as evaluate, \
             patch('src.developer.test_execution.execute_applied_patch_tests',
                   wraps=__import__('src.developer.test_execution', fromlist=['execute_applied_patch_tests']).execute_applied_patch_tests) as backend_test:
            self.app.view.selected_authorization.set(approval['run_id']); self.app.inputs_changed()
            self.app.view.apply_button.invoke()
            self.assertIsNotNone(self.app.view.apply_confirmation)
            apply.assert_not_called(); test.assert_not_called()
            self.app.confirm_apply(self.app.state.pending_apply)
            self.wait(lambda: not self.app.state.loading)
            execution = self.app.state.application_result
            self.assertEqual('applied', execution['status'])
            apply.assert_called_once_with(self.app.state.repository, self.app.state.workspace, approval['run_id'])
            test.assert_not_called(); verify.assert_not_called(); evaluate.assert_not_called()
            self.assertEqual(head_before, self.git('rev-parse', 'HEAD'))
            self.assertEqual(refs_before, self.git('show-ref'))
            self.assertEqual(index_before, self.git('ls-files', '--stage', '-z'))
            self.assertEqual(before_bytes.replace(b'return 1', b'return 2'), (self.repo / 'app.py').read_bytes())
            self.assertEqual(b' M app.py\n', self.git('status', '--porcelain=v1'))
            self.assertEqual(['app.py'], execution['files_changed'])
            self.assertEqual(1, len(execution['file_postimages']))
            postimage = execution['file_postimages'][0]
            self.assertEqual(hashlib.sha256(before_bytes).hexdigest(), postimage['preimage_sha256'])
            expected_hash = hashlib.sha256((self.repo / 'app.py').read_bytes()).hexdigest()
            self.assertEqual(expected_hash, postimage['expected_postimage_sha256'])
            self.assertEqual(expected_hash, postimage['observed_postimage_sha256'])
            self.app.view.selected_execution.set(execution['run_id']); self.app.inputs_changed()
            self.app.view.test_button.invoke(); self.wait(lambda: not self.app.state.loading)
            observation = self.app.state.observation_result
            self.assertEqual('passed', observation['status'])
            self.assertEqual(bound, observation['test_identities'])
            self.assertFalse(observation['unexpected_repository_changes'])
            self.assertEqual([], observation['unexpected_changed_paths'])
            test.assert_called_once_with(self.app.state.repository, self.app.state.workspace, execution['run_id'])
            self.assertEqual((), backend_test.call_args.kwargs['tests'])
            verify.assert_not_called(); evaluate.assert_not_called()
            self.app.view.selected_observation.set(observation['run_id']); self.app.inputs_changed()
            runs_before_log_read = sorted((self.workspace_path / 'runs').iterdir())
            self.app.view.stdout_button.invoke(); self.wait(lambda: not self.app.state.loading)
            self.assertEqual('verified', self.app.state.log_result['integrity'])
            self.assertEqual(observation['stdout_sha256'], self.app.state.log_result['sha256'])
            self.assertEqual('disabled', str(self.app.view.log_text.cget('state')))
            self.app.view.stderr_button.invoke(); self.wait(lambda: not self.app.state.loading)
            self.assertEqual('verified', self.app.state.log_result['integrity'])
            self.assertEqual(observation['stderr_sha256'], self.app.state.log_result['sha256'])
            self.assertIn('Ran 1 test', self.app.view.log_text.get('1.0', 'end'))
            self.assertEqual(runs_before_log_read, sorted((self.workspace_path / 'runs').iterdir()))
            test.assert_called_once()
            self.app.view.verify_button.invoke(); self.wait(lambda: not self.app.state.loading)
            verification = self.app.state.verification_result
            self.assertEqual('verified', verification['status'])
            verify.assert_called_once_with(self.app.state.repository, self.app.state.workspace,
                                           execution['run_id'], observation['run_id'])
            evaluate.assert_not_called()
            self.app.view.selected_verification.set(verification['run_id']); self.app.inputs_changed()
            self.app.view.evaluate_button.invoke(); self.wait(lambda: not self.app.state.loading)
            evaluation = self.app.state.evaluation_result
            self.assertEqual('no_recovery_required', evaluation['classification'])
            evaluate.assert_called_once_with(self.app.state.repository, self.app.state.workspace,
                                             verification['run_id'])
            self.assertFalse(evaluation['retry_eligible'])
            self.assertFalse(evaluation['rollback_performed'])
            self.assertFalse(evaluation['source_mutation_performed'])
            self.assertFalse(evaluation['lifecycle_transition_performed'])
            self.assertEqual(head_before, self.git('rev-parse', 'HEAD'))
            self.assertEqual(index_before, self.git('ls-files', '--stage', '-z'))

    def test_windows_public_backend_failing_chain_uses_external_evidence(self):
        self.draft()
        self.confirmation()
        self.app.view.confirm_button.invoke()
        self.wait(lambda: not self.app.state.loading)
        approval = self.app.state.decision_result
        self.app.view.selected_authorization.set(approval['run_id'])
        self.app.inputs_changed()
        self.app.view.apply_button.invoke()
        self.app.confirm_apply(self.app.state.pending_apply)
        self.wait(lambda: not self.app.state.loading)
        execution = self.app.state.application_result
        self.assertEqual('applied', execution['status'])
        self.assertEqual('    return 2\n', (self.repo / 'app.py').read_text().splitlines(keepends=True)[-1])
        self.assertFalse((self.repo / 'test-executed').exists())
        self.assertIsNone(self.app.state.observation_result)
        self.app.view.selected_execution.set(execution['run_id'])
        self.app.inputs_changed()
        self.app.view.test_button.invoke()
        self.wait(lambda: not self.app.state.loading)
        observation = self.app.state.observation_result
        self.assertEqual('failed', observation['status'])
        self.assertTrue((self.repo / 'test-executed').exists())
        self.assertIsNone(self.app.state.verification_result)
        self.app.view.selected_observation.set(observation['run_id'])
        self.app.inputs_changed()
        self.app.view.verify_button.invoke()
        self.wait(lambda: not self.app.state.loading)
        verification = self.app.state.verification_result
        self.assertEqual('not_verified', verification['status'])
        self.assertIsNone(self.app.state.evaluation_result)
        self.app.view.selected_verification.set(verification['run_id'])
        self.app.inputs_changed()
        self.app.view.evaluate_button.invoke()
        self.wait(lambda: not self.app.state.loading)
        evaluation = self.app.state.evaluation_result
        self.assertEqual('unexpected_side_effect', evaluation['classification'])
        self.assertTrue(evaluation['blocking_conditions'])
        self.assertFalse(evaluation['retry_eligible'])
        self.assertFalse(evaluation['rollback_performed'])

    def test_confirmation_cancel_and_four_explicit_operations(self):
        self.draft()
        self.confirmation()
        self.app.view.confirm_button.invoke()
        self.wait(lambda: not self.app.state.loading)
        decision = self.app.state.decision_result
        self.assertEqual('approve', decision['decision'])
        self.assertEqual('disabled', str(self.app.view.apply_button.cget('state')))
        self.app.view.selected_authorization.set(decision['run_id'])
        self.app.inputs_changed()
        self.assertEqual('normal', str(self.app.view.apply_button.cget('state')))
        with patch.object(self.service, 'apply', return_value={'run_id': 'execution-run', 'status': 'applied',
                'execution_id': 'execution-id', 'file_postimages': []}) as apply, \
             patch.object(self.service, 'test', return_value={'run_id': 'observation-run', 'status': 'failed',
                'test_identities': ['tests.unit.Case.test_one'], 'failures': 1}) as test, \
             patch.object(self.service, 'verify', return_value={'run_id': 'verification-run', 'status': 'not_verified',
                'deviations': ['phase70_tests_did_not_pass']}) as verify, \
             patch.object(self.service, 'evaluate', return_value={'run_id': 'evaluation-run',
                'classification': 'failed_tests', 'retry_eligible': False}) as evaluate:
            self.app.view.apply_button.invoke()
            self.assertIsNotNone(self.app.view.apply_confirmation)
            apply.assert_not_called()
            self.app.cancel_apply()
            apply.assert_not_called()
            self.app.view.apply_button.invoke()
            self.app.confirm_apply(self.app.state.pending_apply)
            self.wait(lambda: not self.app.state.loading)
            apply.assert_called_once_with(self.app.state.repository, self.app.state.workspace, decision['run_id'])
            test.assert_not_called()
            self.assertEqual('execution-run', self.app.state.application_result['run_id'])
            self.app.view.selected_execution.set('execution-run')
            self.app.inputs_changed()
            self.app.view.test_button.invoke()
            self.wait(lambda: not self.app.state.loading)
            test.assert_called_once_with(self.app.state.repository, self.app.state.workspace, 'execution-run')
            verify.assert_not_called()
            self.app.view.selected_observation.set('observation-run')
            self.app.inputs_changed()
            self.app.view.verify_button.invoke()
            self.wait(lambda: not self.app.state.loading)
            verify.assert_called_once_with(self.app.state.repository, self.app.state.workspace, 'execution-run', 'observation-run')
            evaluate.assert_not_called()
            self.app.view.selected_verification.set('verification-run')
            self.app.inputs_changed()
            self.app.view.evaluate_button.invoke()
            self.wait(lambda: not self.app.state.loading)
            evaluate.assert_called_once_with(self.app.state.repository, self.app.state.workspace, 'verification-run')
            self.assertIn('failed_tests', self.app.view.run_sections[4][1].get('1.0', 'end'))
