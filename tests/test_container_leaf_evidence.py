"""Exact retained leaves: parent exclusions never expand mutation authority."""
import copy
import difflib
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.developer.implementation_planning import _container_exclusion_basis, plan_change
from src.developer.local_workflow import DeveloperWorkspace, parse_local_repository, _git_index_state
from src.developer.patch_drafting import SuppliedPatchGenerator, draft_patch
from src.developer.patch_authorization import record_patch_decision
from src.developer.patch_application import apply_approved_patch
from src.developer.test_execution import execute_applied_patch_tests
from src.developer.execution_verification import verify_execution, _valid_phase65_informational_warning


class _Tokenizer:
    def __call__(self, text, add_special_tokens=True, **kwargs):
        return {"input_ids": [1] * max(1, len(text.split()) + 2)}


class _Model:
    tokenizer = _Tokenizer()

    def encode(self, texts, **kwargs):
        vectors = np.ones((len(texts), 384), dtype=np.float32)
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


class ContainerLeafEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.repo = self.home / 'repo'
        for name in ('module', 'tests'):
            (self.repo / name).mkdir(parents=True)
            (self.repo / name / '__init__.py').write_text('')
        self.source = ('class Calculator:\n    """' + 'context ' * 300 + '"""\n'
                       '    def divide(self, a, b):\n        self._last_answer = a * 1.0 / b\n'
                       '        return self._last_answer\n\n'
                       '    def sibling(self):\n        return 7\n')
        (self.repo / 'module/calc.py').write_text(self.source)
        (self.repo / 'tests/test_calc.py').write_text(
            'import unittest\nfrom module.calc import Calculator\n\n'
            'class CalculatorTest(unittest.TestCase):\n    """' + 'context ' * 300 + '"""\n'
            '    def test_divide(self):\n        self.assertEqual(1.5, Calculator().divide(3, 2))\n\n'
            '    def test_sibling(self):\n        self.assertEqual(7, Calculator().sibling())\n')
        self.git('init', '--quiet'); self.git('config', 'user.name', 'Leaf proof test')
        self.git('config', 'user.email', 'leaf@example.invalid')
        self.git('add', '--all'); self.git('commit', '--quiet', '-m', 'baseline')
        self.workspace = DeveloperWorkspace(self.home / 'workspace')
        self.parsed = parse_local_repository(self.repo)
        self.chunks = {(c.file_path, c.qualified_name): c for c in self.parsed.chunks}
        self.primary = self.chunks['module/calc.py', 'Calculator.divide']
        self.testleaf = self.chunks['tests/test_calc.py', 'CalculatorTest.test_divide']
        self.containers = [self.chunks[p, s] for p, s in (
            ('module/calc.py', 'module.calc'), ('module/calc.py', 'Calculator'),
            ('tests/test_calc.py', 'tests.test_calc'), ('tests/test_calc.py', 'CalculatorTest'))]
        self.exclusions = [self.exclusion(c) for c in self.containers]
        self.targets = [self.target(self.primary, 'primary_target'), self.target(self.testleaf, 'test_target')]
        identity = 'tests.test_calc.CalculatorTest.test_divide'
        self.expected = {'status': 'known', 'selected_tests': [identity], 'evidence': [
            {'test': identity, 'source': 'planned_target_static_import',
             'target_paths': ['module/calc.py', 'tests/test_calc.py']}]}
        self.impact = {'repository': {'working_tree_sha256': self.parsed.inventory.snapshot_id},
                       'index_freshness': {'status': 'current'},
                       'changes': {'files': [], 'token_limit_exclusions': self.exclusions},
                       'retrieval': {'query_evidence': [dict(file_path=self.primary.file_path,
                           symbol=self.primary.qualified_name, start_line=self.primary.start_line,
                           end_line=self.primary.end_line)], 'context_diagnostics': {
                               'included_context': [self.included(c) for c in (self.primary, self.testleaf)]}}}

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              capture_output=True).stdout.decode().strip()

    @staticmethod
    def exclusion(c):
        return dict(chunk_id=c.chunk_id, file_path=c.file_path, qualified_name=c.qualified_name,
                    start_line=c.start_line, end_line=c.end_line, reason='over_limit', token_count=350)

    @staticmethod
    def included(c):
        return dict(file_path=c.file_path, symbol_name=c.qualified_name,
                    content_sha256=hashlib.sha256(c.content.encode()).hexdigest())

    @staticmethod
    def target(c, role):
        return dict(file_path=c.file_path, qualified_symbol=c.qualified_name, start_line=c.start_line,
                    end_line=c.end_line, role=role, current_index_evidence=True,
                    evidence_types=['retrieval_evidence' if role == 'primary_target' else 'additional_related_context'])

    def basis(self, item=None, impact=None, targets=None, expected=None):
        return _container_exclusion_basis(item or self.exclusions[0], impact or self.impact,
                                         targets if targets is not None else self.targets, self.repo,
                                         expected if expected is not None else self.expected)

    def test_real_shape_module_and_class_primary_and_test_leaves(self):
        for item, kind in zip(self.exclusions, ['exact_retained_primary_leaf'] * 2 + ['exact_retained_test_leaf'] * 2):
            with self.subTest(symbol=item['qualified_name']):
                basis = self.basis(item=item)
                self.assertEqual(kind, basis['kind'])
                self.assertEqual(1, len(basis['proofs']))
                self.assertNotEqual(item['qualified_name'], basis['proofs'][0]['qualified_symbol'])
                self.assertEqual(item['chunk_id'], basis['container']['chunk_id'])
        related = copy.deepcopy(self.targets)
        related[1].update(start_line=None, end_line=None)
        self.assertEqual('exact_retained_test_leaf', self.basis(item=self.exclusions[3], targets=related)['kind'])

    def test_multiple_targets_require_every_exact_retained_leaf(self):
        sibling = self.chunks['module/calc.py', 'Calculator.sibling']
        targets = self.targets + [self.target(sibling, 'primary_target')]
        impact = copy.deepcopy(self.impact)
        impact['retrieval']['context_diagnostics']['included_context'].append(self.included(sibling))
        impact['retrieval']['query_evidence'].append(dict(file_path=sibling.file_path,
            symbol=sibling.qualified_name, start_line=sibling.start_line, end_line=sibling.end_line))
        self.assertEqual(2, len(self.basis(impact=impact, targets=targets)['proofs']))
        impact['retrieval']['context_diagnostics']['included_context'].pop()
        self.assertIsNone(self.basis(impact=impact, targets=targets))

    def test_multiple_test_leaves_require_each_exact_binding(self):
        sibling=self.chunks['tests/test_calc.py','CalculatorTest.test_sibling']
        targets=self.targets+[self.target(sibling,'test_target')]
        impact=copy.deepcopy(self.impact)
        impact['retrieval']['context_diagnostics']['included_context'].append(self.included(sibling))
        expected=copy.deepcopy(self.expected)
        identity='tests.test_calc.CalculatorTest.test_sibling'
        expected['selected_tests'].append(identity)
        expected['evidence'].append({'test':identity,'source':'planned_target_static_import',
                                     'target_paths':['tests/test_calc.py']})
        self.assertEqual(2,len(self.basis(item=self.exclusions[2],impact=impact,targets=targets,expected=expected)['proofs']))
        expected['evidence'].pop()
        self.assertIsNone(self.basis(item=self.exclusions[2],impact=impact,targets=targets,expected=expected))

    def test_unreported_git_change_and_parse_failure_cannot_be_waived(self):
        source=self.repo/'module/calc.py'
        source.write_text(self.source+'# changed parent\n')
        current=parse_local_repository(self.repo)
        impact=copy.deepcopy(self.impact)
        impact['repository']['working_tree_sha256']=current.inventory.snapshot_id
        module=next(c for c in current.chunks if c.qualified_name=='module.calc')
        self.assertIsNone(self.basis(item=self.exclusion(module),impact=impact))
        source.write_text(self.source+'invalid python (\n')
        current=parse_local_repository(self.repo)
        impact['repository']['working_tree_sha256']=current.inventory.snapshot_id
        self.assertTrue(current.parse_failures)
        self.assertIsNone(self.basis(impact=impact))

    def test_common_negative_cases_remain_blocking(self):
        for name, edit in (
            ('changed parent', lambda i,t: i['changes']['files'].append({'path': 'module/calc.py'})),
            ('stale index', lambda i,t: i['index_freshness'].update(status='stale')),
            ('wrong snapshot', lambda i,t: i['repository'].update(working_tree_sha256='0'*64)),
            ('excluded leaf', lambda i,t: i['changes']['token_limit_exclusions'].append(self.exclusion(self.primary))),
            ('missing retained leaf', lambda i,t: i['retrieval']['context_diagnostics'].update(included_context=[])),
            ('wrong leaf hash', lambda i,t: i['retrieval']['context_diagnostics']['included_context'][0].update(content_sha256='0'*64)),
            ('sibling substituted', lambda i,t: i['retrieval']['context_diagnostics']['included_context'][0].update(symbol_name='Calculator.sibling')),
            ('wrong leaf symbol', lambda i,t: t[0].update(qualified_symbol='Calculator.other')),
            ('outside range', lambda i,t: t[0].update(start_line=999)),
            ('not exact planned primary', lambda i,t: t[0].update(current_index_evidence=False)),
            ('missing primary range', lambda i,t: t[0].update(start_line=None)),
            ('manual inspection', lambda i,t: t[0].update(evidence_types=['manual_inspection'])),
            ('passing tests only', lambda i,t: i['retrieval']['context_diagnostics'].update(included_context=[])),
            ('same-file evidence', lambda i,t: i['retrieval']['context_diagnostics']['included_context'][0].pop('symbol_name')),
            ('label without hash', lambda i,t: i['retrieval']['context_diagnostics']['included_context'][0].pop('content_sha256')),
        ):
            impact, targets = copy.deepcopy(self.impact), copy.deepcopy(self.targets)
            edit(impact, targets)
            with self.subTest(case=name): self.assertIsNone(self.basis(impact=impact, targets=targets))
        for key, value in [('chunk_id','0'*64), ('file_path','other.py'), ('qualified_name','Other'),
                           ('start_line',999), ('end_line',999), ('start_line',True), ('reason','empty')]:
            item=copy.deepcopy(self.exclusions[0]); item[key]=value
            with self.subTest(field=key): self.assertIsNone(self.basis(item=item))
        failed=copy.copy(self.parsed)
        from dataclasses import replace
        failed=replace(failed, parse_failures=({'file_path':'module/calc.py'},))
        with patch('src.developer.local_workflow.parse_local_repository', return_value=failed):
            self.assertIsNone(self.basis())

    def test_test_binding_negative_cases_remain_blocking(self):
        item=self.exclusions[2]
        for name, edit in (
            ('unbound identity', lambda e: e.update(selected_tests=[])),
            ('missing binding', lambda e: e.update(evidence=[])),
            ('wrong source', lambda e: e['evidence'][0].update(source='manual_inspection')),
            ('passing test source', lambda e: e['evidence'][0].update(source='tests_passed')),
            ('sibling identity', lambda e: e['evidence'][0].update(test='tests.test_calc.CalculatorTest.test_sibling')),
            ('wrong binding path', lambda e: e['evidence'][0].update(target_paths=['other.py'])),
            ('unknown binding', lambda e: e.update(status='unknown')),
        ):
            expected=copy.deepcopy(self.expected); edit(expected)
            with self.subTest(case=name): self.assertIsNone(self.basis(item=item, expected=expected))
        with patch('src.developer_testing.catalog', return_value={}):
            self.assertIsNone(self.basis(item=item))
        expected=copy.deepcopy(self.expected); expected['evidence'][0]['source']='explicit_developer_selection'
        self.assertEqual('exact_retained_test_leaf', self.basis(item=item,expected=expected)['kind'])

    def plan(self):
        primary,testleaf=self.primary,self.testleaf
        query={'question':'Update Calculator.divide', 'run_id':'query-fixture',
               'results':[dict(chunk_id=primary.chunk_id,file_path=primary.file_path,
                   qualified_name=primary.qualified_name,start_line=primary.start_line,end_line=primary.end_line,
                   rank=1,related_context=[dict(chunk_id=testleaf.chunk_id,file_path=testleaf.file_path,
                       symbol_name=testleaf.qualified_name,reason='caller_relationship')])],
               'context':dict(included_context=[self.included(c) for c in (primary,testleaf)],
                              relationship_diagnostics=[],omitted_context=[],
                              expansion_decisions=[{'chunk_id':primary.chunk_id,'related_chunk_ids':[testleaf.chunk_id]}])}
        with patch('src.developer.local_workflow.load_model',return_value=_Model()):
            self.workspace.index(self.repo)
            with patch.object(self.workspace,'query',return_value=query):
                return plan_change(self.workspace,self.repo,goal='Update Calculator.divide',top_k=1)

    def diff(self, replacement):
        return ''.join(difflib.unified_diff(self.source.splitlines(True), replacement.splitlines(True),
                                           fromfile='a/module/calc.py',tofile='b/module/calc.py'))

    def test_scope_parent_never_authorizes_sibling_patch(self):
        plan=self.plan()
        self.assertEqual('completed',plan['status'],plan['unresolved_evidence'])
        self.assertEqual({'Calculator.divide','CalculatorTest.test_divide'},set(plan['proposed_action']['target_symbols']))
        self.assertEqual(4,len([w for w in plan['warnings'] if w['type']=='token_limit_exclusion']))
        from src.developer.local_workflow import LocalWorkflowError
        with self.assertRaisesRegex(LocalWorkflowError, 'exceeds path-qualified Phase 65 symbol scope'):
            draft_patch(self.workspace,self.repo,plan['proposed_action'],
                        SuppliedPatchGenerator(self.diff(self.source.replace('return 7','return 8'))),
                        plan_run_id=plan['run_id'])
        self.assertEqual(self.source,(self.repo/'module/calc.py').read_text())
        self.assertEqual('',self.git('status','--porcelain'))

    def lifecycle(self):
        plan=self.plan()
        self.assertEqual('completed',plan['status'],plan['unresolved_evidence'])
        draft=draft_patch(self.workspace,self.repo,plan['proposed_action'],
                          SuppliedPatchGenerator(self.diff(self.source.replace('a * 1.0 / b','a / b'))),
                          plan_run_id=plan['run_id'])
        self.assertEqual('draft',draft['status'],draft)
        approval=record_patch_decision(self.workspace,self.repo,draft['run_id'],'approve')
        applied=apply_approved_patch(self.workspace,self.repo,approval['run_id'])
        observation=execute_applied_patch_tests(self.workspace,self.repo,applied['run_id'])
        self.assertEqual('passed',observation['status'])
        return plan,approval,applied,observation

    def test_primary_and_test_historical_proofs_survive_exact_lifecycle(self):
        plan,approval,applied,observation=self.lifecycle()
        head,index=self.git('rev-parse','HEAD'),_git_index_state(self.repo)
        result=verify_execution(self.workspace,self.repo,applied['run_id'],observation['run_id'])
        self.assertEqual('verified',result['status'],result)
        self.assertEqual(2,len(result['expected_test_identities']))
        self.assertEqual(head,self.git('rev-parse','HEAD'))
        self.assertEqual(index,_git_index_state(self.repo))
        self.assertEqual({('module/calc.py','Calculator.divide')},
                         {(r['file_path'],r['qualified_symbol']) for r in applied['actual_patch_symbol_scope']})

    def test_phase71_tampered_proofs_are_uncertain(self):
        from src.developer import execution_verification as verifier
        plan,approval,applied,observation=self.lifecycle()
        original_reader=verifier._read_run
        changes=[('type',lambda w:w.update(type='unknown')),
                 ('relabeled retrieval omission',lambda w:w.update(type='retrieval_omission')),
                 ('classification',lambda w:w.update(classification='blocking')),
                 ('basis kind',lambda w:w['basis'].update(kind='manual_review')),
                 ('container path',lambda w:w['basis']['container'].update(file_path='other.py')),
                 ('container symbol',lambda w:w['basis']['container'].update(qualified_symbol='Other')),
                 ('boolean container range',lambda w:w['basis']['container'].update(start_line=True)),
                 ('missing proof',lambda w:w['basis']['proofs'][0].pop('content_sha256'))]
        for field,value in [('chunk_id','0'*64),('file_path','other.py'),('qualified_symbol','Calculator.sibling'),
                            ('content_sha256','0'*64),('start_line',999),('end_line',999),('target_role','related_context')]:
            changes.append((field,lambda w,k=field,v=value:w['basis']['proofs'][0].update({k:v})))
        for name,edit in changes:
            def reader(workspace,run_id,kind):
                meta,payload=original_reader(workspace,run_id,kind)
                if kind=='plan':
                    payload=copy.deepcopy(payload)
                    warning=next(w for w in payload['warnings'] if w['basis'].get('kind')=='exact_retained_primary_leaf')
                    edit(warning)
                return meta,payload
            with self.subTest(case=name),patch.object(verifier,'_read_run',side_effect=reader):
                result=verify_execution(self.workspace,self.repo,applied['run_id'],observation['run_id'])
                self.assertEqual('uncertain',result['status'],result)
                self.assertIn('phase65_informational_evidence_classification_invalid',result['unresolved_uncertainty'])
        for name,edit in [('test identity',lambda p,w:w['basis']['proofs'][0].update(test_identity='tests.test_calc.CalculatorTest.test_sibling')),
                          ('binding source',lambda p,w:w['basis']['proofs'][0].update(expected_test_binding_source='manual_inspection')),
                          ('historical binding source',lambda p,w:p['tests']['expected_test_selection']['evidence'][0].update(source='manual_inspection')),
                          ('removed expected binding',lambda p,w:p['tests']['expected_test_selection'].update(evidence=[])),
                          ('historical exclusion removed',lambda p,w:p['change_impact']['changes'].update(token_limit_exclusions=[]))]:
            def reader(workspace,run_id,kind):
                meta,payload=original_reader(workspace,run_id,kind)
                if kind=='plan':
                    payload=copy.deepcopy(payload)
                    warning=next(w for w in payload['warnings'] if w['basis'].get('kind')=='exact_retained_test_leaf')
                    edit(payload,warning)
                return meta,payload
            with self.subTest(case=name),patch.object(verifier,'_read_run',side_effect=reader):
                result=verify_execution(self.workspace,self.repo,applied['run_id'],observation['run_id'])
                self.assertNotEqual('verified',result['status'],result)
                self.assertIn('phase65_informational_evidence_classification_invalid',result['unresolved_uncertainty'])

    def test_phase71_rejects_broadened_execution_scope_and_parent_authority(self):
        from src.developer.patch_application import _load_authorization
        plan,approval,applied,observation=self.lifecycle()
        auth=_load_authorization(self.workspace,approval['run_id'])
        warning=next(w for w in plan['warnings'] if w['basis']['kind']=='exact_retained_primary_leaf')
        self.assertTrue(_valid_phase65_informational_warning(warning,plan,root=self.repo,execution=applied,authorization=auth))
        execution=copy.deepcopy(applied)
        execution['actual_patch_symbol_scope'].append({'file_path':'module/calc.py','qualified_symbol':'Calculator.sibling'})
        self.assertFalse(_valid_phase65_informational_warning(warning,plan,root=self.repo,execution=execution,authorization=auth))
        from types import SimpleNamespace
        broadened=SimpleNamespace(allowed_symbol_scope=auth.allowed_symbol_scope+(('module/calc.py','Calculator'),),
                                  candidate_symbol_scope=auth.candidate_symbol_scope)
        self.assertFalse(_valid_phase65_informational_warning(warning,plan,root=self.repo,execution=applied,authorization=broadened))
        from src.developer import execution_verification as verifier
        original_reader=verifier._read_run
        def reader(workspace,run_id,kind):
            meta,payload=original_reader(workspace,run_id,kind)
            if kind=='execution':
                payload=copy.deepcopy(payload)
                payload['actual_patch_symbol_scope'].append({'file_path':'module/calc.py','qualified_symbol':'Calculator.sibling'})
            return meta,payload
        with patch.object(verifier,'_read_run',side_effect=reader):
            result=verify_execution(self.workspace,self.repo,applied['run_id'],observation['run_id'])
        self.assertEqual('not_verified',result['status'],result)
        self.assertIn('phase65_informational_evidence_classification_invalid',result['unresolved_uncertainty'])
