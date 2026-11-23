"""Tests obligatorios para la CLI, specs 015 y 027."""

import os
import re
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from openai import APIConnectionError
from typer.testing import CliRunner

from docuchat.cli import app, build_table, stats_line, summary_line
from docuchat.config import get_settings
from docuchat.index import indexer as indexer_mod
from docuchat.index.indexer import IndexStats
from docuchat.ingest.scanner import IngestResult
from docuchat.models import DocType, Document, Page

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
runner = CliRunner()


# ── FakeEmbedder (copia de tests/index/test_indexer.py) ─────────────────


class FakeEmbedder:
    def __init__(self, fail_on: str | None = None) -> None:
        self.calls: list[list[str]] = []
        self.fail_on = fail_on

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self.fail_on is not None and any(self.fail_on in t for t in texts):
            raise APIConnectionError(request=__import__("httpx").Request("POST", "http://test"))
        return [[float(len(t)), 1.0, 0.5] for t in texts]


# ── Fixture index_env ──────────────────────────────────────────────────


@pytest.fixture()
def index_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    """Índice en tmp_path/data con embedder falso; devuelve data_dir."""
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DOCUCHAT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(
        "docuchat.cli.build_indexer",
        lambda s: indexer_mod.build_indexer(s, embedder=FakeEmbedder()),
    )
    get_settings.cache_clear()
    yield tmp_path / "data"
    get_settings.cache_clear()


# ── Test 01: help ──────────────────────────────────────────────────────


def test_01_help() -> None:
    """runner.invoke(app, ["--help"]) → exit_code 0, 'ingest' en salida."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ingest" in result.output


# ── Test 02: dry-run samples ───────────────────────────────────────────


def test_02_ingest_dry_run_samples() -> None:
    """ingest SAMPLES --dry-run → exit 0, docs presentes, resumen coincide."""
    result = runner.invoke(app, ["ingest", str(SAMPLES), "--dry-run"])
    assert result.exit_code == 0
    assert "contrato_servicios.pdf" in result.output
    assert "politica_vacaciones.docx" in result.output
    assert re.search(r"7 documentos, 22 páginas, \d+ caracteres", result.output)


# ── Test 04: carpeta inexistente ───────────────────────────────────────


def test_04_nonexistent_folder(tmp_path: Path) -> None:
    """ingest path_inexistente --dry-run → exit 1, 'No existe la carpeta'."""
    result = runner.invoke(app, ["ingest", str(tmp_path / "no"), "--dry-run"])
    assert result.exit_code == 1
    assert "No existe la carpeta" in result.output


# ── Test 05: ok + roto ─────────────────────────────────────────────────


def test_05_mixed_ok_broken(tmp_path: Path) -> None:
    """ok.txt + roto.pdf → exit 1, ERROR roto.pdf, resumen 1 doc/1 pág/4 chars."""
    (tmp_path / "ok.txt").write_text("hola")
    (tmp_path / "roto.pdf").write_bytes(b"no soy un pdf")
    result = runner.invoke(app, ["ingest", str(tmp_path), "--dry-run"])
    assert result.exit_code == 1
    assert "ERROR roto.pdf: FileDataError" in result.output
    assert "1 documentos, 1 páginas, 4 caracteres" in result.output


# ── Test 06: default documents_dir ─────────────────────────────────────


def test_06_default_documents_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Sin carpeta pero DOCUCHAT_DOCUMENTS_DIR=SAMPLES → 7 documentos."""
    monkeypatch.setenv("DOCUCHAT_DOCUMENTS_DIR", str(SAMPLES))
    get_settings.cache_clear()
    result = runner.invoke(app, ["ingest", "--dry-run"])
    get_settings.cache_clear()
    assert result.exit_code == 0
    assert "7 documentos" in result.output


# ── Test 07: summary_line vacío ────────────────────────────────────────


def test_07_summary_line_empty() -> None:
    """summary_line(IngestResult()) → '0 documentos, 0 páginas, 0 caracteres'."""
    assert summary_line(IngestResult()) == "0 documentos, 0 páginas, 0 caracteres"


