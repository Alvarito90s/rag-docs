# 015 · CLI: `docuchat ingest --dry-run`
Fase: 1 · Depende de: 014

## Objetivo
Primer comando de la CLI: listar los documentos y páginas de una carpeta con su número de caracteres, sin indexar nada.

## Archivos
- modificar: `pyproject.toml` (solo dependencias y `[project.scripts]`)
- crear: `src/docuchat/cli.py`
- crear: `tests/test_cli.py`

## Interfaz
1. Dependencias, con este comando exacto (actualiza `pyproject.toml` y `uv.lock`):
   `uv add "typer>=0.29,<1" "rich>=15,<16"`
2. Añade a `pyproject.toml`, después de `dependencies`:
```toml
[project.scripts]
docuchat = "docuchat.cli:app"
```
   y ejecuta `uv sync`.

`src/docuchat/cli.py`:
```python
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


def summary_line(result: IngestResult) -> str:
    """'N documentos, M páginas, C caracteres'."""


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
```

## Comportamiento
1. El `@app.callback()` es obligatorio: sin él, Typer convierte una app de un solo comando en ese comando y `docuchat ingest` dejaría de funcionar.
2. `build_table`: `Table(title=f"Documentos en {escape(str(root))}")`, columnas `"Documento"`, `"Tipo"`, `"Página"` (`justify="right"`), `"Caracteres"` (`justify="right"`). Por documento: una fila por página con `escape(doc.source)` y `doc.doc_type.value` SOLO en la primera fila del documento (en las siguientes, `""`), el número de página y `page.char_count`. Un documento sin páginas ocupa una fila con página `"-"` y caracteres `"0"`.
3. `summary_line`: `f"{n_docs} documentos, {n_paginas} páginas, {n_caracteres} caracteres"`.
4. `ingest`:
   a. Si no hay `--dry-run`: `typer.echo("La indexación llega en la Fase 2. Usa --dry-run.", err=True)` y `raise typer.Exit(code=1)`.
   b. `root = folder if folder is not None else get_settings().documents_dir`.
   c. Si `root` no es una carpeta: `typer.echo(f"No existe la carpeta: {root}", err=True)` y `Exit(code=1)`.
   d. `result = load_folder(root)`. Crea `console = Console()` DENTRO de la función (si se crea a nivel de módulo, los tests no capturan la salida). `console.print(build_table(result, root))` y `console.print(summary_line(result))`.
   e. Por cada error: `typer.echo(f"ERROR {source}: {mensaje}", err=True)`. Si hubo errores, `Exit(code=1)`; si no, termina con 0.

## Tests obligatorios
`tests/test_cli.py` con `from typer.testing import CliRunner`; `runner = CliRunner()`; `SAMPLES = Path(__file__).resolve().parents[1] / "samples"`. Usa `result.output` (incluye stdout y stderr). NO cambies los valores esperados.
1. `runner.invoke(app, ["--help"])` → `exit_code == 0` y `"ingest"` en la salida.
2. `["ingest", str(SAMPLES), "--dry-run"]` → `exit_code == 0`; la salida contiene `"contrato_servicios.pdf"`, `"politica_vacaciones.docx"` y casa con `re.search(r"7 documentos, 22 páginas, \d+ caracteres", salida)`.
3. `["ingest", str(SAMPLES)]` (sin `--dry-run`) → `exit_code == 1`, `"Usa --dry-run"` en la salida.
4. `["ingest", str(tmp_path / "no"), "--dry-run"]` → `exit_code == 1`, `"No existe la carpeta"` en la salida.
5. Carpeta con `ok.txt` (`"hola"`) y `roto.pdf` (`b"no soy un pdf"`) → `exit_code == 1`, `"ERROR roto.pdf: FileDataError"` y `"1 documentos, 1 páginas, 4 caracteres"` en la salida.
6. Sin argumento de carpeta: `monkeypatch.setenv("DOCUCHAT_DOCUMENTS_DIR", str(SAMPLES))`, `get_settings.cache_clear()` antes y después → `["ingest", "--dry-run"]` da `exit_code == 0` y `"7 documentos"`.
7. `summary_line(IngestResult())` → `"0 documentos, 0 páginas, 0 caracteres"`.
8. `build_table` con un `IngestResult` de un documento de 2 páginas (constrúyelo a mano con `Document`/`Page`): `table.row_count == 2`.

## Referencia de librerías
Typer 0.29 + Rich 15 (patrón verificado):
```python
from typer.testing import CliRunner

result = CliRunner().invoke(app, ["ingest", "samples", "--dry-run"])
result.exit_code  # int
result.output  # str: stdout + stderr mezclados

raise typer.Exit(code=1)  # termina con código 1
typer.echo("mensaje", err=True)  # escribe en stderr

table = Table(title="T")
table.add_column("Página", justify="right")
table.add_row("1")
table.row_count  # número de filas
```

## Aceptación
- [ ] `uv run pytest -q tests/test_cli.py` pasa
- [ ] `uv run docuchat ingest samples --dry-run` muestra la tabla y `7 documentos, 22 páginas, … caracteres` (salida 0)
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Comandos `search`, `ask` y `serve`; indexado real; barra de progreso (Fase 2).
