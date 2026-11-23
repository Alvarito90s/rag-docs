"""Tests para src/docuchat/index/embeddings.py."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from openai import APIConnectionError, OpenAI

from docuchat.config import Settings
from docuchat.index.embeddings import (
    Embedder,
    EmbeddingError,
    OpenAIEmbedder,
    make_embedder,
)

# ── Helper ─────────────────────────────────────────────────────────────


def fake_response(vectors: list[list[float]], order: list[int] | None = None) -> SimpleNamespace:
    """Devuelve un objeto SimpleNamespace que simula la respuesta del servidor."""
    if order is None:
        order = list(range(len(vectors)))
    data = [SimpleNamespace(index=i, embedding=v) for i, v in zip(order, vectors, strict=False)]
    return SimpleNamespace(data=data)


# ── Test 1: 5 textos, batch_size=2, 3 respuestas ──────────────────────


def test_batch_processing(settings: Settings):
    client = OpenAI(
        base_url=settings.embedding_base_url,
        api_key=settings.llm_api_key or "sin-clave",
        timeout=settings.request_timeout,
        max_retries=settings.request_max_retries,
    )
    client.embeddings.create = MagicMock()  # type: ignore[assignment]
    embedder = OpenAIEmbedder(client, "m", batch_size=2)
    embedder._client = client  # noqa: SLF001

    vectors = [[float(i)] for i in range(5)]
    client.embeddings.create.side_effect = [
        fake_response(vectors[0:2]),
        fake_response(vectors[2:4]),
        fake_response(vectors[4:5]),
    ]

    result = embedder.embed([f"t{i}" for i in range(5)])
    assert result == [[0.0], [1.0], [2.0], [3.0], [4.0]]
    assert client.embeddings.create.call_count == 3

    call_inputs = [c.kwargs["input"] for c in client.embeddings.create.call_args_list]
    assert [len(ci) for ci in call_inputs] == [2, 2, 1]


# ── Test 2: todas las llamadas usan el modelo ──────────────────────────


def test_uses_model(settings: Settings):
    client = OpenAI(
        base_url=settings.embedding_base_url,
        api_key=settings.llm_api_key or "sin-clave",
        timeout=settings.request_timeout,
        max_retries=settings.request_max_retries,
    )
    client.embeddings.create = MagicMock()  # type: ignore[assignment]
    embedder = OpenAIEmbedder(client, "Qwen3-Embedding-0.6B-4bit-DWQ", batch_size=2)
    embedder._client = client  # noqa: SLF001

    client.embeddings.create.side_effect = [
        fake_response([[0.0], [1.0]]),
    ]

    embedder.embed(["a", "b"])

    for call in client.embeddings.create.call_args_list:
        assert call.kwargs["model"] == "Qwen3-Embedding-0.6B-4bit-DWQ"


# ── Test 3: respuesta desordenada → ordenada ───────────────────────────


def test_out_of_order_response():
    client = OpenAI(
        base_url="http://test",
        api_key="x",
    )
    client.embeddings.create = MagicMock()  # type: ignore[assignment]
    embedder = OpenAIEmbedder(client, "m", batch_size=2)
    embedder._client = client  # noqa: SLF001

    client.embeddings.create.side_effect = [
        fake_response([[2.0], [1.0]], order=[1, 0]),
    ]

    result = embedder.embed(["x", "y"])
    assert result == [[1.0], [2.0]]


# ── Test 4: servidor devuelve menos embeddings → EmbeddingError ───────


def test_incomplete_response():
    client = OpenAI(
        base_url="http://test",
        api_key="x",
    )
    client.embeddings.create = MagicMock()  # type: ignore[assignment]
    embedder = OpenAIEmbedder(client, "m", batch_size=2)
    embedder._client = client  # noqa: SLF001

    client.embeddings.create.return_value = fake_response([[0.0]])

    try:
        embedder.embed(["a", "b"])
        raise AssertionError("EmbeddingError esperado")
    except EmbeddingError as e:
        assert str(e) == "Se esperaban 2 embeddings y llegaron 1"


# ── Test 5: embed([]) → [] sin llamar al servidor ─────────────────────


def test_empty_list():
    client = OpenAI(
        base_url="http://test",
        api_key="x",
    )
    client.embeddings.create = MagicMock()  # type: ignore[assignment]
    embedder = OpenAIEmbedder(client, "m", batch_size=2)
    embedder._client = client  # noqa: SLF001

    result = embedder.embed([])
    assert result == []
    client.embeddings.create.assert_not_called()


# ── Test 6: batch_size <= 0 → ValueError ──────────────────────────────


def test_invalid_batch_size():
    client = OpenAI(
        base_url="http://test",
        api_key="x",
    )
    with pytest.raises(ValueError, match="batch_size must be positive"):
        OpenAIEmbedder(client, "m", 0)


# ── Test 7: APIConnectionError se propaga ─────────────────────────────


def test_connection_error_propagates():
    client = OpenAI(
        base_url="http://test",
        api_key="x",
    )
    client.embeddings.create = MagicMock()  # type: ignore[assignment]
    embedder = OpenAIEmbedder(client, "m", batch_size=2)
    embedder._client = client  # noqa: SLF001

    request = httpx.Request("POST", "http://test")
    client.embeddings.create.side_effect = APIConnectionError(request=request)

    with pytest.raises(APIConnectionError):
        embedder.embed(["a"])


# ── Test 8: make_embedder(Settings()) ─────────────────────────────────


def test_make_embedder(settings: Settings):
    embedder = make_embedder(settings)
    assert embedder.model == "Qwen3-Embedding-0.6B-4bit-DWQ"
    assert embedder._client.max_retries == 3  # noqa: SLF001
    assert embedder._client.timeout == 60.0  # noqa: SLF001
    assert str(embedder._client.base_url) == "http://127.0.0.1:8000/v1/"  # noqa: SLF001
    assert embedder._client.api_key == "sin-clave"  # noqa: SLF001


# ── Test 9: isinstance estático (type-check) ──────────────────────────


def test_embedder_protocol():
    def _check(e: Embedder) -> None:
        pass

    client = OpenAI(
        base_url="http://test",
        api_key="x",
    )
    _check(OpenAIEmbedder(client, "m", batch_size=1))
