"""13 tests obligatorios: /api/search y /api/ingest."""

import threading

import pytest
from starlette.testclient import TestClient

from docuchat.api.app import create_app
from docuchat.config import Settings
from tests.api.conftest import FakeEmbedder


class TestSearch:
    """Tests del endpoint POST /api/search."""

    def test_search_bm25_manual_cafetera(
        self, ingested: TestClient, api_settings: Settings
    ) -> None:
        """POST /api/search {"query": "E-17", "mode": "bm25"} → primer resultado coherente."""
        resp = ingested.post(
            "/api/search",
            json={"query": "E-17", "mode": "bm25"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) > 0

        first = results[0]
        assert first["source"] == "manual_cafetera.pdf"
        assert first["page"] == 7
        assert first["rank"] == 1
        assert first["bm25_rank"] == 1
        assert first["vector_rank"] is None
        assert first["url"] == "/files/manual_cafetera.pdf#page=7"
        assert "código de error E-17" in first["text"]

    def test_search_top_k_limit(self, ingested: TestClient) -> None:
        """{"query": "garantía", "top_k": 2} → 2 resultados con rank [1, 2]."""
        resp = ingested.post(
            "/api/search",
            json={"query": "garantía", "top_k": 2},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 2
        assert [r["rank"] for r in results] == [1, 2]

    def test_search_default_top_k(self, ingested: TestClient) -> None:
        """Sin top_k → como mucho 5 resultados."""
        resp = ingested.post(
            "/api/search",
            json={"query": "garantía"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) <= 5

    def test_search_empty_index(self, client: TestClient) -> None:
        """Índice vacío → 200 y []."""
        resp = client.post("/api/search", json={"query": "E-17"})
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.parametrize(
        "body",
        [
            {"query": ""},
            {"query": "x", "top_k": 0},
            {"query": "x", "mode": "otro"},
        ],
    )
    def test_search_validation(self, client: TestClient, body: dict) -> None:
        """Validación → 422."""
        resp = client.post("/api/search", json=body)
        assert resp.status_code == 422


class TestSearchEmbeddingError:
    """Tests del endpoint POST /api/search con error de embeddings."""

    def test_search_embedding_error(self, api_settings: Settings) -> None:
        """embedder.fail_on_query = True → 502 y detail con APIConnectionError."""
        embedder = FakeEmbedder()
        embedder.fail_on_query = True
        app = create_app(api_settings, embedder=embedder)
        client = TestClient(app)

        # Necesitamos al menos un chunk para que el searcher intente embedder
        # Pero el searcher solo llama a embed cuando hay chunks → creamos ingesta vacía
        # con FakeEmbedder y añadimos directamente algunos chunks al store
        from docuchat.index.vector_store import VectorStore
        from docuchat.models import Chunk

        store = VectorStore(
            api_settings.chroma_dir,
            api_settings.chroma_collection,
            api_settings.embedding_model,
        )
        chunk = Chunk(
            chunk_id="test#p1#c0",
            source="test.pdf",
            doc_sha256="a" * 64,
            page=1,
            position=0,
            text="E-17: código de error",
        )
        store.add([chunk], [[0.1, 0.2, 0.3]])

        resp = client.post(
            "/api/search",
            json={"query": "E-17", "mode": "vector"},
        )
        assert resp.status_code == 502
        assert "Error con el servidor de embeddings: APIConnectionError" in resp.json()["detail"]


class TestIngest:
    """Tests del endpoint POST /api/ingest y GET /api/ingest/{job_id}."""

    def test_ingest_no_body(
        self,
        client: TestClient,
        services,
        api_settings: Settings,
    ) -> None:
        """POST /api/ingest (sin cuerpo) → 202, status == "running", reset is False."""
        resp = client.post("/api/ingest")
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "running"
        assert data["reset"] is False

        job_id = data["id"]
        # Esperar a que termine
        services.jobs.wait(job_id)
        assert services.jobs.get(job_id).status == "done"

        # Consultar estado final
        resp = client.get(f"/api/ingest/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert data["stats"]["added"] == 7
        assert data["stats"]["chunks_added"] == 26

    def test_ingest_reset_true(self, client: TestClient, services) -> None:
        """POST /api/ingest {"reset": true} → 202 y reset is True."""
        resp = client.post("/api/ingest", json={"reset": True})
        assert resp.status_code == 202
        data = resp.json()
        assert data["reset"] is True

    def test_ingest_one_at_a_time(
        self,
        client: TestClient,
        services,
        api_settings: Settings,
    ) -> None:
        """Una a la vez: primer POST → 202; segundo → 409."""
        embedder: FakeEmbedder = services.embedder
        embedder.block = threading.Event()

        # Primer ingest → 202
        resp1 = client.post("/api/ingest", json={})
        assert resp1.status_code == 202
        job_id = resp1.json()["id"]

        # Segundo ingest → 409
        resp2 = client.post("/api/ingest", json={})
        assert resp2.status_code == 409
        assert resp2.json()["detail"] == "Ya hay una ingesta en marcha"

        # Liberar y esperar
        embedder.block.set()
        services.jobs.wait(job_id)
        assert services.jobs.get(job_id).status == "done"

    def test_ingest_unknown_id(self, client: TestClient) -> None:
        """GET /api/ingest/nada → 404 y detail == "Ingesta no encontrada"."""
        resp = client.get("/api/ingest/nada")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Ingesta no encontrada"


class TestSearchAfterApiIngest:
    """Tests de búsqueda tras una ingesta por API."""

    def test_search_after_ingest_api(
        self,
        api_settings: Settings,
    ) -> None:
        """Tras una ingesta por API, buscar "SKU-4471-B" encuentra glosario_interno.md."""
        embedder = FakeEmbedder()
        app = create_app(api_settings, embedder=embedder)
        client = TestClient(app)

        # Hacer ingesta por API
        resp = client.post("/api/ingest", json={})
        assert resp.status_code == 202
        job_id = resp.json()["id"]

        # Esperar
        from docuchat.api.app import Services

        services: Services = app.state.services
        services.jobs.wait(job_id)
        assert services.jobs.get(job_id).status == "done"

        # Ahora buscar
        resp = client.post(
            "/api/search",
            json={"query": "SKU-4471-B", "mode": "bm25"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) > 0
        sources = [r["source"] for r in results]
        assert "glosario_interno.md" in sources
