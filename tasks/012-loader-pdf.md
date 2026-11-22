# 012 · Loader de PDF
Fase: 1 · Depende de: 010, 011

## Objetivo
Leer un PDF con PyMuPDF y devolver una `Page` por página, con el texto limpio y los párrafos separados por `"\n\n"`.

## Archivos
- crear: `src/docuchat/ingest/pdf_loader.py`
- crear: `tests/ingest/test_pdf_loader.py`

## Interfaz
```python
from pathlib import Path

import pymupdf

from docuchat.ingest.cleaning import (
    fix_hyphenation,
    join_lines,
    normalize_whitespace,
    remove_repeated_edges,
)
from docuchat.models import Page


def extract_paragraphs(path: Path) -> list[list[str]]:
    """Devuelve, por cada página, la lista de bloques de texto en orden de lectura."""


def load_pdf(path: Path) -> list[Page]:
    """Carga un PDF: una Page por página no vacía, con el texto limpio."""
```

## Comportamiento
1. `extract_paragraphs`: abre con `with pymupdf.open(path) as doc:`; para cada página, `page.get_text("blocks", sort=True)`; conserva solo bloques de texto (`b[6] == 0`) cuyo texto `b[4]` no esté vacío tras `strip()`; devuelve el texto crudo `b[4]` de cada bloque (sin limpiar). Una lista por página, también para páginas sin bloques (lista vacía).
2. `load_pdf`:
   a. `pages = remove_repeated_edges(extract_paragraphs(path))`.
   b. Para cada página `n` (empezando en 1): cada párrafo → `join_lines(fix_hyphenation(p))` (en ese orden: primero el guion, luego unir líneas); une los párrafos con `"\n\n"`; aplica `normalize_whitespace`.
   c. Si el texto queda vacío, la página se omite, pero las demás conservan su número real.
3. Los errores de PyMuPDF (archivo corrupto, etc.) NO se capturan aquí: se propagan.

## Tests obligatorios
`tests/ingest/test_pdf_loader.py`, con `SAMPLES = Path(__file__).resolve().parents[2] / "samples"`. NO cambies los valores esperados.
1. `load_pdf(contrato_servicios.pdf)` → 4 páginas, números `[1, 2, 3, 4]`.
2. Contrato: ninguna página contiene `"Nubaria Datos S.L."` ni coincide con `re.search(r"Página \d+ de 4", texto)` (cabecera y pie eliminados).
3. Manual (`manual_cafetera.pdf`): 10 páginas; ninguna contiene `"Brevia X2 · página"` ni `"Manual de usuario · Cafetera Brevia X2"`.
4. Manual, página 5: contiene `"descalcificación periódica"` y NO contiene `"descalci-"`.
5. Paper (`paper_rag_resumen.pdf`, 2 páginas, sin cabecera): 2 páginas; p1 contiene `"Hybrid retrieval improved Hit@5 from 0.71 to 0.84 on the internal benchmark."`.
6. Datos clave LITERALES en el `text` de su página (sin normalizar en el test): contrato p2 `"El precio total del servicio asciende a 4.800 euros anuales, pagaderos por trimestres vencidos."`; manual p7 `"El código de error E-17 indica que el depósito de agua está vacío."`; manual p9 `"La garantía de la cafetera cubre defectos de fabricación durante tres años."`.
7. En los 3 PDFs, ningún texto de página contiene un `"\n"` suelto: `"\n" not in texto.replace("\n\n", "")`.
8. `extract_paragraphs(contrato)`: 4 listas; el primer bloque de cada página empieza por `"Contrato de prestación de servicios"` y el último empieza por `"Página "` (orden de lectura con `sort=True`).
9. PDF con una página en blanco en medio: créalo en `tmp_path` con PyMuPDF (3 páginas; texto en la 1 y la 3 con `page.insert_text((72, 72), "texto uno")` y `"texto tres"`; la 2 vacía) → `load_pdf` devuelve números `[1, 3]`.
10. Archivo con bytes basura (`b"no soy un pdf"`) guardado como `roto.pdf` → `pytest.raises(pymupdf.FileDataError)`.

## Referencia de librerías
PyMuPDF 1.26+ (verificado con 1.28):
```python
import pymupdf

with pymupdf.open(path) as doc:  # Path o str
    for page in doc:  # en orden
        for b in page.get_text("blocks", sort=True):
            x0, y0, x1, y1, texto, block_no, block_type = b
            # block_type 0 = texto, 1 = imagen. 'texto' trae "\n" entre líneas.

doc = pymupdf.open()  # PDF nuevo (para tests)
page = doc.new_page()
page.insert_text((72, 72), "texto uno")
doc.save(tmp_path / "x.pdf")

pymupdf.open("roto.pdf")  # bytes inválidos -> pymupdf.FileDataError
```

## Aceptación
- [ ] `uv run pytest -q tests/ingest/test_pdf_loader.py` pasa
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
OCR, tablas o columnas en PDF, metadatos del PDF, otros formatos.
