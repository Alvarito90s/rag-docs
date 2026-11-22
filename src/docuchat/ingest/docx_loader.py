"""Loader de DOCX: párrafos y tablas como una única página."""

from pathlib import Path

from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph

from docuchat.ingest.cleaning import normalize_whitespace
from docuchat.models import Page


def table_to_text(table: Table) -> str:
    """Una línea por fila con las celdas separadas por ' | '."""
    return "\n".join(" | ".join(cell.text.strip() for cell in row.cells) for row in table.rows)


def load_docx(path: Path) -> list[Page]:
    """Carga un DOCX como una única página (párrafos y tablas en orden)."""
    doc = DocxDocument(str(path))
    parts: list[str] = []
    for item in doc.iter_inner_content():
        if isinstance(item, Paragraph):
            txt = item.text.strip()
            if txt:
                parts.append(txt)
        elif isinstance(item, Table):
            txt = table_to_text(item)
            if txt.strip():
                parts.append(txt)
    full_text = "\n\n".join(parts)
    full_text = normalize_whitespace(full_text)
    if not full_text.strip():
        return []
    return [Page(number=1, text=full_text)]
