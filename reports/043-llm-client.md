# Informe 043 · Cliente LLM con streaming
Estado: COMPLETADA

## Cambios
- `src/docuchat/generation/llm_client.py`: Creación con `ChatModel` protocol, `OpenAIChatModel` (stream, complete, model property) y `make_chat_model` (factory con URL, clave, timeout, reintentos). Sin capturas de errores, sin referencia a reasoning.
- `tests/generation/test_llm_client.py`: 8 tests con `MagicMock` + `SimpleNamespace`: filtro de trozos, call args, `thinking=True`, `complete()`, solo espacios, propagación de `APIConnectionError`, perezosidad y `make_chat_model`.
- `docs/STATE.md`: Actualizado a spec 043, nuevo módulo `llm_client`, conteo 299 tests.

## Verificación
```
uv run pytest -q tests/generation/test_llm_client.py → 8 passed
uv run pytest -q → 299 passed, 5 warnings
uv run ruff check . → All checks passed!
uv run ruff format --check . → 97 files already formatted
uv run mypy src → Success: no issues found in 25 source files
grep -n "reasoning\|except" src/docuchat/generation/llm_client.py → sin resultados
```

## Decisiones que tomé
Ninguna. La spec era explícita en todos los detalles de implementación.

## Bloqueos y dudas
Ninguno. Los 8 tests pasaron en el primer intento tras corregir la lógica de `lstrip` (el flag `first` se movió al interior del bloque `if` para no marcarse como consumido si el chunk se descarta vacío).
