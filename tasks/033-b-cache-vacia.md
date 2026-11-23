# 033-b · Searcher: no cachear un índice vacío
Fase: 3 · Depende de: 033

## Objetivo
Corregir un fallo: si la primera búsqueda se hace con el índice vacío, `Searcher` guarda una caché vacía sin BM25 y la siguiente búsqueda (ya con chunks) revienta con `AssertionError`.

Reproducción (comprobada):
```python
s = Searcher(store_vacio, embedder, candidate_k=5, rrf_k=60, query_instruction="")
s.search("hola", 3)      # [] y guarda _cache_chunks = {} con _bm25_index = None
store_vacio.add([...], [...])
s.search("hola", 3)      # AssertionError
```

## Archivos
- modificar: `src/docuchat/retrieval/searcher.py` (solo `Searcher.__init__`, `refresh` y `search`)
- modificar: `tests/retrieval/test_searcher.py` (solo AÑADIR un test)

## Comportamiento
1. Sustituye `self._cache_chunks` y `self._bm25_index` por un único atributo:
   `self._cache: tuple[dict[str, Chunk], Bm25Index] | None = None`.
2. `refresh()` → `self._cache = None`.
3. En `search`, si `self._cache is None`: `chunks = self._store.all_chunks()`; si está vacío → `return []` SIN guardar nada (la caché sigue en `None` y la próxima búsqueda vuelve a mirar el store). Si no, `self._cache = ({...}, Bm25Index(ids, textos))`.
4. Después: `cache, bm25 = self._cache` y el resto igual que ahora. Sin `assert` en el código.
5. El mapa de chunks que se actualiza con los `hits` vectoriales puede seguir siendo el dict de la caché.

## Tests obligatorios
Añadir a `tests/retrieval/test_searcher.py`. NO cambies los tests existentes.
1. `test_empty_then_filled`: `Searcher` sobre un `VectorStore` nuevo (vacío) con `KeywordEmbedder` → `search("cafetera", 5) == []`. Después `store.add(CORPUS, KeywordEmbedder().embed([c.text for c in CORPUS]))` y, SIN `refresh`, `search("cafetera", 1)` → un resultado con `chunk_id == "b.pdf#p3#c0"`.

## Aceptación
- [ ] `uv run pytest -q tests/retrieval/test_searcher.py` → 14 passed
- [ ] `uv run pytest -q` pasa entero (264)
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "assert\|_bm25_index\|_cache_chunks" src/docuchat/retrieval/searcher.py` → sin resultados

## Fuera de alcance
Cualquier otro cambio en `searcher.py`, `cli.py` u otros módulos.
