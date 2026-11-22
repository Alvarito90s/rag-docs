"""Loader de PDF: PyMuPDF → lista de Page con texto limpio."""

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
    with pymupdf.open(path) as doc:  # type: ignore[no-untyped-call]
        all_blocks: list[list[str]] = []
        for page in doc:
            page_blocks: list[str] = []
            for b in page.get_text("blocks", sort=True):
                x0, y0, x1, y1, texto, block_no, block_type = b
                if block_type == 0 and texto.strip():
                    page_blocks.append(texto)
            all_blocks.append(page_blocks)
        return all_blocks


def load_pdf(path: Path) -> list[Page]:
    """Carga un PDF: una Page por página no vacía, con el texto limpio."""
    raw_pages = extract_paragraphs(path)
    cleaned = remove_repeated_edges(raw_pages)
    pages: list[Page] = []
    for number, paragraphs in enumerate(cleaned, start=1):
        full_text = "\n\n".join(paragraphs)
        full_text = fix_hyphenation(full_text)
        full_text = normalize_whitespace(full_text)
        # join_lines por párrafo
        paras = full_text.split("\n\n")
        paras = [join_lines(p) for p in paras if p.strip()]
        joined = "\n\n".join(paras)
        if not joined.strip():
            continue
        pages.append(Page(number=number, text=joined))
    return pages
