"""Tests para métricas de evaluación por categoría (spec 083)."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from docuchat.config import Settings
from docuchat.evaluation.categories import (
    CategoryScores,
    keywords_by_category,
    retrieval_by_category,
)
from docuchat.evaluation.dataset import EvalQuestion, load_questions
from docuchat.evaluation.report import (
    GenerationReport,
    RetrievalReport,
    render_category_table,
    render_results,
)
from docuchat.evaluation.runner import (
    Answerer,
    build_eval_index,
    eval_settings,
    evaluate_generation,
    evaluate_retrieval,
)
from docuchat.generation.prompts import NO_ANSWER
from docuchat.models import Chunk, SearchResult, make_chunk_id
from docuchat.retrieval.searcher import SearchMode, build_searcher

ROOT = Path(__file__).resolve().parents[2]


# ── Helpers ──────────────────────────────────────────────────────────────────


def q(qid: str, category: str, answerable: bool = True) -> EvalQuestion:
    if answerable:
        return EvalQuestion(
            id=qid,
            question="¿X?",
            expected_doc="a.pdf",
            expected_page=1,
            answer_keywords=["x"],
            answerable=True,
            category=category,
        )
    return EvalQuestion(
        id=qid,
        question="¿X?",
        answerable=False,
        category=category,
    )


class FakeEmbedder:
    def embed(self, texts):
        return [[float(len(t)), 1.0, 0.5] for t in texts]


@pytest.fixture()
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def bm25_report(tmp: Path, docs: str, questions_file: str) -> RetrievalReport:
    base = Settings(documents_dir=ROOT / docs)
    s = eval_settings(base, tmp / docs, 800)
    fake = FakeEmbedder()
    chunks = build_eval_index(s, fake)
    searcher = build_searcher(s, embedder=fake)
    qs = load_questions(ROOT / questions_file)
    return evaluate_retrieval(searcher, qs, SearchMode.BM25, chunk_size=800, chunks=chunks)


# ── Test 1 ───────────────────────────────────────────────────────────────────


def test_retrieval_by_category():
    questions = [q("a01", "x"), q("b01", "y"), q("a02", "x")]
    ranks = [1, None, 3]
    result = retrieval_by_category(questions, ranks)
    keys = list(result.keys())
    assert keys == ["x", "y"]
    x = result["x"]
    assert x.questions == 2
    assert x.hit_at_1 == 0.5
    assert x.hit_at_5 == 1.0
    assert x.mrr == pytest.approx(2 / 3, abs=1e-6)
    y = result["y"]
    assert y.questions == 1
    assert y.hit_at_1 == 0.0
    assert y.hit_at_5 == 0.0
    assert y.mrr == 0.0


# ── Test 2 ───────────────────────────────────────────────────────────────────


def test_retrieval_by_category_longitud():
    with pytest.raises(ValueError, match="questions y ranks deben tener la misma longitud"):
        retrieval_by_category([q("a01", "x")], [])


# ── Test 3 ───────────────────────────────────────────────────────────────────


def test_retrieval_by_category_vacio():
    assert retrieval_by_category([], []) == {}


# ── Test 4 ───────────────────────────────────────────────────────────────────


def test_keywords_by_category():
    questions = [
        q("a01", "x"),
        q("a02", "x"),
        q("b01", "y"),
        q("u01", "sin_respuesta", answerable=False),
    ]
    keywords_ok_map = {"a01": True, "a02": False, "u01": None}
    result = keywords_by_category(questions, keywords_ok_map)
    assert result == {"x": 0.5, "y": 0.0}
    assert "sin_respuesta" not in result


# ── Test 5 ───────────────────────────────────────────────────────────────────


def test_bm25_v2_por_categoria(clean_env: Path):
    r = bm25_report(clean_env, "samples_v2", "eval/questions_v2.jsonl")
    assert r.chunks == 73
    assert r.hit_at_1 == pytest.approx(0.7, abs=1e-6)
    assert r.hit_at_5 == pytest.approx(0.8, abs=1e-6)
    cat_keys = list(r.by_category.keys())
    assert cat_keys == [
        "literal",
        "parafrasis",
        "numerica",
        "distractor",
        "implicita",
        "tabla",
        "profunda",
    ]
    cat = r.by_category
    c = cat["parafrasis"]
    assert (c.questions, c.hit_at_1, c.hit_at_5, c.mrr) == (
        10,
        0.3,
        0.4,
        pytest.approx(0.36, abs=1e-6),
    )
    c = cat["implicita"]
    assert (c.questions, c.hit_at_1, c.hit_at_5, c.mrr) == (
        10,
        0.1,
        0.4,
        pytest.approx(0.2503968, abs=1e-6),
    )
    c = cat["tabla"]
    assert (c.questions, c.hit_at_1, c.hit_at_5, c.mrr) == (
        10,
        1.0,
        1.0,
        pytest.approx(1.0, abs=1e-6),
    )
    c = cat["distractor"]
    assert (c.questions, c.hit_at_1, c.hit_at_5, c.mrr) == (
        10,
        0.9,
        0.9,
        pytest.approx(0.9111111, abs=1e-6),
    )


# ── Test 6 ───────────────────────────────────────────────────────────────────


def test_bm25_v1_general(clean_env: Path):
    r = bm25_report(clean_env, "samples", "eval/questions.jsonl")
    assert list(r.by_category) == ["general"]
    general = r.by_category["general"]
    assert general.questions == 32
    assert general.hit_at_1 == pytest.approx(27 / 32, abs=1e-6)
    assert general.hit_at_5 == 1.0
    assert general.mrr == pytest.approx(0.9088542, abs=1e-6)


# ── Test 7 ───────────────────────────────────────────────────────────────────


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
    def search(self, query: str, top_k: int) -> list[SearchResult]:
        return CONTEXT[:top_k]


class QueueChat:
    def __init__(self, answers: list[list[str]]) -> None:
        self.answers = list(answers)

    def stream(self, messages) -> "Iterator[str]":
        yield from self.answers.pop(0)


def test_generation_por_categoria():

    A1 = EvalQuestion(
        id="a01",
        question="¿Alfa?",
        expected_doc="a.pdf",
        expected_page=1,
        answer_keywords=["alfa"],
        answerable=True,
        category="x",
    )
    A2 = EvalQuestion(
        id="a02",
        question="¿Alfa?",
        expected_doc="a.pdf",
        expected_page=1,
        answer_keywords=["alfa"],
        answerable=True,
        category="x",
    )
    U = EvalQuestion(
        id="u01",
        question="¿Y?",
        answerable=False,
        category="sin_respuesta",
    )
    chat = QueueChat([["Es alfa [1]."], ["Ni idea [1]."], [NO_ANSWER]])
    answerer = Answerer(FakeRetriever(), chat, top_k=5, context_max_chars=6000)
    report = evaluate_generation(answerer, [A1, A2, U])
    assert report.keywords_by_category == {"x": 0.5}


# ── Test 8 ───────────────────────────────────────────────────────────────────


def test_render_category_table():
    r1 = RetrievalReport(
        chunk_size=800,
        mode="hybrid",
        chunks=73,
        questions=20,
        hit_at_1=0.5,
        hit_at_5=0.75,
        mrr=0.6,
        by_category={
            "literal": CategoryScores(10, 0.9, 1.0, 0.95),
            "implicita": CategoryScores(10, 0.1, 0.4, 0.25),
        },
    )
    r2 = RetrievalReport(
        chunk_size=800,
        mode="bm25",
        chunks=70,
        questions=20,
        hit_at_1=0.5,
        hit_at_5=0.75,
        mrr=0.6,
        by_category={"literal": CategoryScores(10, 0.8, 1.0, 0.9)},
    )
    r3 = RetrievalReport(
        chunk_size=500,
        mode="hybrid",
        chunks=73,
        questions=20,
        hit_at_1=0.5,
        hit_at_5=0.75,
        mrr=0.6,
        by_category={"literal": CategoryScores(10, 0.123, 1.0, 0.5)},
    )
    gen = GenerationReport(
        questions=20,
        answerable=20,
        unanswerable=0,
        keyword_accuracy=0.5,
        citation_precision=None,
        refusal_accuracy=None,
        false_refusals=0,
        avg_first_token_s=None,
        avg_total_s=0.0,
        keywords_by_category={"literal": 1.0, "implicita": 0.0},
    )

    expected_lines = [
        "| Categoría | Preguntas | Hit@1 hybrid | Hit@1 bm25 | Palabras clave |",
        "| --- | ---: | ---: | ---: | ---: |",
        "| literal | 10 | 0.900 | 0.800 | 1.000 |",
        "| implicita | 10 | 0.100 | — | 0.000 |",
    ]
    result = render_category_table([r1, r2, r3], gen, 800)
    assert result.split("\n") == expected_lines


# ── Test 9 ───────────────────────────────────────────────────────────────────


def test_render_category_table_sin_generacion():
    r1 = RetrievalReport(
        chunk_size=800,
        mode="hybrid",
        chunks=73,
        questions=20,
        hit_at_1=0.5,
        hit_at_5=0.75,
        mrr=0.6,
        by_category={
            "literal": CategoryScores(10, 0.9, 1.0, 0.95),
            "implicita": CategoryScores(10, 0.1, 0.4, 0.25),
        },
    )
    r2 = RetrievalReport(
        chunk_size=800,
        mode="bm25",
        chunks=70,
        questions=20,
        hit_at_1=0.5,
        hit_at_5=0.75,
        mrr=0.6,
        by_category={"literal": CategoryScores(10, 0.8, 1.0, 0.9)},
    )

    expected_lines = [
        "| Categoría | Preguntas | Hit@1 hybrid | Hit@1 bm25 |",
        "| --- | ---: | ---: | ---: |",
        "| literal | 10 | 0.900 | 0.800 |",
        "| implicita | 10 | 0.100 | — |",
    ]
    result = render_category_table([r1, r2], None, 800)
    assert result.split("\n") == expected_lines


# ── Test 10 ──────────────────────────────────────────────────────────────────


def test_render_category_table_no_aplica():
    # solo "general"
    r_gen = RetrievalReport(
        chunk_size=800,
        mode="bm25",
        chunks=1,
        questions=1,
        hit_at_1=1.0,
        hit_at_5=1.0,
        mrr=1.0,
        by_category={"general": CategoryScores(32, 0.8, 1.0, 0.9)},
    )
    assert render_category_table([r_gen], None, 800) == ""
    # chunk no encontrado
    assert render_category_table([r_gen], None, 1200) == ""


# ── Test 11 ──────────────────────────────────────────────────────────────────


def test_render_results_con_categorias():
    r1 = RetrievalReport(
        chunk_size=800,
        mode="hybrid",
        chunks=73,
        questions=20,
        hit_at_1=0.5,
        hit_at_5=0.75,
        mrr=0.6,
        by_category={
            "literal": CategoryScores(10, 0.9, 1.0, 0.95),
            "implicita": CategoryScores(10, 0.1, 0.4, 0.25),
        },
    )
    r2 = RetrievalReport(
        chunk_size=800,
        mode="bm25",
        chunks=70,
        questions=20,
        hit_at_1=0.5,
        hit_at_5=0.75,
        mrr=0.6,
        by_category={"literal": CategoryScores(10, 0.8, 1.0, 0.9)},
    )
    text = render_results(
        date="d",
        llm_model="m",
        embedding_model="e",
        generation_chunk_size=None,
        retrieval=[r1, r2],
        generation=None,
    )
    assert "### Por categoría (chunk 800)" in text
    assert text.index("### Por categoría (chunk 800)") < text.index("## Generación")


# ── Test 12 ──────────────────────────────────────────────────────────────────


def test_render_results_v1_sin_cambios():
    r = RetrievalReport(
        chunk_size=800,
        mode="bm25",
        chunks=1,
        questions=1,
        hit_at_1=1.0,
        hit_at_5=1.0,
        mrr=1.0,
        by_category={"general": CategoryScores(32, 0.8, 1.0, 0.9)},
    )
    text = render_results(
        date="d",
        llm_model="m",
        embedding_model="e",
        generation_chunk_size=None,
        retrieval=[r],
        generation=None,
    )
    assert "Por categoría" not in text


# ── Test 13 ──────────────────────────────────────────────────────────────────


def test_defaults_compatibles():
    r = RetrievalReport(
        chunk_size=800,
        mode="bm25",
        chunks=1,
        questions=1,
        hit_at_1=1.0,
        hit_at_5=1.0,
        mrr=1.0,
    )
    assert r.by_category == {}
    g = GenerationReport(
        questions=1,
        answerable=1,
        unanswerable=0,
        keyword_accuracy=1.0,
        citation_precision=None,
        refusal_accuracy=None,
        false_refusals=0,
        avg_first_token_s=None,
        avg_total_s=0.0,
    )
    assert g.keywords_by_category == {}
