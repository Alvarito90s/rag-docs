"""Tests para los modelos Pydantic de la ingesta."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from docuchat.models import DocType, Document, Page

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
