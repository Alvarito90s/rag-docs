"""Formato de la salida del CLI: tablas y líneas de texto."""

from pathlib import Path

from rich.markup import escape
from rich.table import Table

from docuchat.generation.citations import Source
from docuchat.index.indexer import IndexStats
from docuchat.ingest.scanner import IngestResult
from docuchat.models import SearchResult


def build_table(result: IngestResult, root: Path) -> Table:
    """Tabla con una fila por página: Documento, Tipo, Página, Caracteres."""
    table = Table(title=f"Documentos en {escape(str(root))}")
    table.add_column("Documento")
    table.add_column("Tipo")
    table.add_column("Página", justify="right")
    table.add_column("Caracteres", justify="right")
    for doc in result.documents:
        if doc.page_count == 0:
            table.add_row(escape(doc.source), doc.doc_type.value, "-", "0")
            continue
        for idx, page in enumerate(doc.pages):
            tipo = doc.doc_type.value if idx == 0 else ""
            doc_name = escape(doc.source) if idx == 0 else ""
            table.add_row(doc_name, tipo, str(page.number), str(page.char_count))
    return table


def summary_line(result: IngestResult) -> str:
    """'N documentos, M páginas, C caracteres'."""
    n_docs = len(result.documents)
    n_paginas = sum(doc.page_count for doc in result.documents)
    n_caracteres = sum(page.char_count for doc in result.documents for page in doc.pages)
    return f"{n_docs} documentos, {n_paginas} páginas, {n_caracteres} caracteres"


def stats_line(stats: IndexStats) -> str:
    """'A añadidos, U actualizados, S sin cambios, R eliminados, E con errores'."""
    return (
        f"{len(stats.added)} añadidos, "
        f"{len(stats.updated)} actualizados, "
        f"{len(stats.unchanged)} sin cambios, "
        f"{len(stats.removed)} eliminados, "
        f"{len(stats.errors)} con errores"
    )


def format_sources(sources: list[Source]) -> list[str]:
    """Una línea por fuente: '[n] documento, p. X'."""
    return [f"[{s.number}] {s.source}, p. {s.page}" for s in sources]


def snippet(text: str, width: int = 150) -> str:
    """Texto en una línea (espacios colapsados), cortado a width caracteres con '…'."""
    plano = " ".join(text.split())
    if len(plano) <= width:
        return plano
    return plano[:width].rstrip() + "…"


def format_result(result: SearchResult) -> str:
    """Dos líneas: cabecera con puesto, documento, página y puntuaciones, y el fragmento."""
    v_rank = f"{result.vector_rank}" if result.vector_rank is not None else "-"
    b_rank = f"{result.bm25_rank}" if result.bm25_rank is not None else "-"
    header = (
        f"[{result.rank}] {result.chunk.source} · p. {result.chunk.page} "
        f"· {result.score:.4f} (vec {v_rank}, bm25 {b_rank})"
    )
    return f"{header}\n    {snippet(result.chunk.text)}"
