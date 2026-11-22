# Informe 004-b · check_env: ajustes de revisión
Estado: COMPLETADA

## Cambios
- `src/docuchat/env_check.py`: `check_model_listed` ahora usa `model_available(model, ids)` en vez de `model in ids` (línea 39)
- `src/docuchat/env_check.py`: `main` usa cadena literal `"Aviso: DOCUCHAT_LLM_API_KEY está vacía; ponla en .env."` en vez de concatenación con `"." + "env."` (línea 100)
- `reports/003-b-config-omlx.md`: creado (la spec ya estaba implementada, solo se registró)

## Verificación
- `grep -n "model_available(model, ids)" src/docuchat/env_check.py` → línea 39 ✅
- `grep -n '"\." + ' src/docuchat/env_check.py` → 0 resultados ✅
- `ls reports/` muestra `003-b-config-omlx.md` y `004-check-env.md` ✅
- `uv run pytest -q` → 54 passed, 5 warnings ✅
- `uv run pytest -q tests/test_env_check.py` → 23 passed ✅
- `uv run ruff check . && uv run ruff format --check .` → all checks passed, 29 files formatted ✅
- `uv run mypy src` → success, no issues found in 3 source files ✅

## Decisiones que tomé
Ninguna. La spec fija todos los cambios exactamente.

## Bloqueos y dudas
Ninguno. Todo pasó a la primera.
