"""Tests del índice léxico FTS5 (spec 100)."""

import os
import threading
from pathlib import Path

import pytest

from docuchat.config import Settings
from docuchat.index.fts import FtsIndex, match_expression, tokenize
from docuchat.models import Chunk, make_chunk_id

TEXTS = [
    "El proveedor ofrece una garantía de dos años.",
    "El depósito de agua tiene 1,8 litros.",
    "El código de error E-17 indica depósito vacío.",
    "Referencia interna SKU-4471-B del filtro.",
]
SOURCES = ["a.md", "b.md", "c.md", "d.md"]


def mk(source: str, page: int, position: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id(source, page, position),
        source=source,
        doc_sha256="a" * 64,
        page=page,
        position=position,
        text=text,
    )


CHUNKS = [mk(s, 1, 0, t) for s, t in zip(SOURCES, TEXTS, strict=True)]


@pytest.fixture()
def fts(tmp_path: Path) -> FtsIndex:
    f = FtsIndex(tmp_path / "sub" / "fts.sqlite3")  # "sub" no existe
    f.add(CHUNKS)
    return f


# 1. test_tokenize
def test_tokenize():
    assert tokenize("Garantía de DOS años, SKU-4471-B!") == [
        "garantia",
        "de",
        "dos",
        "anos",
        "sku",
        "4471",
        "b",
    ]
    assert tokenize("¿Qué pasa?") == ["que", "pasa"]
    assert tokenize("") == []
    assert tokenize("snake_case x²") == ["snake_case", "x2"]


# 2. test_match_expression
def test_match_expression():
    assert match_expression("Garantía E-17") == '"garantia" OR "e" OR "17"'
    assert match_expression('NEAR(" OR *') == '"near" OR "or"'
    assert match_expression("¿?") == ""


# 3. test_garantia
def test_garantia(fts: FtsIndex):
    results = fts.search("Garantía", 5)
    assert len(results) == 1
    assert results[0][0] == "a.md#p1#c0"
    assert results[0][1] == pytest.approx(0.8473, abs=1e-3)


# 4. test_codigos
def test_codigos(fts: FtsIndex):
    results = fts.search("E-17", 5)
    assert results[0] == ("c.md#p1#c0", pytest.approx(1.6122, abs=1e-3))
    sku_results = fts.search("sku 4471", 5)
    assert [r[0] for r in sku_results] == ["d.md#p1#c0"]


# 5. test_orden_y_k
def test_orden_y_k(fts: FtsIndex):
    depo = fts.search("deposito", 5)
    assert [r[0] for r in depo] == ["b.md#p1#c0", "c.md#p1#c0"]
    el_de = fts.search("el de", 5)
    assert [r[0] for r in el_de] == ["a.md#p1#c0", "b.md#p1#c0", "c.md#p1#c0"]
    el_de_k1 = fts.search("el de", 1)
    assert [r[0] for r in el_de_k1] == ["a.md#p1#c0"]


# 6. test_sin_resultados
def test_sin_resultados(fts: FtsIndex):
    assert fts.search("xyz", 5) == []
    assert fts.search("", 5) == []
    assert fts.search("¿?", 5) == []
    assert fts.search("garantia", 0) == []
    # No lanza excepción
    assert fts.search('NEAR(" OR *', 5) == []


# 7. test_snake_case
def test_snake_case(tmp_path: Path):
    f = FtsIndex(tmp_path / "f.sqlite3")
    chunk = mk("e.md", 1, 0, "Usa la variable snake_case aquí.")
    f.add([chunk])
    results = f.search("snake_case", 5)
    assert [r[0] for r in results] == ["e.md#p1#c0"]
    assert f.search("snake", 5) == []


# 8. test_count_sources_delete_clear
def test_count_sources_delete_clear(fts: FtsIndex):
    assert fts.count() == 4
    assert fts.sources() == set(SOURCES)
    fts.delete_source("a.md")
    assert fts.count() == 3
    assert fts.search("garantia", 5) == []
    before = fts.count()
    fts.add([])
    assert fts.count() == before
    fts.clear()
    assert fts.count() == 0
    assert fts.sources() == set()


# 9. test_persistencia
def test_persistencia(tmp_path: Path):
    f = FtsIndex(tmp_path / "fts.sqlite3")
    f.add(CHUNKS)
    f2 = FtsIndex(tmp_path / "fts.sqlite3")
    assert f2.count() == 4
    results = f2.search("garantia", 5)
    assert len(results) >= 1
    assert results[0][0] == "a.md#p1#c0"


# 10. test_otro_hilo
def test_otro_hilo(tmp_path: Path):
    f = FtsIndex(tmp_path / "fts.sqlite3")
    f.add(CHUNKS)
    results: list[tuple[str, float]] = []

    def run() -> None:
        f2 = FtsIndex(tmp_path / "fts.sqlite3")
        results.extend(f2.search("garantia", 5))

    t = threading.Thread(target=run)
    t.start()
    t.join()
    assert len(results) >= 1
    assert results[0][0] == "a.md#p1#c0"


# 11. test_fts_path
def test_fts_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
    s = Settings(data_dir=tmp_path)
    assert s.fts_path == tmp_path / "fts.sqlite3"
