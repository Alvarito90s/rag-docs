# 045-b · `ask`: no repetir la respuesta
Fase: 4 · Depende de: 045

## Objetivo
Corregir `docuchat ask`: la respuesta sale dos veces, primero en streaming y luego otra vez con `typer.echo(answer.text)`, que la spec no pide.

Reproducción (comprobada contra oMLX):
```
El código de error E-17 indica que el depósito de agua está vacío [1].
El código de error E-17 indica que el depósito de agua está vacío [1].

Fuentes:
[1] manual_cafetera.pdf, p. 7
```

## Archivos
- modificar: `src/docuchat/cli.py` (solo la función `ask`)
- modificar: `tests/test_cli.py` (solo `test_28_ask_answer`)

## Comportamiento
1. Borra la línea `typer.echo(answer.text)` (y su comentario). La respuesta ya se ha impreso trozo a trozo con `on_token`.
2. En el `except`, deja solo `(OpenAIError, EmbeddingError)`: `APIConnectionError` es subclase de `OpenAIError`. Si `APIConnectionError` deja de usarse en `cli.py`, quita su import.
3. Nada más cambia.

## Tests obligatorios
En `test_28_ask_answer`, AÑADE al final (sin cambiar las aserciones existentes):
```python
assert result.output.count("indica depósito vacío [1].") == 1
```

## Aceptación
- [ ] `uv run pytest -q tests/test_cli.py` → 34 passed
- [ ] `uv run pytest -q` pasa entero (317)
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "answer.text\|APIConnectionError" src/docuchat/cli.py` → sin resultados

## Fuera de alcance
Cualquier otro cambio.
