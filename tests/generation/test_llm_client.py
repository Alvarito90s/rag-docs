"""Tests para src/docuchat/generation/llm_client.py."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError

from docuchat.generation.llm_client import OpenAIChatModel, make_chat_model
from docuchat.generation.prompts import Message


def ch(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=content))])


CHUNKS = [
    SimpleNamespace(choices=[]),
    ch(None),
    ch("\n\n"),
    ch("  Hola"),
    ch(""),
    ch(" mundo [1]."),
    ch(None),
]
MSGS: list[Message] = [
    {"role": "system", "content": "s"},
    {"role": "user", "content": "u"},
]


def test_stream_returns_filtered_trozos() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = iter(CHUNKS)
    model = OpenAIChatModel(client, "m", max_tokens=10, temperature=0.2, thinking=False)

    result = list(model.stream(MSGS))
    assert result == ["Hola", " mundo [1]."]


def test_stream_call_args() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = iter(CHUNKS)
    model = OpenAIChatModel(client, "m", max_tokens=10, temperature=0.2, thinking=False)

    list(model.stream(MSGS))
    expected = {
        "model": "m",
        "messages": MSGS,
        "max_tokens": 10,
        "temperature": 0.2,
        "stream": True,
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
    }
    assert client.chat.completions.create.call_args.kwargs == expected
    assert client.chat.completions.create.call_count == 1


def test_thinking_true_extra_body() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = iter(CHUNKS)
    model = OpenAIChatModel(client, "m", max_tokens=10, temperature=0.2, thinking=True)

    list(model.stream(MSGS))
    assert client.chat.completions.create.call_args.kwargs["extra_body"] == {
        "chat_template_kwargs": {"enable_thinking": True}
    }


def test_complete_joins_and_strips() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = iter(CHUNKS)
    model = OpenAIChatModel(client, "m", max_tokens=10, temperature=0.2, thinking=False)

    assert model.complete(MSGS) == "Hola mundo [1]."


def test_only_whitespace_strips_everything() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = iter([ch("\n"), ch("  ")])
    model = OpenAIChatModel(client, "m", max_tokens=10, temperature=0.2, thinking=False)

    assert list(model.stream(MSGS)) == []
    assert model.complete(MSGS) == ""


def test_propagates_api_connection_error() -> None:
    import httpx

    client = MagicMock()
    client.chat.completions.create.side_effect = APIConnectionError(
        request=httpx.Request("POST", "http://test"),
    )
    model = OpenAIChatModel(client, "m", max_tokens=10, temperature=0.2, thinking=False)

    with pytest.raises(APIConnectionError):
        list(model.stream(MSGS))


def test_lazy_streaming() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = iter(CHUNKS)
    model = OpenAIChatModel(client, "m", max_tokens=10, temperature=0.2, thinking=False)

    gen = model.stream(MSGS)
    assert client.chat.completions.create.call_count == 0
    next(gen)
    assert client.chat.completions.create.call_count == 1


def test_make_chat_model_returns_openai_chat_model(settings: object) -> None:
    with patch("docuchat.generation.llm_client.OpenAI") as mock_openai:
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        mock_settings = settings  # type: ignore[assignment]

        chat_model = make_chat_model(mock_settings)  # type: ignore[arg-type]

        assert isinstance(chat_model, OpenAIChatModel)
        assert chat_model.model == "Qwen3.6-35B-A3B-6bit"
