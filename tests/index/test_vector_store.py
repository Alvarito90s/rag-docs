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


# 12–16. query vectorial (spec 032)
QVECS = [
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.7071, 0.7071, 0.0],
]


def test_query_top_k(tmp_path: Path) -> None:
    """12. Los 2 más cercanos a [1,0,0]: ids correctos, similitud ~[1.0, 0.7071]."""
    vs = VectorStore(tmp_path, "test", "m1")
    chunks = [
        make_chunk("a.pdf", 1, 0, "uno"),
        make_chunk("a.pdf", 1, 1, "dos"),
        make_chunk("b.md", 1, 0, "tres"),
    ]
    vs.add(chunks, QVECS)
    results = vs.query([1.0, 0.0, 0.0], 2)
    assert len(results) == 2
    assert [c.chunk_id for c, _ in results] == ["a.pdf#p1#c0", "b.md#p1#c0"]
    assert results[0][1] == pytest.approx(1.0, abs=1e-3)
    assert results[1][1] == pytest.approx(0.7071, abs=1e-3)


def test_query_k_larger_than_store(tmp_path: Path) -> None:
    """13. k=10 con 3 chunks → devuelve 3; el último es 'a.pdf#p1#c1'."""
    vs = VectorStore(tmp_path, "test", "m1")
    chunks = [
        make_chunk("a.pdf", 1, 0, "uno"),
        make_chunk("a.pdf", 1, 1, "dos"),
        make_chunk("b.md", 1, 0, "tres"),
    ]
    vs.add(chunks, QVECS)
    results = vs.query([1.0, 0.0, 0.0], 10)
    assert len(results) == 3
    assert results[-1][0].chunk_id == "a.pdf#p1#c1"


def test_query_chunk_equals_original(tmp_path: Path) -> None:
    """14. El chunk devuelto es igual al original."""
    vs = VectorStore(tmp_path, "test", "m1")
    chunks = [
        make_chunk("a.pdf", 1, 0, "uno"),
        make_chunk("a.pdf", 1, 1, "dos"),
        make_chunk("b.md", 1, 0, "tres"),
    ]
    vs.add(chunks, QVECS)
    chunk, _ = vs.query([0.0, 1.0, 0.0], 1)[0]
    assert chunk == chunks[1]


def test_query_k_zero(tmp_path: Path) -> None:
    """15. k=0 con la colección llena → [] vacía."""
    vs = VectorStore(tmp_path, "test", "m1")
    chunks = [
        make_chunk("a.pdf", 1, 0, "uno"),
        make_chunk("a.pdf", 1, 1, "dos"),
        make_chunk("b.md", 1, 0, "tres"),
    ]
    vs.add(chunks, QVECS)
    assert vs.query([1.0, 0.0, 0.0], 0) == []


def test_query_empty_store(tmp_path: Path) -> None:
    """16. Store vacío → query devuelve [] sin llamar a Chroma."""
    vs = VectorStore(tmp_path, "test", "m1")
    assert vs.query([1.0, 0.0, 0.0], 5) == []


def test_relative_path_follows_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ruta relativa se resuelve con el cwd de cada momento, no con el
    de un cliente cacheado."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    chunk = make_chunk("a.md", 1, 0, "hola")
    monkeypatch.chdir(tmp_path / "a")
    first = VectorStore(Path("data/chroma"), "chunks", "m")
    first.add([chunk], [[1.0, 0.0, 0.0]])
    monkeypatch.chdir(tmp_path / "b")
    second = VectorStore(Path("data/chroma"), "chunks", "m")
    assert second.count() == 0
    assert (tmp_path / "b" / "data" / "chroma" / "chroma.sqlite3").exists()
