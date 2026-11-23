# Informe 004-c · check_env: no romper con la clave vacía
Estado: COMPLETADA

## Bug corregido
Con `DOCUCHAT_LLM_API_KEY` vacía, `OpenAI(api_key="")` lanzaba
`OpenAIError: Missing credentials` al **crear el cliente**, y
`scripts/check_env.py` terminaba con traceback.

## Cambios
- `src/docuchat/env_check.py`: añadida constante `MISSING_API_KEY = "sin-clave"`
  y cambiado `make_client` para usar `api_key=settings.llm_api_key or MISSING_API_KEY`.
  Cuando la clave está vacía, se envía el marcador `"sin-clave"` en vez de `""`,
  evitando `OpenAIError` y dejando que el servidor responda 401.
- `tests/test_env_check.py`: añadidos 2 tests obligatorios
  - `test_make_client_empty_key`: `Settings()` → `client.api_key == "sin-clave"`
  - `test_make_client_with_key`: `DOCUCHAT_LLM_API_KEY=abc` → `client.api_key == "abc"`

## Verificación
- `uv run pytest -q tests/test_env_check.py` → **25 passed** ✅
- `env -u OPENAI_API_KEY DOCUCHAT_LLM_API_KEY= uv run python scripts/check_env.py`
  → imprime aviso + `[FAIL]`, **sin traceback**, EXIT 1 ✅
- `uv run pytest -q` → **125 passed**, 5 warnings ✅
- `uv run ruff check .` → sin errores ✅
- `uv run ruff format --check .` → 49 files ✅
- `uv run mypy src` → success, 11 files ✅

## Observaciones
- Se reañadió `exclude = ["tasks"]` en `[tool.ruff]` del pyproject.toml porque
  las specs contienen bloques Python que ruff intentaba formatear como Python.
- El import `MISSING_API_KEY` en `test_env_check.py` se quitó (no se usa,
  los tests comprueban `client.api_key` directamente).

## Decisiones que tomé
Ninguna. La spec fija la constante, el cambio en `make_client` y los 2 tests.

## Bloqueos y dudas
Ninguno. Todo pasó a la primera tras corregir líneas largas y orden de imports.
