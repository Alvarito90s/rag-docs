"""Prompts y construcción de mensajes para el LLM."""

from collections.abc import Sequence

from openai.types.chat import ChatCompletionMessageParam

from docuchat.models import SearchResult

Message = ChatCompletionMessageParam

NO_ANSWER = "No lo sé con la información de los documentos."

SYSTEM_PROMPT = (
    "Eres DocuChat, un asistente que responde preguntas usando SOLO los fragmentos "
    "de documentos que recibes.\n"
    "Reglas:\n"
    "1. Usa únicamente la información de los fragmentos; nunca tu conocimiento propio.\n"
    "2. Cita cada dato con el número de su fragmento entre corchetes, por ejemplo [1] o [2][3].\n"
    f"3. Si los fragmentos no contienen la respuesta, responde exactamente: {NO_ANSWER}\n"
    "4. Responde en el idioma de la pregunta, de forma breve y directa."
)


def format_block(number: int, result: SearchResult) -> str:
    """Bloque numerado: '[n] <source>, p. <page>' + salto de línea + texto."""
    return f"[{number}] {result.chunk.source}, p. {result.chunk.page}\n{result.chunk.text}"


def build_context(
    results: Sequence[SearchResult], max_chars: int
) -> tuple[str, list[SearchResult]]:
    """Contexto numerado desde 1 y los resultados que caben, en orden."""
    if not results:
        return ("", [])

    blocks: list[str] = []
    used: list[SearchResult] = []

    for i, result in enumerate(results, start=1):
        block = format_block(i, result)
        # El primero se incluye siempre
        if not blocks:
            blocks.append(block)
            used.append(result)
            continue

        candidate = "\n\n".join(blocks + [block])
        if len(candidate) <= max_chars:
            blocks.append(block)
            used.append(result)
        else:
            break

    return ("\n\n".join(blocks), used)


def build_messages(question: str, context: str) -> list[Message]:
    """Sistema + usuario con fragmentos y pregunta."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Fragmentos:\n\n{context}\n\nPregunta: {question}",
        },
    ]
