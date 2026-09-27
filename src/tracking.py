"""Lightweight, source-free experiment run tracking."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Iterator, Mapping

import yaml

from src.config import PrototypeConfig


SOFTWARE_VERSION = "0.1.0"
LOGGER = logging.getLogger("prototype")


def configuration_hash(values: Mapping[str, object]) -> str:
    """Hash canonical configuration values, independent of YAML formatting."""
    encoded = json.dumps(dict(values), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def deterministic_run_id(timestamp: datetime, command: str, config_sha256: str) -> str:
    """Build a stable ID for a timestamp, command, and configuration."""
    stamp = timestamp.astimezone(timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = hashlib.sha256(f"{command}\0{config_sha256}".encode()).hexdigest()[:12]
    return f"{stamp}-{suffix}"


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _json_default(value: object) -> str:
    return str(value)


class RunTracker:
    """Create immutable run files and attach structured logging to a command."""

    def __init__(self, config: PrototypeConfig, command: str, arguments: list[str]):
        self.config = config
        self.command = command
        self.arguments = arguments
        self.config_values = config.to_dict()
        self.config_sha256 = configuration_hash(self.config_values)
        timestamp = datetime.now(timezone.utc)
        base = config.data_root / "runs"
        base.mkdir(parents=True, exist_ok=True)
        run_id = deterministic_run_id(timestamp, " ".join(arguments), self.config_sha256)
        run_directory = base / run_id
        counter = 1
        while run_directory.exists():
            run_directory = base / f"{run_id}-{counter}"
            counter += 1
        self.run_id = run_directory.name
        self.directory = run_directory
        self.started_at = timestamp
        self._started = time.perf_counter()

    @property
    def results_path(self) -> Path:
        return self.directory / "results.json"

    def _metadata(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "timestamp": self.started_at.isoformat(),
            "command": self.command,
            "arguments": self.arguments,
            "git_commit_sha": _git_commit(),
            "configuration_hash": self.config_sha256,
            "software_version": SOFTWARE_VERSION,
            "runtime": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "executable": sys.executable,
            },
        }

    @contextmanager
    def execute(self) -> Iterator[None]:
        self.directory.mkdir(parents=True, exist_ok=False)
        (self.directory / "config.yaml").write_text(
            yaml.safe_dump(self.config_values, sort_keys=True), encoding="utf-8", newline="\n"
        )
        handler = logging.FileHandler(self.directory / "logs.txt", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        LOGGER.addHandler(handler)
        LOGGER.setLevel(logging.INFO)
        LOGGER.info("Starting command: %s", self.command)
        try:
            yield
        except Exception:
            LOGGER.exception("Command failed; inspect this run directory for details")
            raise
        finally:
            LOGGER.info("Finished command: %s", self.command)
            handler.close()
            LOGGER.removeHandler(handler)

    def finish(self, payload: Mapping[str, object]) -> dict[str, object]:
        duration = round(time.perf_counter() - self._started, 6)
        metadata = self._metadata()
        metadata["duration_seconds"] = duration
        self.directory.joinpath("metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True, default=_json_default) + "\n",
            encoding="utf-8",
        )
        result = {
            "run_id": self.run_id,
            "configuration_hash": self.config_sha256,
            "software_version": SOFTWARE_VERSION,
            "command": self.command,
            "payload": dict(payload),
        }
        self.results_path.write_text(
            json.dumps(result, indent=2, sort_keys=True, default=_json_default) + "\n",
            encoding="utf-8",
        )
        return result


def load_run(run_root: Path, run_id: str) -> tuple[dict[str, object], dict[str, object]]:
    directory = run_root / run_id
    if not directory.is_dir():
        raise ValueError(
            f"Run '{run_id}' was not found under '{run_root}'. Check PROTOTYPE_DATA_ROOT and the run ID."
        )

    records: dict[str, dict[str, object]] = {}
    for filename in ("metadata.json", "results.json"):
        record_path = directory / filename
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except OSError as error:
            raise ValueError(
                f"Run '{run_id}' is missing or cannot read '{filename}': {error}"
            ) from error
        except (json.JSONDecodeError, UnicodeError) as error:
            raise ValueError(
                f"Run '{run_id}' has invalid '{filename}': {error}"
            ) from error
        if not isinstance(record, dict):
            raise ValueError(
                f"Run '{run_id}' has invalid '{filename}': expected a JSON object"
            )
        records[filename] = record

    metadata = records["metadata.json"]
    results = records["results.json"]
    return metadata, results