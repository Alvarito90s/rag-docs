"""Tests para evaluate_generation — 6 tests obligatorios."""

from collections.abc import Callable, Iterator, Sequence

import pytest

from docuchat.evaluation.dataset import EvalQuestion
from docuchat.evaluation.runner import evaluate_generation
from docuchat.generation.answer import Answerer
from docuchat.generation.prompts import NO_ANSWER, Message
from docuchat.models import Chunk, SearchResult, make_chunk_id

# ── Helpers ──────────────────────────────────────────────────────────────────


def mk(source: str, page: int, text: str, rank: int = 1) -> SearchResult:
    chunk = Chunk(
        chunk_id=make_chunk_id(source, page, 0),
        source=source,
        doc_sha256="a" * 64,
        page=page,
        position=0,
        text=text,
    )
    return SearchResult(chunk=chunk, rank=rank, score=0.1)


CONTEXT = [mk("a.pdf", 1, "Alfa."), mk("b.md", 2, "Beta.")]


class FakeRetriever:
    """Devuelve siempre CONTEXT (recorte a top_k)."""

    def search(self, query: str, top_k: int) -> list[SearchResult]:
        return CONTEXT[:top_k]


class QueueChat:
    """Cada llamada a stream devuelve la siguiente respuesta de la cola."""

    def __init__(self, answers: list[list[str]]) -> None:
        self.answers = list(answers)

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        yield from self.answers.pop(0)


def fake_clock(values: list[float]) -> Callable[[], float]:
    it = iter(values)
    return lambda: next(it)


# ── Preguntas de prueba ─────────────────────────────────────────────────────

A = EvalQuestion(
    id="q01",
    question="¿Alfa?",
    expected_doc="a.pdf",
    expected_page=1,
    answer_keywords=["alfa"],
    answerable=True,
)

U = EvalQuestion(
    id="u01",
    question="¿Capital de Francia?",
    answerable=False,
)


# ── Test 1: Todo bien ───────────────────────────────────────────────────────


def test_1_todo_bien():
    """Respuesta correcta + rechazo correcto."""
    chat = QueueChat([["Es alfa ", "[1]."], [NO_ANSWER]])
    answerer = Answerer(FakeRetriever(), chat, top_k=5, context_max_chars=6000)
    report = evaluate_generation(
        answerer, [A, U], clock=fake_clock([0.0, 0.5, 2.0, 10.0, 10.25, 11.0])
    )

    assert report.questions == 2
    assert report.answerable == 1
    assert report.unanswerable == 1
    assert report.keyword_accuracy == 1.0
    assert report.citation_precision == 1.0
    assert report.refusal_accuracy == 1.0
    assert report.false_refusals == 0
    assert report.avg_first_token_s == pytest.approx(0.375)
    assert report.avg_total_s == pytest.approx(1.5)


# ── Test 2: Detalle del resultado 0 ─────────────────────────────────────────


def test_2_result_details():
    """Verifica campos individuales de results."""
    chat = QueueChat([["Es alfa ", "[1]."], [NO_ANSWER]])
    answerer = Answerer(FakeRetriever(), chat, top_k=5, context_max_chars=6000)
    report = evaluate_generation(
        answerer, [A, U], clock=fake_clock([0.0, 0.5, 2.0, 10.0, 10.25, 11.0])
    )

    r0 = report.results[0]
    assert r0.id == "q01"
    assert r0.answer == "Es alfa [1]."
    assert r0.keywords_ok is True
    assert r0.citations_correct == 1
    assert r0.citations_total == 1
    assert r0.first_token_s == 0.5
    assert r0.total_s == 2.0

    r1 = report.results[1]
    assert r1.id == "u01"
    assert r1.no_answer is True
    assert r1.keywords_ok is None
    assert r0.answerable is True
    assert r1.citations_correct == 0
    assert r1.citations_total == 0


# ── Test 3: Todo mal ────────────────────────────────────────────────────────


def test_3_todo_mal():
    """Refusa lo que sí se puede; cita mal lo que no."""
    chat = QueueChat([[NO_ANSWER], ["Es París [2]."]])
    answerer = Answerer(FakeRetriever(), chat, top_k=5, context_max_chars=6000)
    report = evaluate_generation(answerer, [A, U], clock=fake_clock([0, 1, 2, 3, 4, 5]))

    assert report.keyword_accuracy == 0.0
    assert report.false_refusals == 1
    assert report.citation_precision is None
    assert report.refusal_accuracy == 0.0


# ── Test 4: Citas a medias ──────────────────────────────────────────────────


def test_4_citas_a_medias():
    """["alfa [1][2]."] → citation_precision == 0.5."""
    chat = QueueChat([["alfa [1][2]."]])
    answerer = Answerer(FakeRetriever(), chat, top_k=5, context_max_chars=6000)
    report = evaluate_generation(answerer, [A], clock=fake_clock([0, 1, 2]))
    assert report.citation_precision == pytest.approx(0.5)


# ── Test 5: Sin trozos ──────────────────────────────────────────────────────


def test_5_sin_trozos():
    """QueueChat([[]]) → first_token_s is None, no_answer is True."""
    chat = QueueChat([[]])
    answerer = Answerer(FakeRetriever(), chat, top_k=5, context_max_chars=6000)
    report = evaluate_generation(answerer, [A], clock=fake_clock([0.0, 1.0]))

    assert report.results[0].first_token_s is None
    assert report.avg_first_token_s is None
    assert report.avg_total_s == 1.0
    assert report.results[0].no_answer is True


# ── Test 6: Sin preguntas ───────────────────────────────────────────────────


def test_6_sin_preguntas():
    """evaluate_generation(answerer, []) → ratios None, avg_total_s == 0.0."""
    chat = QueueChat([[]])
    answerer = Answerer(FakeRetriever(), chat, top_k=5, context_max_chars=6000)
    report = evaluate_generation(answerer, [])

    assert report.questions == 0
    assert report.answerable == 0
    assert report.unanswerable == 0
    assert report.keyword_accuracy is None
    assert report.citation_precision is None
    assert report.refusal_accuracy is None
    assert report.false_refusals == 0
    assert report.avg_first_token_s is None
    assert report.avg_total_s == 0.0
    assert report.results == []


# ── Test 7: Falso rechazo con NO_ANSWER ──────────────────────────────────


def test_7_falso_rechazo():
    """NO_ANSWER en pregunta con respuesta → keywords_ok=False, false_refusals=1."""
    chat = QueueChat([[NO_ANSWER]])
    answerer = Answerer(FakeRetriever(), chat, top_k=5, context_max_chars=6000)
    report = evaluate_generation(answerer, [A], clock=fake_clock([0.0, 1.0, 2.0]))

    r0 = report.results[0]
    assert r0.id == "q01"
    assert r0.no_answer is True
    assert r0.keywords_ok is False
    assert r0.citations_correct == 0
    assert r0.citations_total == 0
    assert report.false_refusals == 1
    assert report.keyword_accuracy == 0.0
