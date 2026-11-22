# 004 · Comprobación del entorno (check_env)
Fase: 0 · Depende de: 003

## Objetivo
Script que verifica que el servidor LLM y el de embeddings responden y tienen los modelos configurados, con salida legible y código de salida 0/1.

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
    """Indica si el modelo está en la lista, aceptando el sufijo implícito ':latest'."""

def check_model_listed(client: OpenAI, model: str, name: str) -> CheckResult:
    """Comprueba que el servidor lista el modelo."""

def check_embedding(client: OpenAI, model: str) -> CheckResult:
    """Pide un embedding de prueba y comprueba que no está vacío."""

def check_chat(client: OpenAI, model: str) -> CheckResult:
    """Pide una respuesta corta al LLM y mide el tiempo."""

def run_checks(settings: Settings, llm_client: OpenAI, embedding_client: OpenAI) -> list[CheckResult]:
    """Ejecuta las cuatro comprobaciones en orden."""

def format_result(result: CheckResult) -> str:
    """Formatea un resultado en una línea."""

def main() -> int:
    """Punto de entrada: imprime los resultados y devuelve 0 si todo va bien, 1 si no."""
```

`scripts/check_env.py` (contenido exacto):
```python
"""Comprueba que Ollama/llama.cpp responde con los modelos configurados."""

import sys

from docuchat.env_check import main

if __name__ == "__main__":
    sys.exit(main())
```

## Comportamiento
1. `make_client`: `OpenAI(base_url=base_url, api_key=settings.llm_api_key, timeout=settings.request_timeout)`.
2. `model_available`: `True` si `wanted` está en `available`, o si `wanted` no contiene `":"` y `f"{wanted}:latest"` está en `available`. En otro caso `False`.
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
9. `main`: `settings = get_settings()`; crea los dos clientes con `make_client` (uno con `llm_base_url`, otro con `embedding_base_url`); llama a `run_checks`; imprime cada línea con `print(format_result(r))`; al final imprime `"Entorno listo."` y devuelve 0 si todas son OK, o `"Hay comprobaciones fallidas."` y devuelve 1. Nunca debe salir con traceback si Ollama está apagado.

## Tests obligatorios
`tests/test_env_check.py`. Clientes falsos con `unittest.mock.MagicMock`; objetos de respuesta con `types.SimpleNamespace`. Error de conexión: `openai.APIConnectionError(request=httpx.Request("GET", "http://test"))` (`httpx` ya viene con `openai`).
1. `model_available` (parametrizado):
   `("bge-m3", ["bge-m3:latest"])` → True; `("qwen3:4b", ["qwen3:4b"])` → True; `("qwen3:4b", ["qwen3:8b"])` → False; `("bge-m3", ["bge-m3:567m"])` → False; `("bge-m3", [])` → False.
2. `check_model_listed`, `models.list.return_value = [SimpleNamespace(id="bge-m3:latest")]`:
   modelo `"bge-m3"` → ok True, detail `"bge-m3 disponible"`; modelo `"qwen3:4b"` → ok False y `"bge-m3:latest"` en detail.
3. `check_model_listed` con lista vacía → ok False, detail termina en `"disponibles: ninguno"`.
4. `check_model_listed` con `models.list.side_effect = APIConnectionError(...)` → ok False, detail empieza por `"APIConnectionError"`.
5. `check_embedding` con `data=[SimpleNamespace(embedding=[0.1] * 1024)]` → ok True, detail `"dim=1024"`, y `embeddings.create` llamado con `model="bge-m3"`.
6. `check_embedding` con `data=[]` → ok False, `"respuesta vacía"`; con `data=[SimpleNamespace(embedding=[])]` → igual.
7. `check_embedding` con `APIConnectionError` → ok False.
8. `check_chat` con `choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))]` → ok True, detail empieza por `"respuesta en "`; con `choices=[]` → ok False; con `APIConnectionError` → ok False.
9. `run_checks` con clientes falsos correctos → nombres `["llm_model", "embedding_model", "embedding", "chat"]`, todos ok. Usa `Settings()` con un `autouse` que borre las variables `DOCUCHAT_*` y haga `chdir(tmp_path)` (igual que en `test_config.py`).
10. `run_checks` con `llm_client.models.list.side_effect = APIConnectionError(...)` → devuelve igualmente 4 resultados; el primero ok False.
11. `format_result`: `CheckResult("chat", True, "x")` → `"[OK] chat: x"`; `CheckResult("chat", False, "x")` → `"[FAIL] chat: x"`.
12. `main` con `monkeypatch.setattr("docuchat.env_check.run_checks", ...)` devolviendo `[CheckResult("a", True, "x")]` → devuelve 0 y `capsys` contiene `"Entorno listo."`; devolviendo uno OK y uno FAIL → devuelve 1 y contiene `"Hay comprobaciones fallidas."`. Parchea también `make_client` para que devuelva un `MagicMock`.

## Referencia de librerías
`openai` 2.x contra Ollama (`/v1`, compatible con OpenAI):
```python
from openai import OpenAI, OpenAIError, APIConnectionError

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama", timeout=60.0)

ids = [m.id for m in client.models.list()]          # p. ej. ["bge-m3:latest", "qwen3:4b"]

emb = client.embeddings.create(model="bge-m3", input=["texto"])
vector: list[float] = emb.data[0].embedding

resp = client.chat.completions.create(
    model="qwen3:4b",
    messages=[{"role": "user", "content": "Hola"}],
    max_tokens=200,
)
texto = resp.choices[0].message.content             # str | None

# Jerarquía de errores: OpenAIError ⊃ APIError ⊃ APIConnectionError, APIStatusError (404, 500…)
```
Crear el cliente `OpenAI(...)` no hace ninguna llamada de red.

## Aceptación
- [ ] `uv run pytest -q tests/test_env_check.py` pasa
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] Con Ollama APAGADO: `uv run python scripts/check_env.py; echo $?` → 4 líneas `[FAIL]`, `Hay comprobaciones fallidas.`, `1`, sin traceback
- [ ] (humano) Con Ollama encendido y los modelos descargados → 4 líneas `[OK]` (embedding `dim=1024`), `Entorno listo.`, `0`

## Fuera de alcance
No descargues modelos (`ollama pull`) ni arranques Ollama. Nada de `rich`/Typer todavía. No reutilices este cliente como cliente de embeddings de la app (llega en la Fase 2).
