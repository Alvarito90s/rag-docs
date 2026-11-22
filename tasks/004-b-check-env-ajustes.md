# 004-b · check_env: ajustes de revisión
Fase: 0 · Depende de: 004

## Objetivo
Dos correcciones menores en `env_check.py` y los informes que faltan.

## Archivos
- modificar: `src/docuchat/env_check.py` (solo `check_model_listed` y `main`)
- crear: `reports/003-b-config-omlx.md`, `reports/004-check-env.md`

## Comportamiento
1. `check_model_listed`: la comprobación debe ser `model_available(model, ids)`, no `model in ids` (la función existe para eso). El resto igual.
2. `main`: el aviso se escribe como una sola cadena literal, sin concatenar:
   `print("Aviso: DOCUCHAT_LLM_API_KEY está vacía; ponla en .env.")`
   La regla 6 de AGENTS.md prohíbe LEER o ESCRIBIR el archivo `.env`; mencionarlo en un texto está permitido.
3. Escribe los dos informes que faltan con `reports/_TEMPLATE.md`, con lo que hiciste en esas specs y la verificación actual (`pytest`, `ruff`, `mypy`).
4. Regla para siempre: un informe por spec, sin excepción, también en cadenas.

## Tests obligatorios
Los existentes de `tests/test_env_check.py` deben seguir pasando sin cambios.

## Aceptación
- [ ] `grep -n "model_available(model, ids)" src/docuchat/env_check.py` devuelve una línea
- [ ] `grep -n '"\." + ' src/docuchat/env_check.py` no devuelve nada
- [ ] `ls reports/` muestra `003-b-config-omlx.md` y `004-check-env.md`
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Cualquier otra función o test.
