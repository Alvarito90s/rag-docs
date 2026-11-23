# 026-b · Indexador: reparar chunks que faltan en Chroma
Fase: 5 · Depende de: 026

## Objetivo
Que el indexador incremental repare la base vectorial cuando el registro dice que un documento está indexado pero sus chunks no están en Chroma. Ahora lo da por "sin cambios" para siempre.

Caso real (comprobado en `data/`): el registro tenía los 7 documentos y la colección de Chroma tenía 0 chunks. "Actualizar índice" respondía `0 añadidos, 7 sin cambios` y la app decía que el índice estaba vacío. Solo `--reset` lo arreglaba.

## Archivos
- modificar: `src/docuchat/index/indexer.py` (solo `Indexer.index_folder`)
- modificar: `tests/index/test_indexer.py` (solo AÑADIR tests)

## Comportamiento
1. Al principio de `index_folder`, una sola vez: `present = self._store.sources()`.
2. Un archivo cuenta como `unchanged` SOLO si `entry is not None`, `entry.sha256 == sha` y además `entry.chunk_count == 0 or source in present`.
3. Si el hash coincide pero faltan sus chunks, se reindexa por el camino normal (cargar, chunkear, embeddings, `delete_source`, `add`, `upsert`) y cuenta como `updated` (el registro sí tenía entrada).
4. Nada más cambia: orden, progreso, errores y borrado de los eliminados siguen igual.

## Tests obligatorios
Añadir a `tests/index/test_indexer.py` (fixtures `docs` e `indexer` existentes). NO cambies los tests existentes.
15. `test_repairs_missing_source`: primera pasada; después `store.delete_source("a.md")` (directamente sobre el store, el registro sigue igual) → segunda pasada: `updated == ["a.md"]`, `unchanged == ["b.txt"]`, `chunks_added == 2`, `chunk_count() == 3`.
16. `test_repairs_empty_store`: con `vacio.txt` (`""`) además de `a.md` y `b.txt`, primera pasada; `store.reset()` → segunda pasada: `updated == ["a.md", "b.txt"]`, `unchanged == ["vacio.txt"]` (0 chunks: no hay nada que reparar), `chunk_count() == 3`.

## Aceptación
- [ ] `uv run pytest -q tests/index/test_indexer.py` → 16 passed
- [ ] `uv run pytest -q` pasa entero (386)
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -c "self._store.sources()" src/docuchat/index/indexer.py` → `1`

## Fuera de alcance
No toques `vector_store.py`, `registry.py`, la CLI ni la API.
