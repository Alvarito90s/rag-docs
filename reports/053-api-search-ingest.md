# 053 · API: /api/search y /api/ingest — Informe

## Resumen

Se implementaron 3 endpoints REST en `routes_api.py` y se crearon 13 tests en `test_search_ingest.py`.

## Cambios realizados

### `src/docuchat/api/routes_api.py` (modificado)
- Se añadieron `APIRouter` e `HTTPException` a las importaciones de FastAPI.
- Se importaron `OpenAIError`, `BaseModel`, `Field` para los modelos de petición.
- Se importaron `JobRunningError`, `job_to_dict` de `api/jobs.py`.
- Se importó `EmbeddingError` de `index/embeddings.py`.
- Se importó `SearchResult` de `models.py`.
- Se importó `SearchMode` de `retrieval/searcher.py`.
- Se registró el router (`APIRouter(prefix="/api")`).
- Se reemplazaron los imports del `Registry` (que antes importaban dentro de cada función) por imports locales dentro de las funciones `health()` y `documents()`.
- Nueva clase `SearchRequest(BaseModel)`: `query` (min_length=1), `top_k` (int|None, gt=0), `mode` (SearchMode, default HYBRID).
- Nueva clase `IngestRequest(BaseModel)`: `reset` (bool, default False).
- Nueva función `result_to_dict(result: SearchResult) -> dict[str, object]`: serializa rank, score, source, page, heading, text, vector_rank, bm25_rank y url.
- Nuevo endpoint `POST /api/search`: busca con `services.searcher.search()`, captura `OpenAIError`/`EmbeddingError` → 502, devuelve lista de `result_to_dict`.
- Nuevo endpoint `POST /api/ingest` (202): acepta cuerpo opcional, llama a `services.jobs.start(reset)`, captura `JobRunningError` → 409.
- Nuevo endpoint `GET /api/ingest/{job_id}`: devuelve `job_to_dict`, 404 si no encontrado.

### `tests/api/test_search_ingest.py` (nuevo)
- 13 tests organizados en 4 clases: `TestSearch`, `TestSearchEmbeddingError`, `TestIngest`, `TestSearchAfterApiIngest`.
- Cobertura: búsqueda BM25 con resultados verificados, top_k, default, índice vacío, validación (3 casos parametrizados), error de embeddings → 502, ingest sin cuerpo, ingest con reset, concurrencia (409), ID desconocido (404), búsqueda tras ingest por API.

### `tests/api/conftest.py` (corrección menor)
- Se corrigió la firma de `APIConnectionError` en `FakeEmbedder` para usar `message="..."` en lugar de `"..."` como argumento posicional, compatible con openai 2.x.

## Verificaciones

| Verificación | Resultado |
|---|---|
| `uv run pytest -q tests/api/test_search_ingest.py` | 13 passed |
| `uv run pytest -q` completo | 351 passed |
| `uv run ruff check .` | ✅ sin errores |
| `uv run ruff format --check .` | ✅ todo formateado |
| `uv run mypy src` | ✅ sin errores |

## Bloqueos

Ninguno. Todas las verificaciones pasan.

## Notas

- Se usó `from e` en el `except (OpenAIError, EmbeddingError)` para cumplir con ruff B904.
- Se usó `from None` en el `except JobRunningError` para suprimir el chain traceback innecesario.
- En `start_ingest` se usó `# type: ignore[assignment]` para `services` con FastAPI dependency injection y cuerpo opcional.
- El endpoint `GET /api/ingest/{job_id}` se añade **después** del POST `/ingest` para evitar colisión de rutas en FastAPI.
