# Informe 015-b · Rehacer la CLI según la spec 015
Estado: COMPLETADA

## Cambios
- `src/docuchat/cli.py`: reescrito siguiendo la spec 015-al pie de la letra
  - `@app.callback()` con `main()` añadido (obligatorio para `docuchat ingest`)
  - `build_table(result, root)`: una fila por página con Documento/Tipo/Página/Caracteres
  - `summary_line(result)`: `'N documentos, M páginas, C caracteres'`
  - `ingest(folder: Path | None, dry_run: bool = False)`: folder es argumento posicional,
    dry_run por defecto False
  - `console = Console()` creado DENTRO de `ingest` (para que los tests capturen salida)
  - Sin `--dry-run`: error por stderr + Exit(1)
  - Errores de load_folder: `typer.echo(f"ERROR {source}: {mensaje}", err=True)` + Exit(1)
  - Eliminados los comandos `search` y `serve` (llegan en Fases 3 y 5)
- `tests/test_cli.py`: reescrito con 8 tests obligatorios (test_01 a test_08)
  - Eliminados los 3 tests inventados y el `@pytest.mark.skip`
- `pyproject.toml`: se quitó `exclude = ["tasks"]` (no lo pedía la spec)

## Especificidad de la spec cumplida
- La carpeta es ARGUMENTO posicional: `docuchat ingest samples --dry-run`
- `dry_run` vale `False` por defecto (sin él, sale con código 1)
- `summary_line` devuelve exactamente `'N documentos, M páginas, C caracteres'`
- Tabla con columnas: Documento, Tipo, Página (justify right), Caracteres (justify right)

## Verificación
- `uv run pytest -q tests/test_cli.py` → **8 passed** ✅
- `uv run docuchat ingest samples --dry-run` → exit 0, última línea
  `7 documentos, 22 páginas, 13612 caracteres` ✅
- `uv run docuchat ingest samples` → exit 1, stderr con `'Usa --dry-run'` ✅
- `uv run pytest -q` → **121 passed**, 5 warnings ✅
- `uv run ruff check .` → sin errores ✅
- `uv run ruff format --check .` → 68 files ✅
- `uv run mypy src` → success, 11 files ✅

## Decisiones que tomé
Ninguna. La spec fija la interfaz exacta, el comportamiento y los 8 tests.

## Bloqueos y dudas
Bucle en `scan_folder` vs `load_folder`: `scan_folder` resuelve `root` internamente,
pero `load_document` recibía el `root` original (relativo). Al llamar desde CLI con
`samples` (relativo), `path.relative_to(root)` fallaba con `ValueError` (absolutos vs
relativos). Solución: resolver `root` después de la comprobación `is_dir` en `ingest()`,
antes de llamar a `load_folder`.
