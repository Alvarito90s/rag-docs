import types
from unittest.mock import MagicMock, patch

import httpx
import pytest
from openai import APIConnectionError

from docuchat.config import Settings, get_settings
from docuchat.env_check import (
    CheckResult,
    check_chat,
    check_embedding,
    check_model_listed,
    format_result,
    main,
    make_client,
    model_available,
    run_checks,
)


@pytest.fixture(autouse=True)
def _clear_env(tmp_path, monkeypatch):
    import os

    get_settings.cache_clear()
    for key in list(os.environ.keys()):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key)
    monkeypatch.chdir(tmp_path)
    yield
    get_settings.cache_clear()


# --- model_available ---


@pytest.mark.parametrize(
    "wanted,available,expected",
    [
        ("Qwen3.6-35B-A3B-6bit", ["Qwen3.6-35B-A3B-6bit", "Qwen3.5-4B-8bit"], True),
        ("Qwen3.6-35B-A3B-6bit", ["Qwen3.5-4B-8bit"], False),
        ("qwen3.6-35b-a3b-6bit", ["Qwen3.6-35B-A3B-6bit"], False),
        ("Qwen3.6-35B-A3B-6bit", [], False),
    ],
)
def test_model_available(wanted, available, expected) -> None:
    assert model_available(wanted, available) is expected


# --- check_model_listed ---


def test_check_model_listed_found() -> None:
    client = MagicMock()
    client.models.list.return_value = [types.SimpleNamespace(id="Qwen3.6-35B-A3B-6bit")]
    result = check_model_listed(client, "Qwen3.6-35B-A3B-6bit", "llm_model")
    assert result.ok is True
    assert result.detail == "Qwen3.6-35B-A3B-6bit disponible"


def test_check_model_listed_not_found() -> None:
    client = MagicMock()
    client.models.list.return_value = [types.SimpleNamespace(id="Qwen3.6-35B-A3B-6bit")]
    result = check_model_listed(client, "Qwen3-Embedding-0.6B-4bit-DWQ", "embedding_model")
    assert result.ok is False
    assert "Qwen3.6-35B-A3B-6bit" in result.detail


def test_check_model_listed_empty_list() -> None:
    client = MagicMock()
    client.models.list.return_value = []
    result = check_model_listed(client, "algún-modelo", "test_model")
    assert result.ok is False
    assert result.detail.endswith("disponibles: ninguno")


def test_check_model_listed_api_error() -> None:
    client = MagicMock()
    err = APIConnectionError(
        request=httpx.Request("GET", "http://test"),
    )
    client.models.list.side_effect = err
    result = check_model_listed(client, "modelo", "test")
    assert result.ok is False
    assert result.detail.startswith("APIConnectionError")


# --- check_embedding ---


def test_check_embedding_ok() -> None:
    client = MagicMock()
    client.embeddings.create.return_value = types.SimpleNamespace(
        data=[types.SimpleNamespace(embedding=[0.1] * 1024)]
    )
    result = check_embedding(client, "Qwen3-Embedding-0.6B-4bit-DWQ")
    assert result.ok is True
    assert result.detail == "dim=1024"
    client.embeddings.create.assert_called_once_with(
        model="Qwen3-Embedding-0.6B-4bit-DWQ",
        input=["prueba de embeddings"],
    )


def test_check_embedding_empty_data() -> None:
    client = MagicMock()
    client.embeddings.create.return_value = types.SimpleNamespace(data=[])
    result = check_embedding(client, "modelo")
    assert result.ok is False
    assert result.detail == "respuesta vacía"


def test_check_embedding_empty_vector() -> None:
    client = MagicMock()
    client.embeddings.create.return_value = types.SimpleNamespace(
        data=[types.SimpleNamespace(embedding=[])]
    )
    result = check_embedding(client, "modelo")
    assert result.ok is False
    assert result.detail == "respuesta vacía"


def test_check_embedding_api_error() -> None:
    client = MagicMock()
    err = APIConnectionError(
        request=httpx.Request("POST", "http://test"),
    )
    client.embeddings.create.side_effect = err
    result = check_embedding(client, "modelo")
    assert result.ok is False


# --- check_chat ---


def test_check_chat_ok() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="OK"))]
    )
    result = check_chat(client, "modelo")
    assert result.ok is True
    assert result.detail.startswith("respuesta en ")


def test_check_chat_empty() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = types.SimpleNamespace(choices=[])
    result = check_chat(client, "modelo")
    assert result.ok is False


def test_check_chat_api_error() -> None:
    client = MagicMock()
    err = APIConnectionError(
        request=httpx.Request("POST", "http://test"),
    )
    client.chat.completions.create.side_effect = err
    result = check_chat(client, "modelo")
    assert result.ok is False


