# Informe 005-b · Samples: datos en sus páginas y tests fieles a la spec
Estado: COMPLETADA

## Cambios
- `scripts/sample_content.py`: reorganizado contrato (precio→p2, garantía→p3, preaviso→p4, filler→p1)
- `scripts/sample_content.py`: todos los datos ahora son oraciones completas con punto final (antes iban incrustadas en frases más largas)
- `scripts/sample_content.py`: manual p5 cambia "descalici-" → "descalci-", mueve "descalici-\nficación" a p5
- `scripts/sample_content.py`: manual p6 elimina "descalici-" (dato de página incorrecta)
- `scripts/sample_content.py`: manual p2, p7, p9 ajustan datos como oraciones completas
- `scripts/sample_content.py`: paper p1 cambia "improves" → "improved", dato como oración completa
- `scripts/sample_content.py`: paper p2 añade párrafo de relleno para alcanzar 600+ chars
- `tests/test_samples.py`: FACTS reescrito con los 10 casos exactos de la spec 005 (4 contrato, 4 manual, 2 paper), frases completas con punto final
- `tests/test_samples.py`: comentario sobre "reorganizar" corregido (PyMuPDF no reorganiza páginas)
- `tests/test_samples.py`: `test_manual_hyphen` usa `doc[4]` (página 5) en vez de `doc[5]` (página 6), "descalci-" en vez de "descalici-"
- `docs/STATE.md`: corregido comando check-env, guion en p.5, "4 informes"
- `samples/*.pdf`: regenerados con `uv run python scripts/make_samples.py`

## Verificación
- `uv run python scripts/make_samples.py` → 7 archivos generados sin errores ✅
- `uv run pytest -q tests/test_samples.py` → 19 passed ✅
- `uv run pytest -q` → 54 passed, 5 warnings ✅
- `grep -c "descalici" scripts/sample_content.py tests/test_samples.py` → 0 en ambos ✅
- `uv run ruff check . && uv run ruff format --check .` → all checks passed, 31 files formatted ✅
- `uv run mypy src` → success, no issues found ✅

## Decisiones que tomé
Ninguna. La spec fija todos los cambios exactos.

## Bloqueos y dudas
Ninguno. Todo pasó a la segunda ronda (primera ronda: contrato p4 sin punto tras "naturales" y paper p2 con 532 chars < 600 mínimos).
