"""Cargador y validador del dataset de preguntas de evaluación."""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvalQuestion(BaseModel):
    """Una pregunta de evaluación."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z]\d{2}$")
    question: str = Field(min_length=1)
    expected_doc: str | None = None
    expected_page: int | None = Field(default=None, ge=1)
    answer_keywords: list[str] = Field(default_factory=list)
    answerable: bool
    category: str = Field(default="general", pattern=r"^[a-z_]+$")

    @model_validator(mode="after")
    def _check_consistency(self) -> "EvalQuestion":
        """Con respuesta: doc, página y keywords obligatorios.
        Sin respuesta: los tres vacíos.
        """
        if self.answerable:
            missing: list[str] = []
            if self.expected_doc is None:
                missing.append("expected_doc")
            if self.expected_page is None:
                missing.append("expected_page")
            if not self.answer_keywords:
                missing.append("answer_keywords")
            if missing:
                raise ValueError(f"una pregunta con respuesta necesita {', '.join(missing)}")
        else:
            extra: list[str] = []
            if self.expected_doc is not None:
                extra.append("expected_doc")
            if self.expected_page is not None:
                extra.append("expected_page")
            if self.answer_keywords:
                extra.append("answer_keywords")
            if extra:
                raise ValueError(f"una pregunta sin respuesta no lleva {', '.join(extra)}")
        return self


class DatasetError(ValueError):
    """Archivo de preguntas inválido."""


def load_questions(path: Path) -> list[EvalQuestion]:
    """Lee un JSONL de preguntas; DatasetError con el número de línea si algo falla."""
    ids: dict[str, int] = {}
    questions: list[EvalQuestion] = []

    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                data = json.loads(stripped)
                q = EvalQuestion(**data)
            except (json.JSONDecodeError, Exception) as e:
                raise DatasetError(f"línea {n}: {e}") from None

            if q.id in ids:
                raise DatasetError(f"línea {n}: id repetido {q.id}")
            ids[q.id] = n
            questions.append(q)

    if not questions:
        raise DatasetError("sin preguntas")

    return questions
