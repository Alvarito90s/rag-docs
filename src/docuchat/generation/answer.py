"""Answerer: búsqueda + contexto + streaming LLM + resolución de citas."""

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Protocol

from docuchat.config import Settings
from docuchat.generation.citations import Source, is_no_answer, resolve_citations
from docuchat.generation.llm_client import ChatModel, make_chat_model
from docuchat.generation.prompts import NO_ANSWER, build_context, build_messages
from docuchat.models import SearchResult
from docuchat.retrieval.searcher import build_searcher


class Retriever(Protocol):
    """Cualquier cosa que busque chunks (Searcher cumple este protocolo)."""

    def search(self, query: str, top_k: int) -> list[SearchResult]: ...


@dataclass(frozen=True)
class Answer:
    """Respuesta final con sus fuentes."""

    question: str
    text: str
    sources: list[Source]
    invalid_citations: list[int]
    no_answer: bool
    context: list[SearchResult]


class Answerer:
    """Responde preguntas con RAG: retrieve → stream → finalize."""

    def __init__(
        self,
        retriever: Retriever,
        chat: ChatModel,
        *,
        top_k: int,
        context_max_chars: int,
    ) -> None:
        self._retriever = retriever
        self._chat = chat
        self._top_k = top_k
        self._context_max_chars = context_max_chars

    def retrieve(self, question: str) -> list[SearchResult]:
        """Busca top_k chunks y devuelve los que caben en el contexto."""
        results = self._retriever.search(question, self._top_k)
        _, used = build_context(results, self._context_max_chars)
        return used

    def stream(self, question: str, context: Sequence[SearchResult]) -> Iterator[str]:
        """Trozos de la respuesta del LLM; NO_ANSWER sin llamar al LLM si no hay contexto."""
        if not context:
            yield NO_ANSWER
            return
        texto, _ = build_context(context, self._context_max_chars)
        yield from self._chat.stream(build_messages(question, texto))

    def finalize(
        self,
        question: str,
        text: str,
        context: Sequence[SearchResult],
    ) -> Answer:
        """Construye el Answer a partir del texto completo."""
        limpio = text.strip()
        if not limpio:
            limpio = NO_ANSWER
        no = is_no_answer(limpio)
        if no:
            sources: list[Source] = []
            invalid: list[int] = []
        else:
            sources, invalid = resolve_citations(limpio, context)
        return Answer(
            question=question,
            text=limpio,
            sources=sources,
            invalid_citations=invalid,
            no_answer=no,
            context=list(context),
        )

    def ask(
        self,
        question: str,
        on_token: Callable[[str], None] | None = None,
    ) -> Answer:
        """retrieve + stream (llamando a on_token por trozo) + finalize."""
        context = self.retrieve(question)
        pieces: list[str] = []
        for piece in self.stream(question, context):
            pieces.append(piece)
            if on_token is not None:
                on_token(piece)
        return self.finalize(question, "".join(pieces), context)


def build_answerer(
    settings: Settings,
    *,
    retriever: Retriever | None = None,
    chat: ChatModel | None = None,
    top_k: int | None = None,
) -> Answerer:
    """Answerer con build_searcher, make_chat_model y los parámetros de settings."""
    return Answerer(
        retriever or build_searcher(settings),
        chat or make_chat_model(settings),
        top_k=top_k if top_k is not None else settings.top_k,
        context_max_chars=settings.context_max_chars,
    )
