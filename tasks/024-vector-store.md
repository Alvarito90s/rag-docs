# 024 · Base vectorial con ChromaDB
Fase: 2 · Depende de: 020

## Objetivo
Envolver ChromaDB en una clase pequeña: guardar chunks con sus embeddings, borrarlos por documento y leerlos todos. Si cambia el modelo de embeddings, avisar en vez de mezclar vectores incompatibles.

## Archivos
- modificar: `pyproject.toml` y `uv.lock`, SOLO con: `uv add "chromadb>=1.5,<2"`
- crear: `src/docuchat/index/vector_store.py`
- crear: `tests/index/test_vector_store.py`

## Interfaz
```python
from collections.abc import Sequence
from pathlib import Path

import chromadb
from chromadb.api.types import Metadata
from chromadb.config import Settings as ChromaSettings

from docuchat.models import Chunk

ADD_BATCH = 1000  # Chroma limita el tamaño de cada add (~5000)


class EmbeddingModelMismatchError(RuntimeError):
    """La colección se creó con otro modelo de embeddings."""


class VectorStore:
    """Colección persistente de chunks en ChromaDB (distancia coseno)."""

    def __init__(self, path: Path, collection_name: str, embedding_model: str) -> None: ...
    def add(self, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]) -> None: ...
    def delete_source(self, source: str) -> None: ...
    def count(self) -> int: ...
    def sources(self) -> set[str]: ...
    def all_chunks(self) -> list[Chunk]: ...
    def reset(self) -> None: ...


def chunk_to_metadata(chunk: Chunk) -> Metadata: ...
def chunk_from_record(chunk_id: str, text: str, metadata: Metadata) -> Chunk: ...
```

## Comportamiento
1. `__init__`: `path.mkdir(parents=True, exist_ok=True)`; cliente `chromadb.PersistentClient(path=str(path), settings=ChromaSettings(anonymized_telemetry=False))`; colección con `_open_collection()` (método privado):
```python
self._client.get_or_create_collection(
    name=self._name,
    embedding_function=None,  # los embeddings los damos nosotros
    configuration={"hnsw": {"space": "cosine"}},
    metadata={"embedding_model": self._model},
)
```
   Si la colección ya existía, Chroma devuelve SU metadata original. Si `collection.metadata["embedding_model"] != embedding_model` → `EmbeddingModelMismatchError(f"El índice se creó con '{guardado}' y ahora se usa '{embedding_model}'. Reindexa con --reset.")`.
2. `chunk_to_metadata`: `{"source", "doc_sha256", "page", "position", "heading"}`; `heading` se guarda como `chunk.heading or ""` (Chroma NO admite `None` en metadatos).
3. `chunk_from_record`: inverso; `heading=metadata["heading"] or None`. Convierte con `str(...)`/`int(...)` para que mypy quede contento.
4. `add`: si `len(chunks) != len(embeddings)` → `ValueError`; lista vacía → no hace nada. Añade en tandas de `ADD_BATCH` con `collection.add(ids=..., embeddings=..., documents=[c.text ...], metadatas=[chunk_to_metadata(c) ...])`.
5. `delete_source`: `collection.delete(where={"source": source})`. Si no hay chunks de ese `source`, no falla.
6. `count`: `collection.count()`.
7. `sources`: conjunto de `metadata["source"]` de `collection.get(include=["metadatas"])`.
8. `all_chunks`: `collection.get(include=["documents", "metadatas"])` → `Chunk` con `chunk_from_record`, ordenados por `(source, page, position)`.
9. `reset`: `self._client.delete_collection(self._name)` y vuelve a crearla con `_open_collection()`.

## Tests obligatorios
`tests/index/test_vector_store.py`, todo en `tmp_path`, embeddings inventados de dimensión 3. Helper `make_chunk(source, page, position, text, heading=None)` con `doc_sha256="a" * 64` y `chunk_id=make_chunk_id(...)`. NO cambies los valores esperados.
1. Store nuevo → `count() == 0`, `sources() == set()`, `all_chunks() == []`.
2. `add` de 3 chunks (2 de `"a.pdf"`, 1 de `"b.md"`) → `count() == 3`, `sources() == {"a.pdf", "b.md"}`.
3. `all_chunks()` devuelve chunks iguales (`==`) a los añadidos, en orden `(source, page, position)`, aunque se añadan desordenados.
4. `heading=None` vuelve como `None`; `heading="Puertos"` vuelve como `"Puertos"`.
5. `delete_source("a.pdf")` → `count() == 1`, `sources() == {"b.md"}`; `delete_source("no.pdf")` no lanza.
6. Persistencia: añadir, crear OTRO `VectorStore` sobre la misma carpeta y modelo → `count()` igual.
7. Modelo distinto: crear con `"m1"`, añadir, abrir con `"m2"` → `EmbeddingModelMismatchError`.
8. `reset()` → `count() == 0`; después se puede volver a añadir.
9. `add` con 2 chunks y 1 embedding → `ValueError`.
10. `add([], [])` no falla y `count() == 0`.
11. Tandas: con `monkeypatch.setattr("docuchat.index.vector_store.ADD_BATCH", 2)`, añadir 5 chunks → `count() == 5`.

## Referencia de librerías
ChromaDB 1.5 (verificado con 1.5.9 y `mypy --strict`):
```python
import chromadb
from chromadb.api.types import Metadata
from chromadb.config import Settings as ChromaSettings

client = chromadb.PersistentClient(
    path="data/chroma", settings=ChromaSettings(anonymized_telemetry=False)
)
col = client.get_or_create_collection(
    name="chunks",
    embedding_function=None,
    configuration={"hnsw": {"space": "cosine"}},
    metadata={"embedding_model": "m1"},
)
col.metadata  # {"embedding_model": "m1"} (la ORIGINAL si ya existía)
metas: list[Metadata] = [{"source": "a.pdf", "page": 1, "heading": ""}]  # None NO se admite
col.add(ids=["a.pdf#p1#c0"], embeddings=[[0.1, 0.2, 0.3]], documents=["texto"], metadatas=metas)
col.count()
col.delete(where={"source": "a.pdf"})
g = col.get(include=["documents", "metadatas"])
ids = g["ids"]
docs = g["documents"] or []
metas_out = g["metadatas"] or []
client.delete_collection("chunks")
# Dimensión distinta en un add -> chromadb.errors.InvalidArgumentError
```

## Aceptación
- [ ] `uv run pytest -q tests/index/test_vector_store.py` pasa
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Búsqueda (`query`, Fase 3), filtros por carpeta, otros backends.
