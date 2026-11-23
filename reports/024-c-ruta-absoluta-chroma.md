# Informe 024-c · Ruta absoluta en ChromaDB PersistentClient
Estado: COMPLETADA

## Cambios
- `src/docuchat/index/vector_store.py`: `PersistentClient(path=str(path.resolve()), ...)` para evitar caché intermitente.
- `src/docuchat/index/indexer.py`: `PersistentClient(path=str(settings.chroma_dir.resolve()), ...)` en `reset_index()`.
- `tests/index/test_vector_store.py`: añadido test `test_relative_path_follows_cwd` que verifica que cambiar el cwd entre instancias no reutiliza un cliente cacheado.

## Verificación
- `uv run pytest -q tests/index/test_vector_store.py` → **17 passed**
- `uv run pytest -q` → **387 passed, 0 failures**
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → 125 files already formatted
- `uv run mypy src` → Success: no issues found in 31 source files
- `grep -n "PersistentClient" -A1 src/docuchat/index/*.py` → ambas llamadas usan `.resolve()`

## Decisiones que tomé
- Ninguna. La spec era explícita en cada cambio.

## Bloqueos y dudas
- No hubo bloqueos. La única corrección fue un E501 (línea muy larga) en el docstring del nuevo test, que se resolvió dividiéndolo en dos líneas.
