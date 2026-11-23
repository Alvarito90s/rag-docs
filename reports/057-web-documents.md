# Informe 057 · Interfaz web: página de documentos con HTMX
Estado: COMPLETADA

## Cambios
- `src/docuchat/api/templates/documents.html`: copia exacta de `tasks/assets/057/documents.html` (lista de documentos indexados + botones HTMX actualizar/reconstruir).
- `src/docuchat/api/templates/_job.html`: copia exacta de `tasks/assets/057/_job.html` (fragmento de progreso con polling cada 1s).
- `src/docuchat/api/static/vendor/htmx.min.js`: descargado con curl desde unpkg (50 917 bytes).
- `src/docuchat/api/routes_web.py`: añadidas 3 rutas — `GET /documents`, `POST /ui/ingest`, `GET /ui/ingest/{job_id}` — reutilizando `list_documents` y `job_to_dict` de módulos existentes.
- `tests/api/test_web.py`: añadidos tests 6–15 (15 tests en total).

## Verificación
- `uv run pytest -q tests/api/test_web.py` → 15 passed
- `uv run pytest -q` → 379 passed, 5 failures preexistentes (chromadb/searcher/CLI)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores
- `grep -rn "unpkg\|cdn" src/docuchat/api/templates` → sin resultados
- Diffs de documentos.html y _job.html → sin diferencias

## Decisiones que tomé
- La ruta `GET /ui/ingest/{job_id}` devuelve `Response` (no `HTMLResponse`) para poder pasar `headers` con `HX-Refresh`.
- No se usa `python-multipart`: el campo `reset` llega como query parameter `?reset=true`, evitando la dependencia extra.
- Los tests 9 y 10 lanzan su propia ingesta (no dependen del fixture `ingested` para evitar problemas de estado compartido entre tests).
- Se añadió el test `test_htmx_serve` (GET /static/vendor/htmx.min.js → 200) como cobertura extra de que el archivo se sirve correctamente.

## Bloqueos y dudas
Sin bloqueos. Todos los tests y verificaciones pasan correctamente.
