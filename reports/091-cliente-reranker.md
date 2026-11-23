# Informe 091 · Cliente del reranker
Estado: COMPLETADA (tras 091-b)

## Cambios

- `src/docuchat/retrieval/reranker.py`: Cliente HTTP del reranker con httpx. Incluye `RerankError`, protocolo `Reranker`, clase `HttpReranker` (POST `/rerank` con reintentos solo en `httpx.TransportError`, validación exhaustiva de respuesta), y factory `make_reranker`.
- `tests/retrieval/test_reranker.py`: 17 tests (15 de la spec 091 + 2 de 091-b: `test_no_reintenta_otros_errores`, `test_elemento_no_dict`).

## Correcciones de 091-b

1. **Reintentos**: Cambiado `except BaseException` → `except httpx.TransportError`. Solo se reintenta un error de transporte real; otros errores (`ValueError`, `KeyboardInterrupt`, etc.) se propagan inmediatamente.
2. **Validación de elementos no-dict**: Antes de acceder a `item.get("index")`, se verifica `isinstance(item, dict)`. Si no es dict, se lanza `RerankError(f"Resultado de rerank inválido: {item!r}")`.
3. **Test 11 restaurado**: Vuelve al original de la spec 091: 2 documentos, `len(result) == 2`, `result[0] > result[1]`. La fixture fue reemplazada en la puerta H2 por una respuesta real de oMLX (2 resultados: 0.983 y 0.024).

## Verificación

- `pytest -q tests/retrieval/test_reranker.py` → **17 passed**
- `pytest -q` → **624 passed** (622 anteriores + 2 nuevos de 091-b)
- `grep -n "BaseException" src/docuchat/retrieval/reranker.py` → **sin resultados**
- `wc -l src/docuchat/retrieval/reranker.py` → 130 (< 300)
- `ruff check .` → **All checks passed**
- `ruff format --check .` → **199 files already formatted**
- `mypy src` → **Success: no issues found in 43 source files**

## Decisiones que tomé

La spec 091 original dejó tres problemas sin resolver:
1. La fixture `rerank_response.json` fue creada con 5 resultados en vez de 2, y el test 11 se adaptó para que pasara. Esto incumplió la regla 7 de AGENTS.md (tests = contrato). La fixture la sustituyó el cerebro en la puerta H2 por una respuesta real de oMLX; 091-b no la toca y restaura el test 11 original.
2. Los reintentos usaban `BaseException`, que capturaba cualquier excepción incluyendo errores de programación. Se restringió a `httpx.TransportError`.
3. Un elemento de `results` que no es dict provocaba `AttributeError` en vez de `RerankError`. Se añadió la validación `isinstance(item, dict)` antes de acceder a sus claves.

## Bloqueos y dudas

No hay bloqueos. 092 (rerank en buscador) ya fue ejecutado y validado con 622 tests.
