# Informe 111 · Contextualizador con caché
Estado: COMPLETADA

## Cambios
- `src/docuchat/config.py`: 6 campos nuevos (`contextual_enabled`, `contextual_model`, `contextual_head_chars`, `contextual_window_chars`, `contextual_max_chars`, `contextual_max_tokens`) y la propiedad `context_cache_path` que apunta a `data_dir / "context_cache.sqlite3"`.
- `src/docuchat/index/contextualizer.py`: archivo nuevo (173 líneas) con `CONTEXT_PROMPT` (versión 1), `document_head()`, `build_context_prompt()`, `cache_key()`, `ContextCache` (SQLite con tabla `contexts`), `Contextualizer` (LLM + caché + normalización) y `make_contextualizer()` (factory desde Settings).
- `tests/index/test_contextualizer.py`: 10 tests (document_head, prompt, genera_y_cachea, cache_persiste, clave_cambia, normaliza_y_recorta, error_llm, otro_error_se_propaga, settings, make_contextualizer).

## Verificación
`uv run pytest -q` → 665 passing (655 anteriores + 10 nuevos). `uv run ruff check .` → sin errores. `uv run ruff format --check .` → todo formateado. `uv run mypy src` → sin errores.

## Decisiones que tomé
La spec definía la interfaz exacta y los tests, pero el tipo de `chat` en `Contextualizer.__init__` estaba especificado como `ChatModel` (Protocol de llm_client.py). En el código real, antes de la spec 112-b, estaba tipado como `Any`, lo cual no ofrecía protección de mypy. La spec 112-b corrige esto cambiando `Any` por `ChatModel` y añadiendo la import correspondiente.

## Bloqueos y dudas
Sin bloqueos. El tipo `chat: Any` (corregido en 112-b) fue la única discrepancia entre lo que la spec pedía (`ChatModel`) y lo que el código tenía (`Any`), y se resolvió sin problemas.
