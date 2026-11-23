"""Tests para la spec 093: rerank activado por defecto (decisión H3)."""

from collections.abc import Sequence

from docuchat.config import Settings, get_settings
from docuchat.evaluation.variants import VARIANTS, parse_variants, variant_settings
from docuchat.retrieval.searcher import build_searcher


def test_activado_por_defecto(settings) -> None:
    """Configuración por defecto: rerank_enabled=True, 10 candidatos."""
    s = Settings()
    assert s.rerank_enabled is True
    assert s.rerank_candidates == 10


def test_desactivable_por_entorno(settings, monkeypatch) -> None:
    """DOCUCHAT_RERANK_ENABLED=false desactiva el rerank."""
    monkeypatch.setenv("DOCUCHAT_RERANK_ENABLED", "false")
    get_settings.cache_clear()
    assert get_settings().rerank_enabled is False
    get_settings.cache_clear()


def test_tests_sin_reranker_real(settings) -> None:
    """El fixture autouse de conftest.py evita llamadas al reranker real."""
    from docuchat.config import Settings

    class FakeEmbedder:
        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            return [[1.0, 0.0, 0.5] for _ in texts]

    searcher = build_searcher(Settings(), embedder=FakeEmbedder())
    assert searcher._reranker is None


def test_variante_sin_rerank(settings) -> None:
    """La variante sin_rerank existe y funciona correctamente."""
    assert VARIANTS["sin_rerank"] == {"rerank_enabled": False}
    assert variant_settings(settings, "sin_rerank").rerank_enabled is False
    assert variant_settings(settings, "base").rerank_enabled is True
    assert parse_variants("sin_rerank,base") == ["sin_rerank", "base"]
