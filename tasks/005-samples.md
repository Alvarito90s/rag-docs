# 005 · Documentos de prueba (samples/)
Fase: 0 · Depende de: 002

## Objetivo
Generar con un script 7 documentos ficticios (PDF, DOCX, MD, TXT) con datos conocidos en páginas conocidas. Serán los fixtures de los tests y la base de la evaluación. Son sintéticos para que el repo público no tenga problemas de licencia.

## Archivos
- crear: `scripts/sample_content.py` (solo datos; puede llegar a 350 líneas)
- crear: `scripts/make_samples.py`
- crear: `tests/test_samples.py`
- generados por el script (se versionan): los 7 archivos de `samples/` de la tabla. Borra `samples/.gitkeep`.

## Interfaz
`scripts/sample_content.py`:
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class PdfSpec:
    """Un PDF: cabecera/pie opcionales y el texto de cada página."""

    filename: str
    header: str | None
    footer: str | None  # admite los marcadores {page} y {total}
    pages: list[str]    # una cadena por página; párrafos separados por "\n\n"


@dataclass(frozen=True)
class DocxSpec:
    """Un DOCX: título, secciones (encabezado, párrafos) y una tabla."""

    filename: str
    title: str
    sections: list[tuple[str, list[str]]]
    table: list[list[str]]       # la primera fila es la cabecera
    table_after_section: int     # índice de la sección tras la que va la tabla


PDFS: list[PdfSpec]
DOCXS: list[DocxSpec]
TEXT_FILES: dict[str, str]       # nombre de archivo -> contenido (MD y TXT)
```

`scripts/make_samples.py`:
```python
def render_pdf(spec: PdfSpec, out_dir: Path) -> Path: ...
def render_docx(spec: DocxSpec, out_dir: Path) -> Path: ...
def write_text(filename: str, content: str, out_dir: Path) -> Path: ...
def main(out_dir: Path = Path("samples")) -> list[Path]: ...
# if __name__ == "__main__": imprime cada ruta generada
```
Importa el contenido con `from sample_content import ...` (el script se ejecuta desde `scripts/`, Python añade esa carpeta al path).

## Comportamiento
### Documentos y datos clave
Cada "dato clave" debe aparecer LITERAL, una sola vez en todo el documento, y en la página indicada. El resto de cada página es texto de relleno que escribes tú: coherente con el tema, en el idioma indicado, sin cifras, fechas ni códigos que contradigan o repitan los datos clave.

| Archivo | Págs. | Idioma | Página → dato clave |
| --- | --- | --- | --- |
| `contrato_servicios.pdf` | 4 | es | 1 → `El presente contrato se firma en Valladolid el 3 de marzo de 2025.`<br>2 → `El precio total del servicio asciende a 4.800 euros anuales, pagaderos por trimestres vencidos.`<br>3 → `El proveedor ofrece una garantía de dos años sobre todos los desarrollos entregados.`<br>4 → `Cualquiera de las partes podrá resolver el contrato con un preaviso de 30 días naturales.` |
| `manual_cafetera.pdf` | 10 | es | 2 → `El depósito de agua tiene una capacidad de 1,8 litros.`<br>5 → `Se recomienda descalcificar la cafetera cada 200 ciclos de preparación.`<br>7 → `El código de error E-17 indica que el depósito de agua está vacío.`<br>9 → `La garantía de la cafetera cubre defectos de fabricación durante tres años.` |
| `paper_rag_resumen.pdf` | 2 | en | 1 → `Hybrid retrieval improved Hit@5 from 0.71 to 0.84 on the internal benchmark.`<br>2 → `The authors used a chunk size of 512 tokens with an overlap of 64 tokens.` |

- Contrato: header `Contrato de prestación de servicios · Nubaria Datos S.L.`, footer `Página {page} de {total}`.
- Manual: header `Manual de usuario · Cafetera Brevia X2`, footer `Brevia X2 · página {page}`. En la página 5, además del dato clave, un párrafo que contenga literalmente `descalci-\nficación` (guion + salto de línea explícito, para probar la limpieza de la Fase 1). Las 10 páginas deben tener texto (manual completo: instalación, uso, limpieza, averías, garantía…).
- Paper: header `None`, footer `None`.
- Cada página de PDF: dato clave (si lo tiene) + 2 o 3 párrafos de relleno, entre 800 y 1.100 caracteres en total.
- Caracteres permitidos en los PDF: ASCII y letras/signos del español (áéíóúüñÁÉÍÓÚÑ¿¡) y `·`. Prohibido `€`, `—`, comillas tipográficas.

`politica_vacaciones.docx` (DocxSpec):
- title `Política de vacaciones 2025`
- secciones: `("Días de vacaciones", ["Cada empleado dispone de 23 días laborables de vacaciones al año.", <1 párrafo de relleno>])`, `("Días adicionales por antigüedad", [<1 párrafo de relleno>])`, `("Solicitudes", ["Las solicitudes deben enviarse con al menos 15 días de antelación.", <1 párrafo de relleno>])`
- table (`table_after_section=1`): `[["Antigüedad", "Días adicionales"], ["Menos de 5 años", "0"], ["De 5 a 10 años", "2"], ["Más de 10 años", "4"]]`

`TEXT_FILES` (contenido EXACTO; termina con un salto de línea):

`apuntes_redes.md`:
```markdown
# Apuntes de redes

## Modelo OSI

El modelo OSI divide la comunicación en siete capas: física, enlace, red, transporte, sesión, presentación y aplicación.

