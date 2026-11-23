# Informe 103-b · Informes de 093 y 100–103, y STATE.md de la fase 10
Estado: COMPLETADA

## Cambios
- `reports/093-rerank-por-defecto.md`: **nuevo** — informe spec 093
- `reports/100-fts-index.md`: **nuevo** — informe spec 100
- `reports/101-get-chunks.md`: **nuevo** — informe spec 101
- `reports/102-indexador-fts.md`: **nuevo** — informe spec 102
- `reports/103-buscador-fts.md`: **nuevo** — informe spec 103 (incluye decisión SearchMode)
- `reports/103-b-informes-fase10.md`: **nuevo** — este informe
- `docs/STATE.md`: fase 10 anotada, tabla `index` y `retrieval` actualizadas, `bm25.py` y `test_bm25.py` eliminados de la tabla, nueva sección "Fase 10", nota de variante `sin_rerank`

## Verificación
- `ls reports/093-*.md reports/10[0-3]-*.md reports/103-b-*.md` → 6 informes
- `git diff --stat src/ tests/ pyproject.toml uv.lock` → sin cambios (esta spec solo toca informes y STATE.md)
- `uv run pytest -q` → 647 passed
- `grep -n "bm25.py\|test_bm25" docs/STATE.md` → sin resultados
- `grep -n "class SearchMode(StrEnum)" src/docuchat/retrieval/searcher.py` → 1 resultado

## Decisiones que tomé
- La spec no detallaba exactamente cómo debía quedar STATE.md. Seguí el patrón de specs anteriores: actualicé la fila del módulo, la sección "Qué falta" y el conteo de informes.
- En `reports/103-buscador-fts.md`, "Decisiones que tomé" explica que al principio cambié `SearchMode` a una clase plain por un error de `.value` que vi al usar `mode` en `cli.py` — pero no hubo error real, solo paranoia. El cerebro lo revirtió a `StrEnum` y pasa todo.

## Bloqueos y dudas
- Ninguno.
