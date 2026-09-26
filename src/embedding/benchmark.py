"""Reproducible benchmark using only generated, non-sensitive Python fixtures."""

import argparse
import json
import os
from pathlib import Path
import platform
import socket
import time
from unittest.mock import patch

import numpy as np

from src.chunker import CodeChunker
from src.models.corpus import RepositoryMetadata
from src.parser import PythonAstParser
from .model import load_model
from .pipeline import EmbeddingPipeline
from .storage import load_artifacts, save_artifacts, write_json


def fixtures(count=128):
    chunks = []
    for i in range(count):
        source = f"def synthetic_{i}(value):\n    return value + {i}\n"
        chunks.append(CodeChunker().chunk_module(
            PythonAstParser().parse(source, f"fixture_{i}.py"), source,
            RepositoryMetadata("synthetic/fixture", "0" * 40),
        )[1])
    return tuple(chunks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    chunks = fixtures()
    pipeline = EmbeddingPipeline(args.cache)
    # Fail any attempted network connection, including during model loading.
    with patch.object(socket.socket, "connect", side_effect=AssertionError("Network prohibited")):
        start = time.perf_counter()
        pipeline._model = load_model(args.cache)
        load_seconds = time.perf_counter() - start
        pipeline._generate_validated(chunks[:8])
        durations, runs = [], []
        for _ in range(3):
            start = time.perf_counter()
            embeddings, rejections = pipeline._generate_validated(chunks)
            durations.append(time.perf_counter() - start)
            runs.append(embeddings)
        if runs[0] != runs[1] or runs[1] != runs[2]:
            raise ValueError("Repeat benchmark output differs")
        start = time.perf_counter()
        manifest = save_artifacts(args.output, embeddings, rejections,
                     batch_size=32, input_count=len(chunks), clearance_sha256="synthetic-only",
                     snapshot_id="synthetic-fixture-v1")
        vectors, metadata, _ = load_artifacts(args.output)
        storage_seconds = time.perf_counter() - start
        np.testing.assert_array_equal(vectors, np.asarray([e.vector for e in embeddings], dtype=np.float32))
    report = {
        "fixture_count": len(chunks), "accepted": len(embeddings), "rejected": len(rejections),
        "model_load_seconds": load_seconds, "generation_seconds": durations,
        "median_chunks_per_second": len(chunks) / float(np.median(durations)),
        "save_and_verify_seconds": storage_seconds, "repeat_identical": True,
        "network_connections_blocked": True, "runtime": manifest,
        "processor": platform.processor(), "logical_cpus": os.cpu_count(),
    }
    write_json(args.output / "benchmark.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "runtime"}, indent=2))


if __name__ == "__main__":
    main()
