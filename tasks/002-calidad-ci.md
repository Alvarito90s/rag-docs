# 002 · Calidad: ruff, mypy, pytest y CI
Fase: 0 · Depende de: 001

## Objetivo
Configurar ruff, mypy (estricto) y pytest en `pyproject.toml`, un test de humo y un workflow de GitHub Actions que los ejecute.

## Archivos
- modificar: `pyproject.toml` (solo AÑADIR al final el bloque de abajo; no cambies nada más)
- crear: `.github/workflows/ci.yml`
- crear: `tests/test_smoke.py`

## Interfaz
Bloque a añadir al final de `pyproject.toml` (exacto):
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = ["pymupdf.*", "fitz.*", "docx.*", "rank_bm25.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --import-mode=importlib"
```

`.github/workflows/ci.yml` (exacto; las versiones de las acciones las fija el cerebro, no las cambies):
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10
        with:
          enable-cache: true
      - name: Instalar
        run: uv sync --locked
      - name: Ruff
        run: |
          uv run ruff check .
          uv run ruff format --check .
      - name: Mypy
        run: uv run mypy src
      - name: Pytest
        run: uv run pytest -q
```

`tests/test_smoke.py`:
```python
import docuchat


def test_version() -> None:
    assert docuchat.__version__ == "0.1.0"
```

## Comportamiento
1. Tras editar, ejecuta `uv run ruff format .` para formatear lo existente, y después las comprobaciones de Aceptación.
2. Con `--import-mode=importlib` los tests NO necesitan `__init__.py` en `tests/`. No los crees.
3. Si `uv sync --locked` falla en local porque el lock está desfasado, ejecuta `uv lock` y anótalo en el informe.

## Tests obligatorios
- `tests/test_smoke.py::test_version`: `docuchat.__version__` → `"0.1.0"`.

## Referencia de librerías
- Ruff: `ruff check .` (lint), `ruff format .` (formatea), `ruff format --check .` (solo comprueba).
- mypy: `strict = true` exige type hints en todas las funciones de `src/`. El plugin `pydantic.mypy` viene con pydantic; no hay que instalar nada.
- `setup-uv` instala uv; `uv sync` descarga Python 3.12 según `.python-version`.

## Aceptación
- [ ] `uv run pytest -q` → 1 passed
- [ ] `uv run ruff check .` y `uv run ruff format --check .` sin errores
- [ ] `uv run mypy src` → `Success: no issues found`
- [ ] `uv sync --locked` sin errores
- [ ] (humano, tras push a GitHub) el workflow CI sale en verde

## Fuera de alcance
Cobertura, pre-commit, badges, matrices de versiones de Python, cualquier código de `src/`.
