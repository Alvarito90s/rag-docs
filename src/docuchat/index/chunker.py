"""Chunking recursivo de texto por separadores de mayor a menor escala."""

import re
from collections.abc import Sequence

from docuchat.models import Chunk, Document, make_chunk_id

SEPARATORS: list[tuple[str, str]] = [
    ("\n\n", r"\n\n+"),  # párrafos
    ("\n", r"\n"),  # líneas
    (" ", r"(?<=[.!?])\s+"),  # frases
    (" ", r" +"),  # palabras
]

Unit = tuple[str, str]  # (joiner, texto)


def split_units(text: str, chunk_size: int, joiner: str = "", level: int = 0) -> list[Unit]:
    """Descompone el texto en unidades de como mucho ``chunk_size`` caracteres."""
    if len(text) <= chunk_size:
        return [(joiner, text)]

    if level >= len(SEPARATORS):
        # Corte duro: trozos de ``chunk_size``; el primero lleva ``joiner``, los demás "".
        out: list[Unit] = []
        for i in range(0, len(text), chunk_size):
            out.append((joiner if i == 0 else "", text[i : i + chunk_size]))
        return out

    sep, pattern = SEPARATORS[level]
    parts = [p for p in re.split(pattern, text) if p.strip()]

    if len(parts) <= 1:
        return split_units(text, chunk_size, joiner, level + 1)

    units: list[Unit] = []
    for i, parte in enumerate(parts):
        stripped = parte.strip()
        j = joiner if i == 0 else sep
        units.extend(split_units(stripped, chunk_size, j, level + 1))
    return units


def join_units(units: Sequence[Unit]) -> str:
    """Une unidades: la primera sin su joiner, las demás precedidas por el suyo."""
    return "".join(u if i == 0 else j + u for i, (j, u) in enumerate(units))


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Agrupa unidades en chunks de como mucho ``chunk_size`` caracteres con solape."""
    if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_size debe ser positivo y mayor que chunk_overlap "
            f"(got chunk_size={chunk_size}, chunk_overlap={chunk_overlap})"
        )

    text = text.strip()
    if not text:
        return []

    units = split_units(text, chunk_size)
    current: list[Unit] = []
    chunks: list[str] = []

    for unit in units:
        if not current:
            current = [unit]
        elif len(join_units(current + [unit])) <= chunk_size:
            current.append(unit)
        else:
            chunks.append(join_units(current))
            # Solape: unidades completas hacia atrás
            carry: list[Unit] = []
            for u in reversed(current):
                if len(join_units([u] + carry)) <= chunk_overlap:
                    carry = [u] + carry
                else:
                    break
            current = carry + [unit]
            while len(current) > 1 and len(join_units(current)) > chunk_size:
                current = current[1:]

    if current:
        chunks.append(join_units(current))

    return chunks


def chunk_document(doc: Document, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """Chunks de todas las páginas; ningún chunk cruza páginas."""
    result: list[Chunk] = []
    for page in doc.pages:
        for position, texto in enumerate(split_text(page.text, chunk_size, chunk_overlap)):
            result.append(
                Chunk(
                    chunk_id=make_chunk_id(doc.source, page.number, position),
                    source=doc.source,
                    doc_sha256=doc.sha256,
                    page=page.number,
                    position=position,
                    heading=page.heading,
                    text=texto,
                )
            )
    return result
