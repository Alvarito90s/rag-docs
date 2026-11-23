"""Tests para integración del reranker en Searcher (spec 092)."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from docuchat.index.fts import FtsIndex, tokenize
from docuchat.index.indexer import sync_fts
from docuchat.index.vector_store import VectorStore
from docuchat.models import Chunk, SearchResult, make_chunk_id
from docuchat.retrieval.reranker import RerankError
from docuchat.retrieval.searcher import Searcher, SearchMode, build_searcher

# ── Embedded por palabras clave ────────────────────────────────────────────

VOCAB = ["contrato", "cafetera", "garantia", "vacaciones"]
INSTR = "Given a question, retrieve passages that answer the question"


class KeywordEmbedder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        out = []
        for t in texts:
            tokens = tokenize(t)
            out.append([float(tokens.count(w)) for w in VOCAB] + [0.01])
        return out


# ── Corpus ─────────────────────────────────────────────────────────────────


def mk(source: str, page: int, position: int, text: str = "x") -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id(source, page, position),
        source=source,
        doc_sha256="a" * 64,
        page=page,
        position=position,
        text=text,
    )


CORPUS = [
    mk("a.pdf", 1, 0, "El contrato se firma en Valladolid."),
    mk("a.pdf", 1, 1, "El contrato incluye garantia de dos años."),
    mk("b.pdf", 3, 0, "La cafetera tiene garantia de tres años."),
    mk("c.md", 1, 0, "Política de vacaciones para el personal."),
]

# Referencia: searcher(store).search("garantia", 4) da los ids:
# ["a.pdf#p1#c1", "b.pdf#p3#c0", "c.md#p1#c0"]
# a.pdf#p1#c0 se descarta por contiguo.


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture()
def store(tmp_path: Path) -> VectorStore:
    st = VectorStore(tmp_path / "chroma", "chunks", "fake")
    st.add(CORPUS, KeywordEmbedder().embed([c.text for c in CORPUS]))
    return st


@pytest.fixture()
def fts(tmp_path: Path, store: VectorStore) -> FtsIndex:
    f = FtsIndex(tmp_path / "fts.sqlite3")
    sync_fts(store, f)
    return f


def make_searcher(
    store: VectorStore,
    fts: FtsIndex,
    reranker: object | None = None,
    rerank_candidates: int = 20,
) -> Searcher:
    return Searcher(
        store,
        KeywordEmbedder(),
        fts=fts,
        candidate_k=20,
        rrf_k=60,
        query_instruction=INSTR,
        reranker=reranker,  # type: ignore[arg-type]
        rerank_candidates=rerank_candidates,
    )


class FakeReranker:
    """Puntúa 1.0 los textos que contienen `prefer` y 0.0 el resto; guarda las llamadas."""

    def __init__(self, prefer: str = "cafetera", error: Exception | None = None) -> None:
        self.prefer = prefer
        self.error = error
        self.calls: list[list[str]] = []

    def rerank(self, query: str, texts: Sequence[str]) -> list[float]:
        self.calls.append(list(texts))
        if self.error is not None:
            raise self.error
        return [1.0 if self.prefer in t else 0.0 for t in texts]


# ── Tests ──────────────────────────────────────────────────────────────────


def test_sin_reranker_igual(store: VectorStore, fts: FtsIndex):
    """Sin reranker, los resultados son idénticos a la referencia."""
    ref_ids = ["a.pdf#p1#c1", "b.pdf#p3#c0", "c.md#p1#c0"]
    results = make_searcher(store, fts).search("garantia", 4)
    assert [r.chunk.chunk_id for r in results] == ref_ids
    assert all(r.rerank_score is None for r in results)


def test_reordena(store: VectorStore, fts: FtsIndex):
    """Con FakeReranker() el primer resultado es el que contiene 'cafetera'."""
    reranker = FakeReranker()
    results = make_searcher(store, fts, reranker=reranker).search("garantia", 4)
    assert [r.chunk.chunk_id for r in results] == ["b.pdf#p3#c0", "a.pdf#p1#c1", "c.md#p1#c0"]
    assert [r.rank for r in results] == [1, 2, 3]
    assert [r.rerank_score for r in results] == [1.0, 0.0, 0.0]


def test_score_rrf_se_conserva(store: VectorStore, fts: FtsIndex):
    """El score RRF, vector_rank y bm25_rank no cambian tras rerank."""
    ref = make_searcher(store, fts).search("garantia", 4)
    reranked = make_searcher(store, fts, reranker=FakeReranker()).search("garantia", 4)

    ref_map = {r.chunk.chunk_id: r for r in ref}
    for r in reranked:
        assert r.score == ref_map[r.chunk.chunk_id].score
        assert r.vector_rank == ref_map[r.chunk.chunk_id].vector_rank
        assert r.bm25_rank == ref_map[r.chunk.chunk_id].bm25_rank


def test_pool(store: VectorStore, fts: FtsIndex):
    """Con rerank_candidates=2 y top_k=1, el pool es de 2 textos."""
    reranker = FakeReranker()
    results = make_searcher(store, fts, reranker=reranker, rerank_candidates=2).search(
        "garantia", 1
    )
    assert reranker.calls == [
        [
            "El contrato incluye garantia de dos años.",
            "La cafetera tiene garantia de tres años.",
        ]
    ]
    assert [r.chunk.chunk_id for r in results] == ["b.pdf#p3#c0"]


def test_pool_minimo_top_k(store: VectorStore, fts: FtsIndex):
    """Con rerank_candidates=1 y top_k=3, el pool es de 3 textos (mínimo top_k)."""
    reranker = FakeReranker()
    make_searcher(store, fts, reranker=reranker, rerank_candidates=1).search("garantia", 3)
    assert len(reranker.calls[0]) == 3


def test_empates_estables(store: VectorStore, fts: FtsIndex):
    """Reranker con puntuaciones iguales mantiene orden RRF."""
    reranker_equal = FakeReranker()
    reranker_equal.rerank = lambda query, texts: [0.5 for _ in texts]  # type: ignore[assignment]
    ref = make_searcher(store, fts).search("garantia", 4)
    ref_ids = [r.chunk.chunk_id for r in ref]
    results = make_searcher(store, fts, reranker=reranker_equal).search("garantia", 4)
    assert [r.chunk.chunk_id for r in results] == ref_ids


def test_fallo_reranker(store: VectorStore, fts: FtsIndex, caplog: pytest.LogCaptureFixture):
    """RerankError → fallback a orden RRF, rerank_score None, log."""
    import logging

    reranker = FakeReranker(error=RerankError("caído"))
    caplog.set_level(logging.WARNING)
    results = make_searcher(store, fts, reranker=reranker).search("garantia", 4)
    ref_ids = ["a.pdf#p1#c1", "b.pdf#p3#c0", "c.md#p1#c0"]
    assert [r.chunk.chunk_id for r in results] == ref_ids
    assert all(r.rerank_score is None for r in results)
    assert "uso el orden RRF" in caplog.text


def test_otro_error_se_propaga(store: VectorStore, fts: FtsIndex):
    """Una excepción distinta de RerankError se propaga."""
    reranker = FakeReranker(error=ValueError("x"))
    with pytest.raises(ValueError):
        make_searcher(store, fts, reranker=reranker).search("garantia", 4)


def test_consulta_vacia(store: VectorStore, fts: FtsIndex):
    """Query vacía → [], sin llamar al reranker."""
    reranker = FakeReranker()
    results = make_searcher(store, fts, reranker=reranker).search("  ", 4)
    assert results == []
    assert reranker.calls == []


def test_modo_bm25(store: VectorStore, fts: FtsIndex):
    """Modo BM25 con reranker: primer resultado es el de 'cafetera'."""
    results = make_searcher(store, fts, reranker=FakeReranker()).search(
        "garantia", 4, SearchMode.BM25
    )
    assert results[0].chunk.chunk_id == "b.pdf#p3#c0"


def test_build_searcher_apagado(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Sin rerank_enabled → make_reranker no se llama."""
    import os

    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            os.environ.pop(key)
    monkeypatch.chdir(tmp_path)

    call_count = 0

    def fake_make_reranker(settings: object, transport: object = None) -> object:
        nonlocal call_count
        call_count += 1
        raise RuntimeError("no se debe llamar")

    monkeypatch.setattr("docuchat.retrieval.searcher.make_reranker", fake_make_reranker)

    from docuchat.config import Settings
    from tests.retrieval.test_rerank_searcher import KeywordEmbedder

    build_searcher(Settings(data_dir=tmp_path, rerank_enabled=False), embedder=KeywordEmbedder())
    assert call_count == 0


