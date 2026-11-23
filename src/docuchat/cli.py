"""CLI de DocuChat: comandos `ingest` y `search`."""

from pathlib import Path
from typing import Annotated

import typer
from openai import OpenAIError
from rich.console import Console
from rich.markup import escape
from rich.progress import Progress
from rich.table import Table

from docuchat.config import get_settings
from docuchat.generation.answer import build_answerer
from docuchat.generation.citations import Source
from docuchat.index.embeddings import EmbeddingError
from docuchat.index.indexer import (
    IndexStats,
    build_indexer,
    reset_index,
)
from docuchat.index.vector_store import EmbeddingModelMismatchError
from docuchat.ingest.scanner import IngestResult, load_folder
from docuchat.models import SearchResult
from docuchat.retrieval.searcher import SearchMode, build_searcher

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
    reset: Annotated[
        bool,
        typer.Option("--reset", help="Borra el índice y lo reconstruye desde cero."),
    ] = False,
) -> None:
    """Indexa una carpeta de documentos (incremental)."""
    # 1. Resolución de carpeta
    root = folder if folder is not None else get_settings().documents_dir
    if not root.is_dir():
        typer.echo(f"No existe la carpeta: {root}", err=True)
        raise typer.Exit(code=1)
    root = root.resolve()
    console = Console()

    # 2. Dry-run: comportamiento actual, --reset se ignora
    if dry_run:
        result = load_folder(root)
        console.print(build_table(result, root))
        console.print(summary_line(result))
        for source, mensaje in result.errors:
            typer.echo(f"ERROR {source}: {mensaje}", err=True)
        if result.errors:
            raise typer.Exit(code=1)
        return

    # 3. Indexación real
    # 3a. Settings
    settings = get_settings()
    # 3b. Reset si procede
    if reset:
        reset_index(settings)
        console.print("Índice borrado.")
    # 3c. Construir indexador
    try:
        indexer = build_indexer(settings)
    except EmbeddingModelMismatchError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from None
    # 3d. Indexar con barra de progreso
    try:
        with indexer, Progress(console=console, transient=True) as progress:
            task = progress.add_task("Indexando", total=None)

            def on_progress(source: str, i: int, total: int) -> None:
                progress.update(task, completed=i, total=total, description=escape(source))

            stats = indexer.index_folder(root, on_progress=on_progress)
            total_chunks = indexer.chunk_count()
    except (OpenAIError, EmbeddingError) as e:
        typer.echo(f"Error con el servidor de embeddings: {type(e).__name__}: {e}", err=True)
        raise typer.Exit(code=1) from None
    # 3f. Estadísticas
    typer.echo(stats_line(stats))
    typer.echo(f"Chunks en el índice: {total_chunks}")
    # 3g. Errores por archivo
    for source, mensaje in stats.errors:
        typer.echo(f"ERROR {source}: {mensaje}", err=True)
    if stats.errors:
        raise typer.Exit(code=1)


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


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Texto a buscar.")],
    top_k: Annotated[
        int | None,
        typer.Option("--top-k", "-k", help="Número de resultados (por defecto DOCUCHAT_TOP_K)."),
    ] = None,
    mode: Annotated[
        SearchMode,
        typer.Option("--mode", help="hybrid, vector o bm25."),
    ] = SearchMode.HYBRID,
) -> None:
    """Busca en los documentos indexados."""
    # a. Validar top_k
    settings = get_settings()
    k = top_k if top_k is not None else settings.top_k
    if k <= 0:
        typer.echo("--top-k debe ser positivo", err=True)
        raise typer.Exit(code=1)

    # b. Construir searcher
    try:
        searcher = build_searcher(settings)
    except EmbeddingModelMismatchError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from None

    # c. Índice vacío
    if searcher.size() == 0:
        typer.echo("El índice está vacío. Ejecuta: docuchat ingest", err=True)
        raise typer.Exit(code=1)

    # d. Buscar
    try:
        results = searcher.search(query, k, mode)
    except (OpenAIError, EmbeddingError) as e:
        typer.echo(f"Error con el servidor de embeddings: {type(e).__name__}: {e}", err=True)
        raise typer.Exit(code=1) from None

    # e. Sin resultados
    if not results:
        typer.echo("Sin resultados.")
        return

    # f. Mostrar resultados
    for i, result in enumerate(results):
        typer.echo(format_result(result))
        if i < len(results) - 1:
            typer.echo()


@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="Pregunta sobre tus documentos.")],
    top_k: Annotated[
        int | None,
        typer.Option("--top-k", "-k", help="Fragmentos de contexto (por defecto DOCUCHAT_TOP_K)."),
    ] = None,
) -> None:
    """Responde a una pregunta citando los documentos."""
    # 1. Settings y validación de top_k
    settings = get_settings()
    if top_k is not None and top_k <= 0:
        typer.echo("--top-k debe ser positivo", err=True)
        raise typer.Exit(code=1)

    # 2. Construir searcher
    try:
        searcher = build_searcher(settings)
    except EmbeddingModelMismatchError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from None

    if searcher.size() == 0:
        typer.echo("El índice está vacío. Ejecuta: docuchat ingest", err=True)
        raise typer.Exit(code=1)

    # 3. Construir answerer y ejecutar
    try:
        answerer = build_answerer(settings, retriever=searcher, top_k=top_k)
        answer = answerer.ask(question, on_token=lambda t: typer.echo(t, nl=False))
        typer.echo()
    except (OpenAIError, EmbeddingError) as e:
        typer.echo()
        typer.echo(f"Error con el servidor de modelos: {type(e).__name__}: {e}", err=True)
        raise typer.Exit(code=1) from None

    # 4. No respuesta
    if answer.no_answer:
        return

    # 5. Respuesta y fuentes

    if answer.sources:
        typer.echo()
        typer.echo("Fuentes:")
        for line in format_sources(answer.sources):
            typer.echo(line)
    else:
        typer.echo(
            "Aviso: la respuesta no cita ninguna fuente.",
            err=True,
        )

    # 6. Citas inválidas
    if answer.invalid_citations:
        invalid_str = ", ".join(f"[{n}]" for n in answer.invalid_citations)
        typer.echo(
            f"Aviso: citas sin fuente descartadas: {invalid_str}",
            err=True,
        )


if __name__ == "__main__":
    app()
