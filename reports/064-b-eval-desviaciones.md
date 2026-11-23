# Informe 064-b · Evaluación: tres desviaciones de las specs 063/064
Estado: COMPLETADA

## Cambios
- `src/docuchat/evaluation/run.py`: Cambiado `except Exception` por `except (OpenAIError, EmbeddingError) as e`; añadidos imports de `OpenAIError` (openai) y `EmbeddingError` (docuchat.index.embeddings). Otras excepciones se propagan.
- `src/docuchat/evaluation/report.py`: En `render_retrieval_table`, eliminado recorte a 5: `r.misses[:5]` → `r.misses`.
- `src/docuchat/evaluation/runner.py`: En `evaluate_generation`, las preguntas con respuesta siempre calculan `keywords_ok` y citas aunque el modelo diga "No lo sé". Se elimina `if not no:` del bloque answerable.
- `tests/evaluation/test_runner_generation.py`: Añadido test 7 (falso rechazo con NO_ANSWER).
- `tests/evaluation/test_report_run.py`: Añadidos test 9 (fallos sin recortar) y test 10 (error no servidor se propaga).

## Verificación
```
uv run pytest -q tests/evaluation → 53 passed
uv run pytest -q → 440 passed
uv run ruff check . → All checks passed!
uv run ruff format --check . → 144 files already formatted
uv run mypy src → Success: no issues found in 37 source files
grep -n "except Exception\|misses\[:\]" src/docuchat/evaluation/*.py → sin resultados
```

## Decisiones que tomé
Ninguna. La spec especificaba exactamente los cambios.

## Bloqueos y dudas
Ninguno.
