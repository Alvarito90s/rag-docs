# Informe 045-b — `ask`: no repetir la respuesta

## Spec
- **Spec:** `tasks/045-b-ask-sin-duplicar.md`
- **Fase:** 4 · Depende de: 045
- **Tipo:** Corrección mínima

## Problema
El comando `docuchat ask` mostraba la respuesta dos veces:
1. Streaming token a token con `on_token` (en `answerer.ask()`).
2. Una segunda vez con `typer.echo(answer.text)` fuera del try.

Resultado visible:
```
El código de error E-17 indica que el depósito de agua está vacío [1].
El código de error E-17 indica que el depósito de agua está vacío [1].

Fuentes:
[1] manual_cafetera.pdf, p. 7
```

## Cambios implementados

### `src/docuchat/cli.py` (función `ask`)
1. **Eliminada** la línea `typer.echo(answer.text)` (línea 263). La respuesta ya se imprime token a token durante el streaming.
2. **Simplificado** el `except`: de `(OpenAIError, EmbeddingError, APIConnectionError)` a `(OpenAIError, EmbeddingError)`. `APIConnectionError` es subclase de `OpenAIError`, así que el primero era redundante.
3. **Eliminado** el import `APIConnectionError` de `openai` (ya no se usaba en este archivo).

### `tests/test_cli.py` (`test_28_ask_answer`)
- Añadida aserción al final del bloque `try`:
  ```python
  assert result.output.count("indica depósito vacío [1].") == 1
  ```
  Verifica que la frase aparece exactamente una vez en la salida.

## Verificaciones
| Verificación | Resultado |
|---|---|
| `uv run pytest -q tests/test_cli.py` | ✅ 34 passed |
| `uv run pytest -q` | ✅ 317 passed |
| `ruff check . && ruff format --check .` | ✅ sin errores |
| `uv run mypy src` | ✅ sin issues |
| `grep "answer.text\|APIConnectionError" src/docuchat/cli.py` | ✅ sin resultados |

## Bloqueos
Ninguno.

## Notas
Corrección mínima de una sola línea eliminada + un import redundante. No hay cambios en interfaces, ni en comportamiento observable más allá de eliminar la duplicación.
