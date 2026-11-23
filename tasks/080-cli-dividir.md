# 080 · Dividir el CLI y vigilar el límite de 300 líneas
Fase: 8 · Depende de: 074

## Objetivo
`src/docuchat/cli.py` tiene 315 líneas e incumple la regla 2 de `AGENTS.md`. Mover las funciones puras de formato a un módulo propio y añadir un test que impida volver a pasar el límite en `src/`.

## Archivos
- crear: `src/docuchat/cli_format.py`
- modificar: `src/docuchat/cli.py` (solo quitar las 6 funciones movidas y sus imports sobrantes; añadir el import de `cli_format`)
- crear: `tests/test_file_sizes.py`

## Interfaz
`src/docuchat/cli_format.py`, con este docstring de módulo: `"""Formato de la salida del CLI: tablas y líneas de texto."""`.

Las 6 funciones se mueven **tal cual** desde `cli.py`, mismo cuerpo, misma firma y mismo docstring:
```python
from pathlib import Path

from rich.markup import escape
from rich.table import Table

from docuchat.generation.citations import Source
from docuchat.index.indexer import IndexStats
from docuchat.ingest.scanner import IngestResult
from docuchat.models import SearchResult


def build_table(result: IngestResult, root: Path) -> Table: ...
def summary_line(result: IngestResult) -> str: ...
def stats_line(stats: IndexStats) -> str: ...
def format_sources(sources: list[Source]) -> list[str]: ...
def snippet(text: str, width: int = 150) -> str: ...
def format_result(result: SearchResult) -> str: ...
```

En `cli.py`, en el bloque de imports:
```python
from docuchat.cli_format import (
    build_table,
    format_result,
    format_sources,
    snippet as snippet,  # reexportación: cli.py no lo usa, los tests lo importan de aquí
    stats_line,
    summary_line,
)
```
Si ruff (I001) prefiere otro orden, aplica `uv run ruff check --fix` y `uv run ruff format`.

## Comportamiento
1. El comportamiento del CLI no cambia: mismos comandos, opciones, mensajes y códigos de salida.
2. `from docuchat.cli import build_table, format_result, format_sources, snippet, stats_line, summary_line` sigue funcionando, porque `cli.py` las importa y las usa. `tests/test_cli.py` NO se toca.
3. Los `monkeypatch.setattr("docuchat.cli.build_indexer" | "docuchat.cli.build_searcher" | "docuchat.cli.build_answerer", ...)` de los tests siguen funcionando: esos nombres se quedan en `cli.py`.
4. Quita de `cli.py` los imports que dejen de usarse (ruff F401 te los marca). Ojo: `escape` y `Table` pueden seguir haciendo falta en `cli.py`; compruébalo con ruff, no a ojo.
5. `snippet` y `build_table`/`summary_line`/`stats_line`/`format_sources`/`format_result` tienen que seguir importables desde `docuchat.cli`, porque `tests/test_cli.py` los importa de ahí. `snippet` solo se usa dentro de `format_result`, así que en `cli.py` quedará sin uso y ruff marcará F401. Para todo nombre que `cli.py` no use, impórtalo con alias explícito de reexportación: `snippet as snippet`. Ese es el modismo que ruff y mypy reconocen como reexportación; no uses `# noqa`. Los que `cli.py` sí usa van sin alias.
6. `tests/test_file_sizes.py` recorre todos los `*.py` bajo `src/` (recursivo) y comprueba que cada uno tenga menos de 300 líneas. El mensaje de fallo lista cada archivo infractor con su número de líneas.

## Tests obligatorios
`tests/test_file_sizes.py`. NO cambies los valores esperados.
```python
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
MAX_LINES = 300
```
1. `test_src_files_under_limit`: para cada `path in sorted(SRC.rglob("*.py"))`, cuenta `len(path.read_text(encoding="utf-8").splitlines())`. Reúne los que tengan `>= MAX_LINES` como `f"{path.relative_to(SRC)}: {n}"` y haz `assert not too_long, "\n".join(too_long)`.
2. `test_scan_finds_files`: `len(list(SRC.rglob("*.py"))) >= 30` (hoy hay 37) (evita que el test anterior pase en vacío si la ruta está mal).
3. `test_cli_format_importable`: `from docuchat.cli_format import build_table, format_result, format_sources, snippet, stats_line, summary_line` y `from docuchat.cli import build_table as b2`; `assert b2 is build_table` (es la misma función, no una copia).

Además, todo `tests/test_cli.py` tiene que seguir pasando sin modificaciones.

## Aceptación
- [ ] `uv run pytest -q tests/test_file_sizes.py` → 3 passed
- [ ] `uv run pytest -q tests/test_cli.py` pasa sin tocar el archivo de tests
- [ ] `uv run pytest -q` pasa entero (467 + 3 = 470)
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `wc -l src/docuchat/cli.py` → menos de 300
- [ ] `git diff --stat tests/test_cli.py` → vacío

## Fuera de alcance
No cambies ningún comando ni opción del CLI. No muevas `ingest`, `search`, `ask` ni `serve`. No toques `tests/test_cli.py`.
