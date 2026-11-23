# 030 · Config de búsqueda y modelo SearchResult
Fase: 3 · Depende de: 027

## Objetivo
Añadir a `Settings` los parámetros de búsqueda (top-k, candidatos, RRF, instrucción de consulta) y el modelo `SearchResult`.

## Archivos
Excepción a la regla de 3 archivos: son añadidos pequeños (como en la 020).
- modificar: `src/docuchat/config.py` (solo AÑADIR campos y un validador)
- modificar: `.env.example` (solo AÑADIR 4 líneas al final)
- modificar: `src/docuchat/models.py` (solo AÑADIR `SearchResult` al final)
- modificar: `tests/test_config.py` y `tests/test_models.py` (solo AÑADIR tests)

## Interfaz
En `Settings`, después de `chroma_collection`:
```python
# Búsqueda
top_k: int = Field(default=5, gt=0)  # resultados que se devuelven
candidate_k: int = Field(default=20, gt=0)  # candidatos por buscador antes de fusionar
rrf_k: int = Field(default=60, gt=0)
query_instruction: str = "Given a question, retrieve passages that answer the question"


@model_validator(mode="after")
def _check_search(self) -> "Settings":
    """Rechaza candidate_k menor que top_k."""
```
`.env.example`, al final:
```
DOCUCHAT_TOP_K=5
DOCUCHAT_CANDIDATE_K=20
DOCUCHAT_RRF_K=60
DOCUCHAT_QUERY_INSTRUCTION="Given a question, retrieve passages that answer the question"
```
En `models.py`, al final:
```python
class SearchResult(BaseModel):
    """Un chunk recuperado, con su puesto final y su puesto en cada buscador."""

    model_config = ConfigDict(frozen=True)

    chunk: Chunk
    rank: int = Field(ge=1)  # puesto final, desde 1
    score: float  # puntuación RRF
    vector_rank: int | None = Field(default=None, ge=1)  # None: no salió en la búsqueda vectorial
    bm25_rank: int | None = Field(default=None, ge=1)  # None: no salió en BM25
```

## Comportamiento
1. `_check_search`: si `candidate_k < top_k` → `ValueError("candidate_k debe ser mayor o igual que top_k")`; si no, devuelve `self`. NO toques `_check_chunking`.
2. `query_instruction` es la instrucción que Qwen3-Embedding antepone a las CONSULTAS (no a los documentos). Puede ser `""` (sin instrucción). Se usa en la spec 033.

## Tests obligatorios
NO cambies los valores esperados. Añadir a `tests/test_config.py` (usa el fixture autouse que ya existe):
1. `test_search_defaults`: `top_k == 5`, `candidate_k == 20`, `rrf_k == 60`, `query_instruction == "Given a question, retrieve passages that answer the question"`.
2. `test_search_env_override`: env `DOCUCHAT_TOP_K=3`, `DOCUCHAT_QUERY_INSTRUCTION=""` → `top_k == 3`, `query_instruction == ""`.
3. `test_candidate_k_not_smaller_than_top_k`: `Settings(top_k=10, candidate_k=5)` → `ValidationError`; `Settings(top_k=10, candidate_k=10)` es válido.
4. `test_invalid_search_values` (parametrizado, 3 casos): `{"top_k": 0}`, `{"candidate_k": 0}`, `{"rrf_k": 0}` → `ValidationError`.

Añadir a `tests/test_models.py` (reutiliza el chunk válido que ya usan los tests de `Chunk`):
5. `test_search_result_valid`: `SearchResult(chunk=chunk, rank=1, score=0.0328)` → `vector_rank is None`, `bm25_rank is None`, `result.chunk.chunk_id == "a.pdf#p1#c0"`.
6. `test_search_result_invalid` (parametrizado, 2 casos): `{"rank": 0}` y `{"vector_rank": 0}` (con el resto de campos válidos) → `ValidationError`.

## Aceptación
- [ ] `uv run pytest -q tests/test_config.py tests/test_models.py` → 40 passed (22 + 18)
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `DOCUCHAT_TOP_K=3 uv run python -c "from docuchat.config import get_settings; print(get_settings().top_k)"` imprime `3`

## Fuera de alcance
Cualquier código de búsqueda (specs 031–034). No leas ni edites `.env`.
