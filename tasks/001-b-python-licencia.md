# 001-b · Python 3.12 fijado y LICENSE
Fase: 0 · Depende de: 001

## Objetivo
Corregir dos fallos de la 001: no existe `.python-version` (el `.venv` se ha creado con Python 3.15) y falta `LICENSE` (que `pyproject.toml` referencia).

## Archivos
- crear: `.python-version`
- crear: `LICENSE`
- regenerar: `.venv/` (no se versiona) y, si cambia, `uv.lock`

## Interfaz
`.python-version`, contenido exacto (una línea):
```
3.12
```
`LICENSE`: texto estándar de la licencia MIT, primera línea `MIT License`, línea de copyright exacta `Copyright (c) 2026 Álvaro`.

## Comportamiento
1. Crea los dos archivos.
2. Ejecuta `uv python install 3.12`, borra `.venv/` (`rm -rf .venv`) y ejecuta `uv sync`.
3. No toques `pyproject.toml`.

## Tests obligatorios
Ninguno nuevo.

## Aceptación
- [ ] `uv run python --version` → `Python 3.12.x`
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `head -1 LICENSE` → `MIT License`

## Fuera de alcance
git (lo gestiona el humano), cualquier código.
