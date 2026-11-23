# Informe spec 031 · Fusión RRF y deduplicación de chunks contiguos

## Resumen
Implementados los módulos de fusión de rankings con Reciprocal Rank Fusion (RRF) y deduplicación de chunks contiguos.

## Archivos creados
| Archivo | Descripción |
| --- | --- |
| `src/docuchat/retrieval/__init__.py` | Paquete de recuperación (docstring) |
| `src/docuchat/retrieval/fusion.py` | `rrf_fuse()` + `drop_adjacent()` |
| `tests/retrieval/__init__.py` | Paquete de tests |
| `tests/retrieval/test_fusion.py` | 10 tests obligatorios |

## Resultados
- `uv run pytest -q tests/retrieval/test_fusion.py` → **10 passed**
- `uv run pytest -q` → **235 passed** (225 anteriores + 10 nuevos)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → 79 files already formatted
- `uv run mypy src` → success, no issues found in 20 source files

## Bloqueos
Ninguno. Todo implementado y verificando correctamente.

## Notas
- La única corrección fue ajustar las assertions `pytest.approx` en los tests de empate y duplicados, ya que `pytest.approx` no soporta listas de tuplas; se separan ids y scores en assertions independientes.
