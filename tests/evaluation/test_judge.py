"""Tests para el juez de fidelidad — 23 tests obligatorios."""

import json
import os
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

import pytest

from docuchat.evaluation.dataset import EvalQuestion
from docuchat.evaluation.judge import (
    JUDGE_PROMPT,
    NO_CITATIONS,
    Judge,
    Verdict,
    build_judge_messages,
    cited_passages,
    parse_verdict,
)
from docuchat.evaluation.report import (
    render_generation_table,
    render_results,
)
from docuchat.evaluation.runner import (
    GenerationReport,
    QuestionResult,
    evaluate_generation,
)
from docuchat.generation.answer import Answer, Answerer, Source
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


class ScriptChat:
    """Cada stream devuelve la siguiente respuesta de la cola y guarda los mensajes."""

    def __init__(self, answers: list[str]) -> None:
        self.answers = list(answers)
        self.calls: list[list[Message]] = []

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        self.calls.append(list(messages))
        yield self.answers.pop(0)


class SameChat:
    """Siempre la misma respuesta."""

    def __init__(self, text: str) -> None:
        self.text = text

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        yield self.text


def fake_clock(values: list[float]) -> Callable[[], float]:
    it = iter(values)
    return lambda: next(it)


# ── Test 1: test_prompt_literal ──────────────────────────────────────────────


def test_prompt_literal():
    """JUDGE_PROMPT empieza por 'Eres un revisor estricto.' y contiene
    '"supported"' y '"unsupported"'."""
    assert JUDGE_PROMPT.startswith("Eres un revisor estricto.")
    assert '"supported"' in JUDGE_PROMPT
    assert '"unsupported"' in JUDGE_PROMPT


# ── Test 2: test_parse_valido ───────────────────────────────────────────────


def test_parse_valido():
    """JSON válido con supported=true."""
    assert parse_verdict('{"supported": true, "unsupported": []}') == Verdict(True, [])


# ── Test 3: test_parse_con_texto_alrededor ──────────────────────────────────


def test_parse_con_texto_alrededor():
    """JSON dentro de un bloque markdown con texto alrededor."""
    result = parse_verdict('Aquí va:\n```json\n{"supported": false, "unsupported": ["X"]}\n```')
    assert result == Verdict(False, ["X"])


# ── Test 4: test_parse_incoherente ──────────────────────────────────────────


def test_parse_incoherente():
    """supported=true pero hay afirmaciones sin respaldo → False."""
    assert parse_verdict('{"supported": true, "unsupported": ["Y"]}') == Verdict(False, ["Y"])


# ── Test 5: test_parse_sin_lista ────────────────────────────────────────────


def test_parse_sin_lista():
    """Sin campo unsupported → usa []."""
    assert parse_verdict('{"supported": true}') == Verdict(True, [])


# ── Test 6: test_parse_invalido (parametrizado, 6 casos) ───────────────────


@pytest.mark.parametrize(
    "input_text",
    [
        "no es json",
        '{"supported": "sí"}',
        '{"supported": true, "unsupported": "x"}',
        '{"supported": true, "unsupported": [1]}',
        "{roto}",
        "[]",
    ],
)
def test_parse_invalido(input_text: str):
    """Todos estos inputs devuelven None."""
    assert parse_verdict(input_text) is None


# ── Test 7: test_build_judge_messages ───────────────────────────────────────


def test_build_judge_messages():
    """2 mensajes, system con JUDGE_PROMPT, user con formato exacto."""
    msgs = build_judge_messages("¿P?", "R [1].", ["Uno.", "Dos."])
    assert len(msgs) == 2
    assert msgs[0] == {"role": "system", "content": JUDGE_PROMPT}
    expected_user = (
        "Pregunta: ¿P?\n\nRespuesta: R [1].\n\nFragmentos citados:\n[1] Uno.\n\n[2] Dos."
    )
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == expected_user


# ── Test 8: test_judge_llama_al_llm ────────────────────────────────────────


def test_judge_llama_al_llm():
    """Judge llama al LLM y devuelve el Verdict."""
    chat = ScriptChat(['{"supported": true, "unsupported": []}'])
    result = Judge(chat).judge("¿P?", "R", ["Uno."])
    assert result == Verdict(True, [])
    assert len(chat.calls) == 1


# ── Test 9: test_judge_sin_fragmentos ──────────────────────────────────────


