"""Tests para fusion.py (rrf_fuse, drop_adjacent)."""

import pytest

from docuchat.models import Chunk, make_chunk_id
from docuchat.retrieval.fusion import drop_adjacent, rrf_fuse


def mk(source: str, page: int, position: int) -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id(source, page, position),
        source=source,
        doc_sha256="a" * 64,
        page=page,
        position=position,
        text="x",
    )


# ── rrf_fuse ──────────────────────────────────────────────────────────────


def test_rrf_basic():
    result = rrf_fuse([["a", "b", "c"], ["b", "c", "d"]], 60)
    ids = [item_id for item_id, _ in result]
    scores = [score for _, score in result]
    assert ids == ["b", "c", "a", "d"]
    assert scores == pytest.approx([0.0325225, 0.0320020, 0.0163934, 0.0158730], abs=1e-6)


def test_rrf_tie():
    result = rrf_fuse([["a", "b"], ["b", "a"]], 1)
    assert [item_id for item_id, _ in result] == ["a", "b"]
    assert [score for _, score in result] == pytest.approx([0.833333, 0.833333], abs=1e-6)


def test_rrf_single_ranking():
    result = rrf_fuse([["z", "y", "x"]], 60)
    ids = [item_id for item_id, _ in result]
    assert ids == ["z", "y", "x"]


def test_rrf_duplicates():
    result = rrf_fuse([["a", "a", "b"]], 60)
    assert [item_id for item_id, _ in result] == ["a", "b"]
    assert [score for _, score in result] == pytest.approx([1 / 61, 1 / 63], abs=1e-6)


def test_rrf_empty():
    assert rrf_fuse([], 60) == []
    assert rrf_fuse([[], []], 60) == []


def test_rrf_k_zero():
    with pytest.raises(ValueError, match="k debe ser positivo"):
        rrf_fuse([["a"]], 0)


# ── drop_adjacent ─────────────────────────────────────────────────────────


def test_drop_adjacent_basic():
    result = drop_adjacent(
        [
            mk("A", 1, 1),
            mk("A", 1, 0),
            mk("A", 1, 2),
            mk("A", 2, 0),
            mk("B", 1, 0),
            mk("A", 1, 3),
        ]
    )
    assert [c.chunk_id for c in result] == [
        "A#p1#c1",
        "A#p2#c0",
        "B#p1#c0",
        "A#p1#c3",
    ]


def test_drop_adjacent_non_contiguous():
    result = drop_adjacent([mk("A", 1, 0), mk("A", 1, 2)])
    assert len(result) == 2


def test_drop_adjacent_different_source_or_page():
    result = drop_adjacent([mk("A", 1, 0), mk("A", 2, 1), mk("B", 1, 1)])
    assert len(result) == 3


def test_drop_adjacent_empty():
    assert drop_adjacent([]) == []
