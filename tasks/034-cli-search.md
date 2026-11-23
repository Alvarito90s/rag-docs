# 034 · Comando `docuchat search`
Fase: 3 · Depende de: 033

## Objetivo
`docuchat search "consulta"` muestra los chunks recuperados con su puesto, documento, página, puntuación y un fragmento del texto.

## Archivos
- modificar: `src/docuchat/cli.py` (solo AÑADIR el comando `search`, las funciones `snippet` y `format_result`, y los imports)
- modificar: `tests/test_cli.py` (solo AÑADIR un fixture y tests)

## Interfaz
```python
from docuchat.models import SearchResult
from docuchat.retrieval.searcher import SearchMode, build_searcher


def snippet(text: str, width: int = 150) -> str:
    """Texto en una línea (espacios colapsados), cortado a width caracteres con '…'."""


def format_result(result: SearchResult) -> str:
    """Dos líneas: cabecera con puesto, documento, página y puntuaciones, y el fragmento."""


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Texto a buscar.")],
    top_k: Annotated[
        int | None,
        typer.Option("--top-k", "-k", help="Número de resultados (por defecto DOCUCHAT_TOP_K)."),
    ] = None,
    mode: Annotated[
        SearchMode,
        typer.Option("--mode", help="hybrid, vector o bm25."),
    ] = SearchMode.HYBRID,
) -> None:
    """Busca en los documentos indexados."""
```
Importa `build_searcher` con `from docuchat.retrieval.searcher import ...` (los tests lo parchean en `docuchat.cli`).

## Comportamiento
1. `snippet`: `plano = " ".join(text.split())`; si `len(plano) <= width` → `plano`; si no → `plano[:width].rstrip() + "…"`.
2. `format_result` devuelve exactamente:
   ```
   [{rank}] {source} · p. {page} · {score:.4f} (vec {vector_rank}, bm25 {bm25_rank})
       {snippet(texto)}
   ```
   con `-` en lugar de `None` en los rangos, 4 espacios de sangría en la segunda línea y `"\n"` entre ambas (sin salto final).
3. `search`:
   a. `settings = get_settings()`; `k = top_k if top_k is not None else settings.top_k`. Si `k <= 0` → `"--top-k debe ser positivo"` por stderr, exit 1.
   b. `searcher = build_searcher(settings)`. `EmbeddingModelMismatchError` → `typer.echo(str(e), err=True)`, exit 1.
   c. Si `searcher.size() == 0` → `"El índice está vacío. Ejecuta: docuchat ingest"` por stderr, exit 1.
   d. `results = searcher.search(query, k, mode)`. `OpenAIError` o `EmbeddingError` → `f"Error con el servidor de embeddings: {type(e).__name__}: {e}"` por stderr, exit 1.
   e. Sin resultados → `typer.echo("Sin resultados.")`, exit 0.
   f. Si no, `typer.echo(format_result(r))` para cada resultado, con una línea en blanco (`typer.echo()`) entre resultados. Usa `typer.echo`, NO una tabla Rich (en 80 columnas la tabla recorta los nombres de documento; comprobado).

## Tests obligatorios
Añadir a `tests/test_cli.py`. NO cambies los valores esperados ni los tests existentes.
```python
from docuchat.retrieval import searcher as searcher_mod


@pytest.fixture()
def search_env(index_env: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """index_env + build_searcher con FakeEmbedder."""
    monkeypatch.setattr(
        "docuchat.cli.build_searcher",
        lambda s: searcher_mod.build_searcher(s, embedder=FakeEmbedder()),
    )
    return index_env
```
En los tests 18–23, primero `runner.invoke(app, ["ingest", str(SAMPLES)])` (exit 0).

18. `test_18_search_bm25`: `search E-17 --mode bm25` → exit 0; la salida contiene `"[1] manual_cafetera.pdf · p. 7 · "` y `"código de error E-17"`.
19. `test_19_search_top_k`: `search SKU-4471-B -k 1 --mode bm25` → exit 0; contiene `"[1] glosario_interno.md · p. 1"` y `"(vec -, bm25 1)"`; NO contiene `"[2]"`.
20. `test_20_search_hybrid_default_k`: `search "garantía de la cafetera"` → exit 0; contiene `"[5] "` y no `"[6] "` (top_k por defecto 5).
21. `test_21_search_no_results`: `search zzzz --mode bm25` → exit 0 y `"Sin resultados."`.
22. `test_22_search_invalid_mode`: `search hola --mode otro` → `exit_code == 2`.
23. `test_23_search_embedding_error`: parchea `docuchat.cli.build_searcher` con `FakeEmbedder(fail_on="")` → `search hola` → exit 1, `"Error con el servidor de embeddings: APIConnectionError"`, `isinstance(result.exception, SystemExit)`.
24. `test_24_search_empty_index` (`search_env`, SIN ingest): `search hola` → exit 1 y `"El índice está vacío"`.
25. `test_25_search_model_mismatch` (`search_env`): `ingest SAMPLES`; `monkeypatch.setenv("DOCUCHAT_EMBEDDING_MODEL", "otro")` y `get_settings.cache_clear()`; `search hola` → exit 1 y `"Reindexa con --reset"`.
26. `test_26_format_result`: con `chunk = Chunk(chunk_id="a.pdf#p3#c0", source="a.pdf", doc_sha256="a" * 64, page=3, position=0, text="  Hola\n\nmundo  ")`, `format_result(SearchResult(chunk=chunk, rank=2, score=0.0327869, vector_rank=None, bm25_rank=1))` == `"[2] a.pdf · p. 3 · 0.0328 (vec -, bm25 1)\n    Hola mundo"`.
27. `test_27_snippet`: `snippet("a " * 100)` tiene 150 caracteres y termina en `"a…"` (el corte cae en un espacio y `rstrip` lo quita); `snippet("corto")` == `"corto"`; `snippet("abc def", width=4)` == `"abc…"`; `snippet("abc def", width=5)` == `"abc d…"`.

## Aceptación
- [ ] `uv run pytest -q tests/test_cli.py` → 26 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `uv run docuchat search --help` muestra `--top-k` y `--mode`
- [ ] (humano, con oMLX y `uv run docuchat ingest` hecho) `uv run docuchat search "¿Qué significa el error E-17?"` → `[1] manual_cafetera.pdf · p. 7`

## Fuera de alcance
No toques `ingest` ni nada de `retrieval/` o `index/`. Nada de `ask` (Fase 4).
