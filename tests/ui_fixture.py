"""Disposable Git fixtures and exact non-writing snapshots for UI tests."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aida-ui-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repository"
        self.repo.mkdir()
        self.workspace_path = self.root / "missing-workspace"
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "UI Fixture")
        self.git("config", "user.email", "ui@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.autocrlf", "false")
        (self.repo / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
        self.git("add", "app.py")
        self.git("commit", "-qm", "fixture")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
                              capture_output=True, check=True).stdout

    def snapshot(self):
        # Include physical index bytes as well as all target files/refs/HEAD.
        return (self.git("rev-parse", "HEAD"), self.git("show-ref"),
                (self.repo / ".git" / "index").read_bytes(),
                {str(path.relative_to(self.repo)): path.read_bytes()
                 for path in self.repo.rglob("*") if path.is_file()},
                {str(path.relative_to(self.workspace_path)): path.read_bytes()
                 for path in self.workspace_path.rglob("*") if path.is_file()})
