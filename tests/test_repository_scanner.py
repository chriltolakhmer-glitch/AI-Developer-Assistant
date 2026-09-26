"""Tests for pinned, deterministic, read-only repository scanning."""

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.scanner import CommitMismatchError, RepositoryScanner, ScannerError


class RepositoryScannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "sample-repo"
        self.root.mkdir()
        self._git("init", "--quiet")
        self._git("config", "user.name", "Scanner Test")
        self._git("config", "user.email", "scanner-test@example.invalid")
        self.scanner = RepositoryScanner()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _git(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def _write(self, relative_path: str, content: bytes) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def _commit(self) -> str:
        self._git("add", "--all")
        self._git("commit", "--quiet", "-m", "test snapshot")
        return self._git("rev-parse", "HEAD")

    def test_rejects_a_different_commit_sha(self) -> None:
        self._write("app.py", b"answer = 42\n")
        actual_sha = self._commit()

        with self.assertRaises(CommitMismatchError):
            self.scanner.scan(self.root, "0" * 40)

        manifest = self.scanner.scan(self.root, actual_sha)
        self.assertEqual(actual_sha, manifest.repository.commit_sha)

    def test_discovers_tracked_python_files_and_applies_shared_exclusions(self) -> None:
        self._write("src/app.py", b"value = 1\n")
        self._write("tests/test_app.py", b"assert True\n")
        self._write("vendor/dependency.py", b"ignored = True\n")
        self._write("VENDORS/copy.py", b"ignored = True\n")
        self._write("fixtures/sample.py", b"ignored = True\n")
        self._write("testdata/sample.py", b"ignored = True\n")
        self._write("src/messages_pb2.py", b"ignored = True\n")
        self._write("src/readme.txt", b"not Python\n")
        commit_sha = self._commit()

        manifest = self.scanner.scan(self.root, commit_sha)

        self.assertEqual(3, manifest.eligible_python_file_count)
        self.assertEqual(3, len([file for file in manifest.files if file.included]))
        self.assertEqual(
            ["VENDORS/copy.py", "src/app.py", "tests/test_app.py"],
            [file.relative_path for file in manifest.files if file.included],
        )
        excluded = {file.relative_path: file.exclusion_reason for file in manifest.files if not file.included}
        self.assertEqual("excluded directory: vendor", excluded["vendor/dependency.py"])
        self.assertEqual("excluded directory: fixtures", excluded["fixtures/sample.py"])
        self.assertEqual("excluded directory: testdata", excluded["testdata/sample.py"])
        self.assertEqual("generated protobuf file (*_pb2.py)", excluded["src/messages_pb2.py"])

    def test_loc_counts_only_nonblank_noncomment_physical_lines(self) -> None:
        content = (
            b"# full-line comment\r\n"
            b"\r\n"
            b"   \t\r\n"
            b"value = 1\r\n"
            b"  # indented comment\r\n"
            b"message = '# not a comment line'\r\n"
        )
        self._write("app.py", content)
        commit_sha = self._commit()

        manifest = self.scanner.scan(self.root, commit_sha)

        self.assertEqual(2, manifest.eligible_python_loc)
        self.assertEqual(2, manifest.files[0].loc)

    def test_manifest_is_consistent_deterministic_and_source_tree_is_unchanged(self) -> None:
        content = b"# comment\nvalue = 7\n"
        self._write("pkg/module.py", content)
        commit_sha = self._commit()
        original_status = self._git("status", "--porcelain")

        first = self.scanner.scan(self.root, commit_sha, repository_id="sample")
        second = self.scanner.scan(self.root, commit_sha, repository_id="sample")

        self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual(1, first.eligible_python_file_count)
        self.assertEqual(1, first.eligible_python_loc)
        self.assertEqual(hashlib.sha256(content).hexdigest(), first.files[0].sha256)
        self.assertEqual(len(content), first.files[0].size_bytes)
        self.assertEqual(original_status, self._git("status", "--porcelain"))
        self.assertEqual(content, (self.root / "pkg/module.py").read_bytes())
        parsed = json.loads(first.to_json())
        self.assertEqual(1, parsed["summary"]["eligible_python_file_count"])
        self.assertNotIn(str(self.root), first.to_json())

    def test_manifest_file_is_written_outside_repository_only(self) -> None:
        self._write("app.py", b"value = 1\n")
        commit_sha = self._commit()
        output_path = Path(self.temporary_directory.name) / "manifests" / "sample.json"

        manifest = self.scanner.scan_to_file(self.root, output_path, commit_sha)

        self.assertEqual(manifest.to_json(), output_path.read_text(encoding="utf-8"))
        with self.assertRaises(ScannerError):
            self.scanner.scan_to_file(self.root, self.root / "manifest.json", commit_sha)
        self.assertEqual("", self._git("status", "--porcelain"))

    def test_requires_full_sha(self) -> None:
        self._write("app.py", b"value = 1\n")
        commit_sha = self._commit()

        with self.assertRaises(ScannerError):
            self.scanner.scan(self.root, commit_sha[:8])


if __name__ == "__main__":
    unittest.main()