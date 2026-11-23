"""Tests para integración FTS en el indexador (spec 102)."""

import shutil
from pathlib import Path

import httpx
import pytest
from openai import APIConnectionError

from docuchat.config import Settings
from docuchat.index.fts import FtsIndex
from docuchat.index.indexer import Indexer, build_indexer, reset_index, sync_fts
from docuchat.index.registry import Registry
from docuchat.index.vector_store import VectorStore
from docuchat.models import Chunk, make_chunk_id


class FakeEmbedder:
    def __init__(self, fail_on: str | None = None) -> None:
        self.calls: list[list[str]] = []
        self.fail_on = fail_on

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self.fail_on is not None and any(self.fail_on in t for t in texts):
            raise APIConnectionError(request=httpx.Request("POST", "http://test"))
        return [[float(len(t)), 1.0, 0.5] for t in texts]


@pytest.fixture()
def parts(tmp_path: Path) -> tuple[VectorStore, Path, FtsIndex]:
    """Store, ruta registry, FTS."""
    store = VectorStore(tmp_path / "chroma", "chunks", "fake")
    reg_path = tmp_path / "r.sqlite3"
    fts = FtsIndex(tmp_path / "fts.sqlite3")
    yield store, reg_path, fts


def make_idx(
    parts: tuple[VectorStore, Path, FtsIndex],
    embedder: FakeEmbedder | None = None,
    *,
    with_fts: bool = True,
) -> Indexer:
    store, reg_path, fts = parts
    registry = Registry(reg_path)
    return Indexer(
        store,
        registry,
        embedder or FakeEmbedder(),
        800,
        120,
        fts=fts if with_fts else None,
    )


def fts_ids(fts: FtsIndex, query: str) -> list[str]:
    return [i for i, _ in fts.search(query, 10)]


@pytest.fixture()
def docs(tmp_path: Path) -> Path:
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.md").write_text("# Alfa\n\nPrimer párrafo de alfa.\n\n## Beta\n\nTexto de beta.\n")
    (d / "b.txt").write_text("Notas de la reunión.\n")
    return d


# 1. test_primera_pasada
def test_primera_pasada(parts: tuple[VectorStore, Path, FtsIndex], docs: Path):
    idx = make_idx(parts)
    stats = idx.index_folder(docs)
    fts = parts[2]
    assert fts.count() == 3
    assert fts.sources() == {"a.md", "b.txt"}
    assert fts_ids(fts, "reunión") == ["b.txt#p1#c0"]
    assert stats.fts_synced == []
    idx.close()


# 2. test_actualizacion
def test_actualizacion(parts: tuple[VectorStore, Path, FtsIndex], docs: Path):
    idx = make_idx(parts)
    idx.index_folder(docs)
    idx.close()
    (docs / "b.txt").write_text("Acta del comité.\n")
    idx2 = make_idx(parts)
    _ = idx2.index_folder(docs)
    idx2.close()
    fts = parts[2]
    assert fts_ids(fts, "reunion") == []
    assert fts_ids(fts, "comite") == ["b.txt#p1#c0"]
    assert fts.count() == 3


# 3. test_borrado
def test_borrado(parts: tuple[VectorStore, Path, FtsIndex], docs: Path):
    idx = make_idx(parts)
    idx.index_folder(docs)
    idx.close()
    (docs / "a.md").unlink()
    idx2 = make_idx(parts)
    idx2.index_folder(docs)
    idx2.close()
    fts = parts[2]
    assert fts.sources() == {"b.txt"}
    assert fts.count() == 1


# 4. test_migracion_sin_embeddings
def test_migracion_sin_embeddings(parts: tuple[VectorStore, Path, FtsIndex]):
    tmp = Path("/tmp/_test_docs_102_mig")
    tmp.mkdir(exist_ok=True)
    (tmp / "a.md").write_text("# Alfa\n\nPrimer párrafo de alfa.\n\n## Beta\n\nTexto de beta.\n")
    (tmp / "b.txt").write_text("Notas de la reunión.\n")
    try:
        # Primera pasada: sin FTS (como v1.0.1)
        idx1 = make_idx(parts, with_fts=False)
        idx1.index_folder(tmp)
        idx1.close()
        fts = parts[2]
        assert fts.count() == 0

        # Segunda pasada: con FTS
        emb = FakeEmbedder()
        idx2 = make_idx(parts, emb)
        stats = idx2.index_folder(tmp)
        idx2.close()
        assert stats.fts_synced == ["a.md", "b.txt"]
        assert stats.unchanged == ["a.md", "b.txt"]
        assert emb.calls == []
        assert fts.count() == 3

        # Tercera pasada: sin cambios
        idx3 = make_idx(parts, FakeEmbedder())
        stats2 = idx3.index_folder(tmp)
        idx3.close()
        assert stats2.fts_synced == []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# 5. test_sobrante_en_fts
