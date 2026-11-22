"""Tests obligatorios loaders DOCX, MD y TXT, spec 013-loader-docx-md-txt.md."""

from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document as DocxDocument

from docuchat.ingest.docx_loader import load_docx
from docuchat.ingest.text_loader import load_markdown, load_txt, split_markdown_sections

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


# --- 1. test_01_load_docx_single_page ---


def test_01_load_docx_single_page() -> None:
    """load_docx(politica_vacaciones.docx) → 1 página, número 1, heading is None."""
    pages = load_docx(SAMPLES / "politica_vacaciones.docx")
    assert len(pages) == 1
    assert pages[0].number == 1
    assert pages[0].heading is None


# --- 2. test_02_load_docx_text_start ---


def test_02_load_docx_text_start() -> None:
    """Texto empieza por 'Política de vacaciones 2025\n\nDías de vacaciones\n\nCada empleado...'."""
    pages = load_docx(SAMPLES / "politica_vacaciones.docx")
    expected_start = (
        "Política de vacaciones 2025\n\n"
        "Días de vacaciones\n\n"
        "Cada empleado dispone de 23 días laborables de vacaciones al año."
    )
    assert pages[0].text.startswith(expected_start)


# --- 3. test_03_load_docx_table_order ---


def test_03_load_docx_table_order() -> None:
    """Tabla aparece DESPUÉS de 'Antigüedad ...' y ANTES de 'Solicitudes'."""
    pages = load_docx(SAMPLES / "politica_vacaciones.docx")
    text = pages[0].text
    table_text = (
        "Antigüedad | Días adicionales\nMenos de 5 años | 0\nDe 5 a 10 años | 2\nMás de 10 años | 4"
    )
    assert table_text in text
    idx_ant = text.index("Días adicionales por antigüedad")
    idx_tab = text.index(table_text)
    idx_sol = text.index("Solicitudes")
    assert idx_ant < idx_tab < idx_sol


# --- 4. test_04_load_docx_empty ---


def test_04_load_docx_empty() -> None:
    """DOCX vacío → load_docx devuelve []."""
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        empty_path = tmp_path / "empty.docx"
        DocxDocument().save(empty_path)
        assert load_docx(empty_path) == []


# --- 5. test_05_load_txt_notas ---


def test_05_load_txt_notas() -> None:
    """load_txt(notas_reunion.txt) → 1 página; contiene 'versión 3.2'; empieza por 'Reunión...'."""
    pages = load_txt(SAMPLES / "notas_reunion.txt")
    assert len(pages) == 1
    assert "versión 3.2" in pages[0].text
    assert pages[0].text.startswith("Reunión del 12 de mayo de 2025\nAsistentes:")


# --- 6. test_06_load_txt_bom_invalid ---


def test_06_load_txt_bom_invalid() -> None:
    """TXT con BOM + byte inválido → 'hola� mundo'."""
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        f = tmp_path / "bom.txt"
        f.write_bytes(b"\xef\xbb\xbfhola\xff mundo")
        pages = load_txt(f)
    assert len(pages) == 1
    assert pages[0].text == "hola� mundo"


# --- 7. test_07_load_txt_empty ---


def test_07_load_txt_empty() -> None:
    """TXT con solo espacios → []."""
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        f = tmp_path / "empty.txt"
        f.write_bytes(b"  \n\n ")
        assert load_txt(f) == []


# --- 8. test_08_load_markdown_apuntes ---


def test_08_load_markdown_apuntes() -> None:
    """apuntes_redes.md → 3 páginas, números [1, 2, 3], encabezados correctos."""
    pages = load_markdown(SAMPLES / "apuntes_redes.md")
    assert len(pages) == 3
    assert [p.number for p in pages] == [1, 2, 3]
    assert [p.heading for p in pages] == [
        "Modelo OSI",
        "Puertos habituales",
        "TCP frente a UDP",
    ]


# --- 9. test_09_load_markdown_apuntes_p2 ---


def test_09_load_markdown_apuntes_p2() -> None:
    """Página 2 de apuntes_redes.md empieza por '## Puertos...' y contiene '| DNS | 53 | UDP |'."""
    pages = load_markdown(SAMPLES / "apuntes_redes.md")
    texto_p2 = pages[1].text
    assert texto_p2.startswith("## Puertos habituales\n\n| Protocolo | Puerto | Transporte |")
    assert "| DNS | 53 | UDP |" in texto_p2


# --- 10. test_10_load_markdown_glosario ---


def test_10_load_markdown_glosario() -> None:
    """glosario_interno.md → 1 página, heading 'Glosario interno', contiene 'SKU-4471-B'."""
    pages = load_markdown(SAMPLES / "glosario_interno.md")
    assert len(pages) == 1
    assert pages[0].heading == "Glosario interno"
    assert "SKU-4471-B" in pages[0].text


# --- 11. test_11_split_markdown_sections_basic ---


def test_11_split_markdown_sections_basic() -> None:
    """split_markdown_sections básico: intro, # A, ## B (### no abre sección)."""
    result = split_markdown_sections("intro\n# A\ntexto a\n### sub\nmás a\n## B\ntexto b")
    assert result == [
        (None, "intro"),
        ("A", "# A\ntexto a\n### sub\nmás a"),
        ("B", "## B\ntexto b"),
    ]


# --- 12. test_12_split_markdown_code_block ---


def test_12_split_markdown_code_block() -> None:
    """Bloque de código: # dentro de ``` no se trata como título."""
    result = split_markdown_sections("# A\n```\n# no es título\n```\nfin")
    assert result == [("A", "# A\n```\n# no es título\n```\nfin")]


# --- 13. test_13_split_markdown_heading_trailing_hashes ---


def test_13_split_markdown_heading_trailing_hashes() -> None:
    """'# Título ##' → encabezado 'Título', línea conservada en texto."""
    result = split_markdown_sections("# Título ##\ncuerpo")
    assert result == [("Título", "# Título ##\ncuerpo")]


# --- 14. test_14_split_markdown_no_space ---


def test_14_split_markdown_no_space() -> None:
    """'#sin espacio' NO es encabezado → va como texto con heading None."""
    result = split_markdown_sections("#sin espacio\ncuerpo")
    assert result == [(None, "#sin espacio\ncuerpo")]
