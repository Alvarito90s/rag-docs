# Informe 020 · Config de indexado y modelo Chunk
Estado: COMPLETADA

## Cambio
Se añadieron los ajustes de indexado y el modelo `Chunk` a la base del proyecto:

- **`src/docuchat/config.py`**: 3 nuevos campos (`embedding_batch_size`, `request_max_retries`, `chroma_collection`) + 2 propiedades derivadas (`chroma_dir`, `registry_path`).
- **`.env.example`**: 3 líneas de ejemplo para las nuevas variables de entorno.
- **`src/docuchat/models.py`**: función `make_chunk_id()` y clase `Chunk` ( BaseModel inmutable con validaciones de patrón SHA-256, página ≥ 1, posición ≥ 0, texto no vacío).
- **`tests/test_config.py`**: 4 tests nuevos (`test_index_defaults`, `test_index_env_override`, `test_derived_paths`, `test_invalid_index_values`).
- **`tests/test_models.py`**: 3 tests nuevos (`test_make_chunk_id`, `test_chunk_valid`, `test_chunk_invalid`).

## Verificación
- `uv run pytest -q tests/test_config.py tests/test_models.py` → **31 passed** (16 + 15)
- `uv run pytest -q` → **135 passed** (125 + 10 nuevos)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → 50 files already formatted
- `uv run mypy src` → success, no issues in 11 files

## Decisiones que tomé
- Colocé `make_chunk_id` y `Chunk` antes de `DocType` en `models.py` para que queden al inicio del archivo, ya que son el foco de esta spec (unidades de indexado/recuperación).
- El import de Pydantic se unificó en una sola línea al inicio del archivo.
- En el test `test_chunk_invalid`, construí un dict base y lo actualicé con kwargs en lugar de pasar argumentos fijos + `**kwargs` para evitar colisión de argumentos duplicados en Python.

## Bloqueos y dudas
Ninguno. Todo pasó a la primera pasada tras corregir el test `test_chunk_invalid`.
