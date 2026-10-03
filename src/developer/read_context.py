"""Operation-scoped cache for already validated developer journal replays.

This context is created for one read-only integration operation only. It has no
process-global cache and does not replace journal validation: the first load
replays and validates every event; reuse is allowed only while the journal file
set and per-file identity metadata remain unchanged.
"""
from collections import defaultdict
from copy import deepcopy
from functools import wraps
from pathlib import Path
import hashlib
import json

from .local_workflow import LocalWorkflowError


def _identity(directory: Path) -> tuple:
    """Return a cheap immutable identity for every event file in a journal."""
    try:
        paths = sorted(directory.glob("*.json"))
        rows = []
        for path in paths:
            stat = path.stat()
            rows.append((path.name, stat.st_dev, stat.st_ino, stat.st_size,
                         stat.st_mtime_ns, stat.st_ctime_ns))
        return tuple(rows)
    except OSError as error:
        raise LocalWorkflowError(f"Cannot identify developer journal state: {error}") from error


class DeveloperReadContext:
    """Validated states reusable within one synchronous read-only operation."""

    def __init__(self) -> None:
        self._states = {}
        self.loads = defaultdict(int)
        self.cache_hits = defaultdict(int)
        self.replays = defaultdict(int)
        self.invalidations = defaultdict(int)
        self._verified_digests = defaultdict(list)
        self.digest_cache_hits = 0

    def load(self, name, workspace, root, loader):
        self.loads[name] += 1
        directory = root(workspace)
        identity = _identity(directory)
        cached = self._states.get(name)
        if cached is not None and cached[0] == identity:
            self.cache_hits[name] += 1
            # Keep each caller's load result detached, matching the ordinary
            # _load contract and preventing nested read helpers mutating cache.
            return deepcopy(cached[1])

        self._states.pop(name, None)
        state = loader(workspace)
        verified_identity = _identity(directory)
        if identity != verified_identity:
            raise LocalWorkflowError("Developer journal changed during a scoped read; retry the operation.")
        # The first caller owns the loader result. Keep a detached cache copy so
        # mutation of that return value cannot poison later reads either.
        self._states[name] = (verified_identity, deepcopy(state))
        events = state.get("events", []) if isinstance(state, dict) else []
        self.replays[name] += len(events) if events else (state.get("sequence", 0) if isinstance(state, dict) else 0)
        return state

    def invalidate(self, name=None) -> None:
        """Invalidate one journal or every cached state after a mutation."""
        if name is None:
            for key in tuple(self._states):
                self.invalidations[key] += 1
            self._states.clear()
            return
        self._states.pop(name, None)
        self.invalidations[name] += 1

    def validated_digest(self, value, expected, calculate):
        """Reuse a digest only when a detached snapshot still equals the input."""
        canonical = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        fingerprint = hashlib.sha256(canonical).digest()
        for prior_fingerprint, digest in self._verified_digests.get(expected, ()):
            if prior_fingerprint == fingerprint:
                self.digest_cache_hits += 1
                return digest
        digest = calculate(value)
        if digest == expected:
            self._verified_digests[expected].append((fingerprint, digest))
        return digest

    def summary(self) -> dict:
        return {"loads": dict(self.loads), "cache_hits": dict(self.cache_hits),
            "events_replayed": dict(self.replays), "invalidations": dict(self.invalidations),
            "digest_cache_hits": self.digest_cache_hits}


def operation_scoped_load(name, root):
    """Decorate a module _load while preserving its standalone behavior."""
    def decorate(loader):
        @wraps(loader)
        def wrapped(workspace):
            context = getattr(workspace, "_read_context", None)
            if context is None:
                return loader(workspace)
            return context.load(name, workspace, root, loader)
        return wrapped
    return decorate
