"""Spec 110: tests de index_text y el campo context."""

from collections.abc import Sequence
from pathlib import Path

from docuchat.index.fts import FtsIndex
from docuchat.index.indexer import Indexer
from docuchat.index.registry import Registry
from docuchat.index.vector_store import VectorStore, chunk_from_record
from docuchat.models import Chunk, index_text, make_chunk_id
from docuchat.retrieval.searcher import Searcher, SearchMode


def mk(text: str = "Llena el depósito.", context: str = "", position: int = 0) -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id("k1.pdf", 2, position),
        source="k1.pdf",
        doc_sha256="a" * 64,
        page=2,
        position=position,
        text=text,
        context=context,
    )


def test_index_text_sin_contexto() -> None:
    assert index_text(mk()) == "Llena el depósito."
    assert index_text(mk(context="   ")) == "Llena el depósito."


def test_index_text_con_contexto() -> None:
    result = index_text(mk(context=" Manual del Termia K1. "))
    assert result == "Manual del Termia K1.\n\nLlena el depósito."


def test_por_defecto_vacio() -> None:
    c = Chunk(
        chunk_id=make_chunk_id("x.pdf", 1, 0),
        source="x.pdf",
        doc_sha256="a" * 64,
        page=1,
        position=0,
        text="hola",
    )
    assert c.context == ""


def test_metadatos_ida_y_vuelta(tmp_path: Path) -> None:
    store = VectorStore(tmp_path / "c", "chunks", "fake")
    c = mk(context="Manual del Termia K1.")
    store.add([c], [[1.0, 0.0, 0.5]])
    chunks = store.get_chunks([c.chunk_id])
    assert len(chunks) == 1
    assert chunks[0].context == "Manual del Termia K1."
    assert chunks[0].text == "Llena el depósito."


def test_indice_antiguo_sin_clave() -> None:
    c = chunk_from_record(
        "x#p1#c0",
        "hola",
        {
            "source": "x",
            "doc_sha256": "a" * 64,
            "page": "1",
            "position": "0",
            "heading": "",
        },
    )
    assert c.context == ""


class FakeEmbedder:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.texts.extend(texts)
        return [[0.0] * 3 for _ in texts]


class FakeReranker:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def rerank(self, query: str, texts: list[str]) -> list[float]:
        self.texts.extend(texts)
        return [0.0] * len(texts)


def test_fts_busca_en_el_contexto(tmp_path: Path) -> None:
    fts = FtsIndex(tmp_path / "fts.sqlite3")
    c = mk(context="Manual del Termia K1.")
    fts.add([c])
    resultados = fts.search("termia", 5)
    ids = [r[0] for r in resultados]
    assert c.chunk_id in ids
    resultados = fts.search("deposito", 5)
    ids = [r[0] for r in resultados]
    assert c.chunk_id in ids


def test_reranker_recibe_index_text(tmp_path: Path) -> None:
    store = VectorStore(tmp_path / "chroma", "chunks", "fake")
    c1 = mk(context="Manual del Termia K1.")
    c2 = mk(text="Otro texto distinto.", position=1)
    store.add([c1, c2], [[1.0, 0.0, 0.5], [0.0, 1.0, 0.5]])
    fts = FtsIndex(tmp_path / "fts.sqlite3")
    fts.add([c1, c2])
    reranker = FakeReranker()
    fake_embedder = FakeEmbedder()
    searcher = Searcher(
        store,
        fake_embedder,
        fts=fts,
        candidate_k=20,
        rrf_k=60,
        query_instruction="",
        reranker=reranker,
        rerank_candidates=10,
    )
    searcher.search("deposito termia", 5, SearchMode.BM25)
    assert "Manual del Termia K1.\n\nLlena el depósito." in reranker.texts
    resultados = store.get_chunks([c1.chunk_id])
    assert len(resultados) == 1
    assert resultados[0].text == "Llena el depósito."


def test_embedder_recibe_index_text(tmp_path: Path) -> None:
    import docuchat.index.indexer as indexer_mod

    store = VectorStore(tmp_path / "chroma", "chunks", "fake")
    registry = Registry(tmp_path / "r.sqlite3")
    embedder = FakeEmbedder()
    fts = FtsIndex(tmp_path / "fts.sqlite3")
    indexer = Indexer(store, registry, embedder, 800, 120, fts=fts)

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "a.txt").write_text("contenido")

    original_chunk_document = indexer_mod.chunk_document
    indexer_mod.chunk_document = lambda doc, cs, co: [mk(context="Manual del Termia K1.")]
    try:
        indexer.index_folder(docs_dir)
    finally:
        indexer_mod.chunk_document = original_chunk_document

    assert "Manual del Termia K1.\n\nLlena el depósito." in embedder.texts
    indexer.close()
