# 005-b · Samples: datos en sus páginas y tests fieles a la spec
Fase: 0 · Depende de: 005

## Objetivo
Los PDFs y `tests/test_samples.py` no cumplen la tabla de la spec 005: hay datos en páginas equivocadas, frases cambiadas, un guion mal escrito en otra página y tests que se adaptaron al resultado en vez de a la spec. Corrígelo.

## Archivos
- modificar: `scripts/sample_content.py`
- modificar: `tests/test_samples.py` (solo `FACTS`, `test_pdf_facts`, `test_manual_hyphen` y el comentario sobre "reorganizar")
- regenerar: `samples/*.pdf` con `uv run python scripts/make_samples.py`
- modificar: `docs/STATE.md`

## Comportamiento
Aclaración: PyMuPDF NO reorganiza páginas. Cada elemento de `PdfSpec.pages` es exactamente una página (`insert_textbox` en una página nueva). Si un dato sale en otra página es porque está en otro elemento de la lista.

1. Contrato (`contrato_servicios.pdf`, 4 páginas), una frase por página, LITERAL y completa:
   - p1 `El presente contrato se firma en Valladolid el 3 de marzo de 2025.`
   - p2 `El precio total del servicio asciende a 4.800 euros anuales, pagaderos por trimestres vencidos.`
   - p3 `El proveedor ofrece una garantía de dos años sobre todos los desarrollos entregados.`
   - p4 `Cualquiera de las partes podrá resolver el contrato con un preaviso de 30 días naturales.`
   Ahora el precio está en p1, la garantía en p2 y el preaviso en p3: muévelos y rellena para que cada página siga teniendo 800–1.100 caracteres.
2. Manual: el dato `La garantía de la cafetera cubre defectos de fabricación durante tres años.` debe estar LITERAL en la página 9 (ahora no se comprueba).
3. Manual, guion: en la página 5 (índice 4 de `pages`), un párrafo que contenga `descalci-\nficación` (con "descalci", no "descalici"). Quita el de la página 6.
4. Paper p1, frase LITERAL: `Hybrid retrieval improved Hit@5 from 0.71 to 0.84 on the internal benchmark.` (ahora pone "improves").
5. `FACTS` en el test = exactamente los 10 casos de la tabla de la spec 005 (4 contrato, 4 manual, 2 paper), con la frase COMPLETA incluido el punto final, no fragmentos. El guion NO es un dato: quítalo de `FACTS`.
6. `test_pdf_facts`: el dato está en `norm(texto de su página)` Y no está en `norm(texto)` de ninguna otra página del mismo PDF.
7. `test_manual_hyphen`: `doc[4].get_text()` (página 5) contiene `"descalci-\n"`.
8. `docs/STATE.md`: corrige lo que no es cierto. No existe `uv run docuchat check-env` (el comando es `uv run python scripts/check_env.py`), el guion está en la p.5 y la tabla de módulos no debe decir "5 informes" si no los hay.
9. Si un texto no cabe (`rc < 0`), acorta el relleno, nunca el dato.

## Tests obligatorios
`tests/test_samples.py` → 19 tests: 1 + 3 + 10 + 1 + 1 + 1 + 1 + 1.

## Aceptación
- [ ] `uv run python scripts/make_samples.py` regenera sin errores
- [ ] `uv run pytest -q tests/test_samples.py` → 19 passed
- [ ] `grep -c "descalici" scripts/sample_content.py tests/test_samples.py` → 0 en ambos
- [ ] `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src` sin errores

## Fuera de alcance
`make_samples.py`, DOCX, MD, TXT, `pyproject.toml`.
