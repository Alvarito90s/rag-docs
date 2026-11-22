# Informe 013-b · Rehacer loaders de DOCX, MD y TXT
Estado: COMPLETADA

## Cambios
- `src/docuchat/ingest/text_loader.py`: reescrito siguiendo la spec 013 al pie de la letra
  - `read_text_file` → `encoding="utf-8-sig", errors="replace"` (antes utf-8)
  - `split_markdown_sections` → nueva función implementada con el algoritmo exacto
    (6a-6f): bloque de código, solo `#` y `##`, `###` no abre sección, cuerpo vacío descartado
  - `load_markdown` → usa `split_markdown_sections` en vez de regex propia
- `src/docuchat/ingest/docx_loader.py`: reescrito siguiendo la spec 013
  - `load_docx` → `doc.iter_inner_content()` en vez de `doc.element.body`
  - `table_to_text` → `strip()` en cada celda
- `tests/ingest/test_text_loaders.py`: reescrito con los 14 tests obligatorios de la spec
  (test_01 a test_14), en orden

## Especificidad de la spec cumplida
- `grep -c "def split_markdown_sections\|def read_text_file\|def load_markdown\|def load_txt" src/docuchat/ingest/text_loader.py` → **4** ✅
- `grep -c "iter_inner_content" src/docuchat/ingest/docx_loader.py` → **1** ✅

## Verificación
- `uv run pytest -q tests/ingest/test_text_loaders.py` → **14 passed** ✅
- `uv run pytest -q` → **112 passed**, 5 warnings ✅
- `uv run ruff check .` → sin errores ✅
- `uv run ruff format --check .` → 21 files ✅
- `uv run mypy src` → success, 11 files ✅

## Decisiones que tomé
Ninguna. La spec fija las 4 firmas, el algoritmo de `split_markdown_sections` (puntos 5a–5f)
y los 14 tests exactos.

## Bloqueos y dudas
Ninguno. Todos los tests pasaron a la primera.
