"""Indexador incremental: sincroniza una carpeta con VectorStore + Registry + FTS."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType

import chromadb
from chromadb.config import Settings as ChromaSettings

from docuchat.config import Settings
from docuchat.index.chunker import chunk_document
from docuchat.index.contextualizer import (
    ChunkContextualizer,
    make_contextualizer,
    make_meta_contextualizer,
)
from docuchat.index.embeddings import Embedder, make_embedder
from docuchat.index.fts import FtsIndex
from docuchat.index.registry import Registry
from docuchat.index.vector_store import VectorStore
from docuchat.ingest.scanner import file_sha256, load_document, scan_folder
from docuchat.models import index_text

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
    fts_synced: list[str] = field(default_factory=list)
    contexts_generated: int = 0


def sync_fts(store: VectorStore, fts: FtsIndex) -> list[str]:
    """Deja en FTS las mismas fuentes que en Chroma; devuelve las rellenadas (orden alfabético)."""
    en_chroma = store.sources()
    en_fts = fts.sources()
    # Borrar restos en FTS que no están en Chroma
    for source in sorted(en_fts - en_chroma):
        fts.delete_source(source)
    # Rellenar lo que falta
    faltan = sorted(en_chroma - en_fts)
    if faltan:
        fts.add([c for c in store.all_chunks() if c.source in set(faltan)])
    return faltan


class Indexer:
    """Indexa una carpeta de forma incremental en VectorStore + Registry."""

    def __init__(
        self,
        store: VectorStore,
        registry: Registry,
        embedder: Embedder,
        chunk_size: int,
        chunk_overlap: int,
        fts: FtsIndex | None = None,
        contextualizer: ChunkContextualizer | None = None,
    ) -> None:
        self._store = store
        self._registry = registry
        self._embedder = embedder
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._fts = fts
        self._contextualizer = contextualizer

    def index_folder(self, root: Path, on_progress: ProgressCallback | None = None) -> IndexStats:
        """Sincroniza el índice con los archivos de root."""
        paths = scan_folder(root)
        total = len(paths)
        scanned_sources: set[str] = set()

        # Sincronizar FTS al inicio
        synced: list[str] = []
        if self._fts is not None:
            synced = sync_fts(self._store, self._fts)

        # Leer fuentes presentes en Chroma (una sola vez al inicio)
        present = self._store.sources()

        added: list[str] = []
        updated: list[str] = []
        unchanged: list[str] = []
        errors: list[tuple[str, str]] = []
        chunks_added = 0
        llm_calls_start = self._contextualizer.llm_calls if self._contextualizer is not None else 0

        for i, path in enumerate(paths, start=1):
            source = path.resolve().relative_to(root.resolve()).as_posix()
            sha = file_sha256(path)
            entry = self._registry.get(source)

            # b) Sin cambios → solo si está en el store (o chunk_count == 0)
            if (
                entry is not None
                and entry.sha256 == sha
                and (entry.chunk_count == 0 or source in present)
            ):
                unchanged.append(source)
                scanned_sources.add(source)
                if on_progress is not None:
                    on_progress(source, i, total)
                continue

            # c) Cargar y chunkear
            try:
                doc = load_document(path, root)
                chunks = chunk_document(doc, self._chunk_size, self._chunk_overlap)
                if self._contextualizer is not None and chunks:
                    chunks = [
                        c.model_copy(update={"context": self._contextualizer.context_for(doc, c)})
                        for c in chunks
                    ]
            except Exception as e:
                errors.append((source, f"{type(e).__name__}: {e}"))
                scanned_sources.add(source)
                if on_progress is not None:
                    on_progress(source, i, total)
                continue

            # d) Embedding
            vectors = self._embedder.embed([index_text(c) for c in chunks]) if chunks else []

            # e) Guardar en store y registry
            self._store.delete_source(source)
            self._store.add(chunks, vectors)
            self._registry.upsert(source, sha, len(chunks))

            # e1) Guardar en FTS
            if self._fts is not None:
                self._fts.delete_source(source)
                self._fts.add(chunks)

            # f) Categorizar
            if entry is None:
                added.append(source)
            else:
                updated.append(source)
            chunks_added += len(chunks)
            scanned_sources.add(source)

            # g) Progreso
            if on_progress is not None:
                on_progress(source, i, total)

        # 2) Archivos eliminados: sources del registry no escaneados (orden alfabético)
        removed: list[str] = []
        for source in sorted(self._registry.all()):
            if source not in scanned_sources:
                self._store.delete_source(source)
                self._registry.delete(source)
                if self._fts is not None:
                    self._fts.delete_source(source)
                removed.append(source)

        return IndexStats(
            added=added,
            updated=updated,
            unchanged=unchanged,
            removed=removed,
            errors=errors,
            chunks_added=chunks_added,
            fts_synced=synced,
            contexts_generated=(
                (self._contextualizer.llm_calls - llm_calls_start)
                if self._contextualizer is not None
                else 0
            ),
        )

    def chunk_count(self) -> int:
        """Número de chunks en la base vectorial."""
        return self._store.count()

    def close(self) -> None:
        """Cierra el registro."""
        self._registry.close()

    def __enter__(self) -> "Indexer":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


def build_indexer(settings: Settings, embedder: Embedder | None = None) -> Indexer:
    """Crea el Indexer con las rutas, modelo y chunking de settings."""
    store = VectorStore(settings.chroma_dir, settings.chroma_collection, settings.embedding_model)
    registry = Registry(settings.registry_path)
    fts = FtsIndex(settings.fts_path)
    if embedder is None:
        embedder = make_embedder(settings)
    contextualizer: ChunkContextualizer | None
    if settings.contextual_enabled:
        contextualizer = make_contextualizer(settings)
    elif settings.contextual_meta_enabled:
        contextualizer = make_meta_contextualizer(settings)
    else:
        contextualizer = None
    return Indexer(
        store=store,
        registry=registry,
        embedder=embedder,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        fts=fts,
        contextualizer=contextualizer,
    )


def reset_index(settings: Settings) -> None:
    """Borra la colección de Chroma, vacía el registro y FTS."""
    client = chromadb.PersistentClient(
        path=str(settings.chroma_dir.resolve()),
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    collection_names = {c.name for c in client.list_collections()}
    if settings.chroma_collection in collection_names:
        client.delete_collection(settings.chroma_collection)
    with Registry(settings.registry_path) as reg:
        reg.clear()
    FtsIndex(settings.fts_path).clear()
