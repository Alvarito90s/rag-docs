# Informe 032 · Búsqueda vectorial en VectorStore
Estado: COMPLETADA

## Cambios
- `src/docuchat/index/vector_store.py`: añadido método `query(self, embedding, k) -> list[tuple[Chunk, float]]` que consulta los k chunks más cercanos a un embedding usando ChromaDB con espacio coseno, devolviendo similitud como `1.0 - distancia`.
- `tests/index/test_vector_store.py`: añadidos 5 tests (12–16) cubriendo query con top-k, k mayor que la colección, chunk igual al original, k=0 y store vacío.

## Verificación
```
uv run pytest -q tests/index/test_vector_store.py → 16 passed
uv run pytest -q → 240 passed, 5 warnings
uv run ruff check . → All checks passed!
uv run ruff format --check . → 80 files already formatted
uv run mypy src → Success: no issues found in 20 source files
```

## Decisiones que tomé
- Ninguna: la spec era completa y sin ambigüedades. Se siguió al pie de la letra la interfaz, comportamiento y tests descritos.

## Bloqueos y dudas
- Ninguno.
