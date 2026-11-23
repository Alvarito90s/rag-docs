# 051 · Ingestas en segundo plano
Fase: 5 · Depende de: 050

## Objetivo
`IngestJobs`: lanza la indexación en un hilo, expone su progreso y su resultado, y no permite dos a la vez. Lo usará la API (053 y 057).

## Archivos
- crear: `src/docuchat/api/__init__.py` (solo el docstring `"""API web: FastAPI, rutas y plantillas."""`)
- crear: `src/docuchat/api/jobs.py`
- crear: `tests/api/__init__.py` (vacío) y `tests/api/test_jobs.py`

## Interfaz
```python
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum

from docuchat.config import Settings
from docuchat.index.embeddings import Embedder
from docuchat.index.indexer import IndexStats, build_indexer, reset_index


class JobStatus(StrEnum):
    """Estado de una ingesta."""

    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class JobRunningError(RuntimeError):
    """Ya hay una ingesta en marcha."""


@dataclass(frozen=True)
class IngestJob:
    """Foto inmutable del estado de una ingesta."""

    id: str
    status: JobStatus
    reset: bool
    started_at: datetime
    finished_at: datetime | None = None
    done: int = 0
    total: int = 0
    current: str = ""
    stats: IndexStats | None = None
    error: str | None = None


class IngestJobs:
    """Ejecuta ingestas de settings.documents_dir de una en una, en un hilo."""

    def __init__(
        self, settings: Settings, embedder: Embedder | None, on_finish: Callable[[], None]
    ) -> None: ...
    def start(self, reset: bool = False) -> IngestJob:
        """Lanza una ingesta; JobRunningError si ya hay una en marcha."""
    def get(self, job_id: str) -> IngestJob | None:
        """Estado actual de una ingesta, o None si no existe."""
    def latest(self) -> IngestJob | None:
        """La última ingesta lanzada, o None."""
    def is_running(self) -> bool:
        """True si hay una ingesta en marcha."""
    def wait(self, job_id: str, timeout: float = 60.0) -> IngestJob:
        """Espera a que termine el hilo (para tests y scripts) y devuelve su estado."""


def job_to_dict(job: IngestJob) -> dict[str, object]:
    """Representación JSON de una ingesta."""
```

## Comportamiento
1. Estado protegido por un `threading.Lock`: un `dict[str, IngestJob]` (id → foto), un `dict[str, threading.Thread]` y el id de la última. Para cambiar una foto usa un método privado `_set(job_id, change: Callable[[IngestJob], IngestJob])` que, dentro del lock, aplica `change` (con `dataclasses.replace`). Sin `# type: ignore`.
2. `start`: dentro del lock, si hay alguna `RUNNING` → `JobRunningError("Ya hay una ingesta en marcha")`. Si no, crea `IngestJob(id=uuid.uuid4().hex, status=RUNNING, reset=reset, started_at=datetime.now(UTC))`, la guarda como última, crea `threading.Thread(target=self._run, args=(job.id,), daemon=True)`. Fuera del lock, `thread.start()` y devuelve la foto inicial.
3. `_run(job_id)`:
   a. `try`: si `reset` → `reset_index(settings)`. `with build_indexer(settings, embedder=embedder) as indexer:` → `stats = indexer.index_folder(settings.documents_dir, on_progress=...)`, donde el callback actualiza `current`, `done` y `total`. Después: `status=DONE`, `stats`, `finished_at=datetime.now(UTC)`.
   b. `except Exception as e` → `status=FAILED`, `error=f"{type(e).__name__}: {e}"`, `finished_at`. (Es el único `except`: un hilo no debe morir en silencio.)
   c. `finally` → `on_finish()` (la app reconstruye el buscador; ver 052). Se llama SIEMPRE, también si falla.
   d. El `Registry` y Chroma se abren DENTRO del hilo (lo hace `build_indexer`): sqlite3 no permite usar una conexión en otro hilo.
4. `wait`: `thread.join(timeout)` y devuelve `get(job_id)`. Si el id no existe → `KeyError`.
5. `job_to_dict` → claves exactamente: `id`, `status` (str), `reset`, `done`, `total`, `current`, `error`, `started_at` (ISO 8601 con `isoformat(timespec="seconds")`), `finished_at` (ISO o `None`) y `stats`: `None` o `{"added": n, "updated": n, "unchanged": n, "removed": n, "errors": n, "chunks_added": n}` (los cinco primeros son longitudes de las listas).

## Tests obligatorios
`tests/api/test_jobs.py`. NO cambies los valores esperados. Nada de red.
```python
class FakeEmbedder:
    def __init__(self) -> None:
        self.block: threading.Event | None = None  # si está, embed espera a que se active
        self.fail = False

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if self.block is not None:
            self.block.wait(10)
        if self.fail:
            raise APIConnectionError(request=httpx.Request("POST", "http://test"))
        return [[float(len(t)), 1.0, 0.5] for t in texts]
```
Fixture `settings_docs`: borra `DOCUCHAT_*`, `chdir(tmp_path)`, `shutil.copytree(SAMPLES, tmp_path / "docs")` y devuelve `Settings(data_dir=tmp_path / "data", documents_dir=tmp_path / "docs")`. Fixture `jobs`: `IngestJobs(settings_docs, embedder, on_finish)` con `on_finish` que cuenta llamadas.
1. Ingesta normal: `job = jobs.start()` → `job.status == RUNNING`; `jobs.wait(job.id)` → `DONE`, `done == total == 7`, `current == "politica_vacaciones.docx"`, `stats.chunks_added == 26`, `finished_at is not None`, `error is None`; `on_finish` llamado 1 vez.
2. Una a la vez: `embedder.block = threading.Event()`; `job = jobs.start()`; `jobs.is_running() is True`; otro `jobs.start()` → `JobRunningError`; `embedder.block.set()`; `wait` → `DONE`; `is_running() is False`.
3. Fallo: `embedder.fail = True` → `wait` → `FAILED`, `error.startswith("APIConnectionError")`, `stats is None`; `on_finish` llamado 1 vez; después se puede lanzar otra (`fail = False` → `DONE`).
4. Incremental: dos ingestas seguidas → la segunda tiene `len(stats.unchanged) == 7` y `chunks_added == 0`.
5. Reset: tras una ingesta, `start(reset=True)` → `DONE`, `len(stats.added) == 7`.
6. Carpeta inexistente: `Settings(..., documents_dir=tmp_path / "no")` → `FAILED`, `error.startswith("FileNotFoundError")`.
7. `get("nada") is None`; `latest() is None` antes de empezar y `latest().id == job.id` después.
8. `job_to_dict` de la ingesta del test 1: claves `{"id", "status", "reset", "done", "total", "current", "error", "started_at", "finished_at", "stats"}`, `status == "done"`, `stats == {"added": 7, "updated": 0, "unchanged": 0, "removed": 0, "errors": 0, "chunks_added": 26}`, `started_at` es `str`. De una foto `RUNNING` recién creada: `stats is None` y `finished_at is None`.

## Aceptación
- [ ] `uv run pytest -q tests/api/test_jobs.py` → 8 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "type: ignore" src/docuchat/api/jobs.py` → sin resultados; `grep -c "except" src/docuchat/api/jobs.py` → `1`

## Fuera de alcance
Nada de FastAPI todavía (052). No toques `index/`.
