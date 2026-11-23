"""Tests para src/docuchat/evaluation/repeats.py y las modificaciones de la spec 086 — 14 tests."""

import contextlib
import json
import os
import unittest.mock as mock
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

from docuchat.config import Settings
from docuchat.evaluation.dataset import load_questions
from docuchat.evaluation.repeats import (
    RunsSummary,
    Stat,
    stat,
    summarize_runs,
    unstable_questions,
)
from docuchat.evaluation.report import render_results, render_runs_table
from docuchat.evaluation.run import main as run_main
from docuchat.evaluation.runner import (
    GenerationReport,
    QuestionResult,
)
from docuchat.evaluation.variants import VARIANTS
from docuchat.generation.prompts import Message

# ── Rutas ────────────────────────────────────────────────────────────────────

QUESTIONS = Path(__file__).resolve().parents[2] / "eval" / "questions.jsonl"
SAMPLES = Path(__file__).resolve().parents[2] / "samples"

# ── Helpers ──────────────────────────────────────────────────────────────────


def res(qid: str, kw: bool | None, no: bool) -> QuestionResult:
    return QuestionResult(
        id=qid,
        answerable=kw is not None,
        answer="x",
        no_answer=no,
        keywords_ok=kw,
        citations_correct=0,
        citations_total=0,
        first_token_s=None,
        total_s=1.0,
    )


def gen(
    kw: float | None,
    fr: int,
    total: float,
    results: list[QuestionResult],
    faithfulness: float | None = None,
) -> GenerationReport:
    return GenerationReport(
        questions=len(results),
        answerable=0,
        unanswerable=0,
        keyword_accuracy=kw,
        citation_precision=1.0,
        refusal_accuracy=1.0,
        false_refusals=fr,
        avg_first_token_s=None,
        avg_total_s=total,
        results=results,
        faithfulness=faithfulness,
    )


class SameChat:
    """Siempre la misma respuesta."""

    def __init__(self, text: str) -> None:
        self.text = text

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        yield self.text


