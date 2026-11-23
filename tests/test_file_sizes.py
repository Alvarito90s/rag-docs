"""Tests del límite de 300 líneas en archivos de src/."""

from pathlib import Path

from docuchat.cli_format import (
    build_table,  # noqa: F401
    format_result,  # noqa: F401
    format_sources,  # noqa: F401
    snippet,  # noqa: F401
    stats_line,  # noqa: F401
    summary_line,  # noqa: F401
)

SRC = Path(__file__).resolve().parents[1] / "src"
MAX_LINES = 300


def test_src_files_under_limit() -> None:
    """Cada archivo .py bajo src/ debe tener menos de 300 líneas."""
    too_long: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        n = len(path.read_text(encoding="utf-8").splitlines())
        if n >= MAX_LINES:
            too_long.append(f"{path.relative_to(SRC)}: {n}")
    assert not too_long, "\n".join(too_long)


def test_scan_finds_files() -> None:
    """Debe haber al menos 30 archivos .py en src/."""
    assert len(list(SRC.rglob("*.py"))) >= 30


def test_cli_format_importable() -> None:
    """Las funciones son importables desde cli_format y cli, y son la misma."""
    from docuchat.cli import build_table as b2

    assert b2 is build_table
