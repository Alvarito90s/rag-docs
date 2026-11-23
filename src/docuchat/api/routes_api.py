"""Rutas de la API REST: health, documentos, búsqueda e ingestas."""

import logging
from collections.abc import Iterator
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.sse import EventSourceResponse, ServerSentEvent
from openai import OpenAIError
from pydantic import BaseModel, Field

from docuchat.api.app import ServicesDep
from docuchat.api.jobs import JobRunningError, job_to_dict
from docuchat.generation.answer import Answer, build_answerer
from docuchat.index.embeddings import EmbeddingError
from docuchat.models import SearchResult
from docuchat.retrieval.searcher import SearchMode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def file_url(source: str, page: int | None = None) -> str:
    """'/files/<source codificado>' y, si hay página, '#page=N'."""
    result = "/files/" + quote(source)
    if page is not None:
        result += f"#page={page}"
    return result


class AskRequest(BaseModel):
    """Cuerpo de POST /api/ask."""

    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, gt=0)


def answer_to_dict(answer: Answer) -> dict[str, object]:
    """Datos del evento 'done'."""
    return {
        "text": answer.text,
        "no_answer": answer.no_answer,
        "sources": [
            {
                "number": source.number,
                "source": source.source,
                "page": source.page,
                "url": file_url(source.source, source.page),
            }
            for source in answer.sources
        ],
        "invalid_citations": answer.invalid_citations,
    }


@router.post("/ask", response_class=EventSourceResponse)
def ask(body: AskRequest, services: ServicesDep) -> Iterator[ServerSentEvent]:
    """Streaming SSE: eventos 'token', 'done' o 'error'."""
    answerer = (
        services.answerer
        if body.top_k is None
        else build_answerer(
            services.settings,
            retriever=services.searcher,
            chat=services.chat,
            top_k=body.top_k,
        )
    )

    try:
        context = answerer.retrieve(body.question)
        trozos: list[str] = []
        for trozo in answerer.stream(body.question, context):
            trozos.append(trozo)
            yield ServerSentEvent(event="token", data={"text": trozo})
        answer = answerer.finalize(body.question, "".join(trozos), context)
        yield ServerSentEvent(event="done", data=answer_to_dict(answer))
    except (OpenAIError, EmbeddingError) as e:
        yield ServerSentEvent(
            event="error",
            data={"message": f"{type(e).__name__}: {e}"},
        )
    except Exception as e:  # noqa: BLE001 — el stream debe terminar siempre con done o error
        logger.exception("Fallo inesperado en /api/ask")
        yield ServerSentEvent(
            event="error",
            data={"message": f"{type(e).__name__}: {e}"},
        )


@router.get("/health")
def health(services: ServicesDep) -> dict[str, object]:
    """Estado de la aplicación con métricas del índice."""
    from docuchat.index.registry import Registry

    reg = Registry(services.settings.registry_path)
    try:
        documents = len(reg.all())
    finally:
        reg.close()

    return {
        "status": "ok",
        "chunks": services.searcher.size(),
        "documents": documents,
        "llm_model": services.settings.llm_model,
        "embedding_model": services.settings.embedding_model,
        "ingest_running": services.jobs.is_running(),
    }


@router.get("/documents")
def documents(services: ServicesDep) -> list[dict[str, object]]:
    """Lista ordenada por source de los documentos indexados."""
    from docuchat.index.registry import Registry

    with Registry(services.settings.registry_path) as reg:
        all_entries = reg.all()

    return [
        {
            "source": source,
            "chunks": entry.chunk_count,
            "indexed_at": entry.indexed_at,
            "url": file_url(source),
        }
        for source, entry in sorted(all_entries.items())
    ]


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
    return {
        "rank": result.rank,
        "score": result.score,
        "source": result.chunk.source,
        "page": result.chunk.page,
        "heading": result.chunk.heading,
        "text": result.chunk.text,
        "vector_rank": result.vector_rank,
        "bm25_rank": result.bm25_rank,
        "url": file_url(result.chunk.source, result.chunk.page),
    }


@router.post("/search")
def search(body: SearchRequest, services: ServicesDep) -> list[dict[str, object]]:
    """Busca chunks y devuelve los resultados serializados."""
    k = body.top_k or services.settings.top_k
    try:
        results = services.searcher.search(body.query, k, body.mode)
    except (OpenAIError, EmbeddingError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error con el servidor de embeddings: {type(e).__name__}: {e}",
        ) from e
    return [result_to_dict(r) for r in results]


@router.post("/ingest", status_code=202)
def start_ingest(
    body: IngestRequest | None = None,
    services: ServicesDep = None,  # type: ignore[assignment]
) -> dict[str, object]:
    """Inicia una ingesta en segundo plano y devuelve el job."""
    reset = body.reset if body else False
    try:
        job = services.jobs.start(reset)
    except JobRunningError as e:
        raise HTTPException(status_code=409, detail=str(e)) from None
    return job_to_dict(job)


@router.get("/ingest/{job_id}")
def ingest_status(job_id: str, services: ServicesDep) -> dict[str, object]:
    """Devuelve el estado de una ingesta por su ID."""
    job = services.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Ingesta no encontrada")
    return job_to_dict(job)
