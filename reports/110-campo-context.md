# Informe 110 · Campo `context` en los chunks e `index_text`
Estado: COMPLETADA

## Cambios
- `src/docuchat/models.py`: campo nuevo `context: str = ""` en `Chunk`; función `index_text(chunk)` que devuelve `context + "\n\n" + text` si context no está vacío, o solo `text` en caso contrario.
- `src/docuchat/index/vector_store.py`: `chunk_to_metadata` añade clave `"context"`; `chunk_from_record` lee `"context"` con fallback a `""` (índices antiguos sin la clave). Chroma sigue guardando `documents=[c.text ...]`.
- `src/docuchat/index/fts.py`: `FtsIndex.add` tokeniza `index_text(c)` en lugar de `c.text`.
- `src/docuchat/index/indexer.py`: `self._embedder.embed([index_text(c) for c in chunks])` en lugar de `[c.text for c in chunks]`.
- `src/docuchat/retrieval/searcher.py`: `self._reranker.rerank(query, [index_text(c) for c in pool])` en lugar de `[c.text for c in pool]`.
- `tests/test_index_text.py`: 8 tests nuevos (sin contexto, con contexto, valor por defecto, metadatos ida y vuelta, índice antiguo sin clave, FTS busca en contexto, reranker recibe index_text, embedder recibe index_text).

## Verificación
`uv run pytest -q` → 655 passing (647 anteriores + 8 nuevos). `uv run ruff check .` → sin errores. `uv run ruff format --check .` → todo formateado. `uv run mypy src` → sin errores. `git diff --stat tests/` → solo el test nuevo añadido.

## Decisiones que tomé
Ninguna: la spec definía la interfaz exacta, los valores esperados de los tests y los archivos a modificar. Todo se implementó tal cual.

## Bloqueos y dudas
Sin bloqueos.
