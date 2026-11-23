# 031 · Fusión RRF y deduplicación de chunks contiguos
Fase: 3 · Depende de: 030

## Objetivo
Funciones puras para fusionar rankings con Reciprocal Rank Fusion y quitar chunks contiguos (solapados) del mismo documento y página.

## Archivos
- crear: `src/docuchat/retrieval/__init__.py` (solo el docstring `"""Recuperación: fusión de rankings y búsqueda híbrida."""`)
- crear: `src/docuchat/retrieval/fusion.py`
- crear: `tests/retrieval/__init__.py` (vacío) y `tests/retrieval/test_fusion.py`

## Interfaz
```python
from collections.abc import Sequence

from docuchat.models import Chunk


def rrf_fuse(rankings: Sequence[Sequence[str]], k: int) -> list[tuple[str, float]]:
    """Fusiona rankings de ids con RRF: score = suma de 1 / (k + puesto)."""


def drop_adjacent(ranked: Sequence[Chunk]) -> list[Chunk]:
    """Quita los chunks contiguos (misma página, posición ±1) a otro ya aceptado."""
```

## Comportamiento
1. `rrf_fuse`:
   a. Si `k <= 0` → `ValueError("k debe ser positivo")`.
   b. En cada ranking, el puesto es la posición desde 1. Si un id se repite dentro del MISMO ranking, solo cuenta su primera aparición (las siguientes se ignoran, pero ocupan puesto).
   c. `score(id) = Σ 1 / (k + puesto)` sobre los rankings en los que aparece.
   d. Devuelve `(id, score)` ordenado por score descendente y, a igualdad, por id ascendente. Rankings vacíos o lista vacía → `[]`.
2. `drop_adjacent`: recorre `ranked` en orden; acepta un chunk salvo que ya se haya aceptado otro con la misma `source`, la misma `page` y `abs(position - otro.position) == 1`. Solo cuentan los ACEPTADOS (un chunk descartado no bloquea a sus vecinos). Mantiene el orden. Motivo: el chunker solapa 120 caracteres entre chunks contiguos de una página, y mostrar los dos repite texto.

## Tests obligatorios
`tests/retrieval/test_fusion.py`. NO cambies los valores esperados. Usa `pytest.approx(..., abs=1e-6)` para los scores.
Helper:
```python
def mk(source: str, page: int, position: int) -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id(source, page, position),
        source=source,
        doc_sha256="a" * 64,
        page=page,
        position=position,
        text="x",
    )
```
1. `rrf_fuse([["a", "b", "c"], ["b", "c", "d"]], 60)` → ids `["b", "c", "a", "d"]`, scores `[0.0325225, 0.0320020, 0.0163934, 0.0158730]`.
2. Empate: `rrf_fuse([["a", "b"], ["b", "a"]], 1)` → `[("a", 0.833333), ("b", 0.833333)]` (orden por id).
3. Un solo ranking conserva el orden: `rrf_fuse([["z", "y", "x"]], 60)` → ids `["z", "y", "x"]`.
4. Repetidos: `rrf_fuse([["a", "a", "b"]], 60)` → `[("a", 1/61), ("b", 1/63)]`.
5. Vacíos: `rrf_fuse([], 60) == []` y `rrf_fuse([[], []], 60) == []`.
6. `rrf_fuse([["a"]], 0)` → `ValueError`.
7. `drop_adjacent([mk("A", 1, 1), mk("A", 1, 0), mk("A", 1, 2), mk("A", 2, 0), mk("B", 1, 0), mk("A", 1, 3)])` → ids `["A#p1#c1", "A#p2#c0", "B#p1#c0", "A#p1#c3"]`.
8. No contiguos se conservan: `drop_adjacent([mk("A", 1, 0), mk("A", 1, 2)])` → los dos.
9. Misma posición en otra página u otro documento no cuenta: `drop_adjacent([mk("A", 1, 0), mk("A", 2, 1), mk("B", 1, 1)])` → los tres.
10. `drop_adjacent([]) == []`.

## Aceptación
- [ ] `uv run pytest -q tests/retrieval/test_fusion.py` → 10 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
Nada de Chroma, BM25 ni embeddings (spec 033). No toques `models.py`.
