"""Rank-only reciprocal rank fusion for validated, snapshot-scoped results."""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math

from src.models.retrieval_result import SearchResult

RRF_CONSTANT = 60
CANDIDATE_WINDOW = 50


@dataclass(frozen=True, slots=True)
class RankContribution:
    channel: str
    rank: int
    score: float
    rrf_score: float


@dataclass(frozen=True, slots=True)
class FusionResult(SearchResult):
    contributions: tuple[RankContribution, ...] = ()


def reciprocal_rank(rank: int) -> float:
    if type(rank) is not int or rank < 1:
        raise ValueError("Rank must be a positive one-based integer")
    return 1.0 / (RRF_CONSTANT + rank)


def validate_cutoff(k: int) -> None:
    if type(k) is not int or not 1 <= k <= CANDIDATE_WINDOW:
        raise ValueError("k must be an integer from 1 to 50")


def fuse_rankings(rankings: Mapping[str, Sequence[SearchResult]], k: int = 50) -> tuple[FusionResult, ...]:
    """Fuse up to 50 results per named channel, preserving component evidence.

    Rank fields must agree with list position; malformed lists fail instead of
    silently changing ranks. Duplicate IDs across channels are fused once.
    """
    validate_cutoff(k)
    if any(not isinstance(name, str) or not name.strip() for name in rankings):
        raise ValueError("Channels must have nonempty names")
    metadata, contributions = {}, defaultdict(list)
    snapshot = None
    for channel in sorted(rankings):
        seen = set()
        for position, result in enumerate(rankings[channel][:CANDIDATE_WINDOW], start=1):
            if type(result.rank) is not int or result.rank != position:
                raise ValueError("Component ranks must match one-based list positions")
            if not result.chunk_id or result.chunk_id in seen:
                raise ValueError("Duplicate or empty chunk ID within a channel")
            if not math.isfinite(result.score):
                raise ValueError("Component score must be finite")
            seen.add(result.chunk_id)
            identity = (result.repository_id, result.commit_sha)
            if snapshot is not None and identity != snapshot:
                raise ValueError("Cannot fuse different snapshots")
            snapshot = identity
            if result.chunk_id in metadata and metadata[result.chunk_id] != result.metadata:
                raise ValueError("Conflicting metadata for the same chunk ID")
            metadata[result.chunk_id] = result.metadata
            contributions[result.chunk_id].append(RankContribution(
                channel, result.rank, result.score, reciprocal_rank(result.rank)))
    scores = {cid: math.fsum(c.rrf_score for c in values) for cid, values in contributions.items()}
    ordered = sorted(scores, key=lambda cid: (-scores[cid], cid))[:k]
    return tuple(FusionResult(cid, rank, scores[cid], metadata[cid], "hybrid", tuple(contributions[cid]))
                 for rank, cid in enumerate(ordered, start=1))
