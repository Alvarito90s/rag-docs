"""Ejecución de evaluación de recuperación y generación."""

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from docuchat.config import Settings
from docuchat.evaluation.categories import (
    CategoryScores,
    keywords_by_category,
    retrieval_by_category,
)
from docuchat.evaluation.dataset import EvalQuestion
from docuchat.evaluation.judge import Judge, cited_passages
from docuchat.evaluation.metrics import (
    citation_counts,
    first_hit_rank,
    hit_at,
    keywords_hit,
    mean_reciprocal_rank,
    ratio,
)
from docuchat.generation.answer import Answerer
from docuchat.generation.citations import is_no_answer
from docuchat.index.embeddings import Embedder
from docuchat.index.indexer import build_indexer, reset_index
from docuchat.retrieval.searcher import Searcher, SearchMode

SEARCH_DEPTH = 10


@dataclass(frozen=True)
class RetrievalReport:
    """Métricas de recuperación de una configuración (tamaño de chunk + modo)."""

    chunk_size: int
    mode: str
    chunks: int
    questions: int
    hit_at_1: float
    hit_at_5: float
    mrr: float
    misses: list[str] = field(default_factory=list)  # ids sin acierto en el top 5
    by_category: dict[str, CategoryScores] = field(default_factory=dict)
    variant: str = "base"


# ─────────────────────────────────────────────────────────────────────────────
# Evaluación de generación
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class QuestionResult:
    """Resultado de una pregunta pasada por el Answerer."""

    id: str
    answerable: bool
    answer: str
    no_answer: bool
    keywords_ok: bool | None  # None en preguntas sin respuesta
    citations_correct: int
    citations_total: int
    first_token_s: float | None
    total_s: float
    faithful: bool | None = None  # None: no juzgada (rechazo, sin juez o veredicto ilegible)
    unsupported: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GenerationReport:
    """Métricas agregadas de generación."""

    questions: int
    answerable: int
    unanswerable: int
    keyword_accuracy: float | None
    citation_precision: float | None
    refusal_accuracy: float | None
    false_refusals: int
    avg_first_token_s: float | None
    avg_total_s: float
    judged: int = 0  # respuestas con veredicto
    unjudged: int = 0  # respuestas juzgables cuyo veredicto no se pudo leer
    faithfulness: float | None = None  # respaldadas / judged
    results: list[QuestionResult] = field(default_factory=list)
    keywords_by_category: dict[str, float | None] = field(default_factory=dict)
    variant: str = "base"


