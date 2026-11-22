"""Tests obligatorios para la CLI, spec 015-cli-ingest.md."""

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from docuchat.cli import app, build_table, summary_line
from docuchat.config import get_settings
from docuchat.ingest.scanner import IngestResult
from docuchat.models import DocType, Document, Page

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
runner = CliRunner()


# --- 1. test_01_help ---


def test_01_help() -> None:
    """runner.invoke(app, ["--help"]) → exit_code 0, 'ingest' en salida."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ingest" in result.output


# --- 2. test_02_ingest_dry_run_samples ---


def test_02_ingest_dry_run_samples() -> None:
    """ingest SAMPLES --dry-run → exit 0, docs presentes, resumen coincide."""
    result = runner.invoke(app, ["ingest", str(SAMPLES), "--dry-run"])
    assert result.exit_code == 0
    assert "contrato_servicios.pdf" in result.output
    assert "politica_vacaciones.docx" in result.output
    assert re.search(r"7 documentos, 22 páginas, \d+ caracteres", result.output)


# --- 3. test_03_no_dry_run ---


def test_03_no_dry_run() -> None:
    """ingest SAMPLES sin --dry-run → exit 1, mensaje 'Usa --dry-run'."""
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 1
    assert "Usa --dry-run" in result.output


# --- 4. test_04_nonexistent_folder ---


def test_04_nonexistent_folder(tmp_path: Path) -> None:
    """ingest path_inexistente --dry-run → exit 1, 'No existe la carpeta'."""
    result = runner.invoke(app, ["ingest", str(tmp_path / "no"), "--dry-run"])
    assert result.exit_code == 1
    assert "No existe la carpeta" in result.output


# --- 5. test_05_mixed_ok_broken ---


def test_05_mixed_ok_broken(tmp_path: Path) -> None:
    """ok.txt + roto.pdf → exit 1, ERROR roto.pdf, resumen 1 doc/1 pág/4 chars."""
    (tmp_path / "ok.txt").write_text("hola")
    (tmp_path / "roto.pdf").write_bytes(b"no soy un pdf")
    result = runner.invoke(app, ["ingest", str(tmp_path), "--dry-run"])
    assert result.exit_code == 1
    assert "ERROR roto.pdf: FileDataError" in result.output
    assert "1 documentos, 1 páginas, 4 caracteres" in result.output


# --- 6. test_06_default_documents_dir ---


def test_06_default_documents_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Sin carpeta pero DOCUCHAT_DOCUMENTS_DIR=SAMPLES → 7 documentos."""
    monkeypatch.setenv("DOCUCHAT_DOCUMENTS_DIR", str(SAMPLES))
    get_settings.cache_clear()
    result = runner.invoke(app, ["ingest", "--dry-run"])
    get_settings.cache_clear()
    assert result.exit_code == 0
    assert "7 documentos" in result.output


# --- 7. test_07_summary_line_empty ---


def test_07_summary_line_empty() -> None:
    """summary_line(IngestResult()) → '0 documentos, 0 páginas, 0 caracteres'."""
    assert summary_line(IngestResult()) == "0 documentos, 0 páginas, 0 caracteres"


# --- 8. test_08_build_table_two_pages ---


def test_08_build_table_two_pages() -> None:
    """build_table con documento de 2 páginas → table.row_count == 2."""
    page1 = Page(number=1, text="hola")
    page2 = Page(number=2, text="mundo")
    doc = Document(
        source="test.txt",
        path=Path("/tmp/test.txt"),
        sha256="a" * 64,
        doc_type=DocType.TXT,
        pages=(page1, page2),
    )
    result = IngestResult(documents=[doc])
    table = build_table(result, Path("/tmp"))
    assert table.row_count == 2
