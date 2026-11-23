# Informe 051-b · `test_jobs.py`: no tocar el `data/` real
Estado: COMPLETADA

## Cambios
- `tests/api/test_jobs.py`:
  - `settings_docs`: añadido `monkeypatch: pytest.MonkeyPatch`, `monkeypatch.delenv(key, raising=False)` en lugar de `del os.environ[key]`, añadido `_env_file=None` a `Settings(...)`.
  - `test_una_a_la_vez`: añadido `monkeypatch`, reemplazado `del os.environ` por `monkeypatch.delenv`, añadido `_env_file=None`.
  - `test_fallo`: mismo tratamiento que arriba.
  - `test_carpeta_inexistente`: mismo tratamiento que arriba.
  - `test_get_latest`: reemplazada creación propia de `Settings()` por fixture `jobs`, eliminados `del os.environ` y `FakeEmbedder`, añadido `jobs.wait(job.id)` al final.

## Verificación
- `uv run pytest -q tests/api/test_jobs.py` → 8 passed
- `uv run pytest -q` → 462 passed
- `uv run ruff check .` → All checks passed!
- `uv run ruff format --check .` → 154 files already formatted
- `uv run mypy src` → Success: no issues found in 37 source files
- `grep -n "Settings()\|del os.environ" tests/api/test_jobs.py` → sin resultados
- `data/chroma/chroma.sqlite3` timestamp: antes=1795442145, después=1795442145 → no modificado

## Decisiones que tomé
- Se mantiene `import os` porque el bucle `for key in list(os.environ):` sigue necesitando `os.environ` para iterar las variables. El spec dice "si os deja de usarse, quitar import", pero `os` sí se usa aún.

## Bloqueos y dudas
- Ninguno.
