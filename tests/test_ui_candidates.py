"""External input adapter, immutable requests, and public Phase 67 fixtures."""
from dataclasses import replace
from copy import deepcopy
import difflib
import json
from pathlib import Path
from unittest.mock import patch

from src.config import load_config
from src.ui.service import RepositoryService
from src.ui.state import ViewState
from tests.ui_fixture import GitFixture
from tests.test_implementation_planning import _Model


class CandidateFixture(GitFixture):
    def setUp(self):
        super().setUp()
        (self.repo / 'tests').mkdir()
        (self.repo / 'tests/test_app.py').write_text('import unittest\nfrom app import run\nclass RunTests(unittest.TestCase):\n    def test_run(self):\n        open("test-executed", "w").write("ran")\n        self.assertEqual(1, run())\n', encoding='utf-8')
        self.git('add', '--all'); self.git('commit', '-qm', 'tests')
        self.service = RepositoryService(replace(load_config(environ={}), developer_workspace=self.workspace_path))
        self.args = (str(self.repo), str(self.workspace_path))
        self.candidate = self.root / 'external.diff'
        original = (self.repo / 'app.py').read_text()
        self.text = ''.join(difflib.unified_diff(original.splitlines(True), original.replace('return 1', 'return 2').splitlines(True), fromfile='a/app.py', tofile='b/app.py'))
        self.candidate.write_bytes(self.text.encode())

    def completed_plan(self):
        with patch('src.developer.local_workflow.load_model', return_value=_Model()):
            self.service.index(*self.args)
            plan = self.service.plan(*self.args, goal='improve run')
        self.assertEqual('completed', plan['status'])
        return plan

    def import_plan(self, plan):
        return self.service.import_candidate(*self.args, plan_run_id=plan['run_id'], proposal=plan['proposed_action'], patch_path=str(self.candidate))


