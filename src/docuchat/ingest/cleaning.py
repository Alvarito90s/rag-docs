"""Funciones puras para limpiar texto extraído de documentos."""

import re


def fix_hyphenation(text: str) -> str:
    """Une palabras partidas con guion a final de línea.

    'descalici-\\nficación' -> 'descalcificación'.
    """
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def normalize_whitespace(text: str) -> str:
    """Normaliza espacios y saltos de línea conservando los párrafos ('\\n\\n')."""
    t = text
    # a. \r\n y \r → \n; espacio duro → espacio
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\xa0", " ")
    # b. secuencia de espacios, tabs, \f, \v → un espacio
    t = re.sub(r"[ \t\f\v]+", " ", t)
    # c. espacios alrededor de cada \n
    t = re.sub(r" *\n *", "\n", t)
    # d. 3+ \n seguidos → \n\n
    t = re.sub(r"\n{3,}", "\n\n", t)
    # e. strip
    return t.strip()


def join_lines(paragraph: str) -> str:
    """Convierte los saltos de línea internos de un párrafo en un espacio."""
    return re.sub(r"\s*\n\s*", " ", paragraph).strip()


def edge_key(paragraph: str) -> str:
    """Clave para comparar cabeceras/pies: espacios colapsados y cada número
    sustituido por '#'.
    """
    return re.sub(r"\d+", "#", " ".join(paragraph.split()))


def remove_repeated_edges(
    pages: list[list[str]],
    min_pages: int = 3,
    min_ratio: float = 0.6,
    edge: int = 2,
) -> list[list[str]]:
    """Quita de cada página los párrafos de borde que se repiten en muchas."""
    if len(pages) < min_pages:
        return [list(p) for p in pages]

    # Para cada página, el conjunto de edge_key de sus párrafos de borde
    page_edge_keys: list[set[str]] = []
    for page in pages:
        n = len(page)
        edge_indices = {i for i in range(n) if i < edge or i >= n - edge}
        keys: set[str] = set()
        for i in edge_indices:
            k = edge_key(page[i])
            if k:
                keys.add(k)
        page_edge_keys.append(keys)

    # Cuenta en cuántas páginas aparece cada clave
    key_counts: dict[str, int] = {}
    for keys in page_edge_keys:
        for k in keys:
            key_counts[k] = key_counts.get(k, 0) + 1

    # Clave repetida
    repeated_keys: set[str] = {
        k for k, count in key_counts.items() if count / len(pages) >= min_ratio
    }

    # Elimina párrafos de borde con clave repetida
    result: list[list[str]] = []
    for _idx, page in enumerate(pages):
        n = len(page)
        edge_indices = {i for i in range(n) if i < edge or i >= n - edge}
        new_page: list[str] = []
        for i, para in enumerate(page):
            if i in edge_indices and edge_key(para) in repeated_keys:
                continue
            new_page.append(para)
        result.append(new_page)
    return result
