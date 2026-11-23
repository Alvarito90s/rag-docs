"""Tests de la ruta web: GET /, estáticos y verificación de copias exactas."""

import threading
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[2]

ASSETS_056 = PROJECT / "tasks" / "assets" / "056"
ASSETS_057 = PROJECT / "tasks" / "assets" / "057"

DESTINOS_056 = {
    "app.js": PROJECT / "src" / "docuchat" / "api" / "static" / "app.js",
    "style.css": PROJECT / "src" / "docuchat" / "api" / "static" / "style.css",
    "base.html": PROJECT / "src" / "docuchat" / "api" / "templates" / "base.html",
    "index.html": PROJECT / "src" / "docuchat" / "api" / "templates" / "index.html",
}


@pytest.mark.usefixtures("ingested")
def test_index_con_índice(client, services: object):
    """Con documentos indexados: 200, contiene conteo y nombre del modelo."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    html = resp.text
    chunks = services.searcher.size()
    assert f"{chunks} fragmentos indexados" in html
    assert "Qwen3.6-35B-A3B-6bit" in html
    assert "El índice está vacío" not in html


def test_index_vacío(client):
    """Con índice vacío: 200, contiene mensaje y estructura HTML."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    html = resp.text
    assert 'id="ask-form"' in html
    assert 'id="answer"' in html
    assert 'id="sources"' in html
    assert "static/app.js" in html
    assert "static/style.css" in html
    assert "El índice está vacío" in html


def test_static_app_js(client):
    """GET /static/app.js → 200 y contiene referencias esperadas."""
    resp = client.get("/static/app.js")
    assert resp.status_code == 200
    text = resp.text
    assert "/api/ask" in text
    assert "getReader" in text
    assert "linkCitations" in text


def test_static_style_css(client):
    """GET /static/style.css → 200 y contiene prefers-color-scheme."""
    resp = client.get("/static/style.css")
    assert resp.status_code == 200
    assert "prefers-color-scheme" in resp.text


def test_copias_exactas():
    """Los archivos copiados de la 056 son idénticos a los de tasks/assets/056/."""
    for nombre, destino in DESTINOS_056.items():
        assert (ASSETS_056 / nombre).read_bytes() == destino.read_bytes(), (
            f"{nombre} difiere del origen"
        )


def test_documents_page_vacía(client):
    """GET /documents con índice vacío → 200; contiene mensaje y HTMX."""
    resp = client.get("/documents")
    assert resp.status_code == 200
    html = resp.text
    assert "No hay documentos indexados" in html
    assert 'hx-post="/ui/ingest"' in html
    assert "static/vendor/htmx.min.js" in html


@pytest.mark.usefixtures("ingested")
def test_documents_page_con_índice(client, services: object):
    """Con documentos indexados: 7 enlaces a /files/, nombre del PDF, resumen."""
    resp = client.get("/documents")
    assert resp.status_code == 200
    html = resp.text
    assert html.count('href="/files/') == 7
    assert 'href="/files/manual_cafetera.pdf"' in html
    assert "7 añadidos" in html


def test_ui_ingest_con_block(client, services: object):
    """POST /ui/ingest bloquea: 200, job creado, HTMX polling; segundo POST → error."""
    services.embedder.block = threading.Event()

    resp = client.post("/ui/ingest")
    assert resp.status_code == 200
    job = services.jobs.latest()
    assert job is not None
    assert job.status == "running"
    html = resp.text
    assert 'hx-trigger="every 1s"' in html
    assert f'hx-get="/ui/ingest/{job.id}"' in html

    # Segundo POST debería dar error
    resp2 = client.post("/ui/ingest")
    assert resp2.status_code == 200
    assert "Ya hay una ingesta en marcha" in resp2.text

    # Liberar y esperar
    services.embedder.block.set()
    services.jobs.wait(job.id)


def test_ui_ingest_status_done(client, services: object):
    """Tras una ingesta terminada: GET /ui/ingest/{id} → 200, contiene resumen, hx-refresh."""
    # Lanzar ingesta directamente para asegurar estado final
    services.jobs.start()
    job = services.jobs.wait(services.jobs.latest().id)
    assert job.status == "done"

    resp = client.get(f"/ui/ingest/{job.id}")
    assert resp.status_code == 200
    assert "7 añadidos" in resp.text
    assert resp.headers.get("hx-refresh") == "true"


def test_ui_ingest_status_running(client, services: object):
    """Mientras corre: GET /ui/ingest/{id} sin hx-refresh; al terminar, con hx-refresh."""
    services.embedder.block = threading.Event()
    client.post("/ui/ingest")
    job = services.jobs.latest()
    assert job is not None

    resp_status = client.get(f"/ui/ingest/{job.id}")
    assert resp_status.status_code == 200
    assert "hx-refresh" not in resp_status.headers

    services.embedder.block.set()
    services.jobs.wait(job.id)

    resp_status2 = client.get(f"/ui/ingest/{job.id}")
    assert resp_status2.headers.get("hx-refresh") == "true"


def test_ui_ingest_status_404(client):
    """GET /ui/ingest/nada → 404."""
    resp = client.get("/ui/ingest/nada")
    assert resp.status_code == 404


def test_ui_ingest_reset(client, services: object):
    """POST /ui/ingest?reset=true → latest().reset es True; esperar a terminar."""
    resp = client.post("/ui/ingest?reset=true")
    assert resp.status_code == 200
    job = services.jobs.latest()
    assert job.reset is True

    services.jobs.wait(job.id)


def test_htmx_local():
    """htmx.min.js existe, pesa >10000 bytes y se sirve con 200."""
    path = PROJECT / "src" / "docuchat" / "api" / "static" / "vendor" / "htmx.min.js"
    assert path.exists()
    assert path.stat().st_size > 10_000


@pytest.mark.usefixtures("ingested")
def test_htmx_serve(client):
    """GET /static/vendor/htmx.min.js → 200."""
    resp = client.get("/static/vendor/htmx.min.js")
    assert resp.status_code == 200


def test_copias_exactas_057():
    """Los archivos copiados (no htmx) son idénticos a los de tasks/assets/057/."""
    for nombre in ("documents.html", "_job.html"):
        destino = PROJECT / "src" / "docuchat" / "api" / "templates" / nombre
        assert (ASSETS_057 / nombre).read_bytes() == destino.read_bytes(), (
            f"{nombre} difiere del origen"
        )
