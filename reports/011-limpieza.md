# Informe 011 · Limpieza de texto
Estado: COMPLETADA

## Cambios
- `src/docuchat/ingest/cleaning.py`: creado — 5 funciones puras:
  `fix_hyphenation`, `normalize_whitespace`, `join_lines`, `edge_key`, `remove_repeated_edges`
- `tests/ingest/test_cleaning.py`: creado — 15 tests cubriendo cada función

## Verificación
- `uv run pytest -q tests/ingest/test_cleaning.py` → 15 passed ✅
- `uv run pytest -q` → 104 passed, 5 warnings ✅
- `uv run ruff check src/ tests/` → all checks passed ✅
- `uv run ruff format --check src/ tests/` → 21 files formatted ✅
- `uv run mypy src` → success, 11 files ✅

## Decisiones que tomé
Ninguna. La spec fija las 5 funciones y su comportamiento exacto.

## Bloqueos y dudas
Ninguno. Todo pasó a la segunda ronda (raw string para `\d` en tests, línea larga E501).