def test_sobrante_en_fts(parts: tuple[VectorStore, Path, FtsIndex], docs: Path):
    idx = make_idx(parts)
    idx.index_folder(docs)
    idx.close()
    # Añadir un chunk fantasma a FTS
    phantom = Chunk(
        chunk_id="zzz.md#p1#c0",
        source="zzz.md",
        doc_sha256="a" * 64,
        page=1,
        position=0,
        text="fantasma",
    )
    parts[2].add([phantom])
    # Segunda pasada: FTS limpia el sobrante
    idx2 = make_idx(parts)
    stats = idx2.index_folder(docs)
    idx2.close()
    fts = parts[2]
    assert "zzz.md" not in fts.sources()
    assert fts_ids(fts, "fantasma") == []
    assert stats.fts_synced == []


# 6. test_reparacion_chroma
def test_reparacion_chroma(parts: tuple[VectorStore, Path, FtsIndex], docs: Path):
    idx = make_idx(parts)
    idx.index_folder(docs)
    idx.close()
    # Simular Chroma dañado
    parts[0].delete_source("a.md")
    # FTS conserva a.md
    idx2 = make_idx(parts)
    stats = idx2.index_folder(docs)
    idx2.close()
    fts = parts[2]
    assert stats.updated == ["a.md"]
    assert fts.count() == 3
    assert fts.sources() == {"a.md", "b.txt"}


# 7. test_fallo_embedder_conserva_fts
def test_fallo_embedder_conserva_fts(parts: tuple[VectorStore, Path, FtsIndex], docs: Path):
    idx = make_idx(parts)
    idx.index_folder(docs)
    idx.close()
    (docs / "b.txt").write_text("Notas cambiadas.\n")
    emb_fail = FakeEmbedder(fail_on="Notas")
    idx2 = make_idx(parts, emb_fail)
    with pytest.raises(APIConnectionError):
        idx2.index_folder(docs)
    # FTS conserva versión anterior
    fts = parts[2]
    assert fts_ids(fts, "reunion") == ["b.txt#p1#c0"]
    assert fts_ids(fts, "cambiadas") == []


# 8. test_sync_fts_directo
def test_sync_fts_directo(parts: tuple[VectorStore, Path, FtsIndex]):
    c1 = Chunk(
        chunk_id=make_chunk_id("x.md", 1, 0),
        source="x.md",
        doc_sha256="a" * 64,
        page=1,
        position=0,
        text="x texto",
    )
    c2 = Chunk(
        chunk_id=make_chunk_id("x.md", 1, 1),
        source="x.md",
        doc_sha256="a" * 64,
        page=1,
        position=1,
        text="x texto 2",
    )
    c3 = Chunk(
        chunk_id=make_chunk_id("y.md", 1, 0),
        source="y.md",
        doc_sha256="a" * 64,
        page=1,
        position=0,
        text="y texto",
    )
    parts[0].add([c1, c2, c3], [[1.0, 0.0, 0.5]] * 3)
    fts = parts[2]
    result = sync_fts(parts[0], fts)
    assert result == ["x.md", "y.md"]
    assert fts.count() == 3
    result2 = sync_fts(parts[0], fts)
    assert result2 == []


# 9. test_build_indexer_y_reset
def test_build_indexer_y_reset(
    settings: Settings,
    tmp_path: Path,
):
    docs_dir = tmp_path / "docs2"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text(
        "# Alfa\n\nPrimer párrafo de alfa.\n\n## Beta\n\nTexto de beta.\n"
    )
    (docs_dir / "b.txt").write_text("Notas de la reunión.\n")
    with build_indexer(settings, embedder=FakeEmbedder()) as idx:
        idx.index_folder(docs_dir)
        idx.close()
    assert FtsIndex(settings.fts_path).count() == 3
    reset_index(settings)
    assert FtsIndex(settings.fts_path).count() == 0
