# Informe 080 · Dividir el CLI y vigilar el límite de 300 líneas
Estado: COMPLETADA

## Cambios
- `src/docuchat/cli_format.py`: **nuevo** — módulo con docstring `"""Formato de la salida del CLI: tablas y líneas de texto."""` y las 6 funciones puras de formato: `build_table`, `summary_line`, `stats_line`, `format_sources`, `snippet`, `format_result`. Imports propios (`Path`, `escape`, `Table`, `Source`, `IndexStats`, `IngestResult`, `SearchResult`).
- `src/docuchat/cli.py`: **modificado** — se eliminaron las 6 funciones de formato (de 315 a 258 líneas). Se quitaron imports que quedaron huérfanos (`Table`, `Source`, `escape`, `IndexStats`, `IngestResult`, `SearchResult`). Se añadió import de `cli_format` con reexportación explícita: `snippet as snippet` para los nombres que `cli.py` importa pero no usa directamente.
- `tests/test_file_sizes.py`: **nuevo** — 3 tests: `test_src_files_under_limit` (todos los .py de src/ < 300 líneas), `test_scan_finds_files` (≥ 30 archivos en src/), `test_cli_format_importable` (misma función importada desde cli_format y cli).

## Verificación
- `uv run pytest -q tests/test_file_sizes.py` → **3 passed**
- `uv run pytest -q tests/test_cli.py` → **36 passed** (sin modificar)
- `uv run pytest -q` → **470 passed** (467 + 3)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores
- `wc -l src/docuchat/cli.py` → **258 líneas** (< 300)
- `git diff --stat tests/test_cli.py` → **vacío**

## Decisiones que tomé
- No hubo decisiones ambiguas: la spec era exhaustiva. Se siguió exactamente el orden de imports que ruff/I001 exige (bloque `docuchat.*` unificado con `cli_format` mezclado alfabéticamente).
- `snippet as snippet` en `cli.py`: ruff marcaría F401 si se importa sin alias porque no se usa en el cuerpo. El modismo `X as X` es reconocido por ruff y mypy como reexportación (no se elimina).
- En `test_file_sizes.py` se añadieron `# noqa: F401` a las 5 funciones importadas solo para verificar que son importables (el import mismo es la prueba de que la función existe).

## Bloqueos y dudas
- Sin bloqueos. Todo pasó a la primera tras aplicar `ruff check --fix` + `ruff format` para ordenar imports y eliminar en blanco extra.
