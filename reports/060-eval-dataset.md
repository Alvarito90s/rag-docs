# Informe 060 · Dataset de evaluación
Estado: COMPLETADA

## Cambios
- `eval/questions.jsonl`: copia exacta de `tasks/assets/060/questions.jsonl` (42 preguntas, 32 con respuesta, 10 sin respuesta)
- `src/docuchat/evaluation/__init__.py`: docstring del paquete
- `src/docuchat/evaluation/dataset.py`: `EvalQuestion` (Pydantic frozen), `DatasetError`, `load_questions()` con validación de coherencia, JSON roto, ids repetidos y archivo vacío
- `tests/evaluation/__init__.py`: vacío
- `tests/evaluation/test_dataset.py`: 11 tests (carga, coherencia samples, copia exacta, creación sin respuesta, _check_consistency parametrizado×3, JSON roto, id repetido, archivo vacío, líneas blancas ignoradas)

## Verificación
- `uv run pytest -q tests/evaluation/test_dataset.py` → **11 passed**
- `uv run pytest -q` → **398 passed, 0 failures**
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 130 files already formatted
- `uv run mypy src` → Success: no issues found in 33 source files
- `cmp eval/questions.jsonl tasks/assets/060/questions.jsonl` → sin salida

## Decisiones que tomé
- El validador `_check_consistency` reporta los campos faltantes/extras de forma específica (`missing.join`, `extra.join`) para que el mensaje incluya exactamente el campo que falla en cada caso parametrizado.
- `load_questions` captura `Exception` (no solo `json.JSONDecodeError`) para también atrapar `ValidationError` de Pydantic y envolverlo en `DatasetError`.
- Las preguntas de test temporales usan `{id, question, answerable, expected_doc, expected_page, answer_keywords}` completos para que la creación de `EvalQuestion` no falle antes del error que se quiere probar.

## Bloqueos y dudas
Sin bloqueos. Todas las verificaciones pasan a la primera.
