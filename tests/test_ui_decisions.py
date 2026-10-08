"""Canonical non-writing review and explicit Phase 68 adapter coverage."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
from unittest.mock import patch

from src.developer.local_workflow import DeveloperWorkspace, _json_bytes
from src.developer.patch_authorization import _read_patch_run
from src.developer.patch_drafting import _draft_patch_candidate, SuppliedPatchGenerator
from src.ui.state import ViewState
from tests import test_ui_candidates as fixtures


class DecisionFixture(fixtures.CandidateFixture):
    def accepted(self):
        plan = self.completed_plan()
        return plan, self.import_plan(plan)

    def blocked(self):
        plan = self.completed_plan()
        proposal = deepcopy(plan['proposed_action'])
        proposal['unresolved_evidence'] = [{'type': 'ambiguous', 'action': 'manual_review_required'}]
        return _draft_patch_candidate(DeveloperWorkspace(self.workspace_path), self.repo,
                                      proposal, SuppliedPatchGenerator(self.text))

    def review(self, draft):
        return self.service.review_patch(*self.args, patch_run_id=draft['run_id'])

    def decide(self, draft, decision, **kwargs):
        return self.service.decide(*self.args, patch_run_id=draft['run_id'], decision=decision,
                                   approved_by=kwargs.get('approved_by', 'local-developer'),
                                   note=kwargs.get('note'))

    def tamper(self, draft, file, transform):
        path = self.workspace_path / 'runs' / draft['run_id'] / file
        value = json.loads(path.read_bytes())
        transform(value)
        path.write_bytes(_json_bytes(value))


class CanonicalReviewTests(DecisionFixture):
    def test_review_preserves_stored_utf8_crlf_without_normalization(self):
        plan = self.completed_plan()
        text = self.text.replace('\n', '\r\n')
        self.candidate.write_bytes(text.encode('utf-8'))
        draft = self.import_plan(plan)
        before = self.snapshot()
        review = self.review(draft)
        self.assertEqual(text, review['draft']['patch_text'])
        self.assertEqual(hashlib.sha256(text.encode('utf-8')).hexdigest(), review['patch_sha256'])
        self.assertEqual(before, self.snapshot())

    def test_accepted_review_exact_ids_scope_digest_linked_tests_and_no_writes(self):
        plan, draft = self.accepted()
        before = self.snapshot()
        with patch.object(DeveloperWorkspace, '_prepare', side_effect=AssertionError('review must not prepare')):
            review = self.review(draft)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(draft, review['draft'])
        self.assertEqual(draft['patch_text'], review['draft']['patch_text'])
        self.assertEqual(hashlib.sha256(draft['patch_text'].encode('utf-8')).hexdigest(), review['patch_sha256'])
        self.assertTrue(review['state_matches'])
        self.assertEqual(plan['tests']['selected_tests'], review['bound_tests'])
        self.assertEqual(plan['run_id'], review['draft']['source_plan_run_id'])
        self.assertLess(set(draft['candidate_paths']), set(draft['target_paths']))
        self.assertEqual(draft['candidate_symbol_scope'], review['draft']['candidate_symbol_scope'])

    def test_intact_blocked_review_is_read_only_and_tests_unavailable(self):
        draft = self.blocked()
        before = self.snapshot()
        review = self.review(draft)
        self.assertEqual('blocked', review['draft']['status'])
        self.assertEqual('', review['draft']['patch_text'])
        self.assertIsNone(review['bound_tests'])
        self.assertEqual(before, self.snapshot())

    def test_missing_record_review_does_not_initialize_workspace(self):
        with self.assertRaisesRegex(ValueError, 'missing or malformed'):
            self.service.review_patch(*self.args, patch_run_id='0' * 20)
        self.assertFalse(self.workspace_path.exists())

    def test_canonical_tamper_metadata_text_scope_and_malformed_record_refused(self):
        _, draft = self.accepted()
        directory = self.workspace_path / 'runs' / draft['run_id']
        originals = {name: (directory / name).read_bytes() for name in ('metadata.json', 'results.json')}
        cases = [('metadata.json', lambda v: v.update(command='wrong')),
                 ('results.json', lambda v: v.update(patch_text=self.text.replace('return 2', 'return 3'))),
                 ('results.json', lambda v: v.update(candidate_symbol_scope=[{'file_path': 'app.py', 'qualified_symbol': 'sibling'}]))]
        for file, transform in cases:
            self.tamper(draft, file, transform)
            before = self.snapshot()
            with self.assertRaises(ValueError): self.review(draft)
            for decision in ('approve', 'reject'):
                with self.assertRaises(ValueError): self.decide(draft, decision)
            self.assertEqual(before, self.snapshot())
            (directory / file).write_bytes(originals[file])
        (directory / 'results.json').write_bytes(b'{')
        with self.assertRaisesRegex(ValueError, 'missing or malformed'): self.review(draft)

    def test_unavailable_linked_plan_never_uses_session_plan_tests(self):
        plan, draft = self.accepted()
        (self.workspace_path / 'runs' / plan['run_id'] / 'results.json').write_bytes(b'{}')
        before = self.snapshot()
        review = self.review(draft)
        self.assertIsNone(review['bound_tests'])
        self.assertTrue(review['linked_plan_error'])
        self.assertEqual(before, self.snapshot())


class Phase68ServiceTests(DecisionFixture):
    def test_exact_public_service_routing_and_errors(self):
        returned = {'authorization_id': 'actual', 'run_id': 'actual-run'}
        with patch('src.developer.patch_authorization.record_patch_decision', return_value=returned) as call:
            result = self.service.decide(*self.args, patch_run_id='exact-run', decision='reject', approved_by='label', note='note')
        self.assertIs(returned, result)
        self.assertIsInstance(call.call_args.args[0], DeveloperWorkspace)
        self.assertEqual(self.repo.resolve(), call.call_args.args[1])
        self.assertEqual(('exact-run', 'reject'), call.call_args.args[2:])
        self.assertEqual({'approved_by': 'label', 'note': 'note'}, call.call_args.kwargs)
        with patch('src.developer.patch_authorization.record_patch_decision', side_effect=ValueError('exact backend error')):
            with self.assertRaisesRegex(ValueError, 'exact backend error'):
                self.service.decide(*self.args, patch_run_id='exact-run', decision='approve', approved_by='label', note=None)

    def test_real_public_approve_and_reject_exact_external_records_no_mutation(self):
        _, draft = self.accepted()
        review = self.review(draft)
        target_before = self.snapshot()[:4]
        for decision in ('approve', 'reject'):
            previous = self.snapshot()[4]
            result = self.decide(draft, decision, approved_by='reviewer', note='literal note')
            self.assertEqual(decision, result['decision'])
            self.assertTrue(result['authorization_id'].startswith('authorization-'))
            self.assertTrue(result['run_id'])
            for field, source in (('source_action_id', 'source_action_id'), ('source_patch_id', 'patch_id'),
                                  ('source_patch_run_id', 'run_id'), ('candidate_paths', 'candidate_paths'),
                                  ('allowed_symbol_scope', 'allowed_symbol_scope'), ('candidate_symbol_scope', 'candidate_symbol_scope')):
                self.assertEqual(draft[source], result[field])
            self.assertEqual(review['patch_sha256'], result['patch_sha256'])
            self.assertEqual(decision == 'approve', result['execution_authorized'])
            self.assertEqual('apply_exact_patch' if decision == 'approve' else 'none', result['allowed_operation'])
            self.assertFalse(result['executed']); self.assertFalse(result['tests_executed'])
            self.assertFalse(result['source_mutation_performed'])
            self.assertEqual(target_before, self.snapshot()[:4])
            after = self.snapshot()[4]
            for path, body in previous.items(): self.assertEqual(body, after[path])
            additions = set(after) - set(previous)
            self.assertTrue(additions)
            self.assertTrue(all(Path(path).parts[:2] == ('runs', result['run_id']) for path in additions))
            self.assertFalse((self.repo / 'test-executed').exists())

    def test_blocked_cannot_approve_but_can_reject_with_stale_source(self):
        draft = self.blocked()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Blocked PatchDraft'): self.decide(draft, 'approve')
        self.assertEqual(before, self.snapshot())
        (self.repo / 'app.py').write_text('def run():\n    return 9\n')
        before_target = self.snapshot()[:4]
        result = self.decide(draft, 'reject')
        self.assertEqual('reject', result['decision'])
        self.assertFalse(result['execution_authorized'])
        self.assertEqual(before_target, self.snapshot()[:4])

    def test_head_source_and_wrong_repository_refusals_preserve_history(self):
        _, draft = self.accepted()
        self.decide(draft, 'approve')
        (self.repo / 'app.py').write_text('def run():\n    return 9\n')
        for committed in (False, True):
            if committed:
                self.git('add', 'app.py'); self.git('commit', '-qm', 'changed HEAD')
            before = self.snapshot()
            with self.assertRaisesRegex(ValueError, 'Repository state'): self.decide(draft, 'approve')
            self.assertEqual(before, self.snapshot())
        # Canonical historical review and rejection remain possible after state drift.
        self.assertFalse(self.review(draft)['state_matches'])
        self.assertEqual('reject', self.decide(draft, 'reject')['decision'])
        other = self.root / 'other'; other.mkdir()
        import subprocess
        subprocess.run(['git', 'clone', '-q', str(self.repo), str(other)], check=True, capture_output=True)
        with self.assertRaisesRegex(ValueError, 'Repository path'):
            self.service.decide(str(other), self.args[1], patch_run_id=draft['run_id'], decision='reject', approved_by='label', note=None)

    def test_audit_limits_and_missing_record_do_not_fabricate_decision(self):
        _, draft = self.accepted()
        before = self.snapshot()
        for label, note, expected in (('', None, 'audit label'), ('x' * 101, None, 'audit label'), ('valid', 'x' * 501, 'review note')):
            with self.assertRaisesRegex(ValueError, expected): self.decide(draft, 'approve', approved_by=label, note=note)
        with self.assertRaises(ValueError):
            self.service.decide(*self.args, patch_run_id='0' * 20, decision='reject', approved_by='valid', note=None)
        self.assertEqual(before, self.snapshot())

    def test_same_head_branch_guard_is_session_only_and_reject_has_no_guard(self):
        _, draft = self.accepted()
        self.git('switch', '-qc', 'same-head')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'branch context'):
            self.service.decide(*self.args, patch_run_id=draft['run_id'], decision='approve', approved_by='label', note=None, expected_branch='refs/heads/main')
        self.assertEqual(before, self.snapshot())
        self.assertEqual('reject', self.service.decide(*self.args, patch_run_id=draft['run_id'], decision='reject', approved_by='label', note=None, expected_branch='refs/heads/main')['decision'])


class DecisionStateTests(DecisionFixture):
    def test_no_selected_patch_cannot_review_or_decide(self):
        state = ViewState(repository=self.args[0], workspace=self.args[1], facts={})
        for operation in ('review_patch', 'review_approval', 'decide_approve', 'decide_reject'):
            self.assertIsNone(state.begin_operation(operation, *self.args))
            self.assertIn('Select the exact Phase 67', state.review_error)
            self.assertIsNone(state.decision_result)

    def ready(self):
        plan, draft = self.accepted()
        state = ViewState(repository=self.args[0], workspace=self.args[1], facts=self.service.read_repository(*self.args),
                          plan_result=plan, candidate_result=draft, selected_plan_run_id=plan['run_id'])
        state.patch_inputs(draft['run_id'])
        request = state.begin_operation('review_approval', *self.args)
        state.complete(request, self.review(draft), None)
        self.assertTrue(state.open_approval(request))
        return state, draft

    def test_confirmation_is_frozen_bound_and_duplicate_submission_refused(self):
        state, draft = self.ready()
        context = state.pending_approval
        self.assertTrue(state.approval_matches())
        self.assertIsNone(state.begin_operation('plan', *self.args))
        request = state.begin_operation('decide_approve', *self.args)
        self.assertEqual(context.patch_run_id, request.patch_run_id)
        self.assertEqual('refs/heads/main', request.expected_branch)
        self.assertIsNone(state.pending_approval)
        self.assertIsNone(state.begin_operation('decide_approve', *self.args))
        state.complete(request, {'decision': 'approve', 'run_id': 'actual'}, None)
        self.assertIsNone(state.begin_operation('decide_reject', *self.args))
        self.assertEqual('actual', state.decision_result['run_id'])

    def test_all_selection_changes_clear_pending_review_and_decision(self):
        state, draft = self.ready()
        baseline = deepcopy(state)
        changes = (lambda s: s.select('other', s.workspace), lambda s: s.select(s.repository, 'other'),
                   lambda s: s.planning_inputs('other goal', ()), lambda s: s.planning_inputs('', ('new.test',)),
                   lambda s: s.candidate_inputs('other.diff', s.selected_plan_run_id),
                   lambda s: s.candidate_inputs(s.candidate_path, ''), lambda s: s.patch_inputs(''))
        for change in changes:
            state = deepcopy(baseline); state.decision_result = {'run_id': 'old'}
            change(state)
            self.assertIsNone(state.pending_approval)
            self.assertIsNone(state.review_result); self.assertIsNone(state.decision_result)

    def test_stale_review_completion_and_unconfirmed_approval_never_decide(self):
        state, draft = self.ready()
        state.pending_approval = None
        self.assertIsNone(state.begin_operation('decide_approve', *self.args))
        request = state.begin_operation('review_patch', *self.args)
        state.patch_inputs('')
        self.assertFalse(state.complete(request, self.review(draft), None))
        self.assertIsNone(state.review_result); self.assertIsNone(state.decision_result)
