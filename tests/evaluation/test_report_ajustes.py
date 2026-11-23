"""Tests para ajustes de report.py tras 083–086 — 5 tests obligatorios."""

from docuchat.evaluation.categories import CategoryScores
from docuchat.evaluation.report import render_generation_table, render_results
from docuchat.evaluation.runner import GenerationReport, QuestionResult, RetrievalReport

# ── Datos comunes ──────────────────────────────────────────────────────────

R2 = RetrievalReport(
    chunk_size=800,
    mode="hybrid",
    chunks=73,
    questions=70,
    hit_at_1=0.7,
    hit_at_5=0.8,
    mrr=0.75,
    by_category={"literal": CategoryScores(10, 0.9, 1.0, 0.95)},
)
G2 = GenerationReport(
    questions=80,
    answerable=70,
    unanswerable=10,
    keyword_accuracy=0.9,
    citation_precision=0.9,
    refusal_accuracy=1.0,
    false_refusals=0,
    avg_first_token_s=0.5,
    avg_total_s=0.7,
    keywords_by_category={"literal": 1.0},
)
KW = dict(
    date="d",
    llm_model="m",
    embedding_model="e",
    generation_chunk_size=800,
    retrieval=[R2],
)


# ── Test 1: categorías vía generations ─────────────────────────────────────


def test_categorias_via_generations():
    """render_results con generations={"base": [G2]} contiene columna 'Palabras clave'."""
    text_via_gen = render_results(
        generation=None,
        generations={"base": [G2]},
        **KW,
    )
    assert "| Categoría | Preguntas | Hit@1 hybrid | Palabras clave |" in text_via_gen
    assert "| literal | 10 | 0.900 | 1.000 |" in text_via_gen

    # Byte a byte idéntico a render_results(generation=G2, ...)
    text_direct = render_results(generation=G2, **KW)
    assert text_via_gen == text_direct


# ── Test 2: categorías varias pasadas ─────────────────────────────────────


def test_categorias_varias_pasadas():
    """Con varias pasadas, no aparece 'Palabras clave'."""
    assert "| Categoría | Preguntas | Hit@1 hybrid |" in render_results(
        generation=G2,
        generations={"base": [G2, G2]},
        **KW,
    )
    assert "Palabras clave |" not in render_results(
        generation=G2,
        generations={"base": [G2, G2]},
        **KW,
    )


# ── Test 3: nota juez ─────────────────────────────────────────────────────


def test_nota_juez():
    """Con judge_model == llm_model, la nota aparece con una sola línea en blanco."""
    lines = render_results(
        generation=G2,
        judge_model="m",
        **KW,
    ).split("\n")[:7]
    assert lines == [
        "# Resultados de la evaluación",
        "",
        "Fecha: d · LLM: `m` · Embeddings: `e` · Juez: `m`",
        "",
        "Nota: el juez es el mismo modelo que responde; la fidelidad es orientativa.",
        "",
        "## Recuperación",
    ]


# ── Test 4: sin nota ──────────────────────────────────────────────────────


def test_sin_nota():
    """Con judge_model != llm_model, sin línea de nota."""
    lines = render_results(
        generation=G2,
        judge_model="otro",
        **KW,
    ).split("\n")
    assert lines[3:5] == ["", "## Recuperación"]


# ── Test 5: separador sin respaldo ────────────────────────────────────────


def test_separador_sin_respaldo():
    """Las afirmaciones sin respaldo se unen con ' ; '."""
    report = GenerationReport(
        questions=80,
        answerable=70,
        unanswerable=10,
        keyword_accuracy=0.9,
        citation_precision=0.9,
        refusal_accuracy=1.0,
        false_refusals=0,
        avg_first_token_s=0.5,
        avg_total_s=0.7,
        results=[
            QuestionResult(
                id="a02",
                answerable=True,
                answer="x",
                no_answer=False,
                keywords_ok=True,
                citations_correct=1,
                citations_total=1,
                first_token_s=0.1,
                total_s=0.2,
                faithful=False,
                unsupported=["A", "B   c"],
            )
        ],
        judged=1,
    )
    text = render_generation_table(report)
    assert "- a02: A; B c" in text
