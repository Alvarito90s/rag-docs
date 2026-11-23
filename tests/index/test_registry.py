"""Tests del registro SQLite de documentos indexados."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from docuchat.index.registry import Registry, RegistryEntry


def test_creates_parent_dirs(tmp_path: Path) -> None:
    """1. Registry(tmp_path / "a" / "b" / "reg.sqlite3") crea las carpetas y el archivo."""
    db = tmp_path / "a" / "b" / "reg.sqlite3"
    assert not db.exists()
    Registry(db)
    assert db.is_file()


def test_empty_registry(tmp_path: Path) -> None:
    """2. get("x.pdf") en un registro vacío → None; all() → {}."""
    reg = Registry(tmp_path / "empty.sqlite3")
    assert reg.get("x.pdf") is None
    assert reg.all() == {}


def test_upsert_and_get(tmp_path: Path) -> None:
    """3. upsert con timestamp fijo → get devuelve el RegistryEntry esperado."""
    reg = Registry(tmp_path / "basic.sqlite3")
    ts = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    reg.upsert("x.pdf", "a" * 64, 3, ts)
    entry = reg.get("x.pdf")
    assert entry == RegistryEntry("x.pdf", "a" * 64, 3, "2026-01-02T03:04:05+00:00")


def test_upsert_updates_same_source(tmp_path: Path) -> None:
    """4. Segundo upsert del mismo source → nuevos valores y len(all()) == 1."""
    reg = Registry(tmp_path / "update.sqlite3")
    reg.upsert("doc.pdf", "a" * 64, 3)
    reg.upsert("doc.pdf", "b" * 64, 5)
    entry = reg.get("doc.pdf")
    assert entry.sha256 == "b" * 64
    assert entry.chunk_count == 5
    assert len(reg.all()) == 1


def test_upsert_without_indexed_at(tmp_path: Path) -> None:
    """5. upsert sin indexed_at → la fecha es timezone-aware."""
    reg = Registry(tmp_path / "auto_ts.sqlite3")
    reg.upsert("x.pdf", "a" * 64, 2)
    entry = reg.get("x.pdf")
    assert datetime.fromisoformat(entry.indexed_at).tzinfo is not None


def test_all_sorted_by_source(tmp_path: Path) -> None:
    """6. all() tras insertar "b.md" y "a.pdf" → list(all()) == ["a.pdf", "b.md"]."""
    reg = Registry(tmp_path / "sort.sqlite3")
    reg.upsert("b.md", "b" * 64, 1)
    reg.upsert("a.pdf", "a" * 64, 2)
    assert list(reg.all()) == ["a.pdf", "b.md"]


def test_delete(tmp_path: Path) -> None:
    """7. delete("a.pdf") → None; delete("no_existe") no lanza."""
    reg = Registry(tmp_path / "delete.sqlite3")
    reg.upsert("a.pdf", "a" * 64, 1)
    reg.delete("a.pdf")
    assert reg.get("a.pdf") is None
    reg.delete("no_existe")  # no debería lanzar


def test_persistence_across_instances(tmp_path: Path) -> None:
    """8. Insertar, cerrar, abrir otro Registry → la fila sigue ahí."""
    db = tmp_path / "persist.sqlite3"
    reg1 = Registry(db)
    reg1.upsert("x.pdf", "a" * 64, 3)
    reg1.close()

    reg2 = Registry(db)
    entry = reg2.get("x.pdf")
    assert entry is not None
    assert entry.sha256 == "a" * 64
    assert entry.chunk_count == 3
    reg2.close()


def test_clear(tmp_path: Path) -> None:
    """9. clear() → all() == {}."""
    reg = Registry(tmp_path / "clear.sqlite3")
    reg.upsert("a.pdf", "a" * 64, 1)
    reg.upsert("b.md", "b" * 64, 2)
    reg.clear()
    assert reg.all() == {}


def test_context_manager(tmp_path: Path) -> None:
    """10. Context manager: tras salir del bloque, la conexión está cerrada."""
    db = tmp_path / "ctx.sqlite3"
    with Registry(db) as reg:
        reg.upsert("x", "a" * 64, 1)
    # Después del with, la conexión está cerrada
    with pytest.raises(sqlite3.ProgrammingError):
        reg.get("x")
