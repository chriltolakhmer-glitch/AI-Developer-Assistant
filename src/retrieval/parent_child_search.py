"""Opt-in, bounded Humanize pilot retrieval returning immutable parent evidence.

Separate in-memory representation: never writes legacy embedding/index artifacts.
"""

from dataclasses import dataclass
import hashlib
from pathlib import Path
from types import MappingProxyType

import numpy as np

from src.embedding.model import external_path, load_model
from src.embedding.pipeline import validate_chunk, validate_vector_matrix
from src.models.chunk import CodeChunk
from src.models.embedding import EmbeddingMetadata
from src.models.retrieval_result import SearchResult
from .direct_calls import DirectCall, direct_calls
from .parent_child_passages import ChildPassage, split_parent, token_count

PILOT_REPOSITORY = "python-humanize/humanize"
PILOT_COMMIT = "392aef707c0e74341ab4a51420984e9ea6b566c5"
FROZEN_MAP_SHA256 = "46c437795ba7876d6cbfe9845bee5590b7b084c575c44880ab79d2ec0e2514d3"


@dataclass(frozen=True, slots=True)
class ParentEvidence(SearchResult):
    # metadata describes the full parent, whose token count may exceed 256.
    content: str = ""
    winning_child_id: str = ""
    dense_rank: int = 0
    expansion_from: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ChildHit:
    child_id: str
    parent_chunk_id: str
    rank: int
    score: float


@dataclass(frozen=True, slots=True)
class ParentChildResponse:
    results: tuple[ParentEvidence, ...]
    dense_parents: tuple[ParentEvidence, ...]
    child_hits: tuple[ChildHit, ...]
    expansion_candidates: tuple[str, ...]
    call_edges: tuple[DirectCall, ...]


def _validate_inventory(chunks, raw_map: bytes, sources):
    if hashlib.sha256(raw_map).hexdigest() != FROZEN_MAP_SHA256:
        raise ValueError("Parent-child mode requires the unchanged frozen Humanize chunk map")
    records, file = {}, None
    for line in raw_map.decode("utf-8").splitlines():
        if line.startswith("FILE "):
            file = line[5:]
        elif line:
            kind, name, start, end, cid = line.split("|")
            records[cid] = (file, kind, name, int(start), int(end))
    if len(chunks) != 44 or len({c.chunk_id for c in chunks}) != 44 or set(records) != {c.chunk_id for c in chunks}:
        raise ValueError("Expected exactly the 44 frozen Humanize parents")
    if set(sources) != {r[0] for r in records.values()}:
        raise ValueError("Source inventory differs from frozen parent files")
    for chunk in chunks:
        validate_chunk(chunk)
        if (chunk.repository_id, chunk.commit_sha) != (PILOT_REPOSITORY, PILOT_COMMIT):
            raise ValueError("Parent-child mode is restricted to the pinned Humanize pilot")
        if (chunk.file_path, chunk.entity_type, chunk.qualified_name, chunk.start_line, chunk.end_line) != records[chunk.chunk_id]:
            raise ValueError("Parent metadata differs from frozen map")
        lines = sources[chunk.file_path].splitlines(keepends=True)
        if "".join(lines[chunk.start_line - 1:chunk.end_line]) != chunk.content:
            raise ValueError("Source text differs from canonical parent content")
        if chunk.entity_type == "module" and chunk.content != sources[chunk.file_path]:
            raise ValueError("Extra source outside the frozen module")


