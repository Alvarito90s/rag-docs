# Informe 100 · FTSIndex en SQLite FTS5
Estado: COMPLETADA

## Cambios
- `src/docuchat/index/fts.py`: **nuevo** — `tokenize()`, `match_expression()`, `FtsIndex` (6 métodos + contexto) con SQLite FTS5
- `src/docuchat/index/bm25.py`: `tokenize` importado de `fts.py`, eliminadas importaciones `re` y `unicodedata`
- `src/docuchat/config.py`: propiedad `fts_path` añadida (`data_dir / "fts.sqlite3"`)
- `tests/index/test_fts.py`: **nuevo** — 11 tests para `tokenize`, `match_expression` y `FtsIndex`

## Verificación
- `uv run pytest -q tests/index/test_fts.py` → 11 passed
- `uv run pytest -q` → 635 passed (624 previos + 11 nuevos)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores

## Decisiones que tomé
- La spec no detallaba la estructura interna de `FtsIndex` más allá de los métodos públicos. Implementé los métodos públicos de la spec: `add`, `delete_source`, `search` (FTS5 + BM25 score), `count`, `sources` y `clear`.
- `search()` usa la sintaxis FTS5 `tokenize = "unicode61 tokenchars '_'"` para que el guion bajo forme parte del token (`snake_case` es un solo token), igual que `\w` en `tokenize`.
- Usé `cast(int, row[0])` en `count()` para evitar el error mypy "Returning Any from function declared to return int".
- Corregí `from typing import Iterator` a reutilizar `Iterator` ya importado de `collections.abc`.

## Bloqueos y dudas
- Ninguno.
