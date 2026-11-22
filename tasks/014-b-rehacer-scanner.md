# 014-b · Rehacer el scanner según la spec 014
Fase: 1 · Depende de: 013-b

## Objetivo
`scanner.py` no tiene la interfaz de la spec 014 (faltan funciones, `IngestResult` es otro y `load_folder` devuelve otra cosa). Rehazlo siguiendo `tasks/014-scanner.md` AL PIE DE LA LETRA.

## Qué está mal (no lo repitas)
- Faltan `file_sha256`, `is_supported`, `scan_folder` y `load_document`.
- `IngestResult` debe ser `@dataclass(frozen=True)` con SOLO `documents: list[Document]` y `errors: list[tuple[str, str]]`. Nada de `files`, `supported` ni `unsupported`.
- `load_folder(root) -> IngestResult`, no una tupla.
- No se filtran archivos y carpetas ocultos (`.git/`) ni los temporales `~$`.
- Los archivos no soportados NO se registran: `scan_folder` simplemente no los devuelve.
- El hash se calcula en bloques de 1 MiB, no con `read_bytes()`.
- Los tests tienen 6 casos inventados; la spec pide 10 concretos.

## Archivos
- reescribir: `src/docuchat/ingest/scanner.py`
- reescribir: `tests/ingest/test_scanner.py`

## Comportamiento
1. Lee `tasks/014-scanner.md` entera antes de empezar.
2. Las firmas, el comportamiento (puntos 1–5) y los 10 tests son los de esa spec, sin cambios. Tests `test_01_...` a `test_10_...`.
3. `cli.py` dejará de importar bien: es esperado; lo arregla la 015-b. Para que la suite pase mientras tanto, NO toques `cli.py`: marca `tests/test_cli.py` entero con `pytestmark = pytest.mark.skip(reason="se rehace en 015-b")`.

## Aceptación
- [ ] `uv run pytest -q tests/ingest/test_scanner.py` → 10 passed
- [ ] `grep -c "^def file_sha256\|^def is_supported\|^def scan_folder\|^def load_document\|^def load_folder" src/docuchat/ingest/scanner.py` → 5
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .` sin errores (mypy puede fallar SOLO en `cli.py`; anótalo)

## Fuera de alcance
`cli.py` (015-b).
