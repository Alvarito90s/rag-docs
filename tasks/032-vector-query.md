# 032 · Búsqueda vectorial en VectorStore
Fase: 3 · Depende de: 024-b

## Objetivo
Añadir a `VectorStore` la consulta de los k chunks más cercanos a un embedding, con su similitud coseno.

## Archivos
- modificar: `src/docuchat/index/vector_store.py` (solo AÑADIR el método `query`)
- modificar: `tests/index/test_vector_store.py` (solo AÑADIR tests)

## Interfaz
```python
def query(self, embedding: Sequence[float], k: int) -> list[tuple[Chunk, float]]:
    """Los k chunks más cercanos con su similitud coseno (1 - distancia), de mayor a menor."""
```

## Comportamiento
1. Si `k <= 0` o `self.count() == 0` → `[]` (sin llamar a Chroma).
2. `n = min(k, self.count())`; `self._collection.query(query_embeddings=[list(embedding)], n_results=n, include=["documents", "metadatas", "distances"])`.
3. Del resultado usa el índice `[0]` de `ids`, `documents`, `metadatas` y `distances` (una sola consulta). Recorre con `zip(..., strict=True)` y reconstruye cada chunk con `chunk_from_record`.
4. Devuelve `(chunk, 1.0 - float(distancia))` en el orden de Chroma (de más a menos similar). La colección ya usa espacio coseno.

## Tests obligatorios
Añadir a `tests/index/test_vector_store.py` (usa el helper `make_chunk` existente). NO cambies los valores esperados ni los tests existentes.
Datos de los tests 1–3:
```python
chunks = [make_chunk("a.pdf", 1, 0, "uno"), make_chunk("a.pdf", 1, 1, "dos"), make_chunk("b.md", 1, 0, "tres")]
vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.7071, 0.7071, 0.0]]
```
1. `query([1.0, 0.0, 0.0], 2)` → ids `["a.pdf#p1#c0", "b.md#p1#c0"]`, similitudes `pytest.approx([1.0, 0.7071], abs=1e-3)`.
2. `query([1.0, 0.0, 0.0], 10)` → 3 resultados (k mayor que la colección no falla); el último es `"a.pdf#p1#c1"`.
3. El chunk devuelto es igual al original: `query([0.0, 1.0, 0.0], 1)[0][0] == chunks[1]`.
4. `query([1.0, 0.0, 0.0], 0) == []` con la colección llena.
5. Store vacío: `query([1.0, 0.0, 0.0], 5) == []`.

## Referencia de librerías
ChromaDB 1.5.x (comprobado; `n_results` mayor que la colección devuelve todos):
```python
res = collection.query(
    query_embeddings=[[1.0, 0.0, 0.0]],
    n_results=2,
    include=["documents", "metadatas", "distances"],
)
res["ids"][0]        # ['a.pdf#p1#c0', 'b.md#p1#c0']
res["distances"][0]  # [0.0, 0.29...]  (coseno: distancia = 1 - similitud)
```
Si mypy se queja de los tipos opcionales de `res["documents"]` etc., usa `or []` como en `all_chunks`; no uses `# type: ignore` salvo que no haya otra forma, y explícalo en el informe.

## Aceptación
- [ ] `uv run pytest -q tests/index/test_vector_store.py` → 16 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
No cambies los demás métodos de `VectorStore`. Nada de instrucciones de consulta ni de BM25 (spec 033).
