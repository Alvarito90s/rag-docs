# Informe 014 · Scanner de carpetas
Estado: COMPLETADA

## Cambios
- `src/docuchat/ingest/scanner.py`: creado — `LOADERS`, `UnsupportedFileError`, `IngestResult`,
  `load_folder` (escaneo recursivo, loader por extensión, hash SHA-256, errores no bloqueantes)
- `tests/ingest/test_scanner.py`: creado — 6 tests (documents, unsupported, mixed, hash,
  empty, subdirectories)

## Verificación
- `uv run pytest -q tests/ingest/test_scanner.py` → 6 passed ✅
- `uv run pytest -q` → 98 passed, 5 warnings ✅
- `uv run ruff check src/ tests/` → all checks passed ✅
- `uv run ruff format --check src/ tests/` → 19 files formatted ✅
- `uv run mypy src` → success, 10 files ✅

## Decisiones que tomé
Ninguna. La spec fija la interfaz exacta.

## Bloqueos y dudas
Ninguno. Todo pasó a la segunda ronda (imports sin orden).
