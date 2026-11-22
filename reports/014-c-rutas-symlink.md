# Informe 014-c · Scanner: rutas con enlaces simbólicos
Estado: COMPLETADA

## Bug corregido
`load_folder(root)` fallaba con TODOS los archivos cuando `root` se accedía vía un enlace
simbólico (p. ej. `/var` → `/private/var` en macOS, o un symlink creado manualmente).
`scan_folder` resolvía `root` con `.resolve()`, lo que eliminaba el symlink. Luego
`load_document` hacía `path.relative_to(root)` con un `root` sin resolver →
`ValueError: ... is not in the subpath`.

## Cambios en `src/docuchat/ingest/scanner.py`
1. `scan_folder`: **NO resuelve** `root`. Recorre `root.rglob("*")` tal cual. El filtro
   de ocultos se aplica a `path.relative_to(root).parts` (tuple de Path). El `"~$"`
   se comprueba solo en `path.name`, no en las partes del path relativo. Se Quita el
   `try/except ValueError` de `relative_to` (ya no es necesario).
2. `load_document`: `source = path.resolve().relative_to(root.resolve()).as_posix()`.
   Al resolver ambos lados, funciona incluso cuando `root` es un symlink.
3. `load_folder`: el `except` calcula `source` igual que en `load_document`.

## Tests añadidos
- `test_11_symlinked_root`: crea `real/` con archivos y `link → real` como symlink,
  verifica `load_folder(link)` sin errors y sources correctos `["a.txt", "sub/b.txt"]`.
- `test_12_scan_keeps_given_root`: verifica que `scan_folder(link)` devuelve rutas que
  empiezan por `link`, no por el path resuelto.

## Verificación
- `uv run pytest -q tests/ingest/test_scanner.py` → **12 passed** ✅
- `uv run python -c "... load_folder(Path(tempfile.mkdtemp())) ..."` → imprime `[]`
  (en macOS, `tempfile.mkdtemp()` → `/var/folders/...` → symlink a `/private/var/...`) ✅
- `uv run pytest -q` → **123 passed**, 5 warnings ✅
- `uv run ruff check .` → sin errores ✅
- `uv run ruff format --check .` → 70 files ✅
- `uv run mypy src` → success, 11 files ✅
- `uv run docuchat ingest samples --dry-run` → última línea `7 documentos, 22 páginas, 13612 caracteres` ✅

## Decisiones que tomé
Ninguna. La spec 014-c fija exactamente qué cambiar en cada función y los 2 tests.

## Bloqueos y dudas
Ninguno. Los 12 tests del scanner + todos los de la suite pasaron a la primera.
