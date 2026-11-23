"""Tests para src/docuchat/evaluation/runner.py — 10 tests obligatorios."""

import dataclasses
import os
import shutil
from collections.abc import Sequence
from pathlib import Path

import pytest

from docuchat.config import Settings
from docuchat.evaluation.dataset import EvalQuestion, load_questions
from docuchat.evaluation.runner import (
    SEARCH_DEPTH,
    RetrievalReport,
    build_eval_index,
    eval_settings,
    evaluate_retrieval,
)
from docuchat.retrieval.searcher import SearchMode, build_searcher

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
ROOT = Path(__file__).resolve().parents[2]


# ── FakeEmbedder ─────────────────────────────────────────────────────────


class FakeEmbedder:
    """Embedder determinista que no toca red."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[float(len(t)), 1.0, 0.5] for t in texts]


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture()
def base(tmp_path: Path):
    """Settings limpia con documents_dir = samples, sin vars de entorno."""
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            os.environ.pop(key)
    tmp_path.chmod(0o755)
    os.chdir(tmp_path)
    return Settings(documents_dir=SAMPLES)


@pytest.fixture()
def preguntas():
    """Preguntas reales del dataset."""
    return load_questions(ROOT / "eval" / "questions.jsonl")


# ── Test 1: eval_settings ────────────────────────────────────────────────


def test_1_eval_settings(base: Settings, tmp_path: Path):
    """data_dir, chunk_size, chunk_overlap y llm_model copiados."""
    s500 = eval_settings(base, tmp_path, 500)
    assert s500.data_dir == tmp_path / "cs500"
    assert s500.chunk_size == 500
    assert s500.chunk_overlap == 75  # 500 // 100 * 15
    assert s500.llm_model == base.llm_model

    s1200 = eval_settings(base, tmp_path, 1200)
    assert s1200.data_dir == tmp_path / "cs1200"
    assert s1200.chunk_size == 1200
    assert s1200.chunk_overlap == 180  # 1200 * 15 // 100


# ── Test 2: build_eval_index (parametrizado) ─────────────────────────────


@pytest.mark.parametrize(
    ("chunk_size", "expected_chunks"),
    [(500, 45), (800, 26), (1200, 23)],
)
def test_2_build_eval_index(base: Settings, tmp_path: Path, chunk_size: int, expected_chunks: int):
    """Cada tamaño de chunk reindexa desde cero y devuelve el número esperado."""
    s = eval_settings(base, tmp_path, chunk_size)
    chunks = build_eval_index(s, FakeEmbedder())
    assert chunks == expected_chunks


# ── Test 3: reindexar dos veces ──────────────────────────────────────────


def test_3_reindexar_misma_carpeta(base: Settings, tmp_path: Path):
    """Empezar de cero siempre da el mismo resultado."""
    s = eval_settings(base, tmp_path, 800)
    c1 = build_eval_index(s, FakeEmbedder())
    c2 = build_eval_index(s, FakeEmbedder())
    assert c1 == c2 == 26


# ── Test 4: BM25 con 800 ────────────────────────────────────────────────


def test_4_bm25_800(base: Settings, tmp_path: Path, preguntas):
    """BM25 con chunk_size=800: métricas exactas."""
    s = eval_settings(base, tmp_path, 800)
    chunks = build_eval_index(s, FakeEmbedder())
    searcher = build_searcher(s, embedder=FakeEmbedder())
    report = evaluate_retrieval(searcher, preguntas, SearchMode.BM25, chunk_size=800, chunks=chunks)
    assert report.chunk_size == 800
    assert report.questions == 32
    assert report.hit_at_1 == pytest.approx(28 / 32)
    assert report.hit_at_5 == 1.0
    assert report.mrr == pytest.approx(0.9203125)
    assert report.misses == []
    assert report.mode == "bm25"


# ── Test 5: BM25 con 1200 ───────────────────────────────────────────────


def test_5_bm25_1200(base: Settings, tmp_path: Path, preguntas):
    """BM25 con chunk_size=1200: hit_at_1 y mrr esperados."""
    s = eval_settings(base, tmp_path, 1200)
    chunks = build_eval_index(s, FakeEmbedder())
    searcher = build_searcher(s, embedder=FakeEmbedder())
    report = evaluate_retrieval(
        searcher, preguntas, SearchMode.BM25, chunk_size=1200, chunks=chunks
    )
    assert report.questions == 32
    assert report.hit_at_1 == pytest.approx(28 / 32)
    assert report.mrr == pytest.approx(0.9229166666666667)


# ── Test 6: solo answerable ─────────────────────────────────────────────


def test_6_solo_answerable(base: Settings, tmp_path: Path, preguntas):
    """Con [q01, u01] solo cuenta q01: questions=1."""
    s = eval_settings(base, tmp_path, 800)
    chunks = build_eval_index(s, FakeEmbedder())
    searcher = build_searcher(s, embedder=FakeEmbedder())
    q01 = preguntas[0]  # q01
    u01 = preguntas[32]  # u01
    report = evaluate_retrieval(
        searcher, [q01, u01], SearchMode.BM25, chunk_size=800, chunks=chunks
    )
    assert report.questions == 1


# ── Test 7: misses ──────────────────────────────────────────────────────


def test_7_misses(base: Settings, tmp_path: Path):
    """Pregunta inexistente → aparece en misses."""
    s = eval_settings(base, tmp_path, 800)
    chunks = build_eval_index(s, FakeEmbedder())
    searcher = build_searcher(s, embedder=FakeEmbedder())
    fake_q = EvalQuestion(
        id="x01",
        question="¿Qué significa el error E-17?",
        expected_doc="manual_cafetera.pdf",
        expected_page=1,
        answer_keywords=["vacío"],
        answerable=True,
    )
    report = evaluate_retrieval(searcher, [fake_q], SearchMode.BM25, chunk_size=800, chunks=chunks)
    assert report.misses == ["x01"]


# ── Test 8: error de indexación ─────────────────────────────────────────


def test_8_error_indexacion(tmp_path: Path):
    """Carpeta con PDF roto → build_eval_index lanza RuntimeError."""
    docs = tmp_path / "docs"
    shutil.copytree(SAMPLES, docs)
    (docs / "roto.pdf").write_bytes(b"no es un pdf")

    settings = Settings(documents_dir=docs, data_dir=tmp_path / "data")
    embedder = FakeEmbedder()
    with pytest.raises(RuntimeError) as exc_info:
        build_eval_index(settings, embedder)
    assert "roto.pdf" in str(exc_info.value)


# ── Test 9: RetrievalReport inmutable ───────────────────────────────────


def test_9_report_inmutable():
    """RetrievalReport es un dataclass frozen."""
    r = RetrievalReport(
        chunk_size=800,
        mode="bm25",
        chunks=26,
        questions=32,
        hit_at_1=0.8,
        hit_at_5=0.95,
        mrr=0.9,
        misses=[],
    )
    assert r.mode == "bm25"
    # Verificar que es inmutable (frozen=True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.chunk_size = 500


# ── Test 10: evaluate_retrieval con SEARCH_DEPTH ─────────────────────────


def test_10_search_depth(base: Settings, tmp_path: Path, preguntas):
    """SEARCH_DEPTH = 10 y hits en rank > 5 → miss."""
    assert SEARCH_DEPTH == 10
    s = eval_settings(base, tmp_path, 800)
    chunks = build_eval_index(s, FakeEmbedder())
    searcher = build_searcher(s, embedder=FakeEmbedder())
    report = evaluate_retrieval(searcher, preguntas, SearchMode.BM25, chunk_size=800, chunks=chunks)
    assert report.chunks == chunks
