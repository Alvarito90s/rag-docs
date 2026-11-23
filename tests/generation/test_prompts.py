"""Tests para src/docuchat/generation/prompts.py."""

from docuchat.generation.prompts import (
    NO_ANSWER,
    SYSTEM_PROMPT,
    build_context,
    build_messages,
    format_block,
)
from docuchat.models import Chunk, SearchResult, make_chunk_id


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


R = [mk("a.pdf", 1, "Alfa."), mk("b.md", 2, "Beta.", 2), mk("c.txt", 1, "Gamma.", 3)]


def test_format_block() -> None:
    assert format_block(3, R[0]) == "[3] a.pdf, p. 1\nAlfa."


def test_build_context_all_fit() -> None:
    context, used = build_context(R, 100)
    assert context == "[1] a.pdf, p. 1\nAlfa.\n\n[2] b.md, p. 2\nBeta.\n\n[3] c.txt, p. 1\nGamma."
    assert len(context) == 67
    assert len(used) == 3


def test_build_context_exact_limit() -> None:
    context, used = build_context(R, 43)
    assert len(context) == 43
    assert len(used) == 2


def test_build_context_one_less() -> None:
    context, used = build_context(R, 42)
    assert context == "[1] a.pdf, p. 1\nAlfa."
    assert len(used) == 1


def test_build_context_first_always_in() -> None:
    context, used = build_context(R, 10)
    assert context == "[1] a.pdf, p. 1\nAlfa."
    assert len(used) == 1


def test_build_context_empty() -> None:
    context, used = build_context([], 100)
    assert context == ""
    assert used == []


def test_build_messages() -> None:
    msgs = build_messages("¿Qué es?", "CTX")
    assert len(msgs) == 2
    assert msgs[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert msgs[1]["content"] == "Fragmentos:\n\nCTX\n\nPregunta: ¿Qué es?"


def test_system_prompt_contains_no_answer_and_tag() -> None:
    assert NO_ANSWER in SYSTEM_PROMPT
    assert "[1]" in SYSTEM_PROMPT


def test_system_prompt_ambiguas() -> None:
    assert "Solo si ningún fragmento contiene la información pedida" in SYSTEM_PROMPT
    assert "di a cuál se refiere" in SYSTEM_PROMPT
