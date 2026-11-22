# 003-b · Config: valores por defecto de oMLX
Fase: 0 · Depende de: 003

## Objetivo
Cambiar los valores por defecto de `Settings` del servidor Ollama al servidor oMLX del humano. La spec 003 ya está actualizada; esta corrige lo que se implementó con la versión antigua.

## Archivos
- modificar: `src/docuchat/config.py` (solo los 6 valores por defecto de abajo y el comentario)
- modificar: `.env.example` (solo esas 6 líneas y la primera línea de comentario)
- modificar: `tests/test_config.py` (solo `test_defaults` y `test_env_override`)

## Interfaz
En `Settings`, exactamente:
```python
    # Servidor LLM (oMLX local, API compatible con OpenAI)
    llm_base_url: str = "http://127.0.0.1:8000/v1"
    llm_api_key: str = ""  # secreto: se pone en .env, nunca en el código
    llm_model: str = "Qwen3.6-35B-A3B-6bit"
    # Embeddings (mismo servidor y misma clave por defecto)
    embedding_base_url: str = "http://127.0.0.1:8000/v1"
    embedding_model: str = "Qwen3-Embedding-0.6B-4bit-DWQ"
```

## Comportamiento
1. `.env.example`: primera línea `# Copia este archivo a .env y pon tu clave de oMLX. .env NO se versiona.` y:
```
DOCUCHAT_LLM_BASE_URL=http://127.0.0.1:8000/v1
DOCUCHAT_LLM_API_KEY=
DOCUCHAT_LLM_MODEL=Qwen3.6-35B-A3B-6bit
DOCUCHAT_EMBEDDING_BASE_URL=http://127.0.0.1:8000/v1
DOCUCHAT_EMBEDDING_MODEL=Qwen3-Embedding-0.6B-4bit-DWQ
```
   El resto de líneas no cambia.
2. No crees ni leas `.env`.

## Tests obligatorios
`tests/test_config.py`:
1. `test_defaults`: `llm_model == "Qwen3.6-35B-A3B-6bit"`, `embedding_model == "Qwen3-Embedding-0.6B-4bit-DWQ"`, `llm_base_url == "http://127.0.0.1:8000/v1"`, `llm_api_key == ""`; el resto de asserts igual que antes.
2. `test_env_override`: usar `DOCUCHAT_LLM_MODEL=Qwen3.5-4B-8bit` → `llm_model == "Qwen3.5-4B-8bit"`.

## Aceptación
- [ ] `uv run pytest -q tests/test_config.py` → 11 passed
- [ ] `grep -rniE 'ollama|11434|bge|qwen3:' src tests .env.example` no devuelve nada
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
Cualquier otro campo, validador o test.
