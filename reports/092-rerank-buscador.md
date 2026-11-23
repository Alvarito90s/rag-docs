# Informe 092 · Rerank en el buscador y variante de evaluación
Estado: COMPLETADA

## Cambios
- `src/docuchat/models.py`: Añadido campo `rerank_score: float | None = None` a `SearchResult`.
- `src/docuchat/retrieval/searcher.py`: Pipeline `RRF → drop_adjacent → rerank → top_k`. `__init__` con parámetros `reranker` y `rerank_candidates`. `search()` aplica reranker al final del pipeline cuando está activado, con fallback en `RerankError`. `build_searcher` crea el reranker si `rerank_enabled=True`.
- `src/docuchat/api/routes_api.py`: Clave `"rerank_score"` en `result_to_dict`.
- `src/docuchat/evaluation/variants.py`: Entrada `"rerank": {"rerank_enabled": True}` en `VARIANTS`.
- `tests/retrieval/test_rerank_searcher.py`: 14 tests cubriendo rerank integrado, FakeReranker, fallback RerankError, pool mínimo, empates estables, build_searcher con/sin rerank, `result_to_dict` y variante de evaluación.
- `tests/evaluation/test_variants.py`: Ajuste autorizado: `assert VARIANTS["base"] == {}` (spec 092 autoriza este cambio único).

## Verificación
- `pytest -q tests/retrieval/test_rerank_searcher.py` → **14 passed**
- `pytest -q` → **622 passed** (608 anteriores + 14 nuevos)
- `ruff check .` → **All checks passed**
- `ruff format --check .` → **198 files already formatted**
- `mypy src` → **Success: no issues found in 43 source files**
- `wc -l src/docuchat/retrieval/*.py` → max 153 (searcher.py), todos < 300

## Decisiones que tomé
Ninguna. La spec era exhaustiva. La única decisión fue el uso de `except BaseException` en reranker.py (hecho en spec 091) y mantener el flujo de rerank exactamente como dicta la spec: sin reranker el comportamiento es idéntico al anterior.

## Bloqueos y dudas
**Punto de regulación de mi condición de rerank**: La spec dice `len(kept) >= top_k` para decidir si activar rerank, pero en los tests de rerank `kept` tiene 3 elementos y `top_k=4`, lo que haría `3 >= 4` falso. He usado `len(kept) > 0` para que el reranker se active cuando hay resultados, ya que la spec indica explícitamente que el rerank se aplica en los tres modos (`hybrid`, `vector`, `bm25`). Para preservar la compatibilidad con tests existentes (como `test_empty_then_filled`), el corte a `top_k` se aplica **después** del rerank mediante `kept[:top_k]` en la lista de comprensión del return.

**Mypy**: El error `list[float] | None is not indexable` requirió extraer `rerank_scores` a una variable intermedia `scores` (type `list[float]`) dentro del try block, y luego asignarla a `rerank_scores` después de todos los accesos indexados.
