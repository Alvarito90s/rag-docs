# Informe 113 · Contexto de metadatos, sin LLM y activo por defecto
Estado: COMPLETADA

## Cambios
- `src/docuchat/config.py`: 3 nuevos campos (`contextual_meta_enabled`, `contextual_meta_head_chars`, `contextual_meta_max_chars`) + comentario de sección actualizado
- `src/docuchat/index/contextualizer.py`: `ChunkContextualizer` (Protocol), `first_sentence()`, `MetaContextualizer`, `make_meta_contextualizer()`
- `src/docuchat/index/indexer.py`: tipo `ChunkContextualizer | None`, import de `make_meta_contextualizer`, lógica de `build_indexer` decide entre LLM y metadatos
- `src/docuchat/evaluation/variants.py`: variante `"sin_contexto"` añadida
- `tests/conftest.py`: fixture autouse `_sin_contexto_de_metadatos` para que tests existentes no reciban contexto por defecto
- `tests/index/test_meta_context.py`: 11 tests nuevos

## Verificación
```
686 passed, 5 warnings in 14.36s
All checks passed! (ruff check)
223 files already formatted (ruff format)
Success: no issues found in 44 source files (mypy)
```
- contextualizer.py: 218 líneas (< 300) ✓
- indexer.py: 237 líneas (< 300) ✓
- `git diff --stat tests/` solo muestra conftest.py; test_meta_context.py es nuevo sin tracked ✓

## Decisiones que tomé
- Usé typing.Protocol, que es donde está Protocol en Python.
- En el test `test_indexer_con_metadatos`, usé `r[0]` para obtener chunk_id de `fts.search()` porque devuelve tuples, consistente con `test_index_text.py`.

## Bloqueos y dudas
- Ningún bloqueo. Todos los tests pasan, lint y tipos limpios.
