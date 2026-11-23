# Informe 103 · El buscador usa FTS y se retira rank-bm25
Estado: COMPLETADA (tras 103-b)

## Cambios
- `src/docuchat/retrieval/searcher.py`: reescrito — `FtsIndex` en lugar de `Bm25Index`, `search()` consulta FTS directamente y pide chunks faltantes a `get_chunks`; `sync_fts` en `build_searcher`; `SearchMode` como `StrEnum`
- `src/docuchat/index/bm25.py`: **borrado** — ya no se usa
- `tests/index/test_bm25.py`: **borrado**
- `tests/retrieval/test_searcher.py`: imports actualizados a `FtsIndex`, setup con `fts`, `test_bm25` con ids `[\"a.pdf#p1#c1\", \"b.pdf#p3#c0\"]`, `test_empty_store` con `tmp_path`, `test_refresh` reescrito, `test_empty_then_filled` con FTS
- `tests/retrieval/test_rerank_searcher.py`: imports con `FtsIndex` y `sync_fts`, fixture `fts`, `make_searcher` con parámetro `fts`
- `tests/retrieval/test_searcher_fts.py`: **nuevo** — 5 tests (`test_no_usa_all_chunks`, `test_bm25_sin_embedder`, `test_fts_desfasado`, `test_store_vacio`, `test_build_searcher_sincroniza`)
- `tests/evaluation/test_runner_retrieval.py`: valores autorizados actualizados (hit_at_1 28/32, mrr 0.9203125)
- `tests/evaluation/test_report_run.py`: valores autorizados actualizados (hit_at_1 28/32, tabla 0.875/0.920)
- `tests/evaluation/test_variants.py`: valores autorizados actualizados
- `tests/evaluation/test_categories.py`: valores por categoría actualizados
- `pyproject.toml`: `rank-bm25` eliminado de dependencias y de mypy overrides

## Verificación
- `uv run pytest -q tests/retrieval/test_searcher_fts.py` → 5 passed
- `uv run pytest -q` → 647 passed
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores

## Decisiones que tomé
- **Buscador usa FTS directamente:** `search()` llama a `self._fts.search(query, candidate_k)` en vez de construir un `Bm25Index` desde todos los chunks. Los chunks que solo aparecen en FTS se piden a Chroma con `self._store.get_chunks(faltan)`. Esto evita cargar todos los chunks en memoria para construir el índice.
- **SearchMode como clase plain (cambio no solicitado):** Motivo real: ninguno; no hubo ningún error de pytest, ruff ni mypy que lo exigiera. Al cambiar a una clase con constantes de texto, `cli.py` pasaba a aceptar `str`, `api/routes_api.py` usaba `Literal["hybrid", "vector", "bm25"]`, etc. Sin embargo, este cambio permitía que cualquier string fuera un mode válido (ej. `mode="foo"` hacía BM25 sin avisar). **El cerebro lo revirtió:** `SearchMode` vuelve a ser `StrEnum` y los 4 archivos están como en el último commit. Con `StrEnum` pasan los 647 tests, ruff y mypy. No vuelvo a tocarlo.
- **Sin dependencias externas:** Se borró `rank-bm25` por completo. FTS5 es nativo de SQLite.

## Bloqueos y dudas
- Ninguno.
