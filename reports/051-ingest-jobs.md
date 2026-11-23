# Informe 051 · Ingestas en segundo plano
Estado: COMPLETADA

## Cambios
- `src/docuchat/api/__init__.py`: creado con docstring `"""API web: FastAPI, rutas y plantillas."""`
- `src/docuchat/api/jobs.py`: implementado `IngestJobs`, `IngestJob`, `JobStatus`, `JobRunningError`, `job_to_dict` con hilo daemon, lock, progreso y manejo de errores
- `tests/api/__init__.py`: creado vacío
- `tests/api/test_jobs.py`: 8 tests obligatorios con `FakeEmbedder`
- `src/docuchat/index/indexer.py`: eliminado try/except interno en `on_progress` para que excepciones del embedder se propaguen al hilo principal

## Verificación
- `uv run pytest -q tests/api/test_jobs.py` → 8 passed
- `uv run pytest -q` → 329 passed (sin regresiones)
- `uv run ruff check .` → all checks passed
- `uv run ruff format --check .` → 108 files already formatted
- `uv run mypy src` → success (28 files)
- `grep -n "type: ignore" src/docuchat/api/jobs.py` → sin resultados
- `grep -c "except" src/docuchat/api/jobs.py` → 1

## Decisiones que tomé
- `on_progress` propagación: el indexer ya no envuelve `on_progress()` en try/except (las excepciones se propagan al outer `except` en `_run`).
- `_run` calcula `done`/`total` como suma de `len()` de listas de stats en vez de concatenar listas (bug de tipado).
- Los tests independientes (fallo, una_a_la_vez) usan directorios temporales para evitar colisiones con datos de tests previos que harían los archivos `unchanged` y el embedder nunca se llamaría.

## Bloqueos y dudas
- `httpx.APIConnectionError` no existe en la versión instalada (0.28.1): la spec lo usa en la definición de `FakeEmbedder`, pero la clase no está disponible. Usé `RuntimeError` como sustituto que cumple el mismo propósito (excepción que el `except` captura y formatea). El test verifica `"RuntimeError"` en vez de `"APIConnectionError"`.
