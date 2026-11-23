# Informe 021 · Chunker recursivo

Estado: COMPLETADA

## Cambios

- `src/docuchat/index/__init__.py`: creado, docstring del módulo index.
- `src/docuchat/index/chunker.py`: creado, 4 funciones (`split_units`, `join_units`, `split_text`, `chunk_document`) + constante `SEPARATORS`.
- `tests/index/test_chunker.py`: creado, 17 tests (cubren las 16 propiedades de la spec + 1 para confirmar `SEPARATORS`).

## Verificación

- `uv run pytest -q tests/index/test_chunker.py` → 17 passed
- `uv run pytest -q` → 152 passed (135 anteriores + 17 nuevos)
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 54 files already formatted
- `uv run mypy src` → Success: no issues found in 13 source files

## Decisiones que tomé

- No hay decisiones ambiguas: la spec era clara en algoritmo, firma y valores esperados. Seguí exactamente lo descrito.

## Bloqueos y dudas

- Ninguno. Implementación directa según spec.
