"""Tests para src/docuchat/index/chunker.py."""

from pathlib import Path

from docuchat.index.chunker import (
    SEPARATORS,
    chunk_document,
    join_units,
    split_text,
    split_units,
)
from docuchat.ingest.scanner import load_folder
from docuchat.models import Chunk

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


# ── Test 1: textos vacíos ────────────────────────────────────────────
def test_split_text_empty_strings():
    assert split_text("", 20, 5) == []
    assert split_text("   \n\n ", 20, 5) == []


# ── Test 2: texto corto ──────────────────────────────────────────────
def test_split_text_short():
    assert split_text("Hola mundo.", 20, 5) == ["Hola mundo."]


# ── Test 3: párrafos que caben solos ─────────────────────────────────
def test_split_text_paragraphs_overlap_zero():
    result = split_text("Uno dos.\n\nTres cuatro.\n\nCinco seis.", 20, 0)
    assert result == ["Uno dos.", "Tres cuatro.", "Cinco seis."]


# ── Test 4: dos párrafos en un chunk ─────────────────────────────────
def test_split_text_two_paragraphs_in_one_chunk():
    text = "Uno dos.\n\nTres cuatro.\n\nCinco seis."
    result = split_text(text, 30, 0)
    assert result == ["Uno dos.\n\nTres cuatro.", "Cinco seis."]


# ── Test 5: frases con puntuación ────────────────────────────────────
def test_split_text_phrases_size_22():
    text = "Frase uno. Frase dos. Frase tres."
    result = split_text(text, 22, 0)
    assert result == ["Frase uno. Frase dos.", "Frase tres."]


# ── Test 6: frases con solape ────────────────────────────────────────
def test_split_text_phrases_with_overlap():
    text = "Frase uno. Frase dos. Frase tres."
    result = split_text(text, 22, 11)
    assert result == ["Frase uno. Frase dos.", "Frase dos. Frase tres."]


# ── Test 7: palabras, sin solape ─────────────────────────────────────
def test_split_text_words_no_overlap():
    result = split_text("aaaa bbbb cccc dddd eeee", 10, 0)
    assert result == ["aaaa bbbb", "cccc dddd", "eeee"]


# ── Test 8: palabras, con solape ─────────────────────────────────────
def test_split_text_words_with_overlap():
    result = split_text("aaaa bbbb cccc dddd eeee", 10, 4)
    assert result == [
        "aaaa bbbb",
        "bbbb cccc",
        "cccc dddd",
        "dddd eeee",
    ]


# ── Test 9: corte duro (sin separadores) ─────────────────────────────
def test_split_text_hard_cut():
    x = "x" * 25
    result = split_text(x, 10, 0)
    assert result == ["x" * 10, "x" * 10, "x" * 5]


# ── Test 10: líneas ──────────────────────────────────────────────────
def test_split_text_lines():
    result = split_text("Línea uno\nLínea dos\nLínea tres", 20, 0)
    assert result == ["Línea uno\nLínea dos", "Línea tres"]


# ── Test 11: errores ─────────────────────────────────────────────────
def test_split_text_errors():
    cases = [(0, 0), (10, -1), (10, 10), (10, 11)]
    for size, overlap in cases:
        try:
            split_text("a", size, overlap)
            raise AssertionError(f"ValueError esperado para ({size}, {overlap})")
        except ValueError:
            pass


# ── Test 12: split_units ─────────────────────────────────────────────
def test_split_units():
    result = split_units("ab cd", 2)
    assert result == [("", "ab"), (" ", "cd")]


# ── Test 13: join_units ──────────────────────────────────────────────
def test_join_units():
    result = join_units([("x", "a"), ("\n\n", "b"), ("", "c")])
    assert result == "a\n\nbc"


# ── Test 14: chunk_document con muestras ─────────────────────────────
def test_chunk_document_samples():
    ingest = load_folder(SAMPLES)
    assert len(ingest.documents) == 7

    expected_total = 26
    expected_per_source = {
        "apuntes_redes.md": 3,
        "contrato_servicios.pdf": 5,
        "glosario_interno.md": 1,
        "manual_cafetera.pdf": 11,
        "notas_reunion.txt": 1,
        "paper_rag_resumen.pdf": 2,
        "politica_vacaciones.docx": 3,
    }

    all_chunks: list[Chunk] = []
    for doc in ingest.documents:
        chunks = chunk_document(doc, 800, 120)
        all_chunks.extend(chunks)

    assert len(all_chunks) == expected_total

    counts: dict[str, int] = {}
    for c in all_chunks:
        counts[c.source] = counts.get(c.source, 0) + 1
    assert counts == expected_per_source

    for c in all_chunks:
        assert len(c.text) <= 800

    ids = [c.chunk_id for c in all_chunks]
    assert len(ids) == len(set(ids))


# ── Test 15: datos clave en chunks ───────────────────────────────────
def test_key_data_in_chunks():
    ingest = load_folder(SAMPLES)
    all_chunks: list[Chunk] = []
    for doc in ingest.documents:
        all_chunks.extend(chunk_document(doc, 800, 120))

    # manual_cafetera.pdf p. 7
    manual_text = "El código de error E-17 indica que el depósito de agua está vacío."
    found_manual = any(manual_text in c.text for c in all_chunks if "manual_cafetera" in c.source)
    assert found_manual

    # contrato_servicios.pdf p. 2
    contrato_text = (
        "El precio total del servicio asciende a 4.800 euros anuales, "
        "pagaderos por trimestres vencidos."
    )
    found_contrato = any(
        contrato_text in c.text for c in all_chunks if "contrato_servicios" in c.source
    )
    assert found_contrato


# ── Test 16: apuntes_redes.md, página 2 ──────────────────────────────
def test_apuntes_redes_page_2():
    ingest = load_folder(SAMPLES)
    all_chunks: list[Chunk] = []
    for doc in ingest.documents:
        all_chunks.extend(chunk_document(doc, 800, 120))

    page2_chunks = [c for c in all_chunks if c.source == "apuntes_redes.md" and c.page == 2]
    assert len(page2_chunks) >= 1

    first = page2_chunks[0]
    assert first.heading == "Puertos habituales"
    assert first.chunk_id == "apuntes_redes.md#p2#c0"


# ── SEPARATORS se mantiene ───────────────────────────────────────────
def test_separators_order():
    assert SEPARATORS == [
        ("\n\n", r"\n\n+"),
        ("\n", r"\n"),
        (" ", r"(?<=[.!?])\s+"),
        (" ", r" +"),
    ]
