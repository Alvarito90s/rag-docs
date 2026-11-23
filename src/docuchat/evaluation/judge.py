"""Juez de fidelidad: ¿está respaldada la respuesta por los fragmentos que cita?"""

import json
from collections.abc import Sequence
from dataclasses import dataclass, field

from docuchat.generation.answer import Answer
from docuchat.generation.llm_client import ChatModel
from docuchat.generation.prompts import Message

JUDGE_PROMPT = (
    "Eres un revisor estricto. Recibes una pregunta, una respuesta y los fragmentos de "
    "documentos que la respuesta cita. Comprueba si cada afirmación de la respuesta está "
    "respaldada por los fragmentos; ignora los números de cita entre corchetes. Responde "
    "SOLO con un objeto JSON, sin texto antes ni después, con esta forma: "
    '{"supported": true o false, "unsupported": ['
    "afirmaciones sin respaldo, copiadas de la respuesta]}. "
    'Si todo está respaldado, "unsupported" es una lista vacía.'
)
NO_CITATIONS = "la respuesta no cita ningún fragmento"


@dataclass(frozen=True)
class Verdict:
    """Veredicto del juez."""

    supported: bool
    unsupported: list[str] = field(default_factory=list)


def build_judge_messages(question: str, answer: str, passages: Sequence[str]) -> list[Message]:
    """Mensajes de sistema y usuario para el juez."""
    user = f"Pregunta: {question}\n\nRespuesta: {answer}\n\nFragmentos citados:\n" + "\n\n".join(
        f"[{i}] {p}" for i, p in enumerate(passages, start=1)
    )
    return [
        {"role": "system", "content": JUDGE_PROMPT},
        {"role": "user", "content": user},
    ]


def parse_verdict(text: str) -> Verdict | None:
    """Extrae el veredicto del texto del juez; None si no es un JSON válido con
    la forma esperada."""
    i = text.find("{")
    j = text.rfind("}")
    if i == -1 or j == -1 or j < i:
        return None
    try:
        data = json.loads(text[i : j + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if "supported" not in data or not isinstance(data["supported"], bool):
        return None
    unsupported = data.get("unsupported", [])
    if not isinstance(unsupported, list) or not all(isinstance(s, str) for s in unsupported):
        return None
    return Verdict(
        supported=data["supported"] and not unsupported,
        unsupported=unsupported,
    )


def cited_passages(answer: Answer) -> list[str]:
    """Textos de los chunks citados por la respuesta, sin repetir, en orden de cita."""
    seen: set[int] = set()
    result: list[str] = []
    for src in answer.sources:
        if src.number in seen:
            continue
        if 1 <= src.number <= len(answer.context):
            result.append(answer.context[src.number - 1].chunk.text)
            seen.add(src.number)
    return result


class Judge:
    """Juez de fidelidad sobre cualquier ChatModel."""

    def __init__(self, chat: ChatModel) -> None:
        self._chat = chat

    def judge(self, question: str, answer: str, passages: Sequence[str]) -> Verdict | None:
        """Veredicto del LLM; sin fragmentos, Verdict(False, [NO_CITATIONS]) sin llamar al LLM."""
        if not passages:
            return Verdict(False, [NO_CITATIONS])
        text = "".join(self._chat.stream(build_judge_messages(question, answer, passages)))
        return parse_verdict(text)
