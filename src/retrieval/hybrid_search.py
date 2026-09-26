"""Local text query -> pinned MiniLM + FAISS / BM25 -> fixed RRF."""

from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
import platform

from src.embedding.model import MAX_TOKENS, external_path, load_model
from src.embedding.pipeline import validate_vector_matrix
from src.models.retrieval_result import SearchResult
from .bm25_index import BM25Index
from .bm25_search import BM25Search
from .embedding_artifacts import _contract
from .rrf import CANDIDATE_WINDOW, RRF_CONSTANT, FusionResult, fuse_rankings, validate_cutoff
from .vector_index import VectorIndex


@dataclass(frozen=True, slots=True)
class HybridSearchResponse:
    dense: tuple[SearchResult, ...]
    lexical: tuple[SearchResult, ...]
    hybrid: tuple[FusionResult, ...]
    query_token_count: int
    rrf_constant: int = RRF_CONSTANT
    candidate_window: int = CANDIDATE_WINDOW


class HybridSearch:
    def __init__(self, dense: VectorIndex, lexical: BM25Index, model_cache: Path):
        self._dense, self._lexical = dense, lexical
        self._cache = external_path(model_cache)
        self._model = None
        self._validate_indexes()

    def _validate_indexes(self):
        dense, lexical = self._dense, self._lexical
        if ((dense.repository_id, dense.commit_sha) != (lexical.repository_id, lexical.commit_sha)
                or dense._ids != lexical.chunk_ids or dense._metadata != lexical._metadata
                or dense._embedding_run_sha256 != lexical._embedding_run_sha256
                or dense._embedding_run != lexical._embedding_run):
            raise ValueError("Hybrid channels must share snapshot, inventory, provenance, and embedding run")
        run = dense._embedding_run
        _contract(run)
        expected = {"python": platform.python_version(), "threads": 1, "seed": 0,
                    "deterministic_algorithms": True, "normalization": "l2",
                    "tokenizer": "pinned-model; special tokens included; truncation=false"}
        packages = ("numpy", "torch", "sentence-transformers", "transformers", "tokenizers", "huggingface-hub")
        if (any(run.get(key) != value for key, value in expected.items())
                or run.get("packages") != {name: version(name) for name in packages}
                or type(run.get("batch_size")) is not int or run["batch_size"] < 1):
            raise ValueError("Query encoder runtime differs from embedding run; rebuild approved artifacts")

    def search(self, query: str, k: int = 50) -> tuple[FusionResult, ...]:
        return self.search_with_details(query, k).hybrid

    def search_with_details(self, query: str, k: int = 50) -> HybridSearchResponse:
        validate_cutoff(k)
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be nonempty text")
        self._validate_indexes()
        if self._model is None:
            self._model = load_model(self._cache)
        text = query.strip()
        count = len(self._model.tokenizer(text, add_special_tokens=True, truncation=False,
                                         padding=False, verbose=False)["input_ids"])
        if count > MAX_TOKENS:
            raise ValueError("Query exceeds 256 tokens; silent truncation is prohibited")
        vectors = self._model.encode([text], batch_size=self._dense._embedding_run["batch_size"],
            show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=False)
        query_vector = validate_vector_matrix(vectors, 1)[0]
        dense = self._dense.search(query_vector, k=CANDIDATE_WINDOW)
        lexical = BM25Search(self._lexical).search(text, k=CANDIDATE_WINDOW)
        hybrid = fuse_rankings({"dense": dense, "bm25": lexical}, k=k)
        return HybridSearchResponse(dense, lexical, hybrid, count)
