from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de DocuChat; cada campo se sobreescribe con DOCUCHAT_<NOMBRE>."""

    model_config = SettingsConfigDict(
        env_prefix="DOCUCHAT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Servidor LLM (oMLX local, API compatible con OpenAI)
    llm_base_url: str = "http://127.0.0.1:8000/v1"
    llm_api_key: str = ""  # secreto: se pone en .env, nunca en el código
    llm_model: str = "Qwen3.6-35B-A3B-6bit"
    # Embeddings (mismo servidor y misma clave por defecto)
    embedding_base_url: str = "http://127.0.0.1:8000/v1"
    embedding_model: str = "Qwen3-Embedding-0.6B-4bit-DWQ"
    request_timeout: float = Field(default=60.0, gt=0)
    # Rutas
    documents_dir: Path = Path("samples")
    data_dir: Path = Path("data")
    # Chunking
    chunk_size: int = Field(default=800, gt=0)
    chunk_overlap: int = Field(default=120, ge=0)
    # Indexado
    embedding_batch_size: int = Field(default=32, gt=0)
    request_max_retries: int = Field(default=3, ge=0)
    chroma_collection: str = "chunks"

    @property
    def chroma_dir(self) -> Path:
        """Carpeta de la base vectorial."""
        return self.data_dir / "chroma"

    @property
    def registry_path(self) -> Path:
        """Archivo SQLite del registro de documentos indexados."""
        return self.data_dir / "registry.sqlite3"

    @model_validator(mode="after")
    def _check_chunking(self) -> "Settings":
        """Rechaza un solape mayor o igual que el tamaño de chunk."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap debe ser menor que chunk_size")
        return self


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia única (cacheada) de Settings."""
    return Settings()
