"""Tests para VectorStore.get_chunks (spec 101)."""

from pathlib import Path

import pytest

from docuchat.index.vector_store import VectorStore
from docuchat.models import Chunk, make_chunk_id


def mk(source: str, page: int, position: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id(source, page, position),
        source=source,
        doc_sha256="a" * 64,
        page=page,
        position=position,
        text=text,
        heading="H" if position == 2 else None,
    )


CHUNKS = [mk("a.md", 1, i, f"texto {i}") for i in range(5)]


@pytest.fixture()
def store(tmp_path: Path) -> VectorStore:
    vs = VectorStore(tmp_path / "chroma", "chunks", "fake")
    vs.add(CHUNKS, [[1.0, 0.0, float(i)] for i in range(5)])
    return vs


# 1. test_orden_pedido
def test_orden_pedido(store: VectorStore):
    ids = [c.chunk_id for c in store.get_chunks(["a.md#p1#c3", "a.md#p1#c0", "a.md#p1#c4"])]
    assert ids == ["a.md#p1#c3", "a.md#p1#c0", "a.md#p1#c4"]


# 2. test_chunk_completo
def test_chunk_completo(store: VectorStore):
    result = store.get_chunks(["a.md#p1#c2"])
    assert result == [CHUNKS[2]]


# 3. test_omite_inexistentes
def test_omite_inexistentes(store: VectorStore):
    ids = [c.chunk_id for c in store.get_chunks(["nope", "a.md#p1#c1", "otro"])]
    assert ids == ["a.md#p1#c1"]


# 4. test_duplicados
def test_duplicados(store: VectorStore):
    ids = [c.chunk_id for c in store.get_chunks(["a.md#p1#c1", "a.md#p1#c1", "a.md#p1#c0"])]
    assert ids == ["a.md#p1#c1", "a.md#p1#c0"]


# 5. test_vacio
def test_vacio(tmp_path: Path):
    assert VectorStore(tmp_path, "empty1", "fake").get_chunks([]) == []
    assert VectorStore(tmp_path, "empty2", "fake").get_chunks([]) == []


# 6. test_sin_coincidencias
def test_sin_coincidencias(store: VectorStore):
    assert store.get_chunks(["nope"]) == []
