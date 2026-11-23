# 043 · Cliente LLM con streaming
Fase: 4 · Depende de: 041

## Objetivo
Cliente de chat contra oMLX (API OpenAI) que devuelve la respuesta en streaming como trozos de texto, con el razonamiento de Qwen activable por config.

## Archivos
- crear: `src/docuchat/generation/llm_client.py`
- crear: `tests/generation/test_llm_client.py`

## Interfaz
```python
from collections.abc import Iterator, Sequence
from typing import Protocol

from openai import OpenAI

from docuchat.config import Settings
from docuchat.env_check import MISSING_API_KEY
from docuchat.generation.prompts import Message


class ChatModel(Protocol):
    """Cualquier cosa que convierta mensajes en texto por trozos."""

    def stream(self, messages: Sequence[Message]) -> Iterator[str]: ...


class OpenAIChatModel:
    """ChatModel contra un servidor compatible con OpenAI (oMLX)."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        *,
        max_tokens: int,
        temperature: float,
        thinking: bool,
    ) -> None: ...

    @property
    def model(self) -> str:
        """Nombre del modelo."""

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        """Trozos de texto de la respuesta; ignora el razonamiento."""

    def complete(self, messages: Sequence[Message]) -> str:
        """Respuesta completa, sin espacios en los extremos."""


def make_chat_model(settings: Settings) -> OpenAIChatModel:
    """Crea el cliente con URL, clave, timeout, reintentos, modelo y parámetros de settings."""
```

## Comportamiento
1. `stream` es un generador (`yield`). Llama UNA vez a:
   ```python
   self._client.chat.completions.create(
       model=self._model,
       messages=list(messages),
       max_tokens=self._max_tokens,
       temperature=self._temperature,
       stream=True,
       extra_body={"chat_template_kwargs": {"enable_thinking": self._thinking}},
   )
   ```
2. Por cada chunk: si `chunk.choices` está vacío → se salta. `piece = chunk.choices[0].delta.content`; si es `None` o `""` → se salta. Hasta emitir el primer trozo, quita los espacios iniciales con `lstrip()` (Qwen a veces empieza con `"\n\n"`); si queda vacío, se salta. Después emite los trozos tal cual.
3. El razonamiento llega en `delta.reasoning_content` (comprobado en oMLX): NO lo leas ni lo emitas.
4. Los errores de `openai` (`OpenAIError`) se propagan; no los captures.
5. `complete` → `"".join(self.stream(messages)).strip()`.
6. `make_chat_model`: `OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key or MISSING_API_KEY, timeout=settings.request_timeout, max_retries=settings.request_max_retries)` y `OpenAIChatModel(client, settings.llm_model, max_tokens=settings.llm_max_tokens, temperature=settings.llm_temperature, thinking=settings.llm_thinking)`.

## Tests obligatorios
`tests/generation/test_llm_client.py`. NO cambies los valores esperados. Cliente falso con `MagicMock`, chunks con `SimpleNamespace`:
```python
def ch(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=content))])


CHUNKS = [SimpleNamespace(choices=[]), ch(None), ch("\n\n"), ch("  Hola"), ch(""), ch(" mundo [1]."), ch(None)]
MSGS: list[Message] = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
```
Modelo de los tests: `OpenAIChatModel(client, "m", max_tokens=10, temperature=0.2, thinking=False)` con `client.chat.completions.create.return_value = iter(CHUNKS)`.
1. `list(model.stream(MSGS))` → `["Hola", " mundo [1]."]`.
2. Tras el 1, `create.call_args.kwargs == {"model": "m", "messages": MSGS, "max_tokens": 10, "temperature": 0.2, "stream": True, "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}}` y `create.call_count == 1`.
3. Con `thinking=True` → `extra_body == {"chat_template_kwargs": {"enable_thinking": True}}`.
4. `complete(MSGS)` → `"Hola mundo [1]."`.
5. Solo espacios: `iter([ch("\n"), ch("  ")])` → `list(stream(...)) == []` y `complete(...) == ""`.
6. Error: `create.side_effect = APIConnectionError(request=httpx.Request("POST", "http://test"))` → `pytest.raises(APIConnectionError)` al hacer `list(model.stream(MSGS))`.
7. Es perezoso: `gen = model.stream(MSGS)` no llama a `create` hasta `next(gen)` (`call_count == 0` antes, `1` después).
8. `make_chat_model(settings)` con el fixture `settings` de `conftest.py` → `isinstance(..., OpenAIChatModel)` y `.model == "Qwen3.6-35B-A3B-6bit"` (no hace red).

## Referencia de librerías
`openai` 2.x, streaming (comprobado contra oMLX con Qwen3.6):
```python
stream = client.chat.completions.create(model=..., messages=[...], stream=True, extra_body={...})
for chunk in stream:              # ChatCompletionChunk
    if not chunk.choices:
        continue
    texto = chunk.choices[0].delta.content   # str | None
```
`extra_body` añade claves al JSON de la petición; oMLX pasa `chat_template_kwargs` a la plantilla de Qwen. Con `enable_thinking=False` la respuesta tarda ~0,2 s en lugar de ~2 s.

## Aceptación
- [ ] `uv run pytest -q tests/generation/test_llm_client.py` → 8 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores (sin `# type: ignore`)
- [ ] `grep -n "reasoning\|except" src/docuchat/generation/llm_client.py` → sin resultados

## Fuera de alcance
No reutilices `env_check.make_client` ni `index/embeddings.py`. Nada de búsqueda ni de citas.
