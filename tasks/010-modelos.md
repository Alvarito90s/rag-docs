# 010 · Modelos Document y Page
Fase: 1 · Depende de: ninguna

## Objetivo
Definir los modelos Pydantic inmutables que devuelve la ingesta: un documento con sus páginas de texto.

## Archivos
- crear: `src/docuchat/models.py`
- crear: `src/docuchat/ingest/__init__.py` (solo el docstring `"""Ingesta: loaders por formato y escaneo de carpetas."""`)
- crear: `tests/test_models.py`

## Interfaz
```python
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocType(StrEnum):
    """Formatos soportados."""

    PDF = "pdf"
    DOCX = "docx"
    MD = "md"
    TXT = "txt"


class Page(BaseModel):
    """Una página (PDF) o sección (MD) de texto ya limpio."""

    model_config = ConfigDict(frozen=True)

    number: int = Field(ge=1)
    text: str
    heading: str | None = None  # encabezado de la sección (solo MD)

    @property
    def char_count(self) -> int:
        """Número de caracteres del texto."""


class Document(BaseModel):
    """Un archivo ingerido con sus páginas."""

    model_config = ConfigDict(frozen=True)

    source: str  # ruta relativa a la carpeta escaneada, con "/" (p. ej. "sub/a.pdf")
    path: Path  # ruta absoluta del archivo
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    doc_type: DocType
    pages: tuple[Page, ...]

    @property
    def page_count(self) -> int:
        """Número de páginas."""

    @property
    def char_count(self) -> int:
        """Suma de caracteres de todas las páginas."""

    @model_validator(mode="after")
    def _check_page_order(self) -> "Document":
        """Exige números de página estrictamente crecientes (pueden tener huecos)."""
```

## Comportamiento
1. `_check_page_order`: si algún `pages[i].number <= pages[i-1].number` lanza `ValueError("los números de página deben ser estrictamente crecientes")`. Un documento sin páginas es válido.
2. Los huecos están permitidos (p. ej. `1, 2, 5`): las páginas vacías se omiten pero conservan su número real.
3. `pages` es una tupla: quien construya un `Document` debe pasar `tuple(lista)`.

## Tests obligatorios
`tests/test_models.py` (usa `SHA = "a" * 64`):
1. `Page(number=1, text="hola").char_count` → `4`; `heading` → `None`.
2. `Page(number=0, text="x")` → `ValidationError`.
3. `Page` es inmutable: asignar `page.text = "y"` → `ValidationError`.
4. `Document(source="a.pdf", path=Path("/tmp/a.pdf"), sha256=SHA, doc_type=DocType.PDF, pages=(Page(number=1, text="ab"), Page(number=3, text="cde")))` → `page_count == 2`, `char_count == 5`.
5. Mismo documento con páginas `(1, 1)` → `ValidationError`; con `(2, 1)` → `ValidationError`.
6. `pages=()` → válido, `page_count == 0`, `char_count == 0`.
7. `sha256="xyz"` → `ValidationError`; `sha256="A" * 64` (mayúsculas) → `ValidationError`.
8. `doc_type="md"` (cadena) → se convierte a `DocType.MD`; `doc_type="pptx"` → `ValidationError`.
9. `DocType.PDF == "pdf"` → `True` (StrEnum).

## Aceptación
- [ ] `uv run pytest -q tests/test_models.py` pasa (todos los casos de arriba)
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
`Chunk` y `SearchResult` (Fase 2 y 3). Cualquier loader.
