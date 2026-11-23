# Informe 112 · Contexto en el indexador y en la evaluación
Estado: COMPLETADA

## Cambios
- `src/docuchat/index/indexer.py`: `IndexStats` añade campo `contexts_generated: int = 0`; `Indexer.__init__` añade parámetro `contextualizer: Contextualizer | None = None`; `index_folder` contextualiza chunks (paso c, dentro del try); `build_indexer` crea contextualizer condicionalmente; `reset_index` no borra la caché.
- `src/docuchat/evaluation/variants.py`: dos entradas nuevas en `VARIANTS`: `"contextual"` y `"contextual_sin_rerank"`.
- `tests/conftest.py`: fixture `autouse` `_sin_contextualizador_real` que parchea `make_contextualizer` para devolver `None` (regla 3: ningún test llama al LLM real).
- `tests/index/test_indexer_contextual.py`: 10 tests (rellena_contexto, embedder_y_fts_ven_el_contexto, stats, sin_contextualizador, error_de_contexto_va_a_errors, migracion_conserva_contexto, build_indexer_contextual, conftest_sin_contextualizador_real, reset_no_borra_la_cache, variantes).

## Verificación
`uv run pytest -q` → 675 passing (665 anteriores + 10 nuevos). `uv run ruff check .` → sin errores. `uv run ruff format --check .` → todo formateado. `uv run mypy src` → sin errores.

## Decisiones que tomé
Ninguna: la spec definía la interfaz exacta, los tests y los valores esperados. La línea de contextualización va dentro del try del paso c para que las excepciones no-OpenAIError se gestionen como errores de archivo, exactamente como `load_document`/`chunk_document`.

## Bloqueos y dudas
Sin bloqueos.
