"""Canonical Phase 70 log reads stay contained, verified and non-executing."""

from pathlib import Path
import hashlib
import shutil
from unittest.mock import patch

from src.developer.local_workflow import LocalWorkflowError, scan_local_repository
from src.developer.ui_read import read_observation_log
from tests.test_ui_candidates import CandidateFixture


class ObservationLogTests(CandidateFixture):
    def setUp(self):
        super().setUp()
        plan = self.completed_plan()
        draft = self.import_plan(plan)
        approval = self.service.decide(*self.args, patch_run_id=draft['run_id'],
                                       decision='approve', approved_by='fixture', note=None)
        execution = self.service.apply(*self.args, approval['run_id'], expected_branch='refs/heads/main')
        self.observation = self.service.test(*self.args, execution['run_id'], expected_branch='refs/heads/main')
        self.workspace = self.service._workspace(str(self.workspace_path))

    def read(self, stream='stdout', run_id=None, offset=0):
        return read_observation_log(self.workspace, self.repo,
                                    run_id or self.observation['run_id'], stream, offset)

    def variant(self, **changes):
        payload = {key: value for key, value in self.observation.items() if key != 'run_id'}
        payload.update(changes)
        return self.workspace._record_run('test-applied-patch', scan_local_repository(self.repo), payload)

    def test_valid_exact_stdout_stderr_and_no_new_evidence_or_execution(self):
        runs_before = sorted((self.workspace_path / 'runs').iterdir())
        marker_before = (self.repo / 'test-executed').read_bytes()
        with patch('src.developer.test_execution.execute_applied_patch_tests',
                   side_effect=AssertionError('log read launched target tests')):
            for stream in ('stdout', 'stderr'):
                with self.subTest(stream=stream):
                    row = self.read(stream)
                    stored = Path(self.observation[f'{stream}_reference']).read_bytes()
                    self.assertEqual(stored.decode('utf-8', errors='replace'), row['content'])
                    self.assertEqual(hashlib.sha256(stored).hexdigest(), row['sha256'])
                    self.assertEqual('verified', row['integrity'])
                    self.assertEqual(self.observation['observation_id'], row['observation_id'])
                    self.assertFalse(row['has_more'])
        self.assertEqual(runs_before, sorted((self.workspace_path / 'runs').iterdir()))
        self.assertEqual(marker_before, (self.repo / 'test-executed').read_bytes())

    def test_missing_and_tampered_logs_are_refused(self):
        stdout = Path(self.observation['stdout_reference'])
        stdout.unlink()
        with self.assertRaisesRegex(LocalWorkflowError, 'missing'):
            self.read()
        stderr = Path(self.observation['stderr_reference'])
        stderr.write_bytes(stderr.read_bytes() + b'altered')
        with self.assertRaisesRegex(LocalWorkflowError, 'SHA-256 mismatch'):
            self.read('stderr')

    def test_traversal_and_wrong_observation_id_are_refused(self):
        traversal = self.variant(stdout_reference='../outside.log')
        with self.assertRaisesRegex(LocalWorkflowError, 'reference'):
            self.read(run_id=traversal)
        wrong_id = self.variant(observation_id='observation-invalid')
        with self.assertRaisesRegex(LocalWorkflowError, 'observation ID'):
            self.read(run_id=wrong_id)

    def test_symlink_escape_wrong_run_and_cross_repository_are_refused(self):
        stdout = Path(self.observation['stdout_reference'])
        stdout.unlink()
        outside = self.root / 'outside.log'
        outside.write_bytes(b'outside')
        stdout.symlink_to(outside)
        with self.assertRaisesRegex(LocalWorkflowError, 'symlink|outside'):
            self.read()
        with self.assertRaisesRegex(LocalWorkflowError, 'observation evidence'):
            self.read(run_id='0' * 20)
        other = self.root / 'other-repository'
        shutil.copytree(self.repo, other, symlinks=True)
        with self.assertRaisesRegex(LocalWorkflowError, 'different repository'):
            read_observation_log(self.workspace, other, self.observation['run_id'], 'stderr')

    def test_large_log_chunks_are_explicit_and_reconstruct_all_content(self):
        content = b'first line\n' + b'X' * 130000 + b'\nlast line\n'
        stdout = Path(self.observation['stdout_reference'])
        stdout.write_bytes(content)
        run_id = self.variant(stdout_sha256=hashlib.sha256(content).hexdigest())
        chunks = []
        offset = 0
        while True:
            row = self.read(run_id=run_id, offset=offset)
            chunks.append(row['content'])
            self.assertLessEqual(row['end'] - row['offset'], 65536)
            if not row['has_more']:
                break
            offset = row['end']
        self.assertGreater(len(chunks), 1)
        self.assertEqual(content.decode(), ''.join(chunks))
        self.assertEqual(len(content), row['total_bytes'])

    def test_multibyte_character_at_chunk_boundary_is_preserved_without_byte_gaps(self):
        content = b'a' * 65535 + '€'.encode('utf-8') + b'end'
        Path(self.observation['stdout_reference']).write_bytes(content)
        run_id = self.variant(stdout_sha256=hashlib.sha256(content).hexdigest())
        first = self.read(run_id=run_id)
        second = self.read(run_id=run_id, offset=first['end'])
        self.assertEqual(65535, first['end'])
        self.assertTrue(first['has_more'])
        self.assertEqual('a' * 65535, first['content'])
        self.assertTrue(second['content'].startswith('€'))
        self.assertFalse(second['has_more'])
        self.assertEqual(content, first['content'].encode('utf-8') + second['content'].encode('utf-8'))

    def test_invalid_utf8_is_reported_after_byte_integrity_check(self):
        content = b'valid-prefix\xffinvalid'
        Path(self.observation['stdout_reference']).write_bytes(content)
        run_id = self.variant(stdout_sha256=hashlib.sha256(content).hexdigest())
        with self.assertRaisesRegex(LocalWorkflowError, 'invalid UTF-8'):
            self.read(run_id=run_id)
