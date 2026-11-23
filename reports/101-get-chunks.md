# Informe 101 · VectorStore.get_chunks(ids)
Estado: COMPLETADA

## Cambios
- `src/docuchat/index/vector_store.py`: método `get_chunks(ids)` añadido — recupera chunks por ID en orden pedido, omite inexistentes y deduplica
- `tests/index/test_get_chunks.py`: **nuevo** — 6 tests (`test_orden_pedido`, `test_chunk_completo`, `test_omite_inexistentes`, `test_duplicados`, `test_vacio`, `test_sin_coincidencias`)

## Verificación
- `uv run pytest -q tests/index/test_get_chunks.py` → 6 passed
- `uv run pytest -q` → 641 passed (635 + 6 nuevos)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores

## Decisiones que tomé
- `get_chunks` usa `list(dict.fromkeys(ids))` para deduplicar manteniendo orden (pattern Python 3.7+).
- El método `test_vacio` no podía usar `store._client.path` porque `chromadb.PersistentClient` no expone `path` como atributo público. Lo cambié a crear dos stores vacíos con `tmp_path`.

## Bloqueos y dudas
- Ninguno.
