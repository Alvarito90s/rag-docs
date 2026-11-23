# Informe 081 · Corpus de evaluación v2
Estado: COMPLETADA

## Cambios
- `scripts/make_samples_v2.py`: copia exacta de `tasks/assets/081/make_samples_v2.py`
- `scripts/samples_v2_manuales.py`: copia exacta de `tasks/assets/081/samples_v2_manuales.py` (3 manuales K1/K2/K3 con trampa de fase 11)
- `scripts/samples_v2_empresa.py`: copia exacta de `tasks/assets/081/samples_v2_empresa.py` (contrato, adenda, informe, reglamento)
- `scripts/samples_v2_textos.py`: copia exacta de `tasks/assets/081/samples_v2_textos.py` (2 DOCX teletrabajo, tarifas, MD, TXT)
- `pyproject.toml`: añadido `"scripts/samples_v2_*.py" = ["E501"]` en `[tool.ruff.lint.per-file-ignores]`
- `samples_v2/`: 15 documentos generados (7 PDFs + 3 DOCX + 3 MD + 2 TXT), 70 páginas, 29641 caracteres
- `tests/test_samples_v2.py`: 27 tests (archivos, copia exacta, páginas, corpus, chunks, trampa, facts)
- `docs/STATE.md`: actualizado con spec 081, módulo samples_v2, conteos, fase 65 specs

## Verificación
```
$ uv run pytest -q tests/test_samples_v2.py
27 passed, 5 warnings

$ uv run pytest -q
497 passed, 5 warnings

$ uv run ruff check .
All checks passed!

$ uv run ruff format --check .
172 files already formatted

$ uv run mypy src
Success: no issues found in 38 source files

$ uv run docuchat ingest samples_v2 --dry-run
15 documentos, 70 páginas, 29641 caracteres

$ for f in make_samples_v2 samples_v2_manuales samples_v2_empresa samples_v2_textos; do cmp scripts/$f.py tasks/assets/081/$f.py; done
(salida vacía = idénticos)

$ git status --short samples/
(salida vacía = samples/ sin cambios)
```

## Decisiones que tomé
- Ninguna: la spec era totalmente determinista. Los tests siguen exactamente la firma descrita en la spec.

## Bloqueos y dudas
- Ninguno. Todos los checks pasaron a la primera (excepto un ajuste de formato de ruff que se corrigió con `ruff format`).
