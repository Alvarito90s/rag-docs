# 026 · Indexador incremental
Fase: 2 · Depende de: 014-c, 021, 022, 023, 024-b

## Objetivo
Unir scanner, chunker, embeddings, VectorStore y Registry en un indexador incremental: solo reindexa los archivos nuevos o con otro hash y borra del índice los que ya no existen.

## Archivos
- crear: `src/docuchat/index/indexer.py`
- crear: `tests/index/test_indexer.py`

## Interfaz
```python
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType

import chromadb
from chromadb.config import Settings as ChromaSettings

from docuchat.config import Settings
from docuchat.index.chunker import chunk_document
from docuchat.index.embeddings import Embedder, make_embedder
from docuchat.index.registry import Registry
from docuchat.index.vector_store import VectorStore
from docuchat.ingest.scanner import file_sha256, load_document, scan_folder

ProgressCallback = Callable[[str, int, int], None]  # (source, hechos, total)


@dataclass(frozen=True)
class IndexStats:
    """Resultado de una pasada de indexación (listas de sources)."""

    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)  # (source, mensaje)
    chunks_added: int = 0


class Indexer:
    """Indexa una carpeta de forma incremental en VectorStore + Registry."""

    def __init__(
        self,
        store: VectorStore,
        registry: Registry,
        embedder: Embedder,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None: ...
    def index_folder(self, root: Path, on_progress: ProgressCallback | None = None) -> IndexStats:
        """Sincroniza el índice con los archivos de root."""
    def chunk_count(self) -> int:
        """Número de chunks en la base vectorial."""
    def close(self) -> None:
        """Cierra el registro."""
    def __enter__(self) -> "Indexer": ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


def build_indexer(settings: Settings, embedder: Embedder | None = None) -> Indexer:
    """Crea el Indexer con las rutas, modelo y chunking de settings."""


def reset_index(settings: Settings) -> None:
    """Borra la colección de Chroma y vacía el registro."""
```

## Comportamiento
1. `index_folder(root)`: recorre `scan_folder(root)` en su orden. Para cada `path`:
   a. `source = path.resolve().relative_to(root.resolve()).as_posix()` y `sha = file_sha256(path)`.
   b. `entry = registry.get(source)`. Si `entry` existe y `entry.sha256 == sha` → `unchanged`; no se carga ni se llama al embedder.
   c. Si no: dentro de `try`, `doc = load_document(path, root)` y `chunks = chunk_document(doc, chunk_size, chunk_overlap)`. Cualquier `Exception` en ESOS DOS pasos → `errors.append((source, f"{type(e).__name__}: {e}"))` y sigue con el siguiente archivo (sin tocar su índice ni su registro).
   d. `vectors = embedder.embed([c.text for c in chunks])` si hay chunks; si `chunks` está vacío NO llames al embedder (`vectors = []`). Los errores del embedder (`OpenAIError`, `EmbeddingError`) NO se capturan: se propagan y paran la pasada.
   e. Solo después de tener los vectores: `store.delete_source(source)`, `store.add(chunks, vectors)`, `registry.upsert(source, sha, len(chunks))`. Este orden garantiza que, si falla el embedder, el índice anterior del archivo sigue intacto.
   f. `added` si `entry` era `None`; `updated` si existía. `chunks_added += len(chunks)`.
   g. Tras cada archivo (sea cual sea el resultado, también `unchanged` y errores), si hay `on_progress`, llama a `on_progress(source, i, total)` con `i` de 1 a `total = len(paths)`.
2. Tras el bucle: cada `source` de `registry.all()` que no esté entre los escaneados (orden alfabético) → `store.delete_source(source)`, `registry.delete(source)`, `removed`. Un archivo que dio error SÍ cuenta como escaneado: no se borra su índice anterior.
3. Devuelve `IndexStats` con las listas en el orden en que se procesaron.
4. `chunk_count()` → `store.count()`. `close()` → `registry.close()`. `__exit__` llama a `close()`.
5. `build_indexer`: crea PRIMERO `VectorStore(settings.chroma_dir, settings.chroma_collection, settings.embedding_model)` (puede lanzar `EmbeddingModelMismatchError`; no lo captures), luego `Registry(settings.registry_path)` y usa `embedder` o, si es `None`, `make_embedder(settings)`. `chunk_size`/`chunk_overlap` de settings.
6. `reset_index`: abre `chromadb.PersistentClient(path=str(settings.chroma_dir), settings=ChromaSettings(anonymized_telemetry=False))`; si `settings.chroma_collection` está en `{c.name for c in client.list_collections()}`, `client.delete_collection(...)`. Después `with Registry(settings.registry_path) as reg: reg.clear()`. NO borres carpetas con `shutil.rmtree`: Chroma cachea el cliente por ruta y el índice queda corrupto (comprobado).

## Tests obligatorios
`tests/index/test_indexer.py`. NO cambies los valores esperados. Nada de red: embedder falso.
```python
class FakeEmbedder:
    def __init__(self, fail_on: str | None = None) -> None:
        self.calls: list[list[str]] = []
        self.fail_on = fail_on

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self.fail_on is not None and any(self.fail_on in t for t in texts):
            raise APIConnectionError(request=httpx.Request("POST", "http://test"))
        return [[float(len(t)), 1.0, 0.5] for t in texts]
```
Fixture `docs(tmp_path)`: carpeta `tmp_path / "docs"` con:
- `a.md` = `"# Alfa\n\nPrimer párrafo de alfa.\n\n## Beta\n\nTexto de beta.\n"` (2 chunks)
- `b.txt` = `"Notas de la reunión.\n"` (1 chunk)

