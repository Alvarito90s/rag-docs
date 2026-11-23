# 062 · Evaluación de la recuperación
Fase: 6 · Depende de: 061

## Objetivo
Indexar `samples/` con un tamaño de chunk dado en una carpeta aparte y medir Hit@1, Hit@5 y MRR@10 de un modo de búsqueda sobre las preguntas con respuesta.

## Archivos
- crear: `src/docuchat/evaluation/runner.py`
- crear: `tests/evaluation/test_runner_retrieval.py`

## Interfaz
```python
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from docuchat.config import Settings
from docuchat.evaluation.dataset import EvalQuestion
from docuchat.evaluation.metrics import first_hit_rank, hit_at, mean_reciprocal_rank
from docuchat.index.embeddings import Embedder
from docuchat.index.indexer import build_indexer, reset_index
from docuchat.retrieval.searcher import Searcher, SearchMode

SEARCH_DEPTH = 10  # resultados por consulta para MRR@10


@dataclass(frozen=True)
class RetrievalReport:
    """Métricas de recuperación de una configuración (tamaño de chunk + modo)."""

    chunk_size: int
    mode: str
    chunks: int
    questions: int
    hit_at_1: float
    hit_at_5: float
    mrr: float
    misses: list[str] = field(default_factory=list)  # ids sin acierto en el top 5


def eval_settings(base: Settings, data_root: Path, chunk_size: int) -> Settings:
    """Copia de base con data_dir propio y chunk_size/overlap (15 %) para la evaluación."""


def build_eval_index(settings: Settings, embedder: Embedder | None = None) -> int:
    """Reindexa settings.documents_dir desde cero y devuelve el número de chunks."""


def evaluate_retrieval(
    searcher: Searcher,
    questions: Sequence[EvalQuestion],
    mode: SearchMode,
    *,
    chunk_size: int,
    chunks: int,
) -> RetrievalReport:
    """Hit@1, Hit@5 y MRR@10 de las preguntas con respuesta."""
```

## Comportamiento
1. `eval_settings` → `base.model_copy(update={"data_dir": data_root / f"cs{chunk_size}", "chunk_size": chunk_size, "chunk_overlap": chunk_size * 15 // 100})`. Así cada tamaño tiene su propio índice y nunca toca `data/` de la app.
2. `build_eval_index`: `reset_index(settings)`; `with build_indexer(settings, embedder=embedder) as indexer:` → `stats = indexer.index_folder(settings.documents_dir)`; si `stats.errors` → `RuntimeError(f"Errores al indexar: {stats.errors}")`; devuelve `indexer.chunk_count()`.
3. `evaluate_retrieval`: solo las preguntas con `answerable`. Para cada una, `results = searcher.search(q.question, SEARCH_DEPTH, mode)` y `rank = first_hit_rank(results, q.expected_doc, q.expected_page)`. `hit_at_1 = hit_at(ranks, 1)`, `hit_at_5 = hit_at(ranks, 5)`, `mrr = mean_reciprocal_rank(ranks)`. `misses` = ids con `rank is None` o `rank > 5`, en orden. `mode` se guarda como `mode.value`.
4. Los errores de embeddings se propagan.

## Tests obligatorios
`tests/evaluation/test_runner_retrieval.py`. NO cambies los valores esperados. Nada de red: `FakeEmbedder` que devuelve `[[float(len(t)), 1.0, 0.5] for t in texts]`. Con BM25 los resultados no dependen del embedder, así que los números son exactos (medidos por el cerebro).
Fixture `base`: borra `DOCUCHAT_*`, `chdir(tmp_path)` y devuelve `Settings(documents_dir=SAMPLES)` (`SAMPLES = ROOT / "samples"`). Preguntas: `load_questions(ROOT / "eval" / "questions.jsonl")`.
1. `eval_settings(base, tmp_path, 500)` → `data_dir == tmp_path / "cs500"`, `chunk_size == 500`, `chunk_overlap == 75`, `llm_model == base.llm_model`; con 1200 → `chunk_overlap == 180`.
2. `build_eval_index` (parametrizado): 500 → `45`; 800 → `26`; 1200 → `23` chunks.
3. Reindexar dos veces la misma carpeta → `26` las dos veces (empieza de cero).
4. BM25 con 800: `evaluate_retrieval(build_searcher(s, embedder=FakeEmbedder()), preguntas, SearchMode.BM25, chunk_size=800, chunks=26)` → `questions == 32`, `hit_at_1 == pytest.approx(27 / 32)`, `hit_at_5 == 1.0`, `mrr == pytest.approx(0.9088541666666666)`, `misses == []`, `mode == "bm25"`.
5. BM25 con 1200 → `hit_at_1 == pytest.approx(28 / 32)`, `mrr == pytest.approx(0.9244791666666666)`.
6. Solo cuentan las preguntas con respuesta: con `[q01, u01]` (las dos primeras de cada tipo del dataset) → `questions == 1`.
7. Fallos: `EvalQuestion(id="x01", question="¿Qué significa el error E-17?", expected_doc="manual_cafetera.pdf", expected_page=1, answer_keywords=["vacío"], answerable=True)` en BM25 con 800 → `misses == ["x01"]`.
8. Error de indexación: carpeta con `samples` copiado más `roto.pdf` (`b"no es un pdf"`) → `build_eval_index` lanza `RuntimeError` con `"roto.pdf"` en el mensaje.

## Aceptación
- [ ] `uv run pytest -q tests/evaluation/test_runner_retrieval.py` → 10 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
Generación (063), informe y script (064). No toques `index/` ni `retrieval/`.