def test_judge_sin_fragmentos():
    """Sin fragmentos, no llama al LLM y devuelve Verdict(False, [NO_CITATIONS])."""
    chat = ScriptChat(["no debería llegarse"])
    result = Judge(chat).judge("¿P?", "R", [])
    assert result == Verdict(False, [NO_CITATIONS])
    assert len(chat.calls) == 0


# ── Test 10: test_cited_passages ───────────────────────────────────────────


def test_cited_passages():
    """Recorre sources en orden, sin repetir, filtra por rango válido."""
    answer = Answer(
        question="q",
        text="t",
        sources=[Source(2, "b.md", 2), Source(1, "a.pdf", 1), Source(2, "b.md", 2)],
        invalid_citations=[],
        no_answer=False,
        context=CONTEXT,
    )
    assert cited_passages(answer) == ["Beta.", "Alfa."]


# ── Test 11: test_generacion_con_juez ──────────────────────────────────────


def test_generacion_con_juez():
    """evalu_generation con judge: 2 juzgadas, 1 no juzgable (rechazo)."""
    A = EvalQuestion(
        id="a01",
        question="¿Alfa?",
        expected_doc="a.pdf",
        expected_page=1,
        answer_keywords=["alfa"],
        answerable=True,
    )
    A2 = EvalQuestion(
        id="a02",
        question="¿Alfa?",
        expected_doc="a.pdf",
        expected_page=1,
        answer_keywords=["alfa"],
        answerable=True,
    )
    U = EvalQuestion(id="u01", question="¿Y?", answerable=False)

    answerer = Answerer(
        FakeRetriever(),
        ScriptChat(["Es alfa [1].", NO_ANSWER, "Inventado [1]."]),
        top_k=5,
        context_max_chars=6000,
    )
    juez = Judge(
        ScriptChat(
            [
                '{"supported": true, "unsupported": []}',
                '{"supported": false, "unsupported": ["Inventado"]}',
            ]
        )
    )

    report = evaluate_generation(answerer, [A, U, A2], judge=juez)

    assert report.judged == 2
    assert report.unjudged == 0
    assert report.faithfulness == 0.5
    assert [r.faithful for r in report.results] == [True, None, False]
    assert report.results[2].unsupported == ["Inventado"]


# ── Test 12: test_generacion_juez_ilegible ─────────────────────────────────


def test_generacion_juez_ilegible():
    """Juez responde texto no JSON → unjudged=1."""
    A = EvalQuestion(
        id="a01",
        question="¿Alfa?",
        expected_doc="a.pdf",
        expected_page=1,
        answer_keywords=["alfa"],
        answerable=True,
    )

    answerer = Answerer(
        FakeRetriever(),
        ScriptChat(["Es alfa [1]."]),
        top_k=5,
        context_max_chars=6000,
    )
    juez = Judge(ScriptChat(["no sé"]))

    report = evaluate_generation(answerer, [A], judge=juez)

    assert report.judged == 0
    assert report.unjudged == 1
    assert report.faithfulness is None
    assert report.results[0].faithful is None


# ── Test 13: test_generacion_sin_juez ──────────────────────────────────────


def test_generacion_sin_juez():
    """Sin judge → judged=0, unjudged=0, faithful=None."""
    A = EvalQuestion(
        id="a01",
        question="¿Alfa?",
        expected_doc="a.pdf",
        expected_page=1,
        answer_keywords=["alfa"],
        answerable=True,
    )

    answerer = Answerer(
        FakeRetriever(),
        ScriptChat(["Es alfa [1]."]),
        top_k=5,
        context_max_chars=6000,
    )

    report = evaluate_generation(answerer, [A])

    assert report.judged == 0
    assert report.unjudged == 0
    assert report.faithfulness is None
    assert report.results[0].faithful is None


# ── Test 14: test_tabla_con_fidelidad ──────────────────────────────────────


def test_tabla_con_fidelidad():
    """Tabla con fidelidad: línea 7 es 'Fidelidad (juez)', sección 'Sin respaldo'."""
    report = GenerationReport(
        questions=2,
        answerable=2,
        unanswerable=0,
        keyword_accuracy=1.0,
        citation_precision=1.0,
        refusal_accuracy=None,
        false_refusals=0,
        avg_first_token_s=0.5,
        avg_total_s=1.0,
        judged=2,
        unjudged=1,
        faithfulness=0.5,
        results=[
            QuestionResult(
                id="a02",
                answerable=True,
                answer="Inventado [1].",
                no_answer=False,
                keywords_ok=True,
                citations_correct=1,
                citations_total=1,
                first_token_s=0.5,
                total_s=1.0,
                faithful=False,
                unsupported=["Inventado"],
            )
        ],
    )
    lines = render_generation_table(report).split("\n")
    assert lines[6] == "| Falsos rechazos | 0 |"
    assert lines[7] == "| Fidelidad (juez) | 0.500 (2 juzgadas, 1 sin juzgar) |"
    assert lines[8] == "| Primer token (media) | 0.50 s |"
    text = "\n".join(lines)
    assert "Sin respaldo según el juez:" in text
    assert "- a02: Inventado" in text


