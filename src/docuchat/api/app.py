"""App FastAPI con servicios compartidos (buscador, answerer, ingestas)."""

from pathlib import Path
from typing import Annotated, cast

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles

from docuchat import __version__
from docuchat.api.jobs import IngestJobs
from docuchat.config import Settings, get_settings
from docuchat.generation.answer import build_answerer
from docuchat.generation.llm_client import ChatModel, make_chat_model
from docuchat.index.embeddings import Embedder
from docuchat.retrieval.searcher import build_searcher


class Services:
    """Objetos compartidos por todas las peticiones."""

    def __init__(
        self, settings: Settings, embedder: Embedder | None = None, chat: ChatModel | None = None
    ) -> None:
        self.settings = settings
        self.embedder = embedder
        self.chat = chat or make_chat_model(settings)
        self.reload()
        self.jobs = IngestJobs(settings, embedder, self.reload)

    def reload(self) -> None:
        """Reconstruye searcher y answerer (tras cada ingesta)."""
        self.searcher = build_searcher(settings=self.settings, embedder=self.embedder)
        self.answerer = build_answerer(
            settings=self.settings,
            retriever=self.searcher,
            chat=self.chat,
        )


def get_services(request: Request) -> Services:
    """Dependencia FastAPI: los servicios guardados en app.state."""
    return cast(Services, request.app.state.services)


ServicesDep = Annotated[Services, Depends(get_services)]


def create_app(
    settings: Settings | None = None,
    *,
    embedder: Embedder | None = None,
    chat: ChatModel | None = None,
) -> FastAPI:
    """App DocuChat; embedder y chat inyectables para tests."""
    settings = settings or get_settings()

    app = FastAPI(title="DocuChat Local", version=__version__)
    app.state.services = Services(settings, embedder, chat)
    from docuchat.api.routes_api import router
    from docuchat.api.routes_web import router as web_router

    app.include_router(router)
    app.include_router(web_router)

    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "static"),
        name="static",
    )

    return app
