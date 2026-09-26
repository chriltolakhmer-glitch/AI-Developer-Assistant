"""Controlled download of public model files only; no source inputs accepted."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from .model import MODEL_ID, MODEL_REVISION, external_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", required=True, type=Path)
    args = parser.parse_args()
    cache = external_path(args.cache)
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"
    from huggingface_hub import snapshot_download

    snapshot = Path(snapshot_download(
        MODEL_ID, revision=MODEL_REVISION, cache_dir=str(cache), token=False,
        allow_patterns=["*.json", "vocab.txt", "model.safetensors", "1_Pooling/*"],
    ))
    hashes = {p.relative_to(snapshot).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(snapshot.rglob("*")) if p.is_file()}
    (cache / "acquisition.json").write_text(json.dumps({
        "model": MODEL_ID, "revision": MODEL_REVISION, "sha256": hashes,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Pinned public model acquired; integrity record saved outside Git.")


if __name__ == "__main__":
    main()