def test_build_searcher_encendido(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Con rerank_enabled=True → make_reranker se llama 1 vez."""
    import os

    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            os.environ.pop(key)
    monkeypatch.chdir(tmp_path)

    call_count = 0

    def fake_make_reranker(settings: object, transport: object = None) -> object:
        nonlocal call_count
        call_count += 1
        return FakeReranker()

    monkeypatch.setattr("docuchat.retrieval.searcher.make_reranker", fake_make_reranker)

    from docuchat.config import Settings
    from tests.retrieval.test_rerank_searcher import KeywordEmbedder

    build_searcher(
        Settings(data_dir=tmp_path, rerank_enabled=True),
        embedder=KeywordEmbedder(),
    )
    assert call_count == 1


def test_result_to_dict():
    """result_to_dict incluye rerank_score."""
    from docuchat.api.routes_api import result_to_dict

    # Sin rerank
    d = result_to_dict(SearchResult(chunk=CORPUS[0], rank=1, score=0.1))
    assert d["rerank_score"] is None

    # Con rerank
    d2 = result_to_dict(SearchResult(chunk=CORPUS[0], rank=1, score=0.1, rerank_score=0.7))
    assert d2["rerank_score"] == 0.7


def test_variante_rerank():
    """La variante 'rerank' existe y sus settings son correctos."""
    from docuchat.config import Settings
    from docuchat.evaluation.variants import VARIANTS, parse_variants, variant_settings

    assert VARIANTS["rerank"] == {"rerank_enabled": True}
    assert parse_variants("base,rerank") == ["base", "rerank"]
    assert variant_settings(Settings(), "rerank").rerank_enabled is True
