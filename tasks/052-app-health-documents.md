# 052 · App FastAPI: servicios, /api/health y /api/documents
Fase: 5 · Depende de: 051

## Objetivo
Crear la app FastAPI con sus servicios compartidos (buscador, answerer, ingestas) y los dos primeros endpoints de solo lectura. Deja preparado el `conftest.py` que usarán las specs 053–057.

## Archivos
Excepción a la regla de 3 archivos: `conftest.py` es infraestructura de tests compartida.
- crear: `src/docuchat/api/app.py`
- crear: `src/docuchat/api/routes_api.py`
- crear: `tests/api/conftest.py`
- crear: `tests/api/test_api.py`

## Interfaz
`src/docuchat/api/app.py`:
```python
from typing import Annotated

from fastapi import Depends, FastAPI, Request

from docuchat import __version__
from docuchat.api.jobs import IngestJobs
from docuchat.config import Settings, get_settings
from docuchat.generation.answer import Answerer, build_answerer
from docuchat.generation.llm_client import ChatModel, make_chat_model
from docuchat.index.embeddings import Embedder
from docuchat.retrieval.searcher import Searcher, build_searcher


class Services:
    """Objetos compartidos por todas las peticiones."""

    def __init__(
        self, settings: Settings, embedder: Embedder | None = None, chat: ChatModel | None = None
    ) -> None: ...
    # atributos públicos: settings, embedder, chat, searcher, answerer, jobs

    def reload(self) -> None:
        """Reconstruye searcher y answerer (tras cada ingesta)."""


def get_services(request: Request) -> Services:
    """Dependencia FastAPI: los servicios guardados en app.state."""


ServicesDep = Annotated[Services, Depends(get_services)]


def create_app(
    settings: Settings | None = None,
    *,
    embedder: Embedder | None = None,
    chat: ChatModel | None = None,
) -> FastAPI:
    """App DocuChat; embedder y chat inyectables para tests."""
```
`src/docuchat/api/routes_api.py`:
```python
from urllib.parse import quote

from fastapi import APIRouter

from docuchat.api.app import ServicesDep
from docuchat.index.registry import Registry

router = APIRouter(prefix="/api")


def file_url(source: str, page: int | None = None) -> str:
    """'/files/<source codificado>' y, si hay página, '#page=N'."""


@router.get("/health")
def health(services: ServicesDep) -> dict[str, object]: ...


@router.get("/documents")
def documents(services: ServicesDep) -> list[dict[str, object]]: ...
```

## Comportamiento
1. `Services.__init__`: guarda `settings` y `embedder`; `self.chat = chat or make_chat_model(settings)`; llama a `reload()`; `self.jobs = IngestJobs(settings, embedder, self.reload)`.
2. `reload`: `self.searcher = build_searcher(settings, embedder=self.embedder)` y `self.answerer = build_answerer(settings, retriever=self.searcher, chat=self.chat)`. Hay que reconstruir el buscador entero, no basta `refresh()`: tras un `reset_index` el VectorStore viejo apunta a una colección borrada y falla con `NotFoundError` (comprobado).
3. `create_app`: `settings = settings or get_settings()`; `FastAPI(title="DocuChat Local", version=__version__)`; `app.state.services = Services(settings, embedder, chat)`; `app.include_router(router)` (importa `router` dentro de la función para evitar el import circular con `routes_api`). `EmbeddingModelMismatchError` NO se captura (lo trata `serve`, spec 055).
4. `get_services` → `request.app.state.services` anotado como `Services`.
5. `file_url(source, page)` → `"/files/" + quote(source)` y, si `page` no es `None`, `+ f"#page={page}"`. `quote` deja `/` sin codificar.
6. `GET /api/health` → `{"status": "ok", "chunks": services.searcher.size(), "documents": n, "llm_model": settings.llm_model, "embedding_model": settings.embedding_model, "ingest_running": services.jobs.is_running()}`, con `n` = número de entradas del registro.
7. `GET /api/documents` → lista ordenada por `source` de `{"source", "chunks", "indexed_at", "url": file_url(source)}`, leída del `Registry(settings.registry_path)`. Abre y cierra el registro EN CADA petición (`with Registry(...)`): FastAPI ejecuta los endpoints síncronos en hilos y sqlite3 no comparte conexiones entre hilos.
8. Endpoints síncronos (`def`, no `async def`): todo lo que llaman es bloqueante.

