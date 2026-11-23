# 050 · Dependencias y config de la API
Fase: 5 · Depende de: 045-b

## Objetivo
Añadir FastAPI, Uvicorn y Jinja2, y los ajustes de host y puerto de la app. El puerto por defecto es 8001 porque 8000 lo usa oMLX.

## Archivos
Excepción a la regla de 3 archivos: son añadidos pequeños.
- modificar: `pyproject.toml` y `uv.lock`, SOLO con: `uv add "fastapi>=0.165,<1" "uvicorn>=0.54,<1" "jinja2>=3.1,<4"`
- modificar: `src/docuchat/config.py` (solo AÑADIR campos)
- modificar: `.env.example` (solo AÑADIR 2 líneas al final)
- modificar: `tests/test_config.py` (solo AÑADIR tests)

## Interfaz
En `Settings`, después de `context_max_chars`:
```python
# API web
api_host: str = "127.0.0.1"
api_port: int = Field(default=8001, gt=0, le=65535)  # 8000 lo usa oMLX
```
`.env.example`, al final:
```
DOCUCHAT_API_HOST=127.0.0.1
DOCUCHAT_API_PORT=8001
```

## Tests obligatorios
Añadir a `tests/test_config.py` (fixture autouse existente). NO cambies los valores esperados.
1. `test_api_defaults`: `api_host == "127.0.0.1"`, `api_port == 8001`.
2. `test_api_env_override`: env `DOCUCHAT_API_PORT=9000` → `9000`.
3. `test_invalid_api_port` (parametrizado, 2 casos): `{"api_port": 0}`, `{"api_port": 70000}` → `ValidationError`.

## Aceptación
- [ ] `uv run pytest -q tests/test_config.py` → 32 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `uv run python -c "import fastapi, uvicorn, jinja2; from fastapi.sse import EventSourceResponse; print(fastapi.__version__)"` imprime `0.165` o superior
- [ ] `git diff pyproject.toml` solo muestra las 3 dependencias nuevas

## Fuera de alcance
Ningún código de la API (specs 051–057). No añadas otras dependencias (ni `python-multipart` ni `sse-starlette`: FastAPI ya trae SSE).
