"""Tests para src/docuchat/index/indexer.py — 14 tests obligatorios."""

import os
import shutil
from collections.abc import Iterator, Sequence
from pathlib import Path

import httpx
import pytest
from openai import APIConnectionError

from docuchat.config import Settings
from docuchat.index.indexer import (
    Indexer,
    build_indexer,
    reset_index,
)
from docuchat.index.registry import Registry
from docuchat.index.vector_store import VectorStore

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


# ── FakeEmbedder ───────────────────────────────────────────────────────


class FakeEmbedder:
    def __init__(self, fail_on: str | None = None) -> None:
        self.calls: list[list[str]] = []
        self.fail_on = fail_on

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self.fail_on is not None and any(self.fail_on in t for t in texts):
            raise APIConnectionError(request=httpx.Request("POST", "http://test"))
        return [[float(len(t)), 1.0, 0.5] for t in texts]


# ── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture()
def docs(tmp_path: Path) -> Path:
    """Carpeta de documentos de prueba."""
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.md").write_text("# Alfa\n\nPrimer párrafo de alfa.\n\n## Beta\n\nTexto de beta.\n")
    (d / "b.txt").write_text("Notas de la reunión.\n")
    return d


@pytest.fixture()
def idx(tmp_path: Path) -> Iterator[Indexer]:
    """Indexer con componentes accesibles."""
    _store = VectorStore(tmp_path / "chroma", "chunks", "fake")
    _registry = Registry(tmp_path / "r.sqlite3")
    _embedder = FakeEmbedder()
    _idx = Indexer(_store, _registry, _embedder, 800, 120)
    _idx._store = _store  # noqa: SLF001
    _idx._registry = _registry  # noqa: SLF001
    _idx._embedder = _embedder  # noqa: SLF001
    yield _idx
    _idx.close()


# ── Test 1: Primera pasada ─────────────────────────────────────────────


def test_1_primera_pasada(idx: Indexer, docs: Path):
    stats = idx.index_folder(docs)

    assert stats.added == ["a.md", "b.txt"]
    assert stats.updated == []
    assert stats.unchanged == []
    assert stats.removed == []
    assert stats.errors == []
    assert stats.chunks_added == 3
    assert idx.chunk_count() == 3

    chunks = idx._store.all_chunks()
    ids = [c.chunk_id for c in chunks]
    assert ids == ["a.md#p1#c0", "a.md#p2#c0", "b.txt#p1#c0"]

    reg_a = idx._registry.get("a.md")
    assert reg_a is not None
    assert reg_a.chunk_count == 2


# ── Test 2: Segunda pasada sin cambios ─────────────────────────────────


def test_2_segunda_pasada_sin_cambios(idx: Indexer, docs: Path):
    idx.index_folder(docs)
    llamadas_primera = len(idx._embedder.calls)

    stats = idx.index_folder(docs)

    assert stats.unchanged == ["a.md", "b.txt"]
    assert stats.chunks_added == 0
    assert len(idx._embedder.calls) == llamadas_primera


# ── Test 3: Reescribir b.txt ───────────────────────────────────────────


def test_3_reescribir_b_txt(idx: Indexer, docs: Path):
    idx.index_folder(docs)

    (docs / "b.txt").write_text("Notas nuevas.\n\nSegundo párrafo.\n")

    stats = idx.index_folder(docs)

    assert stats.updated == ["b.txt"]
    assert stats.unchanged == ["a.md"]
    assert idx.chunk_count() == 3

    chunks = idx._store.all_chunks()
    b_chunks = [(c.chunk_id, c.text) for c in chunks if c.source == "b.txt"]
    assert b_chunks == [("b.txt#p1#c0", "Notas nuevas.\n\nSegundo párrafo.")]

    import hashlib

    sha_nueva = hashlib.sha256((docs / "b.txt").read_bytes()).hexdigest()
    assert idx._registry.get("b.txt").sha256 == sha_nueva


# ── Test 4: Borrar a.md ────────────────────────────────────────────────


def test_4_borrar_a_md(idx: Indexer, docs: Path):
    idx.index_folder(docs)
    (docs / "a.md").unlink()

    stats = idx.index_folder(docs)

    assert stats.removed == ["a.md"]
    assert idx._store.sources() == {"b.txt"}
    assert idx._registry.get("a.md") is None
    assert idx.chunk_count() == 1


# ── Test 5: Archivo roto y segunda pasada ─────────────────────────────


def test_5_archivo_roto(idx: Indexer, docs: Path):
    (docs / "roto.pdf").write_bytes(b"no es un pdf")

    stats = idx.index_folder(docs)

    assert stats.errors[0][0] == "roto.pdf"
    assert stats.errors[0][1].startswith("FileDataError")
    assert stats.added == ["a.md", "b.txt"]
    assert idx._registry.get("roto.pdf") is None

    # Segunda pasada: roto.pdf sigue en errores, no se borra nada
    stats2 = idx.index_folder(docs)
    assert stats2.removed == []


# ── Test 6: Archivo vacío ─────────────────────────────────────────────


def test_6_archivo_vacio(idx: Indexer, docs: Path):
    (docs / "vacio.txt").write_text("")

    stats = idx.index_folder(docs)

    assert stats.added == ["a.md", "b.txt", "vacio.txt"]
    assert idx._registry.get("vacio.txt").chunk_count == 0
    # Ninguna llamada del embedder con lista vacía
    assert [] not in idx._embedder.calls


# ── Test 7: Fallo del embedder en adición ─────────────────────────────


