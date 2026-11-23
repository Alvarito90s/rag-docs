# 060 · Dataset de evaluación
Fase: 6 · Depende de: 024-c

## Objetivo
Versionar las 42 preguntas de evaluación (32 con respuesta en `samples/`, 10 sin ella) y un cargador que las valide.

## Archivos
- crear (copia exacta): `eval/questions.jsonl` ← `tasks/assets/060/questions.jsonl` (lo ha escrito el cerebro; NO lo edites)
- crear: `src/docuchat/evaluation/__init__.py` (solo el docstring `"""Evaluación: dataset, métricas, ejecución e informe."""`)
- crear: `src/docuchat/evaluation/dataset.py`
- crear: `tests/evaluation/__init__.py` (vacío) y `tests/evaluation/test_dataset.py`

## Interfaz
```python
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class EvalQuestion(BaseModel):
    """Una pregunta de evaluación."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z]\d{2}$")
    question: str = Field(min_length=1)
    expected_doc: str | None = None
    expected_page: int | None = Field(default=None, ge=1)
    answer_keywords: list[str] = Field(default_factory=list)  # cada una admite alternativas con "|"
    answerable: bool

    @model_validator(mode="after")
    def _check_consistency(self) -> "EvalQuestion":
        """Con respuesta: doc, página y palabras clave obligatorios. Sin respuesta: los tres vacíos."""


class DatasetError(ValueError):
    """Archivo de preguntas inválido."""


def load_questions(path: Path) -> list[EvalQuestion]:
    """Lee un JSONL de preguntas; DatasetError con el número de línea si algo falla."""
```

## Comportamiento
1. `_check_consistency`: si `answerable` y falta `expected_doc`, `expected_page` o `answer_keywords` está vacío → `ValueError("una pregunta con respuesta necesita expected_doc, expected_page y answer_keywords")`. Si NO `answerable` y alguno de los tres tiene valor → `ValueError("una pregunta sin respuesta no lleva expected_doc, expected_page ni answer_keywords")`.
2. `load_questions`: lee en UTF-8 línea a línea (numeradas desde 1) y salta las líneas en blanco. `json.JSONDecodeError` o `ValidationError` → `DatasetError(f"línea {n}: {e}")`. Id repetido → `DatasetError(f"línea {n}: id repetido {id}")`. Si no hay ninguna pregunta → `DatasetError("sin preguntas")`.

## Tests obligatorios
`tests/evaluation/test_dataset.py`. NO cambies los valores esperados. `ROOT = Path(__file__).resolve().parents[2]`.
1. `load_questions(ROOT / "eval" / "questions.jsonl")` → 42 preguntas; 32 con `answerable`; ids únicos; el primero es `"q01"` y el último `"u10"`.
2. Coherencia con `samples/`: cada `expected_doc` existe en `ROOT / "samples"`, y `expected_page <= número de páginas` de ese documento (usa `load_document(path, ROOT / "samples").page_count`).
3. Copia exacta: los bytes de `eval/questions.jsonl` son iguales a los de `tasks/assets/060/questions.jsonl`.
4. `EvalQuestion` válida sin respuesta: `EvalQuestion(id="u01", question="¿X?", answerable=False)` → `expected_doc is None`, `answer_keywords == []`.
5. `_check_consistency` (parametrizado, 3 casos) → `ValidationError`: con respuesta sin `expected_page`; con respuesta con `answer_keywords=[]`; sin respuesta con `expected_doc="a.pdf"`.
6. JSON roto: archivo con una línea válida y en la línea 2 `{no es json` → `DatasetError` cuyo mensaje empieza por `"línea 2:"`.
7. Id repetido en la línea 3 → mensaje `"línea 3: id repetido q01"`.
8. Archivo vacío (o solo con líneas en blanco) → `DatasetError("sin preguntas")`.
9. Las líneas en blanco intermedias se ignoran: dos preguntas separadas por `"\n\n"` → 2.

## Aceptación
- [ ] `uv run pytest -q tests/evaluation/test_dataset.py` → 11 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `cmp eval/questions.jsonl tasks/assets/060/questions.jsonl` → sin salida

## Fuera de alcance
Métricas (061) y ejecución (062–064). No edites el dataset.
