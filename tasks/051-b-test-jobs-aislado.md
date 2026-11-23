# 051-b · `test_jobs.py`: no tocar el `data/` real
Fase: 5 · Depende de: 051

## Objetivo
`test_get_latest` crea `Settings()` sin `data_dir`. Con el cwd en la raíz del repo, eso apunta a `data/`, el índice real. Además lanza una ingesta con `FakeEmbedder` (vectores de 3 dimensiones) y no la espera.

Resultado, comprobado por el cerebro: cada `uv run pytest` reescribe `data/chroma`. Después, la app falla al preguntar con `InvalidArgumentError: Collection expecting embedding with dimension of 3, got 1024`.

Además, los tests de este archivo borran variables con `del os.environ[...]`. Eso se filtra al resto de la suite.

## Archivos
- modificar: `tests/api/test_jobs.py` (solo `test_get_latest`, el fixture `settings_docs` y los tests que usan `del os.environ`)

## Comportamiento
1. `test_get_latest` usa el fixture `jobs` (que ya trabaja en `tmp_path`) en vez de crear `Settings()`. Las aserciones son las mismas. Al final, `jobs.wait(job.id)`, para que el hilo no siga vivo después del test.
2. En todo el archivo, cambia `for key in list(os.environ): ... del os.environ[key]` por `monkeypatch.delenv(key)`, añadiendo `monkeypatch: pytest.MonkeyPatch` a la firma del fixture o test. Si `os` deja de usarse, quita su import.
3. Todos los `Settings(...)` del archivo reciben también `_env_file=None`, para que los tests no lean el `.env` del humano.
4. No cambies ninguna aserción ni ningún valor esperado.

## Tests obligatorios
No hay tests nuevos: el número de tests no cambia (462).

## Aceptación
- [ ] `uv run pytest -q tests/api/test_jobs.py` pasa
- [ ] `uv run pytest -q` → 462 passed
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "Settings()\|del os.environ" tests/api/test_jobs.py` → sin resultados
- [ ] La suite ya no toca `data/`. Comprueba que estos dos números salen iguales (si no existe `data/chroma`, anótalo en el informe):
  - `stat -f %m data/chroma/chroma.sqlite3` antes de `uv run pytest -q`;
  - el mismo comando después.

## Fuera de alcance
Cualquier otro archivo. Si ves el mismo patrón en otros tests, anótalo en el informe; no lo corrijas.
