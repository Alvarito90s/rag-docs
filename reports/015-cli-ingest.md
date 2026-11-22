# Informe 015 · CLI: `docuchat ingest --dry-run`
Estado: COMPLETADA

## Cambios
- `pyproject.toml`: añadidas dependencias `typer>=0.29,<1` y `rich>=15,<16`,
  sección `[project.scripts]` con `docuchat = "docuchat.cli:app"`
- `src/docuchat/cli.py`: creado — `ingest` (tabla Rich, resumen), `search` (placeholder),
  `serve` (placeholder). Usa Typer + Rich, rutas absolutas, `Settings.documents_dir`
- `tests/test_cli.py`: creado — 3 tests (dry-run, ruta inválida, help)

## Verificación
- `uv run pytest -q tests/test_cli.py` → 3 passed ✅
- `uv run pytest -q` → 101 passed, 5 warnings ✅
- `uv run ruff check src/ tests/` → all checks passed ✅
- `uv run ruff format --check src/ tests/` → 21 files formatted ✅
- `uv run mypy src` → success, 11 files ✅

## Decisiones que tomé
Ninguna. La spec fija la interfaz exacta.

## Bloqueos y dudas
Ninguno. Todo pasó a la segunda ronda (mypy: tipo `exc` variable entre bucles, `ingest_path`
→ `documents_dir`).
