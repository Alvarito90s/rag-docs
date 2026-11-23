# 033 · Buscador híbrido (vectorial + BM25 + RRF)
Fase: 3 · Depende de: 030, 031, 032

## Objetivo
`Searcher`: dada una consulta, combina la búsqueda vectorial y BM25 con RRF, quita chunks contiguos y devuelve los top-k como `SearchResult`.

## Archivos
- crear: `src/docuchat/retrieval/searcher.py`
- crear: `tests/retrieval/test_searcher.py`

## Interfaz
```python
from enum import StrEnum

from docuchat.config import Settings
from docuchat.index.bm25 import Bm25Index
from docuchat.index.embeddings import Embedder, make_embedder
from docuchat.index.vector_store import VectorStore
from docuchat.models import Chunk, SearchResult
from docuchat.retrieval.fusion import drop_adjacent, rrf_fuse


class SearchMode(StrEnum):
    """Qué buscadores se usan."""

    HYBRID = "hybrid"
    VECTOR = "vector"
    BM25 = "bm25"


def format_query(query: str, instruction: str) -> str:
    """Antepone la instrucción de Qwen3-Embedding: 'Instruct: {instruction}\\nQuery:{query}'."""


class Searcher:
    """Búsqueda híbrida sobre VectorStore; el índice BM25 se construye en memoria la primera vez."""

    def __init__(
        self,
        store: VectorStore,
        embedder: Embedder,
        *,
        candidate_k: int,
        rrf_k: int,
        query_instruction: str,
    ) -> None: ...
    def size(self) -> int:
        """Número de chunks indexados."""
    def refresh(self) -> None:
        """Olvida el índice BM25 en memoria; se reconstruye en la siguiente búsqueda."""
    def search(
        self, query: str, top_k: int, mode: SearchMode = SearchMode.HYBRID
    ) -> list[SearchResult]:
        """Los top_k chunks más relevantes para query."""


def build_searcher(settings: Settings, embedder: Embedder | None = None) -> Searcher:
    """Crea el Searcher con el VectorStore y los parámetros de settings."""
```

## Comportamiento
1. `format_query`: si `instruction` es `""` → `query` tal cual; si no → `f"Instruct: {instruction}\nQuery:{query}"` (sin espacio tras `Query:`, formato oficial de Qwen3-Embedding). Solo las consultas llevan instrucción; los documentos se indexaron sin ella.
2. `size()` → `store.count()`. `refresh()` pone a `None` la caché interna (chunks por id + `Bm25Index`).
3. `search`:
   a. Si `query.strip() == ""` o `top_k <= 0` → `[]` sin llamar al embedder.
   b. Si la caché es `None`: `chunks = store.all_chunks()`, guarda `{chunk_id: chunk}` y `Bm25Index(ids, textos)`. Si no hay chunks → `[]` (sin llamar al embedder).
   c. Si `mode` es `HYBRID` o `VECTOR`: `vector = embedder.embed([format_query(query, query_instruction)])[0]`; `hits = store.query(vector, candidate_k)`; `vector_ids = [c.chunk_id for c, _ in hits]`. Si no, `vector_ids = []`.
   d. Si `mode` es `HYBRID` o `BM25`: `bm25_ids = [i for i, _ in bm25.search(query, candidate_k)]` (consulta SIN instrucción). Si no, `[]`.
   e. `rankings`: `[vector_ids, bm25_ids]` en HYBRID, `[vector_ids]` en VECTOR, `[bm25_ids]` en BM25. `fused = rrf_fuse(rankings, rrf_k)`.
   f. Mapa de chunks: la caché, actualizada con los chunks de `hits` (por si el índice cambió tras crear la caché). `ordered = [mapa[i] for i, _ in fused]`; `kept = drop_adjacent(ordered)[:top_k]`.
   g. Devuelve un `SearchResult` por chunk de `kept`: `rank` desde 1, `score` = su score RRF, `vector_rank` = posición desde 1 en `vector_ids` o `None`, `bm25_rank` igual con `bm25_ids`.
   h. Los errores del embedder (`OpenAIError`, `EmbeddingError`) se propagan; no los captures.
