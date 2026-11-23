# 064 · Informe y script `eval/run_eval.py`

## Resumen
Implementación completa del renderizado de informes de evaluación y del script
`eval/run_eval.py` para ejecutar la comparativa con un solo comando.

## Archivos creados

### `src/docuchat/evaluation/report.py`
- `fmt(value, digits=3)` → `"—" | "0.844"`
- `fmt_seconds(value)` → `"—" | "0.46 s"`
- `render_retrieval_table(reports)` → tabla Markdown con una fila por informe
- `render_generation_table(report)` → tabla de métricas + sección de fallos si `keywords_ok is False`
- `render_results(...)` → Markdown completo con todos los bloques

### `src/docuchat/evaluation/run.py`
- `run_evaluation(base, questions, chunk_sizes, modes, data_root, generation_chunk_size, embedder, chat)` → `(list[RetrievalReport], GenerationReport | None)`
- `main(argv)` → CLI con `argparse`, parsea `--questions`, `--documents-dir`, `--data-root`,
  `--chunk-sizes`, `--modes`, `--generation-chunk-size`, `--skip-llm`, `--out`, `--json`.
  Escribe `results.md` (UTF-8) y `results.json` (`asdict`, `ensure_ascii=False`, `indent=2`).
  Devuelve 0 o 1 en error.

### `eval/run_eval.py`
Exactamente 6 líneas, envoltura de `main()` desde `docuchat.evaluation.run`.

### `tests/evaluation/test_report_run.py`
8 tests obligatorios:
1. `fmt` / `fmt_seconds` con valores y `None`
2. `render_retrieval_table` → 4 líneas exactas
3. `render_generation_table` → 9 líneas + sección "Fallos:"
4. `render_results` sin generación → encabezados + "No ejecutada (--skip-llm)."
5. `run_evaluation` con `generation_chunk_size=None` → `hit_at_1 ≈ 27/32`, generación `None`
6. `run_evaluation` con `chat=RefuseChat()` → `questions=42`, `false_refusals=32`, `refusal_accuracy=1.0`
7. `main` con `--skip-llm` → `rc=0`, `r.md` contiene la fila BM25, JSON con `generation=None`
8. `main` con error de servidor → `rc=1`, stderr contiene `"Error con el servidor de modelos: APIConnectionError"`

## Verificaciones

| Comando | Resultado |
| --- | --- |
| `uv run pytest -q tests/evaluation/test_report_run.py` | 8 passed |
| `uv run pytest -q` | 437 passed, 0 failures |
| `uv run ruff check . && uv run ruff format --check .` | Sin errores |
| `uv run mypy src` | Sin errores |
| `uv run python eval/run_eval.py --help` | Muestra todas las opciones |

## Notas
- Se respetó la restricción de no modificar `runner.py`, `metrics.py` ni `dataset.py`.
- Los 8 tests son el contrato: ningún valor esperado modificado.
- `eval/run_eval.py` tiene exactamente las 6 líneas especificadas.
- Se usó `FakeEmbedder` como en spec 062 y `RefuseChat` para tests de generación.
- El test 8 de error de servidor requiere parchear `make_chat_model` en
  `docuchat.generation.answer` (donde se importa), no en `llm_client`.
