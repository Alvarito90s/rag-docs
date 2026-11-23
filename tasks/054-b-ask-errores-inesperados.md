# 054-b · `/api/ask`: avisar de cualquier error
Fase: 5 · Depende de: 054, 051-b

## Objetivo
Hoy `/api/ask` solo convierte en evento `error` los `OpenAIError` y `EmbeddingError`. Cualquier otra excepción corta el stream sin `done` ni `error`. Por ejemplo, el `InvalidArgumentError` de Chroma con un índice de otra dimensión. Entonces el chat se queda en "Pensando…" sin decir nada (comprobado por el cerebro), y el error solo aparece en la consola del servidor.

## Archivos
- modificar: `src/docuchat/api/routes_api.py` (solo `ask` y un `logger` de módulo)
- modificar: `src/docuchat/api/static/app.js` (solo la función `ask`)
- modificar: `tests/api/test_ask.py` (solo AÑADIR 2 tests)

## Comportamiento
1. **`routes_api.py`**:
   - Añade `import logging` y, a nivel de módulo, `logger = logging.getLogger(__name__)`.
   - En `ask`, tras el `except (OpenAIError, EmbeddingError)` actual (que no cambia), añade:
     ```python
     except Exception as e:  # noqa: BLE001 — el stream debe terminar siempre con done o error
         logger.exception("Fallo inesperado en /api/ask")
         yield ServerSentEvent(
             event="error",
             data={"message": f"{type(e).__name__}: {e}"},
         )
     ```
   - Si ruff no conoce `BLE001` con las reglas activas, quita solo el `noqa` y deja el comentario.
2. **`app.js`**, en la función `ask`:
   - Antes del `while (true)`, declara `let finished = false;`.
   - Dentro del bucle interno, tras `if (parsed) handleEvent(parsed[0], parsed[1]);`, añade `if (parsed && (parsed[0] === "done" || parsed[0] === "error")) finished = true;`.
   - Tras el `while (true)`, añade `if (!finished) showError("la conexión se cerró sin respuesta");`.
   - Nada más cambia.

## Tests obligatorios
En `tests/api/test_ask.py`, AÑADE estos 2 tests. NO cambies los existentes. Usa los fixtures `ingested`, `services`, `monkeypatch` y `caplog`.

7b. **Error inesperado al recuperar.**
- Prepara: `monkeypatch.setattr(services.answerer, "retrieve", boom)`, con `boom(question)` lanzando `RuntimeError("boom")`.
- Ejecuta: `ingested.post("/api/ask", json={"question": "test"})`.
- Esperado:
  - `status_code == 200`;
  - `parse_sse(resp.text) == [("error", {"message": "RuntimeError: boom"})]`;
  - hay un registro de `caplog` con `levelname == "ERROR"` y `name == "docuchat.api.routes_api"`.

7c. **Error a mitad del stream.**
- Prepara: `monkeypatch.setattr(services.answerer, "stream", cortado)`, con `cortado(question, context)` un generador que hace `yield "Hola"` y luego `raise RuntimeError("corte")`.
- Esperado: `parse_sse(resp.text) == [("token", {"text": "Hola"}), ("error", {"message": "RuntimeError: corte"})]`.

## Aceptación
- [ ] `uv run pytest -q tests/api/test_ask.py` pasa (2 tests más)
- [ ] `uv run pytest -q` → 464 passed
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "finished" src/docuchat/api/static/app.js` → 3 líneas

## Fuera de alcance
No cambies los mensajes de los errores existentes ni el resto de endpoints.
