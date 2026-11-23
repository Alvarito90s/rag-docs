# 024-c · Chroma con ruta absoluta (tests intermitentes)
Fase: 5 · Depende de: 026-b

## Objetivo
Arreglar los fallos intermitentes de la suite (1 de cada 10-20 ejecuciones: `no such table: acquire_write`, `no such table: collections`, `Error purging logs`).

Causa (comprobada): `chromadb.PersistentClient` cachea el cliente por la CADENA de la ruta. Con `data_dir` relativo (`"data"`, tras un `chdir` a un tmp distinto en cada test), todos los tests usan la clave `"data/chroma"` y Chroma reutiliza un cliente que apunta a la carpeta de un test anterior, ya borrada. Con la ruta resuelta a absoluta: 0 fallos en 30 ejecuciones.

## Archivos
- modificar: `src/docuchat/index/vector_store.py` (solo el `PersistentClient` de `__init__`)
- modificar: `src/docuchat/index/indexer.py` (solo el `PersistentClient` de `reset_index`)
- modificar: `tests/index/test_vector_store.py` (solo AÑADIR un test)

## Comportamiento
1. `VectorStore.__init__`: `chromadb.PersistentClient(path=str(path.resolve()), ...)`.
2. `reset_index`: `chromadb.PersistentClient(path=str(settings.chroma_dir.resolve()), ...)`.
3. Nada más cambia.

## Tests obligatorios
Añadir a `tests/index/test_vector_store.py` (sin el arreglo falla siempre con `assert 1 == 0`; comprobado):
```python
def test_relative_path_follows_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Una ruta relativa se resuelve con el cwd de cada momento, no con el de un cliente cacheado."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    chunk = make_chunk("a.md", 1, 0, "hola")
    monkeypatch.chdir(tmp_path / "a")
    first = VectorStore(Path("data/chroma"), "chunks", "m")
    first.add([chunk], [[1.0, 0.0, 0.0]])
    monkeypatch.chdir(tmp_path / "b")
    second = VectorStore(Path("data/chroma"), "chunks", "m")
    assert second.count() == 0
    assert (tmp_path / "b" / "data" / "chroma" / "chroma.sqlite3").exists()
```

## Aceptación
- [ ] `uv run pytest -q tests/index/test_vector_store.py` → 17 passed
- [ ] `uv run pytest -q` pasa entero (387)
- [ ] Estabilidad: `for i in $(seq 1 20); do uv run pytest -q -p no:cacheprovider 2>&1 | grep -E "passed|failed"; done` → 20 líneas `387 passed`, ninguna con `failed`
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "PersistentClient" -A1 src/docuchat/index/*.py` → las dos llamadas usan `.resolve()`

## Fuera de alcance
No cambies `config.py` (las rutas relativas en settings siguen siendo válidas) ni los tests existentes.
