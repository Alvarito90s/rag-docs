# Informe 045 · Comando `docuchat ask`
Estado: COMPLETADA

## Cambios
- `src/docuchat/cli.py`: añadidos imports (`APIConnectionError`, `build_answerer`, `Source`), función `format_sources()` y comando `ask()` con validación de `--top-k`, manejo de errores y listado de fuentes.
- `tests/test_cli.py`: añadidos imports (`answer_mod`, `Source`, `NO_ANSWER`, `format_sources`), clase `FakeChat` y tests 28-35 (`ask_answer`, `ask_invalid_citation`, `ask_no_answer`, `ask_no_citations`, `ask_empty_index`, `ask_llm_error`, `ask_top_k`, `format_sources`).

## Verificación
- `uv run pytest -q tests/test_cli.py` → 34 passed
- `uv run pytest -q` → 317 passed
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores
- `uv run docuchat ask --help` → muestra `--top-k`

## Decisiones que tomé
- Las 7 nuevas funciones de test usan `pytest.MonkeyPatch()` inline con `try/finally` para no depender de fixtures y mantener cada test autocontenido (como hacen los tests 12, 13, 22, 25 existentes).
- `FakeChat.stream` no usa type hint en el parámetro `messages` (sin `Iterator` importado) para evitar warnings de ruff sobre imports no usados.

## Bloqueos y dudas
Ninguno. Todo limpio en el primer intento.
