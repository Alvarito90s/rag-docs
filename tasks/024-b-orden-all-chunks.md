# 024-b · VectorStore.all_chunks: devolver en orden
Fase: 2 · Depende de: 024

## Objetivo
`all_chunks()` no ordena: devuelve los chunks en el orden en que Chroma los guarda. La spec 024 (punto 8) exige orden `(source, page, position)`, y el test 3 no lo detecta porque añade los chunks ya ordenados.

## Archivos
- modificar: `src/docuchat/index/vector_store.py` (solo `all_chunks`)
- modificar: `tests/index/test_vector_store.py` (solo el test 3)

## Comportamiento
1. `all_chunks` ordena el resultado con `key=lambda c: (c.source, c.page, c.position)`.
2. En el `zip` usa `strict=True` (si Chroma devolviera listas de distinta longitud, debe fallar, no truncar en silencio).
3. Test 3, reescrito: añade en ESTE orden `b.md p1 c0`, `a.pdf p2 c0`, `a.pdf p1 c1`, `a.pdf p1 c0` → `[ (c.source, c.page, c.position) for c in all_chunks() ] == [("a.pdf", 1, 0), ("a.pdf", 1, 1), ("a.pdf", 2, 0), ("b.md", 1, 0)]`.

## Aceptación
- [ ] `uv run pytest -q tests/index/test_vector_store.py` pasa
- [ ] El test 3 FALLA si quitas el `sorted` (compruébalo y dilo en el informe)
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Todo lo demás.
