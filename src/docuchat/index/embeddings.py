"""Cliente de embeddings por lotes contra oMLX (API compatible con OpenAI)."""

from collections.abc import Sequence
from typing import Protocol

from openai import OpenAI

from docuchat.config import Settings
from docuchat.env_check import MISSING_API_KEY


class EmbeddingError(RuntimeError):
    """Respuesta de embeddings incoherente."""


class Embedder(Protocol):
    """Cualquier cosa que convierta textos en vectores."""

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OpenAIEmbedder:
    """Embedder contra un servidor compatible con OpenAI (oMLX)."""

    def __init__(self, client: OpenAI, model: str, batch_size: int) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self._client = client
        self._model = model
        self._batch_size = batch_size

    @property
    def model(self) -> str:
        """Nombre del modelo de embeddings."""
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Calcula embeddings para *texts* en lotes; propaga OpenAIError."""
        if not texts:
            return []

        result: list[list[float]] = []
        texts_list = list(texts)

        for i in range(0, len(texts_list), self._batch_size):
            batch = texts_list[i : i + self._batch_size]
            resp = self._client.embeddings.create(
                model=self._model,
                input=list(batch),
            )

            # El servidor puede devolverlos desordenados; ordena por index.
            items = sorted(resp.data, key=lambda item: item.index)

            if len(items) != len(batch):
                raise EmbeddingError(
                    f"Se esperaban {len(batch)} embeddings y llegaron {len(items)}"
                )

            result.extend(list(item.embedding) for item in items)

        return result


def make_embedder(settings: Settings) -> OpenAIEmbedder:
    """Crea el embedder con URL, clave, timeout, reintentos, modelo y lote."""
    client = OpenAI(
        base_url=settings.embedding_base_url,
        api_key=settings.llm_api_key or MISSING_API_KEY,
        timeout=settings.request_timeout,
        max_retries=settings.request_max_retries,
    )
    return OpenAIEmbedder(client, settings.embedding_model, settings.embedding_batch_size)
