# Informe 005-c · Samples: comprobar que cada dato está en una sola página
Estado: COMPLETADA

## Cambios
- `tests/test_samples.py`: `test_pdf_facts` reescrito para verificar unicidad — comprueba que cada dato aparece en exactamente una página del PDF, no en varias
- Cuerpo del test: lista comprehensiva `pages_with_fact` sobre todas las páginas, assert de igualdad con `[page]`

## Verificación
- `uv run pytest -q tests/test_samples.py` → 19 passed ✅
- `uv run ruff check . && uv run ruff format --check .` → all checks passed, 33 files ✅
- `uv run pytest -q` → 54 passed, 5 warnings ✅

## Decisiones que tomé
Ninguna. La spec fija el código exacto del test.

## Bloqueos y dudas
Ninguno. Los datos están correctamente ubicados y no aparecen duplicados en otras páginas.
