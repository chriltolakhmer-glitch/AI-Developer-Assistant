"""Portable float32 matrix plus deterministic JSON provenance and hashes."""

from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import platform

import numpy as np

from .model import DIMENSIONS, MODEL_ID, MODEL_REVISION, MAX_TOKENS, external_path
from .pipeline import digest, validate_vector_matrix


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def save_artifacts(output: Path, embeddings, rejections, *, batch_size: int,
                   input_count: int, clearance_sha256: str, snapshot_id="corpus-snapshot-v1",
                   input_manifest=None):
    output = external_path(output)
    ids = [e.chunk_id for e in embeddings]
    if ids != sorted(set(ids)):
        raise ValueError("Embedding IDs must be unique and sorted")
    if len(embeddings) + len(rejections) != input_count:
        raise ValueError("Input/output counts do not reconcile")
    rejected_ids = [r["chunk_id"] for r in rejections]
    if rejected_ids != sorted(set(rejected_ids)) or set(ids) & set(rejected_ids):
        raise ValueError("Invalid rejection mapping")
    vectors = (np.asarray([e.vector for e in embeddings], dtype=np.float32)
               if ids else np.empty((0, DIMENSIONS), dtype=np.float32))
    validate_vector_matrix(vectors, len(ids))
    if not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-6):
        raise ValueError("Vectors must be normalized before storage")
    output.mkdir(parents=True, exist_ok=False)
    np.save(output / "vectors.npy", vectors, allow_pickle=False)
    write_json(output / "metadata.json", [{"row": i, "chunk_id": e.chunk_id,
               "metadata": asdict(e.metadata)} for i, e in enumerate(embeddings)])
    write_json(output / "rejections.json", rejections)
    manifest = {
        "schema_version": "1.0", "snapshot_id": snapshot_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL_ID, "revision": MODEL_REVISION,
        "dimensions": DIMENSIONS, "dtype": "float32", "normalization": "l2",
        "representation": "source-strip-v1", "chunk_schema": "phase5.3",
        "input_policy": "reject-empty-or-over-256-v1", "max_tokens": MAX_TOKENS,
        "tokenizer": "pinned-model; special tokens included; truncation=false",
        "device": "cpu", "threads": 1, "seed": 0, "deterministic_algorithms": True,
        "batch_size": batch_size, "python": platform.python_version(), "os": platform.platform(),
        "packages": {p: version(p) for p in ("numpy", "torch", "sentence-transformers", "transformers", "tokenizers", "huggingface-hub")},
        "counts": {"input": input_count, "accepted": len(ids), "rejected": len(rejections), "split": 0, "failed": 0},
        "clearance_sha256": clearance_sha256,
        "input_manifest": input_manifest,
        "artifacts": {name: digest((output / name).read_bytes())
                      for name in ("vectors.npy", "metadata.json", "rejections.json")},
    }
    # Written last: absence means an incomplete run, never a valid artifact set.
    write_json(output / "run.json", manifest)
    return manifest


def load_artifacts(output: Path):
    output = external_path(output)
    manifest = json.loads((output / "run.json").read_text(encoding="utf-8"))
    if (manifest["schema_version"] != "1.0" or manifest["model"] != MODEL_ID
            or manifest["revision"] != MODEL_REVISION or manifest["dimensions"] != DIMENSIONS):
        raise ValueError("Unsupported embedding artifact contract")
    for name in ("vectors.npy", "metadata.json", "rejections.json"):
        if digest((output / name).read_bytes()) != manifest["artifacts"][name]:
            raise ValueError("Artifact integrity mismatch")
    vectors = np.load(output / "vectors.npy", allow_pickle=False)
    metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
    rejections = json.loads((output / "rejections.json").read_text(encoding="utf-8"))
    validate_vector_matrix(vectors, len(metadata))
    if vectors.dtype != np.float32 or not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-6):
        raise ValueError("Invalid stored vector dtype or normalization")
    ids = [m["chunk_id"] for m in metadata]
    if ids != sorted(set(ids)) or [m["row"] for m in metadata] != list(range(len(ids))):
        raise ValueError("Invalid row mapping")
    if len(ids) != manifest["counts"]["accepted"]:
        raise ValueError("Invalid artifact count")
    rejected_ids = [r["chunk_id"] for r in rejections]
    if (rejected_ids != sorted(set(rejected_ids)) or set(ids) & set(rejected_ids)
            or len(rejections) != manifest["counts"]["rejected"]
            or len(ids) + len(rejections) != manifest["counts"]["input"]):
        raise ValueError("Invalid rejection count or mapping")
    return vectors, metadata, manifest
