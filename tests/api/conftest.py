"""Fixtures compartidos para tests de la API."""

import os
import threading
from collections.abc import Iterator, Sequence
from pathlib import Path

import httpx
import pytest
from openai import APIConnectionError
from openai.types.chat import ChatCompletionMessageParam
from starlette.testclient import TestClient

from docuchat.api.app import Services, create_app
from docuchat.config import Settings

Message = ChatCompletionMessageParam

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


class FakeEmbedder:
    def __init__(self) -> None:
        self.block: threading.Event | None = None
        self.fail_on_query = False

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if self.block is not None:
            self.block.wait(10)
        if self.fail_on_query and any(t.startswith("Instruct:") for t in texts):
            raise APIConnectionError(
                message="Connection refused", request=httpx.Request("POST", "http://test")
            )
        return [[float(len(t)), 1.0, 0.5] for t in texts]


class FakeChat:
    def __init__(self) -> None:
        self.pieces: list[str] = ["Dato ", "[1]."]
        self.fail = False
        self.calls: list[list[Message]] = []

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        self.calls.append(list(messages))
        if self.fail:
            raise APIConnectionError(
                message="Connection refused", request=httpx.Request("POST", "http://test")
            )
        yield from self.pieces


@pytest.fixture()
def api_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Settings:
    """Settings con variables borradas, samples copiados y rutas apuntando a tmp."""
    for key in list(os.environ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    for path in SAMPLES.rglob("*"):
        if path.is_file():
            dest = docs_dir / path.relative_to(SAMPLES)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(path.read_bytes())

    return Settings(
        data_dir=tmp_path / "data",
        documents_dir=docs_dir,
    )


@pytest.fixture()
def embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture()
def chat() -> FakeChat:
    return FakeChat()


@pytest.fixture()
def app(api_settings: Settings, embedder: FakeEmbedder, chat: FakeChat):
    return create_app(api_settings, embedder=embedder, chat=chat)


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def services(app: object) -> Services:
    return app.state.services


@pytest.fixture()
def ingested(client: TestClient, services: Services):
    services.jobs.start()
    services.jobs.wait(services.jobs.latest().id)
    assert services.jobs.latest().status == "done"
    return client
