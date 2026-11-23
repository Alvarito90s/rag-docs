# Informe 085 — Juez LLM opcional para verificar fidelidad de respuestas

## Resumen

Implementé el juez de fidelidad: un LLM que recibe la pregunta, la respuesta y los fragmentos citados, y devuelve un veredicto JSON indicando si las afirmaciones están respaldadas por los fragmentos. Se activa con `--judge` y es opcional: sin esa opción, la evaluación no cambia.

## Archivos creados

| Archivo | Líneas | Descripción |
| --- | ---: | --- |
| `src/docuchat/evaluation/judge.py` | 90 | Módulo completo con JUDGE_PROMPT, NO_CITATIONS, Verdict, build_judge_messages(), parse_verdict(), cited_passages(), Judge |

## Archivos modificados

| Archivo | Cambios |
| --- | --- |
| `src/docuchat/evaluation/runner.py` | `QuestionResult` → campos `faithful` + `unsupported`. `GenerationReport` → campos `judged`, `unjudged`, `faithfulness`. `evaluate_generation()` → parámetro `judge`. |
| `src/docuchat/evaluation/report.py` | `render_generation_table()` → fila "Fidelidad (juez)" + sección "Sin respaldo según el juez:". `render_results()` → parámetro `judge_model` con nota cuando juez == modelo que responde. |
| `src/docuchat/evaluation/run.py` | `run_variant()` → parámetro `judge`. `main()` → opciones `--judge` + `--judge-model`, creación de `Judge(make_chat_model(...))`, error si `--judge` + `--skip-llm`. |
| `tests/evaluation/test_judge.py` | 25 tests (17 funciones + 6 parametrizados) cubriendo toda la funcionalidad. |
| `docs/STATE.md` | Actualizado con spec 085. |

## Resultados

- `uv run pytest -q tests/evaluation/test_judge.py` → **25 passed**
- `uv run pytest -q` → **564 passed** (todos los tests anteriores + los nuevos)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores
- `uv run python eval/run_eval.py --help` → muestra `--judge` y `--judge-model`
- Todos los archivos de `src/docuchat/evaluation/*.py` bajo 300 líneas (máx: 267)

## Detalles de implementación

### judge.py
- `JUDGE_PROMPT` en dos literales concatenadas para evitar E501
- `parse_verdict()` robusto: extrae JSON por `{`/`}`, valida tipo dict, `supported` bool, `unsupported` lista de str
- `cited_passages()` recorre `answer.sources` sin repetir números, filtra por rango válido
- `Judge.judge()` sin fragmentos → `Verdict(False, [NO_CITATIONS])` sin llamar al LLM

### runner.py
- `evaluate_generation()` llama al juez solo cuando `judge is not None` y `no_answer is False`
- `judged` = respuestas con veredicto, `unjudged` = respuestas juzgables sin veredicto legible
- `faithfulness = ratio(respaldadas, judged)`, None si judged == 0

### report.py
- Fila "Fidelidad (juez)" se inserta después de "Falsos rechazos"
- Sección "Sin respaldo según el juez:" tras "Fallos:", texto recortado a 160 chars
- `render_results()` con `judge_model` → nota cuando juez == modelo que responde

### run.py
- `--judge` + `--skip-llm` → `parser.error()`
- `--judge-model` hereda `DOCUCHAT_LLM_MODEL` por defecto
- `make_chat_model` parcheable en tests vía `docuchat.evaluation.run.make_chat_model`

## Bloqueos

Ninguno. Todo implementado según spec.
