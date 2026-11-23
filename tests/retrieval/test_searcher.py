"""Tests para searcher.py (Searcher, format_query, build_searcher)."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from docuchat.index.bm25 import tokenize
from docuchat.index.vector_store import VectorStore
from docuchat.models import Chunk, make_chunk_id
from docuchat.retrieval.searcher import Searcher, SearchMode, build_searcher, format_query

# ── Embedder falso por palabras clave ──────────────────────────────────────

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


class TestSearcher:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path):
        self.store = VectorStore(tmp_path / "chroma", "chunks", "fake")
        embedder_corpus = KeywordEmbedder()
        self.store.add(CORPUS, embedder_corpus.embed([c.text for c in CORPUS]))
        self.searcher = Searcher(
            self.store,
            KeywordEmbedder(),
            candidate_k=20,
            rrf_k=60,
            query_instruction=INSTR,
        )

    # ── format_query ───────────────────────────────────────────────────────

    def test_format_query_with_instruction(self):
        assert format_query("hola", "Busca") == "Instruct: Busca\nQuery:hola"

    def test_format_query_empty_instruction(self):
        assert format_query("hola", "") == "hola"

    # ── Híbrido ────────────────────────────────────────────────────────────

    def test_hybrid_cafetera(self):
        results = self.searcher.search("cafetera", 1)
        r = results[0]
        assert r.chunk.chunk_id == "b.pdf#p3#c0"
        assert r.rank == 1
        assert r.vector_rank == 1
        assert r.bm25_rank == 1
        assert r.score == pytest.approx(2 / 61)

    # ── Vectorial con deduplicación ────────────────────────────────────────

    def test_vector_dedup(self):
        results = self.searcher.search("garantia del contrato", 5, SearchMode.VECTOR)
        ids = [r.chunk.chunk_id for r in results]
        assert ids == ["a.pdf#p1#c1", "b.pdf#p3#c0", "c.md#p1#c0"]
        vector_ranks = [r.vector_rank for r in results]
        assert vector_ranks == [1, 3, 4]
        bm25_ranks = [r.bm25_rank for r in results]
        assert bm25_ranks == [None, None, None]
        ranks = [r.rank for r in results]
        assert ranks == [1, 2, 3]

    # ── BM25 ───────────────────────────────────────────────────────────────

    def test_bm25(self):
        results = self.searcher.search("garantia del contrato", 5, SearchMode.BM25)
        ids = [r.chunk.chunk_id for r in results]
        assert ids == ["a.pdf#p1#c0", "b.pdf#p3#c0"]
        bm25_ranks = [r.bm25_rank for r in results]
        assert bm25_ranks == [1, 3]
        vector_ranks = [r.vector_rank for r in results]
        assert vector_ranks == [None, None]

    def test_bm25_rescates_proper_noun(self):
        results = self.searcher.search("Valladolid", 1)
        assert results[0].chunk.chunk_id == "a.pdf#p1#c0"
        assert results[0].bm25_rank == 1

    # ── Instrucción ────────────────────────────────────────────────────────

    def test_query_instruction(self):
        self.searcher.search("cafetera", 1)
        assert self.searcher._embedder.calls == [[f"Instruct: {INSTR}\nQuery:cafetera"]]

    def test_query_instruction_empty(self):
        self.searcher._query_instruction = ""
        self.searcher.search("cafetera", 1)
        assert self.searcher._embedder.calls == [["cafetera"]]

    # ── Casos vacíos ───────────────────────────────────────────────────────

    def test_empty_query(self):
        assert self.searcher.search("   ", 5) == []
        assert self.searcher._embedder.calls == []

    def test_zero_top_k(self):
        assert self.searcher.search("cafetera", 0) == []
        assert self.searcher._embedder.calls == []

    # ── Store vacío ────────────────────────────────────────────────────────

    def test_empty_store(self):
        empty_store = VectorStore(Path("data/test_empty_chroma"), "chunks", "fake")
        empty_searcher = Searcher(
            empty_store,
            KeywordEmbedder(),
            candidate_k=20,
            rrf_k=60,
            query_instruction=INSTR,
        )
        assert empty_searcher.size() == 0
        assert empty_searcher.search("cafetera", 5) == []
        assert empty_searcher._embedder.calls == []

    # ── refresh ────────────────────────────────────────────────────────────

    def test_refresh(self):
        # Primera búsqueda BM25
        r1 = self.searcher.search("Valladolid", 5, SearchMode.BM25)
        assert len(r1) == 1

        # Añadimos un chunk con "Valladolid"
        new_chunk = mk("d.txt", 1, 0, "Valladolid en invierno.")
        self.store.add([new_chunk], [[0.01] * 5])

        # Sin refresh → sigue 1 resultado
        r2 = self.searcher.search("Valladolid", 5, SearchMode.BM25)
        assert len(r2) == 1

        # Tras refresh → 2 resultados
        self.searcher.refresh()
        r3 = self.searcher.search("Valladolid", 5, SearchMode.BM25)
        ids = {r.chunk.chunk_id for r in r3}
        assert ids == {"a.pdf#p1#c0", "d.txt#p1#c0"}

    # ── Caché con índice vacío ─────────────────────────────────────────────

    def test_empty_then_filled(self, tmp_path: Path):
        # Store vacío → search devuelve [] sin cachear nada
        empty_store = VectorStore(tmp_path / "empty", "chunks", "fake")
        s = Searcher(
            empty_store,
            KeywordEmbedder(),
            candidate_k=20,
            rrf_k=60,
            query_instruction=INSTR,
        )
        assert s.search("cafetera", 5) == []

        # Añadimos el corpus sin refresh
        empty_store.add(CORPUS, KeywordEmbedder().embed([c.text for c in CORPUS]))

        # Buscamos de nuevo: debería encontrar el resultado
        results = s.search("cafetera", 1)
        assert len(results) == 1
        assert results[0].chunk.chunk_id == "b.pdf#p3#c0"

    # ── build_searcher ─────────────────────────────────────────────────────

    def test_build_searcher(self, settings):
        searcher = build_searcher(settings, embedder=KeywordEmbedder())
        assert searcher.size() == 0
        assert searcher.search("hola", 5) == []
