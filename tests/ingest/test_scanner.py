"""Tests obligatorios del scanner, spec 014-scanner.md."""

from pathlib import Path

import pytest

from docuchat.ingest.scanner import (
    UnsupportedFileError,
    file_sha256,
    load_document,
    load_folder,
    scan_folder,
)
from docuchat.models import DocType

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


# --- 1. test_01_scan_folder_samples ---


def test_01_scan_folder_samples() -> None:
    """scan_folder(SAMPLES) → nombres ordenados de los 7 archivos soportados."""
    files = scan_folder(SAMPLES)
    assert [p.name for p in files] == [
        "apuntes_redes.md",
        "contrato_servicios.pdf",
        "glosario_interno.md",
        "manual_cafetera.pdf",
        "notas_reunion.txt",
        "paper_rag_resumen.pdf",
        "politica_vacaciones.docx",
    ]


# --- 2. test_02_scan_folder_filters_hidden ---


def test_02_scan_folder_filters_hidden(tmp_path: Path) -> None:
    """Árbol con ocultos, ~$, no-soportados → solo a.MD, b.txt, sub/c.txt."""
    (tmp_path / "b.txt").write_text("x")
    (tmp_path / "a.MD").write_text("x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("x")
    (tmp_path / ".oculto").mkdir()
    (tmp_path / ".oculto" / "d.txt").write_text("x")
    (tmp_path / ".e.txt").write_text("x")
    (tmp_path / "~$f.docx").write_text("x")
    (tmp_path / "g.pptx").write_text("x")
    git = sub / ".git"
    git.mkdir()
    (git / "h.md").write_text("x")
    files = scan_folder(tmp_path)
    assert [p.relative_to(tmp_path).as_posix() for p in files] == [
        "a.MD",
        "b.txt",
        "sub/c.txt",
    ]


# --- 3. test_03_scan_folder_errors ---


def test_03_scan_folder_errors(tmp_path: Path) -> None:
    """scan_folder(path_inexistente) → FileNotFoundError; scan_folder(archivo) →
    NotADirectoryError."""
    with pytest.raises(FileNotFoundError):
        scan_folder(tmp_path / "no_existe")
    archivo = tmp_path / "f.txt"
    archivo.write_text("x")
    with pytest.raises(NotADirectoryError):
        scan_folder(archivo)


# --- 4. test_04_file_sha256_abc ---


def test_04_file_sha256_abc(tmp_path: Path) -> None:
    """file_sha256 de un archivo con b'abc' → hash esperado."""
    f = tmp_path / "abc.txt"
    f.write_bytes(b"abc")
    assert file_sha256(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


# --- 5. test_05_load_document_contract ---


def test_05_load_document_contract() -> None:
    """load_document(contrato, SAMPLES) → source, doc_type, page_count, path.is_absolute(),
    sha256."""
    doc = load_document(SAMPLES / "contrato_servicios.pdf", SAMPLES)
    assert doc.source == "contrato_servicios.pdf"
    assert doc.doc_type == DocType.PDF
    assert doc.page_count == 4
    assert doc.path.is_absolute()
    assert doc.sha256 == file_sha256(SAMPLES / "contrato_servicios.pdf")


# --- 6. test_06_load_document_subdir ---


def test_06_load_document_subdir(tmp_path: Path) -> None:
    """load_document(tmp/sub/c.txt, tmp) → source == 'sub/c.txt', doc_type TXT."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.txt").write_text("x")
    doc = load_document(tmp_path / "sub" / "c.txt", tmp_path)
    assert doc.source == "sub/c.txt"
    assert doc.doc_type == DocType.TXT


# --- 7. test_07_load_document_unsupported ---


def test_07_load_document_unsupported(tmp_path: Path) -> None:
    """load_document(g.pptx, tmp_path) → UnsupportedFileError."""
    (tmp_path / "g.pptx").write_text("x")
    with pytest.raises(UnsupportedFileError):
        load_document(tmp_path / "g.pptx", tmp_path)


# --- 8. test_08_load_folder_samples ---


def test_08_load_folder_samples() -> None:
    """load_folder(SAMPLES) → 7 docs, sin errors, page_count total 22."""
    result = load_folder(SAMPLES)
    assert len(result.documents) == 7
    assert result.errors == []
    total_pages = sum(doc.page_count for doc in result.documents)
    assert total_pages == 22
    assert [d.source for d in result.documents] == [
        "apuntes_redes.md",
        "contrato_servicios.pdf",
        "glosario_interno.md",
        "manual_cafetera.pdf",
        "notas_reunion.txt",
        "paper_rag_resumen.pdf",
        "politica_vacaciones.docx",
    ]


# --- 9. test_09_load_folder_mixed_ok_broken ---


def test_09_load_folder_mixed_ok_broken(tmp_path: Path) -> None:
    """ok.txt + roto.pdf → 1 doc, 1 error con FileDataError."""
    (tmp_path / "ok.txt").write_text("hola")
    (tmp_path / "roto.pdf").write_bytes(b"no soy un pdf")
    result = load_folder(tmp_path)
    assert len(result.documents) == 1
    assert result.documents[0].source == "ok.txt"
    assert len(result.errors) == 1
    assert result.errors[0][0] == "roto.pdf"
    assert result.errors[0][1].startswith("FileDataError")


# --- 10. test_10_load_folder_empty_file ---


def test_10_load_folder_empty_file(tmp_path: Path) -> None:
    """vacio.txt (' \\n') → 1 doc con page_count == 0."""
    (tmp_path / "vacio.txt").write_bytes(b" \n")
    result = load_folder(tmp_path)
    assert len(result.documents) == 1
    assert result.documents[0].page_count == 0
    assert result.errors == []


# --- 11. test_11_symlinked_root ---


def test_11_symlinked_root(tmp_path: Path) -> None:
    """load_folder(link) → sin errors, sources relativos correctos."""
    real = tmp_path / "real"
    real.mkdir()
    (real / "a.txt").write_text("hola")
    sub = real / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("adiós")
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    r = load_folder(link)
    assert r.errors == []
    assert [d.source for d in r.documents] == ["a.txt", "sub/b.txt"]


# --- 12. test_12_scan_keeps_given_root ---


def test_12_scan_keeps_given_root(tmp_path: Path) -> None:
    """scan_folder(link) → todas las rutas empiezan por 'link'."""
    real = tmp_path / "real"
    real.mkdir()
    (real / "a.txt").write_text("hola")
    sub = real / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("adiós")
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    files = scan_folder(link)
    for p in files:
        assert str(p).startswith(str(link))
