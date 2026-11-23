"""Tests para preguntas v2 con categoría: spec 082."""

from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from docuchat.evaluation.dataset import EvalQuestion, load_questions
from docuchat.evaluation.metrics import keywords_hit
from docuchat.ingest.scanner import load_document

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "eval" / "questions_v2.jsonl"
SAMPLES_V2 = ROOT / "samples_v2"
LETTER = {
    "literal": "l",
    "parafrasis": "p",
    "numerica": "n",
    "distractor": "d",
    "implicita": "i",
    "tabla": "t",
    "profunda": "f",
    "sin_respuesta": "u",
}


# ── Carga v2 ──────────────────────────────────────────────────────────────


class TestCargaV2:
    """Test 1: 80 preguntas, 70 answerable, ids únicos, primera l01, última u10."""

    def test_carga_v2(self):
        qs = load_questions(V2)
        assert len(qs) == 80
        assert sum(1 for q in qs if q.answerable) == 70
        ids = [q.id for q in qs]
        assert len(ids) == len(set(ids))
        assert ids[0] == "l01"
        assert ids[-1] == "u10"


class TestCopiaExactaV2:
    """Test 2: bytes iguales al asset."""

    def test_copia_exacta(self):
        src = V2.read_bytes()
        dst = (ROOT / "tasks" / "assets" / "082" / "questions_v2.jsonl").read_bytes()
        assert src == dst


# ── Categorías ────────────────────────────────────────────────────────────


class TestDiezPorCategoria:
    """Test 3: 10 preguntas por cada una de las 8 categorías."""

    def test_diez_por_categoria(self):
        qs = load_questions(V2)
        counts = Counter(q.category for q in qs)
        expected = {c: 10 for c in LETTER}
        assert counts == expected


class TestLetraDelId:
    """Test 4: q.id[0] == LETTER[q.category] para cada pregunta."""

    def test_letra_del_id(self):
        for q in load_questions(V2):
            assert q.id[0] == LETTER[q.category]


class TestSinRespuestaCoherente:
    """Test 5: category == sin_respuesta ↔ not answerable."""

    def test_sin_respuesta_coherente(self):
        for q in load_questions(V2):
            assert (q.category == "sin_respuesta") == (not q.answerable)


# ── Coherencia con samples_v2 ────────────────────────────────────────────


class TestPaginaExiste:
    """Test 6: expected_page válido para cada pregunta con respuesta."""

    def test_pagina_existe(self):
        for q in load_questions(V2):
            if q.answerable:
                doc = load_document(SAMPLES_V2 / q.expected_doc, SAMPLES_V2)
                page_numbers = {p.number for p in doc.pages}
                assert q.expected_page in page_numbers


class TestPalabrasClaveEnSuPagina:
    """Test 7: keywords_hit en la página esperada para cada pregunta con respuesta."""

    def test_palabras_clave_en_su_pagina(self):
        qs = load_questions(V2)
        fallos: list[str] = []
        for q in qs:
            if not q.answerable:
                continue
            doc = load_document(SAMPLES_V2 / q.expected_doc, SAMPLES_V2)
            page_text = ""
            for p in doc.pages:
                if p.number == q.expected_page:
                    page_text = p.text
                    break
            if not keywords_hit(page_text, q.answer_keywords):
                fallos.append(q.id)
        assert not fallos, f"Palabras clave no encontradas en las páginas: {fallos}"


# ── v1 sin cambios ───────────────────────────────────────────────────────


class TestV1SinCambios:
    """Test 8: v1 tiene 42 preguntas con category == general."""

    def test_v1_sin_cambios(self):
        qs = load_questions(ROOT / "eval" / "questions.jsonl")
        assert len(qs) == 42
        assert all(q.category == "general" for q in qs)


# ── Campo category ───────────────────────────────────────────────────────


class TestCategoriaPorDefecto:
    """Test 9: EvalQuestion sin category → general."""

    def test_categoria_por_defecto(self):
        q = EvalQuestion(id="u01", question="¿X?", answerable=False)
        assert q.category == "general"


class TestCategoriaInvalida:
    """Test 10: categories inválidas lanzan ValidationError."""

    @pytest.mark.parametrize("value", ["Distractor", "sin respuesta", ""])
    def test_categoria_invalida(self, value: str):
        with pytest.raises(ValidationError):
            EvalQuestion(id="u01", question="¿X?", answerable=False, category=value)
