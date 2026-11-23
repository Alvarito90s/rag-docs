# Informe 084 · Variantes de evaluación
Estado: COMPLETADA

## Cambios
- `src/docuchat/evaluation/variants.py`: nuevo módulo con `VARIANTS`, `parse_variants()` y `variant_settings()`
- `src/docuchat/evaluation/runner.py`: añadido campo `variant: str = "base"` a `RetrievalReport` y `GenerationReport`
- `src/docuchat/evaluation/run.py`: dataclass `VariantResult`, función `run_variant()`, envoltura `run_evaluation()` compatible, `main` con nueva opción `--variants`
- `src/docuchat/evaluation/report.py`: `render_retrieval_table` con columna Variante, `render_category_table` con etiquetas variant/mode, `render_results` con parámetros `generations` y `questions_file`
- `tests/evaluation/test_variants.py`: 16 tests (14 funciones, 2 parametrizados con 3 y 2 casos)

## Verificación
- `uv run pytest -q tests/evaluation/test_variants.py` → 17 passed
- `uv run pytest -q` → 539 passed
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → 181 files already formatted
- `uv run mypy src` → success, no issues found
- `uv run python eval/run_eval.py --help` → muestra `--variants`
- `wc -l src/docuchat/evaluation/*.py` → todos por debajo de 300 (máx 244 run.py)
- `git diff --stat tests/ eval/` → solo `test_variants.py` nuevo

## Decisiones que tomé
- Usé `import dataclasses` con `dataclasses.replace()` en lugar de `from dataclasses import replace` para mantener consistencia con el resto del proyecto.
- En `variants.py`, accedo a `Settings.model_fields` (desde la clase, no la instancia) para evitar la advertencia de Pydantic v2.11 sobre acceso a `model_fields` en instancias.

## Bloqueos y dudas
Ninguno. La implementación fue directa y todos los tests pasaron a la primera (tras 2 correcciones menores: test parametrizado y un import no usado).
