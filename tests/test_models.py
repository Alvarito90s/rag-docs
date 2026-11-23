"""Tests para los modelos Pydantic de la ingesta."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from docuchat.models import Chunk, DocType, Document, Page, SearchResult, make_chunk_id

SHA = "a" * 64


# --- test_page ---


def test_page_char_count() -> None:
    page = Page(number=1, text="hola")
    assert page.char_count == 4
    assert page.heading is None


def test_page_number_must_be_ge_1() -> None:
    with pytest.raises(ValidationError):
        Page(number=0, text="x")


def test_page_is_frozen() -> None:
    page = Page(number=1, text="hola")
    with pytest.raises(ValidationError):
        page.text = "y"


# --- test_document ---


def test_document_counters() -> None:
    doc = Document(
        source="a.pdf",
        path=Path("/tmp/a.pdf"),
        sha256=SHA,
        doc_type=DocType.PDF,
        pages=(Page(number=1, text="ab"), Page(number=3, text="cde")),
    )
    assert doc.page_count == 2
    assert doc.char_count == 5


def test_document_page_order_same() -> None:
    with pytest.raises(ValidationError):
        Document(
            source="a.pdf",
            path=Path("/tmp/a.pdf"),
            sha256=SHA,
            doc_type=DocType.PDF,
            pages=(Page(number=1, text="a"), Page(number=1, text="b")),
        )


def test_document_page_order_descending() -> None:
    with pytest.raises(ValidationError):
        Document(
            source="a.pdf",
            path=Path("/tmp/a.pdf"),
            sha256=SHA,
            doc_type=DocType.PDF,
            pages=(Page(number=2, text="a"), Page(number=1, text="b")),
        )


def test_document_empty_pages() -> None:
    doc = Document(
        source="a.pdf",
        path=Path("/tmp/a.pdf"),
        sha256=SHA,
        doc_type=DocType.PDF,
        pages=(),
    )
    assert doc.page_count == 0
    assert doc.char_count == 0


def test_document_sha256_pattern() -> None:
    with pytest.raises(ValidationError):
        Document(
            source="a.pdf",
            path=Path("/tmp/a.pdf"),
            sha256="xyz",
            doc_type=DocType.PDF,
            pages=(),
        )
    with pytest.raises(ValidationError):
        Document(
            source="a.pdf",
            path=Path("/tmp/a.pdf"),
            sha256="A" * 64,
            doc_type=DocType.PDF,
            pages=(),
        )


def test_doc_type_str_enum() -> None:
    doc = Document(
        source="a.md",
        path=Path("/tmp/a.md"),
        sha256=SHA,
        doc_type="md",
        pages=(),
    )
    assert doc.doc_type == DocType.MD
    with pytest.raises(ValidationError):
        Document(
            source="a.pptx",
            path=Path("/tmp/a.pptx"),
            sha256=SHA,
            doc_type="pptx",
            pages=(),
        )


def test_doctype_equals_string() -> None:
    assert DocType.PDF == "pdf"


# --- make_chunk_id ---


def test_make_chunk_id() -> None:
    assert make_chunk_id("sub/a.pdf", 3, 0) == "sub/a.pdf#p3#c0"


# --- Chunk ---


def test_chunk_valid() -> None:
    chunk = Chunk(
        chunk_id="a.pdf#p1#c0",
        source="a.pdf",
        doc_sha256=SHA,
        page=1,
        position=0,
        text="hola",
    )
    assert chunk.heading is None


@pytest.mark.parametrize(
    "kwargs",
    [{"text": ""}, {"page": 0}, {"position": -1}],
)
def test_chunk_invalid(kwargs: dict) -> None:
    base = {
        "chunk_id": "a.pdf#p1#c0",
        "source": "a.pdf",
        "doc_sha256": SHA,
        "page": 1,
        "position": 0,
        "text": "hola",
    }
    base.update(kwargs)
    with pytest.raises(ValidationError):
        Chunk(**base)


# --- SearchResult ---


@pytest.fixture()
def valid_chunk() -> Chunk:
    return Chunk(
        chunk_id="a.pdf#p1#c0",
        source="a.pdf",
        doc_sha256=SHA,
        page=1,
        position=0,
        text="hola",
    )


def test_search_result_valid(valid_chunk: Chunk) -> None:
    result = SearchResult(chunk=valid_chunk, rank=1, score=0.0328)
    assert result.vector_rank is None
    assert result.bm25_rank is None
    assert result.chunk.chunk_id == "a.pdf#p1#c0"


@pytest.mark.parametrize(
    "kwargs",
    [{"rank": 0}, {"vector_rank": 0}],
)
def test_search_result_invalid(kwargs: dict) -> None:
    base = {
        "chunk": Chunk(
            chunk_id="a.pdf#p1#c0",
            source="a.pdf",
            doc_sha256=SHA,
            page=1,
            position=0,
            text="hola",
        ),
        "rank": 1,
        "score": 0.0328,
        "vector_rank": None,
        "bm25_rank": None,
    }
    base.update(kwargs)
    with pytest.raises(ValidationError):
        SearchResult(**base)