def evaluate_generation(
    answerer: Answerer,
    questions: Sequence[EvalQuestion],
    clock: Callable[[], float] = time.perf_counter,
    judge: Judge | None = None,
) -> GenerationReport:
    """Responde cada pregunta y agrega las métricas."""
    results: list[QuestionResult] = []
    kw_oks: list[bool] = []
    sum_correct: int = 0
    sum_total: int = 0
    refusals_no_answer: int = 0
    false_refusals: int = 0

    for q in questions:
        t0 = clock()
        first_token_time: float | None = None

        def _on_token(piece: str) -> None:
            nonlocal first_token_time
            if first_token_time is None:
                first_token_time = clock()

        answer = answerer.ask(q.question, on_token=_on_token)
        end = clock()

        no = is_no_answer(answer.text)
        kw_ok: bool | None = None
        cit_correct: int = 0
        cit_total: int = 0

        if q.answerable:
            assert q.expected_doc is not None
            assert q.expected_page is not None
            kw_ok = keywords_hit(answer.text, q.answer_keywords)
            cit_correct, cit_total = citation_counts(
                answer.sources, q.expected_doc, q.expected_page
            )
            kw_oks.append(kw_ok)
            sum_correct += cit_correct
            sum_total += cit_total
            if no:
                false_refusals += 1
        else:
            if no:
                refusals_no_answer += 1

        # Juez: se evalúa solo respuestas que no son rechazo
        faithful: bool | None = None
        unsupported: list[str] = []
        if judge is not None and not no:
            verdict = judge.judge(q.question, answer.text, cited_passages(answer))
            if verdict is None:
                faithful = None
            else:
                faithful = verdict.supported
                unsupported = verdict.unsupported

        results.append(
            QuestionResult(
                id=q.id,
                answerable=q.answerable,
                answer=answer.text,
                no_answer=no,
                keywords_ok=kw_ok,
                citations_correct=cit_correct,
                citations_total=cit_total,
                first_token_s=(first_token_time - t0 if first_token_time is not None else None),
                total_s=end - t0,
                faithful=faithful,
                unsupported=unsupported,
            )
        )

    n_answerable = sum(1 for q in questions if q.answerable)
    n_unanswerable = len(questions) - n_answerable

    first_tokens = [r.first_token_s for r in results if r.first_token_s is not None]
    avg_ft = sum(first_tokens) / len(first_tokens) if first_tokens else None

    # Calcular métricas de fidelidad
    judged = sum(1 for r in results if r.faithful is not None)
    unjudged = sum(
        1 for r in results if r.faithful is None and not r.no_answer and judge is not None
    )
    respaldadas = sum(1 for r in results if r.faithful is True)
    faithfulness = ratio(respaldadas, judged) if judged > 0 else None

    return GenerationReport(
        questions=len(questions),
        answerable=n_answerable,
        unanswerable=n_unanswerable,
        keyword_accuracy=ratio(sum(kw_oks), n_answerable),
        citation_precision=ratio(sum_correct, sum_total),
        refusal_accuracy=ratio(refusals_no_answer, n_unanswerable),
        false_refusals=false_refusals,
        avg_first_token_s=avg_ft,
        avg_total_s=(sum(r.total_s for r in results) / len(results) if results else 0.0),
        judged=judged,
        unjudged=unjudged,
        faithfulness=faithfulness,
        results=results,
        keywords_by_category=keywords_by_category(
            questions, {r.id: r.keywords_ok for r in results}
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Evaluación de recuperación (062 — no modificar)
# ─────────────────────────────────────────────────────────────────────────────


def eval_settings(base: Settings, data_root: Path, chunk_size: int) -> Settings:
    """Copia de base con data_dir propio y chunk_size/overlap (15 %) para la evaluación."""
    return base.model_copy(
        update={
            "data_dir": data_root / f"cs{chunk_size}",
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_size * 15 // 100,
        }
    )


def build_eval_index(settings: Settings, embedder: Embedder | None = None) -> int:
    """Reindexa settings.documents_dir desde cero y devuelve el número de chunks."""
    reset_index(settings)
    with build_indexer(settings, embedder=embedder) as indexer:
        stats = indexer.index_folder(settings.documents_dir)
        if stats.errors:
            raise RuntimeError(f"Errores al indexar: {stats.errors}")
        return indexer.chunk_count()


def evaluate_retrieval(
    searcher: Searcher,
    questions: Sequence[EvalQuestion],
    mode: SearchMode,
    *,
    chunk_size: int,
    chunks: int,
) -> RetrievalReport:
    """Hit@1, Hit@5 y MRR@10 de las preguntas con respuesta."""
    answerable_q = [q for q in questions if q.answerable]
    ranks: list[int | None] = []
    misses: list[str] = []

    for q in answerable_q:
        assert q.expected_doc is not None
        assert q.expected_page is not None
        retrieved = searcher.search(q.question, SEARCH_DEPTH, mode)
        rank = first_hit_rank(retrieved, q.expected_doc, q.expected_page)
        ranks.append(rank)
        if rank is None or rank > 5:
            misses.append(q.id)

    return RetrievalReport(
        chunk_size=chunk_size,
        mode=mode.value,
        chunks=chunks,
        questions=len(answerable_q),
        hit_at_1=hit_at(ranks, 1),
        hit_at_5=hit_at(ranks, 5),
        mrr=mean_reciprocal_rank(ranks),
        misses=misses,
        by_category=retrieval_by_category(answerable_q, ranks),
    )
