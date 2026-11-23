"""Cliente de chat con streaming contra un servidor compatible con OpenAI (oMLX)."""

from collections.abc import Iterator, Sequence
from typing import Protocol

from openai import OpenAI

from docuchat.config import Settings
from docuchat.env_check import MISSING_API_KEY
from docuchat.generation.prompts import Message


class ChatModel(Protocol):
    """Cualquier cosa que convierta mensajes en texto por trozos."""

    def stream(self, messages: Sequence[Message]) -> Iterator[str]: ...


class OpenAIChatModel:
    """ChatModel contra un servidor compatible con OpenAI (oMLX)."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        *,
        max_tokens: int,
        temperature: float,
        thinking: bool,
    ) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._thinking = thinking

    @property
    def model(self) -> str:
        """Nombre del modelo."""
        return self._model

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        """Trozos de texto de la respuesta; ignora el razonamiento."""
        first = True
        response = self._client.chat.completions.create(
            model=self._model,
            messages=list(messages),
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            stream=True,
            extra_body={"chat_template_kwargs": {"enable_thinking": self._thinking}},
        )
        for chunk in response:
            if not chunk.choices:
                continue
            piece = chunk.choices[0].delta.content
            if piece is None or piece == "":
                continue
            if first:
                piece = piece.lstrip()
                if piece == "":
                    continue
                first = False
            yield piece

    def complete(self, messages: Sequence[Message]) -> str:
        """Respuesta completa, sin espacios en los extremos."""
        return "".join(self.stream(messages)).strip()


def make_chat_model(settings: Settings) -> OpenAIChatModel:
    """Crea el cliente con URL, clave, timeout, reintentos, modelo y parámetros de settings."""
    client = OpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key or MISSING_API_KEY,
        timeout=settings.request_timeout,
        max_retries=settings.request_max_retries,
    )
    return OpenAIChatModel(
        client,
        settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        thinking=settings.llm_thinking,
    )
