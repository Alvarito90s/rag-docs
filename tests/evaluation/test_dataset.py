"""Tests para src/docuchat/evaluation/dataset.py."""

import json
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from docuchat.evaluation.dataset import DatasetError, EvalQuestion, load_questions
from docuchat.ingest.scanner import load_document

ROOT = Path(__file__).resolve().parents[2]


class TestLoadQuestions:
    """Test 1: carga completa del dataset."""

    def test_carga_completa(self):
        questions = load_questions(ROOT / "eval" / "questions.jsonl")
        assert len(questions) == 42
        assert sum(1 for q in questions if q.answerable) == 32
        ids = [q.id for q in questions]
        assert len(ids) == len(set(ids))
        assert ids[0] == "q01"
        assert ids[-1] == "u10"


class TestCoherenciaConSamples:
    """Test 2: coherencia con documentos de samples/."""

    def test_expected_doc_existe_y_pagina_valida(self):
        questions = load_questions(ROOT / "eval" / "questions.jsonl")
        samples = ROOT / "samples"
        for q in questions:
            if q.expected_doc is not None and q.expected_page is not None:
                doc_path = samples / q.expected_doc
                assert doc_path.exists(), f"{q.expected_doc} no existe en samples/"
                doc = load_document(doc_path, samples)
                assert q.expected_page <= doc.page_count


class TestCopiaExacta:
    """Test 3: los bytes de eval/questions.jsonl son iguales a tasks/assets/060/questions.jsonl."""

    def test_copia_exacta(self):
        src = ROOT / "eval" / "questions.jsonl"
        dst = ROOT / "tasks" / "assets" / "060" / "questions.jsonl"
        assert src.read_bytes() == dst.read_bytes()


class TestEvalQuestionSinRespuesta:
    """Test 4: EvalQuestion válida sin respuesta."""

    def test_creacion_sin_respuesta(self):
        q = EvalQuestion(id="u01", question="¿X?", answerable=False)
        assert q.expected_doc is None
        assert q.answer_keywords == []


class TestCheckConsistency:
    """Test 5: _check_consistency (parametrizado, 3 casos → 3 tests)."""

    @pytest.mark.parametrize(
        "kwargs,error_contains",
        [
            (
                {"id": "q01", "question": "x", "answerable": True},
                "una pregunta con respuesta necesita expected_doc",
            ),
            (
                {
                    "id": "q02",
                    "question": "x",
                    "answerable": True,
                    "expected_doc": "a.pdf",
                    "expected_page": 1,
                    "answer_keywords": [],
                },
                "una pregunta con respuesta necesita answer_keywords",
            ),
            (
                {
                    "id": "u01",
                    "question": "x",
                    "answerable": False,
                    "expected_doc": "a.pdf",
                },
                "una pregunta sin respuesta no lleva expected_doc",
            ),
        ],
    )
    def test_check_consistency(self, kwargs, error_contains):
        with pytest.raises(ValidationError) as exc_info:
            EvalQuestion(**kwargs)
        assert error_contains in str(exc_info.value)


class TestJsonRoto:
    """Test 6: JSON inválido en línea 2."""

    def test_json_roto(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            json.dump(
                {
                    "id": "q01",
                    "question": "x",
                    "answerable": True,
                    "expected_doc": "a.pdf",
                    "expected_page": 1,
                    "answer_keywords": ["x"],
                },
                f,
            )
            f.write("\n{no es json\n")
            f.flush()
            with pytest.raises(DatasetError) as exc_info:
                load_questions(Path(f.name))
        assert str(exc_info.value).startswith("línea 2:")


class TestIdRepetido:
    """Test 7: id repetido en la línea 3."""

    def test_id_repetido(self):
        def _valid_q(ident: str) -> dict:
            return {
                "id": ident,
                "question": "x",
                "answerable": True,
                "expected_doc": "a.pdf",
                "expected_page": 1,
                "answer_keywords": ["x"],
            }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            json.dump(_valid_q("q01"), f)
            f.write("\n")
            json.dump(_valid_q("q02"), f)
            f.write("\n")
            json.dump(_valid_q("q01"), f)
            f.flush()
            with pytest.raises(DatasetError) as exc_info:
                load_questions(Path(f.name))
        assert str(exc_info.value) == "línea 3: id repetido q01"


class TestArchivoVacio:
    """Test 8: archivo vacío o solo líneas en blanco."""

    def test_archivo_vacio(self):
        with (
            tempfile.NamedTemporaryFile(
                mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
            ) as f,
            pytest.raises(DatasetError) as exc_info,
        ):
            load_questions(Path(f.name))
        assert str(exc_info.value) == "sin preguntas"


class TestLineasBlancoIgnoradas:
    """Test 9: líneas en blanco intermedias se ignoran."""

    def test_lineas_blanco_ignoradas(self):
        def _valid_q(ident: str) -> dict:
            return {
                "id": ident,
                "question": "x",
                "answerable": True,
                "expected_doc": "a.pdf",
                "expected_page": 1,
                "answer_keywords": ["x"],
            }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            json.dump(_valid_q("q01"), f)
            f.write("\n\n")
            json.dump(_valid_q("q02"), f)
            f.flush()
            questions = load_questions(Path(f.name))
        assert len(questions) == 2
