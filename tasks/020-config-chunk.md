# 020 · Config de indexado y modelo Chunk
Fase: 2 · Depende de: ninguna

## Objetivo
Añadir los ajustes de indexado a `Settings` y el modelo `Chunk` (fragmento de una página con sus metadatos).

## Archivos
Excepción a la regla de 3 archivos: son añadidos pequeños.
- modificar: `src/docuchat/config.py` (solo AÑADIR campos y propiedades)
- modificar: `.env.example` (solo AÑADIR 3 líneas al final)
- modificar: `src/docuchat/models.py` (solo AÑADIR `Chunk` y `make_chunk_id`)
- modificar: `tests/test_config.py` y `tests/test_models.py` (solo AÑADIR tests)

## Interfaz
En `Settings`, después de `chunk_overlap`:
```python
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
```
`.env.example`, al final:
```
DOCUCHAT_EMBEDDING_BATCH_SIZE=32
DOCUCHAT_REQUEST_MAX_RETRIES=3
DOCUCHAT_CHROMA_COLLECTION=chunks
```
En `models.py`:
```python
def make_chunk_id(source: str, page: int, position: int) -> str:
    """Id estable de un chunk: '<source>#p<page>#c<position>'."""
    return f"{source}#p{page}#c{position}"


class Chunk(BaseModel):
    """Fragmento de texto de una página, la unidad que se indexa y se recupera."""

    model_config = ConfigDict(frozen=True)

    chunk_id: str
    source: str
    doc_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page: int = Field(ge=1)
    position: int = Field(ge=0)  # orden del chunk dentro de su página, desde 0
    heading: str | None = None
    text: str = Field(min_length=1)
```

## Tests obligatorios
NO cambies los valores esperados. Añadir a `tests/test_config.py` (usa el fixture autouse que ya existe):
1. `test_index_defaults`: `embedding_batch_size == 32`, `request_max_retries == 3`, `chroma_collection == "chunks"`.
2. `test_index_env_override`: env `DOCUCHAT_EMBEDDING_BATCH_SIZE=8` → `8`.
3. `test_derived_paths`: por defecto `chroma_dir == Path("data/chroma")` y `registry_path == Path("data/registry.sqlite3")`; con env `DOCUCHAT_DATA_DIR=/tmp/x` → `Path("/tmp/x/chroma")`.
4. `test_invalid_index_values` (parametrizado): `{"embedding_batch_size": 0}`, `{"request_max_retries": -1}` → `ValidationError`.

Añadir a `tests/test_models.py`:
5. `make_chunk_id("sub/a.pdf", 3, 0)` → `"sub/a.pdf#p3#c0"`.
6. `Chunk(chunk_id="a.pdf#p1#c0", source="a.pdf", doc_sha256=SHA, page=1, position=0, text="hola")` es válido y `heading is None`.
7. `test_chunk_invalid` (parametrizado, 3 casos): `{"text": ""}`, `{"page": 0}`, `{"position": -1}` sobre el chunk del punto 6 → `ValidationError`.

## Aceptación
- [ ] `uv run pytest -q tests/test_config.py tests/test_models.py` pasa (16 + 15 = 31 tests)
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
`SearchResult` (Fase 3). Cualquier otro cambio.
