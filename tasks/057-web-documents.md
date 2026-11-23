# 057 · Interfaz web: página de documentos con HTMX
Fase: 5 · Depende de: 056

## Objetivo
Página `/documents` con la lista de documentos indexados (enlazados al original) y botones para actualizar o reconstruir el índice, con el progreso actualizándose solo (HTMX).

## Archivos
Excepción a la regla de 3 archivos: las plantillas se COPIAN tal cual de `tasks/assets/057/`.
- crear (copia exacta): `src/docuchat/api/templates/documents.html` ← `tasks/assets/057/documents.html`
- crear (copia exacta): `src/docuchat/api/templates/_job.html` ← `tasks/assets/057/_job.html`
- crear (descarga): `src/docuchat/api/static/vendor/htmx.min.js` con:
  `mkdir -p src/docuchat/api/static/vendor && curl -fsSL -o src/docuchat/api/static/vendor/htmx.min.js https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js`
  (se versiona: la app debe funcionar sin internet; no uses CDN en las plantillas)
- modificar: `src/docuchat/api/routes_web.py` (solo AÑADIR 3 rutas)
- modificar: `tests/api/test_web.py` (solo AÑADIR tests)

## Interfaz
```python
from docuchat.api.jobs import JobRunningError, job_to_dict
from docuchat.api.routes_api import documents as list_documents


@router.get("/documents", response_class=HTMLResponse)
def documents_page(request: Request, services: ServicesDep) -> HTMLResponse: ...


@router.post("/ui/ingest", response_class=HTMLResponse)
def ui_start_ingest(request: Request, services: ServicesDep, reset: bool = False) -> HTMLResponse: ...


@router.get("/ui/ingest/{job_id}", response_class=HTMLResponse)
def ui_ingest_status(request: Request, job_id: str, services: ServicesDep) -> HTMLResponse: ...
```

## Comportamiento
1. `documents_page` → `TemplateResponse(request, "documents.html", {"documents": list_documents(services), "job": job_to_dict(última) o None, "message": None, "documents_dir": str(settings.documents_dir)})`, con `última = services.jobs.latest()`.
2. `ui_start_ingest` (`reset` llega como query `?reset=true`; nada de formularios, así no hace falta `python-multipart`): `services.jobs.start(reset)` → fragmento `_job.html` con `{"job": job_to_dict(job), "message": None}`. `JobRunningError` → mismo fragmento con `{"job": None, "message": "Ya hay una ingesta en marcha"}` y status 200 (HTMX no pinta respuestas 4xx por defecto).
3. `ui_ingest_status`: id desconocido → `HTTPException(404, "Ingesta no encontrada")`. Si no, fragmento `_job.html` con su `job_to_dict`. Si su estado NO es `running`, añade la cabecera `HX-Refresh: true` a la respuesta (HTMX recarga la página y la tabla sale actualizada).
4. Mientras corre, el fragmento lleva `hx-get="/ui/ingest/<id>" hx-trigger="every 1s" hx-swap="outerHTML"` (ya está en `_job.html`): HTMX pregunta cada segundo y se reemplaza a sí mismo.

## Tests obligatorios
Añadir a `tests/api/test_web.py`. NO cambies los valores esperados ni los tests existentes. `services = app.state.services` (fixture).
6. `GET /documents` con índice vacío → 200; contiene `"No hay documentos indexados"`, `'hx-post="/ui/ingest"'` y `"static/vendor/htmx.min.js"`.
7. Con `ingested` → `html.count('href="/files/') == 7`, contiene `'href="/files/manual_cafetera.pdf"'` y `"7 añadidos"` (resumen de la última ingesta).
8. `POST /ui/ingest` con `embedder.block = threading.Event()` → 200; `job = services.jobs.latest()`; el HTML contiene `'hx-trigger="every 1s"'` y `f'hx-get="/ui/ingest/{job.id}"'`. Un segundo `POST /ui/ingest` → 200 y `"Ya hay una ingesta en marcha"`. Después `embedder.block.set()` y `services.jobs.wait(job.id)`.
9. Tras una ingesta terminada, `GET /ui/ingest/{id}` → 200, contiene `"7 añadidos"`, `response.headers["hx-refresh"] == "true"`.
10. Mientras corre (`block` puesto), `GET /ui/ingest/{id}` → `"hx-refresh" not in response.headers`; después liberar y esperar.
11. `GET /ui/ingest/nada` → 404.
12. `POST /ui/ingest?reset=true` → `services.jobs.latest().reset is True` (y esperar a que termine).
13. htmx local: `src/docuchat/api/static/vendor/htmx.min.js` existe, pesa más de 10 000 bytes y `GET /static/vendor/htmx.min.js` → 200.
14. Copias exactas de `documents.html` y `_job.html` respecto a `tasks/assets/057/` (como el test 5).

## Aceptación
- [ ] `uv run pytest -q tests/api/test_web.py` → 14 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -rn "unpkg\|cdn" src/docuchat/api/templates` → sin resultados
- [ ] (humano) `uv run docuchat serve` → `http://127.0.0.1:8001/documents` lista los 7 documentos; "Actualizar índice" muestra el progreso y al terminar recarga la tabla; el enlace de un PDF lo abre

## Fuera de alcance
No modifiques la API JSON, `jobs.py` ni las plantillas de la 056.
