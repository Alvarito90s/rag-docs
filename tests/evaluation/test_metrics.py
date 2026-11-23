"""Tests para src/docuchat/evaluation/metrics.py."""

import pytest

from docuchat.generation.citations import Source
from docuchat.models import Chunk, SearchResult, make_chunk_id


def mk(source: str, page: int, text: str = "", rank: int = 1) -> SearchResult:
    """Helper para crear SearchResult de prueba."""
    chunk = Chunk(
        chunk_id=make_chunk_id(source, page, 0),
        source=source,
        doc_sha256="a" * 64,
        page=page,
        position=0,
        text=text or f"Texto de {source} página {page}",
    )
    return SearchResult(chunk=chunk, rank=rank, score=0.1)


def test_normalize() -> None:
    from docuchat.evaluation.metrics import normalize

    assert normalize("Garantía de DOS Años") == "garantia de dos anos"


@pytest.mark.parametrize(
    ("text", "keywords", "expected"),
    [
        ("El depósito está vacío.", ["vacío"], True),
        ("El deposito esta VACIO", ["vacío"], True),
        ("Cuesta 4800 euros", ["4.800|4800"], True),
        ("DNS usa el puerto 53 por UDP", ["53", "udp"], True),
        ("DNS usa el puerto 53", ["53", "udp"], False),
        ("No lo sé", ["valladolid"], False),
        ("cualquier cosa", [], True),
    ],
)
def test_keywords_hit(text: str, keywords: list[str], expected: bool) -> None:
    from docuchat.evaluation.metrics import keywords_hit

    assert keywords_hit(text, keywords) == expected


def test_first_hit_rank() -> None:
    from docuchat.evaluation.metrics import first_hit_rank

    results = [mk("a.pdf", 1), mk("b.pdf", 2), mk("b.pdf", 2)]
    assert first_hit_rank(results, "b.pdf", 2) == 2
    assert first_hit_rank(results, "b.pdf", 3) is None
    assert first_hit_rank([], "a.pdf", 1) is None


def test_hit_at() -> None:
    from docuchat.evaluation.metrics import hit_at

    assert hit_at([1, 3, None, 6], 5) == pytest.approx(0.5)
    assert hit_at([1, 3, None, 6], 1) == pytest.approx(0.25)
    assert hit_at([], 5) == 0.0
    with pytest.raises(ValueError, match="k debe ser positivo"):
        hit_at([1], 0)


def test_mean_reciprocal_rank() -> None:
    from docuchat.evaluation.metrics import mean_reciprocal_rank

    assert mean_reciprocal_rank([1, 2, None, 4]) == pytest.approx(0.4375)
    assert mean_reciprocal_rank([]) == 0.0


def test_citation_counts() -> None:
    from docuchat.evaluation.metrics import citation_counts

    sources = [
        Source(1, "a.pdf", 3),
        Source(2, "a.pdf", 4),
        Source(3, "b.md", 3),
    ]
    assert citation_counts(sources, "a.pdf", 3) == (1, 3)
    assert citation_counts([], "a.pdf", 3) == (0, 0)


def test_ratio() -> None:
    from docuchat.evaluation.metrics import ratio

    assert ratio(3, 4) == 0.75
    assert ratio(0, 0) is None
