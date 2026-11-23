# Informe 026 · Indexador incremental
Estado: COMPLETADA

## Cambio
- `src/docuchat/index/indexer.py`: nuevo módulo con `IndexStats`, `Indexer`,
  `build_indexer` y `reset_index`
- `tests/index/test_indexer.py`: 14 tests obligatorios

## Implementación
- `Indexer.index_folder`: recorre `scan_folder(root)`, compara SHA-256 con
  registry para detectar unchanged, carga/.chunkea en try/except, embed solo
  si hay chunks (sin llamar al embedder si la lista está vacía), guarda en
  store y registry tras obtener vectores, detecta borrados al final comparando
  registry con sources escaneados (excluyendo los que dieron error).
- `build_indexer`: crea `VectorStore` → `Registry` → `Indexer` con settings.
- `reset_index`: borra colección Chroma (comprobando existencia) y vacía
  registro SQLite con `with Registry(...) as reg: reg.clear()`. Sin `rmtree`.

## Verificación
- `uv run pytest -q tests/index/test_indexer.py` → **14 passed** ✅
- `uv run pytest -q` → **208 passed** ✅
- `uv run ruff check .` → sin errores ✅
- `uv run ruff format --check .` → 72 files ✅
- `uv run mypy src` → success, 18 files ✅
- `grep -n rmtree indexer.py` → sin resultados ✅
- `grep -n except indexer.py` → un único `except Exception` (línea 79) ✅

## Decisiones que tomé
Ninguna. La spec fija la interfaz exacta, el comportamiento paso a paso,
los tests obligatorios con valores esperados y los criterios de aceptación.

## Bloqueos y dudas
Ninguno. Todos los tests pasaron en el primer intento.
