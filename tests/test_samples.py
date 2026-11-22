"""Tests para los documentos de prueba generados."""

from pathlib import Path

import pymupdf
import pytest
from docx import Document

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def norm(s: str) -> str:
    """Normaliza espacios y saltos de línea."""
    return " ".join(s.split())


# --- test_files ---


def test_files() -> None:
    """Todos los archivos especificados en la task 005."""
    expected = {
        "contrato_servicios.pdf",
        "manual_cafetera.pdf",
        "paper_rag_resumen.pdf",
        "politica_vacaciones.docx",
        "apuntes_redes.md",
        "glosario_interno.md",
        "notas_reunion.txt",
    }
    actual = {f.name for f in SAMPLES.iterdir() if f.is_file()}
    assert actual == expected


# --- test_page_counts ---


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("contrato_servicios.pdf", 4),
        ("manual_cafetera.pdf", 10),
        ("paper_rag_resumen.pdf", 2),
    ],
)
def test_page_counts(filename: str, expected: int) -> None:
    with pymupdf.open(SAMPLES / filename) as doc:
        assert doc.page_count == expected


# --- test_pdf_facts ---
# Las páginas corresponden exactamente al orden de PdfSpec.pages:
# cada página de la lista produce una sola página en el PDF (PyMuPDF no
# reorganiza páginas al ajustar el contenido a las cajas de texto).

FACTS: list[tuple[str, int, str]] = [
    # contrato: 4 datos clave (espec 005 tabla)
    (
        "contrato_servicios.pdf",
        1,
        "El presente contrato se firma en Valladolid el 3 de marzo de 2025.",
    ),
    (
        "contrato_servicios.pdf",
        2,
        "El precio total del servicio asciende a 4.800 euros anuales, "
        "pagaderos por trimestres vencidos.",
    ),
    (
        "contrato_servicios.pdf",
        3,
        "El proveedor ofrece una garantía de dos años sobre todos los desarrollos entregados.",
    ),
    (
        "contrato_servicios.pdf",
        4,
        "Cualquiera de las partes podrá resolver el contrato con un preaviso de 30 días naturales.",
    ),
    # manual: 4 datos clave (espec 005 tabla)
    ("manual_cafetera.pdf", 2, "El depósito de agua tiene una capacidad de 1,8 litros."),
    (
        "manual_cafetera.pdf",
        5,
        "Se recomienda descalcificar la cafetera cada 200 ciclos de preparación.",
    ),
    (
        "manual_cafetera.pdf",
        7,
        "El código de error E-17 indica que el depósito de agua está vacío.",
    ),
    (
        "manual_cafetera.pdf",
        9,
        "La garantía de la cafetera cubre defectos de fabricación durante tres años.",
    ),
    # paper: 2 datos clave (espec 005 tabla)
    (
        "paper_rag_resumen.pdf",
        1,
        "Hybrid retrieval improved Hit@5 from 0.71 to 0.84 on the internal benchmark.",
    ),
    (
        "paper_rag_resumen.pdf",
        2,
        "The authors used a chunk size of 512 tokens with an overlap of 64 tokens.",
    ),
]


@pytest.mark.parametrize("filename,page,fact", FACTS)
def test_pdf_facts(filename: str, page: int, fact: str) -> None:
    with pymupdf.open(SAMPLES / filename) as doc:
        pages_with_fact = [i + 1 for i in range(doc.page_count) if fact in norm(doc[i].get_text())]
    assert pages_with_fact == [page], f"{filename}: '{fact}' en páginas {pages_with_fact}"


# --- test_contract_header_footer ---


def test_contract_header_footer() -> None:
    """El contrato debe tener cabecera y footer en todas las páginas."""
    header = "Contrato de prestación de servicios · Nubaria Datos S.L."
    with pymupdf.open(SAMPLES / "contrato_servicios.pdf") as doc:
        for i in range(doc.page_count):
            texto = doc[i].get_text()
            assert header in texto, f"Cabecera no encontrada en página {i + 1}"
            assert f"Página {i + 1} de 4" in texto, f"Footer incorrecto en página {i + 1}"


# --- test_manual_hyphen ---


def test_manual_hyphen() -> None:
    """Página 5 del manual debe contener guionamiento: descalci-\\nficación."""
    with pymupdf.open(SAMPLES / "manual_cafetera.pdf") as doc:
        texto_crudo = doc[4].get_text()  # página 5, índice 4
        # Verifica que el guion + salto de línea explícito estén presentes
        assert "descalci-" in texto_crudo, "Guion 'descalci-' no encontrado en página 5 del manual"
        # El guion debe ir seguido de salto de línea
        assert "descalci-\n" in texto_crudo, (
            "Combinación 'descalci-\\\\n' no encontrada en página 5 del manual"
        )


# --- test_pages_have_text ---


def test_pages_have_text() -> None:
    """Todas las páginas de los PDFs deben tener al menos 600 chars."""
    pdfs = [
        "contrato_servicios.pdf",
        "manual_cafetera.pdf",
        "paper_rag_resumen.pdf",
    ]
    for pdf_name in pdfs:
        with pymupdf.open(SAMPLES / pdf_name) as doc:
            for i in range(doc.page_count):
                texto = doc[i].get_text()
                assert len(norm(texto)) >= 600, (
                    f"{pdf_name} p.{i + 1}: texto demasiado corto ({len(norm(texto))})"
                )


# --- test_docx ---


def test_docx() -> None:
    """El DOCX debe contener textos clave, encabezados y tabla."""
    doc = Document(SAMPLES / "politica_vacaciones.docx")
    parrafos = [p.text for p in doc.paragraphs]
    texto_completo = " ".join(parrafos)
    assert "Cada empleado dispone de 23 días laborables de vacaciones al año." in texto_completo
    assert "Las solicitudes deben enviarse con al menos 15 días de antelación" in texto_completo
    celdas = [c.text.strip() for table in doc.tables for row in table.rows for c in row.cells]
    assert "Más de 10 años" in celdas
    assert "4" in celdas


# --- test_text_files ---


def test_text_files() -> None:
    """Los archivos de texto deben contener datos clave."""
    apuntes = (SAMPLES / "apuntes_redes.md").read_text(encoding="utf-8")
    assert "| DNS | 53 | UDP |" in apuntes

    glosario = (SAMPLES / "glosario_interno.md").read_text(encoding="utf-8")
    assert "SKU-4471-B" in glosario
    assert "RGPD" in glosario
    assert "KPI-07" in glosario
    assert "SLA-Oro" in glosario

    notas = (SAMPLES / "notas_reunion.txt").read_text(encoding="utf-8")
    assert "versión 3.2" in notas
    assert "Marta Ibáñez" in notas
