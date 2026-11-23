"""Tests para reranker.py (HttpReranker, make_reranker)."""

import json
from pathlib import Path

import httpx
import pytest

from docuchat.config import Settings
from docuchat.retrieval.reranker import (
    HttpReranker,
    RerankError,
    make_reranker,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "rerank_response.json"


def make(handler, *, instruction: str = "I", max_retries: int = 0) -> HttpReranker:
    client = httpx.Client(base_url="http://test/v1", transport=httpx.MockTransport(handler))
    return HttpReranker(client, "m", instruction=instruction, max_retries=max_retries)


# 1. test_orden_de_entrada
def test_orden_de_entrada():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "results": [
                    {"index": 1, "relevance_score": 0.9},
                    {"index": 0, "relevance_score": 0.2},
                ]
            },
        )

    result = make(handler).rerank("q", ["a", "b"])
    assert result == [0.2, 0.9]


# 2. test_peticion
def test_peticion():
    saved: httpx.Request | None = None

    def handler(request):
        nonlocal saved
        saved = request
        return httpx.Response(
            200,
            json={
                "results": [
                    {"index": 0, "relevance_score": 0.5},
                    {"index": 1, "relevance_score": 0.6},
                ]
            },
        )

    make(handler).rerank("q", ["a", "b"])

    assert saved is not None
    assert saved.method == "POST"
    assert str(saved.url) == "http://test/v1/rerank"
    body = json.loads(saved.content)
    assert body == {
        "model": "m",
        "query": "q",
        "documents": ["a", "b"],
        "instruction": "I",
        "return_documents": False,
    }


# 3. test_sin_instruccion
def test_sin_instruccion():
    saved: dict | None = None

    def handler(request):
        nonlocal saved
        saved = json.loads(request.content)
        return httpx.Response(200, json={"results": [{"index": 0, "relevance_score": 0.5}]})

    make(handler, instruction="").rerank("q", ["a"])
    assert "instruction" not in saved


# 4. test_lista_vacia
def test_lista_vacia():
    called = False

    def handler(request):
        nonlocal called
        called = True
        return httpx.Response(200, json={"results": []})

    result = make(handler).rerank("q", [])
    assert result == []
    assert not called


# 5. test_error_http
def test_error_http():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(401, text="API key required")

    with pytest.raises(RerankError, match=r"^El reranker respondió 401"):
        make(handler).rerank("q", ["a"])

    assert call_count == 1


# 6. test_no_json
def test_no_json():
    def handler(request):
        return httpx.Response(200, text="hola")

    with pytest.raises(RerankError, match="La respuesta del reranker no es JSON"):
        make(handler).rerank("q", ["a"])


# 7. test_falta_puntuacion
def test_falta_puntuacion():
    def handler(request):
        return httpx.Response(
            200,
            json={"results": [{"index": 0, "relevance_score": 0.5}]},
        )

    with pytest.raises(RerankError, match=r"Se esperaban 2 puntuaciones y llegaron 1"):
        make(handler).rerank("q", ["a", "b"])


# 8. test_resultado_invalido
@pytest.mark.parametrize(
    "results",
    [
        [{"index": 5, "relevance_score": 0.1}, {"index": 0, "relevance_score": 0.2}],
        [{"index": 0, "relevance_score": 0.1}, {"index": 0, "relevance_score": 0.2}],
        [{"index": 0, "relevance_score": "alto"}, {"index": 1, "relevance_score": 0.2}],
        {"no": "lista"},
    ],
)
def test_resultado_invalido(results):
    def handler(request):
        return httpx.Response(200, json={"results": results})

    with pytest.raises(
        RerankError,
        match="Resultado de rerank inválido|Índice repetido"
        "|La respuesta del reranker no tiene 'results'",
    ):
        make(handler).rerank("q", ["a", "b"])


# 9. test_reintenta_conexion
def test_reintenta_conexion():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(
            200,
            json={
                "results": [
                    {"index": 0, "relevance_score": 0.7},
                    {"index": 1, "relevance_score": 0.3},
                ]
            },
        )

    result = make(handler, max_retries=1).rerank("q", ["a", "b"])
    assert result == [0.7, 0.3]
    assert call_count == 2


# 10. test_agota_reintentos
def test_agota_reintentos():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        raise httpx.ConnectError("boom", request=request)

    with pytest.raises(RerankError, match=r"^Error de conexión con el reranker: ConnectError"):
        make(handler, max_retries=2).rerank("q", ["a"])

    assert call_count == 3


# 11. test_respuesta_real_de_omlx
def test_respuesta_real_de_omlx():
    def handler(request):
        return httpx.Response(
            200,
            content=FIXTURE.read_bytes(),
            headers={"content-type": "application/json"},
        )

    result = make(handler).rerank(
        "¿Cuánto dura la garantía?",
        ["La garantía es de 2 años.", "El envío es gratuito."],
    )

    assert len(result) == 2
    assert result[0] > result[1]


# 12. test_no_reintenta_otros_errores
def test_no_reintenta_otros_errores():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        raise ValueError("bug")

    with pytest.raises(ValueError, match="bug"):
        make(handler, max_retries=2).rerank("q", ["a"])

    assert call_count == 1


# 13. test_elemento_no_dict
def test_elemento_no_dict():
    def handler(request):
        return httpx.Response(
            200,
            json={"results": [1, 2]},
        )

    with pytest.raises(RerankError, match=r"^Resultado de rerank inválido: 1"):
        make(handler).rerank("q", ["a", "b"])


# 14. test_make_reranker
def test_make_reranker(settings: Settings):
    saved: httpx.Request | None = None

    def handler(request):
        nonlocal saved
        saved = request
        return httpx.Response(200, json={"results": [{"index": 0, "relevance_score": 1.0}]})

    r = make_reranker(
        Settings(
            rerank_base_url="http://rr/v1",
            rerank_model="R",
            llm_api_key="k",
        ),
        transport=httpx.MockTransport(handler),
    )

    assert r.model == "R"
    r.rerank("q", ["a"])

    assert saved is not None
    assert str(saved.url) == "http://rr/v1/rerank"
    assert saved.headers["authorization"] == "Bearer k"
