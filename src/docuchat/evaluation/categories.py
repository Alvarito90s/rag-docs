"""Métricas de evaluación agrupadas por categoría de pregunta."""

from collections import OrderedDict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from docuchat.evaluation.dataset import EvalQuestion
from docuchat.evaluation.metrics import hit_at, mean_reciprocal_rank, ratio


@dataclass(frozen=True)
class CategoryScores:
    """Métricas de recuperación de una categoría."""

    questions: int
    hit_at_1: float
    hit_at_5: float
    mrr: float


def retrieval_by_category(
    questions: Sequence[EvalQuestion], ranks: Sequence[int | None]
) -> dict[str, CategoryScores]:
    """Agrupa por q.category los puestos alineados con questions."""
    if len(questions) != len(ranks):
        raise ValueError("questions y ranks deben tener la misma longitud")
    if not questions:
        return {}

    groups: OrderedDict[str, list[int | None]] = OrderedDict()
    for q, rank in zip(questions, ranks, strict=False):
        groups.setdefault(q.category, []).append(rank)

    result: dict[str, CategoryScores] = {}
    for cat, cat_ranks in groups.items():
        result[cat] = CategoryScores(
            questions=len(cat_ranks),
            hit_at_1=hit_at(cat_ranks, 1),
            hit_at_5=hit_at(cat_ranks, 5),
            mrr=mean_reciprocal_rank(cat_ranks),
        )
    return result


def keywords_by_category(
    questions: Sequence[EvalQuestion], keywords_ok: Mapping[str, bool | None]
) -> dict[str, float | None]:
    """Acierto de palabras clave por categoría, solo de las preguntas con respuesta."""
    groups: OrderedDict[str, list[bool]] = OrderedDict()
    for q in questions:
        if not q.answerable:
            continue
        a = keywords_ok.get(q.id) is True
        groups.setdefault(q.category, []).append(a)

    return {cat: ratio(sum(acc), len(acc)) for cat, acc in groups.items()}
