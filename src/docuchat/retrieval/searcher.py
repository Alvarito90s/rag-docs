"""Buscador híbrido: vectorial + BM25 con fusión RRF y reranker opcional."""

import logging
from enum import StrEnum

from docuchat.config import Settings
from docuchat.index.bm25 import Bm25Index
from docuchat.index.embeddings import Embedder, make_embedder
from docuchat.index.vector_store import VectorStore
from docuchat.models import Chunk, SearchResult
from docuchat.retrieval.fusion import drop_adjacent, rrf_fuse
from docuchat.retrieval.reranker import Reranker, RerankError, make_reranker

logger = logging.getLogger(__name__)


class SearchMode(StrEnum):
    """Modos de búsqueda."""

    HYBRID = "hybrid"
    VECTOR = "vector"
    BM25 = "bm25"


def format_query(query: str, instruction: str) -> str:
    """Antepone la instrucción de embedding: 'Instruct: {instruction}\nQuery:{query}'."""
    if not instruction:
        return query
    return f"Instruct: {instruction}\nQuery:{query}"


class Searcher:
    """Búsqueda híbrida sobre VectorStore; el índice BM25 se construye en memoria la primera vez."""

    def __init__(
        self,
        store: VectorStore,
        embedder: Embedder,
        *,
        candidate_k: int,
        rrf_k: int,
        query_instruction: str,
        reranker: Reranker | None = None,
        rerank_candidates: int = 20,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._candidate_k = candidate_k
        self._rrf_k = rrf_k
        self._query_instruction = query_instruction
        self._reranker = reranker
        self._rerank_candidates = rerank_candidates
        self._cache: tuple[dict[str, Chunk], Bm25Index] | None = None

    def size(self) -> int:
        """Número de chunks indexados."""
        return self._store.count()

    def refresh(self) -> None:
        """Olvida la caché interna; se reconstruye en la siguiente búsqueda."""
        self._cache = None

    def search(
        self, query: str, top_k: int, mode: SearchMode = SearchMode.HYBRID
    ) -> list[SearchResult]:
        """Los top_k chunks más relevantes para query."""
        if not query.strip() or top_k <= 0:
            return []

        # Lazy init
        if self._cache is None:
            chunks = self._store.all_chunks()
            if not chunks:
                return []
            cache_map = {c.chunk_id: c for c in chunks}
            ids = list(cache_map)
            texts = [cache_map[cid].text for cid in ids]
            self._cache = (cache_map, Bm25Index(ids, texts))

        cache, bm25 = self._cache
        vector_ids: list[str] = []
        bm25_ids: list[str] = []

        if mode in (SearchMode.HYBRID, SearchMode.VECTOR):
            vector = self._embedder.embed([format_query(query, self._query_instruction)])[0]
            hits = self._store.query(vector, self._candidate_k)
            vector_ids = [c.chunk_id for c, _ in hits]
            for c, _ in hits:
                cache[c.chunk_id] = c

        if mode in (SearchMode.HYBRID, SearchMode.BM25):
            bm25_results = bm25.search(query, self._candidate_k)
            bm25_ids = [i for i, _ in bm25_results]

        # rankings según mode
        if mode == SearchMode.HYBRID:
            rankings = [vector_ids, bm25_ids]
        elif mode == SearchMode.VECTOR:
            rankings = [vector_ids]
        else:
            rankings = [bm25_ids]

        fused = rrf_fuse(rankings, self._rrf_k)
        ordered = [cache[i] for i, _ in fused]
        kept = drop_adjacent(ordered)

        # Mapas de posición (desde 1)
        vector_map: dict[str, int] = {cid: i + 1 for i, cid in enumerate(vector_ids)}
        bm25_map: dict[str, int] = {cid: i + 1 for i, cid in enumerate(bm25_ids)}
        fused_scores = dict(fused)

        # Rerank opcional
        rerank_scores: list[float] | None = None
        ordered_indices: list[int] = []
        if self._reranker is not None and len(kept) > 0:
            try:
                pool = kept[: max(self._rerank_candidates, top_k)]
                scores = self._reranker.rerank(query, [c.text for c in pool])
                ordered_indices = sorted(range(len(pool)), key=lambda i: -scores[i])
                kept = [pool[i] for i in ordered_indices[:top_k]]
                rerank_scores = scores
            except RerankError as e:
                logger.warning("Reranker no disponible; uso el orden RRF: %s", e)
                rerank_scores = None

        return [
            SearchResult(
                chunk=chunk,
                rank=rank,
                score=fused_scores[chunk.chunk_id],
                vector_rank=vector_map.get(chunk.chunk_id),
                bm25_rank=bm25_map.get(chunk.chunk_id),
                rerank_score=(
                    rerank_scores[ordered_indices[rank - 1]] if rerank_scores is not None else None
                ),
            )
            for rank, chunk in enumerate(kept[:top_k], start=1)
        ]


def build_searcher(settings: Settings, embedder: Embedder | None = None) -> Searcher:
    """Crea el Searcher con el VectorStore y los parámetros de settings."""
    store = VectorStore(settings.chroma_dir, settings.chroma_collection, settings.embedding_model)
    reranker = make_reranker(settings) if settings.rerank_enabled else None
    return Searcher(
        store,
        embedder or make_embedder(settings),
        candidate_k=settings.candidate_k,
        rrf_k=settings.rrf_k,
        query_instruction=settings.query_instruction,
        reranker=reranker,
        rerank_candidates=settings.rerank_candidates,
    )
