# 081 · Corpus de evaluación v2
Fase: 8 · Depende de: 080

## Objetivo
Generar `samples_v2/`, un corpus de 15 documentos más difícil que `samples/`. Tiene manuales casi iguales, versiones de un mismo documento y páginas que no nombran su producto, para que la evaluación pueda medir mejoras de recuperación. El contenido lo ha escrito el cerebro: tú solo lo copias, lo generas y lo proteges con tests.

## Archivos
- crear (copia exacta, NO edites su contenido):
  - `scripts/make_samples_v2.py` ← `tasks/assets/081/make_samples_v2.py`
  - `scripts/samples_v2_manuales.py` ← `tasks/assets/081/samples_v2_manuales.py`
  - `scripts/samples_v2_empresa.py` ← `tasks/assets/081/samples_v2_empresa.py`
  - `scripts/samples_v2_textos.py` ← `tasks/assets/081/samples_v2_textos.py`
- modificar: `pyproject.toml` (solo `[tool.ruff.lint.per-file-ignores]`: añadir `"scripts/samples_v2_*.py" = ["E501"]`)
- crear (generados por el script, se versionan): los 15 archivos de `samples_v2/`
- crear: `tests/test_samples_v2.py`

## Interfaz
Ya viene escrita en los assets. `scripts/make_samples_v2.py` reutiliza `render_pdf`, `render_docx` y `write_text` de `scripts/make_samples.py`, y `PdfSpec`, `DocxSpec` y `_p` de `scripts/sample_content.py`. No modifiques esos dos archivos.

```python
def main(out_dir: Path = Path("samples_v2")) -> list[Path]:
    """Genera los 15 documentos del corpus v2 y devuelve sus rutas."""
```

## Comportamiento
1. Copia los 4 assets con `cp`, sin reescribirlos a mano. Se comprueba byte a byte.
2. Genera el corpus desde la raíz del repo con `uv run python scripts/make_samples_v2.py`. Tiene que imprimir 15 rutas.
3. `samples/` y su generador NO cambian. La evaluación v1 sigue intacta.
4. Por diseño, las páginas 2, 3 y 6 de cada manual NO nombran el modelo en el cuerpo. La cabecera, que sí lo nombra, la quita `remove_repeated_edges`, porque se repite en las 6 páginas. **No es un bug: no lo "arregles".** Es la trampa que medirá el retrieval contextual (fase 11).
5. `tests/test_samples_v2.py` lee los archivos versionados de `samples_v2/`; no los regenera.

## Tests obligatorios
`tests/test_samples_v2.py`. NO cambies los valores esperados.

```python
from pathlib import Path

import pymupdf
import pytest

from docuchat.index.chunker import chunk_document
from docuchat.ingest.scanner import load_document, load_folder

ROOT = Path(__file__).resolve().parents[1]
SAMPLES_V2 = ROOT / "samples_v2"
ASSETS = ROOT / "tasks" / "assets" / "081"
```

1. `test_files`: el conjunto de nombres de los archivos de `SAMPLES_V2` es exactamente:
   `manual_hervidor_k1.pdf`, `manual_hervidor_k2.pdf`, `manual_hervidor_k3.pdf`, `contrato_mantenimiento.pdf`, `adenda_contrato_2026.pdf`, `informe_anual_2025.pdf`, `reglamento_interno.pdf`, `politica_teletrabajo_2025.docx`, `politica_teletrabajo_2026.docx`, `tarifas_soporte.docx`, `guia_onboarding.md`, `faq_clientes.md`, `catalogo_recambios.md`, `acta_comite_2026_03.txt`, `acta_comite_2026_06.txt`.
2. `test_copia_exacta` (parametrizado con los 4 nombres de script): `(ROOT / "scripts" / name).read_bytes() == (ASSETS / name).read_bytes()`.
3. `test_page_counts` (parametrizado, 7 casos; `pymupdf.open(...).page_count`): k1 6, k2 6, k3 6, contrato 5, adenda 2, informe 12, reglamento 6.
4. `test_corpus_completo`: `load_folder(SAMPLES_V2)` → `errors == []`, 15 documentos y 70 páginas en total (suma de `page_count`).
5. `test_numero_de_chunks`: la suma de `len(chunk_document(doc, 800, 120))` sobre los documentos de `load_folder(SAMPLES_V2)` es **73**.
6. `test_trampa_manuales` (parametrizado: `("k1", "K1")`, `("k2", "K2")`, `("k3", "K3")`): con `doc = load_document(SAMPLES_V2 / f"manual_hervidor_{m}.pdf", SAMPLES_V2)` y `pages = {p.number: p.text for p in doc.pages}`:
   - las páginas 1, 4 y 5 contienen `modelo`;
   - las páginas 2, 3 y 6 no contienen ninguno de `"K1"`, `"K2"` ni `"K3"`.
7. `test_facts` (parametrizado, 10 casos `(archivo, página, texto)`): el texto aparece en `pages[página]` de `load_document(SAMPLES_V2 / archivo, SAMPLES_V2)`, tras colapsar espacios con `" ".join(texto.split())` en los dos lados:
   - `("contrato_mantenimiento.pdf", 2, "6.200 euros anuales")`
   - `("adenda_contrato_2026.pdf", 1, "6.900 euros anuales")`
   - `("informe_anual_2025.pdf", 3, "22.300 unidades")`
   - `("reglamento_interno.pdf", 5, "Artículo 17. Regalos")`
   - `("manual_hervidor_k3.pdf", 6, "900 101 203")`
   - `("catalogo_recambios.md", 4, "MB-30")`
   - `("tarifas_soporte.docx", 1, "9,99 euros al mes")`
   - `("politica_teletrabajo_2026.docx", 1, "Personal de oficina | 3 días")`
   - `("acta_comite_2026_06.txt", 1, "38.000 euros")`
   - `("faq_clientes.md", 6, "cinco días laborables")`

Total: 1 + 4 + 7 + 1 + 1 + 3 + 10 = **27 tests**.

## Aceptación
- [ ] `for f in make_samples_v2 samples_v2_manuales samples_v2_empresa samples_v2_textos; do cmp scripts/$f.py tasks/assets/081/$f.py; done` → sin salida
- [ ] `uv run python scripts/make_samples_v2.py` → 15 rutas
- [ ] `uv run docuchat ingest samples_v2 --dry-run` → la última línea empieza por `15 documentos, 70 páginas`
- [ ] `uv run pytest -q tests/test_samples_v2.py` → 27 passed
- [ ] `uv run pytest -q` pasa entero (470 + 27 = 497)
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `git status --short samples/` → vacío

## Fuera de alcance
No escribas preguntas (spec 082). No toques `samples/`, `scripts/make_samples.py`, `scripts/sample_content.py` ni nada de `src/`. Si una página no tiene el número de chunks o el texto que espera un test, NO cambies el contenido ni el test: para y explícalo en "Bloqueos".
