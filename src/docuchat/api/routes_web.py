"""Rutas web: servir archivos de documentos con /files/{source}."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from docuchat.api.app import ServicesDep
from docuchat.api.jobs import JobRunningError, job_to_dict
from docuchat.api.routes_api import documents as list_documents
from docuchat.ingest.scanner import is_supported

router = APIRouter()

TEMPLATES = Jinja2Templates(directory=Path(__file__).parent / "templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, services: ServicesDep) -> HTMLResponse:
    """Página de preguntas."""
    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "chunks": services.searcher.size(),
            "llm_model": services.settings.llm_model,
        },
    )


def resolve_document(root: Path, source: str) -> Path | None:
    """Ruta del documento source dentro de root, o None si sale de root."""
    base = root.resolve()
    path = (base / source).resolve()
    if not path.is_relative_to(base):
        return None
    if not path.is_file():
        return None
    if not is_supported(path):
        return None
    return path


@router.get("/files/{source:path}")
def get_file(source: str, services: ServicesDep) -> FileResponse:
    """Sirve el archivo de documento original; 404 si no existe o no es soportado."""
    path = resolve_document(services.settings.documents_dir, source)
    if path is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return FileResponse(path)


@router.get("/documents", response_class=HTMLResponse)
def documents_page(request: Request, services: ServicesDep) -> HTMLResponse:
    """Página con la lista de documentos indexados y botones de ingesta."""
    last = services.jobs.latest()
    job = job_to_dict(last) if last is not None else None
    return TEMPLATES.TemplateResponse(
        request,
        "documents.html",
        {
            "documents": list_documents(services),
            "job": job,
            "message": None,
            "documents_dir": str(services.settings.documents_dir),
        },
    )


@router.post("/ui/ingest", response_class=HTMLResponse)
def ui_start_ingest(
    request: Request,
    services: ServicesDep,
    reset: bool = Query(default=False),
) -> HTMLResponse:
    """Lanza una ingesta desde la UI y devuelve el fragmento de progreso."""
    try:
        job = services.jobs.start(reset)
    except JobRunningError:
        return TEMPLATES.TemplateResponse(
            request,
            "_job.html",
            {"job": None, "message": "Ya hay una ingesta en marcha"},
        )
    return TEMPLATES.TemplateResponse(
        request,
        "_job.html",
        {"job": job_to_dict(job), "message": None},
    )


@router.get("/ui/ingest/{job_id}", response_class=HTMLResponse)
def ui_ingest_status(request: Request, job_id: str, services: ServicesDep) -> Response:
    """Devuelve el fragmento de progreso de una ingesta por su ID."""
    job = services.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Ingesta no encontrada")
    headers: dict[str, str] = {}
    if job.status != "running":
        headers["HX-Refresh"] = "true"
    return TEMPLATES.TemplateResponse(
        request,
        "_job.html",
        {"job": job_to_dict(job), "message": None},
        background=None,
        headers=headers,
    )
