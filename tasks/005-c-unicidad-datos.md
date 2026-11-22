# 005-c · Samples: comprobar que cada dato está en una sola página
Fase: 0 · Depende de: 005-b

## Objetivo
`test_pdf_facts` no cumple el punto 6 de la 005-b: falta comprobar que el dato NO aparece en otras páginas.

## Archivos
- modificar: `tests/test_samples.py` (solo el cuerpo de `test_pdf_facts`)

## Interfaz
```python
@pytest.mark.parametrize("filename,page,fact", FACTS)
def test_pdf_facts(filename: str, page: int, fact: str) -> None:
    with pymupdf.open(SAMPLES / filename) as doc:
        pages_with_fact = [i + 1 for i in range(doc.page_count) if fact in norm(doc[i].get_text())]
    assert pages_with_fact == [page], f"{filename}: '{fact}' en páginas {pages_with_fact}"
```

## Comportamiento
1. Sustituye el cuerpo por el de arriba, tal cual. No cambies `FACTS` ni ningún valor esperado.
2. Escribe `reports/005-c-unicidad-datos.md` y también `reports/004-b-check-env-ajustes.md`, que falta.

## Aceptación
- [ ] `uv run pytest -q tests/test_samples.py` → 19 passed
- [ ] `uv run ruff check . && uv run ruff format --check .` sin errores
- [ ] `ls reports/` muestra `004-b-check-env-ajustes.md` y `005-c-unicidad-datos.md`

## Fuera de alcance
Todo lo demás.