# ── Test 15: test_tabla_sin_juez ───────────────────────────────────────────


def test_tabla_sin_juez():
    """Sin juez → tabla normal sin 'Fidelidad' ni 'Sin respaldo'."""
    report = GenerationReport(
        questions=2,
        answerable=2,
        unanswerable=0,
        keyword_accuracy=1.0,
        citation_precision=1.0,
        refusal_accuracy=None,
        false_refusals=0,
        avg_first_token_s=0.5,
        avg_total_s=1.0,
        judged=0,
        unjudged=0,
        faithfulness=None,
        results=[
            QuestionResult(
                id="a02",
                answerable=True,
                answer="Inventado [1].",
                no_answer=False,
                keywords_ok=True,
                citations_correct=1,
                citations_total=1,
                first_token_s=0.5,
                total_s=1.0,
                faithful=None,
                unsupported=[],
            )
        ],
    )
    text = render_generation_table(report)
    assert "Fidelidad" not in text
    assert "Sin respaldo" not in text


# ── Test 16: test_render_results_juez (3 casos) ────────────────────────────


def test_render_results_juez_mismo_modelo():
    """judge_model == llm_model → 'Nota: el juez es el mismo modelo...'."""
    text = render_results(
        date="2025-01-01 12:00",
        llm_model="m",
        embedding_model="e",
        generation_chunk_size=None,
        retrieval=[],
        generation=None,
        judge_model="m",
    )
    assert "· Juez: `m`" in text
    assert "Nota: el juez es el mismo modelo que responde; la fidelidad es orientativa." in text


def test_render_results_juez_diferente_modelo():
    """judge_model != llm_model → sin nota."""
    text = render_results(
        date="2025-01-01 12:00",
        llm_model="m",
        embedding_model="e",
        generation_chunk_size=None,
        retrieval=[],
        generation=None,
        judge_model="otro",
    )
    assert "· Juez: `otro`" in text
    assert "Nota:" not in text


def test_render_results_sin_juez():
    """judge_model=None → sin 'Juez'."""
    text = render_results(
        date="2025-01-01 12:00",
        llm_model="m",
        embedding_model="e",
        generation_chunk_size=None,
        retrieval=[],
        generation=None,
        judge_model=None,
    )
    assert "Juez" not in text


# ── Test 17: test_main_judge_sin_llm ───────────────────────────────────────


def test_main_judge_sin_llm():
    """--judge + --skip-llm → SystemExit con code 2."""
    with pytest.raises(SystemExit) as exc_info:
        from docuchat.evaluation.run import main

        main(["--skip-llm", "--judge", "--chunk-sizes", "800"])
    assert exc_info.value.code == 2


# ── Test 18: test_main_con_juez ────────────────────────────────────────────


def test_main_con_juez(tmp_path: Path):
    """main con --judge: r.md contiene fidelidad y JSON tiene judged==42."""
    import contextlib
    import unittest.mock as mock

    from docuchat.evaluation.run import main as run_main

    QUESTIONS = Path(__file__).resolve().parents[2] / "eval" / "questions.jsonl"
    SAMPLES = Path(__file__).resolve().parents[2] / "samples"

    class FakeEmbedder:
        def __init__(self) -> None:
            self.calls: list[list[str]] = []

        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            self.calls.append(list(texts))
            return [[float(len(t)), 1.0, 0.5] for t in texts]

    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            os.environ.pop(key)
    tmp_path.chmod(0o755)
    os.chdir(tmp_path)

    same = SameChat("Respuesta [1].")
    same_judge = SameChat('{"supported": true, "unsupported": []}')

    patches = [
        mock.patch(
            "docuchat.index.indexer.make_embedder",
            return_value=FakeEmbedder(),
        ),
        mock.patch(
            "docuchat.retrieval.searcher.make_embedder",
            return_value=FakeEmbedder(),
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
                "--judge",
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
    assert "| Fidelidad (juez) | 1.000 (42 juzgadas, 0 sin juzgar) |" in md_content
    assert "· Juez: `" in md_content
    json_data = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert json_data["generation"]["judged"] == 42
