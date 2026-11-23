"""Tests para src/docuchat/generation/citations.py."""

import pytest

from docuchat.generation.citations import (
    NO_ANSWER,
    Source,
    find_citations,
    is_no_answer,
    resolve_citations,
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


# ---- find_citations ----


def test_find_citations_multiple_patterns() -> None:
    assert find_citations("A [1]. B [2][3], C [1, 4] y [ 2 ]; D [5;6]") == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]


def test_find_citations_no_citations() -> None:
    assert find_citations("Sin citas") == []


def test_find_citations_year_and_letter() -> None:
    assert find_citations("Año [2025] y [a]") == [2025]


def test_find_citations_zero() -> None:
    assert find_citations("[0]") == [0]


# ---- resolve_citations ----


def test_resolve_citations_mixed() -> None:
    ctx = [mk("a.pdf", 1, "x"), mk("b.md", 2, "y", 2)]
    sources, fakes = resolve_citations("X [2]. Y [1][2]. Z [7].", ctx)
    assert sources == [
        Source(2, "b.md", 2),
        Source(1, "a.pdf", 1),
    ]
    assert fakes == [7]


def test_resolve_citations_all_fake() -> None:
    ctx = [mk("a.pdf", 1, "x"), mk("b.md", 2, "y", 2)]
    sources, fakes = resolve_citations("Nada [0] [3]", ctx)
    assert sources == []
    assert fakes == [0, 3]


def test_resolve_citations_none() -> None:
    ctx = [mk("a.pdf", 1, "x"), mk("b.md", 2, "y", 2)]
    sources, fakes = resolve_citations("Sin citas.", ctx)
    assert sources == []
    assert fakes == []


def test_resolve_citations_empty_context() -> None:
    sources, fakes = resolve_citations("Dato [1].", [])
    assert sources == []
    assert fakes == [1]


# ---- is_no_answer ----


@pytest.mark.parametrize(
    "text,expected",
    [
        (NO_ANSWER, True),
        ("  no lo se.", True),
        ("NO LO SÉ", True),
        ("El depósito... no lo sé", False),
        ("", False),
    ],
)
def test_is_no_answer(text: str, expected: bool) -> None:
    assert is_no_answer(text) == expected