class CandidateTests(CandidateFixture):
    def test_adapter_uses_public_function_and_preserves_utf8_crlf_once(self):
        text = self.text.replace('\n', '\r\n') + '\n'
        self.candidate.write_bytes(text.encode('utf-8'))
        proposal = {'action_id': 'proposal-exact'}
        returned = {'status': 'draft'}
        with patch('src.developer.patch_drafting.draft_patch', return_value=returned) as draft:
            result = self.service.import_candidate(*self.args, plan_run_id='exact-run', proposal=proposal, patch_path=str(self.candidate))
        self.assertIs(returned, result)
        self.assertIs(proposal, draft.call_args.args[2])
        self.assertEqual(text, draft.call_args.args[3].patch_text)
        self.assertEqual({'plan_run_id': 'exact-run'}, draft.call_args.kwargs)
        self.assertFalse(self.workspace_path.exists())

    def test_external_boundary_missing_utf8_unreadable_and_symlink(self):
        inside = self.repo / 'inside.diff'; inside.write_bytes(self.text.encode())
        link = self.root / 'link.diff'; link.symlink_to(inside)
        for path in (inside, link):
            with self.assertRaisesRegex(ValueError, 'outside'):
                self.service.import_candidate(*self.args, plan_run_id='x', proposal={}, patch_path=str(path))
        self.candidate.write_bytes(b'\xff')
        with self.assertRaises(UnicodeDecodeError):
            self.service.import_candidate(*self.args, plan_run_id='x', proposal={}, patch_path=str(self.candidate))
        with self.assertRaises(FileNotFoundError):
            self.service.import_candidate(*self.args, plan_run_id='x', proposal={}, patch_path=str(self.root / 'missing'))
        with patch.object(Path, 'read_bytes', side_effect=PermissionError('unreadable')):
            with self.assertRaisesRegex(PermissionError, 'unreadable'):
                self.service.import_candidate(*self.args, plan_run_id='x', proposal={}, patch_path=str(self.candidate))

    def test_real_public_draft_strict_subset_persists_only_external_evidence(self):
        plan = self.completed_plan()
        before = self.snapshot()[:4]
        result = self.import_plan(plan)
        self.assertEqual('draft', result['status'])
        self.assertEqual(self.text, result['patch_text'])
        self.assertEqual(plan['run_id'], result['source_plan_run_id'])
        self.assertEqual(plan['proposed_action']['action_id'], result['source_action_id'])
        self.assertTrue(result['patch_id'].startswith('patch-'))
        self.assertTrue(result['run_id'])
        self.assertEqual(['app.py'], result['candidate_paths'])
        self.assertLess(set(result['candidate_paths']), set(result['target_paths']))
        self.assertEqual([{'file_path': 'app.py', 'qualified_symbol': 'run'}], result['candidate_symbol_scope'])
        self.assertEqual(before, self.snapshot()[:4])
        self.assertFalse(result['tests_executed'])
        self.assertFalse((self.repo / 'test-executed').exists())
        stored = json.loads((self.workspace_path / 'runs' / result['run_id'] / 'results.json').read_text())
        self.assertEqual({key: value for key, value in result.items() if key != 'run_id'}, stored)

    def test_real_refusals_do_not_create_draft_runs_or_mutate_target(self):
        plan = self.completed_plan()
        before = self.snapshot()
        variants = ['diff --git a/app.py b/app.py\n' + self.text,
                    '--- a/app.py\ninvalid\n', self.text.replace('app.py', 'outside.py')]
        for text in variants:
            self.candidate.write_bytes(text.encode())
            with self.assertRaises((ValueError, RuntimeError)):
                self.import_plan(plan)
            self.assertEqual(before, self.snapshot())
        self.candidate.write_bytes(self.text.encode())
        altered = deepcopy(plan); altered['proposed_action']['goal'] = 'altered goal'
        with self.assertRaises((ValueError, RuntimeError)):
            self.import_plan(altered)
        self.assertEqual(before, self.snapshot())

    def test_real_stale_source_and_head_refused(self):
        plan = self.completed_plan()
        (self.repo / 'app.py').write_text('def run():\n    return 3\n')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.import_plan(plan)
        self.assertEqual(before, self.snapshot())
        self.git('add', 'app.py'); self.git('commit', '-qm', 'new head')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.import_plan(plan)
        self.assertEqual(before, self.snapshot())

    def test_request_captures_exact_plan_and_rejects_stale_candidate_completion(self):
        plan = {'status': 'completed', 'run_id': 'plan-exact', 'proposed_action': {'action_id': 'proposal-exact'}}
        state = ViewState(repository=self.args[0], workspace=self.args[1], facts={}, plan_result=plan)
        state.candidate_inputs(str(self.candidate), 'plan-exact')
        request = state.begin_operation('import_candidate', *self.args)
        self.assertEqual('plan-exact', request.plan_run_id)
        plan['proposed_action']['action_id'] = 'later-change'
        self.assertEqual('proposal-exact', request.proposal['action_id'])
        self.assertIsNone(state.begin_operation('import_candidate', *self.args))
        state.candidate_inputs('another.diff', 'plan-exact')
        self.assertFalse(state.complete(request, {'status': 'draft'}, None))
        self.assertIsNone(state.candidate_result)
        for status in ('limited', 'manual_review_required'):
            state.plan_result['status'] = status
            self.assertIsNone(state.begin_operation('import_candidate', *self.args))

    def test_backend_exception_propagates_and_missing_plan_creates_no_run(self):
        with self.assertRaises((ValueError, KeyError)):
            self.service.import_candidate(*self.args, plan_run_id='missing', proposal={}, patch_path=str(self.candidate))
        self.assertFalse(list(self.workspace_path.rglob('metadata.json')))

    def test_public_noncompleted_plan_is_refused_without_draft_record(self):
        with patch('src.developer.local_workflow.load_model', return_value=_Model()):
            plan = self.service.plan(*self.args, goal='improve run')
        self.assertNotEqual('completed', plan['status'])
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.import_plan(plan)
        self.assertEqual(before, self.snapshot())

    def test_public_missing_plan_and_altered_stored_test_binding_refused(self):
        plan = self.completed_plan()
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.service.import_candidate(*self.args, plan_run_id='missing', proposal=plan['proposed_action'], patch_path=str(self.candidate))
        self.assertEqual(before, self.snapshot())
        record = self.workspace_path / 'runs' / plan['run_id'] / 'results.json'
        changed = json.loads(record.read_text())
        changed['tests']['expected_test_selection']['selected_tests'] = ['invalid.test.identity']
        record.write_bytes(json.dumps(changed, sort_keys=True, separators=(',', ':')).encode())
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.import_plan(plan)
        self.assertEqual(before, self.snapshot())
