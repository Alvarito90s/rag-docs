# 027 · `docuchat ingest` indexa de verdad
Fase: 2 · Depende de: 026

## Objetivo
Sin `--dry-run`, `docuchat ingest` indexa la carpeta con el `Indexer` incremental, con barra de progreso Rich y opción `--reset`.

## Archivos
- modificar: `src/docuchat/cli.py` (solo `ingest`, una función nueva `stats_line` y los imports)
- modificar: `tests/test_cli.py` (sustituye `test_03_no_dry_run` y añade los tests nuevos)

## Interfaz
```python
from openai import OpenAIError
from rich.progress import Progress

from docuchat.index.embeddings import EmbeddingError
from docuchat.index.indexer import IndexStats, build_indexer, reset_index
from docuchat.index.vector_store import EmbeddingModelMismatchError


def stats_line(stats: IndexStats) -> str:
    """'A añadidos, U actualizados, S sin cambios, R eliminados, E con errores'."""


@app.command()
def ingest(
    folder: Annotated[Path | None, typer.Argument(help=...)] = None,  # igual que ahora
    dry_run: Annotated[bool, typer.Option("--dry-run", help=...)] = False,  # igual que ahora
    reset: Annotated[
        bool,
        typer.Option("--reset", help="Borra el índice y lo reconstruye desde cero."),
    ] = False,
) -> None:
    """Indexa una carpeta de documentos (incremental)."""
```
Importa `build_indexer` y `reset_index` con `from docuchat.index.indexer import ...` (los tests los parchean en `docuchat.cli`).

## Comportamiento
1. Resolución de carpeta igual que ahora (argumento o `documents_dir`; si no existe → `"No existe la carpeta: ..."`, exit 1; después `root = root.resolve()`). Va ANTES de cualquier otra cosa.
2. Con `--dry-run`: exactamente el comportamiento actual (tabla + resumen + errores). `--reset` se ignora.
3. Sin `--dry-run`:
   a. `settings = get_settings()`.
   b. Si `reset`: `reset_index(settings)` y `console.print("Índice borrado.")`.
   c. `indexer = build_indexer(settings)`. `EmbeddingModelMismatchError` → `typer.echo(str(e), err=True)`, exit 1.
   d. `with indexer, Progress(console=console, transient=True) as progress:` crea `task = progress.add_task("Indexando", total=None)` y llama a `indexer.index_folder(root, on_progress=...)`, donde el callback hace `progress.update(task, completed=i, total=total, description=escape(source))`. Dentro del mismo `with`, guarda `total_chunks = indexer.chunk_count()`.
   e. `OpenAIError` o `EmbeddingError` durante la pasada → `typer.echo(f"Error con el servidor de embeddings: {type(e).__name__}: {e}", err=True)` y exit 1. Ningún otro `except`.
   f. Imprime `stats_line(stats)` y luego `f"Chunks en el índice: {total_chunks}"`.
   g. Por cada error de `stats.errors`: `typer.echo(f"ERROR {source}: {mensaje}", err=True)`; si hay alguno, exit 1. Si no, exit 0.
4. `stats_line`: `f"{len(added)} añadidos, {len(updated)} actualizados, {len(unchanged)} sin cambios, {len(removed)} eliminados, {len(errors)} con errores"`.

## Tests obligatorios
`tests/test_cli.py`. NO cambies los valores esperados ni los tests 01, 02 y 04–08 existentes. BORRA `test_03_no_dry_run` (ya no aplica) y añade:

