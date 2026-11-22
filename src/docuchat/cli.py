"""CLI de DocuChat: comando `ingest` con Rich."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from docuchat.config import get_settings
from docuchat.ingest.scanner import IngestResult, load_folder

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="DocuChat Local: pregunta a tus documentos.",
)


@app.callback()
def main() -> None:
    """DocuChat Local."""


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


@app.command()
def ingest(
    folder: Annotated[
        Path | None,
        typer.Argument(help="Carpeta a ingerir (por defecto DOCUCHAT_DOCUMENTS_DIR)."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Solo lista documentos y páginas; no indexa."),
    ] = False,
) -> None:
    """Ingiere una carpeta de documentos."""
    if not dry_run:
        typer.echo(
            "La indexación llega en la Fase 2. Usa --dry-run.",
            err=True,
        )
        raise typer.Exit(code=1)
    root = folder if folder is not None else get_settings().documents_dir
    if not root.is_dir():
        typer.echo(f"No existe la carpeta: {root}", err=True)
        raise typer.Exit(code=1)
    root = root.resolve()
    console = Console()
    result = load_folder(root)
    console.print(build_table(result, root))
    console.print(summary_line(result))
    for source, mensaje in result.errors:
        typer.echo(f"ERROR {source}: {mensaje}", err=True)
    if result.errors:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