## Puertos habituales

| Protocolo | Puerto | Transporte |
| --- | --- | --- |
| SSH | 22 | TCP |
| SMTP | 25 | TCP |
| DNS | 53 | UDP |
| HTTPS | 443 | TCP |

## TCP frente a UDP

TCP garantiza la entrega ordenada de los segmentos; UDP no.
```

`glosario_interno.md`:
```markdown
# Glosario interno

- **SKU-4471-B**: referencia interna del filtro de agua de la Brevia X2.
- **RGPD**: Reglamento General de Protección de Datos.
- **KPI-07**: tasa de resolución en primer contacto.
- **SLA-Oro**: acuerdo de nivel de servicio con respuesta en menos de 4 horas.
```

`notas_reunion.txt`:
```
Reunión del 12 de mayo de 2025
Asistentes: Marta Ibáñez, Jorge Salas, Lucía Pardo

1. Se acordó migrar el servidor de pruebas a la versión 3.2 antes del 30 de junio.
2. Responsable de la migración: Marta Ibáñez.
3. La próxima revisión del presupuesto será en septiembre.
```

### Renderizado
1. `render_pdf`: página A4 (595 × 842). Cabecera con `insert_text` en `(56, 40)`, `fontsize=9`. Pie en `(56, 815)`, `fontsize=9`, con `footer.format(page=n, total=len(spec.pages))` (n empieza en 1). Cuerpo con `insert_textbox(Rect(56, 70, 539, 790), texto, fontsize=11, fontname="helv")`; si devuelve `< 0` lanza `ValueError(f"El texto no cabe: {spec.filename} p.{n}")`.
2. `render_docx`: `add_heading(title, level=0)`; por sección `add_heading(encabezado, level=1)` + `add_paragraph` por párrafo; la tabla (estilo `"Table Grid"`) justo después de la sección `table_after_section`.
3. `write_text`: UTF-8, contenido tal cual.
4. `main`: crea `out_dir` si no existe, genera todo y devuelve las 7 rutas. Sobrescribe si existen.
5. Strings largas: pártelas con concatenación implícita entre paréntesis para cumplir `line-length = 100` (ruff E501).

## Tests obligatorios
`tests/test_samples.py`. Comprueba los archivos YA generados en `SAMPLES = Path(__file__).resolve().parents[1] / "samples"` (no importes los scripts). Normaliza con `def norm(s: str) -> str: return " ".join(s.split())` antes de buscar frases en PDFs (el texto se parte en líneas).
1. `test_files`: el conjunto de nombres de `samples/` es exactamente los 7 archivos.
2. `test_page_counts` (parametrizado): contrato → 4, manual → 10, paper → 2.
3. `test_pdf_facts` (parametrizado, 10 casos de la tabla): el dato está en `norm(texto de esa página)` y en ninguna otra página del mismo PDF.
4. `test_contract_header_footer`: cada página `n` del contrato contiene la cabecera y `f"Página {n} de 4"`.
5. `test_manual_hyphen`: el texto crudo (sin normalizar) de la página 5 del manual contiene `"descalci-\n"`.
6. `test_pages_have_text`: toda página de los 3 PDF tiene `len(norm(texto)) >= 600`.
7. `test_docx`: los párrafos contienen `"Cada empleado dispone de 23 días laborables de vacaciones al año."` y `"Las solicitudes deben enviarse con al menos 15 días de antelación."`; las celdas de las tablas contienen `"Más de 10 años"` y `"4"`.
8. `test_text_files`: `"| DNS | 53 | UDP |"` en `apuntes_redes.md`; `"SKU-4471-B"` en `glosario_interno.md`; `"versión 3.2"` en `notas_reunion.txt`.

## Referencia de librerías
PyMuPDF 1.26+ (importa `pymupdf`, NO `fitz`):
```python
import pymupdf

doc = pymupdf.open()                          # PDF nuevo vacío
page = doc.new_page(width=595, height=842)    # A4 en puntos
page.insert_text(pymupdf.Point(56, 40), "Cabecera", fontsize=9, fontname="helv")
rc = page.insert_textbox(pymupdf.Rect(56, 70, 539, 790), texto, fontsize=11, fontname="helv")
# rc < 0  -> no cabe y no se ha escrito nada. "\n" en el texto fuerza salto de línea.
doc.save("salida.pdf")
doc.close()

with pymupdf.open("salida.pdf") as doc:       # lectura (tests)
    n = doc.page_count
    texto_p1 = doc[0].get_text()              # índice 0 = página 1
```
python-docx 1.x:
```python
from docx import Document

doc = Document()
doc.add_heading("Título", level=0)
doc.add_heading("Sección", level=1)
doc.add_paragraph("Texto.")
table = doc.add_table(rows=0, cols=2)
table.style = "Table Grid"
for a, b in filas:
    cells = table.add_row().cells
    cells[0].text = a
    cells[1].text = b
doc.save("salida.docx")

d = Document("salida.docx")                   # lectura (tests)
parrafos = [p.text for p in d.paragraphs]
celdas = [c.text for t in d.tables for r in t.rows for c in r.cells]
```

## Aceptación
- [ ] `uv run python scripts/make_samples.py` genera los 7 archivos en `samples/`
- [ ] `uv run pytest -q tests/test_samples.py` pasa
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
PDFs reales o escaneados, OCR, `eval/questions.jsonl`, cualquier loader de `src/` (Fase 1). No añadas dependencias.
