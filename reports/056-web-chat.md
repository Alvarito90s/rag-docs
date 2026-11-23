# Informe 056 · Interfaz web: página de preguntas
Estado: COMPLETADA

## Cambios
- `src/docuchat/api/templates/base.html`: copia exacta de `tasks/assets/056/` (plantilla base con head, header/nav, block content/scripts)
- `src/docuchat/api/templates/index.html`: copia exacta de `tasks/assets/056/` (formulario ask-form, sección result, warning, sources)
- `src/docuchat/api/static/app.js`: copia exacta de `tasks/assets/056/` (fetch SSE a /api/ask, streaming token, linkCitations)
- `src/docuchat/api/static/style.css`: copia exacta de `tasks/assets/056/` (CSS vars, prefers-color-scheme, layout)
- `src/docuchat/api/routes_web.py`: añadida variable `TEMPLATES` (Jinja2Templates) y nueva ruta `GET /` que renderiza `index.html` con `chunks` y `llm_model`
- `src/docuchat/api/app.py`: añadida importación de `Path` y `StaticFiles`; montado `/static` con `StaticFiles` al final de `create_app`
- `tests/api/test_web.py`: 5 tests (index vacío, index con documentos, static/app.js, static/style.css, copias exactas)

## Verificación
- `uv run pytest -q tests/api/test_web.py` → 5 passed, 0 failures
- `uv run pytest -q` → 374 passed, 0 failures
- `uv run ruff check .` → All checks passed!
- `uv run ruff format --check .` → 122 files already formatted
- `uv run mypy src` → Success: no issues found in 31 source files
- Diffs de copias → sin diferencias

## Decisiones que tomé
- Usé `services.settings.llm_model` en lugar de `settings.llm_model` (import de config), porque `config.py` no exporta una variable `settings` sino la función `get_settings()`. Esto es consistente con la práctica ya usada en `routes_api.py`.

## Bloqueos y dudas
- Ninguno. Todo limpio de primera.
