# 013 · Loaders de DOCX, Markdown y TXT
Fase: 1 · Depende de: 010, 011

## Objetivo
Cargar DOCX y TXT como una sola página, y Markdown como una página por sección (encabezados `#` y `##`).

## Archivos
- crear: `src/docuchat/ingest/docx_loader.py`
- crear: `src/docuchat/ingest/text_loader.py`
- crear: `tests/ingest/test_text_loaders.py`

## Interfaz
`docx_loader.py`:
```python
from pathlib import Path

from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph

from docuchat.ingest.cleaning import normalize_whitespace
from docuchat.models import Page


def table_to_text(table: Table) -> str:
    """Una línea por fila con las celdas separadas por ' | '."""


def load_docx(path: Path) -> list[Page]:
    """Carga un DOCX como una única página (párrafos y tablas en orden)."""
```
`text_loader.py`:
```python
from pathlib import Path

from docuchat.ingest.cleaning import normalize_whitespace
from docuchat.models import Page


def read_text_file(path: Path) -> str:
    """Lee un archivo de texto en UTF-8 (con o sin BOM), sustituyendo bytes inválidos."""


def load_txt(path: Path) -> list[Page]:
    """Carga un TXT como una única página."""


def split_markdown_sections(text: str) -> list[tuple[str | None, str]]:
    """Parte un Markdown en (encabezado, texto de la sección) por encabezados de nivel 1 y 2."""


def load_markdown(path: Path) -> list[Page]:
    """Carga un Markdown: una Page por sección no vacía, con su encabezado en `heading`."""
```

## Comportamiento
1. `table_to_text`: por cada fila, `" | ".join(celda.text.strip() for celda in fila.cells)`; filas unidas con `"\n"`.
2. `load_docx`: recorre `doc.iter_inner_content()` (orden real del documento). `Paragraph` → su `text.strip()` si no está vacío; `Table` → `table_to_text`. Une las partes con `"\n\n"`, aplica `normalize_whitespace`. Devuelve `[Page(number=1, text=...)]`, o `[]` si queda vacío.
3. `read_text_file`: `path.read_text(encoding="utf-8-sig", errors="replace")`.
4. `load_txt`: `normalize_whitespace(read_text_file(path))` → `[Page(number=1, text=...)]` o `[]`.
5. `split_markdown_sections`:
   a. Recorre las líneas (`text.split("\n")`). Una línea cuyo `lstrip()` empieza por ` ``` ` alterna el estado "dentro de bloque de código".
   b. Fuera de código, una línea que case con `re.match(r"^(#{1,2}) +(.+?)\s*#*\s*$", linea)` abre sección nueva con encabezado `m.group(2).strip()`. La línea del encabezado forma parte del texto de su sección.
   c. Las líneas anteriores al primer encabezado forman una sección con encabezado `None`.
   d. `###` y niveles más profundos NO abren sección.
   e. Se descartan las secciones cuyo cuerpo (las líneas sin contar la del encabezado) esté vacío tras `strip()`.
   f. El texto de cada sección se devuelve con `normalize_whitespace`.
6. `load_markdown`: `split_markdown_sections(read_text_file(path))` → `Page(number=i, text=texto, heading=encabezado)` con `i` desde 1.

## Tests obligatorios
`tests/ingest/test_text_loaders.py`, `SAMPLES = Path(__file__).resolve().parents[2] / "samples"`. NO cambies los valores esperados.
1. `load_docx(politica_vacaciones.docx)` → 1 página, número 1, `heading is None`.
2. Su texto empieza por `"Política de vacaciones 2025\n\nDías de vacaciones\n\nCada empleado dispone de 23 días laborables de vacaciones al año."`.
3. Su texto contiene `"Antigüedad | Días adicionales\nMenos de 5 años | 0\nDe 5 a 10 años | 2\nMás de 10 años | 4"`, y esa tabla aparece DESPUÉS de `"Días adicionales por antigüedad"` y ANTES de `"Solicitudes"` (compara con `text.index(...)`).
4. DOCX vacío creado en `tmp_path` con `DocxDocument().save(...)` → `[]`.
5. `load_txt(notas_reunion.txt)` → 1 página; contiene `"versión 3.2"`; empieza por `"Reunión del 12 de mayo de 2025\nAsistentes:"`.
6. TXT en `tmp_path` con bytes `b"\xef\xbb\xbfhola\xff mundo"` (BOM + byte inválido) → texto `"hola� mundo"`.
7. TXT vacío (`b"  \n\n "`) → `[]`.
8. `load_markdown(apuntes_redes.md)` → 3 páginas, números `[1, 2, 3]`, encabezados `["Modelo OSI", "Puertos habituales", "TCP frente a UDP"]`. (La sección `# Apuntes de redes` no tiene cuerpo y se descarta.)
9. Página 2 de `apuntes_redes.md`: texto empieza por `"## Puertos habituales\n\n| Protocolo | Puerto | Transporte |"` y contiene `"| DNS | 53 | UDP |"`.
10. `load_markdown(glosario_interno.md)` → 1 página, `heading == "Glosario interno"`, contiene `"SKU-4471-B"`.
11. `split_markdown_sections("intro\n# A\ntexto a\n### sub\nmás a\n## B\ntexto b")` → `[(None, "intro"), ("A", "# A\ntexto a\n### sub\nmás a"), ("B", "## B\ntexto b")]`.
12. Bloque de código: `split_markdown_sections("# A\n```\n# no es título\n```\nfin")` → `[("A", "# A\n```\n# no es título\n```\nfin")]`.
13. `split_markdown_sections("# Título ##\ncuerpo")` → `[("Título", "# Título ##\ncuerpo")]`.
14. `split_markdown_sections("#sin espacio\ncuerpo")` → `[(None, "#sin espacio\ncuerpo")]`.

## Referencia de librerías
python-docx 1.1+ (verificado con 1.2):
```python
from docx import Document as DocxDocument  # alias: no choca con docuchat.models.Document
from docx.table import Table
from docx.text.paragraph import Paragraph

doc = DocxDocument(str(path))
for item in doc.iter_inner_content():  # Paragraph y Table en orden del documento
    if isinstance(item, Paragraph):
        item.text
    elif isinstance(item, Table):
        for row in item.rows:
            [cell.text for cell in row.cells]
```

## Aceptación
- [ ] `uv run pytest -q tests/ingest/test_text_loaders.py` pasa
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Imágenes, cabeceras/pies de Word, estilos, front-matter YAML, otros formatos.
