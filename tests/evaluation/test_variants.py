"""Tests para src/docuchat/evaluation/variants.py, run.py y report.py — 16 tests obligatorios."""

import dataclasses
import json
import os
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

from docuchat.config import Settings
from docuchat.evaluation.dataset import load_questions
from docuchat.evaluation.report import (
    render_category_table,
    render_results,
    render_retrieval_table,
)
from docuchat.evaluation.run import main as run_main
from docuchat.evaluation.runner import (
    GenerationReport,
    RetrievalReport,
)
from docuchat.evaluation.variants import (
    VARIANTS,
    parse_variants,
    variant_settings,
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


# ── Fixture base ──────────────────────────────────────────────────────────


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
def preguntas_v1():
    """Preguntas reales del dataset."""
    return load_questions(QUESTIONS)


# ── Test 1: variantes por defecto ────────────────────────────────────────


def test_variants_por_defecto():
    """Solo base está vacía."""
    assert VARIANTS["base"] == {}


# ── Test 2: parse_variants ───────────────────────────────────────────────


def test_parse_variants():
    """Casos básicos de parseado."""
    assert parse_variants("base") == ["base"]
    assert parse_variants(" base , ") == ["base"]
    monkeypatch_setitem(VARIANTS, "top3", {"top_k": 3})
    assert parse_variants("top3,base") == ["top3", "base"]


# ── Test 3: parse_variants_errores (parametrizado) ───────────────────────


@pytest.mark.parametrize(
    ("text, expected_msg_start"),
    [
        ("", "indica al menos una variante"),
        ("base,base", "variante repetida: base"),
        ("base,nope", "variante desconocida: nope"),
    ],
)
def test_parse_variants_errores(text: str, expected_msg_start: str):
    """Parseo con entrada inválida lanza ValueError con el mensaje correcto."""
    with pytest.raises(ValueError) as exc_info:
        parse_variants(text)
    assert str(exc_info.value).startswith(expected_msg_start)


# ── Test 4: variant_settings ─────────────────────────────────────────────


def test_variant_settings(base: Settings):
    """Aplica cambios y no modifica base."""
    monkeypatch_setitem(VARIANTS, "top3", {"top_k": 3})
    result = variant_settings(base, "top3")
    assert result.top_k == 3
    assert base.top_k == 5
    assert variant_settings(base, "base").model_dump() == base.model_dump()


# ── Test 5: variant_settings_errores (parametrizado) ─────────────────────


@pytest.mark.parametrize(
    ("variant_name, changes, expected_msg"),
    [
        ("nope", None, None),
        ("mala", {"no_existe": 1}, "ajuste desconocido en la variante mala: no_existe"),
    ],
)
def test_variant_settings_errores(
    base: Settings, variant_name: str, changes: dict | None, expected_msg: str | None
):
    """Variantes desconocidas o con ajustes inválidos lanzan ValueError."""
    if changes is not None:
        monkeypatch_setitem(VARIANTS, variant_name, changes)
    with pytest.raises(ValueError) as exc_info:
        variant_settings(base, variant_name)
    if expected_msg:
        assert str(exc_info.value) == expected_msg


# ── Test 6: run_variant ──────────────────────────────────────────────────


def test_run_variant(base: Settings, tmp_path: Path, preguntas_v1):
    """Evalúa una variante con top3, modo BM25, chunk 800, sin generación."""
    monkeypatch_setitem(VARIANTS, "top3", {"top_k": 3})
    from docuchat.evaluation.run import run_variant

    result = run_variant(
        base,
        list(preguntas_v1),
        variant="top3",
        chunk_sizes=[800],
        modes=[SearchMode.BM25],
        data_root=tmp_path / "ev",
        generation_chunk_size=None,
        embedder=FakeEmbedder(),
    )
    assert result.variant == "top3"
    assert [r.variant for r in result.retrieval] == ["top3"]
    assert result.retrieval[0].hit_at_1 == pytest.approx(28 / 32)
    assert result.generations == []
    assert (tmp_path / "ev" / "top3" / "cs800").is_dir()


# ── Test 7: run_evaluation_compatible ────────────────────────────────────


def test_run_evaluation_compatible(base: Settings, tmp_path: Path, preguntas_v1):
    """run_evaluation mantiene la misma firma y comportamiento."""
    from docuchat.evaluation.run import run_evaluation

    reports, generation = run_evaluation(
        base,
        list(preguntas_v1),
        chunk_sizes=[800],
        modes=[SearchMode.BM25],
        data_root=tmp_path / "eval",
        generation_chunk_size=None,
        embedder=FakeEmbedder(),
    )
    assert reports[0].variant == "base"
    assert generation is None


# ── Test 8: render_retrieval_table con variantes ─────────────────────────


def test_render_retrieval_table_con_variantes():
    """Tabla con columna Variante cuando hay variantes no-base."""
    reports = [
        RetrievalReport(
            chunk_size=800,
            mode="bm25",
            chunks=26,
            questions=32,
            hit_at_1=0.84375,
            hit_at_5=1.0,
            mrr=0.9088541666666666,
            misses=[],
            variant="base",
        ),
        RetrievalReport(
            chunk_size=800,
            mode="bm25",
            chunks=26,
            questions=32,
            hit_at_1=0.84375,
            hit_at_5=1.0,
            mrr=0.9088541666666666,
            misses=[],
            variant="top3",
        ),
    ]
    lines = render_retrieval_table(reports).split("\n")
    assert lines == [
        "| Variante | Chunk | Modo | Chunks | Hit@1 | Hit@5 | MRR@10 | Fallos (top 5) |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
        "| base | 800 | bm25 | 26 | 0.844 | 1.000 | 0.909 | — |",
        "| top3 | 800 | bm25 | 26 | 0.844 | 1.000 | 0.909 | — |",
    ]


# ── Test 9: render_results una generación igual ──────────────────────────


def test_render_results_una_generacion_igual(base: Settings):
    """generations={"base": [g]} produce el mismo texto que generation=g."""
    g = GenerationReport(
        questions=42,
        answerable=32,
        unanswerable=10,
        keyword_accuracy=0.96875,
        citation_precision=1.0,
        refusal_accuracy=1.0,
        false_refusals=1,
        avg_first_token_s=0.456,
        avg_total_s=0.61,
        results=[],
    )
    a = render_results(
        date="2025-01-01 12:00",
        llm_model="test",
        embedding_model="test",
        generation_chunk_size=800,
        retrieval=[],
        generation=None,
        generations={"base": [g]},
    )
    b = render_results(
        date="2025-01-01 12:00",
        llm_model="test",
        embedding_model="test",
        generation_chunk_size=800,
        retrieval=[],
        generation=g,
    )
    assert a == b


# ── Test 10: render_results varias variantes ─────────────────────────────


def test_render_results_varias_variantes():
    """Múltiples variantes generan secciones individuales."""
    g = GenerationReport(
        questions=42,
        answerable=32,
        unanswerable=10,
        keyword_accuracy=0.96875,
        citation_precision=1.0,
        refusal_accuracy=1.0,
        false_refusals=1,
        avg_first_token_s=0.456,
        avg_total_s=0.61,
        results=[],
    )
    text = render_results(
        date="2025-01-01 12:00",
        llm_model="test",
        embedding_model="test",
        generation_chunk_size=800,
        retrieval=[],
        generation=None,
        generations={"base": [g], "top3": [dataclasses.replace(g, variant="top3")]},
    )
    assert "### Variante `base`" in text
    assert "### Variante `top3`" in text
    assert text.count("| Métrica | Valor |") == 2


# ── Test 11: render_results questions_file ───────────────────────────────


def test_render_results_questions_file():
    """questions_file aparece en el texto introductorio."""
    text = render_results(
        date="2025-01-01 12:00",
        llm_model="test",
        embedding_model="test",
        generation_chunk_size=None,
        retrieval=[],
        generation=None,
        questions_file="eval/questions_v2.jsonl",
    )
    assert "Preguntas con respuesta de `eval/questions_v2.jsonl`" in text


# ── Test 12: category_labels con variantes ───────────────────────────────


def test_category_labels_con_variantes():
    """Las columnas muestran Hit@1 {variant}/{mode}."""
    from docuchat.evaluation.categories import CategoryScores

    report = RetrievalReport(
        chunk_size=800,
        mode="bm25",
        chunks=26,
        questions=32,
        hit_at_1=0.84375,
        hit_at_5=1.0,
        mrr=0.9088541666666666,
        misses=[],
        variant="top3",
        by_category={"literal": CategoryScores(10, 0.9, 1.0, 0.95)},
    )
    lines = render_category_table([report], None, 800).split("\n")
    assert lines[0] == "| Categoría | Preguntas | Hit@1 top3/bm25 |"


# ── Test 13: main dos variantes ──────────────────────────────────────────


def test_main_dos_variantes(base: Settings, tmp_path: Path):
    """main con --variants base,top3 → tabla con columnas variantes."""
    monkeypatch_setitem(VARIANTS, "top3", {"top_k": 3})
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
                "--variants",
                "base,top3",
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
    assert "| base | 800 | bm25 | 26 | 0.875 | 1.000 | 0.920 | — |" in md_content
    assert "| top3 | 800 | bm25 | 26 | 0.875 | 1.000 | 0.920 | — |" in md_content
    json_data = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert json_data["variants"] == ["base", "top3"]
    assert json_data["generations"] == {}
    assert json_data["generation"] is None


# ── Test 14: main variante desconocida ───────────────────────────────────


def test_main_variante_desconocida(base: Settings, tmp_path: Path):
    """--variants con nombre inválido → SystemExit(2)."""
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
        with pytest.raises(SystemExit) as exc_info:
            run_main(
                [
                    "--skip-llm",
                    "--variants",
                    "nope",
                    "--data-root",
                    str(tmp_path / "d"),
                    "--questions",
                    str(QUESTIONS),
                    "--documents-dir",
                    str(SAMPLES),
                ]
            )
    assert exc_info.value.code == 2


# ── Helpers ───────────────────────────────────────────────────────────────


def monkeypatch_setitem(d: dict, key: str, value: object) -> None:
    """Ayuda para añadir variantes temporalmente en tests."""
    d[key] = value
