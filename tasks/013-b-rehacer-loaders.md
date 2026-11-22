# 013-b · Rehacer loaders de DOCX, MD y TXT según la spec 013
Fase: 1 · Depende de: 013

## Objetivo
La implementación de la 013 no cumple su interfaz ni su comportamiento. Rehazla siguiendo `tasks/013-loaders-docx-md-txt.md` AL PIE DE LA LETRA.

## Qué está mal (no lo repitas)
- `split_markdown_sections` no existe: es parte de la interfaz obligatoria.
- `load_markdown` parte con `#+` (todos los niveles); la spec dice solo `#` y `##`, y `###` NO abre sección.
- No se ignoran los bloques de código ```` ``` ````.
- La línea del encabezado no se incluye en el texto de la sección.
- `read_text_file` usa `utf-8`; la spec dice `encoding="utf-8-sig", errors="replace"`.
- `load_docx` recorre `doc.element.body` a mano; la spec dice `doc.iter_inner_content()`.
- `table_to_text` no hace `strip()` de cada celda.
- `tests/ingest/test_text_loaders.py` tiene 6 tests inventados; la spec pide 14 concretos.

## Archivos
- reescribir: `src/docuchat/ingest/text_loader.py`
- reescribir: `src/docuchat/ingest/docx_loader.py`
- reescribir: `tests/ingest/test_text_loaders.py`

## Comportamiento
1. Lee `tasks/013-loaders-docx-md-txt.md` entera antes de empezar.
2. Las firmas, el algoritmo de `split_markdown_sections` (puntos 5a–5f) y los 14 tests son los de esa spec, sin cambios.
3. Nombra los tests `test_01_...` a `test_14_...` siguiendo el número del punto de la spec.

## Aceptación
- [ ] `uv run pytest -q tests/ingest/test_text_loaders.py` → 14 passed
- [ ] `grep -c "def split_markdown_sections\|def read_text_file\|def load_markdown\|def load_txt" src/docuchat/ingest/text_loader.py` → 4
- [ ] `grep -c "iter_inner_content" src/docuchat/ingest/docx_loader.py` → 1
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
`scanner.py` y `cli.py` (van en 014-b y 015-b).
