"""8 tests obligatorios para los endpoints /api/health y /api/documents."""

from starlette.testclient import TestClient

from docuchat.api.app import create_app


class TestHealth:
    """Tests del endpoint /api/health."""

    def test_health_empty_index(self, client: TestClient, api_settings) -> None:
        """GET /api/health con índice vacío → 200 y valores iniciales."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {
            "status": "ok",
            "chunks": 0,
            "documents": 0,
            "llm_model": "Qwen3.6-35B-A3B-6bit",
            "embedding_model": "Qwen3-Embedding-0.6B-4bit-DWQ",
            "ingest_running": False,
        }

    def test_health_after_ingest(self, ingested: TestClient) -> None:
        """Con ingesta completada: chunks == 26, documents == 7."""
        resp = ingested.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chunks"] == 26
        assert data["documents"] == 7


class TestDocuments:
    """Tests del endpoint /api/documents."""

    def test_documents_empty(self, client: TestClient) -> None:
        """GET /api/documents con índice vacío → []."""
        resp = client.get("/api/documents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_documents_after_ingest(self, ingested: TestClient) -> None:
        """Con ingesta: 7 elementos ordenados por source, primeras claves correctas."""
        resp = ingested.get("/api/documents")
        assert resp.status_code == 200
        docs = resp.json()
        assert len(docs) == 7

        # Ordenados por source
        sources = [d["source"] for d in docs]
        assert sources == sorted(sources)

        # El primero
        assert docs[0]["source"] == "apuntes_redes.md"
        assert docs[0]["url"] == "/files/apuntes_redes.md"

        # Suma de chunks
        assert sum(d["chunks"] for d in docs) == 26

        # Claves obligatorias
        expected_keys = {"source", "chunks", "indexed_at", "url"}
        for doc in docs:
            assert set(doc.keys()) == expected_keys


class TestServicesReload:
    """Tests del rebuild de servicios."""

    def test_reload_after_ingest(self, ingested: TestClient, services) -> None:
        """reload tras ingesta: searcher es otro objeto, chunks == 26."""
        old = services.searcher
        services.jobs.start()
        services.jobs.wait(services.jobs.latest().id)
        assert services.jobs.latest().status == "done"
        assert services.searcher is not old
        assert services.searcher.size() == 26

    def test_reset_rebuilds(self, ingested: TestClient, services) -> None:
        """Reset no rompe el buscador: tras reset+reingest, health chunks == 26."""
        services.jobs.wait(services.jobs.start(reset=True).id)
        assert services.jobs.latest().status == "done"
        services.jobs.wait(services.jobs.start().id)
        assert services.jobs.latest().status == "done"

        resp = ingested.get("/api/health")
        assert resp.json()["chunks"] == 26


class TestFileUrl:
    """Tests de la función file_url."""

    def test_file_url_with_page(self) -> None:
        assert "file_url(" not in dir()
        from docuchat.api.routes_api import file_url

        result = file_url("sub dir/a.pdf", 3)
        assert result == "/files/sub%20dir/a.pdf#page=3"

    def test_file_url_without_page(self) -> None:
        from docuchat.api.routes_api import file_url

        result = file_url("a.md")
        assert result == "/files/a.md"


class TestAppCreation:
    """Tests de create_app sin embedder ni chat."""

    def test_app_without_embedder_or_chat(self, api_settings) -> None:
        """create_app sin embedder ni chat → no hace red al crearse."""
        app = create_app(api_settings)
        assert app.title == "DocuChat Local"

        from starlette.testclient import TestClient

        client = TestClient(app)
        resp = client.get("/api/health")
        assert resp.status_code == 200
