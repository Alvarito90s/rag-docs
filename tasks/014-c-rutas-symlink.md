# 014-c · Scanner: rutas con enlaces simbólicos
Fase: 1 · Depende de: 015-b

## Objetivo
Corregir un bug: `load_folder(root)` falla con TODOS los archivos cuando `root` pasa por un enlace simbólico (en macOS, `/var` → `/private/var`; también cualquier carpeta enlazada). `scan_folder` devuelve rutas resueltas y `load_document` hace `path.relative_to(root)` con el `root` sin resolver → `ValueError ... is not in the subpath`. Los tests actuales no lo ven porque `tmp_path` ya viene resuelto, y la CLI lo esquiva con un `root.resolve()`.

## Archivos
- modificar: `src/docuchat/ingest/scanner.py` (solo `scan_folder`, `load_document` y `load_folder`)
- modificar: `tests/ingest/test_scanner.py` (solo AÑADIR los 2 tests de abajo)

## Comportamiento
1. `scan_folder`: NO resuelve `root`. Recorre `root.rglob("*")` tal cual, de modo que las rutas devueltas empiezan por el `root` recibido. El filtro de ocultos se aplica a `path.relative_to(root).parts`. El `"~$"` se comprueba solo en `path.name`, como dice la spec 014. Quita el `try/except ValueError`.
2. `load_document`: `source = path.resolve().relative_to(root.resolve()).as_posix()`. El resto igual.
3. `load_folder`: en el `except`, calcula `source` igual que en el punto 2.
4. No toques `cli.py`: su `root.resolve()` es inofensivo.

## Tests obligatorios
Añade a `tests/ingest/test_scanner.py` (NO cambies los 10 existentes):
11. `test_11_symlinked_root`: crea `real = tmp_path / "real"` con `a.txt` (`"hola"`) y `sub/b.txt` (`"adiós"`), y `link = tmp_path / "link"` con `link.symlink_to(real, target_is_directory=True)`. Entonces `r = load_folder(link)` → `r.errors == []` y `[d.source for d in r.documents] == ["a.txt", "sub/b.txt"]`.
12. `test_12_scan_keeps_given_root`: con la misma estructura, `scan_folder(link)` → todas las rutas cumplen `str(p).startswith(str(link))`.

## Aceptación
- [ ] `uv run pytest -q tests/ingest/test_scanner.py` → 12 passed
- [ ] `uv run python -c "import tempfile; from pathlib import Path; from docuchat.ingest.scanner import load_folder; d = Path(tempfile.mkdtemp()); (d / 'x.txt').write_text('hola'); print(load_folder(d).errors)"` imprime `[]` (en macOS `tempfile` devuelve `/var/...`, que es un enlace a `/private/var`)
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Todo lo demás.
