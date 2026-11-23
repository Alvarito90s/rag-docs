"""Índice léxico de chunks en SQLite FTS5 (puntuación BM25)."""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from collections.abc import Iterator, Sequence
from contextlib import closing, contextmanager
from pathlib import Path
from typing import cast

from docuchat.models import Chunk, index_text


def tokenize(text: str) -> list[str]:
    """Minúsculas, sin tildes, palabras alfanuméricas (\\w+).

    'Garantía SKU-4471' -> ['garantia', 'sku', '4471'].
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    return re.findall(r"\w+", text)


def match_expression(query: str) -> str:
    """Consulta FTS5: los tokens de query entre comillas dobles, unidos por ' OR '.

    'Garantía E-17' -> '"garantia" OR "e" OR "17"'. Sin tokens -> ''.
    """
    tokens = tokenize(query)
    if not tokens:
        return ""
    return " OR ".join(f'"{t}"' for t in tokens)


class FtsIndex:
    """Índice léxico de chunks en SQLite FTS5 (puntuación BM25)."""

    TABLE = "chunks"

    def __init__(self, path: Path) -> None:
        """Crea la carpeta padre y la tabla si no existen."""
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with self._connect() as conn:
            conn.execute(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS {self.TABLE} USING fts5("
                f"chunk_id UNINDEXED, source UNINDEXED, text,"
                f" tokenize = \"unicode61 tokenchars '_'\""
                f")"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path)) as conn, conn:
            yield conn

    def add(self, chunks: Sequence[Chunk]) -> None:
        """Agrega chunks al índice."""
        if not chunks:
            return
        token_texts = [(c.chunk_id, c.source, " ".join(tokenize(index_text(c)))) for c in chunks]
        with self._connect() as conn:
            conn.executemany(
                f"INSERT INTO {self.TABLE} (chunk_id, source, text) VALUES (?, ?, ?)",
                token_texts,
            )

    def delete_source(self, source: str) -> None:
        """Elimina todos los chunks de una fuente."""
        with self._connect() as conn:
            conn.execute(f"DELETE FROM {self.TABLE} WHERE source = ?", (source,))

    def search(self, query: str, k: int) -> list[tuple[str, float]]:
        """Hasta k (chunk_id, score), de mayor a menor score."""
        expr = match_expression(query)
        if k <= 0 or not expr:
            return []
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT chunk_id, bm25({self.TABLE}) FROM {self.TABLE} "
                f"WHERE {self.TABLE} MATCH ? ORDER BY bm25({self.TABLE}), rowid "
                f"LIMIT ?",
                (expr, k),
            )
            return [(row[0], -float(row[1])) for row in cursor.fetchall()]

    def count(self) -> int:
        """Número de chunks en el índice."""
        with self._connect() as conn:
            row = conn.execute(f"SELECT count(*) FROM {self.TABLE}").fetchone()
            return cast(int, row[0])

    def sources(self) -> set[str]:
        """Fuentes presentes en el índice."""
        with self._connect() as conn:
            rows = conn.execute(f"SELECT DISTINCT source FROM {self.TABLE}").fetchall()
            return {row[0] for row in rows}

    def clear(self) -> None:
        """Borra todo el índice."""
        with self._connect() as conn:
            conn.execute(f"DELETE FROM {self.TABLE}")
