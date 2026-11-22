"""Tests obligatorios del loader PDF, spec 012-loader-pdf.md."""

import re
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf
import pytest

from docuchat.ingest.pdf_loader import extract_paragraphs, load_pdf

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
_FOOTER_RE = re.compile(r"Página \d+ de 4")


# --- 1. test_contract_pages ---


def test_contract_pages() -> None:
    """load_pdf(contrato_servicios.pdf) → 4 páginas, números [1, 2, 3, 4]."""
    pages = load_pdf(SAMPLES / "contrato_servicios.pdf")
    assert len(pages) == 4
    assert [p.number for p in pages] == [1, 2, 3, 4]


# --- 2. test_contract_header_footer_removed ---


def test_contract_header_footer_removed() -> None:
    """Contrato: ninguna página contiene 'Nubaria ...' ni r'Página \\d+ de 4'."""
    pages = load_pdf(SAMPLES / "contrato_servicios.pdf")
    for p in pages:
        assert "Nubaria Datos S.L." not in p.text
        assert _FOOTER_RE.search(p.text) is None


# --- 3. test_manual_header_footer_removed ---


def test_manual_header_footer_removed() -> None:
    """Manual: 10 páginas; sin cabecera ni pie repetidos."""
    pages = load_pdf(SAMPLES / "manual_cafetera.pdf")
    assert len(pages) == 10
    for p in pages:
        assert "Brevia X2 · página" not in p.text
        assert "Manual de usuario · Cafetera Brevia X2" not in p.text


# --- 4. test_manual_hyphen_joined ---


def test_manual_hyphen_joined() -> None:
    """Manual p5: 'descalcificación periódica' presente, 'descalici-' ausente."""
    pages = load_pdf(SAMPLES / "manual_cafetera.pdf")
    texto_p5 = pages[4].text
    assert "descalcificación periódica" in texto_p5
    assert "descalici-" not in texto_p5


# --- 5. test_paper_pages ---


def test_paper_pages() -> None:
    """Paper: 2 pág.; p1 contiene 'Hybrid retrieval improved Hit@5...'."""
    pages = load_pdf(SAMPLES / "paper_rag_resumen.pdf")
    assert len(pages) == 2
    assert (
        "Hybrid retrieval improved Hit@5 from 0.71 to 0.84 "
        "on the internal benchmark." in pages[0].text
    )


# --- 6. test_key_facts_literal ---


def test_key_facts_literal() -> None:
    """Datos clave LITERALES en su página: contrato p2, manual p7, manual p9."""
    contrato = load_pdf(SAMPLES / "contrato_servicios.pdf")
    assert (
        "El precio total del servicio asciende a 4.800 euros anuales, "
        "pagaderos por trimestres vencidos." in contrato[1].text
    )
    manual = load_pdf(SAMPLES / "manual_cafetera.pdf")
    assert "El código de error E-17 indica que el depósito de agua está vacío." in manual[6].text
    assert (
        "La garantía de la cafetera cubre defectos de fabricación "
        "durante tres años." in manual[8].text
    )


# --- 7. test_no_single_newlines ---


def test_no_single_newlines() -> None:
    """En los 3 PDFs, ningún texto contiene un '\\n' suelto."""
    for filename in [
        "contrato_servicios.pdf",
        "manual_cafetera.pdf",
        "paper_rag_resumen.pdf",
    ]:
        pages = load_pdf(SAMPLES / filename)
        for p in pages:
            no_single = p.text.replace("\n\n", "")
            assert "\n" not in no_single, f"'\\n' suelto en {filename} p.{p.number}"


# --- 8. test_extract_paragraphs_order ---


def test_extract_paragraphs_order() -> None:
    """extract_paragraphs(contrato): 4 listas; primer bloque empieza por
    'Contrato de prestación...', último por 'Página '."""
    blocks = extract_paragraphs(SAMPLES / "contrato_servicios.pdf")
    assert len(blocks) == 4
    for page_blocks in blocks:
        assert page_blocks[0].startswith("Contrato de prestación de servicios")
        assert page_blocks[-1].startswith("Página ")


# --- 9. test_blank_page_skipped ---


def test_blank_page_skipped() -> None:
    """PDF con página en blanco en medio → load_pdf devuelve números [1, 3]."""
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        doc = pymupdf.open()
        doc.new_page().insert_text((72, 72), "texto uno")
        doc.new_page()  # página vacía
        doc.new_page().insert_text((72, 72), "texto tres")
        doc.save(tmp_path / "blanco.pdf")
        doc.close()

        pages = load_pdf(tmp_path / "blanco.pdf")
        assert len(pages) == 2
        assert [p.number for p in pages] == [1, 3]


# --- 10. test_corrupt_pdf_raises ---


def test_corrupt_pdf_raises() -> None:
    """Archivo con bytes basura → pytest.raises(pymupdf.FileDataError)."""
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "roto.pdf").write_bytes(b"no soy un pdf")
        with pytest.raises(pymupdf.FileDataError):
            load_pdf(tmp_path / "roto.pdf")
