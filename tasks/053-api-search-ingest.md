# 053 · API: /api/search y /api/ingest
Fase: 5 · Depende de: 052

## Objetivo
Búsqueda por API y lanzamiento/consulta de ingestas en segundo plano.

## Archivos
- modificar: `src/docuchat/api/routes_api.py` (solo AÑADIR modelos y endpoints)
- crear: `tests/api/test_search_ingest.py`

## Interfaz
```python
from fastapi import HTTPException
from openai import OpenAIError
from pydantic import BaseModel, Field

from docuchat.api.jobs import JobRunningError, job_to_dict
from docuchat.index.embeddings import EmbeddingError
from docuchat.models import SearchResult
from docuchat.retrieval.searcher import SearchMode


class SearchRequest(BaseModel):
    """Cuerpo de POST /api/search."""

    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, gt=0)
    mode: SearchMode = SearchMode.HYBRID


class IngestRequest(BaseModel):
    """Cuerpo de POST /api/ingest."""

    reset: bool = False


def result_to_dict(result: SearchResult) -> dict[str, object]:
    """Representación JSON de un resultado de búsqueda."""


@router.post("/search")
def search(body: SearchRequest, services: ServicesDep) -> list[dict[str, object]]: ...


@router.post("/ingest", status_code=202)
def start_ingest(services: ServicesDep, body: IngestRequest | None = None) -> dict[str, object]: ...


@router.get("/ingest/{job_id}")
def ingest_status(job_id: str, services: ServicesDep) -> dict[str, object]: ...
```

## Comportamiento
1. `result_to_dict` → `{"rank", "score", "source", "page", "heading", "text", "vector_rank", "bm25_rank", "url": file_url(source, page)}`.
2. `POST /api/search`: `k = body.top_k or settings.top_k`; `services.searcher.search(body.query, k, body.mode)` → lista de `result_to_dict`. `OpenAIError` o `EmbeddingError` → `HTTPException(502, f"Error con el servidor de embeddings: {type(e).__name__}: {e}")`. Validación (query vacía, top_k ≤ 0, modo desconocido) → 422 automático de FastAPI.
3. `POST /api/ingest`: cuerpo opcional (`{}` o sin cuerpo → `reset=False`). `services.jobs.start(reset)` → 202 con `job_to_dict(job)`. `JobRunningError` → `HTTPException(409, "Ya hay una ingesta en marcha")`.
4. `GET /api/ingest/{job_id}` → `job_to_dict`; id desconocido → `HTTPException(404, "Ingesta no encontrada")`.

## Tests obligatorios
`tests/api/test_search_ingest.py`, con los fixtures de `conftest.py`. NO cambies los valores esperados.
1. `POST /api/search {"query": "E-17", "mode": "bm25"}` (con `ingested`) → 200; el primero: `source == "manual_cafetera.pdf"`, `page == 7`, `rank == 1`, `bm25_rank == 1`, `vector_rank is None`, `url == "/files/manual_cafetera.pdf#page=7"`, `"código de error E-17" in text`.
2. `{"query": "garantía", "top_k": 2}` → 2 resultados con `rank` `[1, 2]`.
3. Sin `top_k` → como mucho 5 resultados.
4. Validación (parametrizado, 3 casos): `{"query": ""}`, `{"query": "x", "top_k": 0}`, `{"query": "x", "mode": "otro"}` → 422.
5. Error de embeddings: `embedder.fail_on_query = True` (con `ingested`) → 502 y `detail.startswith("Error con el servidor de embeddings: APIConnectionError")`.
6. Índice vacío: `{"query": "E-17"}` → 200 y `[]`.
7. `POST /api/ingest` (sin cuerpo) → 202, `status == "running"`, `reset is False`; tras `services.jobs.wait(id)`, `GET /api/ingest/{id}` → 200, `status == "done"`, `stats["added"] == 7`, `stats["chunks_added"] == 26`.
8. `POST /api/ingest {"reset": true}` → 202 y `reset is True`.
9. Una a la vez: `embedder.block = threading.Event()`; primer `POST /api/ingest` → 202; segundo → 409 con `detail == "Ya hay una ingesta en marcha"`; `embedder.block.set()` y `wait`.
10. `GET /api/ingest/nada` → 404 y `detail == "Ingesta no encontrada"`.
11. Tras una ingesta por API, `POST /api/search {"query": "SKU-4471-B", "mode": "bm25"}` encuentra `glosario_interno.md` (el buscador se recargó).

## Aceptación
- [ ] `uv run pytest -q tests/api/test_search_ingest.py` → 13 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
`/api/ask` (054), HTML (056, 057). No toques `jobs.py` ni `app.py`.
