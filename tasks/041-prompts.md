# 041 · Prompt de sistema y contexto numerado
Fase: 4 · Depende de: 040

## Objetivo
Construir los mensajes para el LLM: prompt de sistema fijo y contexto numerado `[n] documento, p. X` con los chunks recuperados, sin pasar de `context_max_chars`.

## Archivos
- crear: `src/docuchat/generation/__init__.py` (solo el docstring `"""Generación: prompts, cliente LLM, citas y respuestas."""`)
- crear: `src/docuchat/generation/prompts.py`
- crear: `tests/generation/__init__.py` (vacío) y `tests/generation/test_prompts.py`

## Interfaz
```python
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
    """'[n] <source>, p. <page>' + salto de línea + texto del chunk."""


def build_context(
    results: Sequence[SearchResult], max_chars: int
) -> tuple[str, list[SearchResult]]:
    """Contexto numerado desde 1 y los resultados que caben, en orden."""


def build_messages(question: str, context: str) -> list[Message]:
    """[system con SYSTEM_PROMPT, user con los fragmentos y la pregunta]."""
```
`SYSTEM_PROMPT` y `NO_ANSWER` deben quedar EXACTAMENTE como arriba (están probados contra Qwen3.6 en oMLX: cita bien y dice "No lo sé" fuera de los documentos).

## Comportamiento
1. `format_block(n, r)` → `f"[{n}] {r.chunk.source}, p. {r.chunk.page}\n{r.chunk.text}"`.
2. `build_context`: recorre `results` en orden; el bloque i lleva el número `i` (desde 1). Los bloques se unen con `"\n\n"`. Antes de añadir un bloque, si YA hay alguno y el contexto resultante superaría `max_chars` caracteres → para (no salta a otros más pequeños). El primero se incluye siempre, aunque sea más largo que `max_chars`. Devuelve `(contexto, usados)`; con `results` vacío → `("", [])`.
3. `build_messages` → `[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"Fragmentos:\n\n{context}\n\nPregunta: {question}"}]`.

## Tests obligatorios
`tests/generation/test_prompts.py`. NO cambies los valores esperados.
```python
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
```
1. `format_block(3, R[0])` → `"[3] a.pdf, p. 1\nAlfa."`.
2. `build_context(R, 100)` → contexto `"[1] a.pdf, p. 1\nAlfa.\n\n[2] b.md, p. 2\nBeta.\n\n[3] c.txt, p. 1\nGamma."` (67 caracteres) y los 3 usados.
3. Límite justo: `build_context(R, 43)` → contexto de 43 caracteres con 2 usados (`[R[0], R[1]]`).
4. Uno menos: `build_context(R, 42)` → `"[1] a.pdf, p. 1\nAlfa."` y 1 usado.
5. El primero siempre entra: `build_context(R, 10)` → igual que el 4.
6. `build_context([], 100)` → `("", [])`.
7. `build_messages("¿Qué es?", "CTX")` → 2 mensajes; `[0] == {"role": "system", "content": SYSTEM_PROMPT}`; `[1]["content"] == "Fragmentos:\n\nCTX\n\nPregunta: ¿Qué es?"`.
8. `NO_ANSWER in SYSTEM_PROMPT` y `"[1]" in SYSTEM_PROMPT`.

## Aceptación
- [ ] `uv run pytest -q tests/generation/test_prompts.py` → 8 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
Llamadas al LLM (043), citas (042). No cambies el texto del prompt.
