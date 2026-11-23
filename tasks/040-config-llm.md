# 040 · Config de generación
Fase: 4 · Depende de: 033-b

## Objetivo
Añadir a `Settings` los parámetros del LLM para responder (tokens, temperatura, razonamiento) y el tamaño máximo del contexto.

## Archivos
- modificar: `src/docuchat/config.py` (solo AÑADIR campos)
- modificar: `.env.example` (solo AÑADIR 4 líneas al final)
- modificar: `tests/test_config.py` (solo AÑADIR tests)

## Interfaz
En `Settings`, después de `query_instruction`:
```python
# Generación
llm_max_tokens: int = Field(default=1024, gt=0)
llm_temperature: float = Field(default=0.2, ge=0, le=2)
llm_thinking: bool = False  # razonamiento de Qwen (más lento); se pasa como enable_thinking
context_max_chars: int = Field(default=6000, gt=0)  # tope del contexto que se manda al LLM
```
`.env.example`, al final:
```
DOCUCHAT_LLM_MAX_TOKENS=1024
DOCUCHAT_LLM_TEMPERATURE=0.2
DOCUCHAT_LLM_THINKING=false
DOCUCHAT_CONTEXT_MAX_CHARS=6000
```

## Comportamiento
1. Sin validadores nuevos. No toques los existentes.
2. `context_max_chars` se mide en caracteres, no en tokens (aproximación suficiente: 6000 caracteres ≈ 1500 tokens, y caben los 5 chunks de 800).

## Tests obligatorios
Añadir a `tests/test_config.py` (usa el fixture autouse existente). NO cambies los valores esperados.
1. `test_generation_defaults`: `llm_max_tokens == 1024`, `llm_temperature == 0.2`, `llm_thinking is False`, `context_max_chars == 6000`.
2. `test_generation_env_override`: env `DOCUCHAT_LLM_THINKING=true`, `DOCUCHAT_LLM_TEMPERATURE=0` → `llm_thinking is True`, `llm_temperature == 0.0`.
3. `test_invalid_generation_values` (parametrizado, 4 casos): `{"llm_max_tokens": 0}`, `{"llm_temperature": -0.1}`, `{"llm_temperature": 2.5}`, `{"context_max_chars": 0}` → `ValidationError`.

## Aceptación
- [ ] `uv run pytest -q tests/test_config.py` → 28 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
Cualquier código de generación (specs 041–045). No leas ni edites `.env`.
