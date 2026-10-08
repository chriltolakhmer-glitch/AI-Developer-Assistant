import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.ui.preferences import AppearancePreferences


class AppearancePreferenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="aida-appearance-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "project"
        self.repo.mkdir()
        self.path = self.root / "settings" / "preferences.json"
        self.store = AppearancePreferences((self.repo,), path=self.path)

    def test_default_is_read_only_and_all_modes_round_trip_without_authority(self):
        self.assertEqual(("System", None), self.store.load())
        self.assertFalse(self.path.parent.exists())
        for mode in ("Light", "Dark", "System"):
            self.assertIsNone(self.store.save(mode))
            self.assertEqual((mode, None), self.store.load())
            self.assertEqual({"appearance": mode}, json.loads(self.path.read_text()))
        self.assertEqual([], list(self.repo.iterdir()))

    def test_target_checkout_and_research_containment_before_any_writes(self):
        for root in (self.repo, self.root / "checkout", self.root / "research"):
            store = AppearancePreferences((root,), path=root / "ui" / "preferences.json")
            self.assertIn("outside", store.save("Dark"))
            self.assertEqual("System", store.load()[0])
            self.assertFalse((root / "ui").exists())
        target_store = AppearancePreferences(path=self.repo / "preferences.json")
        self.assertIn("outside", target_store.save("Dark", str(self.repo)))

    def test_corrupt_oversize_and_lifecycle_payloads_fail_to_system(self):
        self.path.parent.mkdir()
        for payload in ('{', 'x' * 4097, '{"appearance":"Blue"}',
                        '{"appearance":"Dark","authorization":"forged"}', '[]', '\xff'):
            self.path.write_bytes(payload.encode('utf-8'))
            mode, error = self.store.load()
            self.assertEqual("System", mode)
            self.assertIsNotNone(error)

    def test_unreadable_file_and_failed_save_are_nonfatal_and_preserve_old_bytes(self):
        self.store.save("Light")
        old = self.path.read_bytes()
        with patch.object(Path, 'read_bytes', side_effect=PermissionError('denied')):
            self.assertIn('denied', self.store.load()[1])
        with patch('src.ui.preferences.os.replace', side_effect=PermissionError('denied')):
            self.assertIn('denied', self.store.save('Dark'))
        self.assertEqual(old, self.path.read_bytes())
        self.assertEqual([self.path], list(self.path.parent.iterdir()))

    def test_symlink_file_and_parent_escape_are_refused(self):
        self.path.parent.mkdir()
        actual = self.root / 'actual.json'
        actual.write_text('{"appearance":"Light"}')
        self.path.symlink_to(actual)
        self.assertIn('symlink', self.store.load()[1])
        self.assertIn('symlink', self.store.save('Dark'))
        self.path.unlink()
        alias = self.root / 'alias'
        alias.symlink_to(self.repo, target_is_directory=True)
        store = AppearancePreferences(path=alias / 'preferences.json')
        self.assertIn('symlink', store.save('Dark'))
        self.assertEqual([], list(self.repo.iterdir()))

    def test_localappdata_and_fallback_paths_are_external_and_not_created_by_load(self):
        store = AppearancePreferences(environ={'LOCALAPPDATA': str(self.root)})
        self.assertEqual(self.root / 'AIDA' / 'ui-v1' / 'preferences.json', store.path)
        store.load()
        self.assertFalse(store.path.exists())
        fallback = AppearancePreferences(environ={})
        self.assertEqual(Path.home() / '.prototype' / 'ui-v1' / 'preferences.json', fallback.path)

    def test_junction_guard_and_cleanup_failure_remain_nonfatal(self):
        with patch.object(Path, 'is_junction', return_value=True):
            self.assertIn('junction', self.store.save('Dark'))
            self.assertEqual('System', self.store.load()[0])
        self.store.save('Light')
        with patch('src.ui.preferences.os.replace', side_effect=PermissionError('replace denied')), \
             patch.object(Path, 'unlink', side_effect=PermissionError('cleanup denied')):
            self.assertIn('replace denied', self.store.save('Dark'))
