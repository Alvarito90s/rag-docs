# Informe 027 · `docuchat ingest` indexa de verdad
Estado: COMPLETADA

## Cambio
- `src/docuchat/cli.py`: añadida función `stats_line()`, modificado comando `ingest` con
  opción `--reset`, flujo de indexación con `Progress` de Rich y manejo de errores
  (`EmbeddingModelMismatchError`, `OpenAIError`, `EmbeddingError`)
- `tests/test_cli.py`: borrado `test_03_no_dry_run`, añadidos tests 09–17 con
  `FakeEmbedder` y fixture `index_env` (parchea `build_indexer` en `docuchat.cli`)

## Implementación
- `stats_line`: formatea `IndexStats` como `"N añadidos, N actualizados, N sin cambios, N eliminados, N con errores"`
- `ingest` sin `--dry-run`: resuelve carpeta → aplica `--reset` → construye `Indexer` → indexa con barra `Progress(transient=True)` → imprime stats y chunks → imprime errores → exit 1 si hay errores
- `ingest` con `--dry-run`: comportamiento original (tabla + resumen), `--reset` se ignora
- `build_indexer` parcheable en `docuchat.cli` para tests (parchea la referencia en el módulo)

## Verificación
- `uv run pytest -q tests/test_cli.py` → **16 passed** ✅
- `uv run pytest -q` → **216 passed** ✅
- `uv run ruff check .` → sin errores ✅
- `uv run ruff format --check .` → 73 files ✅
- `uv run mypy src` → success, 18 files ✅
- `grep "Usa --dry-run" cli.py test_cli.py` → sin resultados ✅

## Decisiones que tomé
Ninguna. La spec fija la interfaz exacta, el comportamiento paso a paso,
los tests con valores esperados y los criterios de aceptación.

## Bloqueos y dudas
Ninguno. Todos los tests pasaron en el primer intento tras añadir el import
faltante de `stats_line` en los tests.
