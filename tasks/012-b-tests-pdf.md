# 012-b · Loader PDF: los tests de la spec
Fase: 1 · Depende de: 012

## Objetivo
El código de `pdf_loader.py` es correcto, pero `tests/ingest/test_pdf_loader.py` no tiene los 10 tests de la spec 012 sino otros 7, más débiles. Sustitúyelos.

## Archivos
- reescribir: `tests/ingest/test_pdf_loader.py`
- crear: `reports/011-limpieza.md` (falta) y `reports/012-b-tests-pdf.md`

## Comportamiento
1. Borra todos los tests actuales del archivo.
2. Escribe EXACTAMENTE los 10 tests de la sección "Tests obligatorios" de `tasks/012-loader-pdf.md`, uno por punto, en el mismo orden, con los mismos valores. Nombres: `test_contract_pages`, `test_contract_header_footer_removed`, `test_manual_header_footer_removed`, `test_manual_hyphen_joined`, `test_paper_pages`, `test_key_facts_literal`, `test_no_single_newlines`, `test_extract_paragraphs_order`, `test_blank_page_skipped`, `test_corrupt_pdf_raises`.
3. NO toques `src/`. Si algún test falla, para y explícalo en "Bloqueos" (el cerebro ya ha comprobado que los 10 pasan con el código actual).

## Aceptación
- [ ] `uv run pytest -q tests/ingest/test_pdf_loader.py` → 10 passed
- [ ] `git diff --stat src/` vacío
- [ ] `uv run ruff check . && uv run ruff format --check .` sin errores
