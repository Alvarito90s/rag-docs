# 004-c · check_env: no romper con la clave vacía
Fase: 0 · Depende de: 004-b

## Objetivo
Corregir un error de la spec 004 (del cerebro): con `DOCUCHAT_LLM_API_KEY` vacía, `OpenAI(api_key="")` lanza `OpenAIError: Missing credentials` al CREAR el cliente, y `scripts/check_env.py` termina con traceback. Debe imprimir el aviso y los `[FAIL]`.

## Archivos
- modificar: `src/docuchat/env_check.py` (solo añadir la constante y cambiar `make_client`)
- modificar: `tests/test_env_check.py` (solo AÑADIR 2 tests)

## Interfaz
```python
MISSING_API_KEY = (
    "sin-clave"  # marcador: el servidor responderá 401 en vez de romper al crear el cliente
)
```
En `make_client`: `api_key=settings.llm_api_key or MISSING_API_KEY`.

## Tests obligatorios
NO cambies los existentes. Añade (con el fixture que borra `DOCUCHAT_*`, y `monkeypatch.delenv("OPENAI_API_KEY", raising=False)`):
1. `test_make_client_empty_key`: `make_client("http://127.0.0.1:9/v1", Settings())` no lanza y `client.api_key == "sin-clave"`.
2. `test_make_client_with_key`: con env `DOCUCHAT_LLM_API_KEY=abc` → `client.api_key == "abc"`.

## Aceptación
- [ ] `uv run pytest -q tests/test_env_check.py` pasa
- [ ] `env -u OPENAI_API_KEY DOCUCHAT_LLM_API_KEY= DOCUCHAT_LLM_BASE_URL=http://127.0.0.1:9/v1 DOCUCHAT_EMBEDDING_BASE_URL=http://127.0.0.1:9/v1 uv run python scripts/check_env.py; echo $?` → aviso de clave vacía, 4 líneas `[FAIL]`, `1`, sin traceback
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Todo lo demás.
