"""Contextualizador: genera contexto para chunks usando el LLM, con caché SQLite."""

import hashlib
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

from openai import OpenAIError

from docuchat.config import Settings
from docuchat.generation.llm_client import ChatModel, make_chat_model
from docuchat.models import Chunk, Document

logger = logging.getLogger(__name__)

CONTEXT_PROMPT_VERSION = "1"

CONTEXT_PROMPT = """<documento>
{head}
</documento>

<pagina numero="{page}">
{page_text}
</pagina>

Este fragmento pertenece a esa página del documento «{source}»:
<fragmento>
{chunk}
</fragmento>

Escribe una o dos frases breves que sitúen el fragmento dentro del documento: de qué documento trata y, si aparecen en el documento, el producto, la versión o la fecha y la sección. Sirven para encontrar el fragmento en una búsqueda. Responde solo con esas frases, en español, sin datos que no estén en el documento."""  # noqa: E501


def document_head(doc: Document, chars: int) -> str:
    """Los primeros chars caracteres de las páginas unidas con "\\n\\n"."""
    return "\n\n".join(p.text for p in doc.pages)[:chars]


def build_context_prompt(
    doc: Document,
    chunk: Chunk,
    *,
    head_chars: int,
    window_chars: int,
) -> str:
    """CONTEXT_PROMPT relleno con el principio del documento, la página (recortada) y el chunk."""
    head = document_head(doc, head_chars)
    page_obj = next((p for p in doc.pages if p.number == chunk.page), None)
    page_text = (page_obj.text[:window_chars] if page_obj else "")[:window_chars]
    return CONTEXT_PROMPT.format(
        head=head,
        page=chunk.page,
        page_text=page_text,
        source=doc.source,
        chunk=chunk.text,
    )


def cache_key(model: str, prompt: str) -> str:
    """sha256 hex de f"{CONTEXT_PROMPT_VERSION}\\n{model}\\n{prompt}"."""
    raw = f"{CONTEXT_PROMPT_VERSION}\n{model}\n{prompt}"
    return hashlib.sha256(raw.encode()).hexdigest()


class ContextCache:
    """Caché persistente clave → contexto en SQLite."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS contexts (key TEXT PRIMARY KEY, context TEXT NOT NULL)"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path)) as conn, conn:
            yield conn

    def get(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT context FROM contexts WHERE key = ?", (key,)).fetchone()
            return row[0] if row else None

    def put(self, key: str, context: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO contexts (key, context) VALUES (?, ?)",
                (key, context),
            )

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT count(*) FROM contexts").fetchone()
            return int(row[0])


class Contextualizer:
    """Genera el contexto de un chunk con el LLM, usando la caché."""

    def __init__(
        self,
        chat: ChatModel,
        model: str,
        cache: ContextCache,
        *,
        head_chars: int,
        window_chars: int,
        max_chars: int,
    ) -> None:
        self._chat = chat
        self._model = model
        self._cache = cache
        self._head_chars = head_chars
        self._window_chars = window_chars
        self._max_chars = max_chars
        self._llm_calls = 0

    @property
    def llm_calls(self) -> int:
        """Llamadas al LLM hechas por esta instancia (las de la caché no cuentan)."""
        return self._llm_calls

    def context_for(self, doc: Document, chunk: Chunk) -> str:
        """Contexto del chunk; "" si el LLM falla (con aviso en el log)."""
        prompt = build_context_prompt(
            doc,
            chunk,
            head_chars=self._head_chars,
            window_chars=self._window_chars,
        )
        key = cache_key(self._model, prompt)
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        try:
            texto = "".join(self._chat.stream([{"role": "user", "content": prompt}]))
        except Exception as e:
            if isinstance(e, OpenAIError):
                logger.warning("No pude generar el contexto de %s: %s", chunk.chunk_id, e)
                return ""
            raise
        self._llm_calls += 1
        normalized = " ".join(texto.split()).strip()[: self._max_chars].rstrip()
        self._cache.put(key, normalized)
        return normalized


def make_contextualizer(settings: Settings) -> Contextualizer:
    """Crea un Contextualizer con los parámetros de settings."""
    model = settings.contextual_model or settings.llm_model
    chat = make_chat_model(
        settings.model_copy(
            update={
                "llm_model": model,
                "llm_max_tokens": settings.contextual_max_tokens,
                "llm_temperature": 0.0,
                "llm_thinking": False,
            }
        )
    )
    return Contextualizer(
        chat,
        model,
        ContextCache(settings.context_cache_path),
        head_chars=settings.contextual_head_chars,
        window_chars=settings.contextual_window_chars,
        max_chars=settings.contextual_max_chars,
    )
