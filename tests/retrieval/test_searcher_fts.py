"""Tests para FTS en Searcher (spec 103)."""

from collections.abc import Sequence
from pathlib import Path

from docuchat.index.fts import FtsIndex, tokenize
from docuchat.index.indexer import sync_fts
from docuchat.index.vector_store import VectorStore
from docuchat.models import Chunk, make_chunk_id
from docuchat.retrieval.searcher import Searcher, SearchMode, build_searcher

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


class TestSearcherFts:
    """Tests de interacción Searcher ↔ FTS (spec 103)."""

    # ── 1. test_no_usa_all_chunks ──────────────────────────────────────────

    def test_no_usa_all_chunks(self, tmp_path: Path):
        """Searcher no llama a all_chunks(); usa FTS."""
        store = VectorStore(tmp_path / "chroma", "chunks", "fake")
        store.add(CORPUS, KeywordEmbedder().embed([c.text for c in CORPUS]))
        fts = FtsIndex(tmp_path / "fts.sqlite3")
        sync_fts(store, fts)
        searcher = Searcher(
            store,
            KeywordEmbedder(),
            fts=fts,
            candidate_k=20,
            rrf_k=60,
            query_instruction=INSTR,
        )
        # BM25: solo chunks que contienen "garantia"
        results = searcher.search("garantia", 4, SearchMode.BM25)
        ids = [r.chunk.chunk_id for r in results]
        assert ids == ["a.pdf#p1#c1", "b.pdf#p3#c0"]

    # ── 2. test_bm25_sin_embedder ──────────────────────────────────────────

    def test_bm25_sin_embedder(self, tmp_path: Path):
        """BM25 no llama al embedder."""
        store = VectorStore(tmp_path / "chroma", "chunks", "fake")
        embedder = KeywordEmbedder()
        store.add(CORPUS, embedder.embed([c.text for c in CORPUS]))
        fts = FtsIndex(tmp_path / "fts.sqlite3")
        sync_fts(store, fts)
        searcher = Searcher(
            store,
            KeywordEmbedder(),
            fts=fts,
            candidate_k=20,
            rrf_k=60,
            query_instruction=INSTR,
        )
        results = searcher.search("garantia", 4, SearchMode.BM25)
        ids = [r.chunk.chunk_id for r in results]
        assert ids == ["a.pdf#p1#c1", "b.pdf#p3#c0"]
        assert results[0].chunk == CORPUS[1]
        assert len(searcher._embedder.calls) == 0

    # ── 3. test_fts_desfasado ─────────────────────────────────────────────

    def test_fts_desfasado(self, tmp_path: Path):
        """Chunks en FTS pero no en Chroma no aparecen en los resultados."""
        store = VectorStore(tmp_path / "chroma", "chunks", "fake")
        store.add(CORPUS, KeywordEmbedder().embed([c.text for c in CORPUS]))
        fts = FtsIndex(tmp_path / "fts.sqlite3")
        sync_fts(store, fts)
        # Phantom chunk en FTS solo
        phantom = mk("z.md", 1, 0, "Este es un fantasma en FTS.")
        fts.add([phantom])
        searcher = Searcher(
            store,
            KeywordEmbedder(),
            fts=fts,
            candidate_k=20,
            rrf_k=60,
            query_instruction=INSTR,
        )
        # "fantasma" solo está en FTS → no se encuentra porque el chunk no existe en Chroma
        results = searcher.search("fantasma", 5, SearchMode.BM25)
        assert results == []
        # Asegurar que z.md#p1#c0 no aparece en resultados de "garantia"
        results_gar = searcher.search("garantia", 5, SearchMode.BM25)
        ids = [r.chunk.chunk_id for r in results_gar]
        assert "z.md#p1#c0" not in ids

    # ── 4. test_store_vacio ───────────────────────────────────────────────

    def test_store_vacio(self, tmp_path: Path):
        """Store vacío + FTS lleno → search devuelve []."""
        store = VectorStore(tmp_path / "chroma", "chunks", "fake")
        fts = FtsIndex(tmp_path / "fts.sqlite3")
        fts.add(CORPUS)
        embedder = KeywordEmbedder()
        searcher = Searcher(
            store,
            embedder,
            fts=fts,
            candidate_k=20,
            rrf_k=60,
            query_instruction=INSTR,
        )
        # count() == 0 → search devuelve [] inmediatamente
        results = searcher.search("garantia", 5, SearchMode.BM25)
        assert results == []
        # embedder no debe haber sido llamado
        assert len(embedder.calls) == 0

    # ── 5. test_build_searcher_sincorporiza ────────────────────────────────

    def test_build_searcher_sincroniza(self, tmp_path: Path):
        """build_searcher sincroniza FTS con Chroma."""
        import os

        for key in list(os.environ):
            if key.startswith("DOCUCHAT_"):
                os.environ.pop(key)
        os.chdir(tmp_path)

        from docuchat.config import Settings
        from docuchat.index.fts import FtsIndex
        from docuchat.index.indexer import build_indexer

        SAMPLES = Path(__file__).resolve().parents[2] / "samples"

        settings = Settings(documents_dir=SAMPLES, data_dir=tmp_path / "data")
        embedder = KeywordEmbedder()
        indexer = build_indexer(settings, embedder=embedder)
        indexer.index_folder(SAMPLES)
        indexer.close()

        # Construir searcher: debe sincronizar FTS
        build_searcher(settings, embedder=KeywordEmbedder())

        # FtsIndex debería tener al menos 4 chunks (sincronizados desde Chroma)
        fts = FtsIndex(settings.fts_path)
        assert fts.count() >= 4
