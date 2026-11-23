# Informe 093 · Rerank activado por defecto
Estado: COMPLETADA

## Cambios
- `src/docuchat/config.py`: `rerank_enabled: bool = True` (antes `False`), `rerank_candidates: int = Field(default=10, gt=0)` (antes `20`)
- `src/docuchat/evaluation/variants.py`: añadida variante `"sin_rerank": {"rerank_enabled": False}` a `VARIANTS`
- `tests/conftest.py`: fixture `autouse` `_sin_reranker_real` que monkeypatchea `make_reranker` a `None`
- `tests/test_rerank_default.py`: **nuevo** — 4 tests (`test_activado_por_defecto`, `test_desactivable_por_entorno`, `test_tests_sin_reranker_real`, `test_variante_sin_rerank`)
- `tests/test_rerank_config.py`: `test_defaults` actualizado, `test_run_checks_rerank_apagado` usa `Settings(rerank_enabled=False)`
- `tests/test_env_check.py`: `test_run_checks_all_ok` y `test_run_checks_partial_failure` usan `Settings(rerank_enabled=False)`
- `tests/retrieval/test_rerank_searcher.py`: `test_build_searcher_apagado` usa `Settings(data_dir=tmp_path, rerank_enabled=False)`

## Verificación
- `uv run pytest -q tests/test_rerank_default.py` → 4 passed
- `uv run pytest -q` → 639 passed (635 de la spec 100 + 4 nuevos)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores

## Decisiones que tomé
- Ninguna: la spec fijaba todos los valores por defecto, el fixture y los cambios autorizados.

## Bloqueos y dudas
- Ninguno.
