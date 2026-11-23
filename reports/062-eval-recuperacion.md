# Informe 062 · Evaluación de la recuperación

## Resumen

Implementado el módulo `runner.py` para la evaluación de recuperación y sus tests.

## Archivos creados / modificados

| Archivo | Acción | Descripción |
| --- | --- | --- |
| `src/docuchat/evaluation/runner.py` | Creado | `eval_settings`, `build_eval_index`, `evaluate_retrieval`, `RetrievalReport` |
| `tests/evaluation/test_runner_retrieval.py` | Creado | 10 tests obligatorios con FakeEmbedder |
| `docs/STATE.md` | Modificado | Actualizado con la spec 062 |

## Funcionalidad

- **`eval_settings(base, data_root, chunk_size)`**: devuelve una copia de `Settings` con `data_dir` en una carpeta aislada (`cs{chunk_size}`), `chunk_size` y `chunk_overlap` (15 %). Cada tamaño de chunk tiene su propio índice, sin interferir con `data/` de la app.
- **`build_eval_index(settings, embedder)`**: limpia el índice con `reset_index`, indexa desde cero `documents_dir`, propaga errores (lanza `RuntimeError`), devuelve `chunk_count`.
- **`evaluate_retrieval(searcher, questions, mode, *, chunk_size, chunks)`**: filtra solo preguntas con `answerable`, busca cada una con `SEARCH_DEPTH=10`, calcula Hit@1, Hit@5, MRR mediante `first_hit_rank`, `hit_at`, `mean_reciprocal_rank`. Registra misses (ids sin acierto en top 5).

## Tests (10)

| # | Nombre | Qué cubre |
|---|---|---|
| 1 | `eval_settings` | data_dir, chunk_size, chunk_overlap, llm_model preservado |
| 2 | `build_eval_index` (parametrizado) | 500→45, 800→26, 1200→23 chunks |
| 3 | Reindexar misma carpeta | dos llamadas → mismo resultado (empieza de cero) |
| 4 | BM25 con 800 | hit_at_1≈27/32, hit_at_5=1.0, mrr≈0.9089, misses=[] |
| 5 | BM25 con 1200 | hit_at_1≈28/32, mrr≈0.9245 |
| 6 | Solo answerable | [q01, u01] → questions=1 |
| 7 | Misses | pregunta inexistente → misses=["x01"] |
| 8 | Error indexación | PDF roto → RuntimeError con "roto.pdf" |
| 9 | RetrievalReport inmutable | frozen=True, no se puede mutar |
| 10 | SEARCH_DEPTH | constante = 10, chunks coherentes |

## Verificaciones

- `uv run pytest -q tests/evaluation/test_runner_retrieval.py` → **12 passed** (10 funciones + 3 parametrizadas)
- `uv run pytest -q` → **423 passing** (411 preexistentes + 12 nuevos)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores

## Bloqueos

Ninguno.
