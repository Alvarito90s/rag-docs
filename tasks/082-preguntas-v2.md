# 082 · Preguntas de evaluación v2 con categoría
Fase: 8 · Depende de: 081

## Objetivo
Añadir una categoría a cada pregunta de evaluación y versionar las 80 preguntas v2 sobre `samples_v2/`, escritas por el cerebro: 70 con respuesta y 10 sin ella, en 8 categorías de 10 preguntas.

## Archivos
- modificar: `src/docuchat/evaluation/dataset.py` (solo añadir el campo `category` a `EvalQuestion`)
- crear (copia exacta, NO lo edites): `eval/questions_v2.jsonl` ← `tasks/assets/082/questions_v2.jsonl`
- crear: `tests/evaluation/test_dataset_v2.py`

## Interfaz
En `EvalQuestion`, justo después de `answerable`:
```python
    category: str = Field(default="general", pattern=r"^[a-z_]+$")
```
No cambies nada más de `dataset.py`.

## Comportamiento
1. Las preguntas sin `category` (todo `eval/questions.jsonl` v1) toman `"general"`. El dataset v1 NO se toca y sigue cargando igual.
2. `category` solo admite minúsculas sin tilde y guion bajo. `"Distractor"` o `"sin respuesta"` → `ValidationError`.
3. Ojo: hoy `EvalQuestion` ignora en silencio las claves desconocidas (es el comportamiento por defecto de pydantic). Si no añades el campo, el JSONL v2 cargaría igual pero sin categoría. El test 3 lo detecta.
4. Categorías del dataset v2 y letra de su id:

   | Letra | Categoría | Qué mide |
   | --- | --- | --- |
   | `l` | `literal` | La pregunta usa las mismas palabras que el texto |
   | `p` | `parafrasis` | La pregunta casi no comparte palabras con el texto |
   | `n` | `numerica` | Cifras, códigos o artículos |
   | `d` | `distractor` | Hay documentos casi iguales: K1/K2/K3, 2025/2026, contrato/adenda, actas |
   | `i` | `implicita` | La pregunta nombra el modelo, pero la página que responde no |
   | `t` | `tabla` | La respuesta está en una celda de una tabla DOCX o Markdown |
   | `f` | `profunda` | La respuesta está al fondo de un documento largo |
   | `u` | `sin_respuesta` | El corpus no la responde |

## Tests obligatorios
`tests/evaluation/test_dataset_v2.py`. NO cambies los valores esperados.
```python
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from docuchat.evaluation.dataset import EvalQuestion, load_questions
from docuchat.evaluation.metrics import keywords_hit
from docuchat.ingest.scanner import load_document

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "eval" / "questions_v2.jsonl"
SAMPLES_V2 = ROOT / "samples_v2"
LETTER = {
    "literal": "l", "parafrasis": "p", "numerica": "n", "distractor": "d",
    "implicita": "i", "tabla": "t", "profunda": "f", "sin_respuesta": "u",
}
```
1. `test_carga_v2`: `load_questions(V2)` → 80 preguntas; 70 con `answerable`; ids únicos; la primera es `"l01"` y la última `"u10"`.
2. `test_copia_exacta`: `V2.read_bytes() == (ROOT / "tasks" / "assets" / "082" / "questions_v2.jsonl").read_bytes()`.
3. `test_diez_por_categoria`: `Counter(q.category for q in load_questions(V2)) == {c: 10 for c in LETTER}`.
4. `test_letra_del_id`: para cada pregunta, `q.id[0] == LETTER[q.category]`.
5. `test_sin_respuesta_coherente`: para cada pregunta, `(q.category == "sin_respuesta") == (not q.answerable)`.
6. `test_pagina_existe`: para cada pregunta con respuesta, `q.expected_page` está en `{p.number for p in load_document(SAMPLES_V2 / q.expected_doc, SAMPLES_V2).pages}`. Usa el conjunto de números, no `page_count`: en Markdown la numeración de secciones no tiene por qué empezar en 1 ni ser consecutiva con el total.
7. `test_palabras_clave_en_su_pagina`: para cada pregunta con respuesta, `keywords_hit(texto de la página esperada, q.answer_keywords)` es `True`. Reúne los ids que fallen y haz `assert not fallos, fallos`. Este test garantiza que cada pregunta se puede responder con su página.
8. `test_v1_sin_cambios`: `load_questions(ROOT / "eval" / "questions.jsonl")` → 42 preguntas, todas con `category == "general"`.
9. `test_categoria_por_defecto`: `EvalQuestion(id="u01", question="¿X?", answerable=False).category == "general"`.
10. `test_categoria_invalida` (parametrizado: `"Distractor"`, `"sin respuesta"`, `""`): `EvalQuestion(id="u01", question="¿X?", answerable=False, category=valor)` → `ValidationError`.

Total: 9 + 3 = **12 tests**.

## Aceptación
- [ ] `cmp eval/questions_v2.jsonl tasks/assets/082/questions_v2.jsonl` → sin salida
- [ ] `uv run pytest -q tests/evaluation/test_dataset_v2.py` → 12 passed
- [ ] `uv run pytest -q tests/evaluation/test_dataset.py` → sigue pasando sin tocarlo
- [ ] `uv run pytest -q` pasa entero (497 + 12 = 509)
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `git diff --stat eval/questions.jsonl tests/evaluation/test_dataset.py` → vacío

## Fuera de alcance
No calcules métricas por categoría ni cambies el informe: eso es la spec 083. No toques `runner.py`, `report.py` ni `run.py`. No edites ninguna pregunta: si una no pasa el test 7, para y explícalo en "Bloqueos" con el id y el texto de la página.
