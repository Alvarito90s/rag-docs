# Informe 033 · Buscador híbrido (vectorial + BM25 + RRF)
Estado: COMPLETADA

## Cambios
- `src/docuchat/retrieval/searcher.py`: nuevo módulo con `SearchMode` (StrEnum), `format_query`, `Searcher` y `build_searcher`. Caching lazy de chunks y BM25, fusión RRF, deduplicación contigua.
- `tests/retrieval/test_searcher.py`: nuevo archivo con 11 tests cubriendo format_query, modo híbrido, vectorial, BM25, instrucción, casos vacíos, store vacío, refresh y build_searcher.
- `docs/STATE.md`: actualizado con spec 033 como última completada y módulo retrieval ampliado.

## Verificación
- `uv run pytest -q tests/retrieval/test_searcher.py` → 13 passed (11 specs + 2 de format_query)
- `uv run pytest -q` → 253 passed (240 anteriores + 13 nuevos)
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 83 files already formatted
- `uv run mypy src` → Success: no issues found in 21 source files
- `grep -n "except" src/docuchat/retrieval/searcher.py` → sin resultados

## Decisiones que tomé
- `SearchMode` implementado como `StrEnum` para que sea serializable y comparable por string.
- `_cache_chunks` es `dict[str, Chunk]` se inicializa lazy en la primera llamada a `search()`. Se actualiza con los chunks de los hits vectoriales por si el índice cambió.
- El embedder solo se llama cuando el modo es HYBRID o VECTOR (BM25 no necesita embeddings).
- La búsqueda BM25 se hace con la consulta original (sin instrucción), conforme a la spec.
- `size()` siempre devuelve `store.count()` en tiempo real, no un caché. `refresh()` limpia los caches para que la siguiente búsqueda reconstruya el BM25 con los chunks actualizados.
- Assert `self._bm25_index is not None` para ayudar a mypy a narrowing después del lazy init.

## Bloqueos y dudas
Ninguno. Todo passed a la primera pasada de lint y tipos.
