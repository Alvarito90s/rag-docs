"""Envoltorio de ChromaDB para almacenar chunks con sus embeddings."""

from collections.abc import Sequence
from pathlib import Path
from typing import cast

import chromadb
from chromadb.api.types import Metadata
from chromadb.config import Settings as ChromaSettings

from docuchat.models import Chunk

ADD_BATCH = 1000  # Chroma limita el tamaño de cada add (~5000)


class EmbeddingModelMismatchError(RuntimeError):
    """La colección se creó con otro modelo de embeddings."""


class VectorStore:
    """Colección persistente de chunks en ChromaDB (distancia coseno)."""

    def __init__(
        self,
        path: Path,
        collection_name: str,
        embedding_model: str,
    ) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(path.resolve()),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._model = embedding_model
        self._name = collection_name
        self._collection = self._open_collection()

    def _open_collection(self) -> chromadb.Collection:
        """Abre o crea la colección; verifica el modelo de embeddings."""
        col = self._client.get_or_create_collection(
            name=self._name,
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
            metadata={"embedding_model": self._model},
        )
        guardado = col.metadata.get("embedding_model")
        if guardado is not None and guardado != self._model:
            raise EmbeddingModelMismatchError(
                f"El índice se creó con '{guardado}' y ahora se usa '{self._model}'. "
                "Reindexa con --reset."
            )
        return col

    def add(
        self,
        chunks: Sequence[Chunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks y embeddings deben tener la misma longitud")
        if len(chunks) == 0:
            return

        for i in range(0, len(chunks), ADD_BATCH):
            batch_chunks = chunks[i : i + ADD_BATCH]
            batch_embs = embeddings[i : i + ADD_BATCH]
            self._collection.add(
                ids=[c.chunk_id for c in batch_chunks],
                embeddings=cast(list[list[float]], batch_embs),  # type: ignore[arg-type]
                documents=[c.text for c in batch_chunks],
                metadatas=[chunk_to_metadata(c) for c in batch_chunks],
            )

    def delete_source(self, source: str) -> None:
        self._collection.delete(where={"source": source})

    def count(self) -> int:
        return self._collection.count()

    def sources(self) -> set[str]:
        result = self._collection.get(include=["metadatas"])
        metadatas = result["metadatas"] or []
        return {str(m["source"]) for m in metadatas}

    def all_chunks(self) -> list[Chunk]:
        result = self._collection.get(include=["documents", "metadatas"])
        ids = result["ids"]
        docs = result["documents"] or []
        metadatas = result["metadatas"] or []
        chunks = [
            chunk_from_record(cid, doc, meta)
            for cid, doc, meta in zip(ids, docs, metadatas, strict=True)
        ]
        return sorted(chunks, key=lambda c: (c.source, c.page, c.position))

    def get_chunks(self, ids: Sequence[str]) -> list[Chunk]:
        """Los chunks de esos ids, en el orden pedido; los que no existen se omiten."""
        if not ids:
            return []
        unicos = list(dict.fromkeys(ids))
        result = self._collection.get(ids=unicos, include=["documents", "metadatas"])
        db_ids = result["ids"]
        docs = result["documents"] or []
        metadatas = result["metadatas"] or []
        por_id = {
            cid: chunk_from_record(cid, doc, meta)
            for cid, doc, meta in zip(db_ids, docs, metadatas, strict=True)
        }
        return [por_id[i] for i in unicos if i in por_id]

    def reset(self) -> None:
        self._client.delete_collection(self._name)
        self._collection = self._open_collection()

    def query(self, embedding: Sequence[float], k: int) -> list[tuple[Chunk, float]]:
        """Los k chunks más cercanos con su similitud coseno (1 - distancia),
        de mayor a menor."""
        if k <= 0 or self.count() == 0:
            return []
        n = min(k, self.count())
        result = self._collection.query(
            query_embeddings=[list(embedding)],  # type: ignore[arg-type]
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        ids = result["ids"][0]
        docs = (result["documents"][0] if result["documents"] else []) or []
        metadatas = (result["metadatas"][0] if result["metadatas"] else []) or []
        distances = (result["distances"][0] if result["distances"] else []) or []
        return [
            (chunk_from_record(cid, doc, meta), 1.0 - float(dist))
            for cid, doc, meta, dist in zip(ids, docs, metadatas, distances, strict=True)
        ]


def chunk_to_metadata(chunk: Chunk) -> Metadata:
    """Convierte un Chunk en metadatos de Chroma (heading → "" si None)."""
    return {
        "source": chunk.source,
        "doc_sha256": chunk.doc_sha256,
        "page": str(chunk.page),
        "position": str(chunk.position),
        "heading": chunk.heading or "",
        "context": chunk.context,
    }


def chunk_from_record(
    chunk_id: str,
    text: str,
    metadata: Metadata,
) -> Chunk:
    """Reconstruye un Chunk a partir de un registro de Chroma."""
    page_val = metadata["page"]
    pos_val = metadata["position"]
    page_str = str(page_val) if not isinstance(page_val, str) else page_val
    pos_str = str(pos_val) if not isinstance(pos_val, str) else pos_val
    return Chunk(
        chunk_id=chunk_id,
        source=metadata["source"],
        doc_sha256=metadata["doc_sha256"],
        page=int(page_str),
        position=int(pos_str),
        heading=metadata.get("heading") or None,
        text=text,
        context=str(metadata.get("context") or ""),
    )
