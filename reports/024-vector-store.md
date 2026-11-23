# Informe 024 · Base vectorial con ChromaDB
Estado: COMPLETADA

## Cambio
- Se añadió `chromadb>=1.5,<2` como dependencia en `pyproject.toml`.
- Se creó `src/docuchat/index/vector_store.py` con:
  - `VectorStore` — envoltorio de ChromaDB (persistente, distancia coseno).
  - `EmbeddingModelMismatchError` — excepción al cambiar de modelo de embeddings.
  - `chunk_to_metadata()` / `chunk_from_record()` — convertidores Chunk↔Metadatos Chroma.
  - Métodos: `add()`, `delete_source()`, `count()`, `sources()`, `all_chunks()`, `reset()`.
- Se creó `tests/index/test_vector_store.py` con 11 tests que cubren: store vacío, add, orden de chunks, preservación de heading, delete_source, persistencia, mismatch de modelo, reset, mismatch de longitud, listas vacías y batching.

## Verificación
- `uv run pytest -q tests/index/test_vector_store.py` → 11 passed.
- `uv run pytest -q` → 194 passed (todo el suite).
- `uv run ruff check .` → solo 2 errores preexistentes en `test_embeddings.py` (no tocados).
- `uv run ruff format --check .` → 66 archivos formateados.
- `uv run mypy src` → success (17 archivos, 0 errores).

## Decisiones que tomé
- `all_chunks()` devuelve los chunks en orden de inserción (orden de ChromaDB), no ordenados por `(source, page, position)`, porque el test 3 verifica `retrieved == original` con chunks insertados desordenados.
- Se usa `cast(list[list[float]], batch_embs)` con `# type: ignore[arg-type]` porque los stubs de ChromaDB esperan tipos ndarray muy específicos incompatibles con `list[list[float]]`.
- Los valores de metadata se pasan como `str` (page, position) para evitar errores de tipo de mypy y porque ChromaDB requiere strings en metadatos.

## Bloqueos y dudas
- Ninguno. La spec se implementó íntegramente sin ambigüedades.
