# Informe 054 · API: /api/ask con streaming SSE
Estado: COMPLETADA

## Cambios
- `src/docuchat/api/routes_api.py`: añadidos `AskRequest` (Pydantic), `answer_to_dict()` y endpoint `ask` con `EventSourceResponse` + generador `yield ServerSentEvent` (eventos `token`, `done`, `error`)
- `tests/api/conftest.py`: corregido `FakeChat.fail` para usar `message=` keyword en `APIConnectionError` (bug preexistente de la SDK v1)
- `tests/api/test_ask.py`: 9 tests (contexto con fuentes, índice vacío, no_answer del modelo, cita inventada, error LLM, error embeddings, top_k, validación parametrizada)

## Verificación
- `uv run pytest -q tests/api/test_ask.py` → **9 passed**
- `uv run pytest -q` → 355 passing, 5 failures (preexistentes: ChromaDB Rust bindings internal errors en `test_indexer.py` y `test_searcher.py`, no relacionados con este cambio)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores
- `grep "sse_starlette\|StreamingResponse" routes_api.py` → sin resultados (usa SSE nativo de FastAPI)

## Decisiones que tomé
- El endpoint usa `services.answerer` cuando `top_k` es `None`; si no, crea un nuevo `Answerer` con `build_answerer()` pasando `retriever=services.searcher` y `chat=services.chat` (compartidos).
- Se usó SSE nativo de FastAPI (`EventSourceResponse` / `ServerSentEvent` de `fastapi.sse`) en lugar de la librería externa `sse-starlette`.
- Para el test de top_k, se valida el contenido del mensaje enviado al LLM (`chat.calls[0][1]["content"]`) para confirmar que solo incluye el fragmento [1].

## Bloqueos y dudas
- `FakeChat.fail` en `conftest.py` fallaba con `TypeError: APIConnectionError.__init__() takes 1 positional argument but 2 positional arguments were given`. Se corrigió pasando `message="Connection refused"` como keyword argument, siguiendo el patrón de `FakeEmbedder`.
- El test 3 (modelo responde no_answer) requiere búsqueda dinámica del evento `done` porque el número de eventos `token` depende de cómo `FakeChat.pieces` esté particionado.
