# 054 · API: /api/ask con streaming SSE
Fase: 5 · Depende de: 053

## Objetivo
`POST /api/ask` responde en streaming con Server-Sent Events: un evento `token` por trozo y un `done` final con las fuentes (o `error`).

## Archivos
- modificar: `src/docuchat/api/routes_api.py` (solo AÑADIR modelo y endpoint)
- crear: `tests/api/test_ask.py`

## Interfaz
```python
from collections.abc import Iterator

from fastapi.sse import EventSourceResponse, ServerSentEvent

from docuchat.generation.answer import Answer, build_answerer


class AskRequest(BaseModel):
    """Cuerpo de POST /api/ask."""

    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, gt=0)


def answer_to_dict(answer: Answer) -> dict[str, object]:
    """Datos del evento 'done'."""


@router.post("/ask", response_class=EventSourceResponse)
def ask(body: AskRequest, services: ServicesDep) -> Iterator[ServerSentEvent]: ...
```

## Comportamiento
1. Answerer: `services.answerer` si `body.top_k` es `None`; si no, `build_answerer(settings, retriever=services.searcher, chat=services.chat, top_k=body.top_k)`.
2. Generador (`def` con `yield`; FastAPI lo ejecuta en un hilo):
   a. Dentro de `try`: `context = answerer.retrieve(question)`; por cada trozo de `answerer.stream(question, context)`, lo guarda y emite `ServerSentEvent(event="token", data={"text": trozo})`; al final `answer = answerer.finalize(question, "".join(trozos), context)`.
   b. `except (OpenAIError, EmbeddingError) as e` → emite `ServerSentEvent(event="error", data={"message": f"{type(e).__name__}: {e}"})` y termina. El status HTTP ya es 200 (las cabeceras se enviaron); el cliente mira el evento.
   c. Si no hubo error, emite `ServerSentEvent(event="done", data=answer_to_dict(answer))`.
3. `answer_to_dict` → `{"text", "no_answer", "sources": [{"number", "source", "page", "url": file_url(source, page)}], "invalid_citations"}`.
4. Validación (pregunta vacía, top_k ≤ 0) → 422 antes de empezar el stream.

## Tests obligatorios
`tests/api/test_ask.py`, con los fixtures de `conftest.py`. NO cambies los valores esperados. Helper para leer el stream:
```python
def parse_sse(body: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in body.strip().split("\n\n"):
        event, data = "message", ""
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[len("event: "):]
            elif line.startswith("data: "):
                data += line[len("data: "):]
        events.append((event, json.loads(data)))
    return events
```
Petición: `client.post("/api/ask", json={...})` y `parse_sse(response.text)`.
1. Con `ingested` y `chat.pieces = ["Dato ", "[1]."]` → status 200, `content-type` empieza por `"text/event-stream"`; eventos `["token", "token", "done"]`; datos de los tokens `{"text": "Dato "}`, `{"text": "[1]."}`; en `done`: `text == "Dato [1]."`, `no_answer is False`, `invalid_citations == []`, una fuente con `number == 1` y `url == f"/files/{source}#page={page}"` (de esa misma fuente).
2. Índice vacío → eventos `["token", "done"]`; token `{"text": NO_ANSWER}`; `done["no_answer"] is True`, `done["sources"] == []`; `chat.calls == []`.
3. El modelo no sabe: `chat.pieces = [NO_ANSWER]` con `ingested` → `done["no_answer"] is True` y `sources == []`.
4. Cita inventada: `chat.pieces = ["Dato [1][9]."]` → `done["invalid_citations"] == [9]`.
5. Error del LLM: `chat.fail = True` con `ingested` → status 200; único evento `("error", ...)` con `message.startswith("APIConnectionError")`.
6. Error de embeddings: `embedder.fail_on_query = True` con `ingested` → evento `error`.
7. `top_k`: `{"question": "hola", "top_k": 1}` con `ingested` → el mensaje de usuario (`chat.calls[0][1]["content"]`) contiene `"[1] "` y no `"[2] "`.
8. Validación (parametrizado, 2 casos): `{"question": ""}` y `{"question": "x", "top_k": 0}` → 422.

## Referencia de librerías
FastAPI 0.165, SSE nativo (comprobado; funciona con POST y con generadores síncronos):
```python
from collections.abc import Iterator
from fastapi.sse import EventSourceResponse, ServerSentEvent


@router.post("/ask", response_class=EventSourceResponse)
def ask(body: AskRequest) -> Iterator[ServerSentEvent]:
    yield ServerSentEvent(event="token", data={"text": "Hola"})
    yield ServerSentEvent(event="done", data={"sources": []})
# En el cable: 'event: token\ndata: {"text": "Hola"}\n\n' ...  (data siempre se serializa a JSON)
```

## Aceptación
- [ ] `uv run pytest -q tests/api/test_ask.py` → 9 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "sse_starlette\|StreamingResponse" src/docuchat/api/routes_api.py` → sin resultados

## Fuera de alcance
La interfaz web que consume este stream (056). No toques `generation/`.
