# Informe 082 · Preguntas de evaluación v2 con categoría
Estado: COMPLETADA

## Cambios
- `src/docuchat/evaluation/dataset.py`: añadido campo `category: str = Field(default="general", pattern=r"^[a-z_]+$")` tras `answerable` en `EvalQuestion`
- `eval/questions_v2.jsonl`: creado (copia exacta de `tasks/assets/082/questions_v2.jsonl`) — 80 preguntas, 70 answerable, 10 sin respuesta, 8 categorías de 10 preguntas
- `tests/evaluation/test_dataset_v2.py`: creado con 12 tests (9 de carga v2 + 3 de v1/patterns)

## Verificación
- `cmp eval/questions_v2.jsonl tasks/assets/082/questions_v2.jsonl` → sin salida (archivos idénticos)
- `uv run pytest -q tests/evaluation/test_dataset_v2.py` → **12 passed**
- `uv run pytest -q tests/evaluation/test_dataset.py` → **11 passed** (sin cambios)
- `uv run pytest -q` → **509 passed**
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores
- `git diff --stat eval/questions.jsonl tests/evaluation/test_dataset.py` → vacío

## Decisiones que tomé
- Para `test_pagina_existe` usé `{p.number for p in doc.pages}` en lugar de `doc.page_count` tal como indica la spec, ya que en Markdown la numeración de secciones no es consecutiva con el total de páginas.
- Para `test_palabras_clave_en_su_pagina` busqué la página por número con `p.number == q.expected_page` y extraí su `.text` para validar con `keywords_hit`.
- El dict `LETTER` en el test se formateó con ruff (un entry por línea) en lugar del formato compacto de la spec, para que `ruff format --check .` pase.

## Bloqueos y dudas
Ninguno. Todos los tests pasaron a la primera.
