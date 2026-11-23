"""9 tests obligatorios para el endpoint POST /api/ask con streaming SSE."""

import json
from typing import Any

import pytest
from starlette.testclient import TestClient

from docuchat.api.app import Services
from docuchat.generation.prompts import NO_ANSWER


def parse_sse(body: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in body.strip().split("\n\n"):
        event, data = "message", ""
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[len("event: ") :]
            elif line.startswith("data: "):
                data += line[len("data: ") :]
        events.append((event, json.loads(data)))
    return events


class TestAskSuccess:
    """Test 1: respuesta normal con contexto."""

    def test_ask_with_context(
        self,
        ingested: TestClient,
        services: Services,
    ) -> None:
        resp = ingested.post("/api/ask", json={"question": "pregunta"})
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

        events = parse_sse(resp.text)
        assert events[0] == ("token", {"text": "Dato "})
        assert events[1] == ("token", {"text": "[1]."})
        assert events[2][0] == "done"

        done = events[2][1]
        assert done["text"] == "Dato [1]."
        assert done["no_answer"] is False
        assert done["invalid_citations"] == []
        assert len(done["sources"]) == 1
        assert done["sources"][0]["number"] == 1

        first = services.searcher.search("pregunta", 1)[0]
        assert done["sources"][0]["source"] == first.chunk.source
        assert done["sources"][0]["page"] == first.chunk.page
        assert done["sources"][0]["url"] == f"/files/{first.chunk.source}#page={first.chunk.page}"


class TestAskEmptyIndex:
    """Test 2: índice vacío → NO_ANSWER."""

    def test_ask_empty_index(self, client: TestClient, chat) -> None:
        resp = client.post("/api/ask", json={"question": "test"})
        events = parse_sse(resp.text)

        assert events[0] == ("token", {"text": NO_ANSWER})
        assert events[1][0] == "done"
        done = events[1][1]
        assert done["no_answer"] is True
        assert done["sources"] == []
        assert chat.calls == []


class TestAskNoAnswer:
    """Test 3: el modelo responde no_answer."""

    def test_ask_model_no_answer(self, ingested: TestClient, services: Services) -> None:
        services.chat.pieces = [NO_ANSWER]

        resp = ingested.post("/api/ask", json={"question": "test"})
        events = parse_sse(resp.text)

        # Buscar el evento done entre los eventos
        done_event = next(e for e in events if e[0] == "done")
        assert done_event[1]["no_answer"] is True
        assert done_event[1]["sources"] == []


class TestAskFakeCitation:
    """Test 4: cita inventada → invalid_citations."""

    def test_ask_fake_citation(self, ingested: TestClient, services: Services) -> None:
        services.chat.pieces = ["Dato [1][9]."]

        resp = ingested.post("/api/ask", json={"question": "test"})
        events = parse_sse(resp.text)

        assert events[0] == ("token", {"text": "Dato [1][9]."})
        assert events[1][0] == "done"
        done = events[1][1]
        assert done["invalid_citations"] == [9]


class TestAskLLMError:
    """Test 5: error del LLM → evento error."""

    def test_ask_llm_error(self, ingested: TestClient, services: Services) -> None:
        services.chat.fail = True

        resp = ingested.post("/api/ask", json={"question": "test"})
        assert resp.status_code == 200

        events = parse_sse(resp.text)
        assert len(events) == 1
        assert events[0][0] == "error"
        assert events[0][1]["message"].startswith("APIConnectionError")


class TestAskEmbeddingError:
    """Test 6: error de embeddings → evento error."""

    def test_ask_embedding_error(self, ingested: TestClient, services: Services) -> None:
        services.embedder.fail_on_query = True

        resp = ingested.post("/api/ask", json={"question": "test"})
        assert resp.status_code == 200

        events = parse_sse(resp.text)
        assert len(events) == 1
        assert events[0][0] == "error"


class TestAskTopK:
    """Test 7: top_k limita el contexto."""

    def test_ask_top_k(self, ingested: TestClient, services: Services) -> None:
        resp = ingested.post("/api/ask", json={"question": "hola", "top_k": 1})
        assert resp.status_code == 200

        _events = parse_sse(resp.text)

        user_content = services.chat.calls[0][1]["content"]
        assert "[1] " in user_content
        assert "[2] " not in user_content


class TestAskValidation:
    """Test 8: validación de parámetros (parametrizado, 2 casos)."""

    @pytest.mark.parametrize(
        "body",
        [
            {"question": ""},
            {"question": "x", "top_k": 0},
        ],
    )
    def test_ask_validation(self, client: TestClient, body: dict) -> None:
        resp = client.post("/api/ask", json=body)
        assert resp.status_code == 422


class TestAskUnexpectedError:
    """Test 7b: error inesperado al recuperar → evento error."""

    def test_ask_retrieve_error(
        self,
        ingested: TestClient,
        services: Services,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        def boom(question: str):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

        monkeypatch.setattr(services.answerer, "retrieve", boom)

        resp = ingested.post("/api/ask", json={"question": "test"})
        assert resp.status_code == 200

        events = parse_sse(resp.text)
        assert events == [("error", {"message": "RuntimeError: boom"})]

        assert caplog.record_tuples == [
            ("docuchat.api.routes_api", 40, "Fallo inesperado en /api/ask")
        ]


class TestAskMidStreamError:
    """Test 7c: error a mitad del stream → token + evento error."""

    def test_ask_mid_stream_error(
        self,
        ingested: TestClient,
        services: Services,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def cortado(question: str, context):  # type: ignore[no-untyped-def]
            yield "Hola"
            raise RuntimeError("corte")

        monkeypatch.setattr(services.answerer, "stream", cortado)

        resp = ingested.post("/api/ask", json={"question": "test"})
        assert resp.status_code == 200

        events = parse_sse(resp.text)
        assert events == [
            ("token", {"text": "Hola"}),
            ("error", {"message": "RuntimeError: corte"}),
        ]
