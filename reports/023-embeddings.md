# Informe 023 · Cliente de embeddings por lotes
Estado: COMPLETADA

## Cambio
- `src/docuchat/index/embeddings.py`: nuevo módulo con EmbeddingError, Embedder
  (Protocol), OpenAIEmbedder y make_embedder
- `tests/index/test_embeddings.py`: 9 tests obligatorios

## Implementación
- `OpenAIEmbedder.__init__`: valida batch_size > 0, guarda client/model/batch_size
- `embed`: divide en lotes, llama a client.embeddings.create, ordena por index,
  verifica count (EmbeddingError si mismatch), propaga OpenAIError
- `make_embedder`: crea OpenAI con embedding_base_url, api_key or MISSING_API_KEY,
  timeout, max_retries; devuelve OpenAIEmbedder con settings.embedding_model
  y embedding_batch_size

## Verificación
- `uv run pytest -q tests/index/test_embeddings.py` → **9 passed** ✅
- `uv run pytest -q` → **194 passed** ✅
- `uv run ruff check .` → sin errores ✅
- `uv run ruff format --check .` → 68 files ✅
- `uv run mypy src` → success, 17 files ✅

## Decisiones que tomé
Ninguna. La spec fija la interfaz exacta, el comportamiento y los 9 tests.

## Bloqueos y dudas
El subagent se quedó sin RAM al finalizar. Corregí 2 errores de ruff en los tests
(orden de imports + strict= en zip) para que pasen las verificaciones finales.
