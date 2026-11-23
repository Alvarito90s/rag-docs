# Informe 086 · Repeticiones de generación
Estado: COMPLETADA

## Cambios
- `src/docuchat/evaluation/repeats.py`: nuevo módulo con Stat, RunsSummary, stat(), outcome(), unstable_questions(), summarize_runs()
- `src/docuchat/evaluation/report.py`: nueva función render_runs_table() (8 líneas de tabla + línea de pasadas/inestables); render_results ampliado para casos con múltiples pasadas y múltiples variantes
- `src/docuchat/evaluation/run.py`: run_variant() gana parámetro `runs: int = 1`, llama evaluate_generation N veces; main() gana opción `--runs`; validación `runs < 1` antes de indexar
- `tests/evaluation/test_repeats.py`: 14 tests (stat, unstable, summarize, render_runs_table, render_results varias pasadas, run_variant con runs, main con --runs)

## Verificación
- `uv run pytest -q tests/evaluation/test_repeats.py` → 14 passed
- `uv run pytest -q` → 578 passed
- `uv run ruff check . && uv run ruff format --check .` → sin errores
- `uv run mypy src` → sin errores
- `uv run python eval/run_eval.py --help` → muestra `--runs`
- `wc -l src/docuchat/evaluation/*.py` → repeats.py 86, report.py 271, run.py 282, runner.py 258 (todos < 300)

## Decisiones que tomé
- La validación `runs < 1` se hizo incondicional al inicio de `run_variant()`, antes del bucle de indexación (como pide la spec: "antes de indexar nada").
- La columna "Palabras clave" en la tabla de categorías se oculta cuando hay varias variantes o varias pasadas (se pasa `generation=None` a `render_category_table`).
- En `unstable_questions`, si una pregunta falta en alguna pasada, se marca como inestable (append de `None`).

## Bloqueos y dudas
Sin bloqueos. Todo passed a la primera pasada de tests tras corregir:
1. Falta de import de `summarize_runs` en report.py (NameError).
2. Tipo de `outcomes` en unstable_questions para mypy (`tuple | None`).
3. Uso de `pytest.MonkeyPatch()` en vez del fixture `monkeypatch` en test 14.
