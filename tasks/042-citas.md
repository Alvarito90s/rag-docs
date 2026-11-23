# 042 · Parser de citas
Fase: 4 · Depende de: 041

## Objetivo
Extraer las citas `[n]` de una respuesta, mapearlas a documento y página, separar las inventadas (número sin fragmento) y detectar la respuesta "No lo sé".

## Archivos
- crear: `src/docuchat/generation/citations.py`
- crear: `tests/generation/test_citations.py`

## Interfaz
```python
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

from docuchat.generation.prompts import NO_ANSWER
from docuchat.models import SearchResult

CITATION_RE = re.compile(r"\[\s*(\d+(?:\s*[,;]\s*\d+)*)\s*\]")


@dataclass(frozen=True)
class Source:
    """Fragmento citado: su número en el contexto, documento y página."""

    number: int
    source: str
    page: int


def find_citations(text: str) -> list[int]:
    """Números citados, sin repetir, en orden de primera aparición."""


def resolve_citations(
    text: str, context: Sequence[SearchResult]
) -> tuple[list[Source], list[int]]:
    """(fuentes válidas en orden de cita, números inventados en orden de cita)."""


def is_no_answer(text: str) -> bool:
    """True si la respuesta empieza por 'no lo sé' (sin distinguir mayúsculas ni tildes)."""
```

## Comportamiento
1. `find_citations`: para cada coincidencia de `CITATION_RE`, separa el grupo por `,` o `;` (con espacios opcionales) y convierte a `int`. Admite `[1]`, `[2][3]`, `[1, 4]`, `[ 2 ]`, `[5;6]`. No valida rangos.
2. `resolve_citations`: el número `n` es válido si `1 <= n <= len(context)`; su `Source` usa `context[n - 1].chunk.source` y `.page`. Los demás van a la lista de inventados.
3. `is_no_answer`: normaliza con NFKD, quita los caracteres combinantes, pasa a minúsculas y quita espacios de los extremos; `True` si empieza por `"no lo se"`. Una cadena vacía → `False`.
4. `NO_ANSWER` se importa para los tests y para no duplicar el texto; no lo redefinas.

## Tests obligatorios
`tests/generation/test_citations.py`. NO cambies los valores esperados. Reutiliza el helper `mk` de `test_prompts.py` (cópialo).
1. `find_citations("A [1]. B [2][3], C [1, 4] y [ 2 ]; D [5;6]")` → `[1, 2, 3, 4, 5, 6]`.
2. `find_citations("Sin citas")` → `[]`; `find_citations("Año [2025] y [a]")` → `[2025]`; `find_citations("[0]")` → `[0]`.
3. Con `ctx = [mk("a.pdf", 1, "x"), mk("b.md", 2, "y", 2)]`: `resolve_citations("X [2]. Y [1][2]. Z [7].", ctx)` → `([Source(2, "b.md", 2), Source(1, "a.pdf", 1)], [7])`.
4. `resolve_citations("Nada [0] [3]", ctx)` → `([], [0, 3])`.
5. `resolve_citations("Sin citas.", ctx)` → `([], [])`; `resolve_citations("Dato [1].", [])` → `([], [1])`.
6. `is_no_answer` (parametrizado): `NO_ANSWER` → True; `"  no lo se."` → True; `"NO LO SÉ"` → True; `"El depósito... no lo sé"` → False; `""` → False.

## Aceptación
- [ ] `uv run pytest -q tests/generation/test_citations.py` → 10 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
No quites las citas inventadas del texto (la respuesta llega en streaming; solo se avisa). No toques `prompts.py`.
