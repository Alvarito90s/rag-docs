"""Índice BM25 en memoria sobre (id, texto).

Se construye a partir de los chunks de la base vectorial al arrancar
la búsqueda, con lo que siempre hay una única fuente de verdad.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    """Minúsculas, sin tildes, palabras alfanuméricas.

    'Garantía SKU-4471' -> ['garantia', 'sku', '4471'].
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    return re.findall(r"\w+", text)


class Bm25Index:
    """Índice BM25 en memoria sobre (id, texto)."""

    def __init__(self, ids: Sequence[str], texts: Sequence[str]) -> None:
        if len(ids) != len(texts):
            raise ValueError("ids y texts deben tener la misma longitud")

        self._ids: list[str] = list(ids)
        self._token_lists: list[list[str]] = [tokenize(t) for t in texts]
        self._vocab_sets: list[set[str]] = [set(tokens) for tokens in self._token_lists]
        self._len = len(self._ids)

        if self._len > 0:
            self._bm25: BM25Okapi | None = BM25Okapi(self._token_lists)
        else:
            self._bm25 = None

    def __len__(self) -> int:
        return self._len

    def search(self, query: str, k: int) -> list[tuple[str, float]]:
        """Busca ``query`` y devuelve hasta ``k`` resultados como (id, score)."""
        if k <= 0 or self._bm25 is None:
            return []

        tokens_query = tokenize(query)
        if not tokens_query:
            return []

        scores = self._bm25.get_scores(tokens_query)

        # Solo documentos con intersección de tokens
        candidates: list[tuple[int, float]] = []
        for idx, vocab in enumerate(self._vocab_sets):
            if set(tokens_query) & vocab:
                candidates.append((idx, float(scores[idx])))

        # Ordena por score descendente, a igualdad por posición original
        candidates.sort(key=lambda x: (-x[1], x[0]))

        return [(self._ids[idx], score) for idx, score in candidates[:k]]
