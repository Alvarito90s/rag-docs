# 023 · Cliente de embeddings por lotes
Fase: 2 · Depende de: 020, 004-c

## Objetivo
Calcular embeddings de muchos textos contra oMLX (`/v1/embeddings`) en lotes, con reintentos, detrás de una interfaz que los tests puedan sustituir por un falso.

## Archivos
- crear: `src/docuchat/index/embeddings.py`
- crear: `tests/index/test_embeddings.py`

## Interfaz
```python
from collections.abc import Sequence
from typing import Protocol

from openai import OpenAI

from docuchat.config import Settings


class EmbeddingError(RuntimeError):
    """Respuesta de embeddings incoherente."""


class Embedder(Protocol):
    """Cualquier cosa que convierta textos en vectores."""

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OpenAIEmbedder:
    """Embedder contra un servidor compatible con OpenAI (oMLX)."""

    def __init__(self, client: OpenAI, model: str, batch_size: int) -> None: ...

    @property
    def model(self) -> str: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def make_embedder(settings: Settings) -> OpenAIEmbedder:
    """Crea el embedder con la URL, clave, timeout, reintentos, modelo y lote de settings."""
```

## Comportamiento
1. `__init__`: si `batch_size <= 0` → `ValueError`. Guarda `client`, `model` y `batch_size`.
2. `embed`:
   a. Lista vacía → `[]` sin llamar al servidor.
   b. Recorre `texts` en lotes consecutivos de `batch_size`. Por lote: `resp = client.embeddings.create(model=self._model, input=list(lote))`.
   c. Ordena `resp.data` por `item.index` (el servidor puede devolverlos desordenados).
   d. Si `len(resp.data) != len(lote)` → `EmbeddingError(f"Se esperaban {len(lote)} embeddings y llegaron {len(resp.data)}")`.
   e. Devuelve los vectores (`list(item.embedding)`) de todos los lotes, en el orden de `texts`.
   f. Los `OpenAIError` NO se capturan: se propagan (el cliente ya reintenta solo).
3. `make_embedder`:
```python
client = OpenAI(
    base_url=settings.embedding_base_url,
    api_key=settings.llm_api_key or MISSING_API_KEY,
    timeout=settings.request_timeout,
    max_retries=settings.request_max_retries,
)
return OpenAIEmbedder(client, settings.embedding_model, settings.embedding_batch_size)
```
   `MISSING_API_KEY` se importa de `docuchat.env_check` (lo crea la spec 004-c). Con la clave vacía, `OpenAI(...)` lanza `OpenAIError` al CREARSE; con el marcador, el servidor responde 401, que es un error claro.
   Los reintentos con espera exponencial (errores de conexión, 408, 409, 429 y 5xx) los hace la propia librería `openai` según `max_retries`. NO implementes un bucle de reintentos propio.

## Tests obligatorios
`tests/index/test_embeddings.py` con `unittest.mock.MagicMock` y `types.SimpleNamespace`. Helper en el test: `def fake_response(vectors, order=None)` que devuelve `SimpleNamespace(data=[SimpleNamespace(index=i, embedding=v) ...])` en el orden de `order` (por defecto 0..n-1). NO cambies los valores esperados.
1. 5 textos, `batch_size=2`, `create.side_effect` con 3 respuestas → `create` llamado 3 veces; los `input` de cada llamada tienen longitudes `[2, 2, 1]`; resultado con 5 vectores en orden (usa vectores `[float(i)]`, con `i` = posición global del texto → resultado `[[0.0], [1.0], [2.0], [3.0], [4.0]]`).
2. Todas las llamadas usan `model="Qwen3-Embedding-0.6B-4bit-DWQ"` (pásalo al construir).
3. Respuesta desordenada (`index` 1 y luego 0, para 2 textos) → el resultado sale ordenado por `index`.
4. El servidor devuelve 1 embedding para un lote de 2 → `EmbeddingError`.
5. `embed([])` → `[]` y `create` no se llama.
6. `OpenAIEmbedder(client, "m", 0)` → `ValueError`.
7. `create.side_effect = openai.APIConnectionError(request=httpx.Request("POST", "http://test"))` → se propaga `APIConnectionError`.
8. `make_embedder(Settings())` (con el fixture que borra `DOCUCHAT_*` y hace `chdir(tmp_path)`): `.model == "Qwen3-Embedding-0.6B-4bit-DWQ"` y el cliente interno tiene `max_retries == 3`, `timeout == 60.0` `str(base_url) == "http://127.0.0.1:8000/v1/"` y `api_key == "sin-clave"` (clave vacía por defecto; accede con `embedder._client`).
9. `isinstance` estático: `def _check(e: Embedder) -> None: ...` llamado con un `OpenAIEmbedder` (basta con que mypy no proteste; el test solo llama a `_check`).

## Referencia de librerías
`openai` 2.x (verificado):
```python
client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="...", timeout=60.0, max_retries=3)
client.max_retries  # 3
str(client.base_url)  # "http://127.0.0.1:8000/v1/"  (añade "/" final)
resp = client.embeddings.create(model="...", input=["a", "b"])
resp.data[0].index  # int
resp.data[0].embedding  # list[float]
```

## Aceptación
- [ ] `uv run pytest -q tests/index/test_embeddings.py` pasa
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Embeddings de consultas con instrucción (Qwen3-Embedding la usa para las preguntas: llega en la Fase 3), caché de embeddings.
