"""Tests para src/docuchat/generation/answer.py."""

from collections.abc import Iterator, Sequence
from pathlib import Path

import httpx
import pytest
from openai import APIConnectionError

from docuchat.config import Settings
from docuchat.generation.answer import Answerer, build_answerer
from docuchat.generation.citations import Source
from docuchat.generation.llm_client import Message
from docuchat.generation.prompts import NO_ANSWER, build_messages
from docuchat.models import Chunk, SearchResult, make_chunk_id


def mk(source: str, page: int, text: str, rank: int = 1) -> SearchResult:
    chunk = Chunk(
        chunk_id=make_chunk_id(source, page, 0),
        source=source,
        doc_sha256="a" * 64,
        page=page,
        position=0,
        text=text,
    )
    return SearchResult(chunk=chunk, rank=rank, score=0.1)


R = [mk("a.pdf", 1, "Alfa."), mk("b.md", 2, "Beta.", 2), mk("c.txt", 1, "Gamma.", 3)]


class FakeRetriever:
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, top_k: int) -> list[SearchResult]:
        self.calls.append((query, top_k))
        return self.results[:top_k]


class FakeChat:
    def __init__(self, pieces: list[str], fail: bool = False) -> None:
        self.pieces = pieces
        self.fail = fail
        self.calls: list[list[Message]] = []

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        self.calls.append(list(messages))
        if self.fail:
            raise APIConnectionError(request=httpx.Request("POST", "http://test"))
        yield from self.pieces


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        documents_dir=tmp_path / "docs",
        data_dir=tmp_path / "data",
    )


def test_ask_normal_case(settings: Settings) -> None:
    r = R[:2]
    retriever = FakeRetriever(r)
    chat = FakeChat(["El dato ", "es X [2]."])
    answerer = Answerer(retriever, chat, top_k=5, context_max_chars=6000)
    tokens: list[str] = []
    answer = answerer.ask("¿Q?", on_token=tokens.append)

    assert tokens == ["El dato ", "es X [2]."]
    assert answer.text == "El dato es X [2]."
    assert answer.sources == [Source(2, "b.md", 2)]
    assert answer.invalid_citations == []
    assert answer.no_answer is False
    assert answer.context == r
    expected_msgs = build_messages("¿Q?", "[1] a.pdf, p. 1\nAlfa.\n\n[2] b.md, p. 2\nBeta.")
    assert chat.calls == [expected_msgs]


def test_fake_citation(settings: Settings) -> None:
    r = R[:2]
    retriever = FakeRetriever(r)
    chat = FakeChat(["Dato [1][9]."])
    answerer = Answerer(retriever, chat, top_k=5, context_max_chars=6000)
    answer = answerer.ask("¿Q?")

    assert answer.sources == [Source(1, "a.pdf", 1)]
    assert answer.invalid_citations == [9]


def test_model_does_not_know(settings: Settings) -> None:
    r = R[:2]
    retriever = FakeRetriever(r)
    chat = FakeChat([NO_ANSWER])
    answerer = Answerer(retriever, chat, top_k=5, context_max_chars=6000)
    answer = answerer.ask("¿Q?")

    assert answer.no_answer is True
    assert answer.sources == []
    assert answer.invalid_citations == []


def test_no_results(settings: Settings) -> None:
    retriever = FakeRetriever([])
    chat = FakeChat([])
    answerer = Answerer(retriever, chat, top_k=5, context_max_chars=6000)
    tokens: list[str] = []
    answer = answerer.ask("¿Q?", on_token=tokens.append)

    assert tokens == [NO_ANSWER]
    assert chat.calls == []
    assert answer.no_answer is True
    assert answer.context == []


def test_empty_response(settings: Settings) -> None:
    r = R[:2]
    retriever = FakeRetriever(r)
    chat = FakeChat(["  ", "\n"])
    answerer = Answerer(retriever, chat, top_k=5, context_max_chars=6000)
    answer = answerer.ask("¿Q?")

    assert answer.text == NO_ANSWER
    assert answer.no_answer is True


def test_context_limit(settings: Settings) -> None:
    retriever = FakeRetriever(R)
    chat = FakeChat(["ok"])
    answerer = Answerer(retriever, chat, top_k=5, context_max_chars=43)

    assert answerer.retrieve("x") == R[:2]
    answer = answerer.ask("x")
    assert answer.context == R[:2]


def test_top_k(settings: Settings) -> None:
    r = R[:2]
    retriever = FakeRetriever(r)
    chat = FakeChat(["ok"])
    answerer = Answerer(retriever, chat, top_k=2, context_max_chars=6000)
    answerer.ask("¿Q?")

    assert retriever.calls == [("¿Q?", 2)]


def test_llm_error(settings: Settings) -> None:
    r = R[:2]
    retriever = FakeRetriever(r)
    chat = FakeChat([], fail=True)
    answerer = Answerer(retriever, chat, top_k=5, context_max_chars=6000)

    with pytest.raises(APIConnectionError):
        answerer.ask("¿Q?")


def test_build_answerer_with_fakes(settings: Settings) -> None:
    retriever = FakeRetriever([])
    chat = FakeChat([])
    answerer = build_answerer(settings, retriever=retriever, chat=chat, top_k=3)
    assert isinstance(answerer, Answerer)
    answer = answerer.ask("hola")
    assert answer.no_answer is True


def test_build_answerer_without_args(settings: Settings) -> None:
    answerer = build_answerer(settings)
    assert isinstance(answerer, Answerer)
