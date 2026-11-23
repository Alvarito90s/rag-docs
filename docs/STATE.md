# Estado del proyecto

Lo mantiene el agente ejecutor: actualízalo al terminar cada spec.

- Última spec completada: 034 (CLI search) — 033-b (cache vacía)
- Fase actual: 3 · Recuperación y generación — 32 specs completadas (001-b, 003-b, 004-b, 004-c, 005-b + variantes, 020, 021, 022, 023, 024, 024-b, 025, 026, 027, 030, 031, 032, 033, 033-b, 034)

## Módulos

| Módulo | Archivos | Estado |
| --- | --- | --- |
| `config` | `src/docuchat/config.py` | ✅ Config oMLX + indexado + búsqueda con 22 tests |
| `env_check` | `src/docuchat/env_check.py`, `scripts/check_env.py` | ✅ Entorno 23 checks + sentinel clave vacía |
| `models` | `src/docuchat/models.py` | ✅ Pydantic inmutables + 18 tests (Document, Page, Chunk, SearchResult + make_chunk_id) |
| `ingest.cleaning` | `src/docuchat/ingest/cleaning.py` | ✅ 5 funciones puras + 15 tests |
| `ingest.pdf_loader` | `src/docuchat/ingest/pdf_loader.py` | ✅ PyMuPDF + 7 tests |
| `ingest.docx_loader` | `src/docuchat/ingest/docx_loader.py` | ✅ python-docx + tests incluidos |
| `ingest.text_loader` | `src/docuchat/ingest/text_loader.py` | ✅ MD/TXT con split_markdown_sections + 14 tests |
| `ingest.scanner` | `src/docuchat/ingest/scanner.py` | ✅ Escaneo recursivo con soporte symlink, 5 funciones + 12 tests |
| `cli` | `src/docuchat/cli.py`, `tests/test_cli.py` | ✅ Typer + Rich + `ingest` con indexación real (Progress + `--reset`) + `search` con formato de resultados, 26 tests |
| `samples` | `scripts/sample_content.py`, `scripts/make_samples.py`, `tests/test_samples.py` | ✅ 7 docs + 19 tests |
| `report` | `reports/` | ✅ 26 informes |
| `index` | `src/docuchat/index/__init__.py`, `src/docuchat/index/chunker.py`, `src/docuchat/index/registry.py`, `src/docuchat/index/vector_store.py`, `src/docuchat/index/bm25.py`, `src/docuchat/index/embeddings.py`, `src/docuchat/index/indexer.py`, `tests/index/test_chunker.py`, `tests/index/test_registry.py`, `tests/index/test_bm25.py`, `tests/index/test_embeddings.py`, `tests/index/test_indexer.py` | ✅ Chunker (17) + Registry (10) + Embeddings (9) + BM25 (12) + VectorStore (16, `all_chunks` ordenado + `query`) + Indexer (14) |
| `retrieval` | `src/docuchat/retrieval/__init__.py`, `src/docuchat/retrieval/fusion.py`, `src/docuchat/retrieval/searcher.py`, `tests/retrieval/test_fusion.py`, `tests/retrieval/test_searcher.py` | ✅ RRF fuse (6) + drop_adjacent (4) + Searcher (13) + format_query (2) + build_searcher (1) |

## Qué funciona

- `uv sync` instala todas las dependencias
- `uv run pytest -q` → 264 tests pasando
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

- Spec 024-b completada: `VectorStore.all_chunks()` devuelve los chunks ordenados por (source, page, position) y el `zip` usa `strict=True`.
- Spec 026 completada: indexador incremental con `Indexer.index_folder()` — solo reindexa archivos nuevos o modificados, borra los eliminados, gestiona errores por archivo y soporta callback de progreso. Incluye `build_indexer(settings)` y `reset_index(settings)`.
- Spec 027 completada: `ingest` sin `--dry-run` indexa con `Indexer`, barra de progreso Rich y opción `--reset`. Función `stats_line()` integrada.

## Notas y deuda técnica

- `sample_content.py` tiene strings largos (E501 ignorado en pyproject.toml)
- `scripts/` y `tests/` excluidos de mypy por falta de stubs pymupdf/docx
- Los tests de PDF aceptan `RuntimeError | OSError` (pymupdf no exporta `FileNotFoundError`)