class FakeEmbedder:
    """Embedder determinista que no toca red."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[float(len(t)), 1.0, 0.5] for t in texts]


# ── Fixture entorno limpio ──────────────────────────────────────────────────


@pytest.fixture()
def base(tmp_path: Path):
    """Settings limpia sin vars de entorno."""
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            os.environ.pop(key)
    tmp_path.chmod(0o755)
    os.chdir(tmp_path)
    return Settings(documents_dir=SAMPLES)


# ── Test 1: test_stat ───────────────────────────────────────────────────────


def test_stat():
    """Stat con valores, vacío y solo None."""
    assert stat([0.5, None, 1.0]) == Stat(0.75, 0.5, 1.0)
    assert stat([]) == Stat(None, None, None)
    assert stat([None]) == Stat(None, None, None)


# ── Test 2: test_unstable ──────────────────────────────────────────────────


def test_unstable():
    """u01 cambia de no_answer, a02 cambia de kw_ok → ambas inestables."""
    r1 = gen(
        1.0,
        0,
        1.0,
        [
            res("a01", True, False),
            res("u01", None, True),
            res("a02", False, False),
        ],
    )
    r2 = gen(
        1.0,
        0,
        1.0,
        [
            res("a01", True, False),
            res("u01", None, False),
            res("a02", True, False),
        ],
    )
    assert unstable_questions([r1, r2]) == ["u01", "a02"]


# ── Test 3: test_unstable_falta_en_una_pasada ──────────────────────────────


def test_unstable_falta_en_una_pasada():
    """a02 falta en r2 → inestable."""
    r1 = gen(
        1.0,
        0,
        1.0,
        [res("a01", True, False), res("a02", True, False)],
    )
    r2 = gen(1.0, 0, 1.0, [res("a01", True, False)])
    assert unstable_questions([r1, r2]) == ["a02"]


# ── Test 4: test_unstable_una_pasada ───────────────────────────────────────


def test_unstable_una_pasada():
    """Con una sola pasada, ninguna inestable."""
    r1 = gen(1.0, 0, 1.0, [res("a01", True, False)])
    assert unstable_questions([r1]) == []


# ── Test 5: test_summarize ─────────────────────────────────────────────────


def test_summarize():
    """Tres pasadas con kw=0.9/1.0/0.8, fr=0/1/2, total=0.7/0.8/0.75."""
    results = [res("a01", True, False)]
    r1 = gen(0.9, 0, 0.7, results)
    r2 = gen(1.0, 1, 0.8, results)
    r3 = gen(0.8, 2, 0.75, results)

    summary = summarize_runs([r1, r2, r3])
    assert summary.runs == 3
    assert summary.keyword_accuracy == pytest.approx(Stat(0.9, 0.8, 1.0), abs=1e-6)
    assert summary.false_refusals == Stat(1.0, 0.0, 2.0)
    assert summary.faithfulness == Stat(None, None, None)
    assert summary.avg_total_s.mean == pytest.approx(0.75)
    assert summary.unstable == []


# ── Test 6: test_summarize_vacio ───────────────────────────────────────────


def test_summarize_vacio():
    """sin pasadas → ValueError."""
    with pytest.raises(ValueError, match="sin pasadas"):
        summarize_runs([])


# ── Test 7: test_render_runs_table ─────────────────────────────────────────


def test_render_runs_table():
    """Tabla exacta de render_runs_table."""
    summary = RunsSummary(
        runs=3,
        keyword_accuracy=Stat(0.9, 0.8, 1.0),
        citation_precision=Stat(0.95, 0.9, 1.0),
        refusal_accuracy=Stat(1.0, 1.0, 1.0),
        false_refusals=Stat(2 / 3, 0.0, 1.0),
        faithfulness=Stat(None, None, None),
        avg_total_s=Stat(0.75, 0.7, 0.8),
        unstable=["q17", "d07"],
    )
    expected = [
        "| M\u00e9trica | Media | M\u00edn | M\u00e1x |",
        "| --- | ---: | ---: | ---: |",
        "| Palabras clave correctas | 0.900 | 0.800 | 1.000 |",
        "| Precisi\u00f3n de citas | 0.950 | 0.900 | 1.000 |",
        "| Rechazo correcto | 1.000 | 1.000 | 1.000 |",
        "| Falsos rechazos | 0.67 | 0 | 1 |",
        "| Tiempo total (media) | 0.75 s | 0.70 s | 0.80 s |",
        "",
        "Pasadas: 3 \u00b7 Preguntas inestables: q17, d07",
    ]
    assert render_runs_table(summary).split("\n") == expected


# ── Test 8: test_render_runs_table_con_juez ────────────────────────────────


def test_render_runs_table_con_juez():
    """Con faithfulness, línea extra y inestables vacío."""
    summary = RunsSummary(
        runs=3,
        keyword_accuracy=Stat(0.9, 0.8, 1.0),
        citation_precision=Stat(0.95, 0.9, 1.0),
        refusal_accuracy=Stat(1.0, 1.0, 1.0),
        false_refusals=Stat(2 / 3, 0.0, 1.0),
        faithfulness=Stat(0.9, 0.85, 0.95),
        avg_total_s=Stat(0.75, 0.7, 0.8),
        unstable=[],
    )
    lines = render_runs_table(summary).split("\n")
    assert lines[6] == "| Fidelidad (juez) | 0.900 | 0.850 | 0.950 |"
    assert lines[7] == "| Tiempo total (media) | 0.75 s | 0.70 s | 0.80 s |"
    assert lines[-1] == "Pasadas: 3 \u00b7 Preguntas inestables: \u2014"


# ── Test 9: test_render_results_varias_pasadas ─────────────────────────────


def test_render_results_varias_pasadas():
    """Múltiples pasadas en base → tabla de runs, sin tabla de una pasada."""
    g1 = gen(0.9, 0, 0.7, [res("a01", True, False)])
    g2 = gen(1.0, 0, 0.8, [res("a01", True, False)])
    text = render_results(
        date="d",
        llm_model="m",
        embedding_model="e",
        generation_chunk_size=800,
        retrieval=[],
        generation=None,
        generations={"base": [g1, g2]},
    )
    assert "| M\u00e9trica | Media | M\u00edn | M\u00e1x |" in text
    assert "Pasadas: 2" in text
    assert "| M\u00e9trica | Valor |" not in text


# ── Test 10: test_render_results_variantes_y_pasadas ──────────────────────


def test_render_results_variantes_y_pasadas():
    """Varias variantes con pasadas distintas."""
    g1 = gen(0.9, 0, 0.7, [res("a01", True, False)])
    g2 = gen(1.0, 0, 0.8, [res("a01", True, False)])
    text = render_results(
        date="d",
        llm_model="m",
        embedding_model="e",
        generation_chunk_size=800,
        retrieval=[],
        generation=None,
        generations={"base": [g1, g2], "top3": [g1]},
    )
    count_media = text.count("| M\u00e9trica | Media | M\u00edn | M\u00e1x |")
    count_valor = text.count("| M\u00e9trica | Valor |")
    assert count_media == 1
    assert count_valor == 1


# ── Test 11: test_run_variant_tres_pasadas ─────────────────────────────────


def test_run_variant_tres_pasadas(base: Settings, tmp_path: Path):
    """Tres pasadas con SameChat."""
    from docuchat.evaluation.run import run_variant
    from docuchat.retrieval.searcher import SearchMode

    same = SameChat("Respuesta [1].")
    fake = FakeEmbedder()
    patches = [
        mock.patch(
            "docuchat.index.indexer.make_embedder",
            return_value=fake,
        ),
        mock.patch(
            "docuchat.retrieval.searcher.make_embedder",
            return_value=fake,
        ),
        mock.patch(
            "docuchat.generation.answer.make_chat_model",
            return_value=same,
        ),
    ]
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        result = run_variant(
            base,
            load_questions(QUESTIONS),
            variant="base",
            chunk_sizes=[800],
            modes=[SearchMode.BM25],
            data_root=tmp_path / "ev",
            generation_chunk_size=800,
            runs=3,
            embedder=fake,
            chat=same,
        )

    assert len(result.generations) == 3
    for g in result.generations:
        assert g.questions == 42
        assert g.variant == "base"


# ── Test 12: test_run_variant_runs_cero ────────────────────────────────────


def test_run_variant_runs_cero(base: Settings, tmp_path: Path):
    """runs=0 → ValueError."""
    from docuchat.evaluation.run import run_variant
    from docuchat.retrieval.searcher import SearchMode

    with pytest.raises(ValueError, match="runs debe ser al menos 1"):
        run_variant(
            base,
            load_questions(QUESTIONS),
            variant="base",
            chunk_sizes=[800],
            modes=[SearchMode.BM25],
            data_root=tmp_path / "ev",
            generation_chunk_size=800,
            runs=0,
            embedder=FakeEmbedder(),
        )


# ── Test 13: test_main_runs_cero ──────────────────────────────────────────


def test_main_runs_cero(base: Settings, tmp_path: Path):
    """--runs 0 → SystemExit(2)."""
    with pytest.raises(SystemExit) as exc_info:
        run_main(
            [
                "--skip-llm",
                "--runs",
                "0",
                "--chunk-sizes",
                "800",
                "--modes",
                "bm25",
                "--data-root",
                str(tmp_path / "d"),
                "--out",
                str(tmp_path / "r.md"),
                "--json",
                str(tmp_path / "r.json"),
                "--questions",
                str(QUESTIONS),
                "--documents-dir",
                str(SAMPLES),
            ]
        )
    assert exc_info.value.code == 2


# ── Test 14: test_main_dos_pasadas ─────────────────────────────────────────


def test_main_dos_pasadas(base: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """--runs 2, SameChat, sin juez → inestables vacías."""
    same = SameChat("Respuesta [1].")
    same_judge = SameChat('{"supported": true, "unsupported": []}')
    fake = FakeEmbedder()
    monkeypatch.setitem(VARIANTS, "top3", {"top_k": 3})

    patches = [
        mock.patch(
            "docuchat.index.indexer.make_embedder",
            return_value=fake,
        ),
        mock.patch(
            "docuchat.retrieval.searcher.make_embedder",
            return_value=fake,
        ),
        mock.patch(
            "docuchat.generation.answer.make_chat_model",
            return_value=same,
        ),
        mock.patch(
            "docuchat.evaluation.run.make_chat_model",
            return_value=same_judge,
        ),
    ]
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        rc = run_main(
            [
                "--runs",
                "2",
                "--chunk-sizes",
                "800",
                "--modes",
                "bm25",
                "--data-root",
                str(tmp_path / "d"),
                "--out",
                str(tmp_path / "r.md"),
                "--json",
                str(tmp_path / "r.json"),
                "--questions",
                str(QUESTIONS),
                "--documents-dir",
                str(SAMPLES),
            ]
        )

    assert rc == 0
    md_content = (tmp_path / "r.md").read_text(encoding="utf-8")
    assert "Pasadas: 2 \u00b7 Preguntas inestables: \u2014" in md_content
    json_data = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert len(json_data["generations"]["base"]) == 2
