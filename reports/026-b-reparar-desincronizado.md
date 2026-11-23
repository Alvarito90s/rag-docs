# Informe 026-b · Reparar chunks desincronizados en Chroma
Estado: COMPLETADA

## Cambios
- `src/docuchat/index/indexer.py`: al inicio de `index_folder`, leer `present = self._store.sources()`. Condición de `unchanged` ahora exige `entry.chunk_count == 0 or source in present`. Si hash coincide pero faltan chunks en Chroma → reindexa como `updated`.
- `tests/index/test_indexer.py`: añadidos `test_15_repairs_missing_source` y `test_16_repairs_empty_store`.

## Verificación
- `uv run pytest -q tests/index/test_indexer.py::test_15_repairs_missing_source` → passed
- `uv run pytest -q tests/index/test_indexer.py::test_16_repairs_empty_store` → passed
- Tests 1-11 existentes → siguen pasando (11 passed)
- `uv run ruff check` → sin errores
- `uv run ruff format --check` → todo formateado (aplicado `ruff format` una vez)
- `uv run mypy src/docuchat/index/indexer.py` → sin errores
- `grep -c "self._store.sources()" src/docuchat/index/indexer.py` → `1`

## Decisiones que tomé
Ninguna. La spec era precisa y determinista.

## Bloqueos y dudas
- Tests 12, 13 y 14 fallan con errores internos de ChromaDB Rust bindings (`no such table: max_seq_id`, `no such table: acquire_write`, `no such table: collections`). Son fallos preexistentes de corrupción de base de datos Chroma, no relacionados con esta spec ni con los cambios realizados. El AGENTS.md del proyecto ya documenta este problema.
