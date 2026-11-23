# 061 · Métricas de evaluación
Fase: 6 · Depende de: 060

## Objetivo
Funciones puras para las métricas: puesto del primer acierto, Hit@k, MRR, palabras clave en la respuesta y precisión de citas.

## Archivos
- crear: `src/docuchat/evaluation/metrics.py`
- crear: `tests/evaluation/test_metrics.py`

## Interfaz
```python
import unicodedata
from collections.abc import Sequence

from docuchat.generation.citations import Source
from docuchat.models import SearchResult


def normalize(text: str) -> str:
    """Minúsculas y sin tildes (NFKD sin caracteres combinantes)."""


def keywords_hit(text: str, keywords: Sequence[str]) -> bool:
    """True si TODAS las palabras clave aparecen; cada una admite alternativas separadas por '|'."""


def first_hit_rank(results: Sequence[SearchResult], doc: str, page: int) -> int | None:
    """Posición (desde 1) del primer resultado con ese documento y página, o None."""


def hit_at(ranks: Sequence[int | None], k: int) -> float:
    """Fracción de puestos que no son None y son <= k."""


def mean_reciprocal_rank(ranks: Sequence[int | None]) -> float:
    """Media de 1/puesto; None cuenta como 0."""


def citation_counts(sources: Sequence[Source], doc: str, page: int) -> tuple[int, int]:
    """(citas a ese documento y página, citas totales)."""


def ratio(numerator: int, denominator: int) -> float | None:
    """numerator/denominator, o None si denominator es 0."""
```

## Comportamiento
1. `normalize`: `unicodedata.normalize("NFKD", text)`, quita los caracteres con `unicodedata.combining(c)` y pasa a minúsculas. No toca espacios ni signos.
2. `keywords_hit`: normaliza `text`; para cada palabra clave, `split("|")`, y basta con que una alternativa normalizada sea subcadena del texto. Todas las palabras clave deben cumplirse. Lista vacía → `True`.
3. `first_hit_rank`: compara `result.chunk.source == doc` y `result.chunk.page == page`; el puesto es la posición en la lista (desde 1), no `result.rank`.
4. `hit_at` y `mean_reciprocal_rank` con lista vacía → `0.0`. `k <= 0` en `hit_at` → `ValueError("k debe ser positivo")`.
5. `citation_counts`: `total = len(sources)`; `correctas` = las de `source == doc` y `page == page`.

## Tests obligatorios
`tests/evaluation/test_metrics.py`. NO cambies los valores esperados. Usa `pytest.approx` para los `float`.
Helper `mk(source, page)` que crea un `SearchResult` (como en `tests/generation/test_prompts.py`).
1. `normalize("Garantía de DOS Años")` → `"garantia de dos anos"`.
2. `keywords_hit` (parametrizado, 7 casos):
   - `("El depósito está vacío.", ["vacío"])` → True
   - `("El deposito esta VACIO", ["vacío"])` → True
   - `("Cuesta 4800 euros", ["4.800|4800"])` → True
   - `("DNS usa el puerto 53 por UDP", ["53", "udp"])` → True
   - `("DNS usa el puerto 53", ["53", "udp"])` → False
   - `("No lo sé", ["valladolid"])` → False
   - `("cualquier cosa", [])` → True
3. `first_hit_rank([mk("a.pdf", 1), mk("b.pdf", 2), mk("b.pdf", 2)], "b.pdf", 2)` → `2`; con `"b.pdf", 3` → `None`; con lista vacía → `None`.
4. `hit_at([1, 3, None, 6], 5)` → `0.5`; `hit_at([1, 3, None, 6], 1)` → `0.25`; `hit_at([], 5)` → `0.0`; `hit_at([1], 0)` → `ValueError`.
5. `mean_reciprocal_rank([1, 2, None, 4])` → `(1 + 0.5 + 0 + 0.25) / 4 = 0.4375`; `mean_reciprocal_rank([])` → `0.0`.
6. `citation_counts([Source(1, "a.pdf", 3), Source(2, "a.pdf", 4), Source(3, "b.md", 3)], "a.pdf", 3)` → `(1, 3)`; con `[]` → `(0, 0)`.
7. `ratio(3, 4)` → `0.75`; `ratio(0, 0)` → `None`.

## Aceptación
- [ ] `uv run pytest -q tests/evaluation/test_metrics.py` → 13 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
Nada de búsquedas ni LLM (062, 063). No reutilices `is_no_answer` aquí.
