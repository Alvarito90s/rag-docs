"""Modelos inmutables que devuelven los loaders de la ingesta."""

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
        return len(self.text)


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
        return len(self.pages)

    @property
    def char_count(self) -> int:
        """Suma de caracteres de todas las páginas."""
        return sum(p.char_count for p in self.pages)

    @model_validator(mode="after")
    def _check_page_order(self) -> "Document":
        """Exige números de página estrictamente crecientes (pueden tener huecos)."""
        for i in range(1, len(self.pages)):
            if self.pages[i].number <= self.pages[i - 1].number:
                raise ValueError("los números de página deben ser estrictamente crecientes")
        return self
