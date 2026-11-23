"""Funciones puras para métricas de evaluación de recuperación y respuesta."""

import unicodedata
from collections.abc import Sequence

from docuchat.generation.citations import Source
from docuchat.models import SearchResult


def normalize(text: str) -> str:
    """Minúsculas y sin tildes (NFKD sin caracteres combinantes)."""
    nfd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfd if not unicodedata.combining(c))
    return stripped.lower()


def keywords_hit(text: str, keywords: Sequence[str]) -> bool:
    """True si TODAS las palabras clave aparecen; cada una admite alternativas separadas por '|'."""
    normalized = normalize(text)
    for kw in keywords:
        alternatives = kw.split("|")
        if not any(normalize(alt) in normalized for alt in alternatives):
            return False
    return True


def first_hit_rank(results: Sequence[SearchResult], doc: str, page: int) -> int | None:
    """Posición (desde 1) del primer resultado con ese documento y página, o None."""
    for i, result in enumerate(results, start=1):
        if result.chunk.source == doc and result.chunk.page == page:
            return i
    return None


def hit_at(ranks: Sequence[int | None], k: int) -> float:
    """Fracción de puestos que no son None y son <= k."""
    if k <= 0:
        raise ValueError("k debe ser positivo")
    if not ranks:
        return 0.0
    hits = sum(1 for r in ranks if r is not None and r <= k)
    return hits / len(ranks)


def mean_reciprocal_rank(ranks: Sequence[int | None]) -> float:
    """Media de 1/puesto; None cuenta como 0."""
    if not ranks:
        return 0.0
    total = sum(1.0 / r if r is not None else 0.0 for r in ranks)
    return total / len(ranks)


def citation_counts(sources: Sequence[Source], doc: str, page: int) -> tuple[int, int]:
    """(citas a ese documento y página, citas totales)."""
    total = len(sources)
    correctas = sum(1 for s in sources if s.source == doc and s.page == page)
    return (correctas, total)


def ratio(numerator: int, denominator: int) -> float | None:
    """numerator/denominator, o None si denominator es 0."""
    if denominator == 0:
        return None
    return numerator / denominator
