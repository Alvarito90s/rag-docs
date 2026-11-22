# 004 · Comprobación del entorno (check_env)
Fase: 0 · Depende de: 003

## Objetivo
Script que verifica que el servidor de modelos (oMLX) responde, tanto para el LLM como para los embeddings, y tienen los modelos configurados, con salida legible y código de salida 0/1.

## Archivos
- crear: `src/docuchat/env_check.py`
- crear: `scripts/check_env.py`
- crear: `tests/test_env_check.py`

## Interfaz
`src/docuchat/env_check.py`:
```python
import time
from collections.abc import Iterable
from dataclasses import dataclass

from openai import OpenAI, OpenAIError

from docuchat.config import Settings, get_settings


@dataclass(frozen=True)
class CheckResult:
    """Resultado de una comprobación."""

    name: str
    ok: bool
    detail: str


def make_client(base_url: str, settings: Settings) -> OpenAI:
    """Crea un cliente OpenAI contra base_url con la api_key y el timeout de settings."""


def model_available(wanted: str, available: Iterable[str]) -> bool:
    """Indica si el id del modelo está exactamente en la lista."""


def check_model_listed(client: OpenAI, model: str, name: str) -> CheckResult:
    """Comprueba que el servidor lista el modelo."""


def check_embedding(client: OpenAI, model: str) -> CheckResult:
    """Pide un embedding de prueba y comprueba que no está vacío."""


def check_chat(client: OpenAI, model: str) -> CheckResult:
    """Pide una respuesta corta al LLM y mide el tiempo."""


def run_checks(
    settings: Settings, llm_client: OpenAI, embedding_client: OpenAI
) -> list[CheckResult]:
    """Ejecuta las cuatro comprobaciones en orden."""


def format_result(result: CheckResult) -> str:
    """Formatea un resultado en una línea."""


def main() -> int:
    """Punto de entrada: imprime los resultados y devuelve 0 si todo va bien, 1 si no."""
```

`scripts/check_env.py` (contenido exacto):
```python
"""Comprueba que oMLX responde con los modelos configurados."""

import sys

from docuchat.env_check import main

if __name__ == "__main__":
    sys.exit(main())
```

## Comportamiento
1. `make_client`: `OpenAI(base_url=base_url, api_key=settings.llm_api_key, timeout=settings.request_timeout)`.
2. `model_available`: `True` si `wanted` está en `available` (comparación exacta, sensible a mayúsculas). En otro caso `False`.
3. `check_model_listed`: `ids = [m.id for m in client.models.list()]`.
   - OK → `CheckResult(name, True, f"{model} disponible")`.
   - No está → `CheckResult(name, False, f"{model} no encontrado; disponibles: {lista}")`, con `lista = ", ".join(sorted(ids))` o `"ninguno"` si está vacía.
4. `check_embedding`: `client.embeddings.create(model=model, input=["prueba de embeddings"])`. Nombre `"embedding"`.
   - `data` vacío o vector vacío → `ok=False`, detail `"respuesta vacía"`.
   - Si no → `ok=True`, detail `f"dim={len(vector)}"`.
5. `check_chat`: `client.chat.completions.create(model=model, messages=[{"role": "user", "content": "Responde solo con la palabra OK."}], max_tokens=200)`, medido con `time.perf_counter()`. Nombre `"chat"`.
   - `choices` vacío → `ok=False`, detail `"respuesta vacía"`.
   - Si no → `ok=True`, detail `f"respuesta en {segundos:.1f} s"`. NO compruebes el contenido del texto (los modelos con razonamiento pueden devolverlo vacío).
6. En las tres funciones `check_*`, cualquier `OpenAIError` se captura y devuelve `ok=False`, detail `f"{type(e).__name__}: {e}"`. No captures `Exception` genérica.
7. `run_checks` devuelve, en este orden y ejecutando siempre las cuatro aunque falle alguna:
   `check_model_listed(llm_client, settings.llm_model, "llm_model")`,
   `check_model_listed(embedding_client, settings.embedding_model, "embedding_model")`,
   `check_embedding(embedding_client, settings.embedding_model)`,
   `check_chat(llm_client, settings.llm_model)`.
8. `format_result`: `f"[OK] {name}: {detail}"` o `f"[FAIL] {name}: {detail}"`.
9. `main`: `settings = get_settings()`; si `settings.llm_api_key` está vacía, imprime primero `"Aviso: DOCUCHAT_LLM_API_KEY está vacía; ponla en .env."` (y sigue). Después crea los dos clientes con `make_client` (uno con `llm_base_url`, otro con `embedding_base_url`); llama a `run_checks`; imprime cada línea con `print(format_result(r))`; al final imprime `"Entorno listo."` y devuelve 0 si todas son OK, o `"Hay comprobaciones fallidas."` y devuelve 1. Nunca debe salir con traceback si el servidor está apagado o la clave es incorrecta.

