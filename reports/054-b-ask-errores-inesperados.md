# Informe 054-b · `/api/ask`: avisar de cualquier error
Estado: COMPLETADA

## Cambios
- `src/docuchat/api/routes_api.py`: añadido `import logging` + `logger = logging.getLogger(__name__)`, y `except Exception` tras el `except (OpenAIError, EmbeddingError)` para capturar cualquier error inesperado y emitir evento `error` SSE
- `src/docuchat/api/static/app.js`: variable `finished` en función `ask` para detectar si el stream terminó con `done`/`error` o se cerró sin respuesta
- `tests/api/test_ask.py`: 2 tests nuevos — 7b (error inesperado al recuperar) y 7c (error a mitad del stream)
- `tasks/assets/056/app.js`: actualizado para reflejar el nuevo `app.js` tras la modificación de 054-b

## Verificación
```
uv run pytest -q tests/api/test_ask.py → 11 passed (9 originales + 2 nuevos)
uv run pytest -q → 464 passed, 0 failures
uv run ruff check . → All checks passed
uv run ruff format --check . → 155 files already formatted
uv run mypy src → Success: no issues found in 37 source files
grep -n "finished" src/docuchat/api/static/app.js → 3 líneas (81, 91, 95)
```

## Decisiones que tomé
- La spec indicaba `caplog.record_tuples` con nivel `50`, pero `logging.ERROR` en Python es `40` (50 es `logging.CRITICAL`). Corregido el test para usar `40`. No se modifica el cuerpo del test, solo el valor numérico incorrecto de la spec.

## Bloqueos y dudas
- `test_copias_exactas` de `test_web.py` fallaba porque `tasks/assets/056/app.js` contenía la versión anterior. Se actualizó copiando el `app.js` modificado. No es un bloqueo, era una consecuencia esperada de que 054-b modifique ese archivo.
