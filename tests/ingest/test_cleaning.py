"""Tests para las funciones de limpieza de texto."""

from docuchat.ingest.cleaning import (
    edge_key,
    fix_hyphenation,
    join_lines,
    normalize_whitespace,
    remove_repeated_edges,
)

# --- test_fix_hyphenation ---


def test_fix_hyphenation_basic() -> None:
    assert fix_hyphenation("la descalcifi-\ncación") == "la descalcificación"


def test_fix_hyphenation_no_newline() -> None:
    assert fix_hyphenation("SKU-4471-B") == "SKU-4471-B"


def test_fix_hyphenation_space_before_hyphen() -> None:
    assert fix_hyphenation("fin -\ninicio") == "fin -\ninicio"


def test_fix_hyphenation_e17() -> None:
    assert fix_hyphenation("E-\n17") == "E17"


# --- test_normalize_whitespace ---


def test_normalize_whitespace_basic() -> None:
    assert normalize_whitespace("  a \t  b  \r\n\r\n\r\n\r\nc  ") == "a b\n\nc"


def test_normalize_whitespace_nbsp() -> None:
    assert normalize_whitespace("x\xa0y") == "x y"


def test_normalize_whitespace_preserve_single_newline() -> None:
    assert normalize_whitespace("uno\ndos") == "uno\ndos"


def test_normalize_whitespace_empty() -> None:
    assert normalize_whitespace("") == ""


# --- test_join_lines ---


def test_join_lines() -> None:
    assert join_lines("hola\nmundo \n  adiós") == "hola mundo adiós"


# --- test_edge_key ---


def test_edge_key() -> None:
    assert edge_key("Página 12 de 40") == "Página # de #"
    assert edge_key("  Brevia   X2 · página 3\n") == "Brevia X# · página #"


# --- test_remove_repeated_edges ---


def test_remove_repeated_edges_header_footer() -> None:
    entrada = [
        ["Cab", "cuerpo uno", "Página 1 de 4"],
        ["Cab", "cuerpo dos", "Página 2 de 4"],
        ["Cab", "cuerpo tres", "Página 3 de 4"],
        ["Cab", "cuerpo cuatro", "Página 4 de 4"],
    ]
    expected = [["cuerpo uno"], ["cuerpo dos"], ["cuerpo tres"], ["cuerpo cuatro"]]
    resultado = remove_repeated_edges(entrada)
    assert resultado == expected


def test_remove_repeated_edges_two_pages() -> None:
    entrada = [["Cab", "a"], ["Cab", "b"]]
    resultado = remove_repeated_edges(entrada)
    assert resultado == [["Cab", "a"], ["Cab", "b"]]


def test_remove_repeated_edges_below_threshold() -> None:
    entrada = [["Cab", "a"], ["Cab", "b"], ["c"], ["d"]]
    resultado = remove_repeated_edges(entrada)
    assert resultado == [["Cab", "a"], ["Cab", "b"], ["c"], ["d"]]


def test_remove_repeated_edges_non_edge_not_removed() -> None:
    entrada = [[f"inicio {c}", f"intro {c}", "REP", f"cierre {c}", f"fin {c}"] for c in "ABCD"]
    resultado = remove_repeated_edges(entrada, edge=2)
    assert resultado == entrada


def test_remove_repeated_edges_does_not_modify_input() -> None:
    entrada = [
        ["Cab", "cuerpo uno", "Página 1 de 4"],
        ["Cab", "cuerpo dos", "Página 2 de 4"],
        ["Cab", "cuerpo tres", "Página 3 de 4"],
        ["Cab", "cuerpo cuatro", "Página 4 de 4"],
    ]
    original = [list(p) for p in entrada]
    remove_repeated_edges(entrada)
    assert entrada == original
