# 015-b · Rehacer la CLI según la spec 015
Fase: 1 · Depende de: 014-b

## Objetivo
`cli.py` no cumple la spec 015. Rehazlo siguiendo `tasks/015-cli-ingest.md` AL PIE DE LA LETRA.

## Qué está mal (no lo repitas)
- La carpeta es un ARGUMENTO posicional (`docuchat ingest samples --dry-run`), no la opción `--path`. Hoy `uv run docuchat ingest samples --dry-run` falla.
- `--dry-run` vale `False` por defecto; sin él, el comando sale con código 1 y el mensaje de la spec.
- Falta `@app.callback()`.
- `console = Console()` va DENTRO de `ingest`, no a nivel de módulo.
- Faltan `build_table` y `summary_line`; la tabla tiene una fila POR PÁGINA (columnas `Documento`, `Tipo`, `Página`, `Caracteres`).
- Sobran los comandos `search` y `serve`: bórralos (llegan en las Fases 3 y 5; `serve` además chocaría con el puerto 8000 de oMLX).
- Los errores van por `typer.echo(..., err=True)` con el formato `ERROR {source}: {mensaje}` y salida 1.
- Tests: 3 inventados; la spec pide 8 concretos.
- `pyproject.toml`: quita `exclude = ["tasks"]` de `[tool.ruff]` (no lo pedía ninguna spec y en `tasks/` no hay Python).

## Archivos
- reescribir: `src/docuchat/cli.py`
- reescribir: `tests/test_cli.py` (quita el `skip` de la 014-b)
- modificar: `pyproject.toml` (solo quitar esa línea)

## Comportamiento
1. Lee `tasks/015-cli-ingest.md` entera antes de empezar.
2. La interfaz, el comportamiento (puntos 1–4) y los 8 tests son los de esa spec. Tests `test_01_...` a `test_08_...`.

## Aceptación
- [ ] `uv run pytest -q tests/test_cli.py` → 8 passed
- [ ] `uv run docuchat ingest samples --dry-run` termina con 0 y la última línea es `7 documentos, 22 páginas, 13612 caracteres`
- [ ] `uv run docuchat ingest samples` termina con 1
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Cualquier otro comando o módulo.
