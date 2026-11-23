"""Spec 112: tests de contextualización en el Indexer."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from docuchat.config import Settings
from docuchat.evaluation.variants import VARIANTS, parse_variants, variant_settings
from docuchat.index.contextualizer import ContextCache
from docuchat.index.fts import FtsIndex
from docuchat.index.indexer import Indexer, build_indexer, reset_index
from docuchat.index.registry import Registry
from docuchat.index.vector_store import VectorStore
from docuchat.models import Chunk, Document

# ── Copia de FakeEmbedder de tests/index/test_indexer.py ────────────────


class FakeEmbedder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.texts: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        self.texts.extend(texts)
        return [[float(len(t)), 1.0, 0.5] for t in texts]


# ── Fixture docs (copia de tests/index/test_indexer.py) ────────────────


@pytest.fixture()
def docs(tmp_path: Path) -> Path:
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.md").write_text("# Alfa\n\nPrimer párrafo de alfa.\n\n## Beta\n\nTexto de beta.\n")
    (d / "b.txt").write_text("Notas de la reunión.\n")
    (d / "c.md").write_text("# Gamma\n\nMás notas sobre el tema.\n")
    return d


# ── FakeContextualizer ─────────────────────────────────────────────────


class FakeContextualizer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    @property
    def llm_calls(self) -> int:
        return len(self.calls)

    def context_for(self, doc: Document, chunk: Chunk) -> str:
        self.calls.append(chunk.chunk_id)
        return f"Contexto de {doc.source} p{chunk.page}"


# ── Fixture parts ──────────────────────────────────────────────────────


@pytest.fixture()
def parts(tmp_path: Path) -> Iterator[tuple[VectorStore, Registry, FtsIndex]]:
    store = VectorStore(tmp_path / "chroma", "chunks", "fake")
    registry = Registry(tmp_path / "r.sqlite3")
    fts = FtsIndex(tmp_path / "fts.sqlite3")
    yield store, registry, fts
    registry.close()


def make(parts, ctx=None, emb=None) -> Indexer:
    store, registry, fts = parts
    return Indexer(store, registry, emb or FakeEmbedder(), 800, 120, fts=fts, contextualizer=ctx)


# ── Tests ──────────────────────────────────────────────────────────────


def test_rellena_contexto(parts, docs) -> None:
    ctx = FakeContextualizer()
    idx = make(parts, ctx)
    idx.index_folder(docs)
    chunks = idx._store.all_chunks()
    for c in chunks:
        assert c.context == f"Contexto de {c.source} p{c.page}"
        assert not c.text.startswith("Contexto")
    idx.close()


def test_embedder_y_fts_ven_el_contexto(parts, docs) -> None:
    ctx = FakeContextualizer()
    idx = make(parts, ctx)
    idx.index_folder(docs)
    assert any(
        "Contexto de b.txt p1\n\nNotas de la reunión." in t
        for call in idx._embedder.calls
        for t in call
    )
    assert len(idx._fts.search("contexto", 10)) == 4
    idx.close()


def test_stats(parts, docs) -> None:
    ctx = FakeContextualizer()
    idx = make(parts, ctx)
    stats = idx.index_folder(docs)
    assert stats.contexts_generated == 4
    # Segunda pasada sin cambios
    stats2 = idx.index_folder(docs)
    assert stats2.contexts_generated == 0
    assert len(ctx.calls) == 4
    idx.close()


def test_sin_contextualizador(parts, docs) -> None:
    idx = make(parts, ctx=None)
    stats = idx.index_folder(docs)
    chunks = idx._store.all_chunks()
    for c in chunks:
        assert c.context == ""
    assert stats.contexts_generated == 0
    idx.close()


def test_error_de_contexto_va_a_errors(docs, tmp_path) -> None:
    store = VectorStore(tmp_path / "chroma", "chunks", "fake")
    registry = Registry(tmp_path / "r.sqlite3")
    fts = FtsIndex(tmp_path / "fts.sqlite3")
    embedder = FakeEmbedder()

    class FailingContextualizer:
        def __init__(self) -> None:
            self.calls: list[str] = []

        @property
        def llm_calls(self) -> int:
            return len(self.calls)

        def context_for(self, doc: Document, chunk: Chunk) -> str:
            if doc.source == "b.txt":
                raise RuntimeError("roto")
            self.calls.append(chunk.chunk_id)
            return f"Contexto de {doc.source} p{chunk.page}"

    ctx = FailingContextualizer()
    idx = Indexer(store, registry, embedder, 800, 120, fts=fts, contextualizer=ctx)
    # Solo a.md y b.txt para que c.md no afecte
    docs_small = tmp_path / "docs_small"
    docs_small.mkdir()
    (docs_small / "a.md").write_text("# Alfa\n\nPrimer párrafo de alfa.\n")
    (docs_small / "b.txt").write_text("Notas de la reunión.\n")
    stats = idx.index_folder(docs_small)
    assert stats.added == ["a.md"]
    assert len(stats.errors) >= 1
    assert stats.errors[0][0] == "b.txt"
    assert "RuntimeError: roto" in stats.errors[0][1]
    idx.close()


def test_migracion_conserva_contexto(docs, tmp_path) -> None:
    store = VectorStore(tmp_path / "chroma", "chunks", "fake")
    registry = Registry(tmp_path / "r.sqlite3")
    fts = FtsIndex(tmp_path / "fts.sqlite3")
    ctx = FakeContextualizer()
    idx = Indexer(store, registry, FakeEmbedder(), 800, 120, fts=fts, contextualizer=ctx)
    idx.index_folder(docs)
    idx.close()

    fts2 = FtsIndex(tmp_path / "fts2.sqlite3")
    from docuchat.index.indexer import sync_fts

    sync_fts(store, fts2)
    assert len(fts2.search("contexto", 10)) == 4


def test_build_indexer_contextual(settings: Settings) -> None:
    call_count = {"n": 0}
    fake_result = FakeContextualizer()

    import docuchat.index.indexer as mod

    original = mod.make_contextualizer
    mod.make_contextualizer = lambda s: (
        call_count.__setitem__("n", call_count["n"] + 1) or fake_result
    )

    try:
        indexer = build_indexer(
            settings.model_copy(update={"contextual_enabled": True}),
            embedder=FakeEmbedder(),
        )
        assert call_count["n"] == 1
        assert indexer._contextualizer is fake_result
        indexer.close()

        indexer2 = build_indexer(
            settings.model_copy(update={"contextual_enabled": False}),
            embedder=FakeEmbedder(),
        )
        assert indexer2._contextualizer is None
        indexer2.close()
    finally:
        mod.make_contextualizer = original


def test_conftest_sin_contextualizador_real(settings: Settings) -> None:
    idx = build_indexer(
        settings.model_copy(update={"contextual_enabled": True}),
        embedder=FakeEmbedder(),
    )
    assert idx._contextualizer is None
    idx.close()


def test_reset_no_borra_la_cache(settings: Settings) -> None:
    cache = ContextCache(settings.context_cache_path)
    cache.put("k", "v")
    reset_index(settings)
    cache2 = ContextCache(settings.context_cache_path)
    assert cache2.get("k") == "v"


def test_variantes() -> None:
    assert VARIANTS["contextual"] == {"contextual_enabled": True}
    assert VARIANTS["contextual_sin_rerank"] == {
        "contextual_enabled": True,
        "rerank_enabled": False,
    }
    result = parse_variants("base,contextual,contextual_sin_rerank,sin_rerank")
    assert result == ["base", "contextual", "contextual_sin_rerank", "sin_rerank"]
    vs = variant_settings(Settings(), "contextual")
    assert vs.rerank_enabled is True