```python
from docuchat.index import indexer as indexer_mod

class FakeEmbedder:  # mismo que en tests/index/test_indexer.py (cópialo aquí)
    ...

@pytest.fixture()
def index_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    """Índice en tmp_path/data con embedder falso; devuelve data_dir."""
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DOCUCHAT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(
        "docuchat.cli.build_indexer",
        lambda s: indexer_mod.build_indexer(s, embedder=FakeEmbedder()),
    )
    get_settings.cache_clear()
    yield tmp_path / "data"
    get_settings.cache_clear()
```
9. `test_09_index_samples` (`index_env`): `ingest SAMPLES` → exit 0; salida contiene `"7 añadidos, 0 actualizados, 0 sin cambios, 0 eliminados, 0 con errores"` y `"Chunks en el índice: 26"`; existe `index_env / "registry.sqlite3"`.
10. `test_10_second_run_unchanged`: dos veces `ingest SAMPLES` → la segunda, exit 0 y `"0 añadidos, 0 actualizados, 7 sin cambios"` en la salida y `"Chunks en el índice: 26"`.
11. `test_11_reset`: `ingest SAMPLES` y luego `ingest SAMPLES --reset` → exit 0, `"Índice borrado."` y `"7 añadidos"` en la salida, `"Chunks en el índice: 26"`.
12. `test_12_model_mismatch`: `ingest SAMPLES`; `monkeypatch.setenv("DOCUCHAT_EMBEDDING_MODEL", "otro")` y `get_settings.cache_clear()`; `ingest SAMPLES` → exit 1 y `"Reindexa con --reset"` en la salida; `ingest SAMPLES --reset` → exit 0 y `"7 añadidos"`.
13. `test_13_embedding_error`: parchea `docuchat.cli.build_indexer` con `FakeEmbedder(fail_on="")` (falla siempre) → exit 1, `"Error con el servidor de embeddings: APIConnectionError"` en la salida, `isinstance(result.exception, SystemExit)` (sin traceback).
14. `test_14_broken_file`: carpeta con `ok.txt` (`"Hola."`) y `roto.pdf` (`b"no es un pdf"`) → exit 1, `"1 añadidos"`, `"1 con errores"` y `"ERROR roto.pdf"` en la salida.
15. `test_15_removed`: carpeta con `a.txt` y `b.txt` (`"A."`, `"B."`) → `ingest`; borra `b.txt`; `ingest` → exit 0 y `"1 eliminados"`, `"Chunks en el índice: 1"`.
16. `test_16_dry_run_ignores_reset`: `ingest SAMPLES --dry-run --reset` → exit 0, `"7 documentos, 22 páginas"` en la salida, `"Índice borrado."` NO en la salida.
17. `test_17_stats_line`: `stats_line(IndexStats(added=["a"], unchanged=["b", "c"], errors=[("d", "x")]))` → `"1 añadidos, 0 actualizados, 2 sin cambios, 0 eliminados, 1 con errores"`.

`CliRunner()` de Typer 0.29 mezcla stdout y stderr en `result.output` (los tests existentes ya lo usan así).

## Referencia de librerías
Rich 15 (comprobado con `CliRunner`: con `transient=True` la barra no deja rastro en la salida):
```python
from rich.progress import Progress

with Progress(console=console, transient=True) as progress:
    task = progress.add_task("Indexando", total=None)  # total desconocido al empezar
    progress.update(task, completed=2, total=7, description="manual_cafetera.pdf")
```

## Aceptación
- [ ] `uv run pytest -q tests/test_cli.py` → 16 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "Usa --dry-run" src/docuchat/cli.py tests/test_cli.py` → sin resultados
- [ ] Servidor inexistente: `DOCUCHAT_EMBEDDING_BASE_URL=http://127.0.0.1:9/v1 DOCUCHAT_REQUEST_MAX_RETRIES=0 DOCUCHAT_DATA_DIR=/tmp/dc-027 uv run docuchat ingest samples; echo $?` → `Error con el servidor de embeddings: APIConnectionError...`, `1`, sin traceback
- [ ] (humano, con `.env` y el modelo de embeddings descargado) `uv run docuchat ingest` → `7 añadidos`, `Chunks en el índice: 26`; repetir → `7 sin cambios`

## Fuera de alcance
No toques `indexer.py` ni nada de `index/`. Nada de `search`, `ask` ni `serve`. No leas `.env`.
