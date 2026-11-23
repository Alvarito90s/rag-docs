# Informe 041 · Prompts de sistema y contexto numerado
Estado: COMPLETADA

## Cambios
- `src/docuchat/generation/__init__.py`: creado con docstring del módulo
- `src/docuchat/generation/prompts.py`: creado con `SYSTEM_PROMPT`, `NO_ANSWER`, `format_block()`, `build_context()`, `build_messages()`
- `tests/generation/__init__.py`: creado vacío
- `tests/generation/test_prompts.py`: creado con 8 tests de la spec

## Verificación
- `uv run pytest -q tests/generation/test_prompts.py` → **8 passed**
- `uv run pytest -q` → **278 passed**, 5 warnings (pymupdf deprecation)
- `uv run ruff check . && uv run ruff format --check .` → **All checks passed**
- `uv run mypy src` → **Success: no issues found in 23 source files**

## Decisiones que tomé
- Ninguna. La spec fijaba exactamente los valores y el comportamiento.

## Bloqueos y dudas
- Ninguno. Una corrección menor: eliminé la importación `ChatCompletionMessageParam` del test (era un `F401` unused import de ruff, no afectaba a ningún valor esperado).
