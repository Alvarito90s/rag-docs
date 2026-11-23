# 056 · Interfaz web: página de preguntas
Fase: 5 · Depende de: 054, 055

## Objetivo
Página principal: caja de pregunta, respuesta en streaming (desde `/api/ask`), citas `[n]` enlazadas al PDF en su página y lista de fuentes.

## Archivos
Excepción a la regla de 3 archivos: las plantillas y los estáticos se COPIAN tal cual de `tasks/assets/056/` (no los reescribas ni los "mejores").
- crear (copia exacta): `src/docuchat/api/templates/base.html` ← `tasks/assets/056/base.html`
- crear (copia exacta): `src/docuchat/api/templates/index.html` ← `tasks/assets/056/index.html`
- crear (copia exacta): `src/docuchat/api/static/app.js` ← `tasks/assets/056/app.js`
- crear (copia exacta): `src/docuchat/api/static/style.css` ← `tasks/assets/056/style.css`
- modificar: `src/docuchat/api/routes_web.py` (solo AÑADIR `TEMPLATES` y la ruta `/`)
- modificar: `src/docuchat/api/app.py` (solo montar `/static` en `create_app`)
- crear: `tests/api/test_web.py`

Cópialos con `cp` (`mkdir -p` antes). Comprueba con `diff` que son idénticos.

## Interfaz
`routes_web.py`:
```python
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES = Jinja2Templates(directory=Path(__file__).parent / "templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, services: ServicesDep) -> HTMLResponse:
    """Página de preguntas."""
```
`app.py`, dentro de `create_app`:
```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
```

## Comportamiento
1. `index` → `TEMPLATES.TemplateResponse(request, "index.html", {"chunks": services.searcher.size(), "llm_model": settings.llm_model})`.
2. Qué hace `app.js` (ya escrito, solo para que lo entiendas): al enviar el formulario hace `fetch("/api/ask")` con POST y JSON, lee el cuerpo con `getReader()`, separa los eventos SSE por `"\n\n"`, añade cada `token` al texto de la respuesta y, con `done`, enlaza las citas `[n]` a `url` (`/files/<doc>#page=N`, en pestaña nueva), lista las fuentes y avisa de citas inventadas. `error` muestra el mensaje. Enter envía; Mayús+Enter hace salto de línea.
3. Las plantillas usan `url_for('static', path=...)`: por eso el montaje se llama `name="static"`.
4. Los archivos de `templates/` y `static/` están bajo `src/docuchat/`, así que hatchling los incluye en el paquete sin tocar `pyproject.toml`.

## Tests obligatorios
`tests/api/test_web.py` (fixtures de `conftest.py`). NO cambies los valores esperados.
1. `GET /` con índice vacío → 200, `content-type` empieza por `"text/html"`; el HTML contiene `'id="ask-form"'`, `'id="answer"'`, `'id="sources"'`, `"static/app.js"`, `"static/style.css"` y `"El índice está vacío"`.
2. Con `ingested` → contiene `"26 fragmentos indexados"` y `"Qwen3.6-35B-A3B-6bit"`, y no `"El índice está vacío"`.
3. `GET /static/app.js` → 200 y contiene `"/api/ask"`, `"getReader"` y `"linkCitations"`.
4. `GET /static/style.css` → 200 y contiene `"prefers-color-scheme"`.
5. Las copias son exactas: para cada uno de los 4 archivos, `(ASSETS / nombre).read_bytes() == (destino).read_bytes()`, con `ASSETS = Path(__file__).resolve().parents[2] / "tasks" / "assets" / "056"`.

## Aceptación
- [ ] `uv run pytest -q tests/api/test_web.py` → 5 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `diff -r tasks/assets/056/app.js src/docuchat/api/static/app.js` (y los otros 3) → sin diferencias
- [ ] (humano) `uv run docuchat serve`, abrir `http://127.0.0.1:8001/`, preguntar "¿Qué significa el error E-17?" → la respuesta aparece poco a poco, `[1]` es un enlace que abre `manual_cafetera.pdf` en la página 7, y abajo sale "Fuentes"

## Fuera de alcance
Página de documentos y HTMX (057). No modifiques los archivos copiados ni la API.
