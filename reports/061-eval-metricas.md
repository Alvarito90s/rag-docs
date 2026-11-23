# Informe 061 · Métricas de evaluación
Estado: COMPLETADA

## Cambios
- `src/docuchat/evaluation/metrics.py`: 7 funciones puras — normalize, keywords_hit, first_hit_rank, hit_at, mean_reciprocal_rank, citation_counts, ratio
- `tests/evaluation/test_metrics.py`: 13 tests (1 normalize + 7 keywords_hit parametrizados + 1 first_hit_rank con 3 assertions + 1 hit_at con 4 assertions + 1 mean_reciprocal_rank con 2 assertions + 1 citation_counts con 2 assertions + 1 ratio con 2 assertions)

## Verificación
- `uv run pytest -q tests/evaluation/test_metrics.py` → 13 passed
- `uv run pytest -q` completo → 411 passed, 0 failures
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → 133 files already formatted
- `uv run mypy src` → Success: no issues found in 34 source files

## Decisiones que tomé
- `hit_at` cuenta sobre el tamaño total de la lista (incluyendo None) según la spec: "Fracción de puestos que no son None y son <= k". Usé `len(ranks)` como denominador, con `hits` como numerador.

## Bloqueos y dudas
- Ninguno. Todo pasó a la primera tras corrección menor de `ruff format` y `ruff check --fix`.
