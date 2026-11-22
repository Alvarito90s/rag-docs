# 003 · Configuración con pydantic-settings
Fase: 0 · Depende de: 002

## Objetivo
Centralizar toda la configuración en `src/docuchat/config.py`, leída de variables de entorno con prefijo `DOCUCHAT_` y de un `.env` opcional.

## Archivos
- crear: `src/docuchat/config.py`
- crear: `tests/test_config.py`
- crear: `.env.example`

## Interfaz
```python
from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de DocuChat; cada campo se sobreescribe con DOCUCHAT_<NOMBRE>."""

    model_config = SettingsConfigDict(
        env_prefix="DOCUCHAT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Servidor LLM (API compatible con OpenAI: Ollama o llama.cpp)
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen3:4b"
    # Embeddings (puede ser otro servidor)
    embedding_base_url: str = "http://localhost:11434/v1"
    embedding_model: str = "bge-m3"
    request_timeout: float = Field(default=60.0, gt=0)
    # Rutas
    documents_dir: Path = Path("samples")
    data_dir: Path = Path("data")
    # Chunking
    chunk_size: int = Field(default=800, gt=0)
    chunk_overlap: int = Field(default=120, ge=0)

    @model_validator(mode="after")
    def _check_chunking(self) -> "Settings":
        """Rechaza un solape mayor o igual que el tamaño de chunk."""
        ...


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia única (cacheada) de Settings."""
    ...
```

## Comportamiento
1. `_check_chunking`: si `chunk_overlap >= chunk_size` lanza `ValueError("chunk_overlap debe ser menor que chunk_size")`; si no, devuelve `self`. (Pydantic lo convierte en `ValidationError`.)
2. `get_settings()` devuelve `Settings()`; gracias a `lru_cache` dos llamadas devuelven el mismo objeto.
3. Ningún otro módulo del proyecto debe leer `os.environ` directamente: siempre `get_settings()`.
4. `.env.example` (contenido exacto):
```
# Copia este archivo a .env y ajusta lo que necesites.
DOCUCHAT_LLM_BASE_URL=http://localhost:11434/v1
DOCUCHAT_LLM_API_KEY=ollama
DOCUCHAT_LLM_MODEL=qwen3:4b
DOCUCHAT_EMBEDDING_BASE_URL=http://localhost:11434/v1
DOCUCHAT_EMBEDDING_MODEL=bge-m3
DOCUCHAT_REQUEST_TIMEOUT=60
DOCUCHAT_DOCUMENTS_DIR=samples
DOCUCHAT_DATA_DIR=data
DOCUCHAT_CHUNK_SIZE=800
DOCUCHAT_CHUNK_OVERLAP=120
```

## Tests obligatorios
`tests/test_config.py`. Fixture `autouse` que (a) borra con `monkeypatch.delenv` toda variable de `os.environ` que empiece por `DOCUCHAT_`, (b) hace `monkeypatch.chdir(tmp_path)` para que no se lea ningún `.env` real, y (c) llama a `get_settings.cache_clear()` antes y después del test.
1. `test_defaults`: `Settings()` → `chunk_size == 800`, `chunk_overlap == 120`, `llm_model == "qwen3:4b"`, `embedding_model == "bge-m3"`, `llm_base_url == "http://localhost:11434/v1"`, `data_dir == Path("data")`, `documents_dir == Path("samples")`.
2. `test_env_override`: env `DOCUCHAT_CHUNK_SIZE=500`, `DOCUCHAT_LLM_MODEL=qwen3.6:35b` → `chunk_size == 500` (tipo `int`), `llm_model == "qwen3.6:35b"`.
3. `test_env_path`: env `DOCUCHAT_DATA_DIR=/tmp/docuchat` → `data_dir == Path("/tmp/docuchat")`.
4. `test_dotenv_file`: escribir `tmp_path / ".env"` con `DOCUCHAT_LLM_MODEL=desde-env` → `Settings().llm_model == "desde-env"`.
5. `test_env_beats_dotenv`: `.env` con `DOCUCHAT_LLM_MODEL=desde-env` y env `DOCUCHAT_LLM_MODEL=desde-os` → `"desde-os"`.
6. `test_overlap_not_smaller_than_size`: `Settings(chunk_size=100, chunk_overlap=100)` → `pytest.raises(ValidationError)`.
7. `test_invalid_values` (parametrizado): `{"chunk_size": 0}`, `{"chunk_overlap": -1}`, `{"request_timeout": 0}` → `ValidationError`.
8. `test_unknown_env_ignored`: env `DOCUCHAT_FOO=1` → `Settings()` no falla.
9. `test_get_settings_cached`: `get_settings() is get_settings()`; tras `get_settings.cache_clear()` devuelve otro objeto (`is not`).

## Referencia de librerías
pydantic-settings 2.x:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class S(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")
    port: int = 8000          # se lee de APP_PORT y se convierte a int

S()                           # variables de entorno > .env > valores por defecto
S(port=9000)                  # los kwargs tienen prioridad sobre todo
```
`ValidationError` se importa de `pydantic`: `from pydantic import ValidationError`.

## Aceptación
- [ ] `uv run pytest -q tests/test_config.py` → 11 passed (9 tests, el 7 con 3 casos)
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `DOCUCHAT_CHUNK_SIZE=500 uv run python -c "from docuchat.config import get_settings; print(get_settings().chunk_size)"` imprime `500`

## Fuera de alcance
Campos de fases posteriores (top-k, RRF, puerto de la API…): se añadirán en sus specs. No crees `.env`.
