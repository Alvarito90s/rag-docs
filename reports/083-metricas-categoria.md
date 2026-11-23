# 083 · Métricas de evaluación por categoría

## Resumen
Implementación completada. Desglose de métricas de evaluación por categoría de pregunta: Hit@1, Hit@5 y MRR de la recuperación, y aciertos de palabras clave de la generación.

## Archivos creados
- `src/docuchat/evaluation/categories.py` (56 líneas)
  - `CategoryScores` — dataclass frozen (questions, hit_at_1, hit_at_5, mrr)
  - `retrieval_by_category()` — agrupa por `q.category`, calcula hit_at/hit_at_5/mrr por grupo, ValueError si longitudes distintas
  - `keywords_by_category()` — ignora `answerable=False`, ratio(aciertos/n) por categoría
- `tests/evaluation/test_categories.py` (13 tests)
  - Tests 1-4: funciones de categorías (normal, longitud, vacío, keywords)
  - Test 5: `bm25_report` con samples_v2 (73 chunks, 7 categorías, valores exactos)
  - Test 6: `bm25_report` con samples v1 (solo "general")
  - Test 7: generación por categoría (QueueChat + FakeRetriever + Answerer)
  - Test 8-10: render_category_table (con generación, sin generación, no aplica)
  - Test 11-12: render_results con categorías
  - Test 13: defaults compatibles

## Archivos modificados
- `src/docuchat/evaluation/runner.py`
  - Import `CategoryScores, keywords_by_category, retrieval_by_category`
  - `RetrievalReport`: nuevo campo `by_category: dict[str, CategoryScores] = field(default_factory=dict)`
  - `GenerationReport`: nuevo campo `keywords_by_category: dict[str, float | None] = field(default_factory=dict)`
  - `evaluate_retrieval`: pasa `by_category=retrieval_by_category(answerable_q, ranks)`
  - `evaluate_generation`: pasa `keywords_by_category=keywords_by_category(questions, {r.id: r.keywords_ok for r in results})`
- `src/docuchat/evaluation/report.py`
  - `render_category_table(retrieval, generation, chunk_size)` → tabla markdown; "" si no aplica (vacío, solo "general", chunk no encontrado)
  - `render_results`: inserta "### Por categoría (chunk {cs})" con tabla antes de "## Generación" cuando aplica

## Verificaciones
- `uv run pytest -q tests/evaluation/test_categories.py` → 13 passed
- `uv run pytest -q` → 522 passed (todos)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores
- `wc -l src/docuchat/evaluation/*.py` → máx 225 (runner.py), todos < 300

## Notas
- El dataset v1 (solo "general") produce un informe idéntico al anterior (no muestra sección "Por categoría")
- Sin imports circulares: categories.py no importa runner.py
- Compatible con `asdict` de run.py (serializa campos nuevos automáticamente)
