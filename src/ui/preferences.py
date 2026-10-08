"""Appearance-only convenience persistence, isolated from project evidence."""

import json
import os
from pathlib import Path
import stat
import tempfile


MODES = ("Light", "Dark", "System")


class AppearancePreferences:
    def __init__(self, protected_roots=(), *, path=None, environ=None):
        environment = os.environ if environ is None else environ
        local = environment.get("LOCALAPPDATA")
        self.path = Path(path) if path is not None else (
            Path(local) / "AIDA" / "ui-v1" / "preferences.json" if local else
            Path.home() / ".prototype" / "ui-v1" / "preferences.json")
        self.protected_roots = tuple(Path(root).expanduser().resolve()
                                     for root in protected_roots if root is not None)

    def _validate(self, repository=""):
        lexical = self.path.expanduser().absolute()
        for part in (lexical, *lexical.parents):
            try:
                metadata = os.lstat(part)
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(metadata.st_mode):
                raise ValueError("Appearance preference path contains a symlink.")
            if os.name == "nt":
                attributes = getattr(metadata, "st_file_attributes", None)
                if attributes is None:
                    raise ValueError("Appearance preference path reparse metadata is unavailable.")
                # Junctions and other reparse points can redirect a Windows path.
                if attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    raise ValueError("Appearance preference path contains a junction or reparse point.")
        resolved = lexical.resolve()
        roots = self.protected_roots + ((Path(repository).expanduser().resolve(),)
                                        if repository else ())
        for root in roots:
            if resolved == root or root in resolved.parents or resolved.parent in root.parents:
                raise ValueError("Appearance preferences must remain outside project and protected roots.")
        return resolved

    def load(self, repository=""):
        try:
            path = self._validate(repository)
            if not path.exists():
                return "System", None
            if not path.is_file() or path.stat().st_size > 4096:
                raise ValueError("Appearance preference file is not a bounded regular file.")
            payload = json.loads(path.read_bytes().decode("utf-8"))
            if (not isinstance(payload, dict) or set(payload) != {"appearance"}
                    or payload["appearance"] not in MODES):
                raise ValueError("Appearance preference content is invalid.")
            return payload["appearance"], None
        except (OSError, ValueError, UnicodeError) as error:
            return "System", f"Appearance preferences unavailable: {error}"

    def save(self, mode, repository=""):
        temporary = None
        try:
            if mode not in MODES:
                raise ValueError("Unknown appearance preference.")
            path = self._validate(repository)
            path.parent.mkdir(parents=True, exist_ok=True)
            path = self._validate(repository)
            descriptor, temporary = tempfile.mkstemp(prefix=".appearance-", dir=path.parent)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump({"appearance": mode}, handle)
                handle.write("\n")
            self._validate(repository)
            os.replace(temporary, path)
            temporary = None
            return None
        except (OSError, ValueError) as error:
            return f"Appearance preference not saved: {error}"
        finally:
            if temporary is not None:
                try:
                    Path(temporary).unlink(missing_ok=True)
                except OSError:
                    pass  # A failed convenience save must not disrupt a developer operation.
