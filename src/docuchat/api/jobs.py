"""Ingestas en segundo plano con hilo, progreso y resultado."""

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
    ) -> None:
        self._settings = settings
        self._embedder = embedder
        self._on_finish = on_finish
        self._lock = threading.Lock()
        self._jobs: dict[str, IngestJob] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._last_id: str | None = None

    def _set(self, job_id: str, change: Callable[[IngestJob], IngestJob]) -> None:
        """Aplica *change* a la foto del job dentro del lock."""
        with self._lock:
            self._jobs[job_id] = change(self._jobs[job_id])

    def start(self, reset: bool = False) -> IngestJob:
        """Lanza una ingesta; JobRunningError si ya hay una en marcha."""
        with self._lock:
            if any(j.status == JobStatus.RUNNING for j in self._jobs.values()):
                raise JobRunningError("Ya hay una ingesta en marcha")
            job_id = uuid.uuid4().hex
            job = IngestJob(
                id=job_id,
                status=JobStatus.RUNNING,
                reset=reset,
                started_at=datetime.now(UTC),
            )
            self._jobs[job_id] = job
            self._last_id = job_id
            thread = threading.Thread(target=self._run, args=(job_id,), daemon=True)
            self._threads[job_id] = thread

        thread.start()
        return job

    def _run(self, job_id: str) -> None:
        """Ejecuta la indexación en este hilo."""
        with self._lock:
            reset = self._jobs[job_id].reset

        try:
            if reset:
                reset_index(self._settings)

            with build_indexer(self._settings, embedder=self._embedder) as indexer:
                stats = indexer.index_folder(
                    self._settings.documents_dir,
                    on_progress=lambda source, done, total: self._set(
                        job_id,
                        lambda j: replace(
                            j,
                            done=done,
                            total=total,
                            current=source,
                        ),
                    ),
                )

            total_files = (
                len(stats.added) + len(stats.updated) + len(stats.unchanged) + len(stats.removed)
            )
            self._set(
                job_id,
                lambda j: replace(
                    j,
                    status=JobStatus.DONE,
                    finished_at=datetime.now(UTC),
                    stats=stats,
                    done=total_files,
                    total=total_files,
                ),
            )
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            self._set(
                job_id,
                lambda j: replace(
                    j,
                    status=JobStatus.FAILED,
                    error=error_msg,
                    finished_at=datetime.now(UTC),
                ),
            )
        finally:
            self._on_finish()

    def get(self, job_id: str) -> IngestJob | None:
        """Estado actual de una ingesta, o None si no existe."""
        with self._lock:
            return self._jobs.get(job_id)

    def latest(self) -> IngestJob | None:
        """La última ingesta lanzada, o None."""
        with self._lock:
            if self._last_id is None:
                return None
            return self._jobs.get(self._last_id)

    def is_running(self) -> bool:
        """True si hay una ingesta en marcha."""
        with self._lock:
            return any(j.status == JobStatus.RUNNING for j in self._jobs.values())

    def wait(self, job_id: str, timeout: float = 60.0) -> IngestJob:
        """Espera a que termine el hilo y devuelve su estado."""
        thread = self._threads.get(job_id)
        if thread is not None:
            thread.join(timeout)
        result = self.get(job_id)
        if result is None:
            raise KeyError(job_id)
        return result


def job_to_dict(job: IngestJob) -> dict[str, object]:
    """Representación JSON de una ingesta."""
    stats_dict: object | None = None
    if job.stats is not None:
        stats_dict = {
            "added": len(job.stats.added),
            "updated": len(job.stats.updated),
            "unchanged": len(job.stats.unchanged),
            "removed": len(job.stats.removed),
            "errors": len(job.stats.errors),
            "chunks_added": job.stats.chunks_added,
        }
    return {
        "id": job.id,
        "status": str(job.status),
        "reset": job.reset,
        "done": job.done,
        "total": job.total,
        "current": job.current,
        "error": job.error,
        "started_at": job.started_at.isoformat(timespec="seconds"),
        "finished_at": job.finished_at.isoformat(timespec="seconds")
        if job.finished_at is not None
        else None,
        "stats": stats_dict,
    }
