"""Fusión de rankings con RRF y deduplicación de chunks contiguos."""

from collections import defaultdict
from collections.abc import Sequence

from docuchat.models import Chunk


def rrf_fuse(rankings: Sequence[Sequence[str]], k: int) -> list[tuple[str, float]]:
    """Fusiona rankings de ids con RRF: score = suma de 1 / (k + puesto).

    * El puesto de cada id es su posición en el ranking (desde 1).
    * Si un id se repite dentro del MISMO ranking solo cuenta su primera aparición.
    * El resultado se ordena por score descendente; en caso de empate, por id ascendente.
    """
    if k <= 0:
        raise ValueError("k debe ser positivo")

    scores: dict[str, float] = defaultdict(float)

    for ranking in rankings:
        seen_in_rank: set[str] = set()
        for rank, item_id in enumerate(ranking, start=1):
            if item_id not in seen_in_rank:
                scores[item_id] += 1.0 / (k + rank)
                seen_in_rank.add(item_id)

    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))


def drop_adjacent(ranked: Sequence[Chunk]) -> list[Chunk]:
    """Quita los chunks contiguos (misma página, posición ±1) a otro ya aceptado.

    Se recorren en orden; un chunk se descarta si ya se aceptó otro con la misma
    ``source``, la misma ``page`` y ``abs(position - otro.position) == 1``.
    Solo cuentan los ACEPTADOS (un chunk descartado no bloquea a sus vecinos).
    """
    accepted: list[Chunk] = []

    for chunk in ranked:
        adjacent_to_accepted = any(
            c.source == chunk.source
            and c.page == chunk.page
            and abs(c.position - chunk.position) == 1
            for c in accepted
        )
        if not adjacent_to_accepted:
            accepted.append(chunk)

    return accepted
