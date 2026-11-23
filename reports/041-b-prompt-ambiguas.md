# Informe 041-b · Prompt: no rechazar preguntas ambiguas, y temperatura 0
Estado: COMPLETADA

## Cambios
- `src/docuchat/generation/prompts.py`: actualizado SYSTEM_PROMPT (regla 3: "ningún fragmento contiene la información pedida" en vez de "no contienen la respuesta"; nueva regla 4 para ambigüedades; antigua regla 4 pasó a regla 5)
- `src/docuchat/config.py`: `llm_temperature` default pasa de 0.2 a 0.0
- `.env.example`: `DOCUCHAT_LLM_TEMPERATURE=0` (antes 0.2)
- `tests/test_config.py`: `test_generation_defaults` espera `0.0`; `test_generation_env_override` usa `"0.7"` con esperado `0.7`
- `tests/generation/test_prompts.py`: nueva prueba `test_system_prompt_ambiguas` con checks de regla 3 y regla 4

## Verificación
- `uv run pytest -q` → 465 passed (464 + 1 nuevo), 0 failures
- `uv run ruff check .` → all checks passed
- `uv run ruff format --check .` → 156 files already formatted
- `uv run mypy src` → success: no issues found in 37 source files
- `grep -n "TEMPERATURE" .env.example` → `20:DOCUCHAT_LLM_TEMPERATURE=0`

## Decisiones que tomé
- La línea f-string de la regla 3 en el prompt supera los 100 caracteres de ruff con `{NO_ANSWER}` embebido. La dividí en dos f-strings adyacentes (misma semántica, concatenación implícita en Python), manteniendo el contenido exacto que especifica la spec.

## Bloqueos y dudas
- Ninguno. Todos los checks pasan a la primera.
