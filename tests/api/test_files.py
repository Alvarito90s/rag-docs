"""7 tests obligatorios para /files/{source} y resolve_document."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient


def test_01_get_pdf(client: TestClient, ingested: TestClient) -> None:
    """GET /files/manual_cafetera.pdf → 200, PDF, sin content-disposition attachment."""
    resp = ingested.get("/files/manual_cafetera.pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
    cd = resp.headers.get("content-disposition", "")
    assert "attachment" not in cd


def test_02_get_md(client: TestClient, ingested: TestClient) -> None:
    """GET /files/apuntes_redes.md → 200 y 'Modelo OSI' en el texto."""
    resp = ingested.get("/files/apuntes_redes.md")
    assert resp.status_code == 200
    assert "Modelo OSI" in resp.text


def test_03_inexistent(client: TestClient, ingested: TestClient) -> None:
    """GET /files/nada.pdf → 404 y detail == 'Documento no encontrado'."""
    resp = ingested.get("/files/nada.pdf")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Documento no encontrado"


def test_04_path_traversal(client: TestClient, ingested: TestClient) -> None:
    """GET con ../ y %2E%2E → 404 (bloquea rutas fuera de la carpeta)."""
    resp1 = ingested.get("/files/../data/x.pdf")
    assert resp1.status_code == 404
    resp2 = ingested.get("/files/%2E%2E/%2E%2E/etc/passwd")
    assert resp2.status_code == 404


def test_05_unsupported_extension(
    client: TestClient,
    ingested: TestClient,
    tmp_path: Path,
) -> None:
    """GET /files/nota.exe → 404 (extensión no soportada)."""
    docs_dir = ingested.app.state.services.settings.documents_dir
    (docs_dir / "nota.exe").write_bytes(b"exe fake")
    resp = ingested.get("/files/nota.exe")
    assert resp.status_code == 404


def test_06_resolve_document(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """resolve_document: ruta fuera de root → None; archivo válido → Path resuelto."""
    from docuchat.api.routes_web import resolve_document

    # Fuera de root
    assert resolve_document(tmp_path, "../x.pdf") is None

    # Archivo válido
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF fake")
    result = resolve_document(tmp_path, "a.pdf")
    assert result == (tmp_path / "a.pdf").resolve()


def test_07_resolve_document_unsupported(tmp_path: Path) -> None:
    """resolve_document con extensión no soportada → None."""
    from docuchat.api.routes_web import resolve_document

    exe = tmp_path / "nota.exe"
    exe.write_bytes(b"exe")
    assert resolve_document(tmp_path, "nota.exe") is None
