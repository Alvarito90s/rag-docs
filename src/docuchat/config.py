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
    # Búsqueda
    top_k: int = Field(default=5, gt=0)  # resultados que se devuelven
    candidate_k: int = Field(default=20, gt=0)  # candidatos por buscador antes de fusionar
    rrf_k: int = Field(default=60, gt=0)
    query_instruction: str = "Given a question, retrieve passages that answer the question"
    # Generación
    llm_max_tokens: int = Field(default=1024, gt=0)
    llm_temperature: float = Field(default=0.2, ge=0, le=2)
    llm_thinking: bool = False  # razonamiento de Qwen (más lento); se pasa como enable_thinking
    context_max_chars: int = Field(default=6000, gt=0)  # tope del contexto que se manda al LLM
    # API web
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8001, gt=0, le=65535)  # 8000 lo usa oMLX

    @model_validator(mode="after")
    def _check_search(self) -> "Settings":
        """Rechaza candidate_k menor que top_k."""
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k debe ser mayor o igual que top_k")
        return self

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