# --- run_checks ---


def test_run_checks_all_ok() -> None:
    llm_client = MagicMock()
    emb_client = MagicMock()
    llm_client.models.list.return_value = [types.SimpleNamespace(id="Qwen3.6-35B-A3B-6bit")]
    emb_client.models.list.return_value = [
        types.SimpleNamespace(id="Qwen3-Embedding-0.6B-4bit-DWQ")
    ]
    emb_client.embeddings.create.return_value = types.SimpleNamespace(
        data=[types.SimpleNamespace(embedding=[0.1] * 100)]
    )
    llm_client.chat.completions.create.return_value = types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="OK"))]
    )
    results = run_checks(Settings(rerank_enabled=False), llm_client, emb_client)
    names = [r.name for r in results]
    assert names == ["llm_model", "embedding_model", "embedding", "chat"]
    assert all(r.ok for r in results)


def test_run_checks_partial_failure() -> None:
    llm_client = MagicMock()
    emb_client = MagicMock()
    err = APIConnectionError(
        request=httpx.Request("GET", "http://test"),
    )
    llm_client.models.list.side_effect = err
    emb_client.models.list.return_value = []
    emb_client.embeddings.create.return_value = types.SimpleNamespace(
        data=[types.SimpleNamespace(embedding=[0.1])]
    )
    llm_client.chat.completions.create.return_value = types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="OK"))]
    )
    results = run_checks(Settings(rerank_enabled=False), llm_client, emb_client)
    assert len(results) == 4
    assert results[0].ok is False


# --- format_result ---


def test_format_result_ok() -> None:
    assert format_result(CheckResult("chat", True, "x")) == "[OK] chat: x"


def test_format_result_fail() -> None:
    assert format_result(CheckResult("chat", False, "x")) == "[FAIL] chat: x"


# --- main ---


def test_main_all_ok(capsys) -> None:
    with patch("docuchat.env_check.run_checks") as mocked:
        mocked.return_value = [CheckResult("a", True, "x")]
        with patch("docuchat.env_check.make_client") as mc:
            mc.return_value = MagicMock()
            get_settings.cache_clear()
            assert main() == 0
    captured = capsys.readouterr()
    assert "Entorno listo." in captured.out


def test_main_partial_fail(capsys) -> None:
    with patch("docuchat.env_check.run_checks") as mocked:
        mocked.return_value = [
            CheckResult("a", True, "x"),
            CheckResult("b", False, "y"),
        ]
        with patch("docuchat.env_check.make_client") as mc:
            mc.return_value = MagicMock()
            get_settings.cache_clear()
            assert main() == 1
    captured = capsys.readouterr()
    assert "Hay comprobaciones fallidas." in captured.out


def test_main_warning_empty_key(capsys, monkeypatch) -> None:
    import os

    if "DOCUCHAT_LLM_API_KEY" in os.environ:
        monkeypatch.delenv("DOCUCHAT_LLM_API_KEY")
    with patch("docuchat.env_check.run_checks") as mocked:
        mocked.return_value = [CheckResult("a", True, "x")]
        with patch("docuchat.env_check.make_client") as mc:
            mc.return_value = MagicMock()
            get_settings.cache_clear()
            main()
    captured = capsys.readouterr()
    assert "Aviso: DOCUCHAT_LLM_API_KEY está vacía" in captured.out


def test_main_no_warning_when_key_set(capsys, monkeypatch) -> None:
    monkeypatch.setenv("DOCUCHAT_LLM_API_KEY", "x")
    with patch("docuchat.env_check.run_checks") as mocked:
        mocked.return_value = [CheckResult("a", True, "x")]
        with patch("docuchat.env_check.make_client") as mc:
            mc.return_value = MagicMock()
            get_settings.cache_clear()
            main()
    captured = capsys.readouterr()
    assert "Aviso: DOCUCHAT_LLM_API_KEY está vacía" not in captured.out


# --- make_client con clave vacía ---


def test_make_client_empty_key(monkeypatch) -> None:
    """make_client(Settings()) no lanza y client.api_key == 'sin-clave'."""
    monkeypatch.delenv("DOCUCHAT_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = make_client("http://127.0.0.1:9/v1", Settings())
    assert client.api_key == "sin-clave"


def test_make_client_with_key(monkeypatch) -> None:
    """DOCUCHAT_LLM_API_KEY=abc → client.api_key == 'abc'."""
    monkeypatch.setenv("DOCUCHAT_LLM_API_KEY", "abc")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = make_client("http://127.0.0.1:9/v1", Settings())
    assert client.api_key == "abc"
