"""Validated configuration for local prototype operations."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Mapping

import yaml


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "default.yaml"
_PACKAGED_DEFAULT_CONFIG_PATH = Path(__file__).with_name("default.yaml")
_SHA1_PATTERN = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
_ENVIRONMENT_KEYS = {
    "PROTOTYPE_DATA_ROOT": "data_root",
    "PROTOTYPE_DEVELOPER_WORKSPACE": "developer_workspace",
    "PROTOTYPE_CORPUS_ROOT": "corpus_root",
    "PROTOTYPE_VALIDATION_OUTPUT": "validation_output",
    "EMBEDDING_MODEL_CACHE": "embedding_model_cache",
    "PROTOTYPE_OFFLINE": "offline",
    "PROTOTYPE_DEVICE": "device",
    "PROTOTYPE_EMBEDDING_MODEL_ID": "embedding_model_id",
    "PROTOTYPE_EMBEDDING_MODEL_REVISION": "embedding_model_revision",
    "PROTOTYPE_EMBEDDING_DIMENSIONS": "embedding_dimensions",
    "PROTOTYPE_MAX_TOKENS": "max_tokens",
    "PROTOTYPE_RETRIEVAL_K": "retrieval_k",
    "PROTOTYPE_RRF_CONSTANT": "rrf_constant",
}


@dataclass(frozen=True, slots=True)
class PrototypeConfig:
    """Runtime settings whose values are safe to expose in run metadata."""

    data_root: Path
    developer_workspace: Path
    corpus_root: Path
    validation_output: Path
    embedding_model_cache: Path
    offline: bool
    device: str
    embedding_model_id: str
    embedding_model_revision: str
    embedding_dimensions: int
    max_tokens: int
    retrieval_k: int
    rrf_constant: int

    def to_dict(self) -> dict[str, object]:
        """Return a YAML/JSON-safe representation for run metadata."""
        return {
            "data_root": str(self.data_root),
            "corpus_root": str(self.corpus_root),
            "validation_output": str(self.validation_output),
            "embedding_model_cache": str(self.embedding_model_cache),
            "offline": self.offline,
            "device": self.device,
            "embedding_model_id": self.embedding_model_id,
            "embedding_model_revision": self.embedding_model_revision,
            "embedding_dimensions": self.embedding_dimensions,
            "max_tokens": self.max_tokens,
            "retrieval_k": self.retrieval_k,
            "rrf_constant": self.rrf_constant,
        }


def _parse_bool(value: object, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.casefold() in {"1", "true", "yes", "on"}:
        return True
    if isinstance(value, str) and value.casefold() in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{field} must be a boolean (true/false)")


def _parse_positive_int(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be a positive integer") from error
    if parsed < 1:
        raise ValueError(f"{field} must be a positive integer")
    return parsed


def _path(value: object, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty path")
    return Path(value).expanduser()


def _expand_templates(values: dict[str, object]) -> None:
    data_root = values.get("data_root")
    if not isinstance(data_root, str):
        return
    for field in ("corpus_root", "validation_output", "embedding_model_cache"):
        value = values.get(field)
        if isinstance(value, str):
            values[field] = value.replace("${data_root}", data_root)


def _validate(values: Mapping[str, object]) -> PrototypeConfig:
    required = {
        "data_root", "developer_workspace", "corpus_root", "validation_output", "embedding_model_cache",
        "offline", "device", "embedding_model_id", "embedding_model_revision",
        "embedding_dimensions", "max_tokens", "retrieval_k", "rrf_constant",
    }
    missing = sorted(required.difference(values))
    if missing:
        raise ValueError(f"Configuration is missing: {', '.join(missing)}")
    device = values["device"]
    model_id = values["embedding_model_id"]
    revision = values["embedding_model_revision"]
    if device != "cpu":
        raise ValueError("device must be 'cpu'; GPU execution is not part of the frozen prototype")
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("embedding_model_id must be non-empty text")
    if not isinstance(revision, str) or not _SHA1_PATTERN.fullmatch(revision):
        raise ValueError("embedding_model_revision must be a full 40-character SHA-1")
    dimensions = _parse_positive_int(values["embedding_dimensions"], "embedding_dimensions")
    max_tokens = _parse_positive_int(values["max_tokens"], "max_tokens")
    if dimensions != 384:
        raise ValueError("embedding_dimensions must remain 384 for the frozen embedding contract")
    if max_tokens != 256:
        raise ValueError("max_tokens must remain 256 for the frozen embedding contract")
    config = PrototypeConfig(
        data_root=_path(values["data_root"], "data_root"),
        developer_workspace=_path(values["developer_workspace"], "developer_workspace"),
        corpus_root=_path(values["corpus_root"], "corpus_root"),
        validation_output=_path(values["validation_output"], "validation_output"),
        embedding_model_cache=_path(values["embedding_model_cache"], "embedding_model_cache"),
        offline=_parse_bool(values["offline"], "offline"),
        device=device,
        embedding_model_id=model_id,
        embedding_model_revision=revision,
        embedding_dimensions=dimensions,
        max_tokens=max_tokens,
        retrieval_k=_parse_positive_int(values["retrieval_k"], "retrieval_k"),
        rrf_constant=_parse_positive_int(values["rrf_constant"], "rrf_constant"),
    )
    developer_root = config.developer_workspace.resolve()
    for research_root in (
        config.data_root,
        config.corpus_root,
        config.validation_output,
        config.embedding_model_cache,
    ):
        resolved_research = research_root.resolve()
        if (developer_root == resolved_research
                or developer_root in resolved_research.parents
                or resolved_research in developer_root.parents):
            raise ValueError(
                "developer_workspace must be separate from research storage; "
                f"'{config.developer_workspace}' overlaps '{research_root}'. "
                "Set PROTOTYPE_DEVELOPER_WORKSPACE to a separate directory."
            )
    return config


def load_config(
    path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> PrototypeConfig:
    """Load YAML defaults, then apply supported environment overrides."""
    if path is not None:
        config_path = Path(path).expanduser()
    elif _DEFAULT_CONFIG_PATH.is_file():
        config_path = _DEFAULT_CONFIG_PATH
    else:
        config_path = _PACKAGED_DEFAULT_CONFIG_PATH
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as error:
        detail = error.strerror or str(error)
        raise ValueError(f"Cannot read configuration file '{config_path}': {detail}") from error
    except yaml.YAMLError as error:
        raise ValueError(f"Cannot parse YAML configuration file '{config_path}': {error}") from error
    if not isinstance(raw, dict):
        raise ValueError(
            f"Configuration file '{config_path}' must contain a YAML mapping at its top level"
        )
    values = dict(raw)
    # Preserve compatibility with pre-Phase-28 custom configuration files.
    values.setdefault("developer_workspace", "~/.prototype/developer-workspace")
    environment = os.environ if environ is None else environ
    for environment_key, field in _ENVIRONMENT_KEYS.items():
        if environment_key in environment:
            values[field] = environment[environment_key]
    _expand_templates(values)
    return _validate(values)


__all__ = ["PrototypeConfig", "load_config"]