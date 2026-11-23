# 022 · Registro SQLite de documentos indexados
Fase: 2 · Depende de: 020

## Objetivo
Guardar qué documentos están indexados y con qué hash, para que el reindexado solo procese lo que cambió.

## Archivos
- crear: `src/docuchat/index/registry.py`
- crear: `tests/index/test_registry.py`

## Interfaz
```python
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
    indexed_at: str  # ISO 8601 en UTC, p. ej. "2026-01-02T03:04:05+00:00"


class Registry:
    """Tabla `documents` en SQLite (stdlib sqlite3)."""

    def __init__(self, db_path: Path) -> None: ...
    def get(self, source: str) -> RegistryEntry | None: ...
    def all(self) -> dict[str, RegistryEntry]: ...
    def upsert(
        self, source: str, sha256: str, chunk_count: int, indexed_at: datetime | None = None
    ) -> None: ...
    def delete(self, source: str) -> None: ...
    def clear(self) -> None: ...
    def close(self) -> None: ...
    def __enter__(self) -> "Registry": ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
```

## Comportamiento
1. `__init__`: `db_path.parent.mkdir(parents=True, exist_ok=True)`; `self._conn = sqlite3.connect(db_path)`; crea la tabla si no existe:
```sql
CREATE TABLE IF NOT EXISTS documents (
    source TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    chunk_count INTEGER NOT NULL,
    indexed_at TEXT NOT NULL
)
```
2. `upsert`: `indexed_at` por defecto `datetime.now(UTC)`; se guarda con `.isoformat(timespec="seconds")`.
```sql
INSERT INTO documents (source, sha256, chunk_count, indexed_at) VALUES (?, ?, ?, ?)
ON CONFLICT(source) DO UPDATE SET
    sha256 = excluded.sha256, chunk_count = excluded.chunk_count, indexed_at = excluded.indexed_at
```
3. Cada escritura (`upsert`, `delete`, `clear`) hace `self._conn.commit()`.
4. `all()` devuelve un dict `source → RegistryEntry` ordenado por `source` (`ORDER BY source`).
5. `delete` de un `source` inexistente no falla. `clear` borra todas las filas.
6. Usa SIEMPRE parámetros `?`; nunca formatees SQL con f-strings.
7. `__exit__` llama a `close()`.

## Tests obligatorios
`tests/index/test_registry.py`, todo en `tmp_path`. NO cambies los valores esperados.
1. `Registry(tmp_path / "a" / "b" / "reg.sqlite3")` crea las carpetas y el archivo.
2. `get("x.pdf")` en un registro vacío → `None`; `all()` → `{}`.
3. `upsert("x.pdf", "a" * 64, 3, datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC))` → `get("x.pdf") == RegistryEntry("x.pdf", "a" * 64, 3, "2026-01-02T03:04:05+00:00")`.
4. Segundo `upsert` del mismo `source` con `"b" * 64` y 5 chunks → `get` devuelve los nuevos valores y `len(all()) == 1`.
5. `upsert` sin `indexed_at` → `datetime.fromisoformat(entry.indexed_at).tzinfo is not None`.
6. `all()` tras insertar `"b.md"` y `"a.pdf"` → `list(all()) == ["a.pdf", "b.md"]`.
7. `delete("a.pdf")` → `get("a.pdf") is None`; `delete("no_existe")` no lanza.
8. Persistencia: insertar, `close()`, abrir otro `Registry` sobre el mismo archivo → la fila sigue ahí.
9. `clear()` → `all() == {}`.
10. Context manager: `with Registry(p) as reg: reg.upsert(...)`; después, `reg.get("x")` lanza `sqlite3.ProgrammingError` (conexión cerrada).

## Referencia de librerías
```python
import sqlite3

conn = sqlite3.connect(path)  # Path o str
conn.execute("CREATE TABLE IF NOT EXISTS ...")
conn.execute("SELECT ... WHERE source = ?", (source,)).fetchone()  # tupla o None
conn.execute("SELECT ...").fetchall()  # lista de tuplas
conn.commit()
conn.close()
# Usar una conexión cerrada -> sqlite3.ProgrammingError
```

## Aceptación
- [ ] `uv run pytest -q tests/index/test_registry.py` → 10 passed
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Guardar chunks o embeddings aquí (van en Chroma), migraciones de esquema.
