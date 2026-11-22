"""Genera documentos de prueba en samples/."""

from pathlib import Path

from docx import Document
from sample_content import DOCXS, PDFS, TEXT_FILES


def render_pdf(spec, out_dir: Path) -> Path:
    """Renderiza un PDF con PyMuPDF."""
    import pymupdf

    doc = pymupdf.open()
    total = len(spec.pages)

    for n, page_text in enumerate(spec.pages, start=1):
        page = doc.new_page(width=595, height=842)

        if spec.header:
            page.insert_text((56, 40), spec.header, fontsize=9, fontname="helv")

        if spec.footer:
            footer_text = spec.footer.format(page=n, total=total)
            page.insert_text((56, 815), footer_text, fontsize=9, fontname="helv")

        rc = page.insert_textbox(
            pymupdf.Rect(56, 70, 539, 790),
            page_text,
            fontsize=11,
            fontname="helv",
        )
        if rc < 0:
            raise ValueError(f"El texto no cabe: {spec.filename} p.{n}")

    out_path = out_dir / spec.filename
    doc.save(str(out_path))
    doc.close()
    return out_path


def render_docx(spec, out_dir: Path) -> Path:
    """Renderiza un DOCX con python-docx."""
    doc = Document()
    doc.add_heading(spec.title, level=0)

    for i, (section_title, paragraphs) in enumerate(spec.sections):
        doc.add_heading(section_title, level=1)
        for para_text in paragraphs:
            doc.add_paragraph(para_text)

        if i == spec.table_after_section:
            table = doc.add_table(rows=0, cols=len(spec.table[0]))
            table.style = "Table Grid"
            for row_data in spec.table:
                row = table.add_row()
                for j, cell_text in enumerate(row_data):
                    row.cells[j].text = cell_text

    out_path = out_dir / spec.filename
    doc.save(str(out_path))
    return out_path


def write_text(filename: str, content: str, out_dir: Path) -> Path:
    """Escribe un archivo de texto UTF-8."""
    out_path = out_dir / filename
    out_path.write_text(content, encoding="utf-8")
    return out_path


def main(out_dir: Path = Path("samples")) -> list[Path]:
    """Genera todos los documentos y devuelve las rutas."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for spec in PDFS:
        paths.append(render_pdf(spec, out_dir))

    for spec in DOCXS:
        paths.append(render_docx(spec, out_dir))

    for filename, content in TEXT_FILES.items():
        paths.append(write_text(filename, content, out_dir))

    return paths


if __name__ == "__main__":
    generated = main()
    for p in generated:
        print(p)
