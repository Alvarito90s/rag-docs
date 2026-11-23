# 041-b · Prompt: no rechazar preguntas ambiguas, y temperatura 0
Fase: 4 · Depende de: 054-b

## Objetivo
Arreglar el falso rechazo de la q17 ("¿Durante cuánto tiempo es gratuito el soporte técnico?"). La recuperación funciona: la página correcta sale la primera.

**Causa** (medida por el cerebro con oMLX):
- La pregunta no dice de qué producto habla, y en el contexto hay dos candidatos: el soporte de la cafetera (12 meses) y la garantía del contrato (2 años).
- El prompt solo tiene una regla para la duda: la 3, "Si los fragmentos no contienen la respuesta… No lo sé". El modelo la aplica.
- Con temperatura 0 rechaza siempre (5 de 5). Con 0,2 rechaza unas 3 de cada 5 veces, así que la evaluación tampoco es reproducible.

**Medido con la evaluación completa** (42 preguntas, chunk 800, híbrida):

| Variante | Palabras clave | Citas | Rechazo correcto | Falsos rechazos |
| --- | ---: | ---: | ---: | ---: |
| Prompt actual, t=0 (5 pasadas) | 0.969 | 1.000 | 1.000 | 1 en las 5 |
| Prompt nuevo, t=0,2 (8 pasadas) | 0.969–1.000 | 0.971–1.000 | 1.000 | 0 en 5, 1 en 3 |
| Prompt nuevo, t=0 (5 pasadas) | 1.000 | 0.971 | 1.000 | 0 en las 5 |

Con el prompt nuevo, la q17 responde por casos: "12 meses para la cafetera [1]; el contrato da 2 años de garantía [2]". Esa segunda cita no es la página esperada, por eso las citas bajan a 0.971. Es mejor respuesta que "No lo sé".

## Archivos
- modificar: `src/docuchat/generation/prompts.py` (solo `SYSTEM_PROMPT`)
- modificar: `src/docuchat/config.py` (solo el valor por defecto de `llm_temperature`)
- modificar: `.env.example` (solo `DOCUCHAT_LLM_TEMPERATURE`)
- modificar: `tests/test_config.py` y `tests/generation/test_prompts.py` (solo lo indicado abajo)

## Comportamiento
1. `SYSTEM_PROMPT` queda EXACTAMENTE así (las reglas 1 y 2 no cambian; la 3 cambia; la 4 es nueva; la antigua 4 pasa a ser la 5):
```python
SYSTEM_PROMPT = (
    "Eres DocuChat, un asistente que responde preguntas usando SOLO los fragmentos "
    "de documentos que recibes.\n"
    "Reglas:\n"
    "1. Usa únicamente la información de los fragmentos; nunca tu conocimiento propio.\n"
    "2. Cita cada dato con el número de su fragmento entre corchetes, por ejemplo [1] o [2][3].\n"
    f"3. Solo si ningún fragmento contiene la información pedida, responde exactamente: {NO_ANSWER}\n"
    "4. Si la pregunta no dice a qué se refiere y los fragmentos responden para un caso concreto, "
    "responde para ese caso y di a cuál se refiere.\n"
    "5. Responde en el idioma de la pregunta, de forma breve y directa."
)
```
2. `config.py`: `llm_temperature: float = Field(default=0.0, ge=0, le=2)`. El comentario, si lo hay, dice que 0 hace las respuestas reproducibles.
3. `.env.example`: `DOCUCHAT_LLM_TEMPERATURE=0`.

## Tests obligatorios
El cerebro autoriza cambiar SOLO estos valores esperados:
- `tests/test_config.py::test_generation_defaults`: `assert s.llm_temperature == 0.0`.
- `tests/test_config.py::test_generation_env_override`: la variable pasa a `"0.7"` y se espera `s.llm_temperature == 0.7`. Si no, el test ya no comprueba nada, porque 0 sería el valor por defecto.

AÑADE en `tests/generation/test_prompts.py`:
- `test_system_prompt_ambiguas`: `"Solo si ningún fragmento contiene la información pedida" in SYSTEM_PROMPT` y `"di a cuál se refiere" in SYSTEM_PROMPT`.

## Aceptación
- [ ] `uv run pytest -q` → 465 passed
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "TEMPERATURE" .env.example` → `DOCUCHAT_LLM_TEMPERATURE=0`
- [ ] (cerebro, con oMLX) Repetir `uv run python eval/run_eval.py`. Se espera:
  - generación: palabras clave 1.000, citas 0.971, rechazo correcto 1.000, 0 falsos rechazos;
  - recuperación: sin cambios.

## Fuera de alcance
- No toques `eval/` ni el README: los resultados nuevos y la v1.0.1 van en la siguiente spec.
- No cambies el dataset. La pregunta q17 es ambigua a propósito: así preguntan los usuarios.
