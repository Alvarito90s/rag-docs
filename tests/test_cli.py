"""Tests obligatorios para la CLI, specs 015 y 027."""

import os
import re
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from openai import APIConnectionError
from typer.testing import CliRunner

from docuchat.cli import (
    app,
    build_table,
    format_result,
    format_sources,
    snippet,
    stats_line,
    summary_line,
)
from docuchat.config import get_settings
from docuchat.generation import answer as answer_mod
from docuchat.generation.citations import Source
from docuchat.generation.prompts import NO_ANSWER
from docuchat.index import indexer as indexer_mod
from docuchat.index.indexer import IndexStats
from docuchat.ingest.scanner import IngestResult
from docuchat.models import DocType, Document, Page
from docuchat.retrieval import searcher as searcher_mod

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


def test_13_embedding_error(cli_env: Path) -> None:
    """Parchea build_indexer con un FakeEmbedder que falla siempre."""
    from docuchat.index import indexer as indexer_mod

    class FailingEmbedder:
        def embed(self, texts):
            raise APIConnectionError(request=__import__("httpx").Request("POST", "http://test"))

    # Patch build_indexer con embedder que siempre falla
    import docuchat.cli as cli_mod

    def failing_bi(s):
        return indexer_mod.build_indexer(s, embedder=FailingEmbedder())

    cli_mod.build_indexer = failing_bi

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


# ── Fixture search_env ─────────────────────────────────────────────────


