"""Personal local-only scan, parse, index, and query workflows.

All source-derived outputs belong under a dedicated developer workspace. This
module deliberately does not invoke research validation, benchmark, clearance,
or experiment-tracking workflows.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, replace
import hashlib
import io
from importlib.metadata import version
import json
import os
import ast
from pathlib import Path, PurePosixPath
import platform
import subprocess
import tempfile
import tokenize as python_tokenize
from typing import Any

import faiss
import numpy as np

from src.chunker import CodeChunker
from src.embedding.model import MODEL_ID, MODEL_REVISION, load_model
from src.embedding.pipeline import validate_vector_matrix
from src.models.chunk import CodeChunk
from src.models.corpus import CorpusManifest, RepositoryMetadata
from src.models.embedding import Embedding, EmbeddingMetadata
from src.parser import ParserError, PythonAstParser
from src.retrieval.bm25_index import BM25Index, SCORING_VERSION, TOKENIZER_VERSION, tokenize
from src.retrieval.bm25_search import BM25Search
from src.retrieval.embedding_artifacts import _metadata
from src.retrieval.rrf import CANDIDATE_WINDOW, fuse_rankings
from src.retrieval.vector_index import VectorIndex
from src.scanner import RepositoryScanner


DEVELOPER_MODE_NOTICE = "This is a local developer workspace. Results are not benchmark results."
_INDEX_SCHEMA = "developer-local-index-v2"
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_IGNORED_DIRECTORIES = frozenset(
    {".git", ".venv", "venv", "__pycache__", "site-packages", "build", "dist",
     "vendor", "vendors", "third_party", "generated", "fixtures", "testdata"}
)


class LocalWorkflowError(ValueError):
    """An actionable developer workflow or storage-isolation error."""


@dataclass(frozen=True, slots=True)
class LocalFile:
    relative_path: str
    absolute_path: Path
    content_sha256: str
    size_bytes: int
    code_loc: int


@dataclass(frozen=True, slots=True)
class LocalInventory:
    root: Path
    repository_id: str
    commit_sha: str
    snapshot_id: str
    files: tuple[LocalFile, ...]
    code_loc: int
    unsupported_extensions: tuple[tuple[str, int], ...]
    excluded_python_count: int
    tracked_file_count: int
    file_decisions: tuple[dict[str, Any], ...] = ()

    def summary(self) -> dict[str, Any]:
        return {
            "repository_id": self.repository_id,
            "repository_path": str(self.root),
            "commit_sha": self.commit_sha,
            "working_tree_sha256": self.snapshot_id,
            "tracked_file_count": self.tracked_file_count,
            "eligible_python_file_count": len(self.files),
            "eligible_python_code_loc": self.code_loc,
            "excluded_python_file_count": self.excluded_python_count,
            "unsupported_extensions": dict(self.unsupported_extensions),
            "files_scanned": self.tracked_file_count,
            "files_included": len(self.files),
            "files_excluded": self.tracked_file_count - len(self.files),
            "file_scope": "Git tracked and nonignored untracked paths; ignored untracked files are not enumerated",
            "supported_languages": ["python"],
        }


@dataclass(frozen=True, slots=True)
class ParsedLocalCode:
    inventory: LocalInventory
    chunks: tuple[CodeChunk, ...]
    parse_failures: tuple[dict[str, Any], ...]
    context: dict[str, dict[str, Any]]


@dataclass(frozen=True, slots=True)
class DeveloperIndex:
    """Loaded developer-only dense and lexical indexes."""

    path: Path
    manifest: dict[str, Any]
    dense: VectorIndex
    lexical: BM25Index
    context: dict[str, dict[str, Any]]

    @classmethod
    def load(cls, path: Path) -> DeveloperIndex:
        path = Path(path).resolve(strict=True)
        try:
            for name in ("manifest.json", "documents.json", "vectors.npy", "state.json"):
                if path not in (path / name).resolve().parents:
                    raise LocalWorkflowError(f"Index artifact '{name}' resolves outside the developer index. Choose a new workspace.")
            manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
            if manifest.get("schema_version") != _INDEX_SCHEMA or manifest.get("mode") != "developer-local":
                raise LocalWorkflowError(
                    f"Unsupported developer index at '{path}'. Rebuild it with prototype local index."
                )
            expected_runtime = {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "faiss": version("faiss-cpu"),
                "tokenizer": TOKENIZER_VERSION,
                "scoring": SCORING_VERSION,
                "model": MODEL_ID,
                "model_revision": MODEL_REVISION,
            }
            if manifest.get("runtime") != expected_runtime:
                raise LocalWorkflowError(
                    "This local index uses a different Python, retrieval, or model contract; "
                    "rebuild it with prototype local index."
                )
            document_bytes = (path / "documents.json").read_bytes()
            vector_bytes = (path / "vectors.npy").read_bytes()
            state_bytes = (path / "state.json").read_bytes()
            hashes = manifest.get("artifacts", {})
            if (hashes.get("documents.json") != _digest(document_bytes)
                    or hashes.get("vectors.npy") != _digest(vector_bytes)
                    or hashes.get("state.json") != _digest(state_bytes)):
                raise LocalWorkflowError(f"Local index integrity check failed at '{path}'. Rebuild the index.")
            rows = json.loads(document_bytes)
            if not isinstance(rows, list) or not rows:
                raise LocalWorkflowError(f"Local index at '{path}' contains no searchable chunks.")
            ids, metadata = _metadata(rows, manifest["repository_id"], manifest["commit_sha"])
            documents = tuple(tuple(row["tokens"]) for row in rows)
            for tokens in documents:
                if any(not isinstance(token, str) or not token or token != token.casefold()
                       for token in tokens):
                    raise LocalWorkflowError(f"Local index token data is invalid at '{path}'. Rebuild the index.")
            vectors = np.load(io.BytesIO(vector_bytes), allow_pickle=False)
            if (vectors.shape != (len(ids), 384) or vectors.dtype != np.float32
                    or not np.isfinite(vectors).all()
                    or not np.allclose(np.linalg.norm(vectors, axis=1), 1, rtol=0, atol=1e-6)):
                raise LocalWorkflowError(f"Local vectors are invalid at '{path}'. Rebuild the index.")
            vector_rows = [
                {"row": row, "chunk_id": chunk_id, "metadata": asdict(item)}
                for row, (chunk_id, item) in enumerate(zip(ids, metadata))
            ]
            dense = VectorIndex._create(vectors, vector_rows, manifest["repository_id"], manifest["commit_sha"])
            lexical = BM25Index._create(ids, metadata, documents)
            state = json.loads(state_bytes)
            context = state.get("context", {})
            if not isinstance(context, dict):
                raise LocalWorkflowError(f"Developer context metadata is invalid at '{path}'. Rebuild the index.")
            content_hashes = {
                row["chunk_id"]: hashlib.sha256(row["content"].encode("utf-8")).hexdigest()
                for row in state.get("chunks", []) if isinstance(row.get("content"), str)
            }
            context = {
                chunk_id: {**details, "content_sha256": details.get("content_sha256", content_hashes.get(chunk_id))}
                for chunk_id, details in context.items()
            }
            return cls(path, manifest, dense, lexical, context)
        except LocalWorkflowError:
            raise
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise LocalWorkflowError(
                f"Cannot load developer index at '{path}': {error}. "
                "Run prototype local index <repository> again."
            ) from error

    def query(self, question: str, top_k: int, model_cache: Path):
        if not isinstance(question, str) or not question.strip():
            raise LocalWorkflowError("Question must be nonempty text.")
        if type(top_k) is not int or not 1 <= top_k <= CANDIDATE_WINDOW:
            raise LocalWorkflowError(f"top-k must be an integer from 1 to {CANDIDATE_WINDOW}.")
        try:
            model = load_model(model_cache)
        except Exception as error:
            raise LocalWorkflowError(
                f"The pinned local model is unavailable in '{model_cache}'. Acquire it explicitly with "
                f"python -m src.embedding.acquire --cache \"{model_cache}\". Details: {error}"
            ) from error
        text = question.strip()
        count = len(model.tokenizer(text, add_special_tokens=True, truncation=False,
                                    padding=False, verbose=False)["input_ids"])
        if count > 256:
            raise LocalWorkflowError("Question exceeds the 256-token local model limit; shorten it and retry.")
        vectors = model.encode([text], batch_size=32, show_progress_bar=False,
                               convert_to_numpy=True, normalize_embeddings=False)
        query_vector = validate_vector_matrix(vectors, 1)[0]
        dense_results = self.dense.search(query_vector, k=CANDIDATE_WINDOW)
        lexical_results = BM25Search(self.lexical).search(text, k=CANDIDATE_WINDOW)
        from .ranking import rank_developer_results
        return rank_developer_results(text, dense_results, lexical_results, top_k, self.context)


def _normalized_name(value: str) -> str:
    return "".join(character.casefold() for character in value if character.isalnum())


def _confidence(signals: list[str]) -> str:
    if "exact_symbol_match" in signals and (
        {"lexical_match", "semantic_match"} <= set(signals)
        or any(signal.endswith("_relationship") for signal in signals)
    ):
        return "high"
    if signals and ("exact_symbol_match" in signals or any(
        signal.endswith("_relationship") for signal in signals
    )):
        return "medium"
    return "low"


def _result_explanation(question: str, row: dict[str, Any]) -> dict[str, Any]:
    details = row.get("developer_context", {})
    reason = row.get("ranking_reason", {})
    query_name = _normalized_name(question)
    symbol_name = row.get("qualified_name", "")
    normalized_symbol = _normalized_name(symbol_name)
    signals: list[str] = []
    if normalized_symbol and normalized_symbol in query_name:
        signals.append("exact_symbol_match")
    if reason.get("matched_metadata_terms"):
        signals.append("related_metadata_terms")
    channels = {item.get("channel") for item in row.get("contributions", [])}
    if "bm25" in channels:
        signals.append("lexical_match")
    if "dense" in channels:
        signals.append("semantic_match")
    edges = details.get("relationship_edges", [])
    relationship_path = [
        {"from": symbol_name, "to": edge.get("symbol"), "kind": edge.get("kind"),
         "file": edge.get("file_path")}
        for edge in edges if edge.get("symbol")
    ]
    for edge in relationship_path:
        if edge["kind"] not in signals:
            signals.append(edge["kind"])
    factors = []
    if "exact_symbol_match" in signals:
        factors.append("symbol_exact_match")
    if reason.get("matched_metadata_terms"):
        factors.append("symbol_or_path_term_match")
    if reason.get("test_factor", 1) < 1:
        factors.append("non_test_preference")
    if reason.get("container_factor", 1) < 1:
        factors.append("definition_container_preference")
    if reason.get("diversity_factor", 1) < 1:
        factors.append("file_diversity")
    if "bm25" in channels:
        factors.append("lexical_candidate_match")
    if "dense" in channels:
        factors.append("semantic_candidate_match")
    if not factors:
        factors.append("base_retrieval_order")
    limitations = []
    if not any(edge["kind"] in {"call_relationship", "caller_relationship"} for edge in relationship_path):
        limitations.append("caller_relationship_unknown")
    if not any(edge["kind"] in {"import_relationship", "importer_relationship"} for edge in relationship_path):
        limitations.append("import_relationship_not_observed")
    return {
        "match_reasons": signals.copy(),
        "relationship_path": relationship_path,
        "ranking_factors": factors,
        "context_expansion_reason": reason.get("context_expansion_reason", "direct retrieval result"),
        "confidence": _confidence(signals),
        "confidence_signals": signals,
        "limitations": limitations,
    }


def _compare_retrievals(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    previous_rows = {row["chunk_id"]: row for row in previous.get("results", [])}
    current_rows = {row["chunk_id"]: row for row in current.get("results", [])}
    previous_files = {row.get("file_path") for row in previous_rows.values()}
    current_files = {row.get("file_path") for row in current_rows.values()}
    rank_changes = []
    explanation_changes = []
    for chunk_id in sorted(previous_rows.keys() & current_rows.keys()):
        old, new = previous_rows[chunk_id], current_rows[chunk_id]
        if old.get("rank") != new.get("rank"):
            rank_changes.append({"chunk_id": chunk_id, "symbol": new.get("qualified_name"),
                                 "file": new.get("file_path"), "previous_rank": old.get("rank"),
                                 "current_rank": new.get("rank")})
        old_explanation = {"ranking_reason": old.get("ranking_reason"),
                           "explanation": old.get("explanation"),
                           "related_context": old.get("related_context", [])}
        new_explanation = {"ranking_reason": new.get("ranking_reason"),
                           "explanation": new.get("explanation"),
                           "related_context": new.get("related_context", [])}
        if old_explanation != new_explanation:
            explanation_changes.append({"chunk_id": chunk_id, "symbol": new.get("qualified_name"),
                                        "file": new.get("file_path"), "previous": old_explanation,
                                        "current": new_explanation})
    return {
        "status": "compared",
        "previous_run_id": previous.get("run_id"),
        "current_run_id": current.get("run_id"),
        "added_files": sorted(current_files - previous_files),
        "removed_files": sorted(previous_files - current_files),
        "ranking_changes": rank_changes,
        "added_results": sorted(current_rows.keys() - previous_rows.keys()),
        "removed_results": sorted(previous_rows.keys() - current_rows.keys()),
        "explanation_changes": explanation_changes,
        "note": "Descriptive comparison only; no quality score is computed.",
    }


class DeveloperWorkspace:
    """Create per-repository indexes and run records under a personal workspace."""

    def __init__(self, root: Path, research_roots: tuple[Path, ...] = ()) -> None:
        self.root = Path(root).expanduser().resolve(strict=False)
        self.research_roots = tuple(Path(item).expanduser().resolve(strict=False) for item in research_roots)

    def _prepare(self, repository: Path | None = None) -> None:
        if _overlaps(self.root, _PROJECT_ROOT):
            raise LocalWorkflowError(
                f"Developer workspace '{self.root}' must be outside the prototype checkout '{_PROJECT_ROOT}'. "
                "Choose a separate writable directory with --workspace or PROTOTYPE_DEVELOPER_WORKSPACE."
            )
        self._assert_isolated(self.root, self.research_roots, "Developer workspace")
        if repository is not None:
            self._assert_isolated(self.root, (repository,), "Developer workspace")
            self._assert_isolated(repository, self.research_roots, "Repository")
        try:
            if self.root.exists() and not self.root.is_dir():
                raise LocalWorkflowError(f"Developer workspace is not a directory: '{self.root}'. Choose --workspace PATH.")
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            for name in ("indexes", "runs", "model-cache", "tmp"):
                self._contained(self.root / name)
                (self.root / name).mkdir(exist_ok=True)
            for name in ("indexes", "runs", "model-cache"):
                for directory, dirs, files in os.walk(self.root / name, followlinks=False):
                    for child in dirs + files:
                        self._contained(Path(directory) / child)
            # Test actual write permission, rather than trusting os.access/ACL hints.
            with tempfile.TemporaryFile(dir=self.root / "tmp"):
                pass
        except OSError as error:
            raise LocalWorkflowError(
                f"Cannot create developer workspace '{self.root}': {error}. "
                "Check directory permissions and free space, or choose a writable local directory "
                "with --workspace or PROTOTYPE_DEVELOPER_WORKSPACE. Existing ACLs are not changed automatically."
            ) from error

    def _contained(self, path: Path) -> Path:
        resolved = path.resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise LocalWorkflowError(f"Workspace path '{path}' resolves outside '{self.root}'. Remove the redirected path or choose a new workspace.")
        return path

    def _indexes(self, inventory: LocalInventory) -> Path:
        # Leave Phase 28/29 snapshots intact; new contracts have a separate namespace.
        return self._contained(self.root / "indexes" / _safe_component(inventory.repository_id) / "v2")

    def inspect(self, repository: Path, changes: bool = False) -> dict[str, Any]:
        root = _resolve_repository_argument(repository)
        self._prepare(root)
        parsed = parse_local_repository(root)
        warning = None
        try:
            tokenizer = load_model(self.root / "model-cache").tokenizer
        except Exception:
            tokenizer = None
            warning = "Pinned local tokenizer unavailable: token limits are unknown. No model is downloaded; acquire the developer model cache to check exact coverage."
        details = []
        indexed_ids = set()
        active_current = False
        active_path = self._indexes(parsed.inventory) / "active.json"
        if active_path.exists():
            active = self._read_active(active_path.parent)
            active_current = active == parsed.inventory.snapshot_id
            index_path = self._contained(active_path.parent / active)
            DeveloperIndex.load(index_path)
            if active_current:
                indexed_ids = {row["chunk_id"] for row in json.loads((index_path / "documents.json").read_text(encoding="utf-8"))}
        for chunk in parsed.chunks:
            text = chunk.content.strip()
            count = None if tokenizer is None else len(tokenizer(text, add_special_tokens=True, truncation=False, padding=False, verbose=False)["input_ids"])
            reason = "empty" if not text else "unknown" if count is None else "over_limit" if count > 256 else "eligible"
            details.append({"chunk_id": chunk.chunk_id, "file_path": chunk.file_path,
                            "qualified_name": chunk.qualified_name, "start_line": chunk.start_line,
                            "end_line": chunk.end_line, "token_count": count, "reason": reason,
                            "in_current_index": chunk.chunk_id in indexed_ids})
        counts = Counter(item["reason"] for item in details)
        payload = {"status": "completed", "mode": "developer-local", "repository": parsed.inventory.summary(),
                   "files": list(parsed.inventory.file_decisions), "generated_chunk_count": len(parsed.chunks),
                   "chunk_counts": {key: counts[key] for key in ("eligible", "empty", "over_limit", "unknown")}, "chunks": details,
                   "parse_failure_count": len(parsed.parse_failures),
                   "skipped_chunk_count": counts["empty"] + counts["over_limit"],
                   "parse_failures": list(parsed.parse_failures), "warning": warning,
                   "active_index_current": active_current, "searchable_chunk_count": len(indexed_ids),
                   "coverage_note": "Eligibility describes current source, not a guarantee that an active index is current."}
        if changes:
            previous_hashes: dict[str, str] = {}
            previous_chunks: tuple[dict[str, Any], ...] = ()
            if active_path.exists():
                try:
                    active = self._read_active(active_path.parent)
                    state = json.loads((active_path.parent / active / "state.json").read_text(encoding="utf-8"))
                    previous_hashes = state.get("file_hashes", {})
                    previous_chunks = tuple(state.get("chunks", ()))
                except (OSError, ValueError, json.JSONDecodeError):
                    pass
            current_hashes = {item.relative_path: item.content_sha256 for item in parsed.inventory.files}
            added = sorted(set(current_hashes) - set(previous_hashes))
            deleted = sorted(set(previous_hashes) - set(current_hashes))
            modified = sorted(name for name in set(current_hashes) & set(previous_hashes)
                              if current_hashes[name] != previous_hashes[name])
            changed_names = set(added + modified + deleted)
            current_symbols = {item["qualified_name"] for item in payload["chunks"] if item["in_current_index"]}
            old_symbols = {item["qualified_name"] for item in previous_chunks if item.get("file_path") in changed_names}
            payload["changes"] = {
                "changed_files": len(changed_names),
                "added_files": added,
                "modified_files": modified,
                "deleted_files": deleted,
                "reindexed_files": len(added) + len(modified),
                "unchanged_files": len(set(current_hashes) - set(added) - set(modified)),
                "stale_symbols": len(old_symbols - current_symbols),
                "reasons": {name: "added" for name in added} | {name: "modified" for name in modified} | {name: "deleted" for name in deleted},
            }
        payload["run_id"] = self._record_run("inspect", parsed.inventory, payload)
        return payload

    @staticmethod
    def _assert_isolated(path: Path, other_roots: tuple[Path, ...], label: str) -> None:
        for other in other_roots:
            if _overlaps(path, other):
                raise LocalWorkflowError(
                    f"{label} '{path}' overlaps protected storage '{other}'. "
                    "Keep developer indexes, model cache, and runs in a separate directory; "
                    "set PROTOTYPE_DEVELOPER_WORKSPACE or pass --workspace."
                )

    def scan(self, repository: Path) -> dict[str, Any]:
        root = _resolve_repository_argument(repository)
        self._prepare(root)
        inventory = scan_local_repository(root)
        payload: dict[str, Any] = {
            "status": "completed", "mode": "developer-local", "scan": inventory.summary(),
        }
        payload["run_id"] = self._record_run("scan", inventory, payload)
        return payload

    def index(self, repository: Path) -> dict[str, Any]:
        root = _resolve_repository_argument(repository)
        self._prepare(root)
        inventory = scan_local_repository(root)
        if not inventory.files:
            raise LocalWorkflowError("No Python chunks could be indexed: no eligible .py files. Only Python is supported; run prototype local inspect PATH for exclusions.")
        repo_indexes = self._indexes(inventory)
        destination = self._contained(repo_indexes / inventory.snapshot_id)
        reused_files = 0
        reused_chunks = 0
        removed_files = 0
        changed_files: list[str] = []
        rebuild_reasons: dict[str, str] = {}
        stale_symbol_count = 0
        if destination.exists():
            existing = DeveloperIndex.load(destination)
            state = json.loads((destination / "state.json").read_text(encoding="utf-8"))
            parsed = ParsedLocalCode(inventory, tuple(CodeChunk(**c) for c in state["chunks"]), tuple(state["parse_failures"]), state.get("context", {}))
            rejections = tuple(state["rejections"])
            indexed_count = existing.manifest["indexed_chunk_count"]
            reused_files, reused_chunks = len(inventory.files), indexed_count
            index_status = "already indexed"
            unchanged_file_count = len(inventory.files)
        else:
            reused_embeddings = []
            cached_chunks = []
            cached_failures = []
            cached_rejections = []
            cached_context = {}
            unchanged = set()
            if (repo_indexes / "active.json").exists():
                previous_path = self._contained(repo_indexes / self._read_active(repo_indexes))
                previous = DeveloperIndex.load(previous_path)
                old_state = json.loads((previous_path / "state.json").read_text(encoding="utf-8"))
                cached_context = old_state.get("context", {})
                current_files = {f.relative_path: f.content_sha256 for f in inventory.files}
                removed_files = len(set(old_state["file_hashes"]) - set(current_files))
                changed_files = sorted(name for name in set(current_files) | set(old_state["file_hashes"])
                                       if current_files.get(name) != old_state["file_hashes"].get(name))
                rebuild_reasons = {name: ("added" if name not in old_state["file_hashes"] else
                                   "deleted" if name not in current_files else "content changed")
                                   for name in changed_files}
                # Chunk IDs bind the commit; a new commit gets a full rebuild.
                if previous.manifest["commit_sha"] == inventory.commit_sha:
                    unchanged = {name for name, digest in current_files.items() if old_state["file_hashes"].get(name) == digest}
                    cached_chunks = [CodeChunk(**c) for c in old_state["chunks"] if c["file_path"] in unchanged]
                    cached_failures = [f for f in old_state["parse_failures"] if f["file_path"] in unchanged]
                    cached_ids = {c.chunk_id for c in cached_chunks}
                    cached_rejections = [r for r in old_state["rejections"] if r["chunk_id"] in cached_ids]
                    rows = json.loads((previous_path / "documents.json").read_text(encoding="utf-8"))
                    vectors = np.load(previous_path / "vectors.npy", allow_pickle=False)
                    for row, vector in zip(rows, vectors):
                        if row["chunk_id"] in cached_ids:
                            reused_embeddings.append(Embedding(row["chunk_id"], tuple(float(v) for v in vector), EmbeddingMetadata(**row["metadata"])))
            changed = replace(inventory, files=tuple(f for f in inventory.files if f.relative_path not in unchanged))
            fresh = _parse_inventory(changed)
            parsed = ParsedLocalCode(inventory, tuple(sorted(cached_chunks + list(fresh.chunks), key=lambda c: c.chunk_id)),
                                     tuple(sorted(cached_failures + list(fresh.parse_failures), key=lambda f: f["file_path"])),
                                     {**{chunk_id: cached_context[chunk_id] for chunk_id in cached_context
                                         if chunk_id in {chunk.chunk_id for chunk in cached_chunks}}, **fresh.context})
            stale_symbol_count = len({chunk.qualified_name for chunk in cached_chunks if chunk.file_path in changed_files} -
                                     {chunk.qualified_name for chunk in parsed.chunks if chunk.file_path in changed_files})
            try:
                if fresh.chunks:
                    new_embeddings, new_rejections = _embed_developer_chunks(fresh.chunks, self.root / "model-cache")
                else:
                    new_embeddings, new_rejections = (), ()
            except Exception as error:
                raise LocalWorkflowError(f"Could not index with the pinned local model: {error}. Check WORKSPACE/model-cache; run prototype local inspect PATH for coverage.") from error
            embeddings = tuple(reused_embeddings) + tuple(new_embeddings)
            rejections = tuple(sorted(tuple(cached_rejections) + tuple(new_rejections), key=lambda row: row["chunk_id"]))
            if not embeddings:
                raise LocalWorkflowError("No searchable Python chunks remain. Run prototype local inspect PATH for parser failures, empty chunks and the 256-token limit.")
            # Do not publish mixed source snapshots if files changed while parsing/embedding.
            if scan_local_repository(root).snapshot_id != inventory.snapshot_id:
                raise LocalWorkflowError("Repository changed during indexing; no index was published. Retry when edits have finished.")
            self._write_index(destination, parsed, embeddings, rejections)
            indexed_count = len(embeddings)
            reused_files, reused_chunks = len(unchanged), len(reused_embeddings)
            index_status = "indexed"
            unchanged_file_count = len(unchanged)
        _write_json(self._contained(repo_indexes / "active.json"), {"snapshot_id": inventory.snapshot_id})
        payload = {
            "status": "completed", "mode": "developer-local", "index_status": index_status,
            "index_path": str(destination), "repository": inventory.summary(),
            "parsed_python_file_count": len(inventory.files) - len(parsed.parse_failures),
            "parse_failure_count": len(parsed.parse_failures), "parse_failures": list(parsed.parse_failures),
            "chunk_count": len(parsed.chunks), "indexed_chunk_count": indexed_count,
            "rejected_chunk_count": len(rejections), "rejections": sorted({r["reason"] for r in rejections}),
            "reused_file_count": reused_files, "rebuilt_file_count": len(inventory.files) - reused_files,
            "reused_chunk_count": reused_chunks, "rebuilt_chunk_count": indexed_count - reused_chunks,
            "removed_file_count": removed_files,
            "cache_reuse": index_status == "already indexed",
            "changed_files": changed_files,
            "rebuild_reasons": rebuild_reasons,
            "reindexed_file_count": len([name for name in changed_files if name in {item.relative_path for item in inventory.files}]),
            "unchanged_file_count": unchanged_file_count,
            "stale_symbol_count": stale_symbol_count,
        }
        payload["run_id"] = self._record_run("index", inventory, payload)
        return payload

    def query(self, question: str, repository: Path | None = None, top_k: int = 10) -> dict[str, Any]:
        self._prepare()
        if repository is not None:
            root = _resolve_repository_argument(repository)
            self._prepare(root)
            inventory = scan_local_repository(root)
            if not inventory.files:
                raise LocalWorkflowError("No eligible Python files: this repository cannot be queried. Run prototype local inspect PATH to see exclusions; supported language: Python only.")
            repo_indexes = self._indexes(inventory)
            active = self._read_active(repo_indexes)
        else:
            active_files = sorted((self.root / "indexes").glob("*/v2/active.json"))
            if not active_files:
                raise LocalWorkflowError(
                    f"No developer index exists under '{self.root / 'indexes'}'. "
                    "Run prototype local index <repository> first."
                )
            if len(active_files) > 1:
                raise LocalWorkflowError(
                    "More than one local repository has an active index. Pass --repository PATH to select one."
                )
            repo_indexes = active_files[0].parent
            active = self._read_active(repo_indexes)
        index = DeveloperIndex.load(self._contained(repo_indexes / active))
        indexed_root = _resolve_repository_argument(Path(index.manifest["repository_path"]))
        self._prepare(indexed_root)
        current = scan_local_repository(indexed_root)
        if current.snapshot_id != index.manifest.get("working_tree_sha256"):
            raise LocalWorkflowError(
                f"Repository '{indexed_root}' changed after indexing. Rebuild it with "
                f"prototype local index \"{indexed_root}\" before querying."
            )
        if repository is not None and current.repository_id != index.manifest.get("repository_id"):
            raise LocalWorkflowError(
                f"No index matches repository '{current.root}'. Run prototype local index \"{current.root}\" first."
            )
        results = index.query(question, top_k, self.root / "model-cache")
        result_rows = results
        for row in result_rows:
            row["explanation"] = _result_explanation(question, row)
            row["ranking_reason"]["index_freshness"] = "current"
        payload: dict[str, Any] = {
            "status": "completed",
            "mode": "developer-local",
            "repository": current.summary(),
            "question": question,
            "top_k": top_k,
            "results": result_rows,
            "index_freshness": {"status": "current", "working_tree_sha256": current.snapshot_id},
            "confidence": {
                "level": result_rows[0]["explanation"]["confidence"] if result_rows else "low",
                "signals": result_rows[0]["explanation"]["confidence_signals"] if result_rows else [],
                "limitations": sorted({
                    limitation for row in result_rows
                    for limitation in row["explanation"]["limitations"]
                }) + (["no_results_returned"] if not result_rows else []),
                "basis": "observed local retrieval and static index evidence; not an answer-quality score",
            },
        }
        grouped: dict[str, dict[str, Any]] = {}
        for row in result_rows:
            file_group = grouped.setdefault(row["file_path"], {"file_path": row["file_path"], "symbols": [], "results": []})
            if row["qualified_name"] not in file_group["symbols"]:
                file_group["symbols"].append(row["qualified_name"])
            if row["chunk_id"] not in file_group["results"]:
                file_group["results"].append(row["chunk_id"])
            for related in row.get("related_context", []):
                related_path = related.get("file_path")
                related_symbol = related.get("symbol_name")
                related_id = related.get("chunk_id")
                if not related_path or not related_symbol or not related_id:
                    continue
                related_group = grouped.setdefault(related_path, {
                    "file_path": related_path, "symbols": [], "results": [], "expansion_reasons": [],
                })
                if related_symbol not in related_group["symbols"]:
                    related_group["symbols"].append(related_symbol)
                if related_id not in related_group["results"]:
                    related_group["results"].append(related_id)
                if related["reason"] not in related_group.setdefault("expansion_reasons", []):
                    related_group["expansion_reasons"].append(related["reason"])
        payload["context"] = {
            "files": list(grouped.values()),
            "expansion_decisions": [
                {"chunk_id": row["chunk_id"], "reason": row["ranking_reason"]["context_expansion_reason"],
                 "related_chunk_ids": [item["chunk_id"] for item in row.get("related_context", [])]}
                for row in result_rows
            ],
            "suppressed_duplicates": [
                {"selected_chunk_id": row["chunk_id"], **duplicate}
                for row in result_rows
                for duplicate in row["ranking_reason"].get("duplicate_suppressed", [])
            ],
            "excluded_context": "Overlapping source ranges and duplicate file ranges are omitted from the selected context.",
        }
        payload["run_id"] = self._record_run("query", current, payload)
        from .observability import record_retrieval
        record_retrieval(self, payload, current, index, "query", top_k)
        return payload

    def _previous_retrieval(self, question: str, repository: Path | None) -> dict[str, Any] | None:
        repository_path = None if repository is None else str(_resolve_repository_argument(repository))
        candidates = []
        for directory in (self.root / "runs").glob("*"):
            try:
                self._contained(directory)
                metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
                if (metadata.get("mode") != "developer-local"
                        or metadata.get("command") not in {"query", "trace"}
                        or (repository_path is not None and metadata.get("repository_path") != repository_path)):
                    continue
                results = json.loads((directory / "results.json").read_text(encoding="utf-8"))
                if results.get("question", "").strip() != question.strip():
                    continue
                results["run_id"] = metadata.get("run_id", directory.name)
                candidates.append((directory.stat().st_mtime_ns, results))
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return max(candidates, default=(0, None), key=lambda item: item[0])[1]

    def compare(self, question: str, repository: Path | None = None, top_k: int = 10) -> dict[str, Any]:
        """Compare current developer retrieval with its prior local record."""
        self._prepare()
        previous = self._previous_retrieval(question, repository)
        current = self.query(question, repository, top_k)
        comparison = ({"status": "no_previous_retrieval", "previous_run_id": None,
                       "current_run_id": current["run_id"], "added_files": [], "removed_files": [],
                       "ranking_changes": [], "added_results": [], "removed_results": [],
                       "explanation_changes": [],
                       "note": "Run this query again later to compare it with a future retrieval; no quality score is computed."}
                      if previous is None else _compare_retrievals(previous, current))
        inventory = scan_local_repository(Path(current["repository"]["repository_path"]))
        payload = {"status": "completed", "mode": "developer-local-retrieval-comparison",
                   "question": question, "current": current, "comparison": comparison}
        payload["run_id"] = self._record_run("compare", inventory, payload)
        return payload

    def analyze_context(
        self, question: str, repository: Path | None = None, top_k: int = 10,
        cases_path: Path | None = None, case_id: str | None = None,
    ) -> dict[str, Any]:
        """Summarize selected, missing, extra, and deduplicated local context."""
        current = self.query(question, repository, top_k)
        selected_files = current["context"]["files"]
        expected: dict[str, Any] = {}
        if cases_path is not None:
            from .evaluation import load_cases

            cases = load_cases(cases_path)
            matches = ([case for case in cases if case["id"] == case_id] if case_id else
                       [case for case in cases if case["query"].strip() == question.strip()])
            if not matches and case_id is None and len(cases) == 1:
                matches = [cases[0]]
            if len(matches) != 1:
                raise LocalWorkflowError(
                    "Select one expected-evidence case with --case-id, or provide a single/matching case in --cases."
                )
            expected = matches[0]["expected"]
        expected_files = set(expected.get("files", []))
        expected_symbols = set(expected.get("symbols", []))
        expected_relationships = set(expected.get("relationships", []))
        case = matches[0] if cases_path is not None else {}
        allowed_extras = set(case.get("allowed_extra_context", expected.get("allowed_extra_context", [])))
        available_files = {row["file_path"] for row in selected_files}
        available_symbols = {symbol for row in selected_files for symbol in row.get("symbols", [])}
        available_relationships = {
            related.get("symbol_name") for row in current["results"]
            for related in row.get("related_context", []) if related.get("symbol_name")
        }
        missing = {
            "files": sorted(expected_files - available_files),
            "symbols": sorted(expected_symbols - available_symbols),
            "relationships": sorted(set(case.get("required_relationships", expected_relationships))
                                     - available_relationships),
        }
        tolerance = case.get("failure_tolerance", expected.get("failure_tolerance", {}))
        extra_files = sorted(available_files - expected_files) if expected_files else sorted(available_files)
        tolerated_missing_relationships = (
            missing["relationships"] if tolerance.get("allow_missing_relationships", False) else []
        )
        duplicate_context = current["context"].get("suppressed_duplicates", [])
        payload = {
            "status": "completed", "mode": "developer-local-context-analysis",
            "question": question, "repository": current["repository"],
            "selected_files": selected_files,
            "expected_evidence": {"files": sorted(expected_files), "symbols": sorted(expected_symbols),
                                  "relationships": sorted(expected_relationships)},
            "missing_expected_evidence": missing,
            "extra_context": {"files": extra_files,
                              "allowed_files": sorted(set(extra_files) & allowed_extras),
                              "unexpected_files": ([] if tolerance.get("allow_extra_files", True)
                                                   else sorted(set(extra_files) - allowed_extras)),
                              "allow_extra_files": tolerance.get("allow_extra_files", True)},
            "tolerated_missing_relationships": tolerated_missing_relationships,
            "duplicate_context": duplicate_context,
            "duplicate_context_count": len(duplicate_context),
            "expected_evidence_note": ("case expectations supplied" if cases_path is not None
                                       else "no expected-evidence case supplied; missing evidence cannot be assessed"),
            "ranking_explanations": [
                {"file": row["file_path"], "symbol": row["qualified_name"],
                 "reasons": row["ranking_reason"]}
                for row in current["results"]
            ],
            "limitations": [
                "Context analysis is limited to the selected top-k results and explicit static relationships.",
                "Duplicate suppression detects identical symbol/content copies; semantically equivalent code may remain.",
            ],
        }
        inventory = scan_local_repository(Path(current["repository"]["repository_path"]))
        payload["run_id"] = self._record_run("analyze-context", inventory, payload)
        return payload

    def trace(self, question: str, repository: Path | None = None, top_k: int = 10) -> dict[str, Any]:
        """Explain selected local retrieval evidence and ranking decisions."""
        payload = self.query(question, repository, top_k)
        selected = []
        for row in payload["results"]:
            explanation = row["explanation"]
            selected.append({
                "file": row["file_path"],
                "symbol": row["qualified_name"],
                "rank": row["rank"],
                "evidence": explanation["match_reasons"],
                "relationship_path": explanation["relationship_path"],
                "ranking_factors": explanation["ranking_factors"],
                "ranking_factor_details": {
                    "matched_metadata_terms": row["ranking_reason"].get("matched_metadata_terms", []),
                    "non_test_preference": "applied" if row["ranking_reason"].get("test_factor", 1) < 1 else "not applied",
                    "definition_container_preference": "applied" if row["ranking_reason"].get("container_factor", 1) < 1 else "not applied",
                    "file_diversity": "applied" if row["ranking_reason"].get("diversity_factor", 1) < 1 else "not applied",
                    "retrieval_channels": [item for item in ("bm25", "dense")
                                           if any(contribution.get("channel") == item
                                                  for contribution in row.get("contributions", []))],
                },
                "context_expansion_reason": explanation["context_expansion_reason"],
                "confidence": {
                    "level": explanation["confidence"],
                    "signals": explanation["confidence_signals"],
                    "limitations": explanation["limitations"],
                },
            })
        payload["mode"] = "developer-local-retrieval-trace"
        payload["trace"] = {"query": question, "selected_results": selected}
        inventory = scan_local_repository(Path(payload["repository"]["repository_path"]))
        payload["run_id"] = self._record_run("trace", inventory, payload)
        return payload

    def diagnose(
        self, case_id: str, cases_path: Path, repository: Path | None = None, top_k: int = 10,
    ) -> dict[str, Any]:
        """Compare expected case evidence with a local index and explain gaps."""
        from .evaluation import load_cases

        cases = load_cases(cases_path)
        case = next((item for item in cases if item["id"] == case_id), None)
        if case is None:
            raise LocalWorkflowError(f"Case '{case_id}' was not found in '{cases_path}'.")
        self._prepare()
        if repository is None:
            active_files = sorted((self.root / "indexes").glob("*/v2/active.json"))
            if not active_files:
                index = None
                root = None
            elif len(active_files) > 1:
                raise LocalWorkflowError("More than one local repository has an active index. Pass --repository PATH to select one.")
            else:
                active_path = active_files[0]
                snapshot_id = self._read_active(active_path.parent)
                index = DeveloperIndex.load(self._contained(active_path.parent / snapshot_id))
                root = _resolve_repository_argument(Path(index.manifest["repository_path"]))
        else:
            root = _resolve_repository_argument(repository)
            self._prepare(root)
            active_path = self._indexes(scan_local_repository(root)) / "active.json"
            if active_path.exists():
                snapshot_id = self._read_active(active_path.parent)
                index = DeveloperIndex.load(self._contained(active_path.parent / snapshot_id))
            else:
                index = None

        inventory = scan_local_repository(root) if root is not None else None
        parsed = parse_local_repository(root) if root is not None else None
        freshness = "missing" if index is None else (
            "current" if inventory and index.manifest.get("working_tree_sha256") == inventory.snapshot_id
            else "stale"
        )
        results = []
        if index is not None:
            results = index.query(case["query"], top_k, self.root / "model-cache")
            for row in results:
                row["explanation"] = _result_explanation(case["query"], row)

        expected = case["expected"]
        expected_files = list(expected.get("files", []))
        expected_symbols = list(expected.get("symbols", []))
        expected_relationships = list(expected.get("relationships", []))
        available_files = sorted({row["file_path"] for row in results})
        available_symbols = sorted({row["qualified_name"] for row in results} | {
            item.get("symbol_name") for row in results for item in row.get("related_context", [])
            if item.get("symbol_name")
        } | {
            edge.get("symbol") for row in results
            for edge in row.get("developer_context", {}).get("relationship_edges", [])
            if edge.get("symbol")
        })
        available_relationships = sorted({
            edge.get("symbol") for row in results
            for edge in row.get("developer_context", {}).get("relationship_edges", [])
            if edge.get("symbol")
        } | {
            item.get("symbol_name") for row in results for item in row.get("related_context", [])
            if item.get("symbol_name")
        })
        missing = ([{"type": "file", "value": value} for value in expected_files if value not in available_files]
                   + [{"type": "symbol", "value": value} for value in expected_symbols if value not in available_symbols]
                   + [{"type": "relationship", "value": value} for value in expected_relationships
                      if value not in available_relationships])
        likely_causes: list[str] = []
        if freshness == "missing":
            likely_causes.append("no active developer index is available")
        elif freshness == "stale":
            likely_causes.append("stale index: indexed working-tree snapshot differs from current source")

        decisions = {item["file_path"]: item for item in inventory.file_decisions} if inventory else {}
        indexed_rows: list[dict[str, Any]] = []
        current_indexed_symbols: set[str] = set()
        if index is not None:
            indexed_rows = json.loads((index.path / "documents.json").read_text(encoding="utf-8"))
            current_indexed_symbols = {row["metadata"]["qualified_name"] for row in indexed_rows}
        old_state = {}
        if index is not None:
            try:
                old_state = json.loads((index.path / "state.json").read_text(encoding="utf-8"))
            except (OSError, ValueError, json.JSONDecodeError):
                old_state = {}
        old_symbols = {item.get("qualified_name") for item in old_state.get("chunks", [])}
        current_symbols = {item.qualified_name for item in parsed.chunks} if parsed else set()
        parse_failures = {item["file_path"] for item in parsed.parse_failures} if parsed else set()
        for value in expected_files:
            decision = decisions.get(value)
            if (decision is None or "missing" in decision["reason"]) and value in old_state.get("file_hashes", {}):
                likely_causes.append(f"file was deleted from current source: {value}")
        for value in expected_symbols:
            if value in old_symbols and value not in current_symbols:
                likely_causes.append(f"symbol was deleted or renamed since the indexed snapshot: {value}")
        for item in missing:
            value = item["value"]
            if item["type"] == "file":
                decision = decisions.get(value)
                if decision and "unsupported" in decision["reason"]:
                    likely_causes.append(f"unsupported language or file type: {value}")
                elif decision and "missing" in decision["reason"] and value in old_state.get("file_hashes", {}):
                    likely_causes.append(f"file was deleted from current source: {value}")
                elif decision and not decision["included"]:
                    likely_causes.append(f"file excluded from the local Python index: {value} ({decision['reason']})")
                elif value in parse_failures:
                    likely_causes.append(f"file could not be parsed: {value}")
                elif value in old_state.get("file_hashes", {}):
                    likely_causes.append(f"file was deleted from current source: {value}")
                else:
                    likely_causes.append(f"expected file was not selected by this query: {value}")
            elif item["type"] == "symbol":
                if value in current_symbols and value not in current_indexed_symbols:
                    likely_causes.append(f"symbol is present in source but not searchable in the active index: {value}")
                elif value in old_symbols and value not in current_symbols:
                    likely_causes.append(f"symbol was deleted or renamed since the indexed snapshot: {value}")
                elif value not in current_symbols:
                    likely_causes.append(f"symbol not found in supported indexed Python source: {value}")
                else:
                    likely_causes.append(f"expected symbol was not selected by this query: {value}")
            elif item["type"] == "relationship":
                likely_causes.append(f"relationship may not be detected by conservative static analysis: {value}")

        payload = {
            "status": "completed", "mode": "developer-local-context-diagnosis", "case_id": case_id,
            "query": case["query"], "index_freshness": {"status": freshness},
            "expected_evidence": {"files": expected_files, "symbols": expected_symbols,
                                  "relationships": expected_relationships},
            "available_evidence": {"files": available_files, "symbols": available_symbols,
                                   "relationships": available_relationships},
            "missing_evidence": missing,
            "likely_causes": list(dict.fromkeys(likely_causes)),
            "results": results,
            "limitations": [
                "Diagnosis compares declared case expectations with bounded local retrieval and static metadata.",
                "A missing relationship can reflect unsupported dynamic/runtime behavior, not incorrect source code.",
            ],
        }
        if inventory is not None:
            payload["repository"] = inventory.summary()
            payload["run_id"] = self._record_run("diagnose", inventory, payload)
            from .observability import record_retrieval
            record_retrieval(self, payload, inventory, index, "diagnose", top_k)
        return payload

    def regression(self, repository: Path, cases_path: Path, baseline: str = "default",
                   create_baseline: bool = False, top_k: int = 10) -> dict[str, Any]:
        from .regression import run_regression
        return run_regression(self, repository, cases_path, baseline, create_baseline, top_k)

    def evaluate(self, repository: Path, cases_path: Path, top_k: int = 10, explain: bool = False, compare: bool = False, stability: bool = False) -> dict[str, Any]:
        from .evaluation import compare_reports, evaluate_cases, load_cases

        cases = load_cases(cases_path)
        root = _resolve_repository_argument(repository)
        inventory = scan_local_repository(root)
        baseline = self._previous_evaluation(inventory.repository_id) if compare else None
        payloads = []
        stability_rows = []
        for case in cases:
            first = self.query(case["query"], repository, top_k)
            payloads.append(first)
            if stability:
                second = self.query(case["query"], repository, top_k)
                first_signature = [(row["chunk_id"], row["rank"]) for row in first["results"]]
                second_signature = [(row["chunk_id"], row["rank"]) for row in second["results"]]
                stability_rows.append({"case": case["id"], "stable": first_signature == second_signature,
                                      "reason": "identical ranked chunk IDs" if first_signature == second_signature else "ranked results changed"})
        payloads = tuple(payloads)
        report = evaluate_cases(cases, payloads)
        report.update({"repository": inventory.summary(), "case_file": str(Path(cases_path).resolve())})
        index_root = self._indexes(inventory)
        report["index_state"] = {"working_tree_sha256": inventory.snapshot_id,
                                  "index_path": str(index_root / self._read_active(index_root))} if (index_root / "active.json").exists() else {"status": "not indexed"}
        if stability:
            stable = sum(item["stable"] for item in stability_rows)
            report["stability"] = {"query_count": len(stability_rows), "stable_results": stable,
                                    "changed_results": len(stability_rows) - stable,
                                    "changed_cases": [item for item in stability_rows if not item["stable"]]}
        if baseline is not None:
            report["comparison"] = compare_reports(baseline, report)
        elif compare:
            report["comparison"] = {"baseline": None, "candidate": {}, "changed_cases": [],
                                     "note": "No prior developer evaluation record exists for this repository."}
        if not explain:
            for detail in report["details"]:
                detail.pop("results", None)
        report["run_id"] = self._record_run("evaluate", inventory, report)
        return report

    def explain_run(self, run_id: str, case_id: str) -> dict[str, Any]:
        directory = self._contained(self.root / "runs" / run_id)
        try:
            metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
            results = json.loads((directory / "results.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise LocalWorkflowError(f"Developer run '{run_id}' is unavailable or invalid: {error}") from error
        if metadata.get("mode") != "developer-local" or metadata.get("command") != "evaluate":
            raise LocalWorkflowError(f"Developer run '{run_id}' is not an evaluation record.")
        case = next((item for item in results.get("details", ()) if item.get("id") == case_id), None)
        if case is None:
            raise LocalWorkflowError(f"Case '{case_id}' was not found in developer run '{run_id}'.")
        return {"status": "completed", "mode": "developer-local-run-explanation", "run_id": run_id,
                "repository": results.get("repository"), "index_state": results.get("index_state"), "case": case}

    def _previous_evaluation(self, repository_id: str) -> dict[str, Any] | None:
        candidates = []
        for directory in (self.root / "runs").glob("*"):
            try:
                metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
                if metadata.get("command") == "evaluate" and metadata.get("repository_id") == repository_id:
                    candidates.append((directory.stat().st_mtime_ns, json.loads((directory / "results.json").read_text(encoding="utf-8"))))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return max(candidates, default=(0, None), key=lambda item: item[0])[1]

    def _read_active(self, repo_indexes: Path) -> str:
        try:
            self._contained(repo_indexes / "active.json")
            value = json.loads((repo_indexes / "active.json").read_text(encoding="utf-8")).get("snapshot_id")
        except (OSError, TypeError, json.JSONDecodeError) as error:
            raise LocalWorkflowError(
                f"No valid developer index is registered under '{repo_indexes}'. "
                "Run prototype local index <repository> first."
            ) from error
        if (not isinstance(value, str) or len(value) != 64
                or any(char not in "0123456789abcdef" for char in value)):
            raise LocalWorkflowError(f"Invalid active-index record under '{repo_indexes}'. Rebuild the index.")
        return value

    def _write_index(
        self,
        destination: Path,
        parsed: ParsedLocalCode,
        embeddings: tuple[Embedding, ...],
        rejections: tuple[dict[str, Any], ...],
    ) -> None:
        inventory = parsed.inventory
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(prefix=".local-index-", dir=destination.parent) as temporary:
                staging = Path(temporary)
                by_id = {chunk.chunk_id: chunk for chunk in parsed.chunks}
                embedding_by_id = {embedding.chunk_id: embedding for embedding in embeddings}
                ids = sorted(embedding_by_id)
                rows = []
                vectors = []
                for row_number, chunk_id in enumerate(ids):
                    embedding = embedding_by_id[chunk_id]
                    chunk = by_id[chunk_id]
                    rows.append({
                        "row": row_number,
                        "chunk_id": chunk_id,
                        "metadata": asdict(embedding.metadata),
                        "tokens": list(tokenize(chunk.content.strip())),
                    })
                    vectors.append(embedding.vector)
                document_bytes = _json_bytes(rows)
                vector_stream = io.BytesIO()
                np.save(vector_stream, np.asarray(vectors, dtype=np.float32), allow_pickle=False)
                vector_bytes = vector_stream.getvalue()
                (staging / "documents.json").write_bytes(document_bytes)
                (staging / "vectors.npy").write_bytes(vector_bytes)
                state_bytes = _json_bytes({
                    "file_hashes": {f.relative_path: f.content_sha256 for f in inventory.files},
                    "chunks": [asdict(c) for c in parsed.chunks],
                    "context": parsed.context,
                    "parse_failures": list(parsed.parse_failures),
                    "rejections": list(rejections),
                })
                (staging / "state.json").write_bytes(state_bytes)
                _write_json(staging / "manifest.json", {
                    "schema_version": _INDEX_SCHEMA,
                    "mode": "developer-local",
                    "repository_id": inventory.repository_id,
                    "repository_path": str(inventory.root),
                    "commit_sha": inventory.commit_sha,
                    "working_tree_sha256": inventory.snapshot_id,
                    "tracked_file_count": inventory.tracked_file_count,
                    "eligible_python_file_count": len(inventory.files),
                    "eligible_python_code_loc": inventory.code_loc,
                    "excluded_python_file_count": inventory.excluded_python_count,
                    "unsupported_extensions": dict(inventory.unsupported_extensions),
                    "parsed_python_file_count": len(inventory.files) - len(parsed.parse_failures),
                    "parse_failure_count": len(parsed.parse_failures),
                    "chunk_count": len(parsed.chunks),
                    "indexed_chunk_count": len(ids),
                    "rejected_chunk_count": len(rejections),
                    "rejection_reasons": sorted({item["reason"] for item in rejections}),
                    "runtime": {
                        "python": platform.python_version(),
                        "numpy": np.__version__,
                        "faiss": version("faiss-cpu"),
                        "tokenizer": TOKENIZER_VERSION,
                        "scoring": SCORING_VERSION,
                        "model": MODEL_ID,
                        "model_revision": MODEL_REVISION,
                    },
                    "artifacts": {
                        "documents.json": _digest(document_bytes),
                        "vectors.npy": _digest(vector_bytes),
                        "state.json": _digest(state_bytes),
                    },
                })
                if destination.exists():
                    raise LocalWorkflowError(f"Refusing to overwrite existing developer index '{destination}'.")
                os.replace(staging, destination)
        except LocalWorkflowError:
            raise
        except OSError as error:
            raise LocalWorkflowError(f"Cannot write developer index under '{destination}': {error}") from error

    def _record_run(self, command: str, inventory: LocalInventory, payload: dict[str, Any]) -> str:
        identity = {
            "mode": "developer-local",
            "command": command,
            "repository_id": inventory.repository_id,
            "working_tree_sha256": inventory.snapshot_id,
            "payload": payload,
        }
        run_id = _digest(_json_bytes(identity))[:20]
        directory = self._contained(self.root / "runs" / run_id)
        result_bytes = _json_bytes(payload)
        if directory.exists():
            try:
                if (directory / "results.json").read_bytes() == result_bytes:
                    return run_id
            except OSError:
                pass
            raise LocalWorkflowError(f"Refusing to overwrite developer run record '{directory}'.")
        directory.mkdir(parents=True, exist_ok=False)
        metadata = {
            "schema_version": "developer-local-run-v1",
            "mode": "developer-local",
            "run_id": run_id,
            "command": command,
            "repository_id": inventory.repository_id,
            "repository_path": str(inventory.root),
            "commit_sha": inventory.commit_sha,
            "working_tree_sha256": inventory.snapshot_id,
            "workspace_sha256": _digest(str(self.root).encode("utf-8")),
        }
        try:
            (directory / "metadata.json").write_bytes(_json_bytes(metadata))
            (directory / "results.json").write_bytes(result_bytes)
        except OSError as error:
            raise LocalWorkflowError(f"Cannot write developer run record under '{directory}': {error}") from error
        return run_id


def scan_local_repository(repository: Path) -> LocalInventory:
    """Read supported Python files in an existing local Git worktree only."""
    root = _resolve_repository_argument(repository)
    top = _git(root, ["rev-parse", "--show-toplevel"])
    try:
        git_root = Path(os.fsdecode(top).strip()).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise LocalWorkflowError(f"Cannot resolve Git root for '{root}': {error}") from error
    if git_root != root:
        raise LocalWorkflowError(f"'{root}' is inside a Git worktree. Pass the repository root directory.")
    commit_sha = os.fsdecode(_git(root, ["rev-parse", "--verify", "HEAD^{commit}"])).strip().lower()
    path_suffix = hashlib.sha256(os.path.normcase(str(root)).encode("utf-8")).hexdigest()[:12]
    repository_id = f"local/{_safe_component(root.name)}-{path_suffix}"
    try:
        manifest: CorpusManifest = RepositoryScanner().scan(root, commit_sha, repository_id=repository_id)
    except (OSError, RuntimeError, ValueError) as error:
        raise LocalWorkflowError(f"Cannot scan local Git repository '{root}': {error}") from error
    excluded_committed = {file.relative_path for file in manifest.files if not file.included}
    listed = _git(root, ["ls-files", "--cached", "--others", "--exclude-standard", "-z"])
    relative_paths = sorted({os.fsdecode(item) for item in listed.split(b"\0") if item})
    files: list[LocalFile] = []
    unsupported = Counter()
    excluded = 0
    decisions = []
    for relative_path in relative_paths:
        decision = {"file_path": relative_path, "included": False, "reason": "unsafe path"}
        decisions.append(decision)
        posix_path = PurePosixPath(relative_path)
        if posix_path.is_absolute() or ".." in posix_path.parts:
            continue
        path = root.joinpath(*posix_path.parts)
        if path.is_symlink() or root not in path.resolve().parents:
            decision["reason"] = "symbolic link or redirected path"
            continue
        if not path.is_file():
            decision["reason"] = "missing or not a regular file"
            continue
        if path.suffix.casefold() != ".py":
            unsupported[path.suffix.casefold() or "[no extension]"] += 1
            decision["reason"] = "unsupported file type (Python only)"
            continue
        if any(part in _IGNORED_DIRECTORIES for part in posix_path.parts[:-1]):
            excluded += 1
            decision["reason"] = "excluded generated/vendor/environment directory"
            continue
        if RepositoryScanner._path_exclusion_reason(relative_path) is not None:
            excluded += 1
            decision["reason"] = RepositoryScanner._path_exclusion_reason(relative_path)
            continue
        if relative_path in excluded_committed:
            excluded += 1
            decision["reason"] = "excluded by committed-file inventory"
            continue
        try:
            data = path.read_bytes()
        except OSError as error:
            raise LocalWorkflowError(f"Cannot read local Python file '{relative_path}': {error}") from error
        files.append(LocalFile(
            relative_path=posix_path.as_posix(),
            absolute_path=path,
            content_sha256=_digest(data),
            size_bytes=len(data),
            code_loc=RepositoryScanner._count_loc(data),
        ))
        decision.update(included=True, reason="supported Python source", content_sha256=_digest(data), size_bytes=len(data))
    files.sort(key=lambda item: item.relative_path)
    payload = [commit_sha, [[item.relative_path, item.content_sha256] for item in files]]
    snapshot_id = _digest(json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8"))
    return LocalInventory(root, repository_id, commit_sha, snapshot_id, tuple(files),
                          sum(item.code_loc for item in files), tuple(sorted(unsupported.items())),
                          excluded, len(relative_paths), tuple(decisions))


def parse_local_repository(repository: Path) -> ParsedLocalCode:
    return _parse_inventory(scan_local_repository(repository))


def _parse_inventory(inventory: LocalInventory) -> ParsedLocalCode:
    metadata = RepositoryMetadata(inventory.repository_id, inventory.commit_sha)
    parser, chunker = PythonAstParser(), CodeChunker()
    chunks: list[CodeChunk] = []
    failures: list[dict[str, Any]] = []
    context: dict[str, dict[str, Any]] = {}
    for file in inventory.files:
        try:
            with python_tokenize.open(file.absolute_path) as source_file:
                source = source_file.read()
            module = parser.parse(source, file.relative_path)
            file_chunks = chunker.chunk_module(module, source, metadata)
            chunks.extend(file_chunks)
            context.update(_developer_context(module, source, file_chunks))
        except ParserError as error:
            failures.append({"file_path": error.relative_path, "line": error.line, "message": error.message})
        except (OSError, UnicodeError, ValueError) as error:
            failures.append({"file_path": file.relative_path, "line": None, "message": str(error)})
    by_leaf_name: dict[str, list[str]] = {}
    for chunk in chunks:
        by_leaf_name.setdefault(chunk.qualified_name.rsplit(".", 1)[-1], []).append(chunk.chunk_id)
    for details in context.values():
        expanded = list(details["related_chunk_ids"])
        for name in details.get("related_symbol_names", []):
            expanded.extend(by_leaf_name.get(name, ()))
        details["related_chunk_ids"] = sorted(set(expanded))
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    for chunk_id, details in context.items():
        edges = []
        targets = (
            ("import_relationship", details.get("related_symbol_names", [])),
            ("call_relationship", details.get("called_symbol_names", [])),
        )
        for kind, names in targets:
            for name in names:
                for target_id in by_leaf_name.get(name, ()):
                    if target_id != chunk_id:
                        target = chunks_by_id[target_id]
                        edges.append({"symbol": target.qualified_name, "file_path": target.file_path,
                                      "kind": kind})
        parent_symbol = details.get("parent_symbol")
        if parent_symbol:
            for target_id in by_leaf_name.get(parent_symbol.rsplit(".", 1)[-1], ()):
                target = chunks_by_id[target_id]
                if target_id != chunk_id and target.file_path == chunks_by_id[chunk_id].file_path:
                    edges.append({"symbol": target.qualified_name, "file_path": target.file_path,
                                  "kind": "parent_relationship"})
        details["relationship_edges"] = sorted(
            { (edge["symbol"], edge["file_path"], edge["kind"]): edge for edge in edges }.values(),
            key=lambda edge: (edge["kind"], edge["file_path"], edge["symbol"]),
        )
    chunks_by_symbol: dict[str, list[str]] = {}
    for chunk_id, details in context.items():
        chunks_by_symbol.setdefault(details["symbol_name"], []).append(chunk_id)
    incoming: dict[str, list[dict[str, str]]] = {}
    for source_id, details in context.items():
        source_chunk = chunks_by_id[source_id]
        for edge in details.get("relationship_edges", []):
            inverse_kind = {"call_relationship": "caller_relationship",
                            "import_relationship": "importer_relationship"}.get(edge["kind"])
            if inverse_kind is None:
                continue
            for target_id in chunks_by_symbol.get(edge["symbol"], ()):
                if target_id != source_id:
                    incoming.setdefault(target_id, []).append({
                        "symbol": source_chunk.qualified_name,
                        "file_path": source_chunk.file_path,
                        "kind": inverse_kind,
                    })
                    context[target_id]["related_chunk_ids"].append(source_id)
    for chunk_id, edges in incoming.items():
        context[chunk_id]["relationship_edges"] = sorted(
            context[chunk_id].get("relationship_edges", []) + edges,
            key=lambda edge: (edge["kind"], edge["file_path"], edge["symbol"]),
        )
        context[chunk_id]["related_chunk_ids"] = sorted(set(context[chunk_id]["related_chunk_ids"]))
    return ParsedLocalCode(inventory, tuple(chunks), tuple(failures), context)


def _developer_context(module: Any, source: str, chunks: tuple[CodeChunk, ...]) -> dict[str, dict[str, Any]]:
    """Build source-structure metadata kept only in the developer index sidecar."""
    tree = ast.parse(source, filename=module.relative_path, type_comments=True)
    by_name = {chunk.qualified_name: chunk for chunk in chunks}
    imports = sorted({item.name if item.module is None else f"{item.module}.{item.name}" for item in module.imports})
    constants = sorted({node.targets[0].id for node in ast.walk(tree)
                        if isinstance(node, ast.Assign) and node.targets
                        and isinstance(node.targets[0], ast.Name)
                        and node.targets[0].id.isupper()})
    calls_by_line = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else None
            if name:
                calls_by_line.setdefault(getattr(node, "lineno", 1), set()).add(name)
    result = {}
    for chunk in chunks:
        parent = chunk.qualified_name.rsplit(".", 1)[0] if "." in chunk.qualified_name else None
        called_names = sorted({
            node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and chunk.start_line <= getattr(node, "lineno", -1) <= chunk.end_line
            and isinstance(node.func, (ast.Name, ast.Attribute))
        })
        related = []
        if parent in by_name:
            related.append(by_name[parent].chunk_id)
        related.extend(item.chunk_id for name, item in by_name.items()
                       if name != chunk.qualified_name and name.rsplit(".", 1)[-1] in calls_by_line.get(chunk.start_line, set()))
        nearby = [item.chunk_id for item in chunks if item.chunk_id != chunk.chunk_id
                  and item.start_line <= chunk.end_line + 3 and item.end_line >= chunk.start_line - 3]
        result[chunk.chunk_id] = {
            "module_name": module.name,
            "symbol_name": chunk.qualified_name,
            "parent_symbol": parent,
            "imports": imports,
            "related_symbol_names": sorted({item.rsplit(".", 1)[-1] for item in imports}),
            "called_symbol_names": called_names,
            "configuration_keys": constants,
            "related_chunk_ids": sorted(set(related)),
            "nearby_chunk_ids": sorted(nearby),
            "source_region": f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}",
            "content_sha256": hashlib.sha256(chunk.content.encode("utf-8")).hexdigest(),
            "why": f"{chunk.entity_type} extracted from the {module.name} module",
        }
    return result


def _embed_developer_chunks(
    chunks: tuple[CodeChunk, ...], model_cache: Path,
) -> tuple[tuple[Embedding, ...], tuple[dict[str, Any], ...]]:
    """Apply the pinned local embedding contract without research clearance files."""
    model = load_model(model_cache)
    accepted: list[tuple[CodeChunk, EmbeddingMetadata, str]] = []
    rejected: list[dict[str, Any]] = []
    for chunk in sorted(chunks, key=lambda item: item.chunk_id):
        text = chunk.content.strip()
        token_count = len(model.tokenizer(text, add_special_tokens=True, truncation=False,
                                          padding=False, verbose=False)["input_ids"])
        if not text or token_count > 256:
            rejected.append({
                "chunk_id": chunk.chunk_id,
                "parent_chunk_id": chunk.chunk_id,
                "token_count": token_count,
                "reason": "empty" if not text else "over_limit",
            })
            continue
        metadata = EmbeddingMetadata(
            chunk.repository_id,
            chunk.commit_sha,
            chunk.file_path,
            chunk.entity_type,
            chunk.qualified_name,
            chunk.start_line,
            chunk.end_line,
            _digest(chunk.content.encode("utf-8")),
            token_count,
        )
        accepted.append((chunk, metadata, text))
    if not accepted:
        return (), tuple(rejected)
    vectors = model.encode([text for _, _, text in accepted], batch_size=32,
                           show_progress_bar=False, convert_to_numpy=True,
                           normalize_embeddings=False)
    vectors = validate_vector_matrix(vectors, len(accepted))
    embeddings = tuple(
        Embedding(chunk.chunk_id, tuple(float(value) for value in vector), metadata)
        for (chunk, metadata, _), vector in zip(accepted, vectors)
    )
    return embeddings, tuple(rejected)


def local_demo() -> dict[str, Any]:
    """Show parsing, chunking, and lexical retrieval on generated memory-only code."""
    source = (
        "def find_session_token(headers):\n"
        "    return headers.get('session-token')\n\n"
        "def build_auth_header(token):\n"
        "    return {'Authorization': token}\n"
    )
    repository_id = "developer-demo/generated-fixture"
    commit_sha = hashlib.sha1(source.encode("utf-8")).hexdigest()
    module = PythonAstParser().parse(source, "demo_auth.py")
    chunks = CodeChunker().chunk_module(module, source, RepositoryMetadata(repository_id, commit_sha))
    metadata = tuple(
        EmbeddingMetadata(chunk.repository_id, chunk.commit_sha, chunk.file_path,
                          chunk.entity_type, chunk.qualified_name, chunk.start_line,
                          chunk.end_line, _digest(chunk.content.encode("utf-8")), 1)
        for chunk in chunks
    )
    order = sorted(range(len(chunks)), key=lambda index: chunks[index].chunk_id)
    index = BM25Index._create(
        tuple(chunks[index].chunk_id for index in order),
        tuple(metadata[index] for index in order),
        tuple(tokenize(chunks[index].content.strip()) for index in order),
    )
    results = BM25Search(index).search("find session token", k=3)
    return {
        "status": "completed",
        "mode": "developer-local-demo",
        "source": "generated in-memory fixture",
        "chunk_count": len(chunks),
        "question": "find session token",
        "results": [_result_to_dict(result) for result in results],
        "notice": DEVELOPER_MODE_NOTICE,
    }


def _git(root: Path, arguments: list[str]) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = os.fsdecode(result.stderr).strip() or "Git returned no diagnostic"
        raise LocalWorkflowError(
            f"'{root}' is not a usable local Git repository (git {arguments[0]} failed: {detail}). "
            "Pass the root of an existing Git working tree; local mode never clones or fetches."
        )
    return result.stdout


def _resolve_repository_argument(repository: Path) -> Path:
    try:
        root = Path(repository).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise LocalWorkflowError(
            f"Repository path does not exist or cannot be resolved: '{repository}'."
        ) from error
    if not root.is_dir():
        raise LocalWorkflowError(f"Repository path is not a directory: '{root}'.")
    return root


def _safe_component(value: str) -> str:
    safe = "".join(character if character.isalnum() or character in "-_" else "-" for character in value)
    return safe.strip("-")[:64] or "repository"


def _overlaps(first: Path, second: Path) -> bool:
    first, second = first.resolve(strict=False), second.resolve(strict=False)
    return first == second or first in second.parents or second in first.parents


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(_json_bytes(value))
    os.replace(temporary, path)


def _result_to_dict(result: Any) -> dict[str, Any]:
    return {
        "chunk_id": result.chunk_id,
        "rank": result.rank,
        "score": result.score,
        "strategy": result.strategy,
        "repository_id": result.repository_id,
        "commit_sha": result.commit_sha,
        "file_path": result.file_path,
        "entity_type": result.entity_type,
        "qualified_name": result.qualified_name,
        "start_line": result.start_line,
        "end_line": result.end_line,
        "contributions": [asdict(item) for item in getattr(result, "contributions", ())],
    }
