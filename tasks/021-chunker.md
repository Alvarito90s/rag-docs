# 021 · Chunker recursivo
Fase: 2 · Depende de: 020

## Objetivo
Partir el texto de cada página en chunks de como mucho `chunk_size` caracteres, cortando por el separador más grande posible (párrafo → línea → frase → palabra) y con solape de unidades completas.

## Archivos
- crear: `src/docuchat/index/__init__.py` (solo `"""Indexado: chunker, embeddings, base vectorial, BM25 y registro."""`)
- crear: `src/docuchat/index/chunker.py`
- crear: `tests/index/test_chunker.py`

## Interfaz
```python
import re
from collections.abc import Sequence

from docuchat.models import Chunk, Document, make_chunk_id

# (texto con el que se vuelve a unir, regex con la que se parte), de mayor a menor
SEPARATORS: list[tuple[str, str]] = [
    ("\n\n", r"\n\n+"),  # párrafos
    ("\n", r"\n"),  # líneas
    (" ", r"(?<=[.!?])\s+"),  # frases
    (" ", r" +"),  # palabras
]

Unit = tuple[str, str]  # (joiner, texto): joiner es lo que va DELANTE de la unidad al unir


def split_units(text: str, chunk_size: int, joiner: str = "", level: int = 0) -> list[Unit]:
    """Descompone el texto en unidades de como mucho chunk_size caracteres."""


def join_units(units: Sequence[Unit]) -> str:
    """Une unidades: la primera sin su joiner, las demás precedidas por el suyo."""


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Agrupa unidades en chunks de como mucho chunk_size caracteres con solape."""


def chunk_document(doc: Document, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """Chunks de todas las páginas de un documento; ningún chunk cruza páginas."""
```

## Comportamiento
`split_units` (recursivo):
1. Si `len(text) <= chunk_size` → `[(joiner, text)]`.
2. Si `level >= len(SEPARATORS)` → corte duro: trozos `text[i:i + chunk_size]`; el primero lleva `joiner`, los demás `""`.
3. Si no: `sep, pattern = SEPARATORS[level]`; `parts = [p for p in re.split(pattern, text) if p.strip()]`.
   - Si `len(parts) <= 1` → `split_units(text, chunk_size, joiner, level + 1)`.
   - Si no, para cada `parte` (índice `i`): `split_units(parte.strip(), chunk_size, joiner if i == 0 else sep, level + 1)`, concatenando los resultados en orden.

`join_units`: `"".join(u if i == 0 else j + u for i, (j, u) in enumerate(units))`.

`split_text`:
1. Si `chunk_size <= 0` o `chunk_overlap < 0` o `chunk_overlap >= chunk_size` → `ValueError`.
2. `text = text.strip()`; si queda vacío → `[]`.
3. `units = split_units(text, chunk_size)`; recorre con una lista `current` (vacía al empezar) y `chunks = []`:
   - Si `current` está vacía → `current = [unit]`.
   - Si `len(join_units(current + [unit])) <= chunk_size` → añade `unit` a `current`.
   - Si no:
     a. añade `join_units(current)` a `chunks`;
     b. solape: `carry = []`; recorre `current` de atrás hacia delante; mientras `len(join_units([u] + carry)) <= chunk_overlap`, haz `carry = [u] + carry`; para en el primero que no cabe;
     c. `current = carry + [unit]`; mientras `len(current) > 1` y `len(join_units(current)) > chunk_size`, quita el primero.
4. Al final, si `current` no está vacía, añade `join_units(current)`.
5. Consecuencia buscada: el solape es de unidades completas (frases, palabras); si la última frase mide más que `chunk_overlap`, no hay solape. Nunca se corta una frase para solapar.

`chunk_document`: para cada página y cada `(position, texto)` de `enumerate(split_text(page.text, ...))` → `Chunk(chunk_id=make_chunk_id(doc.source, page.number, position), source=doc.source, doc_sha256=doc.sha256, page=page.number, position=position, heading=page.heading, text=texto)`.

## Tests obligatorios
`tests/index/test_chunker.py`. NO cambies los valores esperados. `split_text(texto, size, overlap)` →:
1. `("", 20, 5)` → `[]`; `("   \n\n ", 20, 5)` → `[]`.
2. `("Hola mundo.", 20, 5)` → `["Hola mundo."]`.
3. `("Uno dos.\n\nTres cuatro.\n\nCinco seis.", 20, 0)` → `["Uno dos.", "Tres cuatro.", "Cinco seis."]`.
4. Mismo texto con `(30, 0)` → `["Uno dos.\n\nTres cuatro.", "Cinco seis."]`.
5. `("Frase uno. Frase dos. Frase tres.", 22, 0)` → `["Frase uno. Frase dos.", "Frase tres."]`.
6. Mismo texto con `(22, 11)` → `["Frase uno. Frase dos.", "Frase dos. Frase tres."]`.
7. `("aaaa bbbb cccc dddd eeee", 10, 0)` → `["aaaa bbbb", "cccc dddd", "eeee"]`.
8. Mismo texto con `(10, 4)` → `["aaaa bbbb", "bbbb cccc", "cccc dddd", "dddd eeee"]`.
9. `("x" * 25, 10, 0)` → `["x" * 10, "x" * 10, "x" * 5]`.
10. `("Línea uno\nLínea dos\nLínea tres", 20, 0)` → `["Línea uno\nLínea dos", "Línea tres"]`.
11. Errores (parametrizado): `(0, 0)`, `(10, -1)`, `(10, 10)`, `(10, 11)` como `(size, overlap)` → `ValueError`.
12. `split_units("ab cd", 2)` → `[("", "ab"), (" ", "cd")]`.
13. `join_units([("x", "a"), ("\n\n", "b"), ("", "c")])` → `"a\n\nbc"`.
14. Con `load_folder(SAMPLES)` (de `docuchat.ingest.scanner`) y `chunk_document(doc, 800, 120)` para cada documento: total de chunks `26`; por `source`: `{"apuntes_redes.md": 3, "contrato_servicios.pdf": 5, "glosario_interno.md": 1, "manual_cafetera.pdf": 11, "notas_reunion.txt": 1, "paper_rag_resumen.pdf": 2, "politica_vacaciones.docx": 3}`; todos con `len(text) <= 800`; todos los `chunk_id` distintos.
15. Los datos clave quedan enteros en algún chunk de su página: `"El código de error E-17 indica que el depósito de agua está vacío."` (manual, p. 7) y `"El precio total del servicio asciende a 4.800 euros anuales, pagaderos por trimestres vencidos."` (contrato, p. 2).
16. `apuntes_redes.md`: el chunk de la página 2 tiene `heading == "Puertos habituales"` y `chunk_id == "apuntes_redes.md#p2#c0"`.

`SAMPLES = Path(__file__).resolve().parents[2] / "samples"`.

## Aceptación
- [ ] `uv run pytest -q tests/index/test_chunker.py` pasa
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Tokens (todo en caracteres), chunks que crucen páginas, embeddings.