@pytest.fixture()
def search_env(index_env: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """index_env + build_searcher con FakeEmbedder."""
    monkeypatch.setattr(
        "docuchat.cli.build_searcher",
        lambda s: searcher_mod.build_searcher(s, embedder=FakeEmbedder()),
    )
    return index_env


# ── Fixture cli_env ────────────────────────────────────────────────────
# Patchea build_indexer Y build_searcher para tests que invocan ingest + search
# sin fixtures intermedios.


@pytest.fixture()
def cli_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    """Limpia env y patchea build_indexer + build_searcher con FakeEmbedder."""
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DOCUCHAT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(
        "docuchat.cli.build_indexer",
        lambda s: indexer_mod.build_indexer(s, embedder=FakeEmbedder()),
    )
    monkeypatch.setattr(
        "docuchat.cli.build_searcher",
        lambda s, embedder=None: searcher_mod.build_searcher(s, embedder=FakeEmbedder()),
    )
    get_settings.cache_clear()
    yield tmp_path / "data"
    get_settings.cache_clear()


# ── Test 18: search bm25 ───────────────────────────────────────────────


def test_18_search_bm25(cli_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    result = runner.invoke(app, ["search", "E-17", "--mode", "bm25"])
    assert result.exit_code == 0
    assert "[1] manual_cafetera.pdf · p. 7 · " in result.output
    assert "código de error E-17" in result.output


# ── Test 19: search top_k ──────────────────────────────────────────────


def test_19_search_top_k(cli_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    result = runner.invoke(app, ["search", "SKU-4471-B", "-k", "1", "--mode", "bm25"])
    assert result.exit_code == 0
    assert "[1] glosario_interno.md · p. 1" in result.output
    assert "(vec -, bm25 1)" in result.output
    assert "[2]" not in result.output


# ── Test 20: search hybrid default k ───────────────────────────────────


def test_20_search_hybrid_default_k(cli_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    result = runner.invoke(app, ["search", "garantía de la cafetera"])
    assert result.exit_code == 0
    assert "[5] " in result.output
    assert "[6] " not in result.output


# ── Test 21: search no results ─────────────────────────────────────────


def test_21_search_no_results(cli_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    result = runner.invoke(app, ["search", "zzzz", "--mode", "bm25"])
    assert result.exit_code == 0
    assert "Sin resultados." in result.output


# ── Test 22: search invalid mode ───────────────────────────────────────


def test_22_search_invalid_mode() -> None:
    result = runner.invoke(app, ["search", "hola", "--mode", "otro"])
    assert result.exit_code == 2


# ── Test 23: search embedding error ────────────────────────────────────


def test_23_search_embedding_error(cli_env: Path) -> None:
    """cli_env: indexa documentos y luego fuerza error de embedding en search."""
    import docuchat.retrieval.searcher as searcher_mod

    # Patch Searcher.search al nivel de la clase (afecta a todas las instancias)
    orig_search = searcher_mod.Searcher.search

    def failing_search(self, *args, **kwargs):
        raise APIConnectionError(request=__import__("httpx").Request("POST", "http://test"))

    searcher_mod.Searcher.search = failing_search

    try:
        # Primero indexar documentos
        result = runner.invoke(app, ["ingest", str(SAMPLES)])
        assert result.exit_code == 0
        # Luego buscar (debería fallar por embedding error)
        result = runner.invoke(app, ["search", "hola", "--mode", "bm25"])
        assert result.exit_code == 1
        assert "Error con el servidor de embeddings: APIConnectionError" in result.output
        assert isinstance(result.exception, SystemExit)
    finally:
        searcher_mod.Searcher.search = orig_search


# ── Test 24: search empty index ────────────────────────────────────────


def test_24_search_empty_index(search_env: Path) -> None:
    result = runner.invoke(app, ["search", "hola"])
    assert result.exit_code == 1
    assert "El índice está vacío" in result.output


# ── Test 25: search model mismatch ─────────────────────────────────────


def test_25_search_model_mismatch(search_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    monkeypatch.setenv("DOCUCHAT_EMBEDDING_MODEL", "otro")
    get_settings.cache_clear()
    result = runner.invoke(app, ["search", "hola"])
    assert result.exit_code == 1
    assert "Reindexa con --reset" in result.output


# ── Test 26: format_result ─────────────────────────────────────────────


def test_26_format_result() -> None:
    from docuchat.models import Chunk, SearchResult

    chunk = Chunk(
        chunk_id="a.pdf#p3#c0",
        source="a.pdf",
        doc_sha256="a" * 64,
        page=3,
        position=0,
        text="  Hola\n\nmundo  ",
    )
    result = SearchResult(
        chunk=chunk,
        rank=2,
        score=0.0327869,
        vector_rank=None,
        bm25_rank=1,
    )
    assert format_result(result) == "[2] a.pdf · p. 3 · 0.0328 (vec -, bm25 1)\n    Hola mundo"


# ── Test 27: snippet ───────────────────────────────────────────────────


def test_27_snippet() -> None:
    assert len(snippet("a " * 100)) == 150
    assert snippet("a " * 100).endswith("a…")
    assert snippet("corto") == "corto"
    assert snippet("abc def", width=4) == "abc…"
    assert snippet("abc def", width=5) == "abc d…"


# ── FakeChat (copia de tests/generation/test_answer.py) ─────────────────


class FakeChat:
    def __init__(self, pieces: list[str], fail: bool = False) -> None:
        self.pieces = pieces
        self.fail = fail
        self.calls: list[list] = []

    def stream(self, messages):
        self.calls.append(list(messages))
        if self.fail:
            raise APIConnectionError(request=__import__("httpx").Request("POST", "http://test"))
        yield from self.pieces


# ── Test 28: ask que responde ──────────────────────────────────────────


def test_28_ask_answer(search_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    chat = FakeChat(["El error E-17 ", "indica depósito vacío [1]."])
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "docuchat.cli.build_answerer",
        lambda s, retriever, top_k: answer_mod.build_answerer(
            s, retriever=retriever, chat=chat, top_k=top_k
        ),
    )
    try:
        result = runner.invoke(app, ["ask", "¿Qué es E-17?"])
        assert result.exit_code == 0
        assert "El error E-17 indica depósito vacío [1]." in result.output
        assert re.search(r"Fuentes:\n\[1\] \S+, p\. \d+", result.output)
        assert result.output.count("indica depósito vacío [1].") == 1

    finally:
        monkeypatch.undo()


# ── Test 29: ask con cita inválida ─────────────────────────────────────


def test_29_ask_invalid_citation(search_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    chat = FakeChat(["Dato [1][9]."])
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "docuchat.cli.build_answerer",
        lambda s, retriever, top_k: answer_mod.build_answerer(
            s, retriever=retriever, chat=chat, top_k=top_k
        ),
    )
    try:
        result = runner.invoke(app, ["ask", "¿Pregunta?"])
        assert result.exit_code == 0
        assert "Aviso: citas sin fuente descartadas: [9]" in result.output
    finally:
        monkeypatch.undo()


# ── Test 30: ask sin respuesta ─────────────────────────────────────────


def test_30_ask_no_answer(search_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    chat = FakeChat([NO_ANSWER])
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "docuchat.cli.build_answerer",
        lambda s, retriever, top_k: answer_mod.build_answerer(
            s, retriever=retriever, chat=chat, top_k=top_k
        ),
    )
    try:
        result = runner.invoke(app, ["ask", "¿Quién ganó el mundial de 2010?"])
        assert result.exit_code == 0
        assert NO_ANSWER in result.output
        assert "Fuentes:" not in result.output
    finally:
        monkeypatch.undo()


# ── Test 31: ask sin citas en la respuesta ─────────────────────────────


def test_31_ask_no_citations(search_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    chat = FakeChat(["Respuesta sin citas."])
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "docuchat.cli.build_answerer",
        lambda s, retriever, top_k: answer_mod.build_answerer(
            s, retriever=retriever, chat=chat, top_k=top_k
        ),
    )
    try:
        result = runner.invoke(app, ["ask", "¿Pregunta?"])
        assert result.exit_code == 0
        assert "Aviso: la respuesta no cita ninguna fuente." in result.output
        assert "Fuentes:" not in result.output
    finally:
        monkeypatch.undo()


# ── Test 32: ask con índice vacío ──────────────────────────────────────


def test_32_ask_empty_index(search_env: Path) -> None:
    result = runner.invoke(app, ["ask", "¿Pregunta?"])
    assert result.exit_code == 1
    assert "El índice está vacío" in result.output


# ── Test 33: ask error de LLM ──────────────────────────────────────────


def test_33_ask_llm_error(search_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    chat = FakeChat([], fail=True)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "docuchat.cli.build_answerer",
        lambda s, retriever, top_k: answer_mod.build_answerer(
            s, retriever=retriever, chat=chat, top_k=top_k
        ),
    )
    try:
        result = runner.invoke(app, ["ask", "¿Pregunta?"])
        assert result.exit_code == 1
        assert "Error con el servidor de modelos: APIConnectionError" in result.output
        assert isinstance(result.exception, SystemExit)
    finally:
        monkeypatch.undo()


# ── Test 34: ask con top_k ─────────────────────────────────────────────


def test_34_ask_top_k(search_env: Path) -> None:
    result = runner.invoke(app, ["ingest", str(SAMPLES)])
    assert result.exit_code == 0
    chat = FakeChat(["Ok [1]."])
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "docuchat.cli.build_answerer",
        lambda s, retriever, top_k: answer_mod.build_answerer(
            s, retriever=retriever, chat=chat, top_k=top_k
        ),
    )
    try:
        result = runner.invoke(app, ["ask", "hola", "-k", "2"])
        assert result.exit_code == 0
        content = chat.calls[0][1]["content"]
        assert "[2] " in content
        assert "[3] " not in content
    finally:
        monkeypatch.undo()


# ── Test 35: format_sources ────────────────────────────────────────────


def test_35_format_sources() -> None:
    result = format_sources([Source(1, "a.pdf", 3), Source(4, "b.md", 1)])
    assert result == ["[1] a.pdf, p. 3", "[4] b.md, p. 1"]