4. `build_searcher`: `VectorStore(settings.chroma_dir, settings.chroma_collection, settings.embedding_model)` (puede lanzar `EmbeddingModelMismatchError`; no lo captures), `embedder or make_embedder(settings)`, y `candidate_k`, `rrf_k`, `query_instruction` de settings.

## Tests obligatorios
`tests/retrieval/test_searcher.py`. NO cambies los valores esperados. Nada de red.
Embedder falso por palabras clave (deterministas y con sentido):
```python
VOCAB = ["contrato", "cafetera", "garantia", "vacaciones"]
INSTR = "Given a question, retrieve passages that answer the question"


class KeywordEmbedder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        out = []
        for t in texts:
            tokens = tokenize(t)  # de docuchat.index.bm25
            out.append([float(tokens.count(w)) for w in VOCAB] + [0.01])
        return out
```
Corpus (helper `mk(source, page, position, text)` como en `test_fusion.py` pero con texto):
```python
CORPUS = [
    mk("a.pdf", 1, 0, "El contrato se firma en Valladolid."),
    mk("a.pdf", 1, 1, "El contrato incluye garantia de dos años."),
    mk("b.pdf", 3, 0, "La cafetera tiene garantia de tres años."),
    mk("c.md", 1, 0, "Política de vacaciones para el personal."),
]
```
Fixture: `VectorStore(tmp_path / "chroma", "chunks", "fake")` con `store.add(CORPUS, KeywordEmbedder().embed([c.text for c in CORPUS]))` y `Searcher(store, embedder, candidate_k=20, rrf_k=60, query_instruction=INSTR)` con un `KeywordEmbedder` NUEVO (para contar sus llamadas).

1. `format_query("hola", "Busca")` → `"Instruct: Busca\nQuery:hola"`.
2. `format_query("hola", "")` → `"hola"`.
3. Híbrido: `search("cafetera", 1)` → un resultado: `chunk.chunk_id == "b.pdf#p3#c0"`, `rank == 1`, `vector_rank == 1`, `bm25_rank == 1`, `score == pytest.approx(2 / 61)`.
4. Vectorial con deduplicación: `search("garantia del contrato", 5, SearchMode.VECTOR)` → ids `["a.pdf#p1#c1", "b.pdf#p3#c0", "c.md#p1#c0"]` (`a.pdf#p1#c0` se descarta por contiguo), `vector_rank` `[1, 3, 4]`, todos `bm25_rank is None`, ranks `[1, 2, 3]`.
5. BM25: `search("garantia del contrato", 5, SearchMode.BM25)` → ids `["a.pdf#p1#c0", "b.pdf#p3#c0"]`, `bm25_rank` `[1, 3]`, `vector_rank` `[None, None]`; el embedder NO se ha llamado.
6. BM25 rescata nombres propios: `search("Valladolid", 1)` → `chunk_id == "a.pdf#p1#c0"` y `bm25_rank == 1`.
7. Instrucción: tras `search("cafetera", 1)`, `embedder.calls == [[f"Instruct: {INSTR}\nQuery:cafetera"]]`. Con `query_instruction=""` → `[["cafetera"]]`.
8. `search("   ", 5) == []` y `search("cafetera", 0) == []`; `embedder.calls == []`.
9. Store vacío: `Searcher` sobre un `VectorStore` nuevo → `size() == 0`, `search("cafetera", 5) == []`, `embedder.calls == []`.
10. `refresh`: `search("Valladolid", 5, SearchMode.BM25)` → 1 resultado. Añade al store `mk("d.txt", 1, 0, "Valladolid en invierno.")` con su vector. Sin `refresh` → sigue 1 resultado; tras `refresh()` → ids `{"a.pdf#p1#c0", "d.txt#p1#c0"}`.
11. `build_searcher(settings, embedder=KeywordEmbedder())` con el fixture `settings` de `conftest.py` → `size() == 0` y `search("hola", 5) == []`.

## Aceptación
- [ ] `uv run pytest -q tests/retrieval/test_searcher.py` → 11 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "except" src/docuchat/retrieval/searcher.py` → sin resultados

## Fuera de alcance
No toques `fusion.py`, `vector_store.py`, `bm25.py` ni `embeddings.py`. Nada de CLI (spec 034). Sin reranker.
