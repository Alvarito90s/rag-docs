# Informe 102 · Indexador escribe en FTS junto con Chroma
Estado: COMPLETADA

## Cambios
- `src/docuchat/index/indexer.py`: `FtsIndex` importado, parámetro `fts` añadido a `Indexer.__init__`, `IndexStats` con campo `fts_synced`, función `sync_fts()` para migración, escritura en FTS en ingest y borrado en eliminación
- `src/docuchat/index/indexer.py`: `build_indexer` crea `FtsIndex` y lo pasa al `Indexer`, `reset_index` vacía FTS
- `tests/index/test_indexer_fts.py`: **nuevo** — 9 tests (`test_primera_pasada`, `test_actualizacion`, `test_borrado`, `test_migracion_sin_embeddings`, `test_sobrante_en_fts`, `test_reparacion_chroma`, `test_fallo_embedder_conserva_fts`, `test_sync_fts_directo`, `test_build_indexer_y_reset`)

## Verificación
- `uv run pytest -q tests/index/test_indexer_fts.py` → 9 passed
- `uv run pytest -q` → 650 passed (641 + 9 nuevos)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores

## Decisiones que tomé
- `sync_fts` hace bidireccional: borra restos en FTS que no están en Chroma y rellena lo que falta desde Chroma.
- El fixture `parts` usa `Tuple[VectorStore, Path, FtsIndex]` (ruta del registry, no instancia) para poder crear un `Registry` nuevo en cada llamada a `make_idx`. Esto evita que el segundo `Indexer` intente abrir un registro ya cerrado por el primero.
- `Indexer.__init__` acepta `fts: FtsIndex | None` para que la primera pasada (sin FTS) funcione sin romper compatibilidad.

## Bloqueos y dudas
- Ninguno.
