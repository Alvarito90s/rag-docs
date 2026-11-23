import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from docuchat.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_env_and_cache(tmp_path, monkeypatch):
    """Borra DOCUCHAT_* de os.environ, chdir a tmp_path y limpia el cache."""
    get_settings.cache_clear()
    for key in list(os.environ.keys()):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key)
    monkeypatch.chdir(tmp_path)
    yield
    get_settings.cache_clear()


# --- Defaults ---


def test_defaults() -> None:
    s = Settings()
    assert s.chunk_size == 800
    assert s.chunk_overlap == 120
    assert s.llm_model == "Qwen3.6-35B-A3B-6bit"
    assert s.embedding_model == "Qwen3-Embedding-0.6B-4bit-DWQ"
    assert s.llm_base_url == "http://127.0.0.1:8000/v1"
    assert s.llm_api_key == ""
    assert s.data_dir == Path("data")
    assert s.documents_dir == Path("samples")


# --- Env override ---


def test_env_override(monkeypatch) -> None:
    monkeypatch.setenv("DOCUCHAT_CHUNK_SIZE", "500")
    monkeypatch.setenv("DOCUCHAT_LLM_MODEL", "Qwen3.5-4B-8bit")
    s = Settings()
    assert s.chunk_size == 500
    assert s.llm_model == "Qwen3.5-4B-8bit"


# --- Dotenv ---


def test_env_path(monkeypatch) -> None:
    monkeypatch.setenv("DOCUCHAT_DATA_DIR", "/tmp/docuchat")
    assert Settings().data_dir == Path("/tmp/docuchat")


def test_dotenv_file(tmp_path) -> None:
    (tmp_path / ".env").write_text("DOCUCHAT_LLM_MODEL=desde-env\n", encoding="utf-8")
    assert Settings().llm_model == "desde-env"


def test_env_beats_dotenv(tmp_path, monkeypatch) -> None:
    (tmp_path / ".env").write_text("DOCUCHAT_LLM_MODEL=desde-env\n", encoding="utf-8")
    monkeypatch.setenv("DOCUCHAT_LLM_MODEL", "desde-os")
    assert Settings().llm_model == "desde-os"


# --- Validation ---


def test_overlap_not_smaller_than_size() -> None:
    with pytest.raises(ValidationError):
        Settings(chunk_size=100, chunk_overlap=100)


@pytest.mark.parametrize(
    "kwargs",
    [{"chunk_size": 0}, {"chunk_overlap": -1}, {"request_timeout": 0}],
)
def test_invalid_values(kwargs: dict) -> None:
    with pytest.raises(ValidationError):
        Settings(**kwargs)


def test_unknown_env_ignored(monkeypatch) -> None:
    monkeypatch.setenv("DOCUCHAT_FOO", "1")
    Settings()  # no debe fallar


# --- Index defaults ---


def test_index_defaults() -> None:
    s = Settings()
    assert s.embedding_batch_size == 32
    assert s.request_max_retries == 3
    assert s.chroma_collection == "chunks"


# --- Index env override ---


def test_index_env_override(monkeypatch) -> None:
    monkeypatch.setenv("DOCUCHAT_EMBEDDING_BATCH_SIZE", "8")
    s = Settings()
    assert s.embedding_batch_size == 8


# --- Derived paths ---


def test_derived_paths(monkeypatch) -> None:
    s = Settings()
    assert s.chroma_dir == Path("data/chroma")
    assert s.registry_path == Path("data/registry.sqlite3")
    monkeypatch.setenv("DOCUCHAT_DATA_DIR", "/tmp/x")
    s2 = Settings()
    assert s2.chroma_dir == Path("/tmp/x/chroma")


# --- Invalid index values ---


@pytest.mark.parametrize(
    "kwargs",
    [{"embedding_batch_size": 0}, {"request_max_retries": -1}],
)
def test_invalid_index_values(kwargs: dict) -> None:
    with pytest.raises(ValidationError):
        Settings(**kwargs)


# --- Cache ---


# --- Search defaults ---


def test_search_defaults() -> None:
    s = Settings()
    assert s.top_k == 5
    assert s.candidate_k == 20
    assert s.rrf_k == 60
    assert s.query_instruction == "Given a question, retrieve passages that answer the question"


# --- Search env override ---


def test_search_env_override(monkeypatch) -> None:
    monkeypatch.setenv("DOCUCHAT_TOP_K", "3")
    monkeypatch.setenv("DOCUCHAT_QUERY_INSTRUCTION", "")
    s = Settings()
    assert s.top_k == 3
    assert s.query_instruction == ""


# --- Search validation ---


def test_candidate_k_not_smaller_than_top_k() -> None:
    with pytest.raises(ValidationError):
        Settings(top_k=10, candidate_k=5)
    Settings(top_k=10, candidate_k=10)  # igual es válido


@pytest.mark.parametrize(
    "kwargs",
    [{"top_k": 0}, {"candidate_k": 0}, {"rrf_k": 0}],
)
def test_invalid_search_values(kwargs: dict) -> None:
    with pytest.raises(ValidationError):
        Settings(**kwargs)


# --- Generation defaults ---


def test_generation_defaults() -> None:
    s = Settings()
    assert s.llm_max_tokens == 1024
    assert s.llm_temperature == 0.2
    assert s.llm_thinking is False
    assert s.context_max_chars == 6000


# --- Generation env override ---


def test_generation_env_override(monkeypatch) -> None:
    monkeypatch.setenv("DOCUCHAT_LLM_THINKING", "true")
    monkeypatch.setenv("DOCUCHAT_LLM_TEMPERATURE", "0")
    s = Settings()
    assert s.llm_thinking is True
    assert s.llm_temperature == 0.0


# --- Generation validation ---


@pytest.mark.parametrize(
    "kwargs",
    [
        {"llm_max_tokens": 0},
        {"llm_temperature": -0.1},
        {"llm_temperature": 2.5},
        {"context_max_chars": 0},
    ],
)
def test_invalid_generation_values(kwargs: dict) -> None:
    with pytest.raises(ValidationError):
        Settings(**kwargs)


# --- Cache ---


# --- API defaults ---


def test_api_defaults() -> None:
    s = Settings()
    assert s.api_host == "127.0.0.1"
    assert s.api_port == 8001


# --- API env override ---


def test_api_env_override(monkeypatch) -> None:
    monkeypatch.setenv("DOCUCHAT_API_PORT", "9000")
    s = Settings()
    assert s.api_port == 9000


# --- API validation ---


@pytest.mark.parametrize(
    "kwargs",
    [{"api_port": 0}, {"api_port": 70000}],
)
def test_invalid_api_port(kwargs: dict) -> None:
    with pytest.raises(ValidationError):
        Settings(**kwargs)


def test_get_settings_cached() -> None:
    first = get_settings()
    second = get_settings()
    assert first is second
    get_settings.cache_clear()
    third = get_settings()
    assert first is not third
