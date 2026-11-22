"""Escaneo recursivo de carpeta: elige loader por extensión y construye Document."""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from docuchat.ingest.docx_loader import load_docx
from docuchat.ingest.pdf_loader import load_pdf
from docuchat.ingest.text_loader import load_markdown, load_txt
from docuchat.models import DocType, Document, Page

Loader = Callable[[Path], list[Page]]

LOADERS: dict[str, tuple[DocType, Loader]] = {
    ".pdf": (DocType.PDF, load_pdf),
    ".docx": (DocType.DOCX, load_docx),
    ".md": (DocType.MD, load_markdown),
    ".txt": (DocType.TXT, load_txt),
}


class UnsupportedFileError(ValueError):
    """Extensión sin loader."""


@dataclass(frozen=True)
class IngestResult:
    """Documentos cargados y errores (source, mensaje) de una carpeta."""

    documents: list[Document] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)


def file_sha256(path: Path) -> str:
    """SHA-256 en hexadecimal (minúsculas) del contenido del archivo, leído en bloques de 1 MiB."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def is_supported(path: Path) -> bool:
    """Indica si la extensión (sin distinguir mayúsculas) tiene loader."""
    return path.suffix.lower() in LOADERS


def scan_folder(root: Path) -> list[Path]:
    """Archivos soportados bajo root (recursivo), ordenados por su ruta relativa."""
    if not root.exists():
        raise FileNotFoundError(f"No existe: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"No es una carpeta: {root}")
    result: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        parts = rel.parts
        # Ocultos: cualquier parte que empieza por "."
        if any(p.startswith(".") for p in parts):
            continue
        # Temporales Office (~$) solo en el nombre del archivo
        if path.name.startswith("~$"):
            continue
        if is_supported(path):
            result.append(path)
    result.sort(key=lambda p: p.relative_to(root).as_posix())
    return result


def load_document(path: Path, root: Path) -> Document:
    """Carga un archivo y construye su Document (source relativo a root)."""
    if not is_supported(path):
        raise UnsupportedFileError(f"Formato no soportado: {path.suffix}")
    source = path.resolve().relative_to(root.resolve()).as_posix()
    path_abs = path.resolve()
    ext = path.suffix.lower()
    doc_type, loader = LOADERS[ext]
    pages = loader(path)
    return Document(
        source=source,
        path=path_abs,
        sha256=file_sha256(path),
        doc_type=doc_type,
        pages=tuple(pages),
    )


def load_folder(root: Path) -> IngestResult:
    """Carga todos los archivos soportados; un archivo que falla va a errors y no para el resto."""
    paths = scan_folder(root)
    documents: list[Document] = []
    errors: list[tuple[str, str]] = []
    for path in paths:
        try:
            doc = load_document(path, root)
            documents.append(doc)
        except Exception as e:
            source = path.resolve().relative_to(root.resolve()).as_posix()
            errors.append((source, f"{type(e).__name__}: {e}"))
    return IngestResult(documents=documents, errors=errors)
