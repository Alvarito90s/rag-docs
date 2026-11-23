import os
import tomllib
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from docuchat.config import Settings, get_settings
from docuchat.env_check import CheckResult, main, run_checks


@pytest.fixture(autouse=True)
def _clear_env(tmp_path, monkeypatch):
    get_settings.cache_clear()
    for key in list(os.environ.keys()):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key)
    monkeypatch.chdir(tmp_path)
    yield
    get_settings.cache_clear()


# --- Settings defaults ---


def test_defaults() -> None:
    s = Settings()
    assert s.rerank_enabled is True
    assert s.rerank_base_url == "http://127.0.0.1:8000/v1"
    assert s.rerank_candidates == 10
    assert s.rerank_instruction == "Given a question, retrieve passages that answer the question"
    assert isinstance(s.rerank_model, str) and len(s.rerank_model) > 0


# --- Settings environment variables ---


def test_env(monkeypatch) -> None:
    monkeypatch.setenv("DOCUCHAT_RERANK_ENABLED", "true")
    monkeypatch.setenv("DOCUCHAT_RERANK_CANDIDATES", "30")
    s = Settings()
    assert s.rerank_enabled is True
    assert s.rerank_candidates == 30


# --- Settings validation ---


def test_candidates_menor_que_top_k() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(top_k=5, rerank_candidates=3)
    assert "rerank_candidates debe ser mayor o igual que top_k" in str(exc_info.value)


def test_candidates_cero() -> None:
    with pytest.raises(ValidationError):
        Settings(rerank_candidates=0)


# --- run_checks ---


def test_run_checks_rerank_apagado() -> None:
    llm = MagicMock()
    emb = MagicMock()
    rerank = MagicMock()
    llm.models.list.return_value = [types.SimpleNamespace(id="modelo")]
    emb.models.list.return_value = [types.SimpleNamespace(id="emb")]
    emb.embeddings.create.return_value = types.SimpleNamespace(
        data=[types.SimpleNamespace(embedding=[0.1] * 10)]
    )
    llm.chat.completions.create.return_value = types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="OK"))]
    )
    results = run_checks(Settings(rerank_enabled=False), llm, emb, rerank_client=rerank)
    assert len(results) == 4
    names = [r.name for r in results]
    assert names == ["llm_model", "embedding_model", "embedding", "chat"]


def test_run_checks_rerank_ok() -> None:
    settings = Settings(rerank_enabled=True, rerank_model="R")
    rerank = MagicMock()
    rerank.models.list.return_value = [types.SimpleNamespace(id="R")]
    results = run_checks(settings, MagicMock(), MagicMock(), rerank_client=rerank)
    assert len(results) == 5
    last = results[-1]
    assert last.name == "rerank_model"
    assert last.ok is True


def test_run_checks_rerank_no_listado() -> None:
    settings = Settings(rerank_enabled=True, rerank_model="R")
    rerank = MagicMock()
    rerank.models.list.return_value = [types.SimpleNamespace(id="otro")]
    results = run_checks(settings, MagicMock(), MagicMock(), rerank_client=rerank)
    last = results[-1]
    assert last.ok is False
    assert "no encontrado" in last.detail


def test_run_checks_rerank_sin_cliente() -> None:
    settings = Settings(rerank_enabled=True)
    results = run_checks(settings, MagicMock(), MagicMock(), rerank_client=None)
    last = results[-1]
    assert last == CheckResult("rerank_model", False, "sin cliente de rerank")


# --- main ---


def test_main_crea_cliente_rerank(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DOCUCHAT_RERANK_ENABLED", "true")
    monkeypatch.setenv("DOCUCHAT_RERANK_BASE_URL", "http://rr/v1")
    called_with: list[str] = []

    def fake(base_url, settings):
        called_with.append(base_url)
        return MagicMock()

    monkeypatch.setattr("docuchat.env_check.make_client", fake)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    main()
    assert "http://rr/v1" in called_with


# --- httpx dependency ---


def test_httpx_declarado() -> None:
    project_root = Path(__file__).resolve().parent.parent
    with open(project_root / "pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)
    deps = pyproject["project"]["dependencies"]
    assert any(dep.startswith("httpx") for dep in deps)
    __import__("httpx")
