# Informe 071 · CI: job Docker
Estado: COMPLETADA

## Cambios
- `.github/workflows/ci.yml`: añadido job `docker` al final del workflow (después de `check`, con `needs: check`). Construye la imagen, la arranca y comprueba `/api/health` en 30 intentos con polling.
- `tests/test_ci_workflow.py`: 5 tests que verifican: (1) job `check` completo, (2) job `docker` existe con contenido esperado, (3) `docker` va después de `check`, (4) `/api/health` es ruta real de la app (con Settings aislado y sin vars DOCUCHAT_), (5) sin tabuladores en ci.yml.

## Verificación
- `uv run pytest -q tests/test_ci_workflow.py` → 5 passed
- `uv run pytest -q` → 452 passed, 0 failures
- `uv run ruff check .` → all checks passed
- `uv run ruff format --check .` → 149 files already formatted
- `uv run mypy src` → success: no issues found in 37 source files

## Decisiones que tomé
Ninguna — la spec fijaba el contenido exacto del job y los 5 tests.

## Bloqueos y dudas
Ninguno. Todo pasó en el primer intento de tests.
