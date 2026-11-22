"""Loaders de TXT y Markdown."""

import re
from pathlib import Path

from docuchat.ingest.cleaning import normalize_whitespace
from docuchat.models import Page


def read_text_file(path: Path) -> str:
    """Lee un archivo de texto en UTF-8 (con o sin BOM), sustituyendo bytes inválidos."""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def load_txt(path: Path) -> list[Page]:
    """Carga un TXT como una única página."""
    text = normalize_whitespace(read_text_file(path))
    if not text.strip():
        return []
    return [Page(number=1, text=text)]


def split_markdown_sections(text: str) -> list[tuple[str | None, str]]:
    """Parte un Markdown en (encabezado, texto de la sección) por encabezados # y ##."""
    HEADING_RE = re.compile(r"^(#{1,2}) +(.+?)\s*#*\s*$")
    lines = text.split("\n")
    sections: list[tuple[str | None, list[str]]] = [(None, [])]
    in_code_block = False

    for line in lines:
        # Bloque de código: líneas cuya lstrip() empieza por ```
        if line.lstrip().startswith("```"):
            in_code_block = not in_code_block
            sections[-1][1].append(line)
            continue

        if not in_code_block:
            m = HEADING_RE.match(line)
            if m:
                # Nueva sección: la línea del encabezado va dentro del texto
                sections.append((m.group(2).strip(), [line]))
                continue

        sections[-1][1].append(line)

    # Filtrar secciones con cuerpo vacío (sin contar la línea de encabezado)
    result: list[tuple[str | None, str]] = []
    for heading, body_lines in sections:
        # El cuerpo son las líneas sin la primera (encabezado)
        body = body_lines[1:] if len(body_lines) > 1 else body_lines
        if not "".join(body).strip():
            continue
        # Normalizar el texto completo (encabezado + cuerpo)
        normalized = normalize_whitespace("\n".join(body_lines))
        result.append((heading, normalized))

    return result


def load_markdown(path: Path) -> list[Page]:
    """Carga un Markdown: una Page por sección no vacía, con su encabezado en `heading`."""
    text = read_text_file(path)
    sections = split_markdown_sections(text)
    pages: list[Page] = []
    for i, (heading, texto) in enumerate(sections, start=1):
        if texto.strip():
            pages.append(Page(number=i, text=texto, heading=heading))
    return pages
