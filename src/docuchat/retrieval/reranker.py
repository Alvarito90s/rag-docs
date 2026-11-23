"""Cliente HTTP del reranker (oMLX /v1/rerank)."""

from collections.abc import Sequence
from typing import Protocol

import httpx

from docuchat.config import Settings
from docuchat.env_check import MISSING_API_KEY


class RerankError(RuntimeError):
    """Fallo al reordenar: conexión, respuesta HTTP de error o respuesta mal formada."""


class Reranker(Protocol):
    """Cualquier cosa que puntúe textos frente a una pregunta."""

    def rerank(self, query: str, texts: Sequence[str]) -> list[float]: ...


class HttpReranker:
    """Reranker contra POST {base_url}/rerank (oMLX)."""

    def __init__(
        self,
        client: httpx.Client,
        model: str,
        *,
        instruction: str,
        max_retries: int,
    ) -> None:
        self._client = client
        self._model = model
        self._instruction = instruction
        self._max_retries = max_retries

    @property
    def model(self) -> str:
        """Id del modelo de rerank."""
        return self._model

    def rerank(self, query: str, texts: Sequence[str]) -> list[float]:
        """Una puntuación por texto, en el orden de entrada; RerankError si algo falla."""
        if not texts:
            return []

        body: dict[str, object] = {
            "model": self._model,
            "query": query,
            "documents": list(texts),
            "return_documents": False,
        }
        if self._instruction:
            body["instruction"] = self._instruction

        last_exc: httpx.TransportError | None = None
        success = False
        for _ in range(self._max_retries + 1):
            try:
                response = self._client.post("rerank", json=body)
                success = True
                break
            except httpx.TransportError as e:
                last_exc = e
                continue

        if not success:
            raise RerankError(
                f"Error de conexión con el reranker: {type(last_exc).__name__}: {last_exc}"
            ) from last_exc

        if response.status_code >= 400:
            raise RerankError(
                f"El reranker respondió {response.status_code}: {response.text[:200]}"
            )

        try:
            data = response.json()
        except ValueError:
            raise RerankError("La respuesta del reranker no es JSON") from None

        if not isinstance(data, dict):
            raise RerankError("La respuesta del reranker no tiene 'results'")

        results = data.get("results")
        if not isinstance(results, list):
            raise RerankError("La respuesta del reranker no tiene 'results'")

        n = len(texts)
        scores: dict[int, float] = {}

        for item in results:
            if not isinstance(item, dict):
                raise RerankError(f"Resultado de rerank inválido: {item!r}")
            index = item.get("index")
            if not isinstance(index, int) or isinstance(index, bool):
                raise RerankError(f"Resultado de rerank inválido: {item!r}")
            if index < 0 or index >= n:
                raise RerankError(f"Resultado de rerank inválido: {item!r}")

            score = item.get("relevance_score")
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                raise RerankError(f"Resultado de rerank inválido: {item!r}")

            if index in scores:
                raise RerankError(f"Índice repetido en el rerank: {index}")

            scores[index] = float(score)

        if len(scores) != n:
            raise RerankError(f"Se esperaban {n} puntuaciones y llegaron {len(scores)}")

        return [scores[i] for i in range(n)]


def make_reranker(settings: Settings, transport: httpx.BaseTransport | None = None) -> HttpReranker:
    """HttpReranker con base_url, clave, timeout, reintentos, modelo e instrucción de settings."""
    client = httpx.Client(
        base_url=settings.rerank_base_url,
        timeout=settings.request_timeout,
        headers={"Authorization": f"Bearer {settings.llm_api_key or MISSING_API_KEY}"},
        transport=transport,
    )
    return HttpReranker(
        client,
        settings.rerank_model,
        instruction=settings.rerank_instruction,
        max_retries=settings.request_max_retries,
    )
