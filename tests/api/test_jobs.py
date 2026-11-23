"""Tests para IngestJobs (ingestas en segundo plano)."""

import os
import shutil
import threading
from collections.abc import Sequence
from pathlib import Path

import pytest

from docuchat.api.jobs import (
    IngestJobs,
    JobRunningError,
    JobStatus,
    job_to_dict,
)
from docuchat.config import Settings


class FakeEmbedder:
    def __init__(self) -> None:
        self.block: threading.Event | None = None
        self.fail = False

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if self.block is not None:
            self.block.wait(10)
        if self.fail:
            raise RuntimeError("connection refused")
        return [[float(len(t)), 1.0, 0.5] for t in texts]


SAMPLES = Path(__file__).parent.parent.parent / "samples"


@pytest.fixture()
def settings_docs(tmp_path: Path):
    """Settings limpia con copia de samples en tmp_path/docs."""
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            del os.environ[key]

    src = Path(__file__).parent.parent.parent / "samples"
    dest = tmp_path / "docs"
    shutil.copytree(src, dest)

    from docuchat.config import Settings

    return Settings(data_dir=tmp_path / "data", documents_dir=dest)


@pytest.fixture()
def jobs(settings_docs: Settings):
    """IngestJobs con embedder real y contador de on_finish."""
    embedder = FakeEmbedder()
    counter = [0]  # mutable para el closure

    def on_finish() -> None:
        counter[0] += 1

    inj = IngestJobs(settings_docs, embedder, on_finish)
    inj._finish_counter = counter  # type: ignore[attr-defined]
    inj._embedder = embedder  # type: ignore[attr-defined]
    return inj


def test_ingesta_normal(jobs: IngestJobs, settings_docs: Settings) -> None:
    job = jobs.start()
    assert job.status == JobStatus.RUNNING

    result = jobs.wait(job.id)
    assert result.status == JobStatus.DONE
    total_files = len(list(settings_docs.documents_dir.iterdir()))
    assert result.done == total_files
    assert result.total == total_files
    assert result.current == "politica_vacaciones.docx"
    assert result.stats is not None
    assert result.stats.chunks_added == 26
    assert result.finished_at is not None
    assert result.error is None
    assert jobs._finish_counter[0] == 1  # type: ignore[attr-defined]


def test_una_a_la_vez() -> None:
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            del os.environ[key]

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(__file__).parent.parent.parent / "samples"
        dest = Path(tmp) / "docs"
        shutil.copytree(src, dest)

        settings = Settings(
            data_dir=Path(tmp) / "data",
            documents_dir=dest,
        )
        embedder = FakeEmbedder()
        embedder.block = threading.Event()

        def on_finish() -> None:
            pass

        jobs = IngestJobs(settings, embedder, on_finish)

        job = jobs.start()
        assert jobs.is_running() is True

        with pytest.raises(JobRunningError):
            jobs.start()

        embedder.block.set()
        result = jobs.wait(job.id)
        assert result.status == JobStatus.DONE
        assert jobs.is_running() is False


def test_fallo() -> None:
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            del os.environ[key]

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(__file__).parent.parent.parent / "samples"
        dest = Path(tmp) / "docs"
        shutil.copytree(src, dest)

        settings = Settings(
            data_dir=Path(tmp) / "data",
            documents_dir=dest,
        )
        embedder = FakeEmbedder()
        embedder.fail = True
        counter = [0]

        def on_finish() -> None:
            counter[0] += 1

        jobs = IngestJobs(settings, embedder, on_finish)
        job = jobs.start()
        result = jobs.wait(job.id)

        assert result.status == JobStatus.FAILED
        assert result.error.startswith("RuntimeError")
        assert result.stats is None
        assert counter[0] == 1

        embedder.fail = False
        job2 = jobs.start()
        result2 = jobs.wait(job2.id)
        assert result2.status == JobStatus.DONE


def test_incremental(jobs: IngestJobs) -> None:
    job1 = jobs.start()
    result1 = jobs.wait(job1.id)
    assert result1.status == JobStatus.DONE

    job2 = jobs.start()
    result2 = jobs.wait(job2.id)
    assert result2.status == JobStatus.DONE
    assert result2.stats is not None
    assert len(result2.stats.unchanged) == 7
    assert result2.stats.chunks_added == 0


def test_reset(jobs: IngestJobs) -> None:
    job1 = jobs.start()
    jobs.wait(job1.id)

    job2 = jobs.start(reset=True)
    result2 = jobs.wait(job2.id)
    assert result2.status == JobStatus.DONE
    assert len(result2.stats.added) == 7


def test_carpeta_inexistente() -> None:
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            del os.environ[key]

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        settings = Settings(
            data_dir=Path(tmp) / "data",
            documents_dir=Path(tmp) / "no",
        )
        embedder = FakeEmbedder()
        counter = [0]

        def on_finish() -> None:
            counter[0] += 1

        jobs = IngestJobs(settings, embedder, on_finish)
        job = jobs.start()
        result = jobs.wait(job.id)

        assert result.status == JobStatus.FAILED
        assert result.error.startswith("FileNotFoundError")
        assert counter[0] == 1


def test_get_latest() -> None:
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            del os.environ[key]

    from docuchat.config import Settings

    settings = Settings()
    embedder = FakeEmbedder()

    def on_finish() -> None:
        pass

    jobs = IngestJobs(settings, embedder, on_finish)

    assert jobs.get("nada") is None
    assert jobs.latest() is None

    job = jobs.start()
    assert jobs.latest() is not None
    assert jobs.latest().id == job.id


def test_job_to_dict(jobs: IngestJobs) -> None:
    job = jobs.start()
    result = jobs.wait(job.id)

    d = job_to_dict(result)
    assert set(d.keys()) == {
        "id",
        "status",
        "reset",
        "done",
        "total",
        "current",
        "error",
        "started_at",
        "finished_at",
        "stats",
    }
    assert d["status"] == "done"
    assert d["stats"] == {
        "added": 7,
        "updated": 0,
        "unchanged": 0,
        "removed": 0,
        "errors": 0,
        "chunks_added": 26,
    }
    assert isinstance(d["started_at"], str)

    running_dict = job_to_dict(job)
    assert running_dict["stats"] is None
    assert running_dict["finished_at"] is None