def test_7_fallo_embedder_adicion(docs: Path):
    tmp_path = docs.parent

    store = VectorStore(tmp_path / "chroma", "chunks", "fake")
    registry = Registry(tmp_path / "r.sqlite3")
    embedder = FakeEmbedder(fail_on="Notas")
    idx = Indexer(store, registry, embedder, 800, 120)

    with pytest.raises(APIConnectionError):
        idx.index_folder(docs)

    assert idx._registry.get("a.md") is not None
    assert idx._registry.get("b.txt") is None
    assert idx.chunk_count() == 2

    # Nueva pasada con embedder normal
    idx2 = Indexer(
        VectorStore(tmp_path / "chroma", "chunks", "fake"),
        Registry(tmp_path / "r.sqlite3"),
        FakeEmbedder(),
        800,
        120,
    )
    stats = idx2.index_folder(docs)
    assert stats.unchanged == ["a.md"]
    assert stats.added == ["b.txt"]
    idx2.close()


# ── Test 8: Fallo del embedder en actualización conserva lo anterior ───


def test_8_fallo_embedder_actualizacion(docs: Path):
    tmp_path = docs.parent

    store = VectorStore(tmp_path / "chroma", "chunks", "fake")
    registry = Registry(tmp_path / "r.sqlite3")
    embedder = FakeEmbedder()
    idx = Indexer(store, registry, embedder, 800, 120)

    # Primera pasada correcta
    stats1 = idx.index_folder(docs)
    assert stats1.added == ["a.md", "b.txt"]

    # Reescribir b.txt
    (docs / "b.txt").write_text("Notas cambiadas.\n")

    # Segunda pasada con embedder que falla
    embedder_fail = FakeEmbedder(fail_on="Notas")
    idx_fail = Indexer(store, registry, embedder_fail, 800, 120)

    with pytest.raises(APIConnectionError):
        idx_fail.index_folder(docs)

    # Los chunks de b.txt siguen siendo los originales
    chunks = store.all_chunks()
    b_chunks = [(c.chunk_id, c.text) for c in chunks if c.source == "b.txt"]
    assert b_chunks == [("b.txt#p1#c0", "Notas de la reunión.")]
    idx.close()
    idx_fail.close()


# ── Test 9: Progreso ───────────────────────────────────────────────────


def test_9_progreso(idx: Indexer, docs: Path):
    (docs / "roto.pdf").write_bytes(b"no es un pdf")

    calls: list[tuple[str, int, int]] = []
    on_progress = lambda s, i, n: calls.append((s, i, n))  # noqa: E731

    idx.index_folder(docs, on_progress=on_progress)

    assert calls == [("a.md", 1, 3), ("b.txt", 2, 3), ("roto.pdf", 3, 3)]


# ── Test 10: Samples ───────────────────────────────────────────────────


def test_10_samples(idx: Indexer, tmp_path: Path):
    src = tmp_path / "s"
    shutil.copytree(SAMPLES, src)

    stats = idx.index_folder(src)

    assert len(stats.added) == 7
    assert stats.chunks_added == 26
    assert idx.chunk_count() == 26


# ── Test 11: build_indexer ─────────────────────────────────────────────


def test_11_build_indexer(settings: Settings, tmp_path: Path):
    # Usar las mismas rutas que settings (que apuntan a tmp_path)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text(
        "# Alfa\n\nPrimer párrafo de alfa.\n\n## Beta\n\nTexto de beta.\n"
    )
    (docs_dir / "b.txt").write_text("Notas de la reunión.\n")

    idx = build_indexer(settings, embedder=FakeEmbedder())
    stats = idx.index_folder(docs_dir)
    idx.close()

    assert stats.added == ["a.md", "b.txt"]
    assert os.path.exists(settings.chroma_dir)
    assert os.path.exists(settings.registry_path)


# ── Test 12: reset_index ──────────────────────────────────────────────


def test_12_reset_index(settings: Settings, tmp_path: Path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text(
        "# Alfa\n\nPrimer párrafo de alfa.\n\n## Beta\n\nTexto de beta.\n"
    )
    (docs_dir / "b.txt").write_text("Notas de la reunión.\n")

    idx = build_indexer(settings, embedder=FakeEmbedder())
    idx.index_folder(docs_dir)
    idx.close()

    reset_index(settings)

    idx2 = build_indexer(settings, embedder=FakeEmbedder())
    assert idx2.chunk_count() == 0
    reg_check = Registry(settings.registry_path)
    assert reg_check.all() == {}
    reg_check.close()

    stats = idx2.index_folder(docs_dir)
    assert stats.added == ["a.md", "b.txt"]
    idx2.close()


# ── Test 13: reset_index permite cambiar de modelo ─────────────────────


def test_13_reset_cambiar_modelo(settings: Settings, tmp_path: Path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text("Contenido de prueba.\n")

    # Indexar con modelo por defecto
    idx = build_indexer(settings, embedder=FakeEmbedder())
    idx.index_folder(docs_dir)
    idx.close()

    # Intentar con otro modelo → debe lanzar
    from docuchat.index.vector_store import EmbeddingModelMismatchError

    settings2 = Settings(embedding_model="otro")
    with pytest.raises(EmbeddingModelMismatchError):
        build_indexer(settings2, embedder=FakeEmbedder())

    # Reset y reintentar con el nuevo modelo
    reset_index(settings2)
    idx2 = build_indexer(settings2, embedder=FakeEmbedder())
    assert idx2.chunk_count() == 0
    idx2.close()


# ── Test 14: reset_index sobre carpeta vacía ──────────────────────────


def test_14_reset_index_carpeta_vacia(settings: Settings):
    # No crear ningún archivo en data_dir
    reset_index(settings)  # No debe lanzar
