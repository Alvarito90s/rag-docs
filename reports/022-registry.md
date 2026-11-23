# Informe 022 · Registro SQLite de documentos indexados

Estado: COMPLETADA

## Cambio

Se implementó el registro de documentos indexados con persistencia SQLite para
permitir reindexación selectiva basada en hash SHA-256.

### Archivos creados

1. **`src/docuchat/index/registry.py`** — Clase `Registry` con CRUD completo:
   - `__init__`: crea tablas si no existen.
   - `get(source) → RegistryEntry | None`
   - `all() → dict[str, RegistryEntry]` (ordenado por source)
   - `upsert(source, sha256, chunk_count, indexed_at)` con UPSERT por conflicto.
   - `delete(source)`, `clear()`
   - Context manager (`__enter__`/`__exit__`) que cierra la conexión.

2. **`tests/index/test_registry.py`** — 10 tests obligatorios de la spec, todos pasando.

### Archivos modificados

- **`tests/index/test_registry.py`** (después de `ruff format`): se ajustó el orden
  de imports y el formato de una línea de assert.

## Verificación

| Comando | Resultado |
| --- | --- |
| `uv run pytest -q tests/index/test_registry.py` | 10 passed ✅ |
| `uv run pytest -q` | 162 passed ✅ |
| `uv run ruff check .` | All checks passed ✅ |
| `uv run ruff format --check .` | 57 files already formatted ✅ |
| `uv run mypy src` | Success: no issues found ✅ |

## Decisiones que tomé

- Seguí la spec al pie de la letra: dataclass frozen, `sqlite3` del estándar,
  parámetros `?` en todas las consultas, `indexed_at` con `.isoformat(timespec="seconds")`.
- La tabla usa `ON CONFLICT(source) DO UPDATE SET` para el `upsert` como indica la spec.
- `all()` devuelve un `dict` ordenado con `ORDER BY source` en el SQL, como exige la spec.
- El `delete` de un source inexistente no lanza porque `sqlite3.execute("DELETE ... WHERE source = ?")`
  simplemente no afecta filas (0 rows affected es válido).

## Bloqueos y dudas

Ninguno. La spec era clara y todos los tests pasan sin ajustes.