## Tests obligatorios
`tests/api/conftest.py` (fixtures compartidos; NO los cambies en specs posteriores salvo que se diga):
```python
SAMPLES = Path(__file__).resolve().parents[2] / "samples"


class FakeEmbedder:
    def __init__(self) -> None:
        self.block: threading.Event | None = None
        self.fail_on_query = False

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if self.block is not None:
            self.block.wait(10)
        if self.fail_on_query and any(t.startswith("Instruct:") for t in texts):
            raise APIConnectionError(request=httpx.Request("POST", "http://test"))
        return [[float(len(t)), 1.0, 0.5] for t in texts]


class FakeChat:
    def __init__(self) -> None:
        self.pieces: list[str] = ["Dato ", "[1]."]
        self.fail = False
        self.calls: list[list[Message]] = []

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        self.calls.append(list(messages))
        if self.fail:
            raise APIConnectionError(request=httpx.Request("POST", "http://test"))
        yield from self.pieces
```
Fixtures: `api_settings` (borra `DOCUCHAT_*`, `chdir(tmp_path)`, copia `SAMPLES` a `tmp_path / "docs"`, devuelve `Settings(data_dir=tmp_path / "data", documents_dir=tmp_path / "docs")`), `embedder` (`FakeEmbedder()`), `chat` (`FakeChat()`), `app` (`create_app(api_settings, embedder=embedder, chat=chat)`), `client` (`TestClient(app)`), `services` (`app.state.services`), `ingested` (lanza `services.jobs.start()`, hace `wait`, comprueba `DONE` y devuelve `client`).

`tests/api/test_api.py`. NO cambies los valores esperados.
1. `GET /api/health` con índice vacío → 200 y `{"status": "ok", "chunks": 0, "documents": 0, "llm_model": "Qwen3.6-35B-A3B-6bit", "embedding_model": "Qwen3-Embedding-0.6B-4bit-DWQ", "ingest_running": False}`.
2. Con `ingested` → `chunks == 26`, `documents == 7`.
3. `GET /api/documents` vacío → `[]`.
4. Con `ingested` → 7 elementos ordenados por `source`; el primero tiene `source == "apuntes_redes.md"` y `url == "/files/apuntes_redes.md"`; `sum(d["chunks"]) == 26`; cada uno tiene las claves `{"source", "chunks", "indexed_at", "url"}`.
5. `reload` tras la ingesta: guarda `old = services.searcher`; tras una ingesta, `services.searcher is not old` y `services.searcher.size() == 26`.
6. Reset no rompe el buscador: tras `ingested`, `services.jobs.wait(services.jobs.start(reset=True).id)` → `DONE` y `GET /api/health` → `chunks == 26`.
7. `file_url("sub dir/a.pdf", 3)` → `"/files/sub%20dir/a.pdf#page=3"`; `file_url("a.md")` → `"/files/a.md"`.
8. `create_app(api_settings)` sin embedder ni chat (no hace red al crearse) → `GET /api/health` 200.

## Referencia de librerías
FastAPI 0.165 (comprobado):
```python
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

app = FastAPI(title="X", version="0.1.0")
app.state.services = ...            # cualquier objeto
client = TestClient(app)
client.get("/api/health").json()
```

## Aceptación
- [ ] `uv run pytest -q tests/api/test_api.py` → 8 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "async def" src/docuchat/api/*.py` → sin resultados

## Fuera de alcance
Search, ingest y ask por API (053, 054), `/files` y `serve` (055), HTML (056, 057).
