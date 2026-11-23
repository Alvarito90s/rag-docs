"""Spec 113: tests de MetaContextualizer, first_sentence y build_indexer con metadatos."""

from collections.abc import Sequence
from pathlib import Path

import httpx
import pytest
from openai import APIConnectionError

from docuchat.config import Settings
from docuchat.index.contextualizer import (
    MetaContextualizer,
    first_sentence,
    make_meta_contextualizer,
)
from docuchat.index.indexer import Indexer, build_indexer
from docuchat.index.registry import Registry
from docuchat.index.vector_store import VectorStore
from docuchat.models import Chunk, DocType, Document, Page, make_chunk_id

# ── Fixtures ───────────────────────────────────────────────────────────

# Copiado de tests/index/test_indexer.py


class FakeEmbedder:
    def __init__(self, fail_on: str | None = None) -> None:
        self.calls: list[list[str]] = []
        self.fail_on = fail_on

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self.fail_on is not None and any(self.fail_on in t for t in texts):
            raise APIConnectionError(request=httpx.Request("POST", "http://test"))
        return [[float(len(t)), 1.0, 0.5] for t in texts]


@pytest.fixture()
def docs(tmp_path: Path) -> Path:
    """Carpeta de documentos de prueba."""
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.md").write_text("# Alfa\n\nPrimer párrafo de alfa.\n\n## Beta\n\nTexto de beta.\n")
    (d / "b.txt").write_text("Notas de la reunión.\n")
    return d


# Copiado de tests/index/test_contextualizer.py


DOC = Document(
    source="k1.pdf",
    path=Path("/x/k1.pdf"),
    sha256="a" * 64,
    doc_type=DocType.PDF,
    pages=(
        Page(number=1, text="Manual del hervidor Termia K1."),
        Page(number=2, text="Uso diario. Llena el depósito."),
    ),
)

CHUNK = Chunk(
    chunk_id=make_chunk_id("k1.pdf", 2, 0),
    source="k1.pdf",
    doc_sha256="a" * 64,
    page=2,
    position=0,
    text="Llena el depósito.",
)


# ── Tests ──────────────────────────────────────────────────────────────


def test_first_sentence() -> None:
    assert first_sentence("Artículo 1. Objeto del reglamento.", 200) == "Artículo 1."
    assert (
        first_sentence("  Acta del\n\ncomité   de dirección", 200) == "Acta del comité de dirección"
    )
    assert first_sentence("¿Puedo? Sí.", 200) == "¿Puedo?"
    assert first_sentence("abc defgh. Otra.", 4) == "abc"
    assert first_sentence("", 200) == ""
    assert first_sentence(" \n ", 200) == ""


def test_context_for() -> None:
    result = MetaContextualizer(head_chars=400, max_chars=200).context_for(DOC, CHUNK)
    assert result == "Documento «k1.pdf». Manual del hervidor Termia K1."


def test_head_chars() -> None:
    result = MetaContextualizer(head_chars=6, max_chars=200).context_for(DOC, CHUNK)
    assert result == "Documento «k1.pdf». Manual"


def test_documento_vacio() -> None:
    doc = Document(
        source="k1.pdf",
        path=Path("/x/k1.pdf"),
        sha256="a" * 64,
        doc_type=DocType.PDF,
        pages=(Page(number=1, text="   "),),
    )
    result = MetaContextualizer(head_chars=400, max_chars=200).context_for(doc, CHUNK)
    assert result == "Documento «k1.pdf»."


def test_llm_calls() -> None:
    c = MetaContextualizer(head_chars=400, max_chars=200)
    c.context_for(DOC, CHUNK)
    c.context_for(DOC, CHUNK)
    assert c.llm_calls == 0


def test_indexer_con_metadatos(tmp_path: Path, docs: Path) -> None:
    store = VectorStore(tmp_path / "chroma", "chunks", "fake")
    registry = Registry(tmp_path / "r.sqlite3")
    emb = FakeEmbedder()
    from docuchat.index.fts import FtsIndex

    fts = FtsIndex(tmp_path / "fts.sqlite3")
    idx = Indexer(
        store,
        registry,
        emb,
        800,
        120,
        fts=fts,
        contextualizer=MetaContextualizer(head_chars=400, max_chars=200),
    )
    stats = idx.index_folder(docs)
    idx.close()

    assert stats.added == ["a.md", "b.txt"]

    # El embedder recibe el contexto con separación "\n\n" entre contexto y texto
    all_texts = [t for call in emb.calls for t in call]
    assert "Documento «b.txt». Notas de la reunión.\n\nNotas de la reunión." in all_texts

    chunks = store.all_chunks()
    b_chunk = [c for c in chunks if c.source == "b.txt"][0]
    assert b_chunk.text == "Notas de la reunión."

    results = fts.search("documento", 10)
    ids = [r[0] for r in results]
    assert len(ids) == 3
    assert {"a.md#p1#c0", "a.md#p2#c0", "b.txt#p1#c0"} == set(ids)

    assert stats.contexts_generated == 0


def test_settings(settings: Settings) -> None:
    assert settings.contextual_meta_enabled is True
    assert settings.contextual_meta_head_chars == 400
    assert settings.contextual_meta_max_chars == 200
    assert settings.contextual_enabled is False


def test_build_indexer_elige(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    llm_obj, meta_obj = object(), object()
    calls = {"llm": 0, "meta": 0}

    def fake_llm(s: Settings) -> object:
        calls["llm"] += 1
        return llm_obj

    def fake_meta(s: Settings) -> object:
        calls["meta"] += 1
        return meta_obj

    monkeypatch.setattr("docuchat.index.indexer.make_contextualizer", fake_llm)
    monkeypatch.setattr("docuchat.index.indexer.make_meta_contextualizer", fake_meta)

    idx = build_indexer(settings, embedder=FakeEmbedder())
    assert idx._contextualizer is meta_obj
    assert calls == {"llm": 0, "meta": 1}
    idx.close()

    idx = build_indexer(
        settings.model_copy(update={"contextual_enabled": True}),
        embedder=FakeEmbedder(),
    )
    assert idx._contextualizer is llm_obj
    assert calls == {"llm": 1, "meta": 1}
    idx.close()

    idx = build_indexer(
        settings.model_copy(update={"contextual_meta_enabled": False}),
        embedder=FakeEmbedder(),
    )
    assert idx._contextualizer is None
    assert calls == {"llm": 1, "meta": 1}
    idx.close()


def test_conftest_sin_metadatos(settings: Settings) -> None:
    """Sin parchear nada en el test, build_indexer debe devolver None."""
    idx = build_indexer(settings, embedder=FakeEmbedder())
    assert idx._contextualizer is None
    idx.close()


def test_make_meta_contextualizer(settings: Settings) -> None:
    result = make_meta_contextualizer(settings.model_copy(update={"contextual_meta_head_chars": 6}))
    assert result.context_for(DOC, CHUNK) == "Documento «k1.pdf». Manual"


def test_variante_sin_contexto() -> None:
    from docuchat.evaluation.variants import VARIANTS, variant_settings

    assert VARIANTS["sin_contexto"] == {"contextual_meta_enabled": False}
    assert variant_settings(Settings(), "sin_contexto").contextual_meta_enabled is False
    assert variant_settings(Settings(), "base").contextual_meta_enabled is True
