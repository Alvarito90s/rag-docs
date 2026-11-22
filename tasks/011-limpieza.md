# 011 · Limpieza de texto
Fase: 1 · Depende de: 010

## Objetivo
Funciones puras para limpiar el texto extraído: guiones de fin de línea, espacios, saltos de línea y cabeceras/pies repetidos.

## Archivos
- crear: `src/docuchat/ingest/cleaning.py`
- crear: `tests/ingest/test_cleaning.py`

## Interfaz
```python
import re


def fix_hyphenation(text: str) -> str:
    """Une palabras partidas con guion a final de línea: 'descalci-\\nficación' -> 'descalcificación'."""


def normalize_whitespace(text: str) -> str:
    """Normaliza espacios y saltos de línea conservando los párrafos ('\\n\\n')."""


def join_lines(paragraph: str) -> str:
    """Convierte los saltos de línea internos de un párrafo en un espacio."""


def edge_key(paragraph: str) -> str:
    """Clave para comparar cabeceras/pies: espacios colapsados y cada número sustituido por '#'."""


def remove_repeated_edges(
    pages: list[list[str]],
    min_pages: int = 3,
    min_ratio: float = 0.6,
    edge: int = 2,
) -> list[list[str]]:
    """Quita de cada página los párrafos de borde (cabecera/pie) que se repiten en muchas páginas."""
```

## Comportamiento
1. `fix_hyphenation`: `re.sub(r"(\w)-\n(\w)", r"\1\2", text)`. Solo actúa con guion + `\n` entre dos caracteres de palabra.
2. `normalize_whitespace`, en este orden:
   a. `\r\n` y `\r` → `\n`; ` ` (espacio duro) → espacio.
   b. Cualquier secuencia de espacios, tabuladores, `\f` o `\v` → un espacio: `re.sub(r"[ \t\f\v]+", " ", t)`.
   c. Quita espacios alrededor de cada `\n`: `re.sub(r" *\n *", "\n", t)`.
   d. 3 o más `\n` seguidos → `\n\n`.
   e. `strip()` del resultado.
3. `join_lines`: `re.sub(r"\s*\n\s*", " ", paragraph).strip()`.
4. `edge_key`: `re.sub(r"\d+", "#", " ".join(paragraph.split()))`.
5. `remove_repeated_edges` (no modifica la entrada; devuelve listas nuevas):
   a. Si `len(pages) < min_pages`, devuelve una copia sin cambios.
   b. Posiciones de borde de una página con `n` párrafos: índices `i` con `i < edge` o `i >= n - edge`.
   c. Para cada página, el CONJUNTO de `edge_key` de sus párrafos de borde (ignora claves vacías). Cuenta en cuántas páginas aparece cada clave.
   d. Clave repetida: `apariciones / len(pages) >= min_ratio`.
   e. En cada página se eliminan los párrafos que están en posición de borde Y cuya clave es repetida. Los párrafos que no son de borde nunca se eliminan.

## Tests obligatorios
`tests/ingest/test_cleaning.py`. NO cambies los valores esperados.
1. `fix_hyphenation("la descalci-\nficación")` → `"la descalcificación"`.
2. `fix_hyphenation("SKU-4471-B")` → igual (sin `\n`).
3. `fix_hyphenation("fin -\ninicio")` → igual (espacio antes del guion).
4. `fix_hyphenation("E-\n17")` → `"E17"`.
5. `normalize_whitespace("  a \t  b  \r\n\r\n\r\n\r\nc  ")` → `"a b\n\nc"`.
6. `normalize_whitespace("x y")` → `"x y"`.
7. `normalize_whitespace("uno\ndos")` → `"uno\ndos"` (los saltos simples se conservan).
8. `normalize_whitespace("")` → `""`.
9. `join_lines("hola\nmundo \n  adiós")` → `"hola mundo adiós"`.
10. `edge_key("Página 12 de 40")` → `"Página # de #"`; `edge_key("  Brevia   X2 · página 3\n")` → `"Brevia X# · página #"`.
11. Cabecera y pie en 4 páginas:
    entrada `[["Cab", "cuerpo uno", "Página 1 de 4"], ["Cab", "cuerpo dos", "Página 2 de 4"], ["Cab", "cuerpo tres", "Página 3 de 4"], ["Cab", "cuerpo cuatro", "Página 4 de 4"]]`
    → `[["cuerpo uno"], ["cuerpo dos"], ["cuerpo tres"], ["cuerpo cuatro"]]`.
    (Ojo: los cuerpos no llevan números a propósito; `"cuerpo 1"` y `"cuerpo 2"` tendrían la misma clave `"cuerpo #"`.)
12. Solo 2 páginas (`< min_pages`): `[["Cab", "a"], ["Cab", "b"]]` → igual.
13. Repetición por debajo del umbral: cabecera `"Cab"` en 2 de 4 páginas (`[["Cab","a"],["Cab","b"],["c"],["d"]]`) → igual (0,5 < 0,6).
14. Un párrafo repetido que NO está en el borde no se quita: 4 páginas, la página `x` (x en `"ABCD"`) es `[f"inicio {x}", f"intro {x}", "REP", f"cierre {x}", f"fin {x}"]` (con `edge=2`, el índice 2 de 5 no es borde) → igual.
15. La entrada no se modifica: tras llamar con la entrada del caso 11, la lista original sigue teniendo `"Cab"` en cada página.

## Aceptación
- [ ] `uv run pytest -q tests/ingest/test_cleaning.py` → 15 passed
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Leer archivos. Cualquier otra limpieza (OCR, columnas, tablas de PDF).
