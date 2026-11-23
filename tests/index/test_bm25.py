"""Tests del índice BM25 (spec 025)."""

import pytest

from docuchat.index.bm25 import Bm25Index, tokenize

IDS = ["c1", "c2", "c3", "c4"]
TEXTS = [
    "El proveedor ofrece una garantía de dos años.",
    "El depósito de agua tiene 1,8 litros.",
    "El código de error E-17 indica depósito vacío.",
    "Referencia interna SKU-4471-B del filtro.",
]


class TestTokenize:
    def test_garantia_sku(self) -> None:
        assert tokenize("Garantía de DOS años, SKU-4471-B!") == [
            "garantia",
            "de",
            "dos",
            "anos",
            "sku",
            "4471",
            "b",
        ]

    def test_special_chars(self) -> None:
        assert tokenize("¿Qué pasa?") == ["que", "pasa"]
        assert tokenize("") == []


class TestBm25Index:
    @classmethod
    def setup_class(cls) -> None:
        cls.index = Bm25Index(IDS, TEXTS)

    def test_search_garantia(self) -> None:
        results = self.index.search("garantia", 5)
        assert len(results) == 1
        assert results[0][0] == "c1"
        assert results[0][1] == pytest.approx(0.8473, abs=1e-3)

    def test_search_garantia_with_accents(self) -> None:
        results = self.index.search("Garantía", 5)
        assert len(results) == 1
        assert results[0][0] == "c1"
        assert results[0][1] == pytest.approx(0.8473, abs=1e-3)

    def test_search_code_e17(self) -> None:
        results = self.index.search("E-17", 5)
        assert len(results) == 1
        assert results[0][0] == "c3"

    def test_search_sku_4471(self) -> None:
        results = self.index.search("sku 4471", 5)
        assert len(results) == 1
        assert results[0][0] == "c4"

    def test_search_deposito(self) -> None:
        results = self.index.search("deposito", 5)
        ids = [r[0] for r in results]
        assert ids == ["c2", "c3"]

    def test_search_el_de(self) -> None:
        results = self.index.search("el de", 5)
        ids = [r[0] for r in results]
        assert ids == ["c1", "c2", "c3"]

    def test_search_el_de_k1(self) -> None:
        results = self.index.search("el de", 1)
        assert [r[0] for r in results] == ["c1"]

    def test_search_no_results(self) -> None:
        assert self.index.search("xyz", 5) == []
        assert self.index.search("", 5) == []
        assert self.index.search("garantia", 0) == []

    def test_empty_index(self) -> None:
        empty = Bm25Index([], [])
        assert len(empty) == 0
        assert empty.search("algo", 5) == []

    def test_mismatched_lengths(self) -> None:
        try:
            Bm25Index(["a"], [])
            raise AssertionError("Debería haber lanzado ValueError")
        except ValueError:
            pass
