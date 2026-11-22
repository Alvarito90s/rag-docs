# 014 · Registro de loaders y escaneo de carpetas
Fase: 1 · Depende de: 012, 013

## Objetivo
Recorrer una carpeta de forma recursiva, elegir el loader según la extensión y construir los `Document` con su hash, sin que un archivo roto pare la ingesta.

## Archivos
- crear: `src/docuchat/ingest/scanner.py`
- crear: `tests/ingest/test_scanner.py`

## Interfaz
```python
import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from docuchat.ingest.docx_loader import load_docx
from docuchat.ingest.pdf_loader import load_pdf
from docuchat.ingest.text_loader import load_markdown, load_txt
from docuchat.models import Document, DocType, Page

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


def is_supported(path: Path) -> bool:
    """Indica si la extensión (sin distinguir mayúsculas) tiene loader."""


def scan_folder(root: Path) -> list[Path]:
    """Archivos soportados bajo root (recursivo), ordenados por su ruta relativa."""


def load_document(path: Path, root: Path) -> Document:
    """Carga un archivo y construye su Document (source relativo a root)."""


def load_folder(root: Path) -> IngestResult:
    """Carga todos los archivos soportados; un archivo que falla va a errors y no para el resto."""
```

## Comportamiento
1. `is_supported`: `path.suffix.lower() in LOADERS`.
2. `scan_folder`:
   a. Si `root` no existe → `FileNotFoundError(f"No existe: {root}")`; si existe pero no es carpeta → `NotADirectoryError(f"No es una carpeta: {root}")`.
   b. Recorre `root.rglob("*")` y se queda con los archivos (`is_file()`) soportados.
   c. Ignora todo lo que tenga, en su ruta RELATIVA a `root`, alguna parte que empiece por `"."` (archivos y carpetas ocultos, p. ej. `.git/`) y los archivos cuyo nombre empiece por `"~$"` (temporales de Office).
   d. Ordena por `ruta.relative_to(root).as_posix()`.
3. `load_document`:
   a. Si no `is_supported(path)` → `UnsupportedFileError(f"Formato no soportado: {path.suffix}")`.
   b. `source = path.relative_to(root).as_posix()`; `path` absoluto = `path.resolve()`.
   c. `Document(source=..., path=..., sha256=file_sha256(path), doc_type=..., pages=tuple(loader(path)))`.
4. `load_folder`: `scan_folder(root)` (sus excepciones SÍ se propagan); para cada archivo, `load_document`; si lanza cualquier `Exception`, añade `(source, f"{type(e).__name__}: {e}")` a `errors` y continúa. Aquí está justificado capturar `Exception` (cada librería lanza sus propios errores).
5. Un documento sin páginas (p. ej. TXT vacío) se incluye en `documents` con `page_count == 0`; no es un error.

## Tests obligatorios
`tests/ingest/test_scanner.py`, `SAMPLES = Path(__file__).resolve().parents[2] / "samples"`. NO cambies los valores esperados.
1. `[p.name for p in scan_folder(SAMPLES)]` → `["apuntes_redes.md", "contrato_servicios.pdf", "glosario_interno.md", "manual_cafetera.pdf", "notas_reunion.txt", "paper_rag_resumen.pdf", "politica_vacaciones.docx"]`.
2. Árbol en `tmp_path` con los archivos `b.txt`, `a.MD`, `sub/c.txt`, `.oculto/d.txt`, `.e.txt`, `~$f.docx`, `g.pptx`, `sub/.git/h.md` (contenido `"x"`) → rutas relativas `["a.MD", "b.txt", "sub/c.txt"]`.
3. `scan_folder(tmp_path / "no_existe")` → `FileNotFoundError`; `scan_folder(un_archivo)` → `NotADirectoryError`.
4. `file_sha256` de un archivo con `b"abc"` → `"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"`.
5. `load_document(SAMPLES / "contrato_servicios.pdf", SAMPLES)` → `source == "contrato_servicios.pdf"`, `doc_type == DocType.PDF`, `page_count == 4`, `path.is_absolute()`, `sha256 == file_sha256(...)`.
6. `load_document(tmp_path / "sub" / "c.txt", tmp_path)` → `source == "sub/c.txt"`, `doc_type == DocType.TXT`.
7. `load_document(tmp_path / "g.pptx", tmp_path)` → `UnsupportedFileError`.
8. `load_folder(SAMPLES)` → 7 documentos, `errors == []`, suma de `page_count` == `22`, `[d.source for d in documents]` igual a la lista del test 1.
9. Carpeta con `ok.txt` (`"hola"`) y `roto.pdf` (`b"no soy un pdf"`) → 1 documento (`ok.txt`); `errors` tiene 1 elemento, `errors[0][0] == "roto.pdf"` y `errors[0][1].startswith("FileDataError")`.
10. Carpeta con `vacio.txt` (`" \n"`) → 1 documento con `page_count == 0`, sin errores.

## Referencia de librerías
```python
import hashlib

h = hashlib.sha256()
with path.open("rb") as f:
    for bloque in iter(lambda: f.read(1024 * 1024), b""):
        h.update(bloque)
h.hexdigest()  # str de 64 caracteres en minúsculas

Path("raiz/sub/c.txt").relative_to(Path("raiz")).as_posix()  # "sub/c.txt"
```

## Aceptación
- [ ] `uv run pytest -q tests/ingest/test_scanner.py` pasa
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
Registro SQLite e indexado incremental (Fase 2), paralelismo, vigilancia de carpetas.
