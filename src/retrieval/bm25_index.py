"""Snapshot-scoped BM25 corpus and identifier-aware lexical representation."""

from collections import Counter, defaultdict
from dataclasses import asdict
import json
import math
from pathlib import Path
import platform
import re
from types import MappingProxyType
import unicodedata

from src.embedding.model import external_path
from src.embedding.pipeline import digest, validate_chunk
from src.embedding.storage import load_artifacts, write_json
from src.models.chunk import CodeChunk
from .embedding_artifacts import _clearance, _contract, _metadata


TOKENIZER_VERSION = "identifier-components-v1"
SCORING_VERSION = "bm25-positive-idf-v1"
K1 = 1.2
B = 0.75


def tokenize(text: str) -> tuple[str, ...]:
    """Preserve whole casefolded words; add unique components per occurrence."""
    if not isinstance(text, str):
        raise ValueError("Lexical input must be text")
    tokens = []
    for word in re.findall(r"\w+", text, flags=re.UNICODE):
        if not any(character.isalnum() for character in word):
            continue
        expanded = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", word)
        expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", expanded)
        expanded = re.sub(r"([A-Za-z])([0-9])", r"\1 \2", expanded)
        expanded = re.sub(r"([0-9])([A-Za-z])", r"\1 \2", expanded)
        variants = [word.casefold()] + [part.casefold() for part in expanded.replace("_", " ").split()]
        tokens.extend(dict.fromkeys(variants))
    return tuple(tokens)


class BM25Index:
    """Build only the accepted dense inventory, using verified CodeChunk text."""

    @classmethod
    def build(cls, chunks: tuple[CodeChunk, ...], embedding_directory: Path,
              clearance_path: Path, *, repository_id: str, commit_sha: str):
        directory = external_path(embedding_directory)
        run_bytes = (directory / "run.json").read_bytes()
        manifest = json.loads(run_bytes)
        _contract(manifest)
        _clearance(clearance_path, manifest["clearance_sha256"], repository_id, commit_sha)
        _, rows, verified_manifest = load_artifacts(directory)
        if verified_manifest != manifest:
            raise ValueError("Embedding manifest changed while loading")
        selected = [row for row in rows if (row["metadata"]["repository_id"],
                    row["metadata"]["commit_sha"]) == (repository_id, commit_sha)]
        selected = [{**row, "row": i} for i, row in enumerate(selected)]
        if not selected:
            raise ValueError("Snapshot has no accepted embeddings")
        ids, metadata = _metadata(selected, repository_id, commit_sha)
        by_id = {}
        for chunk in chunks:
            if (chunk.repository_id, chunk.commit_sha) != (repository_id, commit_sha):
                raise ValueError("Chunks must belong to the requested snapshot")
            validate_chunk(chunk)
            if chunk.chunk_id in by_id:
                raise ValueError("Duplicate chunk IDs")
            by_id[chunk.chunk_id] = chunk
        if not set(ids).issubset(by_id):
            raise ValueError("Missing accepted chunks; lexical and dense inventories must match")
        documents = tuple(tokenize(by_id[cid].content.strip()) for cid in ids)
        instance = cls._create(ids, metadata, documents)
        instance._embedding_run = manifest
        instance._embedding_run_sha256 = digest(run_bytes)
        return instance

    @classmethod
    def _create(cls, ids, metadata, documents):
        instance = cls()
        instance._ids, instance._metadata, instance._documents = tuple(ids), tuple(metadata), tuple(documents)
        instance._lengths = tuple(len(tokens) for tokens in documents)
        instance._average_length = sum(instance._lengths) / len(ids) if ids else 0.0
        postings = defaultdict(list)
        for row, tokens in enumerate(documents):
            for term, frequency in sorted(Counter(tokens).items()):
                postings[term].append((row, frequency))
        instance._postings = MappingProxyType({term: tuple(values) for term, values in sorted(postings.items())})
        instance._idf = MappingProxyType({term: math.log1p((len(ids) - len(values) + 0.5) / (len(values) + 0.5))
                                         for term, values in instance._postings.items()})
        return instance

    @property
    def count(self) -> int:
        return len(self._ids)

    @property
    def chunk_ids(self) -> tuple[str, ...]:
        return self._ids

    @property
    def tokenized_chunks(self) -> tuple[tuple[str, ...], ...]:
        return self._documents

    @property
    def repository_id(self) -> str:
        return self._metadata[0].repository_id

    @property
    def commit_sha(self) -> str:
        return self._metadata[0].commit_sha

    def save(self, output: Path):
        output = external_path(output)
        output.mkdir(parents=True, exist_ok=False)
        write_json(output / "documents.json", [
            {"row": i, "chunk_id": cid, "metadata": asdict(meta), "tokens": tokens}
            for i, (cid, meta, tokens) in enumerate(zip(self._ids, self._metadata, self._documents))])
        write_json(output / "manifest.json", {
            "schema_version": "1.0", "scoring": SCORING_VERSION, "tokenizer": TOKENIZER_VERSION,
            "k1": K1, "b": B, "query_terms": "sorted-unique", "tie_policy": "score-desc-chunk-id-asc-v1",
            "count": self.count, "repository_id": self.repository_id, "commit_sha": self.commit_sha,
            "python": platform.python_version(), "unicode": unicodedata.unidata_version,
            "embedding_run": self._embedding_run, "embedding_run_sha256": self._embedding_run_sha256,
            "documents_sha256": digest((output / "documents.json").read_bytes()),
        })

    @classmethod
    def load(cls, directory: Path, clearance_path: Path):
        directory = external_path(directory)
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        expected = {"schema_version": "1.0", "scoring": SCORING_VERSION, "tokenizer": TOKENIZER_VERSION,
                    "k1": K1, "b": B, "query_terms": "sorted-unique", "tie_policy": "score-desc-chunk-id-asc-v1",
                    "python": platform.python_version(), "unicode": unicodedata.unidata_version}
        if any(manifest.get(key) != value for key, value in expected.items()):
            raise ValueError("Unsupported BM25 contract or runtime; rebuild the index")
        run = manifest["embedding_run"]
        _contract(run)
        _clearance(clearance_path, run["clearance_sha256"], manifest["repository_id"], manifest["commit_sha"])
        raw = (directory / "documents.json").read_bytes()
        if digest(raw) != manifest["documents_sha256"]:
            raise ValueError("BM25 artifact integrity mismatch")
        rows = json.loads(raw)
        if not rows or len(rows) != manifest["count"]:
            raise ValueError("Invalid BM25 document count")
        ids, metadata = _metadata(rows, manifest["repository_id"], manifest["commit_sha"])
        documents = []
        for row in rows:
            tokens = row["tokens"]
            if not isinstance(tokens, list) or any(not isinstance(t, str) or not t
                    or t != t.casefold() or not all(c.isalnum() or c == "_"
                        or unicodedata.category(c).startswith("M") for c in t)
                    or not any(c.isalnum() for c in t) for t in tokens):
                raise ValueError("Invalid stored lexical tokens")
            documents.append(tuple(tokens))
        instance = cls._create(ids, metadata, tuple(documents))
        instance._embedding_run, instance._embedding_run_sha256 = run, manifest["embedding_run_sha256"]
        return instance
