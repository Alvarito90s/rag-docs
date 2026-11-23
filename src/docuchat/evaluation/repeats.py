"""Agregado de varias pasadas de la evaluación de generación."""

from collections.abc import Sequence
from dataclasses import dataclass, field

from docuchat.evaluation.runner import GenerationReport, QuestionResult


@dataclass(frozen=True)
class Stat:
    """Media, mínimo y máximo de una métrica entre pasadas (None si ninguna pasada la tiene)."""

    mean: float | None
    low: float | None
    high: float | None


@dataclass(frozen=True)
class RunsSummary:
    """Resumen de N pasadas de generación."""

    runs: int
    keyword_accuracy: Stat
    citation_precision: Stat
    refusal_accuracy: Stat
    false_refusals: Stat
    faithfulness: Stat
    avg_total_s: Stat
    unstable: list[str] = field(default_factory=list)


def stat(values: Sequence[float | None]) -> Stat:
    """Stat de los valores que no son None."""

    clean = [v for v in values if v is not None]
    if not clean:
        return Stat(None, None, None)
    return Stat(sum(clean) / len(clean), min(clean), max(clean))


def outcome(result: QuestionResult) -> tuple[bool | None, bool]:
    """Resultado comparable de una pregunta: (keywords_ok, no_answer)."""

    return (result.keywords_ok, result.no_answer)


def unstable_questions(reports: Sequence[GenerationReport]) -> list[str]:
    """Ids cuyo resultado cambia entre pasadas, en el orden de la primera pasada."""

    if len(reports) <= 1:
        return []

    first_ids = [r.id for r in reports[0].results]
    unstable: list[str] = []

    for qid in first_ids:
        outcomes: list[tuple[bool | None, bool] | None] = []
        for report in reports:
            for r in report.results:
                if r.id == qid:
                    outcomes.append(outcome(r))
                    break
            else:
                # falta en esta pasada
                outcomes.append(None)
        if len(set(outcomes)) > 1:
            unstable.append(qid)
    return unstable


def summarize_runs(reports: Sequence[GenerationReport]) -> RunsSummary:
    """Resume varias pasadas de la misma variante."""

    if not reports:
        raise ValueError("sin pasadas")

    return RunsSummary(
        runs=len(reports),
        keyword_accuracy=stat([r.keyword_accuracy for r in reports]),
        citation_precision=stat([r.citation_precision for r in reports]),
        refusal_accuracy=stat([r.refusal_accuracy for r in reports]),
        false_refusals=stat([float(r.false_refusals) for r in reports]),
        faithfulness=stat([r.faithfulness for r in reports]),
        avg_total_s=stat([r.avg_total_s for r in reports]),
        unstable=unstable_questions(reports),
    )
