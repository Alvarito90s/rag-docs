"""Tests del almacén vectorial con ChromaDB."""

from pathlib import Path

import pytest

from docuchat.index.vector_store import (
    EmbeddingModelMismatchError,
    VectorStore,
)
from docuchat.models import Chunk, make_chunk_id


def make_chunk(
    source: str,
    page: int,
    position: int,
    text: str = "",
    heading: str | None = None,
) -> Chunk:
    """Helper para crear chunks de prueba."""
    return Chunk(
        chunk_id=make_chunk_id(source, page, position),
        source=source,
        doc_sha256="a" * 64,
        page=page,
        position=position,
        heading=heading,
        text=text,
    )


def make_embeddings(chunks: list[Chunk]) -> list[list[float]]:
    """Genera embeddings ficticios de dimensión 3."""
    return [[0.1, 0.2, 0.3] for _ in chunks]


# 1. Store nuevo
def test_new_store_is_empty(tmp_path: Path) -> None:
    """1. Store nuevo → count() == 0, sources() == set(), all_chunks() == []"""
    vs = VectorStore(tmp_path, "test", "m1")
    assert vs.count() == 0
    assert vs.sources() == set()
    assert vs.all_chunks() == []


# 2. add de 3 chunks
def test_add_three_chunks(tmp_path: Path) -> None:
    """2. add de 3 chunks (2 de 'a.pdf', 1 de 'b.md')
    count() == 3, sources() == {'a.pdf', 'b.md'}."""
    vs = VectorStore(tmp_path, "test", "m1")
    chunks = [
        make_chunk("a.pdf", 1, 0, "texto uno"),
        make_chunk("a.pdf", 2, 0, "texto dos"),
        make_chunk("b.md", 1, 0, "texto tres"),
    ]
    vs.add(chunks, make_embeddings(chunks))
    assert vs.count() == 3
    assert vs.sources() == {"a.pdf", "b.md"}


# 3. all_chunks ordenado
def test_all_chunks_sorted(tmp_path: Path) -> None:
    """3. all_chunks() devuelve los chunks en orden (source, page, position),
    aunque se añadan desordenados."""
    vs = VectorStore(tmp_path, "test", "m1")
    chunks = [
        make_chunk("b.md", 1, 0, "texto b1"),
        make_chunk("a.pdf", 2, 0, "texto a2"),
        make_chunk("a.pdf", 1, 1, "texto a1 c1"),
        make_chunk("a.pdf", 1, 0, "texto a1 c0"),
    ]
    vs.add(chunks, make_embeddings(chunks))
    assert [(c.source, c.page, c.position) for c in vs.all_chunks()] == [
        ("a.pdf", 1, 0),
        ("a.pdf", 1, 1),
        ("a.pdf", 2, 0),
        ("b.md", 1, 0),
    ]


# 4. heading None y heading con valor
def test_heading_preserved(tmp_path: Path) -> None:
    """4. heading=None vuelve como None; heading='Puertos' vuelve como 'Puertos'."""
    vs = VectorStore(tmp_path, "test", "m1")
    c_none = make_chunk("a.pdf", 1, 0, "texto", heading=None)
    c_heading = make_chunk("a.pdf", 2, 0, "texto", heading="Puertos")
    vs.add([c_none, c_heading], make_embeddings([c_none, c_heading]))
    retrieved = vs.all_chunks()
    assert retrieved[0].heading is None
    assert retrieved[1].heading == "Puertos"


# 5. delete_source
def test_delete_source(tmp_path: Path) -> None:
    """5. delete_source('a.pdf') → count() == 1, sources() == {'b.md'};
    delete_source('no.pdf') no lanza."""
    vs = VectorStore(tmp_path, "test", "m1")
    chunks = [
        make_chunk("a.pdf", 1, 0, "texto a"),
        make_chunk("a.pdf", 2, 0, "texto a2"),
        make_chunk("b.md", 1, 0, "texto b"),
    ]
    vs.add(chunks, make_embeddings(chunks))
    vs.delete_source("a.pdf")
    assert vs.count() == 1
    assert vs.sources() == {"b.md"}
    vs.delete_source("no.pdf")  # no debería lanzar


# 6. Persistencia
def test_persistence_across_instances(tmp_path: Path) -> None:
    """6. Añadir, crear OTRO VectorStore sobre la misma carpeta y modelo → count() igual."""
    vs1 = VectorStore(tmp_path, "test", "m1")
    chunks = [make_chunk("a.pdf", 1, 0, "texto")]
    vs1.add(chunks, make_embeddings(chunks))
    vs2 = VectorStore(tmp_path, "test", "m1")
    assert vs2.count() == 1


# 7. Modelo distinto
def test_model_mismatch(tmp_path: Path) -> None:
    """7. Crear con 'm1', añadir, abrir con 'm2' → EmbeddingModelMismatchError."""
    vs1 = VectorStore(tmp_path, "test", "m1")
    vs1.add(
        [make_chunk("a.pdf", 1, 0, "texto")],
        make_embeddings([make_chunk("a.pdf", 1, 0, "texto")]),
    )
    with pytest.raises(EmbeddingModelMismatchError):
        VectorStore(tmp_path, "test", "m2")


# 8. reset
def test_reset(tmp_path: Path) -> None:
    """8. reset() → count() == 0; después se puede volver a añadir."""
    vs = VectorStore(tmp_path, "test", "m1")
    chunks = [make_chunk("a.pdf", 1, 0, "texto")]
    vs.add(chunks, make_embeddings(chunks))
    vs.reset()
    assert vs.count() == 0
    vs.add(chunks, make_embeddings(chunks))
    assert vs.count() == 1


# 9. add con distinta longitud
def test_add_length_mismatch(tmp_path: Path) -> None:
    """9. add con 2 chunks y 1 embedding → ValueError."""
    vs = VectorStore(tmp_path, "test", "m1")
    chunks = [make_chunk("a.pdf", 1, 0, "x"), make_chunk("a.pdf", 2, 0, "y")]
    with pytest.raises(ValueError):
        vs.add(chunks, [[0.1, 0.2, 0.3]])


# 10. add con listas vacías
def test_add_empty(tmp_path: Path) -> None:
    """10. add([], []) no falla y count() == 0."""
    vs = VectorStore(tmp_path, "test", "m1")
    vs.add([], [])
    assert vs.count() == 0


# 11. Tandas (batching)
def test_add_batches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """11. Con ADD_BATCH patcheado a 2, añadir 5 chunks → count() == 5."""
    monkeypatch.setattr("docuchat.index.vector_store.ADD_BATCH", 2)
    vs = VectorStore(tmp_path, "test", "m1")
    chunks = [make_chunk("a.pdf", i + 1, 0, f"texto {i}") for i in range(5)]
    vs.add(chunks, make_embeddings(chunks))
    assert vs.count() == 5