# ── Test 08: build_table dos páginas ───────────────────────────────────


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


# ── Test 09: index samples ─────────────────────────────────────────────


def test_09_index_samples(index_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    assert "7 añadidos, 0 actualizados, 0 sin cambios, 0 eliminados, 0 con errores" in result.output
    assert "Chunks en el índice: 26" in result.output
    assert (index_env / "registry.sqlite3").exists()


# ── Test 10: segunda pasada sin cambios ─────────────────────────────────


def test_10_second_run_unchanged(index_env: Path) -> None:
    runner.invoke(app, ["ingest", str(SAMPLES)])
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    assert "0 añadidos, 0 actualizados, 7 sin cambios" in result.output
    assert "Chunks en el índice: 26" in result.output


# ── Test 11: reset ─────────────────────────────────────────────────────


def test_11_reset(index_env: Path) -> None:
    runner.invoke(app, ["ingest", str(SAMPLES)])
    result = runner.invoke(app, ["ingest", str(SAMPLES), "--reset"])
    assert result.exit_code == 0
    assert "Índice borrado." in result.output
    assert "7 añadidos" in result.output
    assert "Chunks en el índice: 26" in result.output


# ── Test 12: model mismatch ────────────────────────────────────────────


def test_12_model_mismatch(index_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["ingest", str(SAMPLES)])
    monkeypatch.setenv("DOCUCHAT_EMBEDDING_MODEL", "otro")
    get_settings.cache_clear()
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 1
    assert "Reindexa con --reset" in result.output
    # Con --reset debería funcionar
    result2 = runner.invoke(app, ["ingest", str(SAMPLES), "--reset"])
    assert result2.exit_code == 0
    assert "7 añadidos" in result2.output


# ── Test 13: embedding error ───────────────────────────────────────────


def test_13_embedding_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "docuchat.cli.build_indexer",
        lambda s: indexer_mod.build_indexer(s, embedder=FakeEmbedder(fail_on="")),
    )
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 1
    assert "Error con el servidor de embeddings: APIConnectionError" in result.output
    assert isinstance(result.exception, SystemExit)


# ── Test 14: archivo roto ──────────────────────────────────────────────


def test_14_broken_file(index_env: Path, tmp_path: Path) -> None:
    d = tmp_path / "mixed"
    d.mkdir()
    (d / "ok.txt").write_text("Hola.")
    (d / "roto.pdf").write_bytes(b"no es un pdf")
    result = runner.invoke(app, ["ingest", str(d)])
    assert result.exit_code == 1
    assert "1 añadidos" in result.output
    assert "1 con errores" in result.output
    assert "ERROR roto.pdf" in result.output


# ── Test 15: archivo eliminado ─────────────────────────────────────────


def test_15_removed(index_env: Path, tmp_path: Path) -> None:
    d = tmp_path / "sub"
    d.mkdir()
    (d / "a.txt").write_text("A.")
    (d / "b.txt").write_text("B.")
    runner.invoke(app, ["ingest", str(d)])
    (d / "b.txt").unlink()
    result = runner.invoke(app, ["ingest", str(d)])
    assert result.exit_code == 0
    assert "1 eliminados" in result.output
    assert "Chunks en el índice: 1" in result.output


# ── Test 16: dry-run ignora reset ──────────────────────────────────────


def test_16_dry_run_ignores_reset(index_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES), "--dry-run", "--reset"])
    assert result.exit_code == 0
    assert "7 documentos, 22 páginas" in result.output
    assert "Índice borrado." not in result.output


# ── Test 17: stats_line ────────────────────────────────────────────────


def test_17_stats_line() -> None:
    s = stats_line(IndexStats(added=["a"], unchanged=["b", "c"], errors=[("d", "x")]))
    assert s == "1 añadidos, 0 actualizados, 2 sin cambios, 0 eliminados, 1 con errores"
