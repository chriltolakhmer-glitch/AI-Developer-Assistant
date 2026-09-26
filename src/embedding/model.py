"""Pinned CPU inference; acquisition is a separate, explicit operation."""

import os
from pathlib import Path

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
DIMENSIONS = 384
MAX_TOKENS = 256
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def external_path(path: Path) -> Path:
    path = Path(path).resolve()
    if path == PROJECT_ROOT or PROJECT_ROOT in path.parents:
        raise ValueError("Research artifacts and model cache must be outside the project")
    return path


def offline_environment() -> None:
    for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "DO_NOT_TRACK"):
        os.environ[name] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"


def load_model(cache: Path):
    """Load only cached, pinned weights; never fall back to network inference."""
    cache = external_path(cache)
    offline_environment()
    import torch
    from sentence_transformers import SentenceTransformer

    torch.manual_seed(0)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    model = SentenceTransformer(
        MODEL_ID, revision=MODEL_REVISION, cache_folder=str(cache),
        local_files_only=True, trust_remote_code=False, device="cpu",
        token=False,
    )
    model.float().eval()
    if model.get_embedding_dimension() != DIMENSIONS or model.max_seq_length != MAX_TOKENS:
        raise ValueError("Cached model does not match the embedding contract")
    return model
