"""Tests para los documentos del corpus v2 (spec 081)."""

from pathlib import Path

import pymupdf
import pytest

from docuchat.index.chunker import chunk_document
from docuchat.ingest.scanner import load_document, load_folder

ROOT = Path(__file__).resolve().parents[1]
SAMPLES_V2 = ROOT / "samples_v2"
ASSETS = ROOT / "tasks" / "assets" / "081"


# 1. test_files


def test_files() -> None:
    """El conjunto de nombres de los archivos de SAMPLES_V2 es exacto."""
    expected = {
        "manual_hervidor_k1.pdf",
        "manual_hervidor_k2.pdf",
        "manual_hervidor_k3.pdf",
        "contrato_mantenimiento.pdf",
        "adenda_contrato_2026.pdf",
        "informe_anual_2025.pdf",
        "reglamento_interno.pdf",
        "politica_teletrabajo_2025.docx",
        "politica_teletrabajo_2026.docx",
        "tarifas_soporte.docx",
        "guia_onboarding.md",
        "faq_clientes.md",
        "catalogo_recambios.md",
        "acta_comite_2026_03.txt",
        "acta_comite_2026_06.txt",
    }
    actual = {f.name for f in SAMPLES_V2.iterdir() if f.is_file()}
    assert actual == expected


# 2. test_copia_exacta


@pytest.mark.parametrize(
    "name",
    [
        "make_samples_v2.py",
        "samples_v2_manuales.py",
        "samples_v2_empresa.py",
        "samples_v2_textos.py",
    ],
)
def test_copia_exacta(name: str) -> None:
    """Los scripts copiados son idénticos a los assets (byte a byte)."""
    assert (ROOT / "scripts" / name).read_bytes() == (ASSETS / name).read_bytes()


# 3. test_page_counts (7 casos parametrizados)


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("manual_hervidor_k1.pdf", 6),
        ("manual_hervidor_k2.pdf", 6),
        ("manual_hervidor_k3.pdf", 6),
        ("contrato_mantenimiento.pdf", 5),
        ("adenda_contrato_2026.pdf", 2),
        ("informe_anual_2025.pdf", 12),
        ("reglamento_interno.pdf", 6),
    ],
)
def test_page_counts(filename: str, expected: int) -> None:
    with pymupdf.open(SAMPLES_V2 / filename) as doc:
        assert doc.page_count == expected


# 4. test_corpus_completo


def test_corpus_completo() -> None:
    """load_folder devuelve 15 documentos, 70 páginas y sin errores."""
    result = load_folder(SAMPLES_V2)
    assert result.errors == []
    assert len(result.documents) == 15
    total_pages = sum(doc.page_count for doc in result.documents)
    assert total_pages == 70


# 5. test_numero_de_chunks


def test_numero_de_chunks() -> None:
    """La suma de chunks(800, 120) sobre los 15 documentos es 73."""
    result = load_folder(SAMPLES_V2)
    total = sum(len(chunk_document(doc, 800, 120)) for doc in result.documents)
    assert total == 73


# 6. test_trampa_manuales (3 casos parametrizados)


@pytest.mark.parametrize(
    "model_key,modelo",
    [
        ("k1", "K1"),
        ("k2", "K2"),
        ("k3", "K3"),
    ],
)
def test_trampa_manuales(model_key: str, modelo: str) -> None:
    """Páginas 1, 4 y 5 nombran el modelo; 2, 3 y 6 no nombran K1/K2/K3."""
    doc = load_document(SAMPLES_V2 / f"manual_hervidor_{model_key}.pdf", SAMPLES_V2)
    pages = {p.number: p.text for p in doc.pages}

    for num in (1, 4, 5):
        texto = pages[num]
        assert modelo in texto, (
            f"manual_hervidor_{model_key}.pdf p.{num}: se esperaba '{modelo}' en el cuerpo"
        )

    for num in (2, 3, 6):
        texto = pages[num]
        assert "K1" not in texto, (
            f"manual_hervidor_{model_key}.pdf p.{num}: no se esperaba 'K1' en el cuerpo"
        )
        assert "K2" not in texto, (
            f"manual_hervidor_{model_key}.pdf p.{num}: no se esperaba 'K2' en el cuerpo"
        )
        assert "K3" not in texto, (
            f"manual_hervidor_{model_key}.pdf p.{num}: no se esperaba 'K3' en el cuerpo"
        )


# 7. test_facts (10 casos parametrizados)

FACTS: list[tuple[str, int, str]] = [
    ("contrato_mantenimiento.pdf", 2, "6.200 euros anuales"),
    ("adenda_contrato_2026.pdf", 1, "6.900 euros anuales"),
    ("informe_anual_2025.pdf", 3, "22.300 unidades"),
    ("reglamento_interno.pdf", 5, "Artículo 17. Regalos"),
    ("manual_hervidor_k3.pdf", 6, "900 101 203"),
    ("catalogo_recambios.md", 4, "MB-30"),
    ("tarifas_soporte.docx", 1, "9,99 euros al mes"),
    ("politica_teletrabajo_2026.docx", 1, "Personal de oficina | 3 días"),
    ("acta_comite_2026_06.txt", 1, "38.000 euros"),
    ("faq_clientes.md", 6, "cinco días laborables"),
]


@pytest.mark.parametrize("filename,page,fact", FACTS)
def test_facts(filename: str, page: int, fact: str) -> None:
    """El texto aparece en la página indicada tras colapsar espacios."""
    doc = load_document(SAMPLES_V2 / filename, SAMPLES_V2)
    pages = {p.number: p.text for p in doc.pages}
    norm_fact = " ".join(fact.split())
    assert norm_fact in " ".join(pages[page].split()), (
        f"'{fact}' no encontrado en {filename} p.{page}"
    )
