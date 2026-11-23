# 045 · Comando `docuchat ask`
Fase: 4 · Depende de: 044

## Objetivo
`docuchat ask "pregunta"` responde en streaming usando los documentos y termina con la lista de fuentes `[n] documento, p. X`.

## Archivos
- modificar: `src/docuchat/cli.py` (solo AÑADIR el comando `ask`, la función `format_sources` y los imports)
- modificar: `tests/test_cli.py` (solo AÑADIR tests y la clase `FakeChat`)

## Interfaz
```python
from docuchat.generation.answer import Answer, build_answerer
from docuchat.generation.citations import Source


def format_sources(sources: list[Source]) -> list[str]:
    """Una línea por fuente: '[n] documento, p. X'."""


@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="Pregunta sobre tus documentos.")],
    top_k: Annotated[
        int | None,
        typer.Option("--top-k", "-k", help="Fragmentos de contexto (por defecto DOCUCHAT_TOP_K)."),
    ] = None,
) -> None:
    """Responde a una pregunta citando los documentos."""
```
Importa `build_searcher` (ya importado) y `build_answerer` a nivel de módulo: los tests los parchean en `docuchat.cli`.

## Comportamiento
1. `settings = get_settings()`. Si `top_k` no es `None` y es `<= 0` → `"--top-k debe ser positivo"` por stderr, exit 1.
2. `searcher = build_searcher(settings)`; `EmbeddingModelMismatchError` → `str(e)` por stderr, exit 1. Si `searcher.size() == 0` → `"El índice está vacío. Ejecuta: docuchat ingest"` por stderr, exit 1.
3. `answerer = build_answerer(settings, retriever=searcher, top_k=top_k)`.
4. `answer = answerer.ask(question, on_token=lambda t: typer.echo(t, nl=False))` y después `typer.echo()` (salto de línea final). `OpenAIError` o `EmbeddingError` → `typer.echo()` y `f"Error con el servidor de modelos: {type(e).__name__}: {e}"` por stderr, exit 1.
5. Si `answer.no_answer` → exit 0 sin nada más.
6. Si hay `answer.sources` → `typer.echo()`, `typer.echo("Fuentes:")` y una línea por cada `format_sources(...)`. Si no hay ninguna → `"Aviso: la respuesta no cita ninguna fuente."` por stderr.
7. Si hay `answer.invalid_citations` → `"Aviso: citas sin fuente descartadas: [9], [12]"` por stderr (números con corchetes, separados por `", "`).
8. `format_sources` → `[f"[{s.number}] {s.source}, p. {s.page}" for s in sources]`.

## Tests obligatorios
Añadir a `tests/test_cli.py`. NO cambies los valores esperados ni los tests existentes.
Copia `FakeChat` de `tests/generation/test_answer.py`. En cada test, crea `chat = FakeChat([...])` y parchea:
```python
monkeypatch.setattr(
    "docuchat.cli.build_answerer",
    lambda s, retriever, top_k: answer_mod.build_answerer(s, retriever=retriever, chat=chat, top_k=top_k),
)
```
(`from docuchat.generation import answer as answer_mod`). Usa el fixture `search_env` y, salvo en el 32, primero `ingest SAMPLES` (exit 0).

28. `test_28_ask_answer`: `FakeChat(["El error E-17 ", "indica depósito vacío [1]."])` → `ask "¿Qué es E-17?"` → exit 0; la salida contiene `"El error E-17 indica depósito vacío [1]."` y `re.search(r"Fuentes:\n\[1\] \S+, p\. \d+", output)`.
29. `test_29_ask_invalid_citation`: `FakeChat(["Dato [1][9]."])` → exit 0 y `"Aviso: citas sin fuente descartadas: [9]"`.
30. `test_30_ask_no_answer`: `FakeChat([NO_ANSWER])` → exit 0, contiene `NO_ANSWER` y NO contiene `"Fuentes:"`.
31. `test_31_ask_no_citations`: `FakeChat(["Respuesta sin citas."])` → exit 0, contiene `"Aviso: la respuesta no cita ninguna fuente."` y no `"Fuentes:"`.
32. `test_32_ask_empty_index` (sin ingest): → exit 1 y `"El índice está vacío"`.
33. `test_33_ask_llm_error`: `FakeChat([], fail=True)` → exit 1, `"Error con el servidor de modelos: APIConnectionError"`, `isinstance(result.exception, SystemExit)`.
34. `test_34_ask_top_k`: `FakeChat(["Ok [1]."])`, `ask hola -k 2` → exit 0; el mensaje de usuario (`chat.calls[0][1]["content"]`) contiene `"[2] "` y no `"[3] "`.
35. `test_35_format_sources`: `format_sources([Source(1, "a.pdf", 3), Source(4, "b.md", 1)])` → `["[1] a.pdf, p. 3", "[4] b.md, p. 1"]`.

## Aceptación
- [ ] `uv run pytest -q tests/test_cli.py` → 34 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `uv run docuchat ask --help` muestra `--top-k`
- [ ] (humano, con oMLX e índice hecho) `uv run docuchat ask "¿Qué significa el error E-17?"` → respuesta con `[1]` y `Fuentes:` con `manual_cafetera.pdf, p. 7`
- [ ] (humano) `uv run docuchat ask "¿Quién ganó el mundial de fútbol de 2010?"` → `No lo sé con la información de los documentos.` sin fuentes

## Fuera de alcance
No toques `ingest`, `search` ni nada de `generation/` o `retrieval/`. Nada de API (Fase 5).
