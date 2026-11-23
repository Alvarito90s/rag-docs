# 064-b · Evaluación: tres desviaciones de las specs 063 y 064
Fase: 6 · Depende de: 064

## Objetivo
Corregir tres desviaciones de las specs que los tests no detectaban:
1. **`run.py`** captura `except Exception` y no `(OpenAIError, EmbeddingError)`. Con eso, un fallo de indexación (`RuntimeError("Errores al indexar…")`) o un bug cualquiera se presenta como "Error con el servidor de modelos".
2. **`report.py`** recorta los fallos a 5 con `r.misses[:5]`. La spec 064 pide unirlos todos.
3. **`runner.py`** (`evaluate_generation`): si una pregunta con respuesta recibe "No lo sé", deja `keywords_ok = None` y no cuenta las citas. La spec 063 (punto 2) dice que un "No lo sé" cuenta como fallo (`keywords_ok = False`). Con el `None`, el falso rechazo (q17) no aparece en la lista "Fallos:" de `results.md`.

## Archivos
- modificar: `src/docuchat/evaluation/run.py` (solo el `except` y sus imports)
- modificar: `src/docuchat/evaluation/report.py` (solo `render_retrieval_table`)
- modificar: `src/docuchat/evaluation/runner.py` (solo `evaluate_generation`)
- modificar: `tests/evaluation/test_runner_generation.py` y `tests/evaluation/test_report_run.py` (solo AÑADIR tests)

## Comportamiento
1. **`run.py`**:
   - Cambia el `except` por `except (OpenAIError, EmbeddingError) as e:`, con `from openai import OpenAIError` y `from docuchat.index.embeddings import EmbeddingError`.
   - El resto de excepciones se propaga.
   - El mensaje no cambia.
2. **`report.py`**: `misses = ", ".join(r.misses) if r.misses else "—"`, sin recortar.
3. **`runner.py`**, en las preguntas con respuesta, SIEMPRE (haya rechazo o no):
   - `kw_ok = keywords_hit(answer.text, q.answer_keywords)`
   - `cit_correct, cit_total = citation_counts(answer.sources, q.expected_doc, q.expected_page)`
   - `kw_oks.append(kw_ok)` y suma de citas.

   Además, `if no: false_refusals += 1`. Las métricas agregadas no cambian de fórmula.

## Tests obligatorios
NO cambies los tests existentes; solo AÑADE estos.

`test_runner_generation.py`:

7. Falso rechazo:
   - Entrada: `QueueChat([[NO_ANSWER]])`, reloj `[0.0, 1.0, 2.0]`, preguntas `[A]`.
   - Esperado:
     - `results[0].no_answer is True`
     - `results[0].keywords_ok is False`
     - citas `0, 0`
     - `false_refusals == 1`
     - `keyword_accuracy == 0.0`

`test_report_run.py`:

9. Fallos sin recortar:
   - Entrada: `render_retrieval_table([RetrievalReport(800, "bm25", 26, 32, 0.5, 0.8, 0.6, ["q01", "q02", "q03", "q04", "q05", "q06"])])`.
   - Esperado: contiene `"| q01, q02, q03, q04, q05, q06 |"`.

10. Error que no es del servidor:
    - Prepara: `monkeypatch.setattr("docuchat.evaluation.run.build_eval_index", boom)`, con `boom` lanzando `RuntimeError("Errores al indexar: roto.pdf")`.
    - Ejecuta: `main([...])` con los mismos argumentos que el test 7.
    - Esperado: `pytest.raises(RuntimeError, match="roto.pdf")`.

## Aceptación
- [ ] `uv run pytest -q tests/evaluation` → 53 passed
- [ ] `uv run pytest -q` → 440 passed
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `grep -n "except Exception\|misses\[:" src/docuchat/evaluation/*.py` → sin resultados

## Fuera de alcance
Cualquier otro cambio.
