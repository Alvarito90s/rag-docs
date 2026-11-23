# Informe 052 · App FastAPI: servicios, /api/health y /api/documents
Estado: COMPLETADA

## Cambios

- `src/docuchat/api/app.py`: **archivo nuevo** — `Services` (settings, embedder, chat, searcher, answerer, jobs con IngestJobs), `reload()` que reconstruye searcher y answerer, `get_services()` como dependencia FastAPI (`request.app.state.services`), `ServicesDep = Annotated[Services, Depends(get_services)]`, `create_app()` con FastAPI(title="DocuChat Local", version=__version__), inyección de embedder/chat para tests, import de `router` dentro de la función para evitar import circular.
- `src/docuchat/api/routes_api.py`: **archivo nuevo** — `router = APIRouter(prefix="/api")`, `file_url(source, page)` con `quote(source)` y `#page=N` opcional, `GET /api/health` (sync, devuelve status/chunks/documents/llm_model/embedding_model/ingest_running, abre/cierra Registry en cada petición), `GET /api/documents` (sync, lista ordenada por source con source/chunks/indexed_at/url, usa `with Registry(...)` para seguridad de hilos).
- `tests/api/conftest.py`: **archivo nuevo** — `FakeEmbedder` (devuelve `[[float(len(t)), 1.0, 0.5]]`, `threading.Event` para bloqueos, `APIConnectionError` en `fail_on_query`), `FakeChat` (devuelve `["Dato ", "[1]."]`, `APIConnectionError` en `fail`), fixtures: `api_settings` (borra DOCUCHAT_*, copia samples, Settings con rutas tmp), `embedder`, `chat`, `app`, `client`, `services`, `ingested` (start + wait + assert DONE).
- `tests/api/test_api.py`: **archivo nuevo** — 9 tests: health vacío (valores exactos), health tras ingesta (chunks=26, documents=7), documents vacío ([]), documents tras ingesta (7 elementos ordenados, primer source=apuntes_redes.md, url correcta, sum chunks=26, claves correctas), reload tras ingesta (searcher es otro objeto), reset no rompe buscador, file_url con página y sin página, create_app sin embedder ni chat.

## Verificación

```
$ uv run pytest -q tests/api/test_api.py
......... [100%]  9 passed

$ uv run pytest -q
338 passed

$ uv run ruff check .
All checks passed!

$ uv run ruff format --check .
113 files already formatted

$ uv run mypy src
Success: no issues found in 30 source files

$ grep -n "async def" src/docuchat/api/*.py
(sin resultados)
```

## Decisiones que tomé

- **No usé `BaseHTTPMiddleware`**: lo añadí en el primer intento para cerrar recursos al finalizar cada petición, pero causó errores mypy y la spec no lo requiere. El patrón `with Registry(...)` en cada endpoint ya maneja correctamente el ciclo de vida del registro SQLite, que es el único recurso que necesita cierre explícito.
- **Import circular resuelto**: `router` se importa dentro de `create_app()` como indica la spec, evitando que `routes_api` (que importa `ServicesDep` de `app`) se cargue antes de que `app` esté definido.
- **`APIConnectionError` en lugar de `httpx.ConnectError`**: seguí la spec que importa `APIConnectionError` de `openai` para los mocks de fallas de red.

## Bloqueos y dudas

Ninguno. Todo pasó a la primera tras corregir:
1. `ServicesDep = Depends(...)` → `ServicesDep = Annotated[Services, Depends(...)]` (FastAPI necesita el tipo `Services` como primer argumento del `Annotated`).
2. Importar `Annotated` de `typing` en `app.py`.
3. Eliminar import circular y middleware innecesario.
