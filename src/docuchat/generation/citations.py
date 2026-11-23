"""Parser de citas [n]: extracción, resolución y detección de 'no lo sé'."""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

from docuchat.generation.prompts import NO_ANSWER  # noqa: F401 re-exported
from docuchat.models import SearchResult

CITATION_RE = re.compile(r"\[\s*(\d+(?:\s*[,;]\s*\d+)*)\s*\]")


@dataclass(frozen=True)
class Source:
    """Fragmento citado: su número en el contexto, documento y página."""

    number: int
    source: str
    page: int


def find_citations(text: str) -> list[int]:
    """Números citados, sin repetir, en orden de primera aparición."""
    seen: set[int] = set()
    result: list[int] = []
    for match in CITATION_RE.finditer(text):
        for num_str in match.group(1).split(","):
            for part in num_str.split(";"):
                n = int(part.strip())
                if n not in seen:
                    seen.add(n)
                    result.append(n)
    return result


def resolve_citations(text: str, context: Sequence[SearchResult]) -> tuple[list[Source], list[int]]:
    """(fuentes válidas en orden de cita, números inventados en orden de cita)."""
    sources: list[Source] = []
    fake: list[int] = []
    for n in find_citations(text):
        if 1 <= n <= len(context):
            chunk = context[n - 1].chunk
            sources.append(Source(number=n, source=chunk.source, page=chunk.page))
        else:
            fake.append(n)
    return sources, fake


def is_no_answer(text: str) -> bool:
    """True si la respuesta empieza por 'no lo sé' (sin distinguir mayúsculas ni tildes)."""
    if not text:
        return False
    normalized = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in normalized if not unicodedata.combining(c)).strip().lower()
    return stripped.startswith("no lo se")
