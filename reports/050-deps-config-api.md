# Informe 050 · Dependencias y config de la API
Estado: COMPLETADA

## Cambios
- `pyproject.toml`: añadidas 3 dependencias — `fastapi>=0.165,<1`, `uvicorn>=0.54,<1`, `jinja2>=3.1,<4` (y resolvidas en `uv.lock`)
- `src/docuchat/config.py`: añadidos campos `api_host: str = "127.0.0.1"` y `api_port: int = Field(default=8001, gt=0, le=65535)` después de `context_max_chars`
- `.env.example`: añadidas 2 líneas al final — `DOCUCHAT_API_HOST=127.0.0.1` y `DOCUCHAT_API_PORT=8001`
- `tests/test_config.py`: añadidos 3 tests — `test_api_defaults`, `test_api_env_override`, `test_invalid_api_port` (parametrizado, 2 casos)

## Verificación
- `uv run pytest -q tests/test_config.py` → **32 passed** en 0.40s
- `uv run pytest -q` → **321 passed**, 5 warnings (todos de pymupdf, no nuestros)
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 103 files already formatted
- `uv run mypy src` → Success: no issues found in 26 source files
- Import verification → `0.165.0`

## Decisiones que tomé
Ninguna. La spec era explícita en todo.

## Bloqueos y dudas
Ninguno.
