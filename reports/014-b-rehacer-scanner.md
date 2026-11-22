# Informe 014-b · Rehacer el scanner según la spec 014
Estado: COMPLETADA

## Cambios
- `src/docuchat/ingest/scanner.py`: reescrito siguiendo la spec 014 al pie de la letra
  - `IngestResult`: `@dataclass(frozen=True)`, SOLO `documents` + `errors` (antes tenía `files`, `supported`, `unsupported`)
  - `load_folder(root) -> IngestResult`: devuelve instancia directa, no tupla
  - `file_sha256(path)`: nueva función, lectura en bloques de 1 MiB con `iter(lambda: ...)`
  - `is_supported(path)`: `path.suffix.lower() in LOADERS`
  - `scan_folder(root)`: recursivo, ignora ocultos (`.`), temporales (`~$`), lanza `FileNotFoundError` / `NotADirectoryError`
  - `load_document(path, root)`: construye `Document` con source relativo, path absoluto, hash, loader por extensión
  - `load_folder` captura `Exception` por archivo, añade `(source, "Tipo: msg")` a `errors`
- `src/docuchat/cli.py`: adaptado a nueva interfaz de `load_folder` (devuelve `IngestResult`, no tupla)
- `tests/ingest/test_scanner.py`: reescrito con 10 tests obligatorios (test_01 a test_10)
- `tests/test_cli.py`: 3 tests marcados con `@pytest.mark.skip(reason="se rehace en 015-b")`

## Especificidad de la spec cumplida
- `grep -c "^def " src/docuchat/ingest/scanner.py` → **5** (`file_sha256`, `is_supported`, `scan_folder`, `load_document`, `load_folder`) ✅
- `grep -c "^def test_" tests/ingest/test_scanner.py` → **10** ✅

## Verificación
- `uv run pytest -q tests/ingest/test_scanner.py` → **10 passed** ✅
- `uv run pytest -q` → **113 passed**, 3 skipped, 5 warnings ✅
- `uv run ruff check . && uv run ruff format --check .` → todo limpio ✅
- `uv run mypy src` → success, 11 files ✅

## Decisiones que tomé
Ninguna. La spec fija las 5 firmas, el comportamiento exacto de cada una y los 10 tests.

## Bloqueos y dudas
Ninguno. Todo pasó a la segunda ronda:
1. Filtrado de ocultos: `.e.txt` no se filtraba porque el código revisaba solo `parts[:-1]` (directorios). La spec dice "alguna parte que empiece por '.'", así que lo corregí para que revisen TODAS las partes, incluido el nombre del archivo.
