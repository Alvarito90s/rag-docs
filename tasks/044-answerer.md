# 044 · Answerer: búsqueda + LLM + citas
Fase: 4 · Depende de: 042, 043

## Objetivo
Orquestar una respuesta: recuperar chunks, construir el contexto, pedir la respuesta en streaming al LLM y resolver sus citas. Lo usarán la CLI (045) y la API (Fase 5).

## Archivos
- crear: `src/docuchat/generation/answer.py`
- crear: `tests/generation/test_answer.py`

## Interfaz
```python
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
        self, retriever: Retriever, chat: ChatModel, *, top_k: int, context_max_chars: int
    ) -> None: ...
    def retrieve(self, question: str) -> list[SearchResult]:
        """Busca top_k chunks y devuelve los que caben en el contexto."""
    def stream(self, question: str, context: Sequence[SearchResult]) -> Iterator[str]:
        """Trozos de la respuesta del LLM; NO_ANSWER sin llamar al LLM si no hay contexto."""
    def finalize(self, question: str, text: str, context: Sequence[SearchResult]) -> Answer:
        """Construye el Answer a partir del texto completo."""
    def ask(self, question: str, on_token: Callable[[str], None] | None = None) -> Answer:
        """retrieve + stream (llamando a on_token por trozo) + finalize."""


def build_answerer(
    settings: Settings,
    *,
    retriever: Retriever | None = None,
    chat: ChatModel | None = None,
    top_k: int | None = None,
) -> Answerer:
    """Answerer con build_searcher, make_chat_model y los parámetros de settings."""
```

## Comportamiento
1. `retrieve`: `results = retriever.search(question, top_k)`; `_, used = build_context(results, context_max_chars)`; devuelve `used`.
2. `stream`: si `context` está vacío → emite solo `NO_ANSWER` y termina (sin llamar al LLM). Si no: `texto, _ = build_context(context, context_max_chars)` y `yield from chat.stream(build_messages(question, texto))`.
3. `finalize`: `limpio = text.strip()`; si queda vacío → `limpio = NO_ANSWER`. `no = is_no_answer(limpio)`. Si `no` → `sources = []`, `invalid = []`; si no → `resolve_citations(limpio, context)`. Devuelve `Answer(question, limpio, sources, invalid, no, list(context))`.
4. `ask`: `context = retrieve(question)`; recorre `stream(question, context)` guardando los trozos y llamando a `on_token(trozo)` si no es `None`; devuelve `finalize(question, "".join(trozos), context)`.
5. Errores de búsqueda o del LLM (`OpenAIError`, `EmbeddingError`) se propagan. Sin `try`/`except` en este módulo.
6. `build_answerer`: `retriever or build_searcher(settings)`, `chat or make_chat_model(settings)`, `top_k if top_k is not None else settings.top_k`, `context_max_chars=settings.context_max_chars`.

## Tests obligatorios
`tests/generation/test_answer.py`. NO cambies los valores esperados. Copia el helper `mk` y `R` de `test_prompts.py`.
```python
class FakeRetriever:
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, top_k: int) -> list[SearchResult]:
        self.calls.append((query, top_k))
        return self.results[:top_k]


class FakeChat:
    def __init__(self, pieces: list[str], fail: bool = False) -> None:
        self.pieces = pieces
        self.fail = fail
        self.calls: list[list[Message]] = []

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        self.calls.append(list(messages))
        if self.fail:
            raise APIConnectionError(request=httpx.Request("POST", "http://test"))
        yield from self.pieces
```
`Answerer(retriever, chat, top_k=5, context_max_chars=6000)` salvo que se diga otra cosa.
1. Caso normal, `FakeRetriever(R[:2])`, `FakeChat(["El dato ", "es X [2]."])`, `tokens = []`, `ask("¿Q?", on_token=tokens.append)` → `tokens == ["El dato ", "es X [2]."]`; `answer.text == "El dato es X [2]."`; `sources == [Source(2, "b.md", 2)]`; `invalid_citations == []`; `no_answer is False`; `context == R[:2]`; `chat.calls == [build_messages("¿Q?", "[1] a.pdf, p. 1\nAlfa.\n\n[2] b.md, p. 2\nBeta.")]`.
2. Cita inventada: `FakeChat(["Dato [1][9]."])` con `R[:2]` → `sources == [Source(1, "a.pdf", 1)]`, `invalid_citations == [9]`.
3. El modelo no sabe: `FakeChat([NO_ANSWER])` → `no_answer is True`, `sources == []`, `invalid_citations == []`.
4. Sin resultados: `FakeRetriever([])` → `tokens == [NO_ANSWER]`, `chat.calls == []`, `no_answer is True`, `context == []`.
5. Respuesta vacía: `FakeChat(["  ", "\n"])` con `R[:2]` → `text == NO_ANSWER`, `no_answer is True`.
6. Límite de contexto: `context_max_chars=43` con `FakeRetriever(R)` → `retrieve("x") == R[:2]` y `ask("x").context == R[:2]`.
7. top_k: `Answerer(..., top_k=2, ...)` → `retriever.calls == [("¿Q?", 2)]` tras `ask("¿Q?")`.
8. Error del LLM: `FakeChat([], fail=True)` con `R[:2]` → `pytest.raises(APIConnectionError)` en `ask`.
9. `build_answerer(settings, retriever=FakeRetriever([]), chat=FakeChat([]), top_k=3)` con el fixture `settings` → `isinstance(..., Answerer)` y `ask("hola").no_answer is True`.
10. `build_answerer(settings)` sin argumentos (índice vacío en tmp, sin red) → `isinstance(..., Answerer)`.

## Aceptación
- [ ] `uv run pytest -q tests/generation/test_answer.py` → 10 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "except" src/docuchat/generation/answer.py` → sin resultados

## Fuera de alcance
No toques `prompts.py`, `citations.py`, `llm_client.py` ni `retrieval/`. Nada de CLI (045).