## Tests obligatorios
`tests/test_env_check.py`. Clientes falsos con `unittest.mock.MagicMock`; objetos de respuesta con `types.SimpleNamespace`. Error de conexión: `openai.APIConnectionError(request=httpx.Request("GET", "http://test"))` (`httpx` ya viene con `openai`).
1. `model_available` (parametrizado):
   `("Qwen3.6-35B-A3B-6bit", ["Qwen3.6-35B-A3B-6bit", "Qwen3.5-4B-8bit"])` → True; `("Qwen3.6-35B-A3B-6bit", ["Qwen3.5-4B-8bit"])` → False; `("qwen3.6-35b-a3b-6bit", ["Qwen3.6-35B-A3B-6bit"])` → False; `("Qwen3.6-35B-A3B-6bit", [])` → False.
2. `check_model_listed`, `models.list.return_value = [SimpleNamespace(id="Qwen3.6-35B-A3B-6bit")]`:
   modelo `"Qwen3.6-35B-A3B-6bit"` → ok True, detail `"Qwen3.6-35B-A3B-6bit disponible"`; modelo `"Qwen3-Embedding-0.6B-4bit-DWQ"` → ok False y `"Qwen3.6-35B-A3B-6bit"` en detail.
3. `check_model_listed` con lista vacía → ok False, detail termina en `"disponibles: ninguno"`.
4. `check_model_listed` con `models.list.side_effect = APIConnectionError(...)` → ok False, detail empieza por `"APIConnectionError"`.
5. `check_embedding` con `data=[SimpleNamespace(embedding=[0.1] * 1024)]` → ok True, detail `"dim=1024"`, y `embeddings.create` llamado con `model="Qwen3-Embedding-0.6B-4bit-DWQ"`.
6. `check_embedding` con `data=[]` → ok False, `"respuesta vacía"`; con `data=[SimpleNamespace(embedding=[])]` → igual.
7. `check_embedding` con `APIConnectionError` → ok False.
8. `check_chat` con `choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))]` → ok True, detail empieza por `"respuesta en "`; con `choices=[]` → ok False; con `APIConnectionError` → ok False.
9. `run_checks` con clientes falsos correctos → nombres `["llm_model", "embedding_model", "embedding", "chat"]`, todos ok. Usa `Settings()` con un `autouse` que borre las variables `DOCUCHAT_*` y haga `chdir(tmp_path)` (igual que en `test_config.py`).
10. `run_checks` con `llm_client.models.list.side_effect = APIConnectionError(...)` → devuelve igualmente 4 resultados; el primero ok False.
11. `format_result`: `CheckResult("chat", True, "x")` → `"[OK] chat: x"`; `CheckResult("chat", False, "x")` → `"[FAIL] chat: x"`.
12. `main` con `monkeypatch.setattr("docuchat.env_check.run_checks", ...)` devolviendo `[CheckResult("a", True, "x")]` → devuelve 0 y `capsys` contiene `"Entorno listo."`; devolviendo uno OK y uno FAIL → devuelve 1 y contiene `"Hay comprobaciones fallidas."`. Parchea también `make_client` para que devuelva un `MagicMock`.
13. `main` con env `DOCUCHAT_LLM_API_KEY` sin definir → la salida contiene `"Aviso: DOCUCHAT_LLM_API_KEY está vacía"`; con `DOCUCHAT_LLM_API_KEY=x` → no lo contiene (mismos parches que el 12, y `get_settings.cache_clear()` antes).

## Referencia de librerías
`openai` 2.x contra oMLX (`/v1`, compatible con OpenAI; exige API key):
```python
from openai import OpenAI, OpenAIError, APIConnectionError

client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key=settings.llm_api_key, timeout=60.0)

ids = [m.id for m in client.models.list()]  # p. ej. ["Qwen3.6-35B-A3B-6bit", "Qwen3.5-4B-8bit"]

emb = client.embeddings.create(model="Qwen3-Embedding-0.6B-4bit-DWQ", input=["texto"])
vector: list[float] = emb.data[0].embedding

resp = client.chat.completions.create(
    model="Qwen3.6-35B-A3B-6bit",
    messages=[{"role": "user", "content": "Hola"}],
    max_tokens=200,
)
texto = resp.choices[0].message.content  # str | None

# Jerarquía de errores: OpenAIError ⊃ APIError ⊃ APIConnectionError, APIStatusError (401, 404, 500…)
# Clave errónea o vacía -> AuthenticationError (subclase de APIStatusError).
```
Crear el cliente `OpenAI(...)` no hace ninguna llamada de red. Con `api_key=""` no falla al crearse; falla con 401 al llamar.

## Aceptación
- [ ] `uv run pytest -q tests/test_env_check.py` pasa
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] Servidor inexistente (NO apagues oMLX, lo estás usando tú): `DOCUCHAT_LLM_BASE_URL=http://127.0.0.1:9/v1 DOCUCHAT_EMBEDDING_BASE_URL=http://127.0.0.1:9/v1 uv run python scripts/check_env.py; echo $?` → 4 líneas `[FAIL]`, `Hay comprobaciones fallidas.`, `1`, sin traceback
- [ ] (humano) Con `.env` con la clave y el modelo de embeddings descargado en oMLX → 4 líneas `[OK]` (embedding `dim=1024`), `Entorno listo.`, `0`

## Fuera de alcance
No descargues modelos, no toques la configuración de oMLX y no leas `.env` ni `~/.omlx/`. Nada de `rich`/Typer todavía. No reutilices este cliente como cliente de embeddings de la app (llega en la Fase 2).
