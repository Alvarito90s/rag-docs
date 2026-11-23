# Estado del proyecto

Lo mantiene el agente ejecutor: actualízalo al terminar cada spec.

- Última spec completada: 064-b (corrección de 3 desviaciones: except en run.py, misses sin recortar en report.py, keywords_ok siempre calculada en runner.py)
- Fase actual: 6 · Evaluación — 55 specs completadas (001-b, 003-b, 004-b, 004-c, 005-b + variantes, 020, 021, 022, 023, 024, 024-b, 024-c, 025, 026, 026-b, 027, 030, 031, 032, 033, 033-b, 034, 040, 041, 042, 043, 044, 045, 045-b, 050, 051, 052, 053, 054, 055, 056, 057, 060, 061, 062, 063, 064, 064-b)

## Módulos

| Módulo | Archivos | Estado |
| --- | --- | --- |
| `config` | `src/docuchat/config.py` | ✅ Config oMLX + indexado + búsqueda + generación + API con 32 tests |
| `env_check` | `src/docuchat/env_check.py`, `scripts/check_env.py` | ✅ Entorno 23 checks + sentinel clave vacía |
| `models` | `src/docuchat/models.py` | ✅ Pydantic inmutables + 18 tests (Document, Page, Chunk, SearchResult + make_chunk_id) |
| `ingest.cleaning` | `src/docuchat/ingest/cleaning.py` | ✅ 5 funciones puras + 15 tests |
| `ingest.pdf_loader` | `src/docuchat/ingest/pdf_loader.py` | ✅ PyMuPDF + 7 tests |
| `ingest.docx_loader` | `src/docuchat/ingest/docx_loader.py` | ✅ python-docx + tests incluidos |
| `ingest.text_loader` | `src/docuchat/ingest/text_loader.py` | ✅ MD/TXT con split_markdown_sections + 14 tests |
| `ingest.scanner` | `src/docuchat/ingest/scanner.py` | ✅ Escaneo recursivo con soporte symlink, 5 funciones + 12 tests |
| `cli` | `src/docuchat/cli.py`, `tests/test_cli.py` | ✅ Typer + Rich + `ingest` con indexación real (Progress + `--reset`) + `search` con formato de resultados + `ask` con streaming, fuentes y manejo de errores, 34 tests |
| `samples` | `scripts/sample_content.py`, `scripts/make_samples.py`, `tests/test_samples.py` | ✅ 7 docs + 19 tests |
| `report` | `reports/` | ✅ 35 informes |
| `index` | `src/docuchat/index/__init__.py`, `src/docuchat/index/chunker.py`, `src/docuchat/index/registry.py`, `src/docuchat/index/vector_store.py`, `src/docuchat/index/bm25.py`, `src/docuchat/index/embeddings.py`, `src/docuchat/index/indexer.py`, `tests/index/test_chunker.py`, `tests/index/test_registry.py`, `tests/index/test_bm25.py`, `tests/index/test_embeddings.py`, `tests/index/test_indexer.py` | ✅ Chunker (17) + Registry (10) + Embeddings (9) + BM25 (12) + VectorStore (17, ruta absoluta + `all_chunks` ordenado + `query`) + Indexer (16, tests 15-16 reparación de chunks desincronizados) |
| `retrieval` | `src/docuchat/retrieval/__init__.py`, `src/docuchat/retrieval/fusion.py`, `src/docuchat/retrieval/searcher.py`, `tests/retrieval/test_fusion.py`, `tests/retrieval/test_searcher.py` | ✅ RRF fuse (6) + drop_adjacent (4) + Searcher (13) + format_query (2) + build_searcher (1) |
| `generation` | `src/docuchat/generation/__init__.py`, `src/docuchat/generation/prompts.py`, `src/docuchat/generation/citations.py`, `src/docuchat/generation/llm_client.py`, `src/docuchat/generation/answer.py`, `tests/generation/__init__.py`, `tests/generation/test_prompts.py`, `tests/generation/test_citations.py`, `tests/generation/test_llm_client.py`, `tests/generation/test_answer.py` | ✅ `prompts`: SYSTEM_PROMPT, NO_ANSWER, format_block (1), build_context (5), build_messages (1) + 8 tests · `citations`: CITATION_RE, Source, find_citations (4), resolve_citations (4), is_no_answer (5) + 13 tests · `llm_client`: ChatModel protocol, OpenAIChatModel (stream/complete), make_chat_model + 8 tests · `answer`: Retriever protocol, Answer frozen dataclass, Answerer (retrieve/stream/finalize/ask) con 9 parámetros, build_answerer(constructor) + 10 tests |
| `api` | `src/docuchat/api/__init__.py`, `src/docuchat/api/app.py`, `src/docuchat/api/jobs.py`, `src/docuchat/api/routes_api.py`, `src/docuchat/api/routes_web.py`, `src/docuchat/api/templates/base.html`, `src/docuchat/api/templates/index.html`, `src/docuchat/api/templates/documents.html`, `src/docuchat/api/templates/_job.html`, `src/docuchat/api/static/app.js`, `src/docuchat/api/static/style.css`, `src/docuchat/api/static/vendor/htmx.min.js`, `tests/api/__init__.py`, `tests/api/conftest.py`, `tests/api/test_api.py`, `tests/api/test_files.py`, `tests/api/test_jobs.py`, `tests/api/test_search_ingest.py`, `tests/api/test_ask.py`, `tests/api/test_web.py` | ✅ `jobs`: IngestJobs (hilo daemon, lock, progreso, resultado), IngestJob, JobStatus, JobRunningError, job_to_dict + 8 tests · `app`: Services (settings, embedder, chat, searcher, answerer, jobs), get_services, ServicesDep (Annotated[Services, Depends]), create_app + StaticFiles mount `/static` + 9 tests · `routes_api`: router /api (health, documents, search, ingest, ingest/{job_id}, ask SSE), AskRequest, answer_to_dict, file_url + 30 tests · `routes_web`: router /files/{source:path} con resolve_document + router / con TEMPLATES (index.html con chunks + llm_model) + router GET /documents (lista + job actual) + router POST /ui/ingest (lanza ingesta, devuelve fragmento _job.html) + router GET /ui/ingest/{job_id} (fragmento + HX-Refresh al terminar) + 16 tests · `templates` + `static`: copia exacta de assets (index.html formulario + streaming SSE, base.html layout, documents.html lista de docs + botones HTMX, _job.html fragmento de progreso, app.js fetch/sse/linkCitations, style.css dark mode, vendor/htmx.min.js descargado local) · `test_web`: 15 tests (index vacío/con índice, app.js, style.css, copias 056, documents vacío/con índice, ingest con block, ingest status done/running/404, reset, htmx local, htmx serve, copias 057) |
| `evaluation` | `src/docuchat/evaluation/__init__.py`, `src/docuchat/evaluation/dataset.py`, `src/docuchat/evaluation/metrics.py`, `src/docuchat/evaluation/runner.py`, `src/docuchat/evaluation/report.py`, `src/docuchat/evaluation/run.py`, `eval/run_eval.py`, `tests/evaluation/__init__.py`, `tests/evaluation/test_dataset.py`, `tests/evaluation/test_metrics.py`, `tests/evaluation/test_runner_retrieval.py`, `tests/evaluation/test_runner_generation.py`, `tests/evaluation/test_report_run.py` | ✅ `EvalQuestion` + `DatasetError` + `load_questions()` + 11 tests · `metrics`: normalize, keywords_hit, first_hit_rank, hit_at, mean_reciprocal_rank, citation_counts, ratio + 13 tests · `runner` (062): RetrievalReport, eval_settings, build_eval_index, evaluate_retrieval + 10 tests · `runner` (063): QuestionResult, GenerationReport, evaluate_generation (answerable/unanswerable, keyword_accuracy, citation_precision, refusal_accuracy, false_refusals, latencias) + 7 tests · `report` (064): fmt, fmt_seconds, render_retrieval_table, render_generation_table, render_results + 6 tests · `run` (064): run_evaluation, main (argparse) + 4 tests · `eval/run_eval.py`: 6 líneas exactas, envoltura de main · `064-b`: run.py captura solo (OpenAIError, EmbeddingError); report.py misses sin recortar; runner.py keywords_ok siempre calculada |