class ParentChildSearch:
    """Explicit opt-in build/search API; baseline classes and schemas are untouched.

    Call build() with verified canonical chunks and complete canonical file text.
    No annotation input is accepted. Only k=5 and the fixed three-seed/two-slot
    policy are supported by this pilot implementation.
    """

    @classmethod
    def build(cls, chunks: tuple[CodeChunk, ...], *, chunk_map_path: Path,
              sources: dict[str, str], model_cache: Path):
        chunks = tuple(sorted(chunks, key=lambda c: c.chunk_id))
        sources = dict(sources)
        raw_map = external_path(chunk_map_path).read_bytes()
        _validate_inventory(chunks, raw_map, sources)
        model = load_model(external_path(model_cache))
        children = tuple(sorted((child for p in chunks for child in split_parent(p, model.tokenizer)),
                                key=lambda c: c.child_id))
        if len({c.child_id for c in children}) != len(children):
            raise ValueError("Duplicate child representation IDs")
        vectors = model.encode([c.content.strip() for c in children], batch_size=32,
                               show_progress_bar=False, convert_to_numpy=True,
                               normalize_embeddings=False)
        vectors = validate_vector_matrix(vectors, len(children))
        edges = direct_calls(chunks, sources)
        counts = {p.chunk_id: token_count(model.tokenizer, p.content) for p in chunks}
        return cls._assemble(chunks, children, vectors, edges, counts, model)

    @classmethod
    def _assemble(cls, chunks, children, vectors, edges, counts, model):
        instance = cls()
        instance._parents = MappingProxyType({c.chunk_id: c for c in chunks})
        instance._children = tuple(children)
        # Immutable backing memory prevents accidental index mutation through views.
        instance._vectors = np.frombuffer(vectors.tobytes(), dtype=np.float32).reshape(vectors.shape)
        instance._edges = tuple(edges)
        instance._counts = MappingProxyType(dict(counts))
        instance._model = model
        instance._graph = MappingProxyType({c.chunk_id: tuple(sorted({e.callee_id for e in edges if e.caller_id == c.chunk_id})) for c in chunks})
        return instance

    @property
    def parents(self) -> tuple[CodeChunk, ...]:
        return tuple(self._parents.values())

    @property
    def children(self) -> tuple[ChildPassage, ...]:
        return self._children

    @property
    def call_edges(self) -> tuple[DirectCall, ...]:
        return self._edges

    def search(self, query: str, k: int = 5) -> tuple[ParentEvidence, ...]:
        return self.search_with_details(query, k).results

    def search_with_details(self, query: str, k: int = 5) -> ParentChildResponse:
        if type(k) is not int or k != 5:
            raise ValueError("Bounded pilot mode returns exactly five parents (k=5)")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be nonempty text")
        text = query.strip()
        if token_count(self._model.tokenizer, text) > 256:
            raise ValueError("Query exceeds 256 tokens; silent truncation is prohibited")
        encoded = self._model.encode([text], batch_size=32, show_progress_bar=False,
                                     convert_to_numpy=True, normalize_embeddings=False)
        vector = validate_vector_matrix(encoded, 1)[0]
        return self._rank(vector)

    def _rank(self, vector) -> ParentChildResponse:
        scores = self._vectors @ vector
        if not np.isfinite(scores).all():
            raise ValueError("Non-finite child scores")
        ordered = sorted(range(len(self._children)), key=lambda i: (-float(scores[i]), self._children[i].child_id))
        hits = tuple(ChildHit(self._children[i].child_id, self._children[i].parent_chunk_id,
                             rank, float(scores[i])) for rank, i in enumerate(ordered, 1))
        best = {}
        for hit in hits:
            best.setdefault(hit.parent_chunk_id, hit)
        dense_ids = sorted(best, key=lambda cid: (-best[cid].score, cid))
        dense_ranks = {cid: rank for rank, cid in enumerate(dense_ids, 1)}
        seeds = dense_ids[:3]
        candidates = sorted({target for seed in seeds for target in self._graph[seed]} - set(seeds),
                            key=lambda cid: (-best[cid].score, cid))
        selected = seeds + candidates[:2]
        expanded = set(candidates[:2])
        selected.extend(cid for cid in dense_ids if cid not in selected)
        def evidence(cid, rank, is_expanded=False):
            p = self._parents[cid]
            metadata = EmbeddingMetadata(p.repository_id, p.commit_sha, p.file_path,
                                         p.entity_type, p.qualified_name, p.start_line,
                                         p.end_line, hashlib.sha256(p.content.encode()).hexdigest(),
                                         self._counts[cid])
            return ParentEvidence(cid, rank, best[cid].score, metadata, "parent_child",
                                  p.content, best[cid].child_id, dense_ranks[cid],
                                  tuple(seed for seed in seeds if cid in self._graph[seed]) if is_expanded else ())
        return ParentChildResponse(
            tuple(evidence(cid, rank, cid in expanded) for rank, cid in enumerate(selected[:5], 1)),
            tuple(evidence(cid, rank) for rank, cid in enumerate(dense_ids, 1)),
            hits, tuple(candidates), self._edges)
