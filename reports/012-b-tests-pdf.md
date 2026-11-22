# Informe 012-b · Loader PDF: los tests de la spec
Estado: COMPLETADA

## Cambios
- `tests/ingest/test_pdf_loader.py`: reescrito con los 10 tests obligatorios de la spec 012,
  en el mismo orden exacto:
  1. `test_contract_pages` — 4 páginas, números [1,2,3,4]
  2. `test_contract_header_footer_removed` — sin "Nubaria ..." ni r'Página \d+ de 4'
  3. `test_manual_header_footer_removed` — 10 páginas, sin cabecera/pie
  4. `test_manual_hyphen_joined` — "descalcificación periódica" presente, "descalici-" ausente
  5. `test_paper_pages` — 2 páginas, dato literal en p1
  6. `test_key_facts_literal` — contrato p2, manual p7, manual p9
  7. `test_no_single_newlines` — sin '\n' suelto en los 3 PDFs
  8. `test_extract_paragraphs_order` — 4 listas, orden sort=True
  9. `test_blank_page_skipped` — PDF temporales con página en blanco
  10. `test_corrupt_pdf_raises` — bytes basura → FileDataError
- Ningún archivo de `src/` modificado

## Verificación
- `uv run pytest -q tests/ingest/test_pdf_loader.py` → 10 passed ✅
- `uv run pytest -q` → 104 passed, 5 warnings ✅
- `git diff --stat src/` → vacío ✅
- `uv run ruff check . && uv run ruff format --check .` → sin errores ✅
- `uv run mypy src` → success, 11 files ✅

## Decisiones que tomé
Ninguna. Los 10 tests se copian de la spec 012-loader-pdf.md con nombres y valores exactos.

## Bloqueos y dudas
Ninguno. Los 10 tests pasan a la primera con el código existente de pdf_loader.py.
