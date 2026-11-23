# Informe 033-b · Searcher: no cachear un índice vacío
Estado: COMPLETADA

## Cambios
- `src/docuchat/retrieval/searcher.py`: Sustituir `_cache_chunks` + `_bm25_index` por `self._cache: tuple[dict[str, Chunk], Bm25Index] | None`. `refresh()` → `self._cache = None`. En `search()`, si store vacío → `return []` SIN guardar caché (permanece `None`). Sin `assert` en el código.
- `tests/retrieval/test_searcher.py`: Añadir `test_empty_then_filled` → verifica que una búsqueda con índice vacío no cachea, y que la siguiente búsqueda (sin refresh) sí recupera datos.

## Verificación
- `uv run pytest -q tests/retrieval/test_searcher.py` → **14 passed**
- `uv run pytest -q` → **264 passed**, 0 failures
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → 85 files already formatted
- `uv run mypy src` → Success: no issues found in 21 source files
- `grep -n "assert\|_bm25_index\|_cache_chunks" src/docuchat/retrieval/searcher.py` → sin resultados (exit 1)

## Decisiones que tomé
- El test usa `tmp_path` en lugar de `Path("data/...")` porque ChromaDB persiste en disco; usar rutas fijas hacía que el store pareciera vacío pero en realidad contenía datos de ejecuciones previas.

## Bloqueos y dudas
- Ninguno. Todo pasó a la primera tras corregir la referencia a `self._bm25_index` → `bm25` en la línea de `bm25.search()` (era un error mío al reemplazar).
