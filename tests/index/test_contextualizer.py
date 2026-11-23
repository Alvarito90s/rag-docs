"""Spec 111: tests de Contextualizer, ContextCache y configuración."""

from pathlib import Path

from openai import APIConnectionError

from docuchat.config import Settings
from docuchat.index.contextualizer import (
    ContextCache,
    Contextualizer,
    build_context_prompt,
    cache_key,
    document_head,
    make_contextualizer,
)
from docuchat.models import Chunk, DocType, Document, Page, make_chunk_id

# ── Fixtures ───────────────────────────────────────────────────────────


class FakeChat:
    def __init__(
        self,
        reply: str = "Manual del Termia K1, uso diario.",
        fail: bool = False,
    ) -> None:
        self.reply, self.fail = reply, fail
        self.calls: list[list[dict[str, str]]] = []

    def stream(self, messages):
        self.calls.append(list(messages))
        if self.fail:
            raise APIConnectionError(request=__import__("httpx").Request("POST", "http://test"))
        yield from [self.reply[:5], self.reply[5:]]


DOC = Document(
    source="k1.pdf",
    path=Path("/x/k1.pdf"),
    sha256="a" * 64,
    doc_type=DocType.PDF,
    pages=(
        Page(number=1, text="Manual del hervidor Termia K1."),
        Page(number=2, text="Uso diario. Llena el depósito."),
    ),
)

CHUNK = Chunk(
    chunk_id=make_chunk_id("k1.pdf", 2, 0),
    source="k1.pdf",
    doc_sha256="a" * 64,
    page=2,
    position=0,
    text="Llena el depósito.",
)


def make(tmp_path: Path, chat: FakeChat, **kw) -> Contextualizer:
    opts = dict(head_chars=1500, window_chars=3000, max_chars=300) | kw
    return Contextualizer(
        chat,
        "m",
        ContextCache(tmp_path / "sub" / "cache.sqlite3"),
        **opts,
    )


# ── Tests ──────────────────────────────────────────────────────────────


def test_document_head() -> None:
    head = "Manual del hervidor Termia K1.\n\nUso diario. Llena el depósito."
    assert document_head(DOC, 1500) == head
    assert document_head(DOC, 6) == "Manual"


def test_prompt() -> None:
    p = build_context_prompt(DOC, CHUNK, head_chars=1500, window_chars=5)
    assert '<pagina numero="2">\nUso d\n</pagina>' in p
    assert "«k1.pdf»" in p
    assert "<fragmento>\nLlena el depósito.\n</fragmento>" in p
    assert p.startswith("<documento>\nManual del hervidor Termia K1.")


def test_genera_y_cachea(tmp_path: Path) -> None:
    chat = FakeChat()
    c = make(tmp_path, chat)
    result = c.context_for(DOC, CHUNK)
    assert result == "Manual del Termia K1, uso diario."
    assert len(chat.calls) == 1
    assert c.llm_calls == 1
    # Segunda llamada → caché
    result2 = c.context_for(DOC, CHUNK)
    assert result2 == "Manual del Termia K1, uso diario."
    assert len(chat.calls) == 1


def test_cache_persiste(tmp_path: Path) -> None:
    chat1 = FakeChat()
    make(tmp_path, chat1).context_for(DOC, CHUNK)
    # Nuevo contextualizador con chat que falla → usa caché
    chat2 = FakeChat(fail=True)
    c2 = make(tmp_path, chat2)
    result = c2.context_for(DOC, CHUNK)
    assert result == "Manual del Termia K1, uso diario."
    assert len(chat2.calls) == 0


def test_clave_cambia() -> None:
    chat = FakeChat()
    cache = ContextCache(Path("/tmp/fake_ctx_test.sqlite3"))
    c1 = Contextualizer(
        chat,
        "m",
        cache,
        head_chars=1500,
        window_chars=3000,
        max_chars=300,
    )
    c1.context_for(DOC, CHUNK)
    assert len(chat.calls) == 1

    chat2 = FakeChat()
    c2 = Contextualizer(
        chat2,
        "otro",
        cache,
        head_chars=1500,
        window_chars=3000,
        max_chars=300,
    )
    c2.context_for(DOC, CHUNK)
    assert len(chat2.calls) == 1

    assert cache_key("m", "p") != cache_key("otro", "p")
    assert cache_key("m", "p") != cache_key("m", "q")
    assert len(cache_key("m", "p")) == 64

    # Limpieza
    cache._path.unlink(missing_ok=True)


def test_normaliza_y_recorta() -> None:
    chat = FakeChat(reply="  Uno\n\n dos   tres  ")
    c = make(Path("/tmp/fake_norm.sqlite3"), chat)
    result = c.context_for(DOC, CHUNK)
    assert result == "Uno dos tres"

    chat2 = FakeChat(reply="  Uno\n\n dos   tres  ")
    c2 = make(Path("/tmp/fake_norm2.sqlite3"), chat2, max_chars=7)
    result2 = c2.context_for(DOC, CHUNK)
    assert result2 == "Uno dos"


def test_error_llm(caplog) -> None:
    c = make(Path("/tmp/fake_err.sqlite3"), FakeChat(fail=True))
    assert c.context_for(DOC, CHUNK) == ""
    assert "No pude generar el contexto" in caplog.text
    # La caché no guardó el error
    assert c._cache.count() == 0


def test_otro_error_se_propaga() -> None:
    class BrokenChat:
        def stream(self, messages):
            raise ValueError("x")

    c = make(Path("/tmp/fake_val.sqlite3"), BrokenChat())  # type: ignore[arg-type]
    try:
        c.context_for(DOC, CHUNK)
    except ValueError:
        pass
    else:
        raise AssertionError("Debería propagar ValueError")


def test_settings(settings: Settings, tmp_path: Path) -> None:
    assert settings.contextual_enabled is False
    assert settings.contextual_model == ""
    assert settings.contextual_head_chars == 1500
    assert settings.contextual_window_chars == 3000
    assert settings.contextual_max_chars == 300
    assert settings.contextual_max_tokens == 200
    assert Settings(data_dir=tmp_path).context_cache_path == tmp_path / "context_cache.sqlite3"


def test_make_contextualizer(settings: Settings) -> None:
    from unittest.mock import MagicMock

    fake = MagicMock()
    received: dict = {}

    import docuchat.index.contextualizer as mod

    original = mod.make_chat_model
    mod.make_chat_model = lambda s: received.update({"received": s}) or fake

    try:
        result = make_contextualizer(settings.model_copy(update={"contextual_model": "ctx"}))
        assert isinstance(result, Contextualizer)
        assert received["received"].llm_model == "ctx"
        assert received["received"].llm_max_tokens == 200
        assert received["received"].llm_temperature == 0.0
        assert received["received"].llm_thinking is False
    finally:
        mod.make_chat_model = original

    received2: dict = {}
    fake2 = MagicMock()
    mod.make_chat_model = lambda s: received2.update({"received": s}) or fake2
    try:
        make_contextualizer(settings)
        assert received2["received"].llm_model == settings.llm_model
    finally:
        mod.make_chat_model = original
