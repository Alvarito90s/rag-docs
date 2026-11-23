"""Tests para src/docuchat/evaluation/report.py y run.py — 8 tests obligatorios."""

import json
import os
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

from docuchat.config import Settings
from docuchat.evaluation.dataset import load_questions
from docuchat.evaluation.report import (
    render_generation_table,
    render_results,
    render_retrieval_table,
)
from docuchat.evaluation.run import main as run_main
from docuchat.evaluation.runner import (
    GenerationReport,
    QuestionResult,
    RetrievalReport,
)
from docuchat.generation.prompts import NO_ANSWER, Message
from docuchat.retrieval.searcher import SearchMode

# ── Rutas al dataset y samples ────────────────────────────────────────────

QUESTIONS = Path(__file__).resolve().parents[2] / "eval" / "questions.jsonl"
SAMPLES = Path(__file__).resolve().parents[2] / "samples"

# ── FakeEmbedder ──────────────────────────────────────────────────────────


class FakeEmbedder:
    """Embedder determinista que no toca red."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[float(len(t)), 1.0, 0.5] for t in texts]


# ── RefuseChat ────────────────────────────────────────────────────────────


class RefuseChat:
    """ChatModel cuyo stream siempre emite NO_ANSWER."""

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        yield NO_ANSWER


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture()
def base(tmp_path: Path):
    """Settings limpia sin vars de entorno."""
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            os.environ.pop(key)
    tmp_path.chmod(0o755)
    os.chdir(tmp_path)
    return Settings(documents_dir=SAMPLES)


@pytest.fixture()
def preguntas():
    """Preguntas reales del dataset."""
    return load_questions(QUESTIONS)


# ── Test 1: fmt y fmt_seconds ─────────────────────────────────────────────


def test_1_fmt_and_fmt_seconds():
    """fmt(0.84375) == '0.844', fmt(None) == '—', fmt_seconds(0.456) == '0.46 s'."""
    from docuchat.evaluation.report import fmt, fmt_seconds

    assert fmt(0.84375) == "0.844"
    assert fmt(None) == "\u2014"
    assert fmt_seconds(0.456) == "0.46 s"
    assert fmt_seconds(None) == "\u2014"


# ── Test 2: render_retrieval_table ────────────────────────────────────────


def test_2_render_retrieval_table():
    """Las 4 líneas exactas (cabecera, separador, 2 filas)."""
    reports = [
        RetrievalReport(
            chunk_size=800,
            mode="bm25",
            chunks=26,
            questions=32,
            hit_at_1=0.875,
            hit_at_5=1.0,
            mrr=0.9203125,
            misses=[],
        ),
        RetrievalReport(
            chunk_size=500,
            mode="vector",
            chunks=45,
            questions=32,
            hit_at_1=0.9,
            hit_at_5=0.95,
            mrr=0.92,
            misses=["q03", "q17"],
        ),
    ]
    lines = render_retrieval_table(reports).split("\n")
    assert len(lines) == 4
    assert lines[0] == "| Chunk | Modo | Chunks | Hit@1 | Hit@5 | MRR@10 | Fallos (top 5) |"
    assert lines[1] == "| ---: | --- | ---: | ---: | ---: | ---: | --- |"
    assert lines[2] == "| 800 | bm25 | 26 | 0.875 | 1.000 | 0.920 | — |"
    assert lines[3] == "| 500 | vector | 45 | 0.900 | 0.950 | 0.920 | q03, q17 |"


# ── Test 3: render_generation_table ──────────────────────────────────────


def test_3_render_generation_table():
    """Tabla exacta de 9 líneas + sección Fallos."""
    report = GenerationReport(
        questions=42,
        answerable=32,
        unanswerable=10,
        keyword_accuracy=0.96875,
        citation_precision=1.0,
        refusal_accuracy=1.0,
        false_refusals=1,
        avg_first_token_s=0.456,
        avg_total_s=0.61,
        results=[
            QuestionResult(
                id="q17",
                answerable=True,
                answer="No lo sé con la información de los documentos.",
                no_answer=False,
                keywords_ok=False,
                citations_correct=0,
                citations_total=0,
                first_token_s=0.4,
                total_s=0.5,
            )
        ],
    )
    text = render_generation_table(report)
    lines = text.split("\n")
    # 9 líneas de tabla
    assert len(lines) >= 9
    assert lines[0] == "| Métrica | Valor |"
    assert lines[1] == "| --- | ---: |"
    assert lines[2] == "| Preguntas | 42 (32 con respuesta, 10 sin respuesta) |"
    assert lines[3] == "| Palabras clave correctas | 0.969 |"
    assert lines[4] == "| Precisión de citas | 1.000 |"
    assert lines[5] == "| Rechazo correcto | 1.000 |"
    assert lines[6] == "| Falsos rechazos | 1 |"
    assert lines[7] == "| Primer token (media) | 0.46 s |"
    assert lines[8] == "| Tiempo total (media) | 0.61 s |"
    # Sección de fallos
    assert "Fallos:" in text
    assert "- q17: No lo sé con la información de los documentos." in text


# ── Test 4: render_results sin generación ────────────────────────────────


def test_4_render_results_no_generation():
    """Contiene encabezados y 'No ejecutada (--skip-llm).'."""
    text = render_results(
        date="2025-01-01 12:00",
        llm_model="Qwen3.6-35B-A3B-6bit",
        embedding_model="Qwen3-Embedding-0.6B-4bit-DWQ",
        generation_chunk_size=None,
        retrieval=[],
        generation=None,
    )
    assert "# Resultados de la evaluación" in text
    assert "## Recuperación" in text
    assert "No ejecutada (--skip-llm)." in text
    assert text.endswith("\n")


# ── Test 5: run_evaluation con skip-llm ──────────────────────────────────


def test_5_run_evaluation_skip_llm(base: Settings, tmp_path: Path, preguntas):
    """Un informe con hit_at_1 ≈ 27/32 y generación None."""
    from docuchat.evaluation.run import run_evaluation

    reports, generation = run_evaluation(
        base,
        list(preguntas),
        chunk_sizes=[800],
        modes=[SearchMode.BM25],
        data_root=tmp_path / "eval",
        generation_chunk_size=None,
        embedder=FakeEmbedder(),
    )
    assert len(reports) == 1
    assert reports[0].hit_at_1 == pytest.approx(28 / 32)
    assert generation is None


# ── Test 6: run_evaluation con generación ────────────────────────────────


def test_6_run_evaluation_with_generation(base: Settings, tmp_path: Path, preguntas):
    """generation.questions == 42, false_refusals == 32, refusal_accuracy == 1.0."""
    from docuchat.evaluation.run import run_evaluation

    reports, generation = run_evaluation(
        base,
        list(preguntas),
        chunk_sizes=[800],
        modes=[SearchMode.BM25],
        data_root=tmp_path / "eval",
        generation_chunk_size=800,
        embedder=FakeEmbedder(),
        chat=RefuseChat(),
    )
    assert generation is not None
    assert generation.questions == 42
    assert generation.false_refusals == 32
    assert generation.refusal_accuracy == 1.0


# ── Test 7: main con skip-llm ────────────────────────────────────────────


def test_7_main_skip_llm(base: Settings, tmp_path: Path):
    """main con embedder fake → 0, r.md contiene la fila esperada, JSON correcto."""
    import contextlib
    import unittest.mock as mock

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
    ]
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        rc = run_main(
            [
                "--skip-llm",
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
    assert "| 800 | bm25 | 26 | 0.875 | 1.000 | 0.920 | — |" in md_content
    json_data = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert json_data["retrieval"][0]["hit_at_1"] == pytest.approx(28 / 32)
    assert json_data["generation"] is None


# ── Test 8: main con error de servidor ───────────────────────────────────


def test_8_main_server_error(base: Settings, tmp_path: Path, capsys):
    """main con un embedder que lanza error → devuelve 1 y stderr contiene el error."""
    import contextlib
    import unittest.mock as mock

    from openai import APIConnectionError

    def failing_make_embedder(*args, **kwargs):
        from unittest.mock import MagicMock

        raise APIConnectionError(message="Connection failed", request=MagicMock())

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
            side_effect=failing_make_embedder,
        ),
    ]
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        rc = run_main(
            [
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

    assert rc == 1
    stderr = capsys.readouterr().err
    assert "Error con el servidor de modelos: APIConnectionError" in stderr


# ── Test 9: Fallos sin recortar ──────────────────────────────────────────


def test_9_fallos_sin_recortar():
    """Todos los misses aparecen, sin recortar a 5."""
    report = RetrievalReport(
        chunk_size=800,
        mode="bm25",
        chunks=26,
        questions=32,
        hit_at_1=0.5,
        hit_at_5=0.8,
        mrr=0.6,
        misses=["q01", "q02", "q03", "q04", "q05", "q06"],
    )
    lines = render_retrieval_table([report]).split("\n")
    assert "| q01, q02, q03, q04, q05, q06 |" in lines[2]


# ── Test 10: Error que no es del servidor ────────────────────────────────


def test_10_error_no_servidor(base: Settings, tmp_path: Path):
    """RuntimeError no capturada se propaga."""
    import contextlib
    import unittest.mock as mock

    def boom(*args, **kwargs):
        raise RuntimeError("Errores al indexar: roto.pdf")

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
            "docuchat.evaluation.run.build_eval_index",
            side_effect=boom,
        ),
    ]
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        with pytest.raises(RuntimeError, match="roto.pdf"):
            run_main(
                [
                    "--skip-llm",
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
