# Informe 063 · Evaluación de generación
Estado: COMPLETADA

## Cambios
- `src/docuchat/evaluation/runner.py`: añadió `QuestionResult`, `GenerationReport` y `evaluate_generation()` (sin modificar código de 062)
- `tests/evaluation/test_runner_generation.py`: 6 tests obligatorios con `FakeRetriever`, `QueueChat` y `fake_clock`

## Verificación
```
pytest -q tests/evaluation/test_runner_generation.py → 6 passed
pytest -q                                         → 429 passed, 0 failures
ruff check .                                      → All checks passed
ruff format --check .                             → 138 files already formatted
mypy src                                          → Success: no issues found in 35 source files
```

## Decisiones que tomé
- `answerable` / `unanswerable` en `GenerationReport` se calculan a partir del flag `answerable` de cada `EvalQuestion`, no del estado de `no_answer` en el resultado.
- `keyword_accuracy` usa `n_answerable` como denominador (total de preguntas respondibles), no el número de preguntas con respuesta real. Así, un rechazo falso cuenta como fallo de keyword (0.0).
- `avg_first_token_s` es `None` cuando no se capturó ningún token (respuesta vacía → NO_ANSWER por defecto).
- Añadí `assert q.expected_doc is not None` / `assert q.expected_page is not None` antes de llamar a `citation_counts` para satisfacer a mypy (garantizado por el validator de `EvalQuestion`).

## Bloqueos y dudas
Ninguno. Los 6 tests pasaron a la primera (tras corregir el denominador de `keyword_accuracy` en la primera iteración).
