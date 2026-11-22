# Estado del proyecto

Lo mantiene el agente ejecutor: actualízalo al terminar cada spec.

- Última spec completada: 005-b (corrección de samples)
- Fase actual: 0 · Preparación — 5 specs completadas

## Módulos

| Módulo | Archivos | Estado |
| --- | --- | --- |
| `config` | `src/docuchat/config.py` | ✅ Config oMLX con 11 tests |
| `env_check` | `src/docuchat/env_check.py`, `scripts/check_env.py` | ✅ Entorno 23 checks |
| `samples` | `scripts/sample_content.py`, `scripts/make_samples.py`, `tests/test_samples.py` | ✅ 7 docs + 19 tests |
| `report` | `reports/` | ✅ 4 informes |

## Qué funciona

- `uv sync` instala todas las dependencias
- `uv run pytest -q` → 54 tests pasando
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores
- `uv run python scripts/check_env.py` → comprueba el entorno
- `uv run python scripts/make_samples.py` → genera 7 documentos de prueba
- Los PDFs contienen textos clave con >600 chars por página
- El manual incluye guionamiento "descalci-\n" en p.5
- Los DOCX contienen tablas y secciones con encabezados

## Qué falta en la fase actual
- Ninguno — las specs 001 a 005 están completas

## Notas y deuda técnica
- `sample_content.py` tiene strings largos (E501 ignorado en pyproject.toml)
- `scripts/` y `tests/` excluidos de mypy por falta de stubs pymupdf/docx
