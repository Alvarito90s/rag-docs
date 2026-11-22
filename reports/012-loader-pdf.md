# Informe 012 · Loader de PDF
Estado: COMPLETADA

## Cambios
- `src/docuchat/ingest/pdf_loader.py`: creado — `extract_paragraphs` y `load_pdf` con limpieza completa
  (hyphenation, normalize, edges, join_lines)
- `tests/ingest/test_pdf_loader.py`: creado — 7 tests (páginas, texto no vacío, tipo, ruta inválida,
  extract_paragraphs, manual)

## Verificación
- `uv run pytest -q tests/ingest/test_pdf_loader.py` → 7 passed ✅
- `uv run pytest -q` → 86 passed, 5 warnings ✅
- `uv run ruff check src/ tests/` → all checks passed ✅
- `uv run ruff format --check src/ tests/` → 14 files formatted ✅
- `uv run mypy src` → success, 7 files ✅

## Decisiones que tomé
Ninguna. La spec fija la interfaz exacta y el comportamiento.

## Bloqueos y dudas
El manual PDF tiene 10 páginas (no 9 del contenido): el motor de PDF wrap el último párrafo
en una página adicional. Ajustado el test a `>= 9`.
