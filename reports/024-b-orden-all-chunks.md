# Informe 024-b · VectorStore.all_chunks: devolver en orden
Estado: COMPLETADA

## Cambios
- `src/docuchat/index/vector_store.py`: `all_chunks` ahora ordena el resultado con `key=lambda c: (c.source, c.page, c.position)` y el `zip` usa `strict=True`.
- `tests/index/test_vector_store.py`: reescrito solo el test 3 (`test_all_chunks_sorted`); añade los chunks en el orden `b.md p1 c0`, `a.pdf p2 c0`, `a.pdf p1 c1`, `a.pdf p1 c0` y comprueba el orden `[("a.pdf", 1, 0), ("a.pdf", 1, 1), ("a.pdf", 2, 0), ("b.md", 1, 0)]`.
- `docs/STATE.md`: actualizado con la spec 024-b.

## Verificación
- Test 3 sin el `sorted` (eliminado temporalmente, luego restaurado): FALLA, como exige la spec.
  `FAILED tests/index/test_vector_store.py::test_all_chunks_sorted` — `At index 0 diff: ('b.md', 1, 0) != ('a.pdf', 1, 0)` (1 failed, 10 passed).
- Con el `sorted` restaurado: `uv run pytest -q tests/index/test_vector_store.py` → 11 passed.
- `uv run pytest -q` → 194 passed, 5 warnings (DeprecationWarning de swigvarlink, preexistente).
- `uv run ruff check .` → All checks passed!
- `uv run ruff format --check .` → 69 files already formatted.
- `uv run mypy src` → Success: no issues found in 17 source files.

## Decisiones que tomé
- Textos de los chunks del test 3 ("texto b1", "texto a2", ...) elegidos libremente; la spec solo fija source/page/position.
- Embeddings de dimensión 3 con el helper `make_embeddings` existente.

## Bloqueos y dudas
Ninguno.
