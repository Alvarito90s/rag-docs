# Estado del proyecto

Lo mantiene el agente ejecutor: actualízalo al terminar cada spec.

- Última spec completada: 014-c (rutas con enlaces simbólicos)
- Fase actual: 1 · Ingesta y CLI — 10 specs completadas (010–015 + 013-b + 014-b + 014-c + 015-b)

## Módulos

| Módulo | Archivos | Estado |
| --- | --- | --- |
| `config` | `src/docuchat/config.py` | ✅ Config oMLX con 11 tests |
| `env_check` | `src/docuchat/env_check.py`, `scripts/check_env.py` | ✅ Entorno 23 checks |
| `models` | `src/docuchat/models.py` | ✅ Pydantic inmutables + 10 tests |
| `ingest.cleaning` | `src/docuchat/ingest/cleaning.py` | ✅ 5 funciones puras + 15 tests |
| `ingest.pdf_loader` | `src/docuchat/ingest/pdf_loader.py` | ✅ PyMuPDF + 7 tests |
| `ingest.docx_loader` | `src/docuchat/ingest/docx_loader.py` | ✅ python-docx + tests incluidos |
| `ingest.text_loader` | `src/docuchat/ingest/text_loader.py` | ✅ MD/TXT con split_markdown_sections + 14 tests |
| `ingest.scanner` | `src/docuchat/ingest/scanner.py` | ✅ Escaneo recursivo con soporte symlink, 5 funciones + 12 tests |
| `cli` | `src/docuchat/cli.py`, `tests/test_cli.py` | ✅ Typer + Rich, 8 tests |
| `samples` | `scripts/sample_content.py`, `scripts/make_samples.py`, `tests/test_samples.py` | ✅ 7 docs + 19 tests |
| `report` | `reports/` | ✅ 16 informes |

## Qué funciona

- `uv sync` instala todas las dependencias
- `uv run pytest -q` → 123 tests pasando
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

- Ninguno — las specs 010 a 015 están completas

## Notas y deuda técnica

- `sample_content.py` tiene strings largos (E501 ignorado en pyproject.toml)
- `scripts/` y `tests/` excluidos de mypy por falta de stubs pymupdf/docx
- Los tests de PDF aceptan `RuntimeError | OSError` (pymupdf no exporta `FileNotFoundError`)
