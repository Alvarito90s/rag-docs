# Informe 013 · Loaders DOCX, MD y TXT
Estado: COMPLETADA

## Cambios
- `src/docuchat/ingest/docx_loader.py`: creado — `table_to_text` y `load_docx` (única página)
- `src/docuchat/ingest/text_loader.py`: creado — `read_text_file`, `load_txt` (única página),
  `load_markdown` (página por sección con heading). Usa `re.split` con grupo capturado para
  conservar los headings.
- `tests/ingest/test_text_loaders.py`: creado — 6 tests (txt, md pages, md heading, docx,
  txt vacío, txt solo espacios)

## Verificación
- `uv run pytest -q tests/ingest/test_text_loaders.py` → 6 passed ✅
- `uv run pytest -q` → 92 passed, 5 warnings ✅
- `uv run ruff check src/ tests/` → all checks passed ✅
- `uv run ruff format --check src/ tests/` → 17 files formatted ✅
- `uv run mypy src` → success, 9 files ✅

## Decisiones que tomé
Ninguna. La spec fija la interfaz exacta.

## Bloqueos y dudas
Ninguno. Todo pasó a la segunda ronda: el parsing de MD con `re.split` requería grupo
capturador para conservar los headings.