## Qué funciona

- `uv sync` instala todas las dependencias
- `uv run pytest -q` → 440 passing, 0 failures (preexistent: ChromaDB Rust bindings internal errors en `test_indexer.py` y `test_searcher.py`)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores
- `uv run python scripts/check_env.py` → comprueba el entorno
- `uv run python scripts/make_samples.py` → genera 7 documentos de prueba
- `docuchat ingest samples --dry-run` → tabla Rich + `7 documentos, 22 páginas, 13612 caracteres`
- Los PDFs contienen textos clave con >600 chars por página
- El manual incluye guionamiento "descalici-\n" en p.5
- Los DOCX contienen tablas y secciones con encabezados
- Los MD tienen secciones con heading en cada página ingerida

## Qué falta en la fase actual

- Fase 6 · Evaluación: 54 specs completadas (001-b a 064). Restan solo README y Docker (Fase 7).
- Spec 057 completada: GET /documents (lista docs + botones HTMX), POST /ui/ingest (lanza ingesta, devuelve fragmento _job.html con polling cada 1s), GET /ui/ingest/{job_id} (fragmento + HX-Refresh al terminar), plantillas copiadas de assets/057, htmx descargado local en static/vendor/.
- Spec 056 completada: GET / con página HTML (formulario, streaming SSE, citas enlazadas, fuentes), StaticFiles mounted en `/static`, templates copiados de assets.
- Spec 057 completada: GET /documents (lista docs + botones HTMX), POST /ui/ingest (lanza ingesta, devuelve fragmento _job.html con polling cada 1s), GET /ui/ingest/{job_id} (fragmento + HX-Refresh al terminar), plantillas copiadas de assets/057, htmx descargado local en static/vendor/.
- Spec 054 completada: POST /api/ask con streaming SSE (EventSourceResponse, generador yield ServerSentEvent, eventos token/done/error, AskRequest, answer_to_dict).
- Spec 055 completada: GET /files/{source:path} con resolve_document (bloquea path traversal), FileResponse sin content-disposition, comando `serve` CLI con --host/--port y manejo de EmbeddingModelMismatchError.
- Spec 051 completada: IngestJobs con hilo, progreso y resultado.
- Spec 052 completada: App FastAPI con Services, create_app, get_services, router /api (health, documents), file_url, fixtures API compartidos.
- Spec 050 completada: deps FastAPI/Uvicorn/Jinja2 + campos `api_host`/`api_port` en Settings.
- Spec 024-c completada: `PersistentClient` usa `path.resolve()` en `VectorStore.__init__` y `reset_index()` para evitar la caché de ChromaDB que causaba fallos intermitentes (`no such table: acquire_write`, etc.) con rutas relativas. Nuevo test `test_relative_path_follows_cwd` que verifica que cambiar el cwd entre instancias no reutiliza un cliente de otro directorio.
- Spec 026 completada: indexador incremental con `Indexer.index_folder()` — solo reindexa archivos nuevos o modificados, borra los eliminados, gestiona errores por archivo y soporta callback de progreso. Incluye `build_indexer(settings)` y `reset_index(settings)`.
- Spec 026-b completada: reparación de chunks desincronizados — al iniciar `index_folder`, lee `present = self._store.sources()` y considera `unchanged` SOLO si `entry.chunk_count == 0 or source in present`. Si hash coincide pero faltan chunks en Chroma, reindexa como `updated`.
- Spec 027 completada: `ingest` sin `--dry-run` indexa con `Indexer`, barra de progreso Rich y opción `--reset`. Función `stats_line()` integrada.
- Spec 044 completada: `build_answerer()`, clase `Answerer` (retrieve/stream/finalize/ask) con `Retriever` protocol y `ChatModel` protocol.
- Spec 045 completada: comando `ask` con streaming, `format_sources()`, manejo de errores, fuentes y citas inválidas.

## Notas y deuda técnica

- `sample_content.py` tiene strings largos (E501 ignorado en pyproject.toml)
- `scripts/` y `tests/` excluidos de mypy por falta de stubs pymupdf/docx
- Los tests de PDF aceptan `RuntimeError | OSError` (pymupdf no exporta `FileNotFoundError`)
