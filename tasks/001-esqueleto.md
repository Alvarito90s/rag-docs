# 001 · Esqueleto del repo
Fase: 0 · Depende de: ninguna

## Objetivo
Crear el proyecto Python con uv (layout `src/`), dependencias fijadas, `.gitignore`, licencia MIT y carpetas base.

## Archivos
Excepción a la regla de 3 archivos: todos son plantillas con contenido exacto. Cópialo tal cual.
- crear/reemplazar: `pyproject.toml`
- crear/reemplazar: `.gitignore`
- crear: `LICENSE`
- crear/reemplazar: `README.md`
- crear/reemplazar: `src/docuchat/__init__.py`
- crear (vacíos): `tests/fixtures/.gitkeep`, `scripts/.gitkeep`, `samples/.gitkeep`, `eval/.gitkeep`
- generado por uv: `.python-version`, `uv.lock`

NO toques `AGENTS.md`, `tasks/`, `reports/_TEMPLATE.md`, `docs/`.

## Interfaz
`src/docuchat/__init__.py`, contenido exacto:
```python
"""DocuChat Local: RAG local con citas a la página exacta."""

__version__ = "0.1.0"
```

## Comportamiento
1. En la raíz del repo ejecuta:
   `uv init --package --name docuchat --python 3.12 --vcs git .`
   Si falla, no insistas: crea a mano los archivos de esta spec, luego `git init` y `uv python pin 3.12`.
2. Sobrescribe los archivos generados con el contenido exacto de abajo. Borra cualquier otro archivo `.py` que haya creado `uv init` (p. ej. `main.py`).
3. `.python-version` debe contener `3.12`.
4. Ejecuta `uv sync` (crea `.venv/` y `uv.lock`).

`pyproject.toml` (contenido exacto; las cotas de versión las fija el cerebro, no las cambies):
```toml
[project]
name = "docuchat"
version = "0.1.0"
description = "Buscador semántico local (RAG) con citas a la página exacta."
readme = "README.md"
license = "MIT"
license-files = ["LICENSE"]
requires-python = ">=3.12"
dependencies = [
    "openai>=2.0,<3",
    "pydantic>=2.11,<3",
    "pydantic-settings>=2.10,<3",
    "pymupdf>=1.26,<2",
    "python-docx>=1.1,<2",
]

[dependency-groups]
dev = [
    "mypy>=2.4",
    "pytest>=9.0",
    "ruff>=0.17",
]

[build-system]
requires = ["hatchling>=1.27"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/docuchat"]
```

`.gitignore` (contenido exacto):
```
# Python
__pycache__/
*.py[cod]
.venv/
build/
dist/
*.egg-info/

# Herramientas
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Entorno y datos locales
.env
data/

# Sistema y editores
.DS_Store
.idea/
.vscode/
```

`README.md` (contenido exacto, se reescribe en la Fase 7):
```markdown
# DocuChat Local

Pregunta a tus documentos en local, con citas a la página exacta. Sin enviar nada a la nube.

> En construcción.
```

`LICENSE`: texto estándar de la licencia MIT, primera línea `MIT License`, línea de copyright exacta `Copyright (c) 2026 Álvaro`.

## Tests obligatorios
Ninguno (no hay funciones). El primer test llega en la spec 002.

## Referencia de librerías
- `uv init --package` crea layout `src/<paquete>/`. `uv sync` instala el proyecto en modo editable + el grupo `dev`.
- `uv.lock` SE VERSIONA: no lo añadas al `.gitignore`.

## Aceptación
- [ ] `uv sync` termina sin errores
- [ ] `uv run python -c "import docuchat; print(docuchat.__version__)"` imprime `0.1.0`
- [ ] `git check-ignore -q uv.lock` devuelve código 1 (no ignorado)
- [ ] `git check-ignore -q .env data/x .venv/x` devuelve código 0
- [ ] `cat .python-version` muestra `3.12`

## Fuera de alcance
Configuración de ruff/mypy/pytest, CI, `config.py`, cualquier módulo o comando CLI (`[project.scripts]` llega en la Fase 1).