Fixture `indexer(tmp_path)`: `Indexer(VectorStore(tmp_path / "chroma", "chunks", "fake"), Registry(tmp_path / "r.sqlite3"), FakeEmbedder(), 800, 120)`; ciérralo al final. Para inspeccionar, guarda store, registry y embedder en variables del test (o en atributos del fixture).

1. Primera pasada → `added == ["a.md", "b.txt"]`, `updated == unchanged == removed == []`, `errors == []`, `chunks_added == 3`, `chunk_count() == 3`; ids de `store.all_chunks()` == `["a.md#p1#c0", "a.md#p2#c0", "b.txt#p1#c0"]`; `registry.get("a.md").chunk_count == 2`.
2. Segunda pasada sin cambios → `unchanged == ["a.md", "b.txt"]`, `chunks_added == 0`, el embedder no recibe llamadas nuevas (`len(calls)` igual que tras la primera).
3. Reescribir `b.txt` con `"Notas nuevas.\n\nSegundo párrafo.\n"` → `updated == ["b.txt"]`, `unchanged == ["a.md"]`, `chunk_count() == 3`; los chunks de `b.txt` son exactamente `[("b.txt#p1#c0", "Notas nuevas.\n\nSegundo párrafo.")]` (id, texto); `registry.get("b.txt").sha256 == file_sha256(docs / "b.txt")`.
4. Borrar `a.md` → `removed == ["a.md"]`, `store.sources() == {"b.txt"}`, `registry.get("a.md") is None`, `chunk_count() == 1`.
5. Añadir `roto.pdf` con `b"no es un pdf"` → `errors[0][0] == "roto.pdf"`, `errors[0][1].startswith("FileDataError")`, `added == ["a.md", "b.txt"]`, `registry.get("roto.pdf") is None`. Segunda pasada: sigue en `errors`, `removed == []`.
6. Archivo vacío `vacio.txt` (`""`) junto a `a.md` y `b.txt` → `added == ["a.md", "b.txt", "vacio.txt"]`, `registry.get("vacio.txt").chunk_count == 0`, ninguna llamada del embedder con lista vacía (`[] not in calls`).
7. Fallo del embedder: `FakeEmbedder(fail_on="Notas")` → `pytest.raises(APIConnectionError)`; después `registry.get("a.md")` existe, `registry.get("b.txt") is None`, `chunk_count() == 2`. Nueva pasada con otro `Indexer` sobre el mismo store y registry y `FakeEmbedder()` → `unchanged == ["a.md"]`, `added == ["b.txt"]`.
8. Fallo del embedder en una actualización conserva lo anterior: primera pasada correcta; reescribe `b.txt` con `"Notas cambiadas.\n"`; pasada con `FakeEmbedder(fail_on="Notas")` → lanza; los chunks de `b.txt` siguen siendo `[("b.txt#p1#c0", "Notas de la reunión.")]`.
9. Progreso: `calls = []`, `on_progress=lambda s, i, n: calls.append((s, i, n))` con `roto.pdf` añadido → `calls == [("a.md", 1, 3), ("b.txt", 2, 3), ("roto.pdf", 3, 3)]`.
10. Samples: `shutil.copytree(SAMPLES, tmp_path / "s")` → 7 `added` (orden alfabético), `chunks_added == 26`, `chunk_count() == 26`.
11. `build_indexer(settings, embedder=FakeEmbedder())` con el fixture `settings` de `conftest.py` → indexa `docs`, `added == ["a.md", "b.txt"]`; existen `settings.chroma_dir` y `settings.registry_path`.
12. `reset_index`: tras el 11 y `close()`, `reset_index(settings)`; un nuevo `build_indexer(settings, embedder=FakeEmbedder())` → `chunk_count() == 0` y `registry.all() == {}` (abre `Registry(settings.registry_path)` para mirarlo); otra pasada → `added == ["a.md", "b.txt"]`.
13. `reset_index` permite cambiar de modelo: tras indexar con el modelo por defecto, `Settings(embedding_model="otro")` → `build_indexer` lanza `EmbeddingModelMismatchError`; tras `reset_index(...)` con esa Settings, `build_indexer` funciona y `chunk_count() == 0`.
14. `reset_index` sobre una carpeta sin índice (data_dir vacío) no lanza.

## Referencia de librerías
Error de conexión para el fake (igual que en `test_embeddings.py`):
```python
import httpx
from openai import APIConnectionError

APIConnectionError(request=httpx.Request("POST", "http://test"))
```
ChromaDB 1.5.x (comprobado):
```python
client = chromadb.PersistentClient(path="data/chroma", settings=ChromaSettings(anonymized_telemetry=False))
[c.name for c in client.list_collections()]  # ['chunks']
client.delete_collection("chunks")  # lanza si no existe: compruébalo antes
```

## Aceptación
- [ ] `uv run pytest -q tests/index/test_indexer.py` → 14 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "rmtree" src/docuchat/index/indexer.py` → sin resultados
- [ ] `grep -n "except" src/docuchat/index/indexer.py` → un único `except Exception`, el del paso 1c

## Fuera de alcance
No toques la CLI (spec 027), ni `vector_store.py`, `registry.py`, `embeddings.py` o `chunker.py`. Sin hilos ni paralelismo. Sin prefijo de instrucción en los embeddings (los documentos no lo llevan; las consultas, en la Fase 3).
