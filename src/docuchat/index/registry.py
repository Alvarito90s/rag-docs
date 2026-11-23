"""Registro SQLite de documentos indexados por hash SHA-256."""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType


@dataclass(frozen=True)
class RegistryEntry:
    """Fila del registro."""

    source: str
    sha256: str
    chunk_count: int
    indexed_at: str  # ISO 8601 en UTC


class Registry:
    """Tabla `documents` en SQLite (stdlib sqlite3)."""

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                source TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                chunk_count INTEGER NOT NULL,
                indexed_at TEXT NOT NULL
            )
            """
        )

    def get(self, source: str) -> RegistryEntry | None:
        row = self._conn.execute(
            "SELECT source, sha256, chunk_count, indexed_at FROM documents WHERE source = ?",
            (source,),
        ).fetchone()
        if row is None:
            return None
        return RegistryEntry(*row)

    def all(self) -> dict[str, RegistryEntry]:
        rows = self._conn.execute(
            "SELECT source, sha256, chunk_count, indexed_at FROM documents ORDER BY source"
        ).fetchall()
        return {row[0]: RegistryEntry(*row) for row in rows}

    def upsert(
        self,
        source: str,
        sha256: str,
        chunk_count: int,
        indexed_at: datetime | None = None,
    ) -> None:
        if indexed_at is None:
            indexed_at = datetime.now(UTC)
        self._conn.execute(
            """
            INSERT INTO documents (source, sha256, chunk_count, indexed_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source) DO UPDATE SET
                sha256 = excluded.sha256,
                chunk_count = excluded.chunk_count,
                indexed_at = excluded.indexed_at
            """,
            (source, sha256, chunk_count, indexed_at.isoformat(timespec="seconds")),
        )
        self._conn.commit()

    def delete(self, source: str) -> None:
        self._conn.execute("DELETE FROM documents WHERE source = ?", (source,))
        self._conn.commit()

    def clear(self) -> None:
        self._conn.execute("DELETE FROM documents")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Registry":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
